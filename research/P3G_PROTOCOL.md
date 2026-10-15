# P3g: one-step reuse of directly observed local-model residuals

Status: FROZEN before P3g outcomes. Root approved the method, evidence matrix,
comparison rule and conditional timing below. No P3g outcomes have been used.
API field-name clarifications may align this text with the implementation,
but may not change the method, evidence requirements or decision rule.
Do not change P3f evidence.

## Question and scope

At the same field-query budget, can one-step reuse of a tracer's previously
observed direct-minus-affine residual improve deployed transport relative to
the stateless P3f curvature allocation? This tests one concrete temporal
reuse construction. It does not assume that discarding previous corrections
caused P3f's accumulated drift.

P3f established an improvement over one fixed hash allocation at equal raw
query counts, but both tested seeds still failed the original absolute
trajectory thresholds. Its image gates passed. Those facts do not establish
temporal smoothness of residuals, validity of a material-memory model, or
causality for the remaining error. P3g must test the new hypothesis directly.

The six full quality trajectories, in execution order, are:

1. stationary-DD-s11-r101
2. stationary-curvature-s11-r101
3. stationary-memory-s11-r101
4. stationary-DD-s83-r521
5. stationary-curvature-s83-r521
6. stationary-memory-s83-r521

The old DD and curvature trajectories also provide full immutable P3f
regression; no seventh quality trajectory is required. Seed pair 11/101 is
previously observed development evidence. Pair 83/521 has no prior run file
in the research runs checked before freezing and is one new-seed transfer
check in the same stationary condition. Do not describe it as a new scene
or multiple independent held-out settings. Freeze the method before its run.

Collect all six trajectories even if an earlier one fails the numerical
quality/comparison screen. Do not add another TTL, fraction, seed, salt,
difference scale, or interpolation variant in response to an outcome.

## Fixed physical, visual, and stateless construction

Keep the P3f settings: 180 steps at dt=1/60; physical capacity 600; render
capacity 9600; physical source rate 180/s; three layers; eps=.07; stationary
wind=0 and turb=0; optical radius .045; tau=.2; RGBA32F accumulation. Preserve
all births, random streams, physical evolution, cooling, visual T/d/life,
source and optical measure, boundary rules, and retirement conditions.

Use each candidate's own post-birth, pre-integration tracer positions.
K=min(600,ceil(N/16)). Partition by the P3f proportional longest-axis rule,
with x/y/z tie order, coordinate-then-stable-ID sorting, target leaf counts,
and stable-ID centroid summation. Do not reorder the tracer array. Rebuild
groups each step; they remain nonpersistent local models, not deformation
carriers or Gaussian covariance updates.

Retain the seven raw queries per group at center,+x,-x,+y,-y,+z,-z, with
delta=eps/8=.00875, centered differences, and the same frozen pre-integration
physical tree. Preserve the P3f score arithmetic, deterministic curvature
ranking, group-ID tie break and M=ceil(.1*K), with integer K evaluated first.
Both curvature and memory compute all 7K model queries and selected-member
direct queries. The selected members use the actual raw direct field, as DD
does; a selected member is never transported by an old residual instead.

The memory arm keeps the same selection rule, but its changed positions can
change subsequent groups, scores and selected identities. Equal query counts
do not imply identical selections. This is a comparison of two deployed
methods, not a fixed-selection-sequence intervention that isolates only one
arithmetic operation throughout the trajectory.

## Residual definition and exact TTL semantics

For a selected stable birth ID i in completing frame f, evaluate the original
unclipped affine model at its actual pre-integration position, using the
model and tree from this same frame. Let a_u be its affine induced velocity
and a_Tb the affine temperature before any clipping. Let d_u,d_Tb be the
actual direct raw query already required for its selected-member transport.
Create the record:

    creatorFrame = f
    residualU = d_u - a_u
    residualTb = d_Tb - a_Tb

Store the three induced-velocity residual components and the scalar Tb
residual separately. This is not a post-speed-clamp velocity difference,
not a visual-temperature residual, and not an error against a DD trajectory
at another position. No extra direct query is used to create it.

The opt-in configuration is correction.memory={ttl:1}, allowed only with
curvature correction. Omitting it retains the exact stateless path and old
schema. Use two distinct maps during a step. Read only the previous step's map;
write only a fresh current map. Selected members always take the current
direct field and write a new residual. An unselected member may read an
entry only when its stable ID matches and creatorFrame==f-1. Then:

    reconstructedU = currentAffineU + oldResidualU
    reconstructedTbRaw = currentAffineTbRaw + oldResidualTb
    reconstructedTb = clamp(reconstructedTbRaw, 0, 1.6)

If there is no eligible entry, use the original unselected affine path.
After this choice, apply external forces at the actual current position and
perform the unchanged single final speed clamp. Do not apply the affine
temperature clip to selected direct values. Do not clip before adding the
stored temperature residual. Preserve the old affine evaluation order:
origin + J0*dx + J1*dy + J2*dz, with left-associated additions, separately
for each u component and Tb. Residual creation is direct minus that value;
reuse adds the stored component once to the corresponding new affine value.
The final temperature operation is max(0,min(1.6,reconstructedTbRaw)).

An unselected member that reuses a residual does not write that residual
to the current map. Thus reuse cannot refresh or propagate its lifetime.
A selected member's new direct query may create a new record even when it
had a prior record. At the end of the step replace the map, discarding old
records. Keep a current selected record even if its tracer retires later in
this same integration step; count it as previousMissing in the next step.
First-frame and newborn members have no historical correction.
Stable birth IDs, not array indices or temporary group IDs, define identity.

Residuals refer to a previous position, numerical tree, local model and
grouping. Treating them as constant for the next step is the hypothesis,
not a derived transport law. No Jacobian transport, interpolation in time,
decay, repeated refresh, neighborhood sharing, or extra TTL is included.

## Query budget, populations, and real costs

For each arm, every frame must obey fieldQueries=7K+selectedN. Residual
creation adds selected-member affine reconstruction and map operations,
but no raw field request. Residual lookup/use adds arithmetic and memory
work. Count this work separately; include all of it in any permitted timing.
Do not count a selected-member residual-baseline evaluation as the deployed
unselected reconstruction or as another direct field query.
The extra selected evaluation is memoryModelEvaluations, equal to the
number of selected direct queries; affineReconstructions retains its old
meaning and counts unselected members only.

Compare curvature and memory actual N,K,M,selectedN and query counts at
every frame. With the unchanged fixture and no render retirement, N=48*f,
K=3*f, every group has 16 members, and the expected total is 342,090 stencil
queries plus 79,488 selected direct queries, or 421,578 per corrected arm.
The final K is 540, so the 600-group capacity is not exercised.

The no-retirement comparison rule refers to render tracers. Native physical
particles retain their original lifecycle and must match exactly at equal
physical seed. Source/render capacity blocking, missing IDs, or different
actual query budgets cannot be hidden by comparing only common particles.
An otherwise valid budget/population difference is a scientific comparison
failure, not automatically a software exception; retain all six trajectories.
An arm violating its own work ledger is an implementation validity failure.

Equal raw requests do not imply equal traversal work or wall time. Positions
and selected groups can differ. Record tree work and the extra residual
creation, bookkeeping, lookup, and reconstruction costs. Compare a usable
implementation's eventual speed to DD, not just to the stateless control.

## Required exposure and memory evidence

Maintain a compact trace for every completing frame, not just the image
times. Let P be previous saved IDs still present among this step's inputs,
S be current selected IDs, and U current unselected IDs. Record at least:

- previous stored records, eligible live records, and records with missing IDs;
- P intersect S (direct takes priority / current residual replaces the old one);
- P intersect U (the actual reuse population), equal to eligible reuse count;
- newly selected IDs without prior history, current saved records, and
  discarded/expired records under explicitly documented definitions;
- saved and reused residual induced-u squared norm, maximum norm, Tb squared
  magnitude, signed Tb sum, maximum absolute Tb, and finite-state checks;
- reused fraction among all inputs and among unselected inputs, plus counts
  of final Tb clipping and final speed clipping.

Do not count a selected member with previous history as a reuse: current
direct has priority. Do not label all previous entries expired when some
were replaced by a new direct observation without defining that convention.
State a partition of previous-map records so totals cannot double-count.
The stateless arm should not secretly carry an unused persistent map.
For this TTL1 rule the accounting identity is previousMembers =
overlappingMembers + reusedMembers + previousMissing, with
previousLiveMembers = overlappingMembers + reusedMembers. All prior stored
records must have creatorFrame=f-1. SavedMembers is current selectedN,
including any members retired later in the current integration step.

The same budget can still yield too little actual reuse if selections persist.
Require at least one actual reuse in each memory trajectory; beyond this
predeclared nonzero-exposure check, report exposure continuously and do not
invent a favorable post-outcome minimum or rescue a failed quality gate.
Low exposure limits interpretation of a
negative result to this particular construction, rather than falsifying all
temporal reuse methods. Nonzero exposure alone does not prove useful reuse.

For each memory creation, retain enough provenance to reconstruct its actual
production direct-minus-unclipped-affine value and link each later use to
the same stable ID and exactly preceding creatorFrame. A saved scalar
residual alone is not independent evidence of where it came from. The
required record includes source position, group ID, actual unclipped affine
and direct raw values, the four residual components and creator frame.
Each per-frame memoryEvents file contains a dictionary of all relevant
production models, including center, member IDs, seven-query stencil,
Jacobian and Tb gradient. Group models are shared by ID to avoid duplicating
them for each event. Retain full cacheBefore and cacheAfter lists. Creation
and use events must link through those lists across frames, including the
four stored values exactly and mandatory expiration without refresh.

Every reuse record must retain its current raw affine input, linked saved
residual, combined raw result, final clipped Tb and applied velocity, enough
to reproduce force/clamp and Euler updates at the detailed checkpoints.
The formal observer reads actual production work and adds no DD oracle
queries. It must not consume RNG, update maps, affect query order, or change
arithmetic. Use stepWithInputs with memoryDetails:true for all 180 steps of
both memory trajectories. Write 360 memoryEvents JSON files with SHA256.
Retain 48 full selection JSON records at the 12 nonzero checkpoints for
curvature/memory across both seeds. Full global partition and centroid
reconstruction are required at those 12 checkpoints; on other frames,
reconstruct the involved models' stencil layout, differences and values at
actual event positions, without claiming an independent whole-population
partition check when the other inputs were not saved.

## Quality, state replay, and immutable baseline

Retain 181 physical/birth traces and full tracer hashes per quality run.
Stateful memory also needs an independently visible deterministic map-state
hash/record at each step: identical current particle arrays alone cannot
prove identical future state. Include stable ID, creatorFrame and residual
values in a canonical order. Reset must clear map state and counters.

Retain 13 ID-ordered Float64 checkpoints and six linear RGBA32F images per
trajectory (frames 90,180; views yaw 0,.7,1.4; 256x192): 78 particle files
and 36 HDR images plus their PNG previews total. Keep original 12 nonzero detailed selection checkpoints
for both corrected methods, alongside the memory provenance above. Verify
matching visual T,d,life, optical measure, same-seed physical/birth/RNG
sequence, and camera noninterference with current and future state.
Retain both fixed foreground and hole masks for each DD capture, 24 mask
files total. Hash canonical memory entries in stable-ID order, separately
from the existing tracer hash, and preserve full entries in detailed state.
For portable hash encoding only, canonicalize either signed zero to +0,
then encode each residual as little-endian Float64 hex. The format is
fnv1a32-json-id-frame-residualF64LE-zero-canonical-v1. Production arithmetic,
stored residual values and cache state are unchanged by this encoding rule;
it avoids JSON's loss of a negative-zero sign creating a false replay error.

The previous P3f ZIP SHA256, independently read before freezing, is
`7fb3e177b5709ea0eecafd94d087752c6252c8879475ab602d4ae1430566d49e`.
Pin its manifest and old DD/curvature 11/101 JSON directly from that archive.
The old pair must match all 181 traces/tracer hashes, 13 particle file hashes,
six raw image hashes and applicable old snapshot fields. Verify supplied
archive bytes, authenticated baseline records, and code fingerprints at
formal-run start/end. Preserve old API/schema when memory is omitted.

Meaningful pre-formal checks should include reset after history exists;
birth IDs under array reordering; direct priority over history; one eligible
reuse followed by mandatory expiry; absent/invalid/stale creator frames;
raw Tb residual followed by final-only clipping; and an observer-on/off
exact replay including memory state. Analytical small cases should make
residual sign, identity and TTL mistakes observable. They do not replace
the six deployed trajectories.

## Frozen decision and conditional timing

Keep the existing absolute quality screen: foreground RGB and alpha NRMSE
each <=5%, every nonzero checkpoint position RMSE<=.007 and p99<=.035,
complete IDs, exact matched visual evolution and physical/birth invariants,
and no capacity blocking/fallback. Use paired DD alpha>.01 foreground,
pool SSE/reference signal before normalization, and the established
floor(q*(n-1)) quantile. Report all six images and 12 nonzero checkpoints;
no pooled seed decision or empty-initial-frame dilution.

For each seed independently, memory must pass the
absolute screen and its maximum checkpoint RMSE and maximum checkpoint p99
are both strictly smaller than stateless curvature's corresponding maxima.
Require equal actual per-frame raw-query budgets and no render retirement
for the compared arms. The stateless control may fail absolute accuracy but
must remain valid and comparable. Strict improvement is not significance.
Both seed pairs, complete observations, and immutable regression must pass
before timing is allowed. Each memory trajectory must have at least one
actual reuse. Beyond that nonzero-exposure condition, exposure magnitude
remains descriptive and cannot become an adjustable post-outcome gate.

Conditional timing retains the P3f protocol: DD versus memory on
11/101 only, five independent runs per arm, orders AB/BA/AB/BA/AB, 20 warmup
frames/reset, 41 completed-frame samples per run at frames 60..180 every
three frames. Include all memory work. Exclude dense diagnostic readback
and full state hashing from timed intervals. Match initial/final particle,
physical, memory, counter and relevant field state to same-arm quality runs
outside timing. Central=median of five run medians; tail=median of five run
p95 values. Require DD/memory central speedup>=1.5 and memory tail<=DD tail.
No timing or speed inference from the new seed follows from this old-pair
measurement. Do not call the growing-load time window steady state.

If any valid scientific screen fails, retain all quality evidence and mark
the planned ten timings skipped. Execution may pass with complete protocol
and engineeringGo=false. Invalid/missing evidence is not a valid negative
experiment. No protocol amendment after seeing outcomes can convert failure
into success; any alternative method needs a separately frozen phase.

## Interpretation limits

A positive result would support bounded benefit from this exact TTL1
construction on one old and one new seed, followed by conditional old-pair
cost evidence. It would not identify the sole cause of drift, establish
physical transport/conservation, validate long-term residual persistence,
prove a representation theorem or paper novelty, or quantify acceptance
probability. A negative result rejects the fixed construction under these
targets; low exposure or changing selection narrows its causal interpretation.

The contract is frozen before the new-seed outcomes. Runtime/harness field
names may be clarified without changing this contract. Any correctness
repair must be documented and followed by the necessary checks; any change
to the method or decision rule requires a separate phase, not retroactive
reinterpretation of P3g.
