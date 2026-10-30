# T58 — completed fixture qualification and its limits

The sole scientific invocation completed with return code 0 and status `completed_qualified_same_operator_fixtures_only`. The [frozen protocol](PROTOCOL.md) and [43 input identities](input-manifest.json) preceded execution. All six categories pass: transforms, original residual, saved phi agreement, saved velocity agreement, saved Jacobian agreement and manufactured system. There were exactly 18 saved-state solves and one manufactured solve; zero new flow trajectories, Green matrices, CG solves or candidate trajectories.

## Saved-state evidence

All values below are maxima over the three original times 0,.125,.25. Weighted phi error uses the whole original box; velocity and Jacobian use the fixed physical core and old-field denominator. Jacobian error is the combined five-component Frobenius norm. Thresholds are residual 1e-10, phi 1e-8, u and J each 1e-7.

| Case | Original residual | phi difference | u difference | J difference | Three direct solves (s) | Fixtures before JSON writes (s) |
|---|---:|---:|---:|---:|---:|---:|
| S32 | 3.8664963e-15 | 9.3208679e-11 | 7.3811066e-11 | 1.4840466e-10 | .001370400 | .023941100 |
| S64 | 6.1792219e-15 | 1.5042789e-10 | 1.1044315e-10 | 3.8066246e-10 | .003741300 | .049958100 |
| S128 | 9.3668410e-15 | 3.2576940e-10 | 2.2089482e-10 | 9.7383896e-10 | .007155700 | .098152400 |
| T64 | 6.3546152e-15 | 1.5042815e-10 | 1.1044333e-10 | 3.8065956e-10 | .002552400 | .027090800 |
| D96 | 1.0767235e-14 | 2.1455380e-10 | 4.4562856e-11 | 1.4933170e-10 | .005017100 | .058212900 |
| Q64 | 6.2000477e-15 | 1.5042785e-10 | 1.1044313e-10 | 3.8065764e-10 | .002470300 | .029195200 |

Reconstructing original phi/boundaries reproduces all 18 saved velocity fields and all six saved initial Jacobians bit-for-bit. Later-time old Jacobians are reconstructed from the original saved fields, without an elliptic solve. Recomputed old CG residual has maximum 9.9371535285e-11 under the separately implemented flux stencil; this diagnostic does not rewrite the original assembled-stencil verdict. Historically failed coarse cases serve only as algebraic fixtures.

## Transforms and largest-grid system

For axial lengths 64,128,192,256,512, all 20 deterministic round trips pass, maximum relative error 3.2229148166e-16. All 15 analytic forward-mode checks pass, maximum 1.0056081173e-15. All 15 operator-normalized eigen residuals pass, maximum 4.5155024081e-16; the separately reported eigenvalue-relative diagnostic has maximum 8.4014817683e-12. The normalization was explicitly frozen before execution; these two residual definitions are not interchangeable.

The manufactured system has nr/nz=256/512, R=8 and the prescribed modes 1,7,n with a nonconstant radial factor. Its original weighted residual is 1.8623116251e-15 and known-phi relative error 1.7100805461e-13. Minimum Thomas pivot is 1032.2989688245; minimum axial eigenvalue is .03855302123. Its solve takes .006388800 s and complete fixture .018783100 s. This signed linear-algebra check is not a physical vortex, a new fluid trajectory or a measurement of S256's dynamic Green-boundary cost.

## Costs, memory and retained data

| Scope | Seconds |
|---|---:|
| RHS assembly, all 19 systems | .001008400 |
| Forward transforms | .005969500 |
| Fresh radial factorizations | .010658900 |
| Triangular solves | .005479300 |
| Inverse transforms | .004839500 |
| Complete direct-solver calls | .028696000 |
| Loading 18 original states | .096967200 |
| Validation/reconstruction, all 19 fixtures | .110192900 |
| Fixtures through raw saves, before individual JSON writes | .305333600 |
| Transform checks | .036606000 |
| Child elapsed before writing result | .514309600 |
| Entire supervised child | **.768266600** |
| Supervisor through pre-receipt point | .893489200 |
| Earlier T56+T57 supervised children, including timeout | 1316.794171300 |
| Cumulative T56+T57+T58 supervised children | **1317.562437900** |

Phase timers are attribution and are not all disjoint from the aggregate rows. Per-fixture timers stop before their JSON record writes; the manufactured fixture's .018783100 s has the same boundary. Whole-child time includes imports, hashing/loading, factor setup, checks and all output; no cache setup is hidden. The supervisor number excludes its final receipt write. Earlier research tasks retain their own costs. The saved-array review additionally reports .1663152 s of reductions and .4073576 s total from its imports/hash work to the point before printing; those are review costs, not another scientific solve or included in the child total.

One OS-only preflight recorded 27,193,638,912 available host bytes; launch recorded 27,049,332,736, both above 3 GiB. Four .25-second-spaced observer samples retained maximum OS lifetime peak working set 60,043,264 bytes, below the 2 GiB observed stop. Maximum sampled private usage is 798,400,512 bytes and peak pagefile 819,228,672 bytes; neither is a separate gate. There is no recorded observer error. This is an observed process metric, not a memory reservation, allocator cap or continuously sampled proof. The retained lifetime counter can include earlier peaks, but observation/termination timing limitations still apply.

Execution ran from 2026-10-30T01:26:11.794381+00:00 to the receipt's recorded finish at 01:26:12.648374+00:00, with bundled Python 3.12.14/NumPy 2.3.5. The executable and all 43 frozen files remained byte-identical. The 19 new NPZs total 18,101,784 bytes, retained in ignored local storage alongside 18 fixture JSONs, transform/manufactured records, stdout, empty stderr and memory JSONL. [execution.json](execution.json) and [result.json](result.json) record individual hashes and all unrounded numbers; no large arrays enter Git.

## Review and decision boundary

The [review](../../../validation/t58-separable-solver-review.md) independently reduces the saved arrays and checks original assembled-stencil residuals, reconstruction and identities. Its differently ordered original stencil gives maximum saved-state new residual 1.1624278431e-14 and manufactured residual 2.1019381518e-15; both pass. Known-phi error remains 1.7100805461e-13. These small floating-point differences are disclosed. This is source/saved-data validation with pre-run reviewer participation, not independent replication or a rerun of FFT/Thomas/CG.

These results support replacing the linear solver in a separately qualified coupled reference. They neither qualify a physical trajectory nor measure a matched old/new speedup. T56's spatial failure and T57's resource failure remain unchanged. The original full t=1 task, ordinary complete-tangent Gaussian comparison and a useful new TOG mechanism remain outstanding. [DECISION](DECISION.md) fixes the next finite preparation.
