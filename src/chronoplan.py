"""Exact-integer reference operators for ChronoPlan; standard library only.

Rows are (start, end, count, sum). Source inputs have count=1. Physical
rows may overlap and may exceed the source duration limit.
"""
from collections import defaultdict
from dataclasses import dataclass


def response(rows, t):
    return tuple(sum(r[i] for r in rows if r[0] <= t < r[1]) for i in (2, 3))


def endpoint(rows, frontier):
    base = [0, 0]
    changes = defaultdict(lambda: [0, 0])
    for a, b, c, s in rows:
        if not (a < b and c > 0):
            raise ValueError('Invalid weighted interval')
        if b <= frontier:
            continue
        if a <= frontier:
            base[0] += c; base[1] += s
        else:
            changes[a][0] += c; changes[a][1] += s
        changes[b][0] -= c; changes[b][1] -= s
    return tuple(base), sorted((t, tuple(v)) for t, v in changes.items() if v != [0, 0])


def sweep(base, changes, frontier):
    """Consume ordered strictly-future nonzero derivatives, including final zero."""
    c, s = base
    left = frontier
    rows = []
    for t, (dc, ds) in changes:
        if t <= left or (dc, ds) == (0, 0):
            raise ValueError('Derivative keys must be strictly ordered and nonzero')
        if c < 0 or (c == 0 and s != 0):
            raise ValueError('Invalid COUNT/SUM response')
        if c:
            rows.append((left, t, c, s))
        c += dc; s += ds; left = t
    if (c, s) != (0, 0):
        raise ValueError('Finite response must return to zero')
    return rows


def synthesize(rows, frontier):
    base, changes = endpoint(rows, frontier)
    return sweep(base, changes, frontier), len(changes)


def reservation(entries):
    if entries < 0:
        raise ValueError('Negative entry count')
    return 96 * entries + 8192


def append_interval(rows, row, frontier):
    """Ordinary overlapping insertion; combine equal keys, never canonicalize."""
    a, b, c, s = row
    if b <= frontier:
        return
    for i, (u, v, d, z) in enumerate(rows):
        if (u, v) == (a, b):
            rows[i] = (u, v, c+d, s+z)
            return
    rows.append(row)


class CatchupTarget:
    """Single-cohort allocation model; source remains owned by the caller.

    apply() counts every real interval, even an expired or duplicate one.
    Installation records must also go through apply(). This class neither
    produces output nor models WAL, threads, or a five-ms pause.
    """
    def __init__(self, snapshot, frontier, update_cap, available_bytes):
        if update_cap < 0:
            raise ValueError('Negative update cap')
        self.rows, self.m = synthesize(snapshot, frontier)
        self.L = len(self.rows)
        self.frontier = frontier
        self.cap = update_cap
        self.used = 0
        self.reserved_bytes = reservation(self.L + update_cap)
        self.active = self.reserved_bytes <= available_bytes

    def apply(self, row):
        if not self.active:
            return False
        if self.used == self.cap:
            self.active = False
            self.rows = []
            return False
        self.used += 1
        append_interval(self.rows, row, self.frontier)
        assert len(self.rows) <= self.L + self.used
        return True

    def advance(self, frontier):
        if frontier < self.frontier:
            raise ValueError('Frontier regression')
        self.frontier = frontier
        self.rows = [r for r in self.rows if r[1] > frontier]

    def install(self):
        if not self.active:
            raise ValueError('Abandoned target cannot be installed')
        return list(self.rows)


@dataclass(frozen=True)
class Action:
    name: str
    one_time_core_s: float
    future_core_s: float
    memory_gib_s: float
    terminal_core_s: float = 0
    feasible: bool = True

    def recurring(self, price):
        return self.future_core_s + price*self.memory_gib_s + self.terminal_core_s


def choose(stay, actions, price=0.02, margin=1.2, cooldown_elapsed=True):
    """Equation (transition cost), with forecasts supplied by the caller.

    Common incurred scans are excluded from all alternatives by the caller.
    Capacity feasibility is independent of cost forecasts.
    """
    eligible = [stay]
    if cooldown_elapsed:
        eligible += [a for a in actions if a.feasible and
                     stay.recurring(price)-a.recurring(price) >= margin*a.one_time_core_s]
    return min(eligible, key=lambda a: a.one_time_core_s+a.recurring(price)).name


class EpochEngine:
    """Sequential logical engine with independent frontiers and both-side routing.

    Intervals: (key, interval_group, start, end, value).
    Points: (key, point_group, time, value).
    Output keys: (key, interval_group, point_group, window_index).
    Retains all output values; finalization/publication belongs to the runtime.
    """
    def __init__(self, window=3, duration=6):
        if window <= 0 or duration <= 0:
            raise ValueError('Window and duration must be positive')
        self.window, self.duration = window, duration
        self.fr = self.fs = 0
        self.intervals = defaultdict(list)
        self.points = []
        self.output = defaultdict(lambda: [0, 0])

    def _add(self, key, c, s):
        if c:
            self.output[key][0] += c
            self.output[key][1] += s

    def epoch(self, intervals, points, next_fr, next_fs, replace=True):
        intervals, points = list(intervals), list(points)
        # Validate the entire batch before mutation.
        if next_fr < self.fr or next_fs < self.fs:
            raise ValueError('Frontier regression')
        if any(a < self.fr or not 0 < b-a <= self.duration for k,g,a,b,x in intervals):
            raise ValueError('Interval fails admission')
        if any(t < self.fs for k,h,t,y in points):
            raise ValueError('Point fails admission')
        for k,g,a,b,x in intervals:
            for sk,h,t,y in self.points:
                if k == sk and a <= t < b:
                    self._add((k,g,h,t//self.window), 1, x*y)
            append_interval(self.intervals[k,g], (a,b,1,x), self.fs)
        for k,h,t,y in points:
            for (rk,g), rows in self.intervals.items():
                if k == rk:
                    c,s = response(rows,t)
                    self._add((k,g,h,t//self.window),c,s*y)
        self.points.extend(points)
        self.fr, self.fs = next_fr, next_fs
        self.points = [p for p in self.points if p[2] >= next_fr]
        for kg, rows in list(self.intervals.items()):
            self.intervals[kg] = synthesize(rows,next_fs)[0] if replace else [r for r in rows if r[1] > next_fs]
        return {k: tuple(v) for k,v in self.output.items()}
