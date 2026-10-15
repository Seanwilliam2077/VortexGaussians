# P3e: bounded local affine field reconstruction

Status: frozen before P3e quality or timing outcomes. This is a small,
exploratory test of one fixed construction after P3d. No budget, difference
scale, grouping rule, condition, seed, or threshold may be selected in response
to its results. Correctness repairs must preserve this contract.

## Question and scope

Can rebuilding local first-order approximations to the numerical velocity and
temperature fields reduce dense tracer query cost while retaining the prior
trajectory and image accuracy targets?

There are two production arms: **DD**, the existing full direct-tree query at
every tracer, and **affine**, the construction below. An additional read-only
diagnostic constructs the same approximation at DD's actual pre-integration
positions. It is not a third deployed trajectory, an optimal oracle, or a
theoretical error bound. No DD diagnostic value can correct the affine arm.

The groups are rebuilt from current tracer positions on every step. Their
centroids have no persistent carrier identity or independently integrated
deformation. This phase implements neither deformation of Gaussian covariance
nor a persistent local flow map. Its central differences are derivatives of the
existing numerical field at a finite scale, not an analytic Jacobian.

Use only the previously observed stationary condition, physics seed 11 and
render seed 101, for 180 steps of dt=1/60. This is not fresh held-out evidence.
Keep physical capacity 600, render capacity 9600, source rate 180/s, three
physical layers, eps=0.07, wind=0, turb=0, and all remaining P3d parameters.
Keep the same render emission rate, optical weights, radius 0.045, tau=0.2,
RGBA32F accumulation, visual cooling/density decay, retirement, depth clamp,
native physics, tree-opening criterion, kernels, and LUTs.

## Frozen partition and local model

After the step's tracer births, before any tracer integration, partition the
arm's own live tracer positions. Do not reorder the production tracer array or
consume either random stream. Stable tracer IDs, rather than transient array
indices, break coordinate ties.

For N>0, request K=min(600,ceil(N/16)) leaves; N=0 produces no groups or field
queries. Recursively partition a node containing N members and requested K
leaves as follows:

1. If K=1, emit a leaf. Otherwise choose the axis with greatest coordinate
   range; equal ranges select x, then y, then z.
2. Sort that node's members by the chosen coordinate, then ascending stable ID.
3. Set leftK=floor(K/2), rightK=K-leftK, and
   cut=floor(N*leftK/K). Recurse on the first cut members with leftK and the
   remaining members with rightK, visiting the left child first.
4. Assign leaf/group numbers in this depth-first order. Within each leaf, sum
   positions in ascending stable-ID order and divide by its membership count
   to obtain the centroid.

This is longest-axis splitting proportional to the requested leaf counts,
not ordinary median splitting. Freeze its arithmetic and tie rules. The
target group size is a budget rule, not an unrestricted guarantee for every
possible N once the 600-group cap binds.

For each centroid c, use delta=eps/8=0.00875 and query the same frozen
pre-integration tree seven times, in this exact order:
c, c+delta*x, c-delta*x, c+delta*y, c-delta*y,
c+delta*z, c-delta*z. Each request is the existing full raw query returning
induced velocity and normalized dynamical Tb, before external forces and the
speed clamp. Retain query thermal support as diagnostic data only.

For each velocity component a and coordinate b, form
J[a,b]=(u_a(c+delta*e_b)-u_a(c-delta*e_b))/(2*delta).
Use the analogous three central differences for grad(Tb). At each member's
actual old position x, reconstruct
u_hat=u(c)+J*(x-c) and Tb_raw=Tb(c)+grad(Tb) dot (x-c).
Use Tb_hat=max(0,min(1.6,Tb_raw)) in the production force calculation. Record
raw values outside [0,1.6], their counts and maximum clipping magnitudes.
The original physical Tb is limited to [0,1.6], with ordinary Float32 storage
rounding in the tree; [0,1] is not its range. Do not add local seven-point
min/max limiting or reconstruct a fictitious thermalWeight.

At the actual tracer position, combine reconstructed induced velocity and
clipped Tb with the unchanged buoyancy, wind/source motion, and procedural curl
terms. Apply the existing speed clamp once, then the unchanged Euler update,
visual cooling, density decay, depth-boundary rule, and retirement test. All
model queries use the same pre-integration tree/time level as DD, and the
external forcing uses the existing forcing-time convention. Do not cache a
model across simulation steps. Do not add residual-driven splits, extra
queries, reference corrections, or a direct fallback in this phase.

The API is field.mode='affine' with
field.affine={maxGroups:600,targetGroupSize:16,deltaScale:0.125}; it supports
the full induced-velocity/Tb construction only (both components, combined
evaluation). Preserve existing tree/grid defaults and their numerical paths.

## Cost exposure and correctness checks

With the unchanged births and no retirement/blocking, this fixture emits 48
tracers per step and ends with N=8640 and K=540. The 600 cap is not reached.
For the 180 production steps, expected member evaluations total 781,920,
groups total 48,870, and seven-query model evaluations total 342,090.
Here N is a multiple of 16, so the proportional split produces groups of 16.
These are exposure/ledger checks, not performance measurements or evidence
that queries at different positions have equal cost.

The nominal full-query count becomes 7/16 of DD's. Count and time all required
partitioning/sorting, centroid calculation, allocations, seven raw queries,
difference/model construction, member reconstruction, forces, integration,
and rendering. No group maintenance, derivative calculation, or allocation is
free preprocessing. Record actual leaf/cluster/thermal work as well as request
counts; changed query positions can change tree traversal cost.

Before formal execution, check empty/small/non-divisible populations, exact
requested leaf counts, deterministic coordinate ties, stable-ID input
permutations, and preservation of the production array/order. Synthetic
constant/affine fields must establish central-difference orientation and
reconstruction arithmetic; exercise Tb clipping and the force/clamp order.
Observer/diagnostic calls must leave physical state, tracer state, RNG progress,
production counters, and subsequent production results unchanged. Numerical
or ledger failures are implementation failures, not evidence against the model.

## Quality evidence: two complete trajectories

Run DD and affine for the entire 180-step horizon before deciding accuracy.
Do not stop quality collection at the first failed accuracy checkpoint. Save
the existing full tracer hash and physical/birth-RNG trace at frame 0 and every
step thereafter: 181 entries per arm. Hash generation is outside performance
measurement. DD and affine must have identical physical trajectories and birth
streams; their render positions, velocities, sampled Tb, and tracer hashes are
allowed to differ as consequences of the approximation.

Save ID-sorted Float64 particle tables at frames 0,15,...,180: 13 per arm,
26 total. Keep the existing full table schema, SHA256, and checkpoint snapshots.
Capture frames 90 and 180 at yaw 0,0.7,1.4, resolution 256x192: six linear
RGBA32F files per arm, 12 total. PNGs are previews; quantitative comparisons
use raw linear images. Camera changes and diagnostics must not change physics
or tracer state. Save the DD foreground masks and their hashes.

DD must reproduce the matching stationary 11/101 DD evidence from the immutable
P3d delivery archive, SHA256:
`1c486850a886e5291d7b1aa6e1ce125b3988d694064c4c38f75920fffd72bc44`.
Authenticate the old manifest and matching raw record against that archive or
pins obtained directly from it. Compare all 181 tracer hashes and physical/birth
trace entries, the 13 particle checkpoint hashes, six raw image hashes, and
applicable old snapshot fields. Do not substitute a newly generated baseline.
Verify actual new binary files. When old binaries are available, verify them
too; a portable record-only baseline must explicitly identify any unavailable
old binaries and rely on authenticated recorded hashes rather than imply that
absent bytes were read. Record the complete provenance of the baseline used.

For every checkpoint, report unmatched live IDs and their optical weight;
do not hide them by comparing only an intersection. For matched identities,
visual T, density d, life, and optical weight must remain exact. Verify equal
source/render emission counts and credits, physical/render RNG progress, and
zero source/render capacity blocking. Missing identities, nonfinite state,
invalid binary/hash evidence, or altered physics invalidate the comparison.

The unchanged accuracy gate is:

- Every nonzero checkpoint's matched-ID position RMSE <=0.007 and position
  error p99 <=0.035, with complete matched identities.
- Foreground RGB NRMSE <=0.05 and alpha NRMSE <=0.05, pooling squared errors
  and DD signal energies over all six captures before taking the ratio/root.
  Each paired DD image defines its foreground by alpha>0.01. Do not average
  per-image RMSE values and call that pooled RMSE.
- All physical/birth/source/visual invariants and complete-evidence checks pass.

The initial checkpoint is an identity check, not a zero-error sample used to
lower the nonzero-checkpoint gate. Preserve the established quantile convention
floor(q*(n-1)) for sorted error samples. Report full-frame image errors as
additional context. These numerical engineering targets are not physical or
perceptual ground truth.

## Read-only DD-position diagnostic

At each of frames 15,30,...,180, DD captures all actual tracer inputs after that
step's births and before any tracer integration, using stride=1. Capture stable
ID, position, pre-integration age, newborn status, frame, and field time.
Immediately query the still-frozen corresponding pre-integration tree. Build
the same partition/model with the same shared production functions on these
DD input positions, and compare reconstructed fields against direct queries at
every input point. Include the same external forces at the same position/time
and the same single speed clamp for the final-velocity comparison.

The 12 diagnostic sets contain 56,160 positions, 3,510 groups and 24,570
seven-point model queries under the exposure above, plus 56,160 direct reference
queries. Preserve all 12 detailed diagnostic files with SHA256 and list them
in the manifest. Separate model/reference query counts and production counts.
Use private diagnostic storage/counters and restore shared scratch state.
These extra direct queries are diagnostic only, never feedback to production
and never part of timing runs.

Report per-checkpoint and correctly pooled induced-velocity error, signed/RMS
Tb error before and after clipping, and total transport-velocity error after
forces/clamp. Retain group geometry/radius, query support, raw Tb clipping, and
speed-clamp exposure needed to interpret discrepancies. Do not infer a point's
thermal support from an affine reconstruction of support weight: none exists.
Distinguish unsupported stencil/model query sites from unsupported direct
reference points.

These same-position errors help distinguish field reconstruction discrepancy
from accumulated trajectory differences and changed group memberships. They
are explanatory measurements only: there is no additional instantaneous-error
STOP threshold. In particular, dividing the position tolerance by three
seconds does not provide a necessary condition or an accumulated-error bound.
Do not use the diagnostic as a theoretical oracle or as a substitute for the
actual trajectory/image gate.

## Conditional timing: ten independent runs

Only after both complete quality trajectories, immutable DD replay, complete
diagnostics, and the actual accuracy gate pass, run five independent page/reset
repeats of each method, ten timing runs total. Retain the planned ten cases in
the manifest even when skipped. A valid completed quality failure records
stageStatus='stopped_after_quality', a timingSkipped reason and the failed
quality gate, protocolComplete=true, and engineeringGo=false. It may still have
execution status='passed': valid negative evidence is not a software failure.
Incomplete or invalid quality evidence cannot be recorded as a completed valid
negative result. Do not run formal performance trials to rescue failed quality.

Use repeat order DD/affine, affine/DD, DD/affine, affine/DD, DD/affine.
This five-repeat 3:2 ordering is not perfectly position-balanced. Each run
performs 20 warmup steps, resets, and replays frames 0 through 180. Sample every
third frame from frame 60 through 180 inclusive: 41 samples per run, 410 total.
This is a warmed fixed simulation-time window with growing tracer load, not
steady state. Match simulation frames across arms.

Use the existing completed-frame wall-time protocol: drain previous GPU work,
measure the whole production frame, then gl.finish(). Include physical stepping,
all affine construction/query/reconstruction costs, integration, upload/draw,
and GPU completion. This is not pure GPU timing. Retain stage costs, workload
counters, and all raw frame times.

No dense tracer hash, snapshot serialization, all-point input observer,
diagnostic field query, particle transfer, screenshot or pixel readback may
enter a measured frame. The existing lightweight physics/birth trace is outside
the interval and must not traverse dense tracers. Initial/final state and
quality-versus-timing production-equivalence checks occur outside timing.

For each run, take frame median and p95 from sorted samples at index
floor(q*(n-1)). Central latency is the median of five per-run frame medians;
tail is the median of five per-run frame p95 values, not pooled-frame p95.
Retain all five run summaries. Correlated frames are not independent repeats.

Engineering success requires complete valid quality evidence and, in this
single condition, central_latency_DD/central_latency_affine >=1.5 and
tail_affine<=tail_DD. Both timing arms must come from this same experiment;
old P3d times are context only. Stage arithmetic means explain costs and must
not be substituted into the repeat-aware decision. Failure of either accuracy
or conditional cost gate stops this frozen construction. Do not add budgets,
change delta, select another seed, relax thresholds, or switch grouping rules
after seeing the result.

## Interpretation limits

Negative evidence rejects this construction under this workload and targets,
not every first-order representation or every method using at most 600 groups.
The group cap is not exercised here. A difference from DD combines field
approximation, finite-difference/LUT/tree-boundary effects, regrouping, thermal
clipping, and trajectory feedback; diagnostic correlations alone do not
establish a unique physical cause.

A positive result is only a bounded feasibility result on one already observed
short condition/device. It establishes neither fresh generalization, physical
realism, divergence-free reconstruction, conservation, covariance deformation,
scene combustion feedback, late ignition, long-time stability, nor a publication
novelty claim. Standard local linearization alone is not the proposed research
contribution. Any later confirmation needs newly frozen conditions and seeds;
the already observed stationary 11/101 pair must never be renamed held-out.
