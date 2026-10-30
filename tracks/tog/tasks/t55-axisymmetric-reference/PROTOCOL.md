# T55 — frozen initial reference qualification

One scientific child, existing bundled Python/NumPy used in T54, timeout 180 seconds including imports, all five cases, comparisons and output. Supervisor separately records complete child cost and its own elapsed preparation/log time. Exactly one invocation: no pilot, warmup, fallback, retuning or trajectory. Source/analytic preparation and reviewer feedback occur before freeze. Previous goal turn is progress: T54 established numerical consistency and the stronger ordinary comparator. The full goal remains active.

Five preselected cases run regardless of earlier *metric* outcomes. A runtime exception/nonfinite value or failure to solve stops the child and leaves partial per-case records; no retry.

| Case | R=Z | radial cells / axial cells | boundary Gauss nodes (r,z,theta) | Purpose |
|---|---:|---:|---:|---|
| S32 | 8 | 32 / 64 | 32,64,32 | coarse spatial |
| S64 | 8 | 64 / 128 | 32,64,32 | base spatial |
| S128 | 8 | 128 / 256 | 32,64,32 | fine spatial |
| Q64 | 8 | 64 / 128 | 64,128,64 | independent boundary quadrature refinement |
| D96 | 12 | 96 / 192 | 48,96,48 | combined larger source/solve domain and boundary quadrature change, same h as S64 |

Q64 isolates boundary quadrature refinement at R=8. D96 changes both the source/solve box and quadrature orders; its difference from S64 is a combined sensitivity check, not an isolated domain-error estimate. Analytic free-space comparisons for every case include the resulting combined initial error. Passing these checks does not independently certify domain truncation or quadrature error, and a future trajectory reference still needs its separately specified spatial/time/domain evidence.

All cases use midpoint analytic q initially, zero initial CG guess, diagonal preconditioning, at most 2000 weighted CG iterations and true weighted relative residual <=1e-10. Candidate convergence in the recurrence must be confirmed by a true residual; if it is too large, restart the direction from that true residual without changing the iteration budget. That is part of this fixed linear solver, not another scientific invocation.

The fixed common core is 0<=r<=4, |z|<=4. Each case reports 3D-weighted relative L2 velocity and full Jacobian errors there against the analytic free-space initial field, plus full-box errors for context. All components, including J_yy, count. No flow-aligned shift, component removal or per-case region change. Store fields in ignored local NPZs for saved-output review; publish compact metrics, settings, complete times and byte identities.

Qualification requires: (a) every linear solve meets the stated residual/iteration limit; (b) S128 core velocity and Jacobian relative errors <=.005; (c) each adjacent spatial refinement reduces each of those errors by a factor >=1.5; (d) Q64 versus S64 core velocity and Jacobian discrepancies <=1e-4, normalized by analytic core norms; (e) D96 versus S64 same-grid core velocity and Jacobian discrepancies <=1e-3. These are fixed initial-reference engineering thresholds, not the future trajectory's physical gate or a true-error theorem. Report all values and failed predicates.

The core omission fraction in initial physical vorticity squared norm and the outside-box Gaussian 5D source-mass fraction are computed analytically as diagnostics. They do not certify the exterior velocity/Jacobian error or later support. The common core has fixed coordinates and matching cells in Q64/D96 comparisons. No interpolation is used to make those comparisons agree.

Freeze TASK, FORMULATION, this protocol, reference implementation, runner, source record and executable identity before launching. The actual parent is `898b5b68ea402d3696e4d6e8f6d196a1ef592916`; historical files remain unchanged. After the child, one saved-data/math review and publication follow. A pass only establishes this initial spatial reconstruction under this protocol. A failure closes this invocation and records an evaluation gap. Neither result authorizes an automatic trajectory, stronger claim or new method.
