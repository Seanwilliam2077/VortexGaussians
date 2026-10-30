# T56 — six completed trajectories, failed spatial qualification

The single scientific child returns code 2 with `completed_failed_checks`. All six fixed cases finish all steps and snapshots. There is no runtime failure or retry. The only false predicate category is **vorticity_disagreements**; the other nine are true. Per the frozen all-required contract, T56 is not a qualified short reference. The passing finer pair is partial evidence, not a substitute success label.

## Where the gate fails

The same conservative limited piecewise-linear reconstruction is integrated on a common finer partition with physical vorticity weight 2*pi*r^3. No alignment, coarse restriction, field clipping or candidate fit is used. Values below are relative discrepancies, not measured true errors of the underlying Euler solution.

| Comparison | t=0 | t=.125 | t=.25 | Fixed 1% field gate |
|---|---:|---:|---:|---|
| S32 / S64 | 0.01627836698 | 0.01631902463 | 0.01662422151 | fails at all three times |
| S64 / S128 | 0.004177862998 | 0.004216435278 | 0.004347559713 | passes |
| S64 / T64 | 0 | 7.495674241e-8 | 1.213714272e-7 | passes |
| S64 / D96 | 0 | 1.099005657e-7 | 2.201247528e-7 | passes |
| S64 / Q64 | 0 | 2.072241308e-16 | 3.039886127e-16 | passes |

The failed S32/S64 comparison already exceeds 1% **before time advancement**, with 1.627836698% initial disagreement and 1.662422151% at t=.25. This localizes an initial coarse-reconstruction resolution problem within this metric. It does not prove that all later discrepancy has the same cause, isolate each spatial operator's error, or demonstrate a failure of the Gaussian carrier.

The nonzero-time spatial reduction factors are 3.870336801 and 3.823805216, above the fixed 1.5 requirement without a small-error waiver. The finer-pair agreement is consistent with useful spatial convergence but is not a continuum-error bound. T64 independently halves dt; D96 expands the box with h, dt, angular order and source-cell rule fixed; Q64 changes only angular order. Radial/axial source-integration error remains coupled to spatial refinement. Tiny control differences cannot independently certify true boundary accuracy or unknown exterior tails.

| Comparison | Maximum velocity discrepancy | Maximum axial-centroid discrepancy (widths) | Maximum covariance discrepancy (initial norm) |
|---|---:|---:|---:|
| S32 / S64 | 0.01188508424 | 0.0002178666340 | 0.002859621198 |
| S64 / S128 | 0.002940626892 | 0.00005824637465 | 0.0005320250111 |
| S64 / T64 | 3.307865783e-8 | 1.470184582e-8 | 1.412445278e-8 |
| S64 / D96 | 8.142783947e-6 | 3.023788248e-7 | 1.166922750e-8 |
| S64 / Q64 | 9.327521270e-15 | 6.938893904e-18 | 4.081885327e-16 |

Velocity gates are .02 for spatial pairs and .01 for controls; moment gates are .01. All pass. Full covariance is evaluated, including the off-diagonal entry; neither moment comparison realigns the primary field. The source mapping differs from T55, so all initial analytic checks were recomputed inside this child rather than inherited:

| Case | Initial core u relative error | Initial core full J relative error | Case threshold |
|---|---:|---:|---:|
| S32 | 0.01351681060 | 0.008264908819 | .02 |
| S64 / T64 | 0.003381846117 | 0.002059174521 | .01 |
| S128 | 0.0008456339348 | 0.0005143955758 | .005 |
| D96 | 0.003382540598 | 0.002058880419 | .01 |
| Q64 | 0.003381846117 | 0.002059174521 | .01 |

## Evolution diagnostics, with their qualification limit

All 700 SSPRK2 steps complete with 1,400 transport stages and 1,418 elliptic solves including saved endpoints. The largest outgoing CFL is .03995456193, below .5. All cell/Euler-stage/face positivity checks pass without clipping, and saved negative cell masses are zero. Maximum recorded volume divergence is 2.842170943e-15; maximum true weighted Poisson residual is 9.999746638e-11. The largest solve uses 639 iterations of the 2000 cap, with zero restarts. The circulation/boundary-flux ledger discrepancy is at most 2.362212828e-16 relative to initial circulation. These checks support execution consistency, not reference accuracy.

The largest saved relative q-squared invariant drift is 0.002310905650 (0.2311%), and largest axial impulse drift 0.000677205059 (0.06772%), both on S32 and below their .02/.01 gates. The physical vorticity squared norm can change through stretching; it is recorded without being mislabeled as a conserved quantity. Later exterior mass is unmeasured. The outer two-cell circulation fractions are only support diagnostics: at t=.25 they range from 1.060993203e-30 on D96 to 6.613348444e-13 on S32.

As an **unqualified-reference observation**, the finest saved case has axial centroid about 0.08839559501 initial widths at t=.25 and meridional cross-covariance -0.01849964926. These describe the saved numerical trajectory; they are not a candidate error, accepted physical benchmark, or satisfaction of the t=1 meaningful-motion gate. No Gaussian trajectory or snapshot fit was evaluated. The original physical task remains unchanged.

## Complete numerical execution costs

Existing bundled Python 3.12.14/NumPy 2.3.5, no installation or new source acquisition. A dense geometric boundary matrix is prepared separately for each case and applied to current q at every stage and endpoint. These are ordinary reference costs, not proposed-method performance results.

| Case | Steps | Solves | Kernel build seconds | All Poisson solve seconds | Case seconds before record write |
|---|---:|---:|---:|---:|---:|
| S32 | 100 | 203 | 0.082897 | 1.074626 | 1.272216 |
| S64 | 100 | 203 | 0.827159 | 6.143461 | 7.603354 |
| S128 | 100 | 203 | 12.988707 | 40.250473 | 56.719345 |
| T64 | 200 | 403 | 1.107787 | 13.085002 | 15.235456 |
| D96 | 100 | 203 | 5.250395 | 18.585937 | 25.362418 |
| Q64 | 100 | 203 | 2.284719 | 7.003699 | 9.852634 |

The full supervised child took **116.53663460002281 s**, within the frozen 600 s limit. Child timer before result writing: 116.29796609992627 s. Supervisor before receipt writing: 116.61247589997947 s. Final comparison work took .06366179999895394 s inside the child. These nested timers have different endpoints and are not extra additive executions. Complete boundary applications, reconstruction/transport, initialization, snapshots and output overhead remain in [result.json](result.json) and case totals. Preparation, mathematical review and later publication are separate work, not hidden inside the solve-only timing.

The six kernels evaluated 1,045,692,416 scalar target/source/angular pairs during construction. The largest matrix alone is 134,742,016 bytes; this is not total peak process memory, which was not measured. The 1,418 solves used 515,506 CG iterations. Six ignored NPZs total 26,258,520 bytes and six flushed per-step logs total 981,157 bytes; saved stdout is 2,264 bytes, stderr empty. All raw/log identities, case parameters and frozen input/executable checks are retained. This is one scientific invocation, not six separately retried jobs.

T55's 3.9182514-second initial qualification, the earlier scalar failure/diagnostics and all historical costs stay in their original records. No earlier status is changed. This complete T56 failure and its six-case cost must remain part of any later reference-development accounting; a later task cannot charge only the passing fine pair.

## Review and consequence

Two pre-run mathematical/code readbacks led to conservative reconstruction/metric choices and explicit unknown later exterior tails before freeze. The frozen program was not altered after seeing results. Post-run review independently reduces existing reconstructions and validates the recorded comparisons, moments, counts, identities and predicates without importing the evaluator or rerunning kernels, solves or trajectories. Reviewer pre-run participation is disclosed in [the saved-data review](../../../validation/t56-coupled-review.md).

The next useful evidence is a separately frozen finer-resolution qualification with the same algorithm and physical thresholds, retaining this failure and reusing existing data explicitly. See [DECISION.md](DECISION.md). No qualified full t=1 reference or TOG mechanism is established.
