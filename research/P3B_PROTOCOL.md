# P3b: a lazy world-grid cache for passive tracer transport

Status: frozen preregistered design from the root's final contract, before
outcome inspection. Implementation/API verification is pending; the numerical
decision rules below must not be adjusted after inspecting quality or timing
outcomes. API-description corrections may align names with the implementation
without changing the statistical contract.
This protocol is separate from P3a and does not change its frozen artifacts.

## Question and reference

Can a lazy Cartesian cache reduce the cost of the P3a passive renderer while
keeping its additional transport and image error below declared limits? The
reference is P3a's direct tree query at the same physical resolution, tracer
budget, source, timestep, physical seed, and render seed. It is a numerical
reference for this existing model, not physical or perceptual ground truth.

The same render RNG and birth schedule are essential: cached-versus-tree image
differences must measure caching and resulting trajectory differences, not a
fresh random rendering sample. Do not use the independently sampled P3a 32x
reference as the denominator or target for the cache-error gate.

## Frozen cache contract

Use an axis-aligned world lattice with fixed origin `(0,0,0)` and spacing `h`.
Locate cells with mathematical `floor(x/h)` on every axis, including negative
coordinates. For each tracer, memoize the eight enclosing lattice-corner
queries as needed and interpolate trilinearly. The cache is sparse and lazy;
there is no fixed clipped spatial box and no outside-domain fallback.

Each entry stores induced Biot-Savart velocity and the direct sampler's pure
normalized dynamical temperature `Tb`. Thermal weight may also be retained for
diagnostics. The cache does not store rendering temperature `T` or density `d`.
Those remain each tracer's own state with the unchanged birth and cooling laws.

Interpolate induced velocity and `Tb` first. At the actual tracer position add
the same direct buoyancy, wind, and procedural curl, then apply the same speed
clamp and integration/boundary rules as the direct path. Interpolating already
clamped corner velocities is a different approximation and is excluded. Even
with this order, interpolation of a normalized `Tb` field is an approximation;
zero-support corner values can attenuate it near support boundaries. The direct
normalized field is defined as zero outside its finite kernel support and can
be discontinuous at that boundary. Keep all eight trilinear weights, including
zero-valued unsupported corners; do not renormalize over supported corners to
quietly change the approximation. This boundary bias is part of what is tested.

Every step clears the cache. Both methods query the frozen pre-integration
physical tree after native source heating and advance through the same Euler
timestep. External procedural forcing uses the same time as the existing
native/direct path. No entry may survive into a different physical time level.
Camera changes cannot shift the lattice or modify any cached field values.

A safety node cap of 200,000 is fixed for the formal matrix. If filling a query would exceed it, that entire
tracer query falls back to the direct tree path; do not combine an incomplete
set of corners or silently zero missing values. Record cap-triggered fallbacks,
node queries, requests/hits, peak nodes, and memory where available. Formal
accuracy/route eligibility requires zero such fallbacks. Zero thermal support
at a lattice corner is a different condition and must not be reported as a
cache-cap fallback. Record it; judge its effect through the error measurements.
Separate the fraction of unsupported node queries from the fraction of
unsupported direct tracer/probe queries; they have different denominators and
cannot be compared as if they measured the same event.
The implementation also guards lattice indices outside safe integer arithmetic;
that exceptional direct-query fallback is not clipping to a spatial cache box.
It must be zero in the formal matrix as part of the total fallback gate.

Current API accounting distinguishes the following quantities:

- `tracerFieldQueries` counts actual tracer transport requests.
- `cacheNodeQueries` counts admitted unique lattice-node evaluations. The
  `cacheHits`/`cacheMisses` counters count stencil lookups, so cap-rejected misses
  are not necessarily node evaluations.
- In a formal grid run with zero fallbacks, `noThermalSupportQueries` counts
  unsupported node evaluations; divide by `cacheNodeQueries`, not tracer count.
  In a tree run it instead counts unsupported direct tracer queries.
- `cacheNoThermalSupportQueries` counts grid tracer queries whose interpolated
  support fraction is zero; `cachePartialSupportQueries` records partial
  support. Their denominator is `tracerFieldQueries`.
- Scratch `fieldProbe` counters combine node and direct-position evaluations.
  Count direct unsupported points from `samples[].tree.thermalWeight === 0`;
  subtract that count from its `noThermalSupportQueries` to obtain unsupported
  nodes. Probe fallback reuses the same direct-point result and adds no extra
  tree evaluation. The production counters are restored after a probe.

## Fixed matrix and held-out use

Inherit P3a's physical capacity 600, render capacity 9600 (16x), three-layer
parameterization of the actual 3D solver, source rate 180/s, `eps=0.07`,
`dt=1/60`, and 180-frame/3-second horizon. Optical radius remains 0.045 and
`tau=0.2`; use the same RGBA32F accumulation and common optical-depth model.
No optical retuning, larger footprint, or source-strength compensation is
allowed to make a cache result look closer.

The three conditions are:

| Condition | Wind | Procedural curl strength | Role |
| --- | ---: | ---: | --- |
| Stationary | 0 | 0 | One seed pair for development; two for confirmation |
| Crosswind | 0.35 | 0 | Held-out condition |
| Curl | 0.2 | 0.55 | Held-out condition |

Use paired `(physics seed, render seed)` values `(11,101)`, `(23,211)`, and
`(47,307)`. These are three pairs, not a 3x3 Cartesian seed matrix. At each
condition/pair run direct tree and grid spacing 0.035, 0.07, and 0.14 (0.5, 1,
and 2 times `eps`): 36 quality trajectories. These are source/forcing
conditions, not reconstructed scenes.

Capture at frames 90 and 180, at yaw 0, 0.7, and 1.4 radians, with 256x192
images: six captures per trajectory, 216 images. Use direct-tree alpha greater
than 0.01 to define each image's fixed foreground mask. Apply it unchanged to
all three cache spacings in that condition/seed pair. Save masks or their
reproducible hashes, dimensions, and pixel counts. Report full-image errors as
secondary evidence; the decision gate uses the declared foreground region.

Record paired tracer state every 15 frames (12 checkpoints, including the
final frame). Use stable birth identities, not the current compacted-array
index. Preserve both all emitted identities and live identities. At every
checkpoint report common, tree-only, and cache-only live identities, counts,
and corresponding optical weights. Missing identities cannot disappear from
the interpretation merely because an error is computed on the intersection.

## Mandatory validity checks

Physical particles, their RNG and source accumulator, and physical time must
match exactly at every frame across tree and cache methods. Render RNG progress,
emission counts/credits, and birth records must match for the same pair. For a
common birth identity, the visual `T`, `d`, and age must remain equal; their
unchanged laws have no dependence on the cached velocity. Additional source
capacity binding invalidates the intended comparison rather than supplying a
free method-dependent source change.

Reset and render/camera calls must preserve the same invariants as P3a. The
direct-tree path must retain P3a's arithmetic and reproduce its prior fixed
configuration trajectory. Stable IDs should be external bookkeeping and must
not alter the prior particle hash schema or consume RNG draws.

Cache diagnostics must cover lattice-node agreement, constant/linear synthetic
fields, negative-coordinate cell boundaries, per-step invalidation, support
boundaries, and the order of external forcing and speed clamping. A deliberately
tiny cache cap checks complete direct-query fallback and accurate cap counters.
Diagnostic queries run outside timing and must restore or isolate cached state,
counters, and RNG. They may not warm the measured cache for free.

Collect same-position tree/cache query comparisons at a predeclared fixed set
of world coordinates and the identical documented physical time. The probe
locations do not follow either method's potentially diverging tracer positions
and must not be chosen after observing errors. Report induced velocity, `Tb`,
and final transport velocity separately, including empty-support counts. These
instantaneous errors help distinguish interpolation error from accumulated path
divergence, but do not replace image/path gates. Probe calls run outside timing.
The fixed 48 probe locations are the Cartesian product
`x = {-0.1, 0, 0.3, 0.8}`, `y = {0.1, 0.5, 1, 2}`, and
`z = {-0.25, 0, 0.25}`, evaluated at each recorded 15-frame checkpoint.

## Error definitions and predeclared gates

Pool sums over the six captures before normalization; do not average six
per-image RMSE values and call that pooled error. For the fixed foreground
pixels, define

`RGB NRMSE = sqrt(sum ||RGB_cache - RGB_tree||^2 / sum ||RGB_tree||^2)`

and

`alpha NRMSE = sqrt(sum (alpha_cache - alpha_tree)^2 / sum alpha_tree^2)`.

An empty foreground or zero/nonfinite denominator is not a passing comparison.
Both foreground RGB and alpha NRMSE must be at most **0.05**. These tolerances
are engineering screening choices, not guarantees about perceived realism.

At each 15-frame checkpoint compute each matched tracer's Euclidean world-space
position error. Its RMS must be at most **0.007** (`0.1*eps`) and its 99th
percentile at most **0.035** (`0.5*eps`). Define the percentile using the sorted
sample at index `floor(0.99*(n-1))`. Every checkpoint must pass; pooling earlier
accurate states cannot hide later drift. Missing live identities or an empty
matched set invalidate eligibility even if the common subset has small error.
All states and errors must be finite. Cache-cap fallbacks must be zero.

## Timing and fixed selection rule

Time all four methods in all three conditions with five independently reset
repetitions: 60 timing runs. Use the development seed pair `(11,101)` for these
timings. Retain P3a's 20-frame code warmup followed by reset and replay, then
sample every third frame from frame 60 through 180 inclusive (41 samples/run).
Balance method order and match physical simulation frames across methods.

This is a warmed fixed simulation-time window with growing particle load, not
steady state. End-to-end latency must include physical stepping, cache clearing,
all cache construction/misses/fallbacks, interpolation and tracer integration,
gather/sort/upload, drawing, and GPU completion. `gl.finish()` synchronized wall
time is completed frame latency, not pure GPU time. Exclude only diagnostic
probes, snapshot/hash serialization, screenshots, and image readback, and label
those exclusions. Report cache cost and the direct-query count reduction rather
than treating lazy cache construction as free preprocessing.

For each method/condition compute each run's frame median and frame p95 using
the sorted-sample index `floor(q*(n-1))`. Define the method's central latency as
the median of its five per-run frame medians. Define its tail statistic as the
median of its five per-run frame p95 values. Name the latter **median of per-run
p95**; it is not the p95 of all 205 pooled frames. Retain the 205 raw samples and
all five runs' summaries, so run-to-run variability and slower runs stay visible.

Select a spacing using **only stationary `(11,101)`**. Among grid spacings that
pass all its error/identity/fallback gates, choose the one with the smallest
central completed end-to-end latency on the corresponding stationary timing
runs. A numerical tie selects the smaller spacing. If none qualifies, no spacing
is selected. The other eight
condition/seed pairs are confirmations and may not be used to choose another
spacing. All curves may be shown without changing this selection rule.

A positive route decision requires the selected spacing to pass the same gates
on all eight confirmations, and to achieve, separately in every condition, at
least **1.5x** median end-to-end speedup over direct tree with its tail statistic
no greater than direct tree, using the central latency and **median of per-run
p95** definitions above for both methods. Do not pool the three conditions to
conceal a slow condition, and do not treat the correlated frames as independent
experimental repetitions.

Execution success, numerical validity, and a positive route decision are
separate fields. A run can execute correctly while no spacing qualifies, while
held-out error fails, or while speedup is inadequate. Plumbing smoke tests may
repair implementation defects, but their quality/timing outcomes cannot be used
to alter these preregistered spacings, conditions, or thresholds.

## Interpretation and remaining scope

A positive result supports a faster approximation to this fixed direct-tracer
model on the declared forcing conditions and short horizon. It does not prove
better fluid physics, physical conservation, universal cache convergence, or
perceptual equivalence. Cache resolution is not physical simulation resolution.

This remains a fire-only rendering/transport baseline. There is no 3D scene
combustion feedback, late ignition, material-mass reconstruction, or fair
layered-versus-3D source calibration in this experiment. More complex scenes,
longer lifecycles, source changes, and broader device/quality scales require
separate evidence. A negative result rejects the tested spacings/implementation
under these gates; it does not rule out every cache or decoupled architecture.
