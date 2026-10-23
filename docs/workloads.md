# Workload and measurement specification

The workload families use the cardinalities, maximum durations, window widths
and stationary point fractions in [workloads.csv](../results/workloads.csv).
Timestamps are integer microseconds. The rules below define the distributions;
the CSV state ratios are measurements summarized over cohorts and snapshots,
not parameters from which exact individual events can be recovered.

## Records and temporal structure

Assign equality keys the integers `0..K-1`, drawn uniformly. Interval routing
classes number one for Campaign and Tariff, two for Entitlement, and four for
FixedBand; point routing has two uniformly selected classes. Encode an interval
class as the corresponding named grouping tuple in Table 1. Routing classes do
not participate in the equality join. Interval values are uniform integers in
`[-5,5]`, point values in `[-3,3]`; COUNT is one on each source record.

For interval start `a`, with probability 0.95 (Campaign), 0.97 (Tariff), or 0.70
(Entitlement), choose end `b=(floor(a/(D/4))+1)*(D/4)`. This is an exact scheduled
deadline, not rounding an already generated end. Otherwise draw an independent
integer duration uniformly in `1..D` and use `b=a+duration`. FixedBand always
uses `b=a+D`. When several records share an end, their different starts and
values remain distinct until the response encoding combines them.

At matched load, generator event progress advances one second per wall-clock
second, with 600,000 arrival slots per second. A record's event start/time is
the progress at its arrival slot minus its sampled delay. Per side, partition
arrivals into blocks of fifty: one uniformly selected position gets a delay
uniform in `[6,3600]` seconds, the other 49 get delays uniform in `[0,4]` seconds,
all on the microsecond grid. Each record therefore passes the one-hour admission
horizon and exactly 2% arrive behind the five-second publication threshold.
Generate intervals from their delayed starts, rather than delaying their ends
independently. Markers are ordered after their assigned epoch's records.

The 72-hour prefix follows these rules before the measured interval. Calibration
uses a separate ten-minute stream. The measured trial restores mature logical
state and runs 1,200 seconds. Input files contain 100 million records, split by
stream offset; the file boundary has no temporal or trial semantics. Source
identities are `(side,offset)`. Saturation varies wall-clock replay speed only;
event timestamps, order, markers and logical input identities stay fixed.

Use Python's MT19937 `random.Random` streams with seeds 9001 for the prefix,
9051 for calibration, and 9101..9105 for trial arrival orderings. Derive independent
streams for side selection, keys, routing, values, endpoint choice, duration and
delay by adding respectively 0, 100, 200, 300, 400, 500 and 600 to each seed.
Draw fields in that order, skipping interval-only fields for points. These seeds specify the revised distribution protocol; exact raw input files
are not reconstructed from the aggregate result tables.

## Changing mixture

The input fractions for shared-deadline, unique-end and small-key shapes are
40%, 40% and 20%. Assign fixed disjoint key sets to these shapes by `key mod 5`:
0/1, 2/3, and 4. Within each shape, `floor(key/5) mod 2` divides keys into two
equally loaded sets. During each 180-second phase the sets receive interval
fractions 0.8 and 0.2; these fractions swap in the next phase. Each set gets
half its shape's offered rate, preserving a global interval fraction of 0.5.
This experiment uses one interval routing class per equality key. The shared
shape uses Tariff's deadline rule; the unique shape uses FixedBand's duration.
The small-key stratum comprises cohorts with fewer than eight distinct live
projected keys at the sampled decision; half the routing groups lie in this
stratum. This is a response-shape stratum, not a rule that short durations alone
force small state: accepted late inputs can keep a short interval observable
until the opposite frontier passes it. The released summaries describe this
mixture and its phase changes; they do not encode the complete input sequence
or every cohort's live-key distribution.

The `n_H/d_E` table column is `sum(n_H)/sum(d_E)` over all equality/routing
cohorts and ten-second measurement snapshots. It is neither the mean of per-key
ratios nor the endpoint-sharing probability. Empty endpoint maps contribute zero
to both totals. The 400-decision diagnostic is balanced by response-shape bin;
its action proportions do not estimate the natural frequencies of the trace.

## Measurement populations

All admitted records enter latency statistics, starting at scheduled ingress
arrival. Completion requires durable journal commitment plus acknowledgment of
all replacements for already published windows. If a record is unmatched or
only updates unpublished windows, commitment alone completes it. Each matched
trial has 720 million observations. Saturation uses the same population.

Every reported system metric is a median of five trial-level quantities. Peak
state is a within-trial maximum; integrated state is its time integral. Planner
CPU percentage divides planner CPU, including scans and unsuccessful planning,
by all worker CPU. Migration execution is charged to total CPU and conversion
work. The paired adaptive-policy rows in [mixed_trials.csv](../results/mixed_trials.csv)
share arrival seeds. They are trial-level summaries, not per-record timing logs.
[attempts.csv](../results/attempts.csv) reports the denominator of allowance
abandonment separately from the balanced decision sample. Here every noncommitted
attempt in that dataset is an allowance abort; no pause-time abort is included.
