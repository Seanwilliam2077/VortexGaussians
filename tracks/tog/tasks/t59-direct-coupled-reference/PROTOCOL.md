# T59 — fixed six-trajectory direct coupled qualification

Question: does the T58-qualified ordinary same-operator solver preserve the coupled reference and allow all unchanged short-window refinement gates to be evaluated? [T58 DECISION](../t58-separable-solver-qualification/DECISION.md) precedes this task. T56 remains failed and T57 remains timed out regardless of this result.

## One fixed schedule

After source review, OS-only preflight and input freeze, allow exactly one scientific child, no more than 600 seconds, with no pilots, retries, installations, searches, fallback, cache or candidate method. Runtime is bundled Python 3.12.14/NumPy 2.3.5, asserted by the child.

Run all six new trajectories in this order, from the unchanged initial state to .25, with snapshots 0,.125,.25:

| Case | R | nr/nz | dt | angular nodes |
|---|---:|---:|---:|---:|
| S64 | 8 | 64/128 | .0025 | 32 |
| S128 | 8 | 128/256 | .0025 | 32 |
| S256 | 8 | 256/512 | .0025 | 32 |
| T128 | 8 | 128/256 | .00125 | 32 |
| D192 | 12 | 192/384 | .0025 | 32 |
| Q128 | 8 | 128/256 | .0025 | 64 |

A complete schedule has 700 steps, 1400 transport stages and 1418 direct elliptic solves, each with a fresh factorization and independently evaluated true original residual. No CG solve. No old trajectory substitutes for a new one. Freeze new formulation/protocol/source/runner/preflight, T55 source/formulation/task, T56 source/formulation/protocol/result/execution/manifests and old S64/S128 case/raw/logs, T57 failure/decision/memory and T58 solver/decision/result/receipts/manifests/review, plus executable identity. Validate all frozen bytes before and after the child. One exclusive execution marker prevents another invocation.

## All required gates

- Initial analytic velocity/Jacobian core errors: each <=.01 for S64, each <=.005 for all other cases.
- Space pairs S64/S128 and S128/S256: physical vorticity <=.01 and velocity <=.02 at every saved time.
- Nonzero-time spatial-error reduction >=1.5 unless both coarse/fine pair vorticity errors <=1e-8.
- Independent controls S128/T128, S128/D192, S128/Q128: physical vorticity and velocity each <=.01 at every saved time.
- Every physical pair: full-box absolute axial circulation-centroid difference <=.01 initial width and covariance Frobenius difference <=.01 initial analytic norm. No altered denominator, alignment, time shift or core-restricted means.
- Every Euler/reconstruction stage finite and nonnegative without clipping; every reconstructed face retains its original upper bound 2*q*(1+1e-12)+1e-300; outgoing CFL <=.5 and volume divergence <=1e-10.
- Every direct solve has finite positive pivots and independent original W-weighted RHS-relative residual <=1e-10.
- Every case circulation/outflow ledger relative discrepancy <=1e-10, saved q-squared relative drift <=.02 and axial-impulse relative drift <=.01. Outer-shell values are diagnostics, not exterior error certificates.
- Additional solver-port category: new S64/S128 vs matching original T56 S64/S128 at 0,.125,.25. Both reconstructed physical vorticity and velocity relative differences <=1e-7 under unchanged common-core integration and old-field denominators. This is q weight 2*pi*r³, u weight 2*pi*r, not the q-squared invariant norm.

The resulting eleven predicate categories comprise the original ten plus solver-port regression. Structural/runtime/preservation, positivity, residual or unsafe-stage failures terminate the child. Safely evaluable metric failures stay failed and finish only the frozen schedule, without tuning; the final result requires all predicates. No partial stage/case/checkpoint upgrades the whole-task result.

## Resources and evidence

One OS-only preflight and launch check require >=3 GiB available host physical memory. Reuse unchanged T57 Windows byte-valued observer at .25 s intervals; stop above 2 GiB observed lifetime peak working set, at 600 seconds or on a live observer error. Kill only this scientific child. This observed stop is not memory reservation or an allocator cap; disclose sampling, unavailable final query and kill/exit tail. Private/pagefile counters are diagnostic. Dense K, construction temporaries, FFT/Thomas buffers, retained snapshots and regression arrays all count. Do not infer process peak from K alone.

The child includes imports, loading/hash checks, geometry, all Green matrix construction/application, direct RHS/FFT/factor/triangular/inverse and independent residual work, analytic initial checks, transport, diagnostics, comparisons and all output. Per-stage timers are nested attribution; whole supervised child time is authoritative. Do not fabricate CG iteration fields or omit setup. Save each actual field snapshot immediately as NPZ and only then a metadata/hash record. Record raw/step logs and case results in ignored local storage. A present interrupted NPZ without completed valid metadata remains an incomplete file. Release each K after final dependent diagnostics and before full-array stacking/save and the next case.

Report all six case costs, phase sums, method/solve/factor/residual counts, source/runtime/raw identities, complete result or preserved partial checkpoints, memory observation and failure reason. Existing T56+T57+T58 supervised children cost 1317.5624378999928 s; retain it separately and add this invocation for cumulative cost. Earlier project costs remain in their receipts. T58's manufactured solve time is not a trajectory-speedup measurement.

Success supports only the ordinary coupled short-window reference and solver port. Full t=1, fair ordinary Gaussian comparison, further scenes and a useful core method remain separate. Failure closes this task without immediate repair, changed dt/residual/thresholds, longer budget, alternative solver or rerun. Decide the next bounded action from actual evidence; art inactive, main unchanged, automation deleted.
