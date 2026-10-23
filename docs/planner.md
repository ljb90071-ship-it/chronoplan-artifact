# Actions, forecasts and accounting

The finite action grammar consumes the complete visible cohort. `Replace(Y)`
rebuilds all its generations as one writer. With one generation, `Retain(Y)` seals
it and opens a different writer. With two, `MergeRetain(Y)` first merges their
responses into one Endpoint target, which becomes sealed beside the new writer.
There is one installation and one cooldown event. Retain's adapter ablation can
use this merge without synthesizing old intervals. EagerSynth permits only Stay
and Replace. All candidates use the same budget and prediction rules.

The code in [planner.py](../src/planner.py) enumerates this grammar and provides
the numerical forecast primitives. The [decision example](../examples/decision.py)
combines them with `Action/choose`. Its input CPU and memory-time values are
illustrative costs in the paper's worked example, not a calibration dataset or
a candidate log from the changing workload.

## Bounded profiles

Each worker tracks its 64 largest interval-state cohorts, ties by equality/routing
key, refreshing every ten seconds. A newly tracked cohort waits for a complete
60-second window. The same rule is applied by each adaptive policy. Fixed
per-cohort counters and histograms are charged to worker memory; preflight scans
are separately charged to planner CPU. This cap limits prediction work and does
not make scanning a large response free.

Size buckets use `min(31,ceil(log2(N+1)))`. A coefficient is total primitive CPU
divided by count in the calibration bucket. Missing buckets use the nearest
nonempty bucket in the same layout and primitive, with downward tie breaking.
If an entire primitive table is empty, that candidate is unavailable; Stay
remains possible. Lookup navigation and payload accumulation have separate
coefficients. A Projected probe's payload count uses the trailing matches/probe
ratio clipped to the predicted population. This is a cost estimate, not a
logarithmic worst-case bound on an overlapping interval query.

`lifetime_bins` maps current residual removal thresholds to powers-of-two upper
edges plus an overflow maximum. Thresholds are measured in microseconds and
divided by the nonnegative 120-second frontier velocity to obtain lifetimes in
wall seconds. Zero velocity yields infinite lifetime. Future births use an
effective distinct-key rate and normalized lifetime histogram; duplicate-key
updates are excluded from births. A new layout uses calibration profiles scaled
by the current interval rate. Split forecasts total stored entries, with separate
calibrated transfer work. Endpoint cancellation and key merging affect the
effective birth profile rather than creating negative predicted populations.

`Population.at(t)` implements current survivors plus the integral of future
births. `removals(left,right)` derives expiration counts from those same lifetimes,
so a separately observed deletion rate is not charged a second time. Header/base
bytes are separate from per-key storage. `integrate` is a per-population primitive:
callers assemble the source phase and installed visible populations of a complete
candidate with disjoint `start_s/end_s` intervals. Set `population_origin_s` to
the installation time for a target population defined at that cut. The source
phase ends where the target phase begins, avoiding duplicate ordinary CPU. It is not a full calibrated engine or an online pool manager.

## Construction and cost

Builder share is in cores (core-seconds per wall-second). Given initial work,
interval arrival rate and catch-up work per record, `construction` computes build
time, service rate, drain time and allowance. It defers a candidate whose catch-up
service cannot exceed arrivals. The estimated installation batch uses
`ceil(rate_R * min(0.005,4096/(rate_R+rate_S)))`; actual sealed batches still pass
the hard counter before installation. One-time CPU includes catch-up once.

All candidates compare to the same `T=max(60,current-last-expiration)`, or 60
seconds at zero progress. Each interval `[0,60]` and `[60,T]` uses 64 midpoint
cells; split a cell at the installation time. The tail uses the identical CPU
and memory-time calculation. It is a finite comparison, not an assertion that
different writers become identical after T.

Before installation, held bytes include source, full target reservation,
scratch and buffers. Occupied target nodes are not added again to their reserved
arena. After installation, retain any capacity the allocator still holds; do not
replace a held reservation by its smaller logical occupancy. Multi-generation
actions sum visible populations, and MergeRetain reserves the new writer's
installation batch separately from the merged old response. Hard co-resident
capacity is checked independently of predicted average occupancy.

Common incurred scans cancel in action comparison but remain planner overhead.
A change qualifies when recurring savings exceed 1.2 times one-time CPU, then
the lowest total cost wins. Successful installation starts the 120-second
cooldown; aborts can be reconsidered at the next decision. The source remains
authoritative through an abort. Ties use action order Stay, Replace, Retain,
MergeRetain, followed by Projected, Split, Endpoint.
