"""Measure entry reservations and stored-row contributions on three exact responses."""
import argparse
from itertools import chain
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from chronoplan import CatchupTarget, EpochEngine, endpoint, reservation, response, sweep
from response_layouts import PackedHistory, packed_reservation, scan_pairs

N = 20_000
U = 4096
OPEN_LIMIT = 64
BUDGET = 3 * 2**20


def fixtures(n):
    # Every time 1..2n-1 is a nonzero change and every response starts at (1,1).
    starts = [0, *range(1, 2 * n - 2, 2)]
    ends = [*range(2, 2 * n - 1, 2), 2 * n - 1]
    return {
        "gaps": [(2 * i, 2 * i + 1, 1, 1) for i in range(n)],
        "overlap": [(a, b, 1, 1) for a, b in zip(starts, ends)],
        "changing_sum": [(t, t + 1, 1, (-1)**t) for t in range(2 * n - 1)],
    }


def probe_vectors(rows, probes):
    """Independent chronological prefix oracle for arbitrary overlapping rows."""
    event = [0, 0]
    base, changes = endpoint(rows, 0)
    event[:] = base
    index = 0
    for t in range(probes):
        while index < len(changes) and changes[index][0] <= t:
            dc, ds = changes[index][1]
            event[0] += dc
            event[1] += ds
            index += 1
        yield tuple(event)


def with_suffix(snapshot, suffix):
    # A distinct key consumes one slot even when it crosses many old segments.
    slots = {}
    for a, b, count, total in chain(snapshot, suffix):
        old_count, old_total = slots.get((a, b), (0, 0))
        slots[a, b] = (old_count + count, old_total + total)
    assert len(slots) <= len(snapshot) + len(suffix)
    return [(a, b, *v) for (a, b), v in slots.items()]


def small_cut():
    frontier = 2
    source = [(0, 6, 1, 2), (3, 8, 1, -1)]
    base, changes = endpoint(source, frontier)
    paired = []
    assert scan_pairs(base, changes, frontier, 2)
    scan_pairs(base, changes, frontier, 2, paired.append)
    # Exercise ordinary catch-up and the last allowance in the installation batch.
    target = CatchupTarget(source, frontier, 2, reservation(5))
    during_build = (2, 7, 1, 4)
    install_batch = (5, 8, 1, 2)
    target.apply(during_build)
    target.advance(4)
    at_cut = response(target.rows, 5)
    assert at_cut == (3, 5)
    # Keep earlier window output while exchanging its interval response at the cut.
    window_key = ("meter", "charge", "reading", 0)
    committed = {}
    for layout in ("Stay", "Disjoint", "Paired"):
        engine = EpochEngine(window=10, duration=8)
        out = engine.epoch([("meter", "charge", a, b, s) for a, b, _, s in source],
                           [("meter", "reading", 5, 2)], 0, frontier, replace=False)
        assert out[window_key] == (2, 2)
        a, b, _, s = during_build
        out = engine.epoch([("meter", "charge", a, b, s)], [], 5, 4, replace=False)
        assert out[window_key] == (3, 10)
        if layout == "Disjoint":
            engine.intervals["meter", "charge"] = target.install()
        elif layout == "Paired":
            engine.intervals["meter", "charge"] = with_suffix(paired, [during_build])
        a, b, _, s = install_batch
        out = engine.epoch([("meter", "charge", a, b, s)], [("meter", "reading", 5, 1)],
                           5, 4, replace=False)
        assert out[window_key] == (8, 21)
        committed[layout] = out[window_key]
    target.apply(install_batch)
    original = source + [during_build, install_batch]
    for t in range(4, 10):
        expected = response(original, t)
        assert response(target.install(), t) == expected
        assert response(with_suffix(paired, [during_build, install_batch]), t) == expected
    after_batch = response(target.rows, 5)
    assert not target.apply((7, 9, 1, 3))
    # A later logical checkpoint is equivalent but can exceed the old flat arena.
    gap_snapshot = [(0, 2, 1, 1), (4, 6, 1, 1)]
    gap_suffix = [(1, 8, 1, 2)]
    restored = with_suffix(gap_snapshot, gap_suffix)
    late_base, late_changes = endpoint(restored, 0)
    late_sweep = sweep(late_base, late_changes, 0)
    assert len(restored) == 3 and len(late_sweep) == 5
    assert list(probe_vectors(restored, 9)) == list(probe_vectors(late_sweep, 9))
    return {
        "frontier": frontier, "source": source, "changes": changes, "base": base,
        "sweep": sweep(base, changes, frontier), "paired": paired,
        "catchup": during_build, "installation_row": install_batch,
        "probe": 5, "at_cut": at_cut, "after_batch": after_batch,
        "committed_count_sum": committed,
        "recovery_entries": {"snapshot_plus_suffix": len(restored),
                             "late_checkpoint_sweep": len(late_sweep)},
    }


def run():
    probes = 2 * N  # Every integer tick through the final, exclusive endpoint.
    last_start = probes - 5
    starts = [i * last_start // (U - 1) for i in range(U)]
    suffix = [(a, a + 4, 1, i % 5 - 2) for i, a in enumerate(starts)]
    assert len(set((a, b) for a, b, _, _ in suffix)) == U
    results = {}
    for name, source in fixtures(N).items():
        base, changes = endpoint(source, 0)
        assert base == (1, 1) and len(changes) == 2 * N - 1
        assert changes[-1][0] == 2 * N - 1
        disjoint = sweep(base, changes, 0)
        pairing = scan_pairs(base, changes, 0, OPEN_LIMIT)
        paired = []
        if pairing is not None:
            assert scan_pairs(base, changes, 0, OPEN_LIMIT, paired.append) == pairing
            assert len(paired) == pairing.entries == N
            assert endpoint(paired, 0) == (base, changes)
        else:
            assert name == "changing_sum"
        packed = PackedHistory(disjoint)
        append_response = list(probe_vectors(suffix, probes))
        history_response = list(probe_vectors(source, probes))
        if name == "gaps":
            closed_form = [(int(t % 2 == 0),) * 2 for t in range(probes)]
        elif name == "overlap":
            closed_form = [(1 + t % 2,) * 2 for t in range(probes - 1)] + [(0, 0)]
        else:
            closed_form = [(1, (-1)**t) for t in range(probes - 1)] + [(0, 0)]
        assert history_response == closed_form
        expected = list(probe_vectors([*source, *suffix], probes))
        assert list(probe_vectors(with_suffix(disjoint, suffix), probes)) == expected
        if paired:
            assert list(probe_vectors(with_suffix(paired, suffix), probes)) == expected
        disjoint_touches = history_lookups = writer_lookups = 0
        for t, delta in enumerate(append_response):
            # Both layouts can skip reads outside their overall time support.
            in_history = disjoint[0][0] <= t < disjoint[-1][1]
            in_writer = suffix[0][0] <= t < suffix[-1][1]
            history_lookups += in_history
            writer_lookups += in_writer
            if not in_writer:
                assert delta == (0, 0)
            row = packed.row_at(t) if in_history else None
            vector = row[2:] if row else (0, 0)
            assert vector == history_response[t]
            assert (vector[0] + delta[0], vector[1] + delta[1]) == expected[t]
            disjoint_touches += row is not None
        # Each successful paired row in these fixtures has COUNT exactly one.
        assert all(c == 1 for _, _, c, _ in paired)
        pair_touches = sum(c for c, _ in history_response) if paired else None
        reserves = {
            "disjoint": reservation(len(disjoint) + U),
            "paired": reservation(len(paired) + U) if paired else None,
            "packed": packed_reservation(len(disjoint)) + reservation(U),
        }
        results[name] = {
            "derivative_keys": len(changes), "disjoint_entries": len(disjoint),
            "paired_entries": len(paired) if paired else None,
            "peak_unmatched": pairing.peak_open if pairing else None,
            "reserved_bytes": reserves,
            "fits": {k: None if v is None else v <= BUDGET for k, v in reserves.items()},
            "index_requests": {
                "disjoint": history_lookups, "paired": history_lookups if paired else None,
                "packed": history_lookups + writer_lookups,
            },
            "historical_rows_touched": {
                "disjoint": disjoint_touches, "paired": pair_touches,
                "packed": disjoint_touches,
            },
        }
    return {"n": N, "update_cap": U, "budget_bytes": BUDGET, "open_limit": OPEN_LIMIT,
            "probes_per_shape": probes, "shapes": results, "small_cut": small_cut()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="write the checked results here")
    args = parser.parse_args()
    report = json.dumps(run(), indent=2) + "\n"
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
