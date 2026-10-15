# P2: authored surface measure in scene coupling

This protocol is written before the P2 outcome runs. It separates representation
invariance from grid-refinement evidence. The objective is to remove dependence
on how an authored surface measure is split among scene primitives, and to
measure remaining discretization effects. It does not establish a conservative
combustion model, calibrated material physics, or a method for estimating area
from an arbitrary captured Gaussian scene. Record the final implementation,
fixtures, parameters, and source fingerprints before running the matrix.

## Contract and scope

Each P2 scene point carries an explicit finite positive `areaWeight`, expressed
in the authored world's squared length units. The fixtures supply this measure
from known surface cells. It is an input to the simulator, distinct from a
display opacity, Gaussian footprint, or analysis-only weight. Missing area on a
real PLY is not evidence for any particular measure. Do not silently infer it
from point count, covariance, opacity, or a global normalization.

Heat state, fuel fraction, glow, and char remain intensive per-site quantities.
Copies of one physical site divide that site's area among themselves while
retaining the same initial intensive state. Fuel clocks use the P1 elapsed
policy in both P2 comparison arms. The shipped legacy coupling remains the
default; the new measure policy is opt-in.

Freeze the reference area to `A_ref = 0.04^2 = 0.0016` world-area units. This is
the coarse fixture's calibration convention, not a recovered physical constant.
With this convention, one coarse interior site contributes the legacy source
strength. Changing `A_ref` changes both propagation and particle-production
rates and must not be used to tune refinement outcomes after inspection.

For an active source i and unburnt recipient j, the graph contribution is

```
delta_h_j = dt * spreadRate * (areaWeight_i / A_ref) * kernel(i, j)
```

where the existing compact-support distance and upward-bias kernel is retained.
The recipient's area cancels when an area-proportional heat input is divided by
an area-proportional heat capacity; hence it does not multiply this intensive
increment again. This interpretation assumes a common capacity per area. It
does not account for material thickness, volumetric mass, or different specific
heat. Graph contributions accumulate in double precision and are stored in
Float32 heat once per recipient per phase, reducing splitting/order roundoff.
Source heat is not debited, so the resulting operation is not energy conserving.

Flame-to-scene heating continues to update intensive heat with the existing
kernel. Its raw unweighted sum changes when recipients are duplicated. Compare
the area-weighted actual stored increments, `sum_j(areaWeight_j * delta_h_j)`,
instead. Such totals have area-times-heat-state units and are proxies, not joules.

The optional measure-based scene feedback schedules `30` particle events per
simulated second per `A_ref` of burning area. This rate already incorporates the
legacy mean of 60 opportunities per second times a 0.5 acceptance probability;
an additional 0.5 gate would halve the intended calibration. A fractional event
accumulator and weighted source selection implement this policy. Exact duplicate
source coordinates are coalesced, then traversed in a frozen coordinate order,
so duplicating or reordering a representation does not change source-choice
probabilities or random-number assignment. The implementation sorts coordinates
lexicographically by x, y, z; groups sharing a coordinate are sorted by group
name. Area sums use ascending-value compensated summation. No rounding epsilon
is added at the event-floor boundary. Record any resulting threshold sensitivity
rather than manufacturing an extra event.

Service-cap deferral and particle-pool rejection are different outcomes. Log
both explicitly, including residual scheduled work and any dropped or discarded
events. In the frozen P2 contract, integer event-service-cap overflow is dropped
and counted; it is not queued as debt. Carry only the fractional event remainder
and cancel that fraction when no live source remains. Capacity rejection consumes
the scheduled event. Reject nonfinite or unsafe event counts. These rules avoid
transferring old source debt to later burners or emitting a delayed burst after
extinction; they do not restore lost heat. The primary outcome cases use
nonbinding graph, hot-sample, and event-service caps;
separate capacity controls expose capped behavior rather than allowing it to
confound the representation-invariance comparison.

## Hypotheses

**G: graph representation invariance.** With nonbinding caps and identical
physical sites, dividing source and recipient area among exact duplicates does
not change intensive state or ignition trajectories at common physical sites.

**F: feedback representation invariance.** On the raised-target fixture, the
measure policy produces the same scheduled events, random stream, particle
trajectory, and common-site scene evolution across duplicate representations.
The original whole-scene hash is representation-specific and cannot test this:
the number and IDs of scene nodes deliberately differ. Use a separately recorded
particle-state hash and common-anchor scene comparisons.

**Q: refinement sensitivity.** On a fixed physical surface and source patch,
measure weighting reduces the discrepancy among sampled
propagation trajectories relative to legacy per-primitive coupling. Refinement
need not yield exact equality. Passing G or F does not establish Q, and passing
this finite-grid test does not establish asymptotic convergence or physical truth.

## Frozen matrix

The intended full matrix has 56 cases. All use `dt = 1/60`, world-fixed layered
VPM, elapsed fuel clocks, and no external emitter, source-band reheating, embers,
or procedural turbulence. Preserve raw per-site snapshots and report sampling
resolution. A quick structural run does not replace a full outcome run.
Graph and refinement runs last 8 simulated seconds; closed-loop runs last 12.
Snapshots are taken every 15 steps (0.25 seconds). Both coupling arms use 1200
particles per layer, the P1 `recycle-cold` policy, and graph, hot-sample, and
scene-event service caps of 1,000,000.

1. **Graph duplicate matrix: 24 cases.** Use the cell-centred connected strip
   and disable
   both flame heating and scene particle feedback. Compare legacy and measure
   coupling, forward and deterministically shuffled primitive order (shuffle
   seed `73013`), and six representations:
   one copy, uniform two copies, uniform four copies, spatially varying copies
   everywhere, varying copies in the source group only, and varying copies in
   the target group only. Run deterministic seed 11; repeated seeds would not
   constitute independent evidence in these graph-only cases. Each physical
   site retains total area `0.0016`. Preignite the complete first two coarse
   columns (source area `0.016`), including every duplicate at those positions.
   The frozen spatial multiplicity map is
   `1 + ((xIndex + 2 * (zIndex + 2)) mod 4)`, where xIndex is `0..20` and
   zIndex is `-2..2`; retain the full map in the fixture metadata.
2. **Full-domain grid refinement: 8 cases.** Use the fixed cell-centred rectangle
   x in `[-0.02, 0.82]`, z in `[-0.10, 0.10]`, y `0.20`. Its area is `0.168`.
   The coarse grid has 21 by 5 cells of side `0.04`. Uniform refinement factors
   `1, 3, 5` give 105, 945, and 2625 sites with cell area `(0.04/factor)^2`.
   Odd refinement factors retain every coarse cell centre as a common anchor.
   The fourth representation subdivides the right 11 coarse columns into 3 by 3
   cells, retaining their centres: the predicate is `xIndex >= 10` (coarse
   centre x at least `0.40`), the cell interface is x `0.38`, and there are 545
   sites. This is a fixed coarse-cell partition, not an exact midplane split.
   Each site's area is its own cell area: no global normalization is applied.
   Preignite precisely the physical source patch `x < 0.06`, whose edges follow
   coarse cell boundaries. This gives source area `0.016` and initially unburnt
   target area `0.152` in every representation. Seed all source nodes directly
   and zero target nodes, rather than relying on a sphere that changes the
   burning measure under refinement. Compare legacy and measure coupling at
   seed 11, both feedback edges off. Verify the area sums, source mask, common
   coordinates, and non-overlapping cell partition before any simulation.
3. **Closed-loop duplicates: 24 cases.** Use the P0 raised-target geometry and
   both coupling edges. Compare legacy and measure coupling at one copy,
   uniform two copies, uniform four copies, and spatially varying copies, for
   seeds `11, 23, 47`. Keep each physical source and target site's total area
   fixed; all duplicate copies of a manually lit source must start lit. The
   raised-target multiplicity map uses the fixture's recorded integer `cell`
   coordinates, `1 + ((cell[0] + 2 * cell[1]) mod 4)`. Use
   the same P1 particle-capacity policy in the two arms and record it. No
   render-quality conclusion follows from this matrix.

Record exact run lengths, caps, particle budgets, initial lit IDs/area, fixture
area sums, multiplicity maps, and anchor maps in the manifest. Standard outcome
runs should cover both propagation onset and fuel exhaustion; report early
trajectories even if every variant eventually becomes fully charred. If the
executed matrix differs, identify the change before inspecting outcome data.

## Measurements and failure criteria

First verify exposure and geometry: nonzero graph heat in graph tests, nonzero
scheduled/admitted scene feedback in feedback tests, and at least some initially
unburnt recipients becoming heated. A no-change result without transport is an
unexposed test, not an invariance success. Record when ignition thresholds are
crossed rather than relying only on final totals.

For G, compare every shared physical anchor at every sampled checkpoint. The
predeclared numerical tolerance for intensive heat, fuel, and char is maximum
absolute difference `1e-5`. Report the raw maximum, not rounded agreement.
Sampled burning/charred states and first-observed ignition times must agree
exactly across duplicate representations. A threshold-crossing difference is
an invariance failure even when the precursor heat difference was small. Also
check the copies of each physical site agree internally. Area-weighted total
fuel consumption, char, ignited fraction, and actual heat deposits must match
within `1e-8 * max(1, abs(reference))`; raw counts need not match.

For F, additionally require identical scheduled/admitted/rejected event counts,
random draw counts, particle-state hashes, and layer occupancies at matched
checkpoints. Full-scene hashes and unweighted recipient heat totals are not
valid equality targets. Preserve and report a failure; do not relabel a changed
random stream as measurement noise. Legacy and measure policies are not
expected to have the same particle trajectory because their event laws differ.

For Q, report area-weighted recipient ignition-fraction and mean-char curves,
common-anchor heat and ignition times, and total actual area-weighted deposits.
The primary trajectory discrepancy is the time-averaged absolute difference in
recipient area-weighted ever-ignited fraction, integrated over the fixed
`0..6` second window by trapezoids at the recorded checkpoints. Compare coarse
versus finest, medium versus finest, and adaptive versus finest, separately for
legacy and measure. The finest is a numerical comparison reference, not ground
truth. Also report common-anchor differences without treating the sparsely
sampled anchors as an area integral.

Support for reduced sensitivity requires the measure coarse-to-fine discrepancy
to be smaller than the legacy discrepancy and the measure medium-to-fine
discrepancy not to exceed its coarse-to-fine discrepancy. An equal-zero metric
means that observable is unresolved at the sampling grid, not evidence of a
strict improvement. Nonmonotonicity, stalled fronts, increased discrepancy, and
adaptive-grid artifacts are reportable negative results. Do not select another
window, threshold, or source calibration after seeing them. Curves and anchor
results remain necessary because one scalar can hide compensating errors.

## Software checks and limitations

The actual API fields are `spreadMeasureMode` (`legacy` or `area`),
`spreadReferenceArea`, `spreadAreaFeedRate`, and authored point `areaWeight`.
Snapshots expose `particleStateHash`, `areaFeed.creditBalance`,
`areaFeed.fractionalCredit`, `areaFeed.wholeEventsPending` (zero),
`areaFeed.burningArea`, and `areaFeed.sourceWeightSum`. The event ledger is

```
areaFeedCreditsGenerated
  = areaFeedAttempts + areaFeedServiceCapDropped
    + areaFeedCancelledCredits + areaFeed.fractionalCredit
areaFeedAttempts = areaFeedAdmitted + areaFeedBlocked
```

Compare the ledger within floating accumulation error and report its maximum
residual. No-live-source steps cancel the fractional remainder; disabling scene
feedback while sources remain preserves the fraction but generates no new
credit. Area-mode admission has no random rejection coin. The global and
per-group proxy counters are `areaWeightedFlameHeatDeposited`,
`areaWeightedGraphHeatDeposited`, and `areaWeightedFuelConsumed`. The snapshot
scene also records represented area and area-weighted fuel, heat, and char.
These fields describe stored state and actual increments, not physical energy.

- Validate finite positive area, constant total represented area, and identical
  initial burning area before running comparisons. Reject missing/invalid area
  for an explicitly measure-based authored scene rather than guessing it.
- Preserve legacy default replay. Reset the event accumulator, source-selection
  bookkeeping, all counters, RNG, and scene/particle states between runs.
- Confirm measure-mode restart determinism and world-fixed camera invariance.
- Check graph, hot-sample, and event caps are nonbinding in primary cases from
  actual counters, not just large configured numbers. Keep particle-pool
  rejection and P1 cold-state removal measurable when that policy is engaged.
- Check all event outcomes reconcile, including cap service, rejected capacity,
  residual fractions, debt, and any explicit drops. Record floating-point
  handling at integer accumulator boundaries; it must not hide real deficits.
- Preserve failed runs and source fingerprints. Software-test success alone is
  not a positive research result, and three seeds do not establish statistical
  generality.

The method requires meaningful authored measure. Real captured splat area,
overlap, occluded surfaces, anisotropic footprints, varying thickness/materials,
and topology remain unresolved. No global point-count division addresses these
issues. Finite-radius quadrature, threshold nonlinearities, timestep dependence,
budget-limited transport, and lossy cold-particle replacement remain. The new
event law also changes temporal emission statistics. Full physical validation,
capture-scene performance, perceptual quality, and research novelty need evidence
beyond these controlled representation tests.
