# P3a: fixed 3D physics with independent render sampling

Status: runtime and matrix contract declared before P3 full results; independent
implementation verification is pending. This document belongs to the independent
audit. P0, P1, and P2 protocols and artifacts remain separate.

## Question and claim boundary

At one fixed sparse, genuinely three-dimensional VPM simulation, can independent
advected render tracers provide a numerically resolved emission/absorption image
without changing the physical trajectory? Compare the existing shared 3D particle
rendering with independent tracer sampling at increasing render budgets.

The strongest supported positive claim is that sparse physical particles do not
in themselves require sparse visual coverage or a shared simulation/rendering
particle set. A dense tracer reference is a numerical reference for this tracer
model, not physical ground truth and not a perceptual preference oracle. Lower
error against it cannot establish better physics, better real-fire appearance,
or superiority to a layered solver. A negative result is useful: reference
instability or excessive tracer cost can reject this particular implementation.
It does not reject decoupled simulation/rendering as an architecture. The main
objectives here are physical-state invariance and render-sampling convergence;
this round does not complete the later matched-cost layered/3D comparison.

This round excludes scene ignition and combustion feedback. The released `vpm3`
branch returns before `stepSpread`; importing its image into a reconstructed
scene would not add a closed-loop combustion experiment. A single source viewed
from three cameras supplies view coverage, not three scenes or held-out scenes.

## Controlled variables

Keep the physical particle budget, emission source and birth schedule, physical
RNG, integration timestep, vortex kernel, thermal dynamics, forces, domain,
boundary policy, and all physical parameters identical across render variants.
Only the passive render representation and its sampling density may change.
Changing the physical particle count is outside P3a: the existing circulation
normalization and source strength have not been calibrated across `Nsim`.

Use a separate random stream for tracers, with the seed recorded. Increasing the
render budget need not preserve a prefix of identical tracer paths because its
birth schedule can change. It must not consume physical random draws or alter
the physical emission accumulator. Changing cameras, drawing extra frames, or
capturing images must not advance either simulation.

Use the same fixed kernel radius and optical model for all render budgets.
Normalize the optical quadrature measure rather than enlarging splats or
retuning emissivity to hide holes. Record the weight definition and its treatment
of births, culling, and empty populations. Do not silently compensate for dead
tracers by changing the global brightness of survivors.

The P3 renderer uses a common isotropic footprint with
`alpha = 1 - exp(-weight * tau * d * g)` and consistent premultiplied emission.
This is a dedicated common optical model, not the unchanged native shader.
Changing only density inside the released shader would not be equivalent: that
shader includes constant opacity terms, clamps, and soot blending. For any
unweighted opacity `a`, the equivalent optical-depth split is
`a_w = 1 - (1-a)^w`. Validate opacity and weight ranges explicitly.

For configured physical and rendering budgets `Nsim` and `Nrender`, tracer
emission rate is the physical rate times `Nrender/Nsim`, and each tracer carries
weight `Nsim/Nrender`. Native physical particles rendered through this common
model carry unit weight. Record accumulated emitted weights, fractional emission
credits, and culling. This does not assert that instantaneous surviving optical
measure is exactly equal across independently sampled trajectories. The primary
matrix requires zero physical and tracer capacity blocks; a cap must not change
the admitted source strength unnoticed.

## Tracer field contract

The implementation contract freezes the pre-integration physical tree at time
`t_n`; both physical particles and passive tracers advance over the same `dt`
with explicit Euler. Queries do not mix this tree with post-step particle
arrays. The tracer traversal is read-only and separate from the solver's
mutable shared query output.

Tracer transport uses Biot-Savart velocity from this frozen tree, pure normalized
dynamic-temperature `Tb` for direct buoyancy, and the same imposed wind,
procedural velocity, speed clamp, and depth boundary rule as the physical 3D
integrator. It does not interpolate solved particle velocities. The native
solver retains its self-aware `Tb` average; passive queries have no self prior.
That distinction is explicit and means the passive approximation need not trace
an identical path even when initialized at an existing physical particle.

Each tracer owns its visual temperature `T` and density `d`, initialized from
the same source distributions as physical particles and cooled by exactly the
same laws. Visual temperature is not interpolated from `Tb` or from physical
`T`. `Tb` is sampled only for transport buoyancy. Use a pure normalized kernel
sum for that query, with `Tb=0` when support is empty; the solver's `S=1, sT=Ti`
self contribution does not apply to a passive off-particle query. Thermal
traversal descends nearby support using bounds; the existing far-field
velocity-only aggregate cannot supply a temperature aggregate.

Record support failures, fallback use, and nonfinite values. A fallback is an
explicit part of the tested tracer model, not evidence that local physical
temperature was reconstructed. Validate the chosen interpolation independently
on constant scalar fields and known small particle configurations.

## Mandatory validity gates

1. The physical state hash is identical at every simulated step across all
   render budgets, tracer seeds, and camera schedules. It covers the full 3D
   particle state, physical RNG progress, emission accumulator, source/pointer,
   and simulation time. The existing `__demo.hash()` is insufficient because it
   does not include the 3D `cloud`. Independently compare exposed physical arrays
   in a small diagnostic rather than trusting only a hash implementation.
2. Reset reproduces the same physical and tracer trajectories for identical
   configuration; render-only calls preserve their state. All numeric states,
   optical weights, and queried fields are finite. An empty physical population
   has a defined safe result, not a fabricated hot source.
3. A same-position/same-color split test verifies optical quadrature: replacing
   one primitive with coincident copies whose weights sum to its weight should
   preserve the composited result in RGBA32F, including 1, 2, 4, 32, and 64
   copies. The predeclared maximum absolute per-channel pixel tolerance is
   `1e-4`; the double-precision scalar algebra check uses `1e-12`. The
   test holds texture phase constant. It must test the renderer, not only the
   mathematical expression in isolation.
4. The sampler's constant-field, support, and time-level checks pass; the raw
   record contains actual query counts and fallback fractions. Transport and
   interpolation work must be included in cost measurements.
5. An independent high-sampling reference passes the stability gate below.
   Failure of this gate disallows a quality winner, even if pictures look full.

## Image evidence and reference stability

Use the linear emission/absorption buffer before bloom, tonemapping, gamma, and
vignetting for primary measurements. P3 requires RGBA32F accumulation with the
required float-color and float-blending extensions; a lower-precision fallback
is not admitted in this matrix. The released default framebuffer is unchanged.
Compare RGB and alpha separately. Preserve
the image resolution, camera, kernel radius, optical material parameters,
measurement region, and sample times across methods. Display final images as
secondary qualitative evidence. Hole counts alone are insufficient because
blur, excessive opacity, or overbrightening can remove holes.

For each physical seed the matrix includes three tracer-seed repetitions. The reference RNG
stream is independent from tested low/high streams, so nested shared samples
cannot make one method artificially close to its own reference. A further
twice-as-dense reference is required. Record all seed assignments, including
reference seeds, rather than selecting favorable realizations.

For each physical-seed/tracer-repeat pair pool squared errors over the
predeclared views, times, and measurement pixels before taking the square root;
the arithmetic mean of per-image RMSEs is not the pooled metric. Let
`E_RGB(A,B)` be pooled linear-RGB RMSE and `E_alpha(A,B)` be pooled alpha RMSE.
Compute both over the full canvas and over a foreground mask defined by the
three-reference ensemble mean alpha greater than `0.01` for that physical seed,
view, and time. Apply that same mask to every candidate and reference comparison;
it is independent of the candidate. Save mask hashes and pixel counts. The
stability gate is, separately for each channel and region:

`E(reference, 2reference) <= 0.25 * E(low, reference)`.

Report the numerator and denominator, all nine physical-seed/tracer-repeat
pairs, and any degenerate zero-signal or empty-ROI case. The quality reference is
accepted only when both channels and both regions pass in all nine pairs (36
gates). This 25% threshold is a predeclared screening decision, not
a physical accuracy tolerance or a conference acceptance criterion. Report
continuous errors for native shared, low, and high render sampling; do not
introduce a success threshold after seeing results. An error relative to this
reference measures numerical agreement with its model only.

## Fixed matrix

The `p3-design.mjs` contract sets `dt=1/60`, horizon `3 s` (180 frames), physical
capacity 600, three layers in the 3D source parameterization, and total physical
emission rate 180 particles per second. Capture frames 90 and 180 (1.5 and 3 s)
at canvas size 256 by 192. Camera yaw values are 0, 0.7, and 1.4 radians. They are
called front, oblique, and side for display; the last is not exactly 90 degrees.
The common isotropic render radius is 0.045 and optical coefficient `tau=0.2`.

Physical seeds are 11, 23, and 47. Candidate tracer seeds are 101, 211, and 307;
the paired reference seeds are 401, 503, and 607; the paired twice-reference
seeds are 701, 809, and 907. For each physical seed run native shared rendering
once, and each of the three repeats at tracer budgets 600, 2400, 9600, 19200
(reference), and 38400 (twice-reference). This is 48 quality trajectories and
288 images. Those capacities are not assumed to equal actual live counts.

Hole fraction is auxiliary: the denominator is pixels with reference alpha at
least 0.2, and a candidate hole has alpha below 0.05. It cannot substitute for
linear RGB and alpha errors or establish physical/perceptual superiority.

The timing matrix has shared rendering plus tracer budgets 600, 2400, 9600, and
19200. Use five fresh-reset repetitions with physical seed 11 and tracer seed
101, cyclically rotating method order. Each run warms up for 20 frames, resets,
and replays; sample every third frame from frame 60 through 180, inclusive.
This supplies 25 timing runs with 41 measured frames per run. Timing is a
separate experiment from image capture. Exploratory `quick` and `pilot` suites
are explicitly labelled; they cannot replace the full matrix or select a
favorable seed, camera, or metric after outcomes are observed.

## Timing and interpretation

Record physical particle counts and actual rendered tracer counts, including
births and culling, rather than only configured caps. Separate physical solve,
field preparation/interpolation, tracer update, gather/sort/upload, and drawing
where possible. The existing layered-only exponential timing accumulator cannot
be reused as a 3D timing result. Report distributions over the warmed, fixed
simulation-time window after code warmup and reset, with repeated fresh resets
and unchanged rendering resolution. This is not steady state: the source grows
the particle population from approximately 180 to 540 over the measured 1--3 s
window. Match methods at each frame and restrict timing claims to that window.

A `gl.finish()`-synchronized wall-clock frame measures completed frame latency;
it is not pure GPU time. A submission-only JavaScript timer cannot establish
completed rendering throughput. Exclude screenshot/readback and research
serialization overhead from the timing experiment while reporting their role
in quality capture. Record the browser, GPU/backend, canvas/internal buffer
size, and framebuffer precision. Do not claim device-independent real-time
performance from a single machine.

The present implementation queries the tree for every tracer. Its measured
cost is the cost of this validation baseline, not a lower bound on decoupling.
If that cost is large, a stronger implementation should cache velocity and
temperature with explicit interpolation error, including cache construction,
updates, and queries in its measured cost. Such an extension requires a separate
experiment; it must not be implied by current timings.

## What remains after P3a

The later layered/shared/3D comparison still requires common physical source
calibration and equal optical measure: their current emission geometries,
rates, circulation factors, footprint expansion, and edge fades differ.
Matching only particle count does not isolate dimensional decomposition.

A paper-level decoupling claim additionally needs multiple prespecified source
and scene configurations, out-of-plane stress cases, held-out scenes and views,
matched-error cost curves, and physical/reference or perceptual validation
appropriate to the final claim. Combustion claims require the same two-way
feedback path in every compared method and a late-ignition test while feedback
remains useful. P3a neither establishes those results nor makes them redundant.
