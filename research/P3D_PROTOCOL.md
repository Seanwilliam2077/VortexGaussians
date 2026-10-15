# P3d: component-specialized DG without changing its trajectory

Status: frozen before P3d quality or timing outcomes. This phase follows the
exploratory P3c component attribution and does not change any P3b/P3c result,
grid spacing, threshold, or interpretation. Only implementation/API description
corrections may be made before source freeze; the experimental contract below
must not be tuned after observing outcomes.

## Question and three arms

Can removing deliberately redundant field calculations make the already tested
direct-velocity/cached-temperature method useful as a faster approximation to
DD, while preserving that method's numerical behavior exactly?

| Arm | Induced velocity at each tracer | Tb at each tracer | Role |
| --- | --- | --- | --- |
| DD | Direct full field query | Same direct full query | Practical direct-tree reference |
| DG-original | Direct full field query, whose Tb is discarded | Cached full node queries, whose velocity is discarded | P3c diagnostic implementation; redundant-work control |
| DG-specialized | Velocity-only direct query | Temperature-only cached node queries | Candidate removing unused component work |

The success comparison is **DG-specialized versus DD**. Improvement over the
intentionally redundant DG-original alone is not evidence of useful acceleration.
This is an implementation/cost experiment, not a claim of new physical accuracy,
novel interpolation, or a SIGGRAPH-level contribution.

The API selector is `field.evaluation`: `combined` by default and `specialized`
only with `field.mode=grid` and `field.components=temperature`. DD uses
`tree/both/combined`; DG-original uses `grid/temperature/combined`;
DG-specialized uses `grid/temperature/specialized`.

## Frozen numerical contract

DG-specialized must calculate the same direct induced velocity and cached
normalized dynamical temperature as DG-original. Preserve the original active
contribution order in both specialized traversals. Skipping thermal-only work
must not reorder velocity additions; skipping velocity-only work must not
reorder thermal-weight and heat additions. Preserve the existing tree-opening
decisions, LUT values/indexing, thermal support, floating-point expressions,
normalization, and interpolation weights. Do not change the underlying kernel,
opening angle, physical solver, or summation precision to make specialization
appear more accurate or faster.

Keep the world lattice origin at zero and spacing `h=0.035`, rebuilt each step,
with complete eight-corner stencils and a 200,000-node safety cap. The specialized
nodes need only calculate and retain the temperature/support data used by DG.
Interpolation still includes zero-valued unsupported corners without supported-
corner renormalization. At each tracer's actual old position, combine direct
induced velocity with the interpolated Tb, add identical buoyancy, wind, and
procedural curl, then apply the same single speed clamp and Euler update.
Keep the same frozen pre-integration tree and forcing-time convention.

Every query must be accounted for by its actual work: full, velocity-only, and
temperature-only queries; node evaluations; direct tracer requests; stencil
work; fallbacks; and the corresponding velocity/thermal contribution counts.
Do not equate query counts across different component work as if each query
cost the same. Required counter properties include no thermal contributions in
the specialized direct-velocity path and no velocity contributions in the
specialized temperature-node path. Counters and diagnostics must not modify the
numerical state. Formal comparisons require zero cache fallbacks and zero
source/render capacity blocking.

The work ledger exposes `fullFieldQueries`, `velocityOnlyFieldQueries`, and
`thermalOnlyFieldQueries`; their sum equals `fieldQueries`. The corresponding
empty-support counts are `fullNoThermalSupportQueries` and
`thermalOnlyNoThermalSupportQueries`, whose sum equals
`noThermalSupportQueries`. A velocity-only query does not evaluate thermal
support: exclude it from the denominator of any thermal-support proportion.
`componentDirectQueries` still counts the specialized arm's actual-position
direct velocity requests, while `componentDirectNoThermalSupportQueries` is
zero there because temperature is not requested. Do not interpret this zero
as evidence that all queried positions had thermal support. A safety fallback
uses the full query, is counted as such, and invalidates the formal zero-
fallback comparison. Query-component diagnostics must check equality and zero
unrequested component work on leaf, aggregated velocity/thermal-overlap,
unsupported, and empty-tree cases as well as actual positions.

All three arms use physical capacity 600, render capacity 9600, source rate
180/s, the actual 3D solver with its three-layer parameterization, `eps=0.07`,
`dt=1/60`, and 180 steps (3 seconds). Preserve optical radius 0.045, `tau=0.2`,
RGBA32F accumulation, emission weights, renderer, cooling, density decay,
retirement, and depth-boundary rules. Do not change h or these parameters in
response to preliminary quality or timing results.

Use the same three forcing conditions: stationary `(wind=0,turb=0)`, crosswind
`(0.35,0)`, and curl `(0.2,0.55)`. Quality uses the same paired seeds `(11,101)`,
`(23,211)`, and `(47,307)`. These nine pairs have already been observed and are
replay/equivalence evidence, not fresh held-out validation. Timing uses the
already specified pair `(11,101)` in each condition. No new seed selection or
parameter selection is performed in this phase.

## Quality: 27 trajectories and exact replay

Run all three arms in every condition/seed pair: **27 quality trajectories**.
Quality execution and timing execution are separate. In quality runs, collect
the existing-schema full tracer hash at frame zero and after each of the 180
steps, alongside physical/birth-RNG traces: 181 hash/trace entries per run.
Computing these dense tracer hashes is permitted only outside benchmark timing.

For every pair, DG-specialized and DG-original must match exactly at every
step in physical state/hash, tracer hash, physical/render RNG progress, source
and tracer emission credits, and birth records. Retain the original tracer-hash
schema so it still covers actual particle attributes rather than a reduced
proxy. Changed counters/configuration metadata are not part of this state
equivalence requirement.

Save detailed particle states at frames 0,15,...,180: **13 checkpoints** per
trajectory, 351 Float64 particle files for the full quality matrix. Match
DG-specialized and DG-original checkpoint bytes/SHA256 exactly, with stable ID
order and all existing particle columns. Full tracer hashes additionally cover
state not represented by that binary table. At frames 90 and 180, capture the
three fixed yaw angles 0,0.7,1.4 at 256x192: six linear RGBA32F images per run,
162 for the matrix. Specialized/original raw image bytes/SHA256 must match.
Display PNGs are previews, not the quantitative equality target.

DD and DG-original must also reproduce the immutable P3c DD/DG evidence. The
P3c delivery archive SHA256 is
`204ebcebc2586a290a9f6eeca527766cdfb5f95d49d2c54bfcbbb9563e3eaee3`.
Record the source/archive provenance of the baseline used; do not silently
replace it with files generated by the evolving P3d implementation. Compare
the 181 physical/birth trace rows, all 13 particle checkpoint files, and all six
raw image files per corresponding case, as actually available in that archive.

**P3c did not save a full tracer hash at every step.** P3d's 181-step dense
tracer equivalence therefore comes from newly replaying DG-original and
DG-specialized in this phase. Do not claim the old archive supplies a trace it
does not contain. Its saved checkpoint tracer hashes remain additional checks.

All methods must preserve the same physical trajectory and birth/random streams
for a given condition/seed pair. DG and DD are allowed to differ in render
positions/velocities; the comparison between them remains the prior numerical
approximation problem. Matched identities must retain equal visual T, d, and
life. Record missing identities and their optical weights, without hiding them
inside an intersection-only error calculation.

Recompute or explicitly carry forward the unchanged P3b accuracy criteria for
DG versus DD: foreground RGB and alpha NRMSE <=5%, every nonzero checkpoint
position RMS <=0.007 and p99 <=0.035, no unmatched live identities, unchanged
visual evolution, and no capacity/cache fallback. Pool image squared errors
and DD signal energies over the six captures before normalization. Foreground
is the paired DD image's alpha>0.01. These are engineering screening criteria,
not physical or perceptual ground truth. Exact DG replay must not be mistaken
for exact equality of DG and DD.

## Timing: 45 independent page/reset runs

Run all three methods in all three conditions with five independent page/reset
repetitions, using `(11,101)`: **45 timing runs**. Each run uses 20 warmup steps,
then resets and replays from frame zero. Sample every third frame from frame
60 through 180 inclusive, yielding 41 samples per run and **1,845 raw samples**.
This is a warmed fixed simulation-time window with growing particle load, not
steady state. Match simulation frames across methods.

For each condition, use the following fixed run order:

| Repeat | First | Second | Third |
| --- | --- | --- | --- |
| 0 | DD | DG-original | DG-specialized |
| 1 | DG-original | DG-specialized | DD |
| 2 | DG-specialized | DD | DG-original |
| 3 | DG-specialized | DG-original | DD |
| 4 | DD | DG-specialized | DG-original |

The first three repeats rotate positions; the final two reverse the first two
rows. Five repeats cannot perfectly balance three method positions. Report the
actual order and this limitation rather than calling it completely balanced.

Use the existing `gl.finish()` synchronized completed-frame wall-time protocol,
draining previous work before the measurement begins. Include physical stepping,
cache clearing/stencil/key construction, node queries, direct component queries,
interpolation, integration, sorting/upload, drawing, and GPU completion. Nothing
needed by the algorithm is free preprocessing. Retain stage costs and actual
work counters to explain any gain or loss. This is not pure GPU timing.

No full tracer hash, dense snapshot serialization, raw particle transfer,
field probe, input observer, screenshot, or pixel readback may be inserted into
the measured frame. Retain the existing lightweight physical/birth lock outside
the measured interval, reusing the returned physical hash where possible. This
trace must not traverse the dense tracer population. Initial/final snapshots
and invariance checks may run outside timing. Verify timing and quality code
exercise the same production algorithm; the absence of diagnostics must not
change numerical state.

For each run, obtain the frame median and p95 from the sorted sample at index
`floor(q*(n-1))`. Define each method/condition's central latency as the median
of its five per-run frame medians. Define its tail statistic as the median of
its five per-run frame p95 values. The tail is **median of per-run p95**, not
the p95 of 205 pooled frames. Retain all raw samples and all five run summaries;
correlated frames are not independent repetitions.

## Fixed decision and stopping rule

Report execution validity, exact numerical equivalence, descriptive DG accuracy,
and engineering cost success separately. An incomplete matrix or missing
baseline/equivalence evidence cannot be treated as a positive result.

The candidate succeeds in this bounded engineering test only if:

1. All required replay/state/image equivalence checks pass, with zero source
   blocking or cache fallbacks and complete evidence.
2. DG retains the frozen accuracy requirements in all nine observed pairs.
3. Separately in every forcing condition,
   `central_latency_DD / central_latency_DG-specialized >= 1.5`, and the
   specialized method's median of per-run p95 is no greater than DD's.

Do not use DG-original as the denominator for the success criterion. Its cost
explains redundant work in the previous diagnostic; a slow original control
does not establish that DG is intrinsically slow or that specialization is
competitively fast. All formal speed ratios come from this same timing matrix,
not by dividing independently collected P3a/P3b/P3c times.

A numerical mismatch is an implementation-equivalence failure requiring diagnosis,
not evidence against the interpolation hypothesis. Once equivalence is achieved,
failure of either cost condition in any forcing condition rejects this tested
component-specialized DG route under the frozen targets. Do not respond by
adding grid scales, choosing another seed, relaxing the thresholds, or hiding a
failed condition in a pooled average. Correctness smoke checks may repair bugs;
their outcomes may not change the method or decision rule.

## Interpretation

A positive result establishes a faster implementation of the previously tested
DG numerical approximation over this short, already observed workload on the
measured device. It does not provide fresh generalization evidence, improved
physical realism, conservative dynamics, scene-combustion feedback, late
ignition, long-time stability, or superiority to a calibrated layered method.
The P3b decision remains unchanged; P3d has its own explicitly bounded decision.

If worthwhile, a later phase must freeze fresh seeds/conditions and longer
horizons before using them for confirmation. The old nine pairs must never be
renamed held-out data for a method informed by their outcomes. This phase does
not claim that specialization or standard field interpolation alone constitutes
a publishable research contribution.
