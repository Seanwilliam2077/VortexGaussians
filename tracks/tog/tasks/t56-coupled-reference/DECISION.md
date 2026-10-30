# T56 — retain the failure; test one fixed finer reference level

T56 fails its complete frozen reference contract. Its sole failed category is the S32/S64 reconstructed vorticity discrepancy, already 1.628% at t=0 and 1.662% at t=.25, above 1%. The finer pair is around .42%–.43%, with spatial reduction factors around 3.8; independent time/domain/angular controls are much smaller. This evidence supports one specific next question: **can an unchanged ordinary algorithm satisfy the same reference requirements on a finer resolution range, with its complete cost counted?** It does not support changing the limiter/metric to erase the failure or treating a passing subset as a T56 success.

## T57 preparation: new finer-resolution qualification

Keep T56 failed and immutable. Prepare a new task that reuses the saved S64 and S128 cases, and adds exactly the following four reference trajectories, still only to t=.25:

| New case | R=Z | radial/axial cells | dt | angular order | Role |
|---|---:|---:|---:|---:|---|
| S256 | 8 | 256/512 | .0025 | 32 | new finest spatial level |
| T128 | 8 | 128/256 | .00125 | 32 | independent time control at finer base |
| D192 | 12 | 192/384 | .0025 | 32 | independent outer-domain control at h=.0625 |
| Q128 | 8 | 128/256 | .0025 | 64 | independent angular control at finer base |

This shifts the new development qualification to S64/S128/S256 with controls at S128. The old S32 failure remains visible and charged; it is not part of a retrospectively rewritten T56 success. Reused S64/S128 agreement is old evidence, not a new measurement. Freeze exact identities for reused arrays, cases, stage logs, initial conditions, source implementation and recorded runtime, as well as the new wrapper/protocol and executable. The original root/output directory must never be used for new writes. If importing unchanged T56 functions, redirect only the output location explicitly and freeze that wrapper; do not quietly modify numerical behavior.

Retain the same annular initialization, source rule, FV/CG solve, conservative reconstruction/limiter, flux, time integrator, full-field comparison, world-coordinate core, output times, shape normalization and all relevant quality/drift/stage predicates. Apply the existing fine analytic u/J threshold .005 to each new case; keep the saved S64/S128 thresholds .01/.005. Require both S64/S128 and S128/S256 field discrepancies <=1%, with the same nonzero-time reduction rule; time/domain/angular controls use S128 and the same 1% field, 1% velocity and .01 moment thresholds. All predicates are required. Do not compare only restricted means, align or fit the fields, use a new metric selected after output, or discard a failed control.

## Fixed preparation and resource boundary

Allow **one scientific child capped at 1200 seconds**, containing four new trajectories, any new geometry matrices, all stages, saved-data comparisons, output and imports. No warmup, pilot, retry, fallback, shorter interval or smaller substitute case after launch. The existing S128 case took 56.72 s including 12.99 s geometry and 40.25 s Poisson solves; those observations motivate a finite cap, not a runtime guarantee. Account for the complete 116.5366346-second T56 invocation, its failed/control cases and any prior preparation separately from the new execution. Do not advertise a speedup from unequal measured work.

S256's geometric matrix alone would contain 1026*131072 float64 entries, about 1.076 GB; temporaries, CG arrays, live fields, reused data and snapshots add to it. Before freezing/running, inspect actual available host memory and specify an observed process-memory stop limit and its measurement method. A reasonable initial preparation requirement is at least 3 GiB host memory available and a 2 GiB process peak-working-set check; these must be checked against the actual wrapper/allocation design rather than assumed from matrix bytes. Release each completed case's geometry before constructing the next. The memory monitor is an observed limit, not a formal allocation/OS resource guarantee. Do not install an accelerator, introduce a different baseline or allocate a larger case silently if the contract cannot be met.

The smaller h raises the outgoing CFL at fixed dt. Existing S128 margin is only preparation evidence; every new Euler stage must still pass the original CFL/positivity/linear-residual checks. Failure must not trigger a smaller dt or clipped field. Runtime, memory or numerical failures keep partial records and close this invocation. A metric failure also closes the new qualification after its frozen schedule; there is no automatic S512 escalation or new source batch.

Passing T57 would support only the new finer reference on [0,.25]. The full t=1 task and any ordinary Gaussian-fit comparison require a separate decision/protocol. If it fails, inspect the specific retained discrepancy before selecting any further action. Neither outcome by itself supplies a new method or justifies a carrier-failure claim.

This proposal was checked conceptually by a mathematical consultant without further numerical execution or source access. Its value is an explicit resolution/cost test grounded in observed convergence, not additional runs merely to fill a queue. No T57 execution has occurred in T56. The full SIGGRAPH/TOG goal remains active and unachieved; it still needs a useful distinct mechanism, strong ordinary comparisons and finite-time/multi-scene evidence. Art remains inactive, main unchanged and the deleted automation unchanged.
