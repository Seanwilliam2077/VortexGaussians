# P3c: separating velocity and temperature cache errors

Status: frozen exploratory attribution design, after the P3b results and before
inspection of P3c outcome data. This is a new experiment, not a revision of the
P3b protocol, thresholds, selection result, or route decision. Implementation
field-name corrections may align this document with the API without changing
the matrix, sampling, metrics, or interpretation rules.

## Question and limits

At the already tested cache spacing `h=0.035`, how much trajectory and image
error appears when only induced velocity, only normalized dynamical temperature
`Tb`, or both are interpolated? Can same-position field probes distinguish an
instantaneous approximation error from its accumulated transport consequences?

P3b found that image error and trajectory error need not satisfy the same
screening decision. One possible explanation is interpolation across the finite
support boundary of `Tb`; another is induced-velocity interpolation, and their
effects may interact. These are hypotheses to distinguish, not assumed causes.
The reference remains the existing direct tree model, not physical or perceptual
ground truth. This experiment makes no performance or usable-speedup claim.

## Four arms and fixed exposure

The first letter selects induced velocity and the second selects `Tb`:

| Arm | Induced velocity | Tb | Runtime field configuration |
| --- | --- | --- | --- |
| DD | Direct tree | Direct tree | `mode: tree, components: both` |
| GD | Grid interpolation | Direct tree | `mode: grid, components: velocity` |
| DG | Direct tree | Grid interpolation | `mode: grid, components: temperature` |
| GG | Grid interpolation | Grid interpolation | `mode: grid, components: both` |

All grid queries use the same world-origin-zero Cartesian lattice at `h=0.035`
and a node cap of 200,000. Retain all eight corner weights, including unsupported
corners whose normalized `Tb` is zero. Do not renormalize over supported corners.
Choose the two raw field components first, then apply identical buoyancy, wind,
procedural curl at the actual tracer position, and one common speed clamp.
Do not interpolate already clamped corner velocities. Integrate and apply the
same cooling, density decay, depth clamp, and retirement rules in all arms.

The frozen pre-integration physical tree, forcing time convention, per-step cache
invalidation, source, and optics remain those of P3b. Hybrid arms may query both
the cache and a direct raw field at a tracer position. Their extra work is not
an optimized implementation and must not be used to claim a practical speedup.

Use physical capacity 600, render capacity 9600, source rate 180/s, three-layer
parameterization of the actual 3D solver, `eps=0.07`, `dt=1/60`, and 180 steps
(3 seconds). Retain optical radius 0.045, `tau=0.2`, RGBA32F accumulation, and
unchanged optical weights. Use three conditions: stationary `(wind=0,turb=0)`,
crosswind `(0.35,0)`, and curl `(0.2,0.55)`. Each condition uses the three paired
seeds `(11,101)`, `(23,211)`, and `(47,307)`, with all four arms: 36 trajectories.

These conditions and seeds have already been examined in P3b. They are reused
for mechanism exploration, not new held-out confirmation. Do not select a new
cache spacing or tune a threshold from these results. No timing matrix is part
of P3c. Any incidental duration is execution metadata, not benchmark evidence.

Capture 256x192 linear HDR at frames 90 and 180 and yaw 0, 0.7, 1.4: six images
per trajectory, 216 images. Record stable-ID particle states initially and after
every 15 steps: 12 nonzero checkpoints. Use the paired DD image's `alpha>0.01`
mask for foreground comparisons; retain the same mask across the other arms.

## Reference-trajectory input probes

The previous fixed-world probe locations included points outside the tracer
population. This experiment instead samples the actual DD transport inputs by
a fixed rule, without selecting positions according to observed errors.

On DD steps 15, 30, ..., 180, record all live inputs with birth identity
`id % 97 === 0`, after this step's births and before any tracer integration.
Include newly born tracers, including identity zero when present. Record each
input's identity, position, pre-integration `age=life`, newborn flag, step/frame,
field time, and input phase. The probe is deliberately on the DD path; it does
not describe the instantaneous field error at already diverged GD/DG/GG paths.

The API `stepWithInputs(dt, {stride:97})` activates the collector for one step
only and clears it in `finally`. It returns `inputs` and `inputPhase`. An
immediate `fieldProbe` of those saved positions may execute after the step,
because it queries the same still-frozen pre-integration tree and the same
forcing-time convention. Record and verify that correspondence; do not query
the next step's tree or use post-integration positions in its place.

For each position, retain direct and cached raw induced velocity, normalized
`Tb`, thermal weight, and grid support fraction. Evaluate all four combinations
at this same position, through the same actual external forces and single clamp.
Record `transportVelocities.{DD,GD,DG,GG}` and each combination's raw induced
velocity, `Tb`, total velocity, pre-clamp velocity/speed, and clamp flag.
The probe evaluates all combinations regardless of production `components`.

Use an isolated scratch cache. Probing must leave physical and render state,
RNG, counters, hashes, and production cache unchanged, and must not prewarm a
later production step. The collector must not change arithmetic, random draws,
births, integration order, or IDs. DD with collection must exactly reproduce DD
without collection. Validate the input phase using newborn age zero and known
pre/post integration states, not merely a returned label.

Separate direct point support (`thermalWeight>0`) from interpolated corner
support (`supportFraction`). Preserve the combinations direct supported or
unsupported versus grid zero, partial, or full support. Report group sample
counts, signed `Tb_grid-Tb_direct`, its RMS, and induced/final velocity errors.
An empty support subgroup has count zero and null metrics. These fixed-rule
particle-time samples are diagnostic; they are not a random independent sample
of physical events. Support strata and signed bias do not alone establish the
cause of accumulated path error.

## Matched trajectory and image measurements

For every condition/seed/checkpoint, compare stable birth identities against DD.
Report common, DD-only, and arm-only live counts and optical weights. Never hide
retirement differences by silently discarding noncommon identities. Use the
intersection of all four live-ID sets for the four-arm interaction calculation,
and record the number excluded. Missing identities invalidate a clean matched
transport interpretation even when the remaining subset has small errors.

For arm A and a matched identity at a checkpoint define the position error
vector `eA = xA - xDD`. Report three-dimensional position RMS, Euclidean error
p99, signed vertical bias `mean(eA.y)`, vertical RMS `sqrt(mean(eA.y^2))`, and
horizontal RMS `sqrt(mean(eA.x^2 + eA.z^2))`. Do not call these single-step
displacement errors. Define p99 by sorted index `floor(0.99*(n-1))`.

Also report these quantities by DD birth-age bin. Convert age to integer steps
`k=round(life/dt)` and require `abs(life-k*dt)<1e-9`. Use bins `[0,30)`,
`[30,60)`, `[60,120)`, and `[120,infinity)` steps, corresponding to
`[0,.5)`, `[.5,1)`, `[1,2)`, and `[2,infinity)` seconds. This avoids ambiguous
floating-point boundary comparisons. Checkpoint life is post-integration;
input-probe life is pre-integration. State which is used and do not shift one
to match the other. Empty bins have count zero and null error metrics.

Pool image squared errors and DD signal energy across the six captures before
normalizing, using the unchanged P3b foreground RGB/alpha NRMSE definitions.
Report full-image metrics as secondary evidence. Do not average per-image
NRMSE values and call that a pooled result. Undefined denominators yield an
explicit undefined result, not a passing value.

## Vector interactions and attribution language

At a common identity/checkpoint define

`eI = eGG - eGD - eDG`.

Compute the RMS norms `rGD`, `rDG`, `rGG`, and `rI` over common identities at
each of the 12 checkpoints. Also compute them pooled over all recorded common
identity/checkpoint observations within one condition/seed pair, by summing
squared vector norms and dividing by the total observation count. This pooled
quantity weights each particle-time observation equally; later checkpoints
with more particles receive more weight. Preserve checkpoint results so this
weighting cannot conceal late drift. Do not pool the nine seed/condition pairs
into one purported independent repetition.

Report the continuous ratios `rGD/rGG`, `rDG/rGG`, and `rI/rGG`, per checkpoint
and pooled within each pair. A zero GG denominator yields null ratios. Ratios
can exceed one and are not percentages of an additive error budget. Do not
subtract scalar RMS values to estimate contributions or impose a new arbitrary
threshold that labels one component dominant. Report all nine pairs, including
opposite or condition-dependent effects, without selecting only favorable ones.

At each same-position input probe separately compute

`vI = vGG - vGD - vDG + vDD`.

This instantaneous total-velocity interaction can expose nonlinear single-clamp
effects. Before that clamp, the prescribed forces add induced velocity and
`buoyancy*Tb` linearly at a fixed position; use the corresponding pre-clamp
interaction as an implementation sanity check, allowing floating-point noise.
The trajectory interaction `eI` has a broader meaning: it also contains changed
query locations, nonlinear evolution, integration/boundary effects, and their
accumulation. It cannot be attributed entirely to the speed clamp or interpreted
as a physical interaction between heat and vorticity.

Permitted conclusions describe controlled substitutions in this model: for
example, that caching one component produced larger measured trajectory error
than caching the other, or that keeping direct `Tb` reduced error under a given
condition. A consistent support-stratified instantaneous bias plus a matching
hybrid trajectory response strengthens a boundary-bias explanation, but does
not prove it is the only cause. A probe measures an approximation at the DD
path; a transported arm additionally changes where future queries occur.

## Validity, descriptive screening, and remaining work

Require exact per-frame physical state/hash, physical and render RNG progress,
birth/emission credits, and birth identity sequence across arms. Common-ID
visual `T`, `d`, and life must match exactly. Source/capacity blocking, unsafe
lattice fallbacks, and cache-cap fallbacks must be zero in the intended formal
comparison; report any violation explicitly. Extra hybrid raw queries have
separate `componentDirectQueries` and `componentDirectNoThermalSupportQueries`
counters, so their point-support counts are not confused with node queries.

DD and GG must reproduce the corresponding frozen P3b h=.035/tree evidence
under matched configurations, including the collector's read-only effect.
Keep source fingerprints and raw states, probes, images, masks, and completeness
checks for all 36 trajectories, 12 nonzero checkpoints and six captures per
trajectory. Diagnose execution failures separately from unfavorable outcomes.

The old P3b engineering criteria may be recomputed descriptively: foreground
RGB and alpha NRMSE <=5%, every checkpoint position RMS <=.007 and p99 <=.035,
with complete matching and no fallbacks. Do not reinterpret a hybrid passing
these checks as a changed P3b decision or a new route-go. P3c makes no speed
claim, and an extra direct tree query may erase any cache benefit.

No result establishes physical correctness, perceptual equivalence, combustion
feedback, late ignition, long-time stability, reconstructed-scene generality,
or superiority to a calibrated layered solver. A promising attribution should
motivate a separately specified algorithm and fresh confirmation data. Do not
reuse these examined conditions/seeds as unseen validation of a later tuned
method, and do not relax the frozen P3b thresholds after viewing this analysis.
