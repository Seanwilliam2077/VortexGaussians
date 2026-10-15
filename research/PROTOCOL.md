# P0 diagnostic experiment protocol

These experiments test the implementation's feedback paths and its sensitivity to
primitive density, frontier budget, and camera frame. They are synthetic
diagnostics, not measurements of physically calibrated combustion or proof of
performance on a captured reconstruction. The run manifest is authoritative for
the actual configuration, seed list, duration, and code version.

## Causal feedback experiment

Two independently controlled factors form four conditions:

| Flame particles heat the scene | Burning scene seeds the solver | Interpretation |
| --- | --- | --- |
| off | off | Scene-graph-only control |
| on | off | Flame-to-scene edge without return feedback |
| off | on | Scene sustains a plume, but that plume cannot ignite a target |
| on | on | Complete feedback loop |

All conditions begin with the same explicitly ignited source patch. The external
emitter is off from time zero. This intervention asks whether already-burning
geometry can create a plume that ignites other geometry; it does not repeat or
replace the manuscript's external-flame-to-table-to-machine demonstration.

The proposed small fixture has nine source sites at `y = 0.20`, with both `x` and
`z` drawn from `[-0.04, 0, 0.04]`, and 27 target sites at the same horizontal
locations with `y` drawn from `[0.45, 0.49, 0.53]`. Its minimum source-to-target
gap is `0.25`, exceeding both the default scene-graph radius `0.11` and the
initial flame-heating radius `0.14`. Three world-fixed slices at
`z = [-0.06, 0, 0.06]` and 600 particles per slice keep the diagnostic inexpensive.
Use the VPM solver, fixed `dt = 1/60`, no procedural turbulence, and no embers.
The full observation window is 12 simulated seconds; a shorter quick run is only
a structural smoke test. Changes to this fixture belong in a new manifest, not
in an unreported search for a successful seed.

The current runner records these quantities separately for each source and target
region:

- Initial, newly ignited, burning, and charred sites, plus ignition times.
- Instantaneous stored heat, fuel, and char summaries at each sampled checkpoint.

It also records global cumulative heat increments actually deposited by flame
particles and by the scene graph, reseed attempts/admissions/random rejections/
capacity rejections, processed/deferred frontier work, and particle summaries.
Those global counters are not per-region heat budgets. Per-region cumulative
deposits, hot-particle encounter counts, and exact per-step ignition events are
future instrumentation additions. Sampled first-ignition times are upper bounds
within the reported sampling interval, not exact event times.

The negative controls are exact implementation checks: with flame-to-scene heat
off, that heat counter must remain zero; with reseeding off, admissions must stay
zero. With the disconnected fixture and no other source, the scene graph must
not ignite the target. The complete loop supports the intended mechanism only
when the trace contains admitted scene-born particles, stored target heat, and
subsequent target ignition. In this fixture, attribution of the first target
heating follows from the disconnected source/target graphs, disabled external
emitter, and the two single-edge controls. After the first target ignites, its
neighbours may also receive ordinary graph heat; the experiment does not attribute
every later target ignition directly to flame particles. A different final image
is insufficient.

A zero target-ignition result has several distinct interpretations. No burning
source or no admissions means the experiment did not engage the tested mechanism.
Zero stored target heat at the sampled checkpoints is classified as no observed
exposure, not proof that no encounter occurred between samples. Nonzero heat
without ignition is reported as exposure without observed ignition; concluding
that the entire trajectory stayed below threshold would require finer sampling
or event instrumentation. An apparent threshold
crossing without ignition warrants checking update order, decay, and fuel before
calling it a defect. Retain all these outcomes and the trajectories; do not label
them all as absence of feedback. A positive result is an existence demonstration,
not a claim that every scene or fuel gap will ignite.

## Emitter and randomness controls

Turning off primary emission must also turn off the primary source-band reheating
of dynamical temperature. Otherwise existing particles or scene-born particles
can continue drawing energy from an ostensibly disabled emitter. Source embers
are disabled for these experiments. Preserve ordinary cooling and transport.

A shared seed alone does not make an intervention a paired random experiment:
conditional admissions can consume different numbers of random draws. Prefer a
separate or counter-based stream for scene feedback. Record the randomness mode;
ordinary demo replay and research-mode replay are different contracts. In the
primary emitter-off experiment, eliminate other stochastic sources as well.
Determinism checks should cover scene heat, fuel, state, char, frontier order,
emission cursor, and relevant particle state. A particle-only hash cannot verify
the combustion experiment.

## Density and budget sensitivity

Use geometrically matched regular surfaces, with coarse sites retained as common
anchors in finer variants. Report nearest-neighbour distances, connectivity, and
physical extent, so loss of connectivity is visible. A second useful stress test
duplicates every site two or four times at the identical position. Duplication
changes representation density without changing geometric support.

Raw burned-splat counts are not comparable across these variants. Report
area-weighted consumed fuel and char for surface samples and group-weighted means
for duplicates: each of `m` replicas of a site carries analysis weight `1/m`.
Compare ignition time and heat at common anchors. Weights normalize the analysis;
they must not silently change the simulated fuel, heat deposition, or burn time.
Any physical normalization added to the dynamics is a separate method variant.

Sweep the frontier budget while keeping geometry, timestep, initial ignition,
and physical parameters fixed. Record whether the cap actually binds. A cap that
never binds is a valid null but cannot show cap sensitivity. A scheduler-only
stress test may preignite more isolated sites than the shipping cap and disable
both feedback edges; this cheaply isolates fuel/char service from neighbourhood
propagation. Identify that test as scheduler stress, not realistic combustion.

Compare trajectories in simulated time, not just the final checkpoint. Report
wall-clock cost separately. A budget-dependent induction time or burn rate is a
representation/scheduling sensitivity, even when the run is deterministic. It is
not by itself a calibrated prediction about real fire.

## Camera-frame check

With world-fixed slices, changing only the rendering camera should leave solver
and scene-burn trajectories identical. Test a stationary and a scripted moving
camera from the same initial state. With view-aligned slices, camera-dependent
world positions and coupling are expected; measure and report the difference,
rather than marking that documented design limitation as a failed invariant.
Record the camera updates used by the actual coupling code, not only a render
parameter that has not yet updated the camera basis.

## Reporting and interpretation

Keep individual seed traces and report paired differences descriptively. A few
seeds are sufficient for deterministic regression and mechanism diagnostics,
not for population-level significance claims. Separate the quick structural run
from the full-duration evidence run. Store the exact manifest, source revision
or file hashes, browser/runtime identity, counters, trajectories, and outcome
classification together. Do not overwrite an earlier null with a retuned run.

These diagnostics can establish causal functionality and reveal sensitivity.
They do not establish visual preference, a converged 3D physical reference,
real-time dense-scene rendering, or generality beyond the tested fixtures.
