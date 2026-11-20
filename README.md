# ChronoPlan supplemental material

Companion to **ChronoPlan: Re-encoding Compacted Temporal Aggregate State**.
This repository provides exact-integer reference operators, executable examples,
algebra checks, and machine-readable paper results. Start with the source and data
links below; running code is optional for understanding the material.

| Read first | Purpose |
|---|---|
| [Paper map](paper-map.md) | Sections, figures, tables and corresponding files |
| [Reference operators](src/chronoplan.py) | Response sweep, bounded catch-up, cost comparison, bilateral epochs |
| [Target layouts](src/response_layouts.py) | Pairing test and predecessor search over packed disjoint history |
| [Shape replay](results/shape_replay.json) | Figure inputs, reservations, search requests and historical payload counts |
| [Implementation notes](docs/implementation.md) | Contracts, algorithm choices and runtime boundaries |
| [Results dictionary](results/README.md) | Fields, units, populations and interpretation |
| [Planner specification](docs/planner.md) | Finite actions, bounded profiles and cost accounting |
| [Workload and measurement rules](docs/workloads.md) | Distributions, progress markers, latency population and trial pairing |
| [Experiment parameters](configs/paper.json) | Configuration described in the paper |
| [Synthesis input](examples/synthesis.json) | Two source intervals and the point frontier used in Figure 1 |
| [Epoch input](examples/epochs.json) | Two routing groups and independently advancing frontiers |

## Run the reference implementation

Requires Python 3.10 or later; all commands below use only the standard library.
Run from this directory after extracting the ZIP. No services, download, build,
database server, or GPU is needed.

```sh
python -B examples/run.py
python -B examples/run.py examples/epochs.json
python -B -m unittest discover -s tests -p "test_*.py" -v
python -B analysis/check_results.py
python -B examples/decision.py
python -B examples/shape_replay.py
```

The first command computes three segments: `[2,3):(1,2)`, `[3,6):(2,1)` and
`[6,8):(1,-1)`. It prints the base and derivatives as well as `m=3, L=3`.
The second prints accumulated output by equality key, interval routing group,
point routing group and window index after each epoch. COUNT remains meaningful
when SUM cancels to zero. The 13-test suite compares 800 epochs against a full-history join, checks 250
individual catch-up targets, rejects mixed-population median inference, and
checks action capabilities, forecast units, admission and capacity abandonment.
The shape replay checks all 40,000 timestamp probes per response after adding the
same 4,096 intervals. It also demonstrates the installation cut in Figure 1 and
the need to retain the build snapshot for recovery.

## Extended checks

```sh
python -B tests/check_response_synthesis.py
python -B tests/check_synthesis_epochs.py
python -B tests/check_capacity.py
```

These write JSON summaries beside their scripts. Expected coverage is 6,622
snapshot/frontier states, 33,110 response probes, 119,196 catch-up cases, 9,600
sequential epochs / 153,600 probes, and 1,800 bilateral epochs / 5,165 replacements.
The extended capacity check exercises the disjoint sweep on two further shapes.
These checks measure logical coverage and entries.

## Result analysis

[check_results.py](analysis/check_results.py) reads CSV summaries, recomputes the
shape examples from intervals, verifies target reservations and action counts,
and derives the percentage changes reported in the paper. CSVs include paper summaries and paired trial-level summaries for the adaptive
policies; they are not per-record timing or execution logs. The analysis command does not rerun the system
experiments. The decision example computes the choice among Stay, Retain, packing and a single
writable replacement using the illustrative Section 6.3 costs. Bounded forecast primitives accept explicit calibration
profiles; they do not perform online hardware calibration.

Configuration values describe those experiments; the lightweight
examples use small integer timestamps and do not load that system configuration.

The Python implementation uses list scans and arbitrary-precision integers to
make the semantics inspectable. It implements the response adapter and logical
epoch rules, not the optimized red-black indexes, fixed-width allocator, concurrent
installation, journal, durable sink or recovery service. The allocator formula is
a byte-accounting model, not a measurement of Python object memory. Runtime and
durability protocols are mapped in the implementation notes. No full-system
performance reproduction command is supplied by this repository.
