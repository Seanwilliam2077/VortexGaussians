# T59 — all short-window reference and port checks pass

The sole scientific child completed six new trajectories and all eleven frozen categories with status `completed_qualified_short_reference_only`, return code 0. It performed 700 steps, 1400 transport stages and 1418 ordinary direct elliptic solves, each with fresh factors and an independently checked original residual. All 18 snapshots have completed NPZ and valid metadata/hash records. No CG or candidate trajectory was run.

This is the first completed qualification of the finer short-reference schedule. It does not retroactively change T56's failed coarse-grid gate or T57's timeout, replace them with successes, or qualify the original full t=1 task.

## Field agreement, controls and invariants

The original common-core physical vorticity differences are:

| Pair | t=0 | t=.125 | t=.25 |
|---|---:|---:|---:|
| S64/S128 | .0041778630 | .0042164353 | .0043475597 |
| S128/S256 | .0010569842 | .0010758189 | .0011194295 |

All satisfy .01. Nonzero-time coarse/fine ratios are 3.919279925 and 3.883728097, exceeding 1.5 without the small-error waiver. Corresponding maximum velocity differences are .0029406269 and .0007330637, below .02.

| Control against S128 | Max vorticity difference | Max velocity difference |
|---|---:|---:|
| Half time step T128 | 1.2668210e-7 | 3.2551976e-8 |
| Larger domain D192 | 5.4847335e-8 | 2.0362767e-6 |
| Doubled angular rule Q128 | 2.6025727e-16 | 2.0242376e-15 |

All satisfy their .01 gates. Across all physical pairs and saved times, the largest absolute axial centroid discrepancy is 5.8246376e-5 initial widths, and covariance relative discrepancy .0005320250; both remain below .01. These moments use each simulation's full box, whereas the field norms use the frozen common core r<=4, |z|<=4. Neither is an unrestricted whole-space error certificate.

Additional old/new port regression passes at all three saved times for both S64 and S128. The maximum physical vorticity difference is 3.4959035203e-12 and velocity difference 2.2131697312e-10, under the old-field denominators and 1e-7 gates. This confirms agreement on these trajectories after the solver replacement, without changing the historical reference qualification.

Across all cases/stages:

| Quantity | Maximum | Gate |
|---|---:|---:|
| Outgoing CFL | .07997729211 | .5 |
| Volume-flux divergence | 5.6843419e-15 | 1e-10 |
| Original weighted RHS-relative solve residual | 1.7202832e-14 | 1e-10 |
| Circulation/outflow ledger relative discrepancy | 2.3622128e-16 | 1e-10 |
| Saved q-squared relative drift | .00053125570 | .02 |
| Axial impulse relative drift | .00017068032 | .01 |

Every accepted Euler/reconstructed state is finite and nonnegative, and the original transport-face upper bound is enforced. Initial analytic u/J errors pass in all cases; finest S256 errors are .0002114196104 and .0001285752645. No clipping, tolerance changes or candidate repair occurs.

As a short-window observation only, S256's axial circulation centroid is .08838071146 at .25, with initial axial centroid approximately zero. This cannot be compared with the original task's displacement requirement at t=1. No Gaussian trajectory was scored here.

## Complete cost and resource evidence

| Case | Steps | Green build (s) | Boundary applications (s) | Checked elliptic calls (s) | Case before JSON write (s) |
|---|---:|---:|---:|---:|---:|
| S64 | 100 | .709590100 | .184280299 | .193386999 | 1.345386300 |
| S128 | 100 | 11.445336900 | 1.894722700 | .791941298 | 15.261498800 |
| S256 | 100 | 98.602655700 | 14.496828600 | 3.880622400 | 127.443544400 |
| T128 | 200 | 12.443274200 | 3.764829599 | 1.492224800 | 19.326091900 |
| D192 | 100 | 40.841008000 | 6.180956200 | 1.603658300 | 50.824670100 |
| Q128 | 100 | 24.337218300 | 1.883503999 | .719809800 | 27.749925000 |

These are single-run attribution values, not repeated performance benchmarks. Every new case rebuilds K; the old S64/S128 fields supply regression comparisons only. Complete Green construction costs 188.379083200 s, boundary applications 28.405121397 s, checked elliptic call wrappers 8.681643598 s, reconstruction 5.839520000 s and transport 7.349679301 s. Boundary setup now accounts for most measured work; this does not establish a research opportunity or inherent ordinary-method bottleneck.

The internal checked-direct timer totals 8.582220499 s, including .218647199 RHS assembly, 1.729986101 forward transforms, 2.241696301 fresh factorizations, 1.278929900 triangular solves, 1.286491400 inverse transforms, .284089603 independent original-RHS assembly and 1.153045199 original residual checks, plus other wrapper overhead. The outer elliptic-call and internal checked-solve timers are nested, not additive. Counts are 1418 for solves, each transform, factorization and original residual; factor reuses and new CG solves are zero.

The physical comparison takes .168440000 s and old-field regression .089616800 s. Each case separately records immediate checkpoint and final-array save costs. Every Green matrix is released after its final dependent diagnostic and before final stacking/saving. The whole supervised child, including imports, setup, all records and output, takes **242.85603079991415 s**. Internal time before result writing is 242.45010559994262 s; supervisor time before its final receipt write is 243.6079251000192 s. Do not add nested timers or treat per-case pre-record times as the complete run.

Prior T56+T57+T58 child cost remains 1317.5624378999928 s, including the failed invocation. Through T59 the cumulative four-task child cost is **1560.418468699907 s**; older tasks retain their own receipts. Review/postprocessing costs are separately disclosed in the review and are not scientific reruns. No equal-work speedup ratio is claimed from comparing different schedules.

The OS-only preflight recorded 27,415,478,272 available host bytes and launch 27,396,128,768, above 3 GiB. Across 970 observations the maximum OS lifetime peak working set is **2,056,495,104 bytes**, below 2 GiB (2,147,483,648 bytes). The approximately 91 MB difference is observed headroom, not a future allocation guarantee. Maximum sampled private usage is 1,976,680,448 bytes and peak pagefile 2,037,846,016 bytes; neither is a separate gate. The final sample at 242.855247600 s retains the lifetime peak with no recorded query error. Sampling and exit/termination tails are limitations of the observation method.

## Provenance and claim limits

Bundled Python 3.12.14/NumPy 2.3.5 is asserted at entry and reported in the result. All 40 frozen input files and executable bytes match after completion. The 24 NPZs total **217,263,132 bytes**: 18 immediate field checkpoints and six complete case arrays, all ignored locally. All six case metadata files, 18 snapshot metadata files, raw files, six stage logs, checkpoint ledger, stdout/stderr and memory records have recorded identities in [execution.json](execution.json); no failed/invalid metadata or terminal-failure record exists. [result.json](result.json) retains all unrounded comparisons, methods, counts, costs and diagnostics.

Pre-run review corrected a source manifest filename mismatch before freeze and before the only scientific invocation. Runner validation also distinguishes present metadata from validated completed records; an incomplete file cannot count as a finished case/checkpoint. No scientific result was used to change the protocol.

The [source/saved-array review](../../../validation/t59-direct-coupled-review.md) independently reads all 24 NPZs, checks that 18 checkpoint fields match complete case arrays, reconstructs all saved u/J, and reduces the 15 physical comparisons, 18 full-box moment sets and six port comparisons. It verifies all 700 steps, 1400 stages and 1418 solve records; the independently applied original stencil on the 18 saved phi fields has maximum residual 1.6857665650e-14. The review reports .5035090 s for array/log work and .9133640 s including imports/hashing to before printing, separately from the scientific child. Pre-run participation is disclosed; no solver, FFT, Green, CG or flow is rerun, so this is not independent replication. The numerical conclusion is limited to this short-window reference and solver port. Full t=1 physical quality, broader scenes, a strong-baseline advantage and a useful new TOG method remain unestablished. [The next decision](DECISION.md) proceeds to that original finite-time task rather than inventing another short success.
