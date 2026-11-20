"""Work through the capacity and break-even comparison in Section 6.3."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from chronoplan import Action, choose, reservation
from planner import Population, construction, integrate
from response_layouts import packed_reservation

BUDGET = 3 * 2**20
CAP = 4096
PRICE = 0.02
INTERVAL_RATE = 200
SETUP_S = 0.010
RUN_S = 60 - SETUP_S

# Example calibration inputs, in microseconds per operation and core-ms per build.
INSERT_US = {"Stay": .65, "Retain": .20, "Packed": .20, "Replace": .95}
BUILD_MS = {"Stay": 0, "Retain": .50, "Packed": 4.50, "Replace": 4.75}


def ledger(runs, probes_per_s, packed_probe_us=.46):
    target = {"Stay": 0, "Retain": reservation(CAP),
              "Packed": packed_reservation(runs) + reservation(CAP),
              "Replace": reservation(runs + CAP)}
    probe_us = {"Stay": .85, "Retain": .97, "Packed": packed_probe_us, "Replace": .42}
    # Uniform illustrative Endpoint node size. Live bytes stay fixed in the comparison.
    source_before = reservation(39_999)
    source_after = reservation(39_998)
    resident = {"Stay": source_after, "Retain": source_after + target["Retain"],
                "Packed": target["Packed"], "Replace": target["Replace"]}
    actions = {}
    for name in target:
        cpu_s = RUN_S * (INTERVAL_RATE * INSERT_US[name] + probes_per_s * probe_us[name]) / 1e6
        memory_time = (SETUP_S * (source_before + target[name]) + RUN_S * resident[name]) / 2**30
        actions[name] = Action(name, BUILD_MS[name] / 1000, cpu_s, memory_time,
                               feasible=target[name] <= BUDGET)
    return actions


def scores(runs, probes_per_s, packed_probe_us=.46):
    actions = ledger(runs, probes_per_s, packed_probe_us)
    chosen = choose(actions["Stay"], [a for name, a in actions.items() if name != "Stay"])
    return {
        "chosen": chosen,
        "cost_core_ms": {name: 1000 * (a.one_time_core_s + a.recurring(PRICE))
                         for name, a in actions.items()},
        "fits": {name: a.feasible for name, a in actions.items()},
    }


def main():
    gaps = {q: scores(20_000, q) for q in (20, 1000, 8000)}
    fast_array = scores(20_000, 8000, .38)
    changing_sum = scores(39_999, 8000)
    assert [case["chosen"] for case in gaps.values()] == ["Retain", "Packed", "Replace"]
    assert fast_array["chosen"] == changing_sum["chosen"] == "Packed"
    free_difference = gaps[1000]["cost_core_ms"]["Replace"] - gaps[1000]["cost_core_ms"]["Packed"]
    rate_slope = RUN_S * (.42 - .46) / 1000
    cross = 1000 - free_difference / rate_slope
    assert round(cross, 2) == 4297.48
    output = {
        "gaps": gaps, "gaps_equal_cost_probes_s": cross,
        "fast_array": fast_array, "changing_sum": changing_sum,
        "construction_example": construction(.8, .2, 100, .0002, 1000, 4096),
        "constant_population_example": integrate(
            Population([(100, float("inf"))], []), {"probes": 2, "matches": 3},
            {"lookup": {0: .01}, "payload": {0: .001}}, 96, 8192, horizon=90,
        ),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
