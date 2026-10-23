# Paper-to-material map

Section and figure/table numbers refer to *ChronoPlan: Re-encoding Compacted
Temporal Aggregate State*. Table 1 defines the complete-cohort action grammar. The paper contains no numbered pseudocode algorithms;
the relevant procedures are identified below by their section names.

| Paper item | Material | What can be inspected or executed |
|---|---|---|
| Section 2: query, routing, frontiers | [EpochEngine](src/chronoplan.py), [epoch example](examples/epochs.json) | Admission, separate routing coordinates, window COUNT/SUM, opposite-side cleanup |
| Section 3: response and replacement criterion | [endpoint/sweep/synthesize](src/chronoplan.py), [exhaustive checks](tests/check_response_synthesis.py) | Equal future response, half-open boundaries, signed SUM, retained COUNT |
| Figure 1 | [input](examples/synthesis.json), [runner](examples/run.py), [figure](figures/response_synthesis.pdf) | Computes the three weighted segments shown in the paper |
| Section 3: compression before expiration | [implementation notes](docs/implementation.md) | Response-domain explanation; the Split indexed data structure is described in the paper, not implemented here |
| Section 4: capacity and append catch-up | [CatchupTarget](src/chronoplan.py), [unit tests](tests/test_reference.py), [capacity scan](tests/check_capacity.py) | L+U accounting, gap counterexample, abandonment, node-layout arithmetic |
| Section 4: actions and transition cost | [planner primitives](src/planner.py), [planner contract](docs/planner.md), [decision example](examples/decision.py) | Action grammar, bounded occupancy, catch-up time, integration and capacity-dependent choice |
| Section 4: bilateral update identity and epoch invariant | [EpochEngine](src/chronoplan.py), [bilateral checks](tests/check_synthesis_epochs.py), [unit tests](tests/test_reference.py) | Cross term once, routing, independent frontiers, output-neutral replacement versus full history |
| Section 5: runtime and recovery | [runtime boundary](docs/implementation.md) | Protocol contract; no executable WAL, sink, concurrent switching or fault injection |
| Table 2 | [workloads](results/workloads.csv), [parameters](configs/paper.json) | Workload and experiment configuration |
| Table 3 | [shape data](results/shapes.csv), [result checker](analysis/check_results.py) | Recomputed exact m, L and entry bytes |
| Section 6: 20,000-interval capacity example | [capacity scan](tests/check_capacity.py) | Recomputes target sizes and residual-budget admission |
| Table 4 | [stationary state](results/stationary.csv) | Per-workload summary values |
| Table 5 and Figure 2 | [mixed results](results/mixed.csv), [result checker](analysis/check_results.py), [figure](figures/migration_costs.pdf) | Migration and latency data; derived relative reductions |
| Table 6 | [decision sample](results/decisions.csv), [result checker](analysis/check_results.py) | Descriptive counts, shares and capacity formula; individual bounds are checked in test_capacity_population.py, not from medians |
| Table 7 | [durability](results/durability.csv) | Summary values, common setup costs |
| Section 6: stationary mixture, saturation, sensitivity | [mixture](results/stationary_mixture.csv), [saturation](results/saturation.csv), [sensitivity](results/sensitivity.csv) | Inline numerical results and throughput/count arithmetic |
| Section 6: marginal latency components | [component data](results/latency_components.json) | Separate quantiles and their interpretation |
| Section 6: correctness counts | [exhaustive checks](tests/check_response_synthesis.py), [bilateral checks](tests/check_synthesis_epochs.py) | Re-executes stated algebra coverage; output JSON is generated locally |

See the [data dictionary](results/README.md) for units and populations. The
aggregate performance/durability tables are available for inspection and analysis;
the reference operators are not a performance-equivalent engine implementation.

Trial-level comparisons and attempt denominators: [mixed_trials.csv](results/mixed_trials.csv),
[attempts.csv](results/attempts.csv), [analysis](analysis/check_results.py).
The [workload specification](docs/workloads.md) defines progress and population
rules while distinguishing distributions from a complete raw input archive.
