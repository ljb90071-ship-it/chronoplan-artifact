# Implementation contracts

## Response and synthesis

`endpoint(rows,f)` folds all changes through `f` into `H(f)`. It returns sorted,
nonzero derivative vectors strictly after `f`. `sweep` emits the current vector
before applying each change, preserving inclusive starts and exclusive ends.
Every physical row is `(a,b,c,s)` with positive COUNT `c`; SUM `s` may be negative
or zero. A grouped point `(d,z)` contributes `(c*d,s*z)`, never an average value.
The executable epoch engine accepts ungrouped source points (`d=1`).

The final derivative must return to zero. Empty responses produce no rows and no
future derivative keys. With `m` future keys there are at most `m` nonzero segments.
Pairing in [response_layouts.py](../src/response_layouts.py) treats the base as
an opening at the frontier and pairs each negative COUNT change with the oldest
unmatched positive inverse vector. The caller first counts on the committed
snapshot, then emits on the same ordered changes if the scan completes. A zero
COUNT change, missing partner, or exhaustion of the open-start limit makes the
disjoint sweep the available fallback. The 64-start limit bounds scratch. With
a complete pairing, each entry accounts for two distinct boundaries. Any exact
alternative row can account for at most two, giving the minimum entry count.

Packed history uses the disjoint snapshot in a 48-byte sorted array. A predecessor
search and end check return at most one match. Catch-up records and the installation
batch enter its separate writable index. Each arena includes 8192 bytes for
metadata and page rounding. At a point, sum the immutable and writable responses.
A frontier can retire complete expired storage pages, while the reference
[PackedHistory](../src/response_layouts.py) exposes predecessor logic.

Adjacent equal unit intervals may synthesize to a support longer than the source
duration limit. This support is physical state and is not passed through ingress
admission or joined again against old points.

`endpoint` sorts its dictionary and therefore costs O(n + m log m) here. Given
already ordered changes, `sweep` is O(m). List-based probes are O(n). These choices
expose the algebra without implying the complexity of a balanced interval index.

## Catch-up and installation

`CatchupTarget` synthesizes one cohort and reserves `96*(L+Umax)+8192` bytes.
The available-byte argument is the residual after source, pinning/COW, scratch,
and shared buffer reservations. Each real interval consumes one allowance,
including duplicates and records whose support already expired. Applying an
interval appends at most one overlapping key; equal `(a,b)` keys combine. The
target is never recanonicalized during catch-up. Frontier advancement deletes
expired supports and cannot increase the entry count.

Every interval from the installation epoch must also pass `apply`. An exhausted
allowance makes the target un-installable; the original source supplied by the
caller is untouched. `install()` returns a copy of the target response only.
These methods have no output accumulator and cannot emit duplicate repairs.
The class models record-count feasibility; it does not measure wall-clock pause
time or coordinate concurrent writers.

## Bilateral epochs

`EpochEngine.epoch` validates the entire batch against the current frontiers and
input duration before mutation. New intervals probe old points and then enter
interval state. New points probe the updated response, counting the new/new
cross term exactly once. Equality keys match; interval-side and point-side
routing attributes become separate output coordinates rather than filters.
After processing, frontiers advance, points with `t < f_R` expire, and interval
supports with `b <= f_S` expire or are synthesized. Output values remain intact.
All output windows are retained in this reference model, so the full-history
oracle can compare complete results after every epoch.

## Cost selection

`Action/choose` applies feasibility, cooldown, a 1.2 savings margin and total
cost comparison. The companion [planner specification](planner.md) defines
complete-cohort actions, adapter filtering, bounded occupancy and primitive-cost
profiles, construction time and terminal integration. [planner.py](../src/planner.py)
implements the numerical primitives and action grammar; the worked example links
capacity to selection. Profiles are explicit inputs, not an online calibration
service. Common incurred scan cost is excluded from comparison and retained in
reported planner overhead.

## Runtime protocol boundary

The paper's durable implementation orders a response snapshot, buffered real
inputs, installation cut and the next real input batch. Source state remains
authoritative until the switch epoch commits; the target is never probed alongside
its source. The journal stores inputs/frontiers/transition descriptors and outbox
replacements under a checksummed commit marker. A sink accepts only newer logical
epochs; retransmission retains epoch numbers and publisher fencing is separate.
A switch depends on its build checkpoint and ordered interval/frontier suffix
until a durable checkpoint includes the installed state. Re-sweeping a later
unswitched checkpoint can give the right response with too many physical entries
for the prior reservation. The exact cut example in
[shape_replay.py](../examples/shape_replay.py) shows three entries from replaying
the build geometry and five from sweeping the later response. The examples
exercise sequential response operations. An engine supplies the journal,
concurrent installation, and recovery service.
