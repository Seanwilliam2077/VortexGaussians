# P1: combustion clocks and cold-particle reuse

This protocol is written before the P1 outcome runs. It evaluates two opt-in
implementation policies against the frozen P0 behavior. Its purpose is to
quantify a fix and its tradeoffs, not to force a positive result or claim new
physical combustion theory. The manifest records the exact parameter names,
source fingerprints, seeds, durations, and settings actually run.

The original processed-clock / block-on-full behavior remains the default.
Density normalization, a new graph scheduler, and physical calibration are
outside this change. Do not divide a coupling coefficient by global splat count
or alter fuel mass to make a density test pass.

## Policies and hypotheses

**Elapsed clock.** Fuel depletion, glow, and char advance once per simulation
step for every currently burning scene primitive. The frontier cap limits graph
neighbourhood work, not these local clocks. Keep the existing phase ordering:
ignition decisions, graph heat deposition, local burning-state updates, removal
of extinguished primitives, then scene-to-solver feedback. Newly deposited graph
heat is still tested for ignition on the following step.

Hypothesis C: for identical ignition histories, elapsed-clock fuel and char are
independent of frontier cap and primitive traversal order. This does not imply
that ignition histories, heat transfer, or propagation become cap-independent.

**Cold-particle reuse.** At a full destination layer, a successful scene-feedback
admission may replace an existing particle only if its rendering temperature and
dynamical temperature are both strictly below `0.55` and its age is at least
`0.5` simulated seconds. The threshold aligns with the current flame-to-scene
heating gate; it is not a claim of physical insignificance. Freeze the exact
coldest-candidate score and deterministic tie-breaking rule before measuring.
Never exceed the configured layer capacity or evict an ineligible particle.

Hypothesis R: reuse prevents the measured P0 loss of ignition-capable particles
while scene fuel is still burning. The intervention removes smoke and vorticity
state; restoring hot particles alone does not establish a better simulation or
better image.

## Experiment matrix

1. **Factorial feedback run.** On the P0 raised-target fixture, run processed/block,
   elapsed/block, processed/reuse, and elapsed/reuse for seeds `11, 23, 47`, each
   for 12 simulated seconds at `dt = 1/60`. Keep three world-fixed VPM layers,
   600 particles per layer, the external emitter and its reheating disabled, and
   embers/procedural turbulence off. Keep the same initial ignition and geometry.
   The frontier cap is not expected to bind on 36 scene points, so this also
   isolates the reuse intervention from the clock intervention.
2. **Clock isolation.** Use the 1681 preignited, disconnected P0 sites with both
   feedback edges off. Compare processed and elapsed clocks at frontier caps
   `350, 700, 1400, 2800`, including reversed order at `1400`. A 2-second
   checkpoint tests local-clock equality before fuel runs out; a later checkpoint
   beyond the six-second burn duration tests extinction. No graph propagation is
   possible in this fixture.
3. **Clock tradeoff.** Run the connected P0 strip, both feedback edges off, with
   processed and elapsed clocks at a binding cap (`16`) and a nonbinding cap
   (`1400`), for 12 seconds. Include the same order variants when budget permits.
   Compare target ignition trajectories and common-anchor states, not only total
   consumed fuel. A skipped source can now run out of fuel before its graph work
   is serviced. Reduced reach is a reportable tradeoff, not a failed experiment.
4. **Eligibility controls.** Exercise a full all-hot/too-young pool that cannot
   admit replacements, a full pool with an eligible cold candidate, and a
   non-full pool. Verify deterministic candidate selection, admission/rejection
   behavior, capacity, and counter reconciliation. These are implementation
   checks; manually initialized controls are not research examples.

Use sampled trajectories with an explicitly recorded interval. The standard
quarter-second sampling is sufficient for broad hot-population coverage and
clock comparisons, but not exact ignition/event timing. Preserve quick structural
runs separately from full-duration runs. If the actual matrix omits a proposed
control, name that omission rather than implying it was completed.

## Measurements

Retain the P0 per-site heat/fuel/char/state snapshots, stable IDs, cumulative
transport counters, randomness counts, and source fingerprints. Keep the global
heat counters distinct from per-region instantaneous heat, as in P0.

For clock comparisons, record local-clock update counts separately from graph
frontier processed/deferred counts. Report per-site fuel/char differences at the
same simulated time, extinction times as sampled intervals, and target ignition
fractions on the strip. Analysis weights continue to affect analysis only.

For reuse, record fresh admissions, recycled admissions, capacity rejections,
random rejections, and candidate examinations if instrumented. Reconcile every
feedback opportunity to an outcome. Validate the discarded particles' temperature
and age eligibility, with event samples or aggregate extrema that make any
threshold violation detectable. Record the deterministic selection rule in the
API documentation or manifest.

Report hot-particle count (`T >= 0.55`) and burning-scene count over time. The
predeclared diagnostic window is `t = 3..6` seconds, where the P0 fixture lost its
hot population while scene primitives remained burning. For each seed, show all
sampled counts and the fraction of checkpoints with both burning fuel and at
least one hot particle. Do not redefine the window after seeing the results.
Also report thermal summaries and total particle count; one hot particle is only
a minimal mechanism-engagement signal, not proof of a convincing plume.

If available, count the discarded density, absolute circulation, and covariance
or age summaries. These are state-loss proxies, not conserved physical mass or
energy. If they are not instrumented, state that the loss has not been quantified.
Rendered smoke opacity/extent, plume appearance, flicker, and vorticity changes
need a separate matched-camera comparison before any visual-quality claim.

## Acceptance checks and outcome interpretation

### Software invariants

- The original default replay remains unchanged under the existing P0 settings.
- Repeating each new policy with the same configuration and seed resets all
  relevant state and reproduces its trajectory and combustion hash.
- No external emitter particles or source-band heat appear in emitter-off runs.
- Elapsed clocks update each burning primitive once per step, including deferred
  primitives; graph processing remains limited by its cap.
- At a nonbinding graph cap with identical ignition history, processed and
  elapsed clocks produce identical per-site fuel/char states before extinction.
  The elapsed policy clamps spent fuel to zero; the legacy path can retain a
  negative overshoot of up to one depletion step. This intentional boundary
  difference is not a failed equality check after extinction. Compare extinction
  intervals and terminal char/state separately.
- Reuse never grows a layer past its capacity, never evicts a hot or too-young
  particle, and never removes a particle on a rejected admission.
- With space available, reuse preserves the ordinary admission behavior. With no
  eligible candidate, it records a rejection without silently stealing a slot.

An invariant violation is a software failure, not a scientific negative result.
Fix it, retain the failed run separately, and rerun the affected comparisons.

### Hypothesis C

Pass on the isolated fixture requires equal per-stable-ID fuel and char across
all elapsed-clock caps/orders at matched checkpoints, and a common extinction
interval. The original processed-clock differences must remain measurable as
the control. For a numerical check before extinction, expected fuel is
approximately `1 - t/6`; compare within an explicit Float32 rounding tolerance
(for example `1e-5` at two seconds), while the within-implementation cross-cap
comparison should be exact when the update sequence is identical.

Failure to remove clock dependence rejects C for this implementation. Passing C
supports only the local-clock fix. Report the connected-strip results even if
elapsed clocks reduce spread or increase cap sensitivity of ignition. The method
still discards deferred graph work and provides no heat-transfer conservation
guarantee. More uniform clock progression is not equivalent to a converged front.

### Hypothesis R

First establish exposure: the pool reaches capacity, a cold eligible candidate
exists, and recycled admissions actually occur. If any is absent, the run does
not test R. A candidate-search counter alone is not a successful replacement.

Compare hot-population coverage in the fixed 3..6-second window for each seed.
An increase over block-on-full supports mitigation; nonzero hot counts at every
sampled checkpoint with burning fuel support complete mitigation only on this
fixture and sampling grid. An unchanged zero-hot interval is a negative result,
not something to repair by changing seeds or thresholds after the fact. Fewer
blocked admissions alone is insufficient, and delayed first target ignition must
be reported even if later coverage improves.

Record the removed-state cost in the same result. A positive hot-count result
with unmeasured or visibly damaged smoke cannot be called a quality improvement.
The conservative description is a bounded policy that exchanges cold state for
continued hot feedback.

## Randomness, cost, and residual limitations

P0 block-on-full skipped random draws when the pool was full. A reuse policy can
consume additional draws when it finds an eligible candidate, so the two paths
can have different random histories after that intervention. Preserve the
default sequence; do not quietly redesign it to obtain matching results. Verify
agreement before the first changed capacity decision, record draw counts, and
describe later comparisons as whole-policy interventions. Three paired seeds
provide diagnostics, not statistical significance or population generality.

Elapsed clocks add work proportional to the burning population. Searching a full
layer for the coldest candidate also costs work; it is not free merely because
the particle count stays bounded. If timed, separate step cost from page setup,
sampling, rendering, and serialization, and record the execution environment.
Do not interpret headless harness duration as a GPU or end-to-end FPS benchmark.

Neither policy fixes nonuniform reconstruction density, frontier traversal bias,
per-frame emission/sample quotas, timestep dependence, camera-dependent slicing,
missing scene obstacles, or scene-light transport. Reuse is not a remeshing method
and does not conserve circulation, smoke mass, or rendered opacity. Claims of
better perceptual quality, physical validity, general capture performance, or
publication novelty require further evidence beyond these synthetic diagnostics.
