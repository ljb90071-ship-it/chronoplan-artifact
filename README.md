# ChronoPlan supplemental material

Companion to **ChronoPlan: Re-encoding Compacted Temporal Aggregate State**.
ChronoPlan adapts compacted temporal state by synthesizing its response and
catching up with arriving records while preserving epoch outputs. Explore these
mechanisms through exact-integer operators, algebra checks and paper result tables.

## Navigate

| Material | Purpose |
|---|---|
| [Paper map](paper-map.md) | Sections, figures, tables and corresponding files |
| [Operators](src/chronoplan.py) | Response sweep, bounded catch-up, cost comparison and bilateral epochs |
| [Implementation notes](docs/implementation.md) | State contracts, algorithm choices and runtime protocols |
| [Results dictionary](results/README.md) | Fields, units, populations and aggregation rules |
| [Planner specification](docs/planner.md) | Finite actions, bounded profiles and cost accounting |
| [Workload and measurement rules](docs/workloads.md) | Distributions, progress markers, latency population and trial pairing |
| [Experiment parameters](configs/paper.json) | System evaluation settings |
| [Synthesis input](examples/synthesis.json) | Figure 1's two intervals and frontier |
| [Epoch input](examples/epochs.json) | Routing groups and independently advancing frontiers |

## Run

Use Python 3.10 or later and its standard library. Run from the repository root:

```sh
python -B examples/run.py
python -B examples/run.py examples/epochs.json
python -B -m unittest discover -s tests -p "test_*.py" -v
python -B analysis/check_results.py
python -B examples/decision.py
```

The synthesis example prints the base, derivatives and three weighted segments:
`[2,3):(1,2)`, `[3,6):(2,1)` and `[6,8):(1,-1)`, with `m=3, L=3`.
The epoch example prints accumulated output by equality key, interval routing
group, point routing group and window index. COUNT remains meaningful when SUM
cancels to zero. The implementation uses list scans and exact integer arithmetic.
Example timestamps and calibration profiles are explicit inputs; system evaluation
settings are documented separately in `configs/paper.json`.

The test suite compares 800 epochs against a full-history join, checks 250
catch-up targets, and exercises action capabilities, forecast units, admission,
capacity abandonment and population-aware statistics.

## Algebra and capacity checks

```sh
python -B tests/check_response_synthesis.py
python -B tests/check_synthesis_epochs.py
python -B tests/check_capacity.py
```

These write JSON summaries beside their scripts. Expected coverage is 6,622
snapshot/frontier states, 33,110 response probes, 119,196 catch-up cases, 9,600
sequential epochs / 153,600 probes, and 1,800 bilateral epochs / 5,165 replacements.
The capacity check evaluates two 20,000-input response families with reservations
of 2.214 and 4.045 MiB against a 3 MiB residual budget. Reservations use the
planner's byte-accounting formula; check execution time depends on the host.

## Analyze results

[check_results.py](analysis/check_results.py) reads aggregate CSV tables and paired
trial summaries, recomputes interval shapes, verifies reservations and action
counts, and derives percentage changes. [decision.py](examples/decision.py)
computes the capacity-dependent choice from the paper's illustrative costs.
The [planner guide](docs/planner.md) defines calibration profiles and forecast
units; the [implementation notes](docs/implementation.md) connect the logical
operators to installation, persistence and recovery protocols.
