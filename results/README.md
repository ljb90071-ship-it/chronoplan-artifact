# Result files and units

These UTF-8 CSV/JSON files contain the paper's summary and trial-level results. Each header
names a field; a blank sensitivity cell means the paper does not report that
quantity. It is not zero. The adaptive-policy trial summaries and attempt counts are provided separately;
no individual candidate records are inferred from medians.
GiB = 2^30 bytes, MiB = 2^20 bytes; million and billion records are decimal.

| File | Rows and fields |
|---|---|
| [workloads.csv](workloads.csv) | Table 2, one row per workload. Equality-key cardinality; maximum input duration and window width in seconds; eligible projected keys / distinct end within a cohort; interval routing dimensions; stationary point-input fraction. |
| [shapes.csv](shapes.csv) | Additional disjoint-sweep examples, each with `n=20` intervals. `m` strictly-future nonzero derivative keys including the return to zero; `L` nonzero runs; `entry_bytes=96*L`, excluding metadata and catch-up. |
| [stationary.csv](stationary.csv) | Table 3, peak operator state in GiB for each method and workload, including transient state. |
| [mixed.csv](mixed.csv) | Table 4. Peak GiB; integrated GiB-min across 20 minutes; converted GiB including failed attempts; CPU core-seconds probing retained nonwritable generations; median across five trial p99 latencies in ms; planner CPU percentage. EagerSynth has zero sealed-generation probe work. |
| [decisions.csv](decisions.csv) | Table 5. 200 candidate decisions per shape bin. `m,L` are candidate medians; `U,used_entries` are medians over completed replacements only. `reserved_mib` uses `96*(L+4096)+8192`, rounded to three decimals. Last three fields are action counts, not percentages. Medians do not reconstruct individual candidate records. |
| [durability.csv](durability.csv) | Table 6. Checkpoint image GiB, journal MiB/s, median recovery seconds, common setup seconds and setup peak GiB. Journal and checkpoints are separate from operator-state metrics. |
| [saturation.csv](saturation.csv) | Maximum reported rate with stable backlog and p99 below 250 ms; count equals rate times 1,200 seconds. |
| [sensitivity.csv](sensitivity.csv) | ChronoPlan lifetime multiplier or reserved update cap, integrated GiB-min, p99 ms, abandoned-attempt percentage, and peak GiB where reported. |
| [stationary_mixture.csv](stationary_mixture.csv) | Static versus ChronoPlan integrated GiB-min and p99 ms on the stationary mixture. |
| [latency_components.json](latency_components.json) | Separate marginal journal-force and sink-persistence p99 values in ms. They must not be added to reconstruct end-to-end p99. |

Operator state includes indexes, accumulators, outboxes, targets and buffers;
finalized sink results are excluded consistently. Durable record latency ends
when the last output replacement caused by that input is acknowledged by the sink.
The mixed workload offers 600,000 records/s for 1,200 seconds (720 million records).

[shape_replay.json](shape_replay.json) supplies both paper figures. The small
cut includes the original rows, base, derivatives, both writable snapshots,
catch-up and installation inputs, and the probe at timestamp 5. The three large
responses share the same derivative-key count, base and last end. Reservations
are bytes after including 4,096 extra intervals. A null value means the pairing
test rejects that response. Index requests count invocations at timestamps inside
each component's time envelope, and historical-row touches count only records
whose payload contributes, over 40,000 probes per response. Both counts measure
logical work. In the reservation chart, the 3 MiB boundary uses the same scale
for all layouts. The hatched region is the 4,096-slot catch-up allowance.
The paired row for changing SUM shows an unavailable status because a SUM
change with no COUNT change cannot be matched. The paper figures are available
in [figures](../figures).

## Trial summaries and decision populations

[mixed_trials.csv](mixed_trials.csv) provides five paired trial rows per adaptive
policy, keyed by trial and arrival seed. Its metric units match mixed.csv. Every
system summary is the median of the corresponding trial-level quantity; a peak
is computed within a trial before taking the median. Planner percent divides
planner CPU by total worker CPU. `latency_records` counts all admitted inputs,
including unmatched and unpublished-window records; completion rules are in
[workloads.md](../docs/workloads.md).

[attempts.csv](attempts.csv) records attempts, allowance aborts and commits for
each trial and update cap. At cap 4096, 130/3250 full-trial attempts abort; the
median trial abort fraction is 4%. These are separate from the balanced
400-candidate diagnostic. Its Replace count is an admitted decision to attempt
replacement, not a completed-target count. Its L and U/used medians have different
populations and cannot certify per-target capacity. That property is checked by
[test_capacity_population.py](../tests/test_capacity_population.py) on individual
reference targets, with explicit counterexamples to the median inference.
