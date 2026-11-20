"""Alternative targets for an ordered COUNT/SUM response."""
from bisect import bisect_right
from collections import defaultdict, deque
from dataclasses import dataclass
from itertools import chain
from operator import itemgetter


@dataclass(frozen=True)
class Pairing:
    entries: int
    peak_open: int


def scan_pairs(base, changes, frontier, open_limit, emit=None):
    """Count a complete forward pairing or return None.

    Use emit only after a successful count on the same committed snapshot.
    A positive COUNT change opens one pair; an inverse vector closes it.
    Equal vectors are matched in start order for deterministic geometry.
    """
    open_by_payload = defaultdict(deque)
    open_count = peak = pairs = 0
    base_change = ((frontier, base),) if base != (0, 0) else ()
    for time, (count, total) in chain(base_change, changes):
        if count > 0:
            if open_count == open_limit:
                return None
            open_by_payload[count, total].append(time)
            open_count += 1
            peak = max(peak, open_count)
        elif count < 0:
            payload = (-count, -total)
            starts = open_by_payload.get(payload)
            if not starts:
                return None
            start = starts.popleft()
            if not starts:
                del open_by_payload[payload]
            if emit is not None:
                emit((start, time, *payload))
            open_count -= 1
            pairs += 1
        else:
            return None
    return Pairing(pairs, peak) if open_count == 0 else None


class PackedHistory:
    """Immutable sorted, disjoint rows, queried by predecessor."""

    def __init__(self, disjoint_rows):
        self.rows = tuple(disjoint_rows)

    def row_at(self, time):
        index = bisect_right(self.rows, time, key=itemgetter(0)) - 1
        if index >= 0 and time < self.rows[index][1]:
            return self.rows[index]
        return None


def packed_reservation(entries):
    """48-byte history rows, one metadata page and at most one page of rounding."""
    return 48 * entries + 8192
