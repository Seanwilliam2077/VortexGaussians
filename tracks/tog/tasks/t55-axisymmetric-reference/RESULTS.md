# T55 — initial spatial reconstruction results

Status: **qualified_initial_only**, with all eight frozen predicates true. One scientific child, five initial elliptic solves, zero fluid trajectories, zero candidate methods and no retry. The ten frozen inputs and executable remain unchanged. The pre-run two-agent readbacks prompted explicit inviscid normalization, the Green boundary endpoint-singularity limitation, and disclosure that D96 changes both box and quadrature. These clarifications were frozen before numerical execution; thresholds and cases were not changed after results.

## Physical task and measured accuracy

[TASK.md](TASK.md) establishes a researcher-defined finite-time coherent-ring transport/shape screen, not a human-validated creative brief. Its future field, displacement and shape requirements have not been evaluated. This run instead checks the necessary initial free-space velocity and full Cartesian Jacobian against analytic ordinary formulas, using 3D physical weights in a fixed core r<=4, |z|<=4. The five Jacobian components include the cylindrical-to-Cartesian J_yy term. There is no axis sample on the cell-centered grids; axis behavior is imposed by zero radial flux/reflection and checked algebraically.

| Case | Core relative u error | Core relative J error | Full-box relative u error | Full-box relative J error | CG iterations |
|---|---:|---:|---:|---:|---:|
| S32 | 0.01480333805 | 0.007889622531 | 0.01491742434 | 0.008013741237 | 138 |
| S64 | 0.003684914356 | 0.001973473200 | 0.003713613161 | 0.002004511695 | 273 |
| S128 | 0.0009202425493 | 0.0004934573731 | 0.0009274278642 | 0.0005013080700 | 538 |
| Q64 | 0.003684914356 | 0.001973473200 | 0.003713613161 | 0.002004511695 | 273 |
| D96 | 0.003686081347 | 0.001972375146 | 0.003696485802 | 0.002001617942 | 416 |

The finest core errors are about **0.0920% in u and 0.0493% in J**, both below the fixed 0.5% gate. Adjacent spatial error-reduction factors are 4.01728144/4.00428600 for velocity and 3.99783616/3.99927797 for the Jacobian, all above 1.5. This observed approximately second-order behavior concerns these three initial grids, not a convergence theorem.

Q64 versus S64 core differences are 8.362970310756439e-15 for u and 1.7873746984816567e-13 for J, both below 1e-4. D96 versus S64 differences are 6.522378115760852e-5 for u and 4.502255222099013e-6 for J, both below 1e-3. These use identical core coordinates without interpolation. **D96 changes the box and quadrature orders together**, so its agreement is not an independent bound on domain truncation. Every case is also compared with the full free-space analytic initial field, which exposes its combined observed error. Extremely small Q64 differences do not prove comparable true quadrature accuracy or general reliability for evolving non-Gaussian sources.

All true weighted linear residuals lie between 9.38789e-11 and 9.71144e-11, below 1e-10 within the 2000-iteration cap. There are zero direction restarts. The CG algebraic norm uses r^3 weights; the physical u/J norms use 2*pi*r and must not be interchanged. This residual is not a physical error bound.

Analytic diagnostic fractions: initial vorticity squared norm omitted by the core is 1.9285151986329603e-6; Gaussian 5D source mass omitted by the R=8 box is 4.1916165523496164e-13, and by R=12 is 3.931088861039587e-30. These fractions do not certify exterior u/J error, boundary singular quadrature or later support. Full-box derivative errors also include the deliberately ordinary boundary ghost stencil.

## Complete recorded numerical costs

Python 3.12.14, NumPy 2.3.5, the existing bundled executable previously identified in T54. No installation or new runtime selection. Timings are single-run observations for reference qualification, not performance claims or candidate-versus-baseline comparisons.

| Case | Green boundary seconds | Linear solve seconds | Derivative reconstruction seconds | Analytic oracle seconds | Case seconds before record writing |
|---|---:|---:|---:|---:|---:|
| S32 | 0.08489220 | 0.00446850 | 0.00010280 | 0.00177610 | 0.10610090 |
| S64 | 0.16080140 | 0.01587470 | 0.00043930 | 0.00656820 | 0.18855450 |
| S128 | 0.38306390 | 0.10167430 | 0.00123370 | 0.02672760 | 0.52227640 |
| Q64 | 1.48134500 | 0.01601490 | 0.00026200 | 0.00649380 | 1.50943480 |
| D96 | 1.17881450 | 0.06951540 | 0.00109980 | 0.02375370 | 1.28177500 |

Full supervised child: **3.918251399998553 s**, including imports, all five cases, comparisons and outputs, within the 180 s cap. Child timer before result writing: 3.7610482999589294 s. Supervisor elapsed before receipt writing: 3.942284299992025 s. The nested phase/case timers are not additive extra costs. The supervisor figure does not include later evidence review and publication; those are separate research preparation/verification work, not hidden solver speed.

The cases evaluate 69,632 total grid cells and 279,756,800 scalar boundary target/source/angular pairs. Counts describe the actual loops, not independent samples, equivalent accuracy work or timings for a dynamic solve. Five ignored raw NPZs total 8,972,626 bytes. Per-case shapes, settings, phase times and raw identities are in [result.json](result.json); per-case JSON and stdout/stderr identities are in [execution.json](execution.json). Stdout is 2,028 bytes and stderr empty. No arrays or logs are committed in local/. Sources used two queries, three primary documents and five web calls before freeze; no external solver implementation or assets were acquired.

T52's earlier scalar failure and T53's two diagnostics remain recorded in their original tasks; T54's successful scalar verification is separate from these five initial reference cases. Nothing here retroactively changes those statuses or costs. This task's review reduces saved arrays only, checks hashes/settings/gates and reads code/math; it does not replicate the scientific invocation. The reviewer also participated before freeze, as disclosed in [the review](../../../validation/t55-reference-review.md).

## Decision supported

The initial reference prerequisite is met under this frozen protocol. It is now reasonable to prepare a bounded dynamic-reference qualification, while retaining the ordinary full-tangent fit as the eventual main comparator and center update only as a diagnostic. No finite-time field, centroid or shape error has been measured. No practical representation failure, new method benefit or TOG core contribution is established. See [DECISION.md](DECISION.md) for the remaining mechanism-specific gap.
