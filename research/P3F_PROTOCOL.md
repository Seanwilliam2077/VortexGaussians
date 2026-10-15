# P3f: fixed-budget selection for direct group correction

Status: frozen before P3f outcomes. This phase follows the P3e negative result
and its explicitly post-hoc residual analysis. It tests one fixed selector and
budget, not a parameter search. Do not add fractions, salts, seeds, difference
scales, or grouping variants in response to results. Correctness repairs must
preserve the method and decision rule below.

## Question, arms, and fixed evidence matrix

Does allocating a fixed number of direct tracer queries using an existing
seven-point second-difference indicator improve deployed trajectories relative
to a predeclared uninformed allocation with the same raw-query budget?

The three production arms are DD, curvature, and hash. DD retains direct full
field queries for every tracer. Both corrected arms build every P3e affine
model, select a fixed fraction of groups, and use direct queries for every
member of the selected groups. They differ only in the selection ranking.
The hash policy is one deterministic uninformed allocation, not an ensemble
of random policies or a statistically representative random baseline.

Run the following six complete quality trajectories, in order:

1. stationary-DD-s11-r101
2. stationary-curvature-s11-r101
3. stationary-hash-s11-r101
4. stationary-DD-s59-r409
5. stationary-curvature-s59-r409
6. stationary-hash-s59-r409

Then run stationary-affine-s11-r101 for complete immutable P3e regression:
seven complete trajectories total. The uncorrected affine regression is not
a fourth newly selected candidate. The matching old DD trajectory also serves
as an immutable P3e regression. Do not terminate quality collection early on
an accuracy, allocation, or comparison failure; collect all seven trajectories
and their complete evidence before deciding whether timing is permitted.

The 11/101 pair is previously observed development evidence. The 59/409 pair
had no prior run in this work before freezing P3f and supplies one new-seed
transfer check in the same stationary condition. It does not establish broad
generalization. The selector, hash, salt, and thresholds must be frozen before
seeing its outputs. Do not rename the old pair held-out evidence.

Retain the P3e 180 steps at dt=1/60, physical capacity 600, render capacity
9600, physical source rate 180/s, three layers, eps=0.07, wind=0, turb=0,
optical radius 0.045, tau=0.2, RGBA32F accumulation, and all other physical,
render, source, birth, cooling, density-decay, boundary, and retirement rules.
Keep separate unchanged physical and render random streams. Neither selector
may consume either stream. No model or physics change is part of P3f.

## Unchanged grouping and local models

Partition each arm's own current tracer inputs after that step's births and
before integration. For N>0, K=min(600,ceil(N/16)); for N=0 there are no groups.
Recursively split by largest coordinate range, with equal ranges choosing
x before y before z. Sort on that coordinate then ascending stable birth ID.
With k requested leaves, leftK=floor(k/2), rightK=k-leftK, and
cut=floor(memberCount*leftK/k). Visit the left child first. At a leaf, sort
members by stable ID and sum positions in that order to obtain its centroid.
Group IDs are the canonical depth-first leaf numbers. This is proportional
longest-axis splitting, not ordinary median splitting. Do not reorder the
production tracer array.

Every group in both corrected arms receives all seven original raw queries,
in order center,+x,-x,+y,-y,+z,-z, with delta=eps/8=0.00875. They use the same
frozen pre-integration physical tree and original full field kernel, traversal,
normalization and LUTs. Retain the original centered velocity Jacobian and Tb
gradient. Unselected members use the original affine reconstruction, including
Tb clipping to [0,1.6], external forces at the actual old position, and exactly
one final speed clamp. Selected members use a full direct raw query at that
actual position and the same external-force/speed-clamp calculation as DD.
Do not affine-clip the directly queried Tb or otherwise modify DD arithmetic.

All velocities are determined before member integration. Keep the original
Euler, visual T/d/life evolution, z clamp, and retirement rules. Construct no
persistent carrier identity, deformation/covariance update, residual-driven
split, temporal model reuse, or new physical state. Existing uncorrected DD
and affine paths must remain numerically unchanged.

## Frozen score and arithmetic order

For each of the seven stored raw query records define the vector
q=(ux,uy+buoy*Tb,uz). This includes the unchanged buoyancy coefficient and raw
normalized Tb. It is before reconstructed-Tb clipping and the speed clamp.
Wind and curl are zero in the frozen stationary condition. This score is a
heuristic for variation in the numerical pre-clamp transport field, not an
error bound; later clamp/support exposure must be recorded rather than assumed
absent merely because P3e did not encounter it.

For component r and axis a, use the exact scalar operation order

    H[r*3+a] = ((q_plus[r] - 2*q_center[r]) + q_minus[r]) / (delta*delta)

where plus/minus are the corresponding stored stencil entries. These are
three diagonal second differences per component; mixed derivatives are not
estimated. They may also reflect tree/LUT nonsmoothness, so do not call H the
analytic Hessian of a physical velocity field.

For each member in ascending stable-ID order, form dx=x-center.x, dy and dz
analogously, and xx=dx*dx, yy=dy*dy, zz=dz*dz. For each output component r:

    residual_r = 0.5 * ((H[r*3]*xx + H[r*3+1]*yy) + H[r*3+2]*zz)

Form memberScore by first adding residual_x*residual_x and
residual_y*residual_y, then adding residual_z*residual_z. Accumulate
score += memberScore sequentially in that ID order. Both corrected policies compute this same score for all
groups. Do not change multiplication/addition association, use a vectorized
reduction with a different order, or tune a weighting after seeing results.

Select M=ceil(0.1*K) groups for K>0, otherwise zero. Compute integer K first
and then multiply by 0.1; do not reassociate this as 0.1*3*frame, whose
floating-point rounding can change ceil at integral boundaries. Curvature sorts by
descending score, then ascending canonical group ID on an exact score tie.
Use the fixed fraction 0.1 even if a different fraction would pass the gate.
Nonfinite score/query/state is an implementation validity failure.

## Frozen uninformed hash ranking

The dedicated salt is 0xa511e9b3. Let frame be the one-based completing frame
(the runtime's s.frame+1 before completing that step), and minBirthId the
minimum stable birth ID in the group. Use JavaScript 32-bit integer arithmetic
exactly as follows; imul means Math.imul, and >>> is unsigned right shift:

    h = (salt ^ imul(frame+1,0x9e3779b9)
              ^ imul(minBirthId+1,0x85ebca6b)) >>> 0
    h = imul(h ^ (h >>> 16),0x7feb352d) >>> 0
    h = imul(h ^ (h >>> 15),0x846ca68b) >>> 0
    rank = (h ^ (h >>> 16)) >>> 0

Sort by ascending unsigned rank, then ascending canonical group ID for equal
ranks, and select the first M groups. Freeze this salt and formula before
new-seed execution. Do not use a physical/render random draw, the reference
errors, or any post-hoc selection of a favorable salt.

The API for corrected affine modes is
field.correction={method:'curvature'|'hash',fraction:0.1,salt:0xa511e9b3},
in addition to the unchanged field.affine configuration. The API may support
other fractions, but formal P3f uses only this fraction and salt. Omitted
correction retains the original affine method and its regression schema.

## Equal-query mechanism control and actual costs

Let selectedN be the number of members in the selected groups. Each corrected
arm must perform exactly 7K model raw queries plus selectedN direct member raw
queries per step. Unselected members use reconstruction. Selected groups still
pay for all seven model queries. Record actual selected groups, member IDs,
counts, and both classes of query work. Do not conflate corrected direct member
requests with affine reconstructions or diagnostic queries.

With unchanged births and no tracer retirement, N=48*frame, K=3*frame, every
group has 16 members, and selectedN=16*ceil(K/10). The 600-group limit is not
reached: final K=540. Thus the two corrected arms have exactly equal raw-query
counts on every frame. The nominal continuous fraction is 7/16+0.1=0.5375
of DD's requests; report the exact integer-rounded counts rather than treating
that approximation as a measured speedup. For all 180 steps, the expected
model query count is 342,090 and selected-member direct count is 79,488,
total 421,578, when there is no retirement/blocking.

Check equal N, K, M, selectedN, and total raw-query requests separately at every
frame for curvature versus hash. A render retirement or missing identity can
change subsequent group populations and destroy the equal-budget comparison.
Such an outcome is a scientific allocation/quality STOP, not automatically a
software exception: finish all seven quality trajectories and record it.
Do not claim superiority from an intersection-only comparison after losing
particles. In contrast, an arm violating its own 7K+selectedN work ledger is
an implementation failure requiring diagnosis.

The no-retirement condition refers to render tracers. Native physical particles
retain their original lifecycle, which must match exactly between methods at
the same seed. Preserve native source/capacity and optical injection rules.

Equal raw-query counts do not imply equal traversal work or wall time, because
query locations differ. Record tree leaf/cluster/thermal work and actual costs.
The hash arm could in principle know selected groups before model evaluation
and skip their unused models. Here it deliberately shares the full 7K model
pipeline to isolate the allocation choice. It is therefore a mechanism control,
not the fastest possible hash-based algorithm. Do not use its avoidable work to
claim competitive algorithm speed. The primary speed denominator is DD.

## Production observations and complete quality records

Save the existing physical/birth trace and full tracer hash at frame zero and
all 180 steps for each of seven trajectories. Verify same-seed physical state,
physical/render random progress, and births across methods. Save 13 ID-ordered
Float64 particle checkpoints at frames 0,15,...,180 per trajectory: 91 files.
Save six linear RGBA32F captures per trajectory at frames 90 and 180, yaw
0,0.7,1.4, resolution 256x192: 42 images. Preserve SHA256 metadata, complete
raw files, checkpoint snapshots, and browser errors. Dense hashing/readback is
quality evidence and must not be inserted into timed frames.

For the four corrected trajectories, observe actual production inputs and
selection details at frames 15,30,...,180 with
stepWithInputs(dt,{stride:1,correctionDetails:true}). Retain these 48 detailed
observation records with SHA256. The observer captures inputs after births and
before integration and reports the actual production models and ranking, not
a separately reconstructed approximation on reference positions.

The returned correctionSelection contains summary/config/delta/fieldTime,
models with their original stencil and diagonalHessian/score/hashRank/selected
fields, rankedGroupIds, selectedMemberIds, and directQueries with stable ID,
group ID, old position, raw field and final velocity. Those direct records
come from the actual selected-member production requests. No extra DD oracle
query is permitted for this observer. Unselected points have no newly measured
direct reference field; do not fabricate one from the local model.

Keep a compact selection/work trace for all 180 production frames to check
per-frame budget equality and grouping/selection counts. Detailed observation
must not consume RNG, alter model arithmetic, change query order, add field
queries, or affect subsequent states. Validate observer-on/off equivalence in
smoke tests. Outside timed intervals, verify hashes/counters after observation.
Ordinary timing runs retain no full models/diagnostic arrays merely for later
analysis. All production work needed to score, rank, query and advect must
nevertheless be included in completed-frame timing.

Independent checks should reconstruct the weighted partition, seven-query
layout, scalar H/score arithmetic, uint32 hash, rankings, exact selected member
set, direct query positions, force/clamp order and member state updates from
the recorded actual inputs. Check cases with score/hash ties and stable IDs,
and verify exact query ledgers and unchanged default paths.

## Immutable P3e regression

The previous P3e delivery archive SHA256 is
`8732952c34a9e4755ba92842ea9c19cf48fe2496cc319d56ac8aec38de1b53a4`.
Authenticate its manifest and old stationary DD/affine 11/101 raw JSON records
through pins obtained directly from that archive. Verify the archive checksum
when the archive is supplied. Do not substitute evolving newly generated files
for the old reference. Verify the baseline and source fingerprints at both ends
of the formal run.

The two replayed old methods must match their archived 181-step physical/birth
traces and tracer hashes, all 13 particle checkpoint hashes, six raw image
hashes, and applicable old snapshot fields. Verify all new raw bytes; verify
old binaries when available, and explicitly identify absent old binaries in a
portable authenticated-record-only package. Do not imply absent bytes were read.
New instrumentation fields may be additional metadata but must not change any
old numerical state or old counter semantics.

## Accuracy, selector comparison, and conditional timing gate

Compare curvature and hash separately against their paired DD trajectory for
each seed. Report all unmatched IDs and optical weights. Matched visual T, d,
life and optical weights must remain exact. Preserve physics/birth/source
invariants and zero source/render capacity blocking. Nonfinite states, missing
files/frames, changed physics, or failed immutable regression are validity
failures, not successful negative experiments.

The existing deployed accuracy thresholds remain unchanged: every nonzero
checkpoint position RMSE<=0.007 and p99<=0.035, foreground RGB NRMSE<=0.05
and alpha NRMSE<=0.05 pooled over the six images, no unmatched identities and
unchanged visual evolution. Each DD image defines foreground by alpha>0.01.
Pool squared errors and reference signal energies before normalization; do not
average per-image RMSE. Use the established sorted-sample quantile at
floor(q*(n-1)). Initial empty checkpoints must not lower nonzero error summaries.
Full-frame errors remain descriptive. These targets are engineering screens,
not physical/perceptual ground truth.

Only after all seven trajectories and regression/observation evidence are
complete, permit timing if ALL of the following hold:

1. Curvature passes the unchanged accuracy/invariance gate on each seed pair.
2. Separately for each seed, curvature's maximum over the 12 nonzero checkpoint
   position RMSE values is strictly below hash's corresponding maximum, AND
   its maximum checkpoint p99 is strictly below hash's corresponding maximum.
   These are two maxima, not necessarily from the same checkpoint. Do not pool
   seeds, average away a failure, or substitute a pooled trajectory p99.
3. Both corrected arms preserve complete matching render identities, no render
   retirement, and equal raw-query budgets at every frame for that seed. Both
   arm-specific query ledgers are valid. The hash arm may fail a numerical
   accuracy threshold, but may not win or lose this comparison through missing
   identities or a different budget.
4. Immutable regression and all source, configuration, file and population
   validity checks pass.

Strict numerical improvement is a predeclared selector screen, not statistical
significance or a guarantee of meaningful improvement. Report continuous effect
sizes. A single hash salt supplies one controlled allocation comparison only.
No instantaneous field-error proxy, division-by-horizon surrogate, or later
post-hoc diagnostic can override these actual trajectory/image conditions.

If a scientifically valid quality/selector/budget condition fails, preserve all
seven trajectories and record timing skipped with the exact failed conditions.
The protocol may be complete and execution status passed while engineeringGo
is false. Missing or invalid evidence must instead be identified as incomplete
or execution failure. Keep the planned ten timing cases visible even when
skipped. Do not run performance trials to rescue failed accuracy or selection.

## Conditional timing on the old pair only

If permitted, compare DD and curvature at old pair 11/101 using five independent
page/reset runs each, ten runs total. Use order DD/curvature, curvature/DD,
DD/curvature, curvature/DD, DD/curvature. This five-repeat 3:2 order is not
perfectly position-balanced. The hash arm is not a primary speed baseline.
No claim about timing on the new seed follows from this old-pair measurement.

Use 20 warmup frames, reset, and replay the full 180 steps. Sample every third
frame from 60 through 180 inclusive, 41 samples per run and 410 total. This is
a warmed fixed simulation-time window with growing load, not steady state.
Use the existing gl.finish completed-frame wall-time protocol, draining prior
GPU work before measurement. Include physics, grouping/sorting, all model
queries, H/score construction, ranking/hash work, selected direct queries,
unselected reconstruction, integration, upload/draw and GPU completion.

Exclude dense state hashing, full observation serialization, extra probes and
pixel readback from the timed interval. The lightweight physics/birth lock is
outside it. Check initial/final physical/tracer hashes, populations, counters
and relevant field state against the same-method quality run outside timing.
Camera-only parameters need not match. Preserve all raw frame times and stage
work, including the actual direct correction cost.

Central latency is median of the five per-run frame medians. Tail is median
of the five per-run frame p95 values, not pooled-frame p95. Quantiles use
floor(q*(n-1)); retain all five run summaries. Stage arithmetic means explain
cost but do not replace these decision statistics. Correlated frame samples
are not independent repeats.

Engineering success additionally requires central_latency_DD divided by
central_latency_curvature>=1.5 and tail_curvature<=tail_DD, measured within
this same P3f timing matrix. Old times and raw-query reductions are context,
not speed evidence. Failure stops this fixed candidate; do not add another
fraction or salt after observing it.

## Interpretation limits

A positive result would show bounded usefulness of one query-allocation rule
on the old condition and one new seed, plus old-pair/device timing. It would
not establish statistical superiority over random policies, a general error
bound, analytic differentiability, physical fidelity, conservation, divergence-
free transport, persistent carrier/covariance deformation, scene combustion
feedback, late ignition or long-time stability. It is not a novelty or paper
acceptance claim. A negative result rejects this fixed allocation/correction
construction under its targets, not every adaptive representation.

The prior P3e outcomes and post-hoc diagnostics remain unchanged. Future fresh
validation, alternative selectors or budgets require a separately frozen phase;
they must not be folded into P3f as if predeclared.
