# T58 — next qualify the ordinary solver inside the coupled reference

All frozen linear-system checks pass. Preserve the limited result `qualified_same_operator_fixtures_only`; the direct solver is an ordinary numerical implementation, not a TOG contribution. T56 stays failed and T57 stays `timeout_no_retry`. Their evidence and costs remain intact.

## Selected finite next task: T59

Prepare and freeze **one new coupled short-reference qualification**, reusing the same physical equation and transport/boundary algorithm. Six new trajectories will use the same T58 direct solver, avoiding a mix of old CG and new direct solves in the physical refinement controls. Existing T56 S64/S128 arrays serve only an additional solver-port regression; they do not substitute for new trajectories.

| Case | R | nr/nz | dt | Green angular nodes | Role |
|---|---:|---:|---:|---:|---|
| S64 | 8 | 64/128 | .0025 | 32 | First spatial level and old/new regression |
| S128 | 8 | 128/256 | .0025 | 32 | Second spatial level and old/new regression |
| S256 | 8 | 256/512 | .0025 | 32 | Third spatial level |
| T128 | 8 | 128/256 | .00125 | 32 | Independent time control against S128 |
| D192 | 12 | 192/384 | .0025 | 32 | Independent domain control against S128 |
| Q128 | 8 | 128/256 | .0025 | 64 | Independent angular control against S128 |

Order as shown; all start from the identical prescribed initial condition and run [0,.25], saving 0,.125,.25. Complete execution entails 700 steps, 1400 transport stages and 1418 elliptic solves. This is neither a restart of T57 nor a full t=1 task. No scientific invocation is authorized before T59 has its own source/protocol/input freeze.

## Changes allowed before that freeze

Use unchanged T56 initialization, conservative positivity-limited reconstruction/flux, SSPRK2, dynamic current-q dense Green matrix, velocity/Jacobian reconstruction, fixed core and physical metric definitions. Read and review an explicit source-level change that binds the elliptic step to the frozen T58 solver and independently checks the true original weighted RHS-relative residual at every solve. Rebuild factors on every call as in T58; no across-call cache, tolerance tuning, changed boundary approximation, installation, source-search batch or new candidate.

Records must identify the direct method and count/time RHS assembly, forward transform, factorization, triangular solve, inverse transform and original residual validation. Do not present a fictitious CG iteration field as evidence of free work. The complete coupled cost includes all dense Green construction/application, reconstruction, transport, comparisons and saving.

Save each snapshot immediately as a checkpoint, so an interruption preserves actual fields. Release each case's Green matrix after its final snapshot and all dependent diagnostics, before stacking/writing final arrays or starting the next case. These are explicit output/lifetime changes, not mathematical changes; freeze and review them. A checkpoint is partial evidence and cannot establish whole-task qualification. Do not resume missing T57 arrays from logs.

## Fixed gates to carry into T59

Retain T57's physical gates and definitions without editing historical files:

- Initial velocity/Jacobian oracle errors: S64 each <=.01; other new cases each <=.005.
- Both spatial pairs S64/S128 and S128/S256: reconstructed vorticity relative L2 <=.01 and velocity <=.02 at all three times. At each nonzero time require coarse/fine vorticity-error reduction >=1.5 unless both pair errors <=1e-8.
- Independent time/domain/angular controls against S128: each vorticity and velocity difference <=.01 at every saved time.
- All physical comparison pairs: absolute axial circulation-weighted centroid difference <=.01 initial width and covariance Frobenius difference <=.01 initial analytic covariance norm, using the existing full-box moment diagnostics. The common-core restriction applies to field errors, not these moments; no restricted means, alignment or changed denominator.
- Every Euler/reconstruction stage: finite nonnegative q and reconstructed face state, retaining the original face upper bound; outgoing-volume CFL <=.5 and flux divergence <=1e-10; no clipping repair. Every elliptic call: original true weighted residual <=1e-10.
- Circulation outflow ledger relative discrepancy <=1e-10, q-squared invariant relative drift <=.02 and axial-impulse relative drift <=.01 under the existing full-box diagnostics.

Add one explicitly new solver-port regression category: for each of S64 and S128 at 0,.125,.25, compare new direct-run q and u against the matching original T56 saved fields, using the same world-coordinate core, physical weighted reconstructed L2 rules and **old-field denominator**, without alignment or refit. Here the q comparison is physical vorticity error with weight 2*pi*r^3, and the velocity comparison uses 2*pi*r; neither is the q-squared invariant's 2*pi*r norm. Require both relative errors <=1e-7. This new gate tests integration consistency; it neither changes nor replaces the 1% reference gates or retroactively relabels T56. The old CG uncertainty remains part of the comparator. All categories are required.

## Fixed resource boundary and interpretation

Allow one scientific child with **600 seconds total**, including imports, Green setup, all fresh factors, residual checks, every trajectory and output. Zero pilots, retries, fallback solvers or automatic parameter changes. One OS-only preparation probe and launch check must show >=3 GiB available host physical memory. Reuse the .25-second OS lifetime peak-working-set observer, stopping above 2 GiB, on timeout, or live observer error; report private/pagefile counters and sampling/kill-tail limitations. This is an observed stop, not a hard allocator limit.

The budget is a finite investigative ceiling, not a performance prediction. T58's .00639-second manufactured solve cannot be multiplied into a credible whole-trajectory runtime or compared against T57 as a speedup. Dense K, construction temporaries, transform/Thomas work, snapshots and old regression fields all contribute to peak memory; K's own size does not certify the total. Include the complete prior T56+T57+T58 child cost 1317.5624378999928 s separately and cumulatively.

If any numerical, regression, preservation or resource requirement fails, preserve all completed checkpoint/log evidence and close T59 as failed/partial without tuning and rerunning in that task. No single successful case or saved stage qualifies the full reference. If all pass, the result supports only the coupled **short-window** reference and solver port. Freeze a later full-t=1 experiment and its budget before any extension.

The next scientific purpose after a qualified reference remains the existing [T55 full-task question](../t55-axisymmetric-reference/TASK.md): does the original carrier deliver useful finite-time motion/shape accuracy beyond ordinary fitting? The fair ordinary complete-tangent comparator is the translation-equivariant projection described in [T57's decision](../t57-finer-short-reference/DECISION.md), with actual axial speed c=beta_star*a_z and no fitting to reference snapshots. No initial residual-times-duration estimate can replace that measurement.

The independent conceptual scope review agrees with six same-solver trajectories, separate port regression and explicit Green/memory/output accounting. No T59 implementation or run occurred in T58. Full research goal remains active and unachieved; art inactive, main unchanged, automation deleted.
