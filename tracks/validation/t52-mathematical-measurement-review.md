# T52 mathematical, code and saved-execution review

30 October 2026. Reviewer: collaboration agent `t48_review`.

**Verdict: the analytical least-squares result and frozen evaluator have no identified mathematical/code blocker; the one numerical consistency attempt failed and remains unvalidated.** There is no numerical pass, measured approximation floor or solver-performance result. The documents may be sealed with those outcomes separate.

## One review before and after the authorized invocation

This reviewer inherited the T48-T51 collaboration context and previously reviewed the complete T51 tangent. Before the scientific invocation, the reviewer directly read SCOPE, ANALYSIS, RUN_PROTOCOL, measure.py and the local-ignore rule, checked the derivation and code by hand, and reported no blocker together with their actual byte counts/SHA-256 identities. The parent then froze those identities in input-manifest.json and supervised the single invocation.

Within the same review task, the reviewer subsequently read the saved input manifest, execution receipt, RESULTS, DECISION and README. The current bytes of all five original inputs match the pre-run manifest, whose identity also matches the execution receipt. The reviewer independently checked that result.json is absent and that both saved logs are zero-byte files with their recorded empty-file SHA-256 digest. These are file/record checks, not a replay of execution.

The reviewer did not execute, import, compile or diagnose the scientific script; did not evaluate its constants numerically or run a replacement integration; and did not acquire sources, reread a paper, view images, install dependencies, simulate a flow or introduce another family. Tool execution was limited to document reads and byte/hash/manifest/log bookkeeping. The disclosed SciPy-to-existing-NumPy preparation change precedes the frozen numerical protocol and does not constitute a measurement retry. This is contextual adversarial hand readback plus review of one saved execution record, not an independent empirical reproduction.

## Full-state ordinary minimizer

1. **The metric is the L2 norm of physical vorticity-derivative error.** It is not the derivative of scalar enstrophy, a kinetic-energy error, a rendered-image difference, a finite-time state error or an application acceptance threshold. All twelve existing parameter derivatives are available in the stated optimization.

2. **Parity legitimately removes only the odd physical contribution.** On all of R^3, even and odd square-integrable fields are orthogonal. The target and translation tangent are even; the covector/covariance tangent is odd. The optimum therefore has zero odd physical contribution, attainable with b=D=0. This does not discard those freedoms in advance or require their parameterization to be injective.

3. **The restriction v=beta a follows from optimization symmetry.** The continuous translation tangent map is injective: a zero L2 field vanishes everywhere; its center value forces v parallel to a, and its remaining quadratic factor then forces v=0. Its Gram matrix is positive definite, so its least-squares minimizer is unique. Rotations fixing a preserve the target, norm and tangent problem, hence also that unique minimizing v. Their common fixed subspace is span(a). This is valid for the L2 problem and does not reuse the invalid shortcut of imposing pointwise target equality at the center on an approximate fit.

4. **The angular and radial factors match.** Squaring (G/s^2)(L-beta)(a dot x)(a cross x) gives the angular integral 8 pi/15 and radial weight r^6 g(r)^2. Weighted least squares yields beta_star as the weighted mean of L. The nondimensional substitution r=sqrt(s)rho gives beta_star=g0 J1/J0, the stated residual squares E_star^2=1-J1^2/(J0 J2) and E_center^2=(J2-4J1/3+4J0/9)/J2. Strict weighted variance of the nonconstant L gives 0<E_star<1. The zero-derivative reference has residual one solely by normalization.

## Closed moment expressions and scale check

5. **J0 and J1.** The half-line sixth Gaussian moment gives J0=15 sqrt(pi)/16. In J1, interchanging the nonnegative integrals and integrating rho^3 exp(-rho^2) from q to infinity gives one-half(q^2+1)exp(-q^2), canceled by the existing factor two. The remaining q^2(q^2+1)exp(-3q^2/2) moments yield J1=(1/3)sqrt(2pi/3), and therefore beta_star/g0=(16/45)sqrt(2/3).

6. **The erf-product identity.** Differentiating the defined F(a,b) under its convergent integral gives the stated a/[sqrt(pi)(1+b^2)sqrt(1+a^2+b^2)]. Differentiating the proposed arctangent expression gives the same derivative, and its value at b=0 is zero. Thus the identity is valid for the scalar parameters used here. With both parameters equal to 1/sqrt(2), its argument becomes 1/(2sqrt(2)). The cross integral is 1/6 and the remaining Gaussian moment is sqrt(pi)/(8sqrt(2)). Expanding four times the A(r)^2 integral consequently gives exactly J2=sqrt(pi)[2 atan(1/(2sqrt(2)))-5/(6sqrt(2))]. No quadrature result was needed or used to fit these expressions.

7. **Norms and initial time scale.** The angular integrals for omega and N give the displayed pi^(3/2) and 8pi/15 constants. Radial scaling gives norm(omega)^2=g0^2|a|^2 sqrt(s)pi^(3/2) and norm(N)^2=(8pi/15)g0^4|a|^4 s^(-1/2)J2. Combining them with t_c=3sqrt(s)/(2g0|a|) yields kappa_N^2=6J2/(5sqrt(pi)), with the residual factors multiplying kappa_N as written. These are initial derivative scales, not a certified error after duration t_c.

8. **Post-failure exact consequence remains analytical.** From the already frozen formula, E_center^2-1=4(J0-3J1)/(9J2). Dividing by sqrt(pi) reduces positivity to 15/16>sqrt(2/3); squaring compares 225/256 with 2/3. Hence 0<E_star<1<E_center follows without numerical constant evaluation. RESULTS explicitly discloses that this consequence was recorded after the failed invocation without altering the frozen inputs. It is not a replacement measurement, and the zero reference remains only a metric anchor, not a proposed fluid solver.

## Frozen evaluator: hand code correspondence

The script's three orders are exactly 128, 256 and 512. Each mapped Gauss-Legendre node contributes to all three moments through one base weight and one ell evaluation, so **896 nodes is the planned total**, not three such sets. Mapping to [0,12], the Gaussian factor, moment powers and fsum accumulation agree with the protocol. There is no adaptive order choice, convergence-driven early success exit or retry path.

For radius<=1/4, the recurrence generates z^n/n! for n=0 through 11, with z=-radius^2/2, and uses the required denominator 2n+3 and factor two. The next alternating term gives the stated real-arithmetic remainder bound because |z|<=1/32. Outside that branch, the erf expression equals the same integrated radial function. This correspondence does not certify library roundoff or cancellation behavior.

Repeated integration by parts for the sixth Gaussian tail gives the polynomial terms shown, with the final zeroth-tail inequality contributing 15/(16R). The bounds for J1 and J2 follow from 0<ell<=2/3. These are truncation/series bounds, not error certificates for a finite quadrature rule.

The code compares all three moments for every rule to the closed expressions and compares adjacent rules using the same closed normalization, with the fixed relative threshold 1e-9. It checks finite positive rule moments and their strict variance inequality; the recorded metrics also require valid residual squares. The metric and kappa implementations match the derived formulas. JSON prohibits nonfinite values, records code identity, preserves inconsistent status rather than retuning, and labels the internal timer as ending before result writing. Output overwrite prevention is explicit. These hand checks did not establish that the runtime could execute the script successfully.

The external supervisor, not measure.py itself, supplies the one-invocation and 60-second child timeout contract. Its complete implementation was not separately audited by this reviewer. The saved execution record is therefore the evidence for the observed attempt; no universal process/watchdog or forensic no-other-execution claim is made here.

## Observed failure and what is not known

The saved receipt records one scientific child attempt with a 60-second timeout, return code **3228369023**, supervised child duration **4.807828599936329 seconds**, and supervisor elapsed before receipt writing **4.814353100024164 seconds**. The current input identities are unchanged, both logs are actually empty, and result.json is actually absent. The input-manifest identity recorded in execution.json matches the saved manifest.

There are no phase markers or numerical results. Consequently the number of completed nodes or rules, import completion, any reached numerical phase, child-reported package versions, per-rule costs, moments, residual decimals and consistency verdict are **unknown or unavailable**. The planned 896 nodes must not be reported as actual completed work. The return code alone does not identify NumPy, a missing DLL, node generation or any other cause. The observed wall duration is the cost of a failed attempt, not a usable fluid-solver or quadrature benchmark.

No retry, alternative interpreter, substitute decimal evaluation or narrower numerical test was performed by this reviewer. The final documents retain the failed attempt and the incomplete numerical cross-check. Mathematical validity and an execution failure are different evidence categories: the latter does not refute the formulas, while the former does not turn the failed run into a measured success.

## Decision and sealed identities

Retaining the ordinary optimal fit as a capable comparator is justified by the full-state derivation. A new method cannot isolate its benefit merely by beating the weaker center update in this metric. The remaining conditional floor does not by itself justify refinement, splitting, another representation or a practical accuracy claim. No multi-carrier method, fluid rollout or new experiment is automatically selected. Any later runtime diagnosis or scientific invocation needs its own bounded task; no external blocker or failure cause has been established by this record.

The ten identities below were generated directly from the final file bytes. The first five are unchanged from pre-run review and input freezing. Hashing delimits reviewed content; it does not certify scientific execution.

| File | Bytes | SHA-256 |
|---|---:|---|
| .gitignore | 7 | `a7d8bdcefba82a95ebc021d87c629fdea21f13af953bf01e28b7cf8b0eeceb41` |
| SCOPE.md | 3948 | `db06c33e42ad375dd7f89079806022e572469fef7638e825bce062b90d518708` |
| ANALYSIS.md | 5822 | `16d2f8b9f9d1e7ea3d9e664bbb3edd2d104d6b87bee052899ceb508d12fdfae3` |
| RUN_PROTOCOL.md | 4155 | `b269487b7f1854943ab98ef80b711b12aa6b78b1ab78630bca391a8c36f8e436` |
| measure.py | 5071 | `488085c916d8172a9f243c2fa9f3e4cf18cc118ca6e628cc7d6fed4636657743` |
| input-manifest.json | 1639 | `7c32812965a7f6853048fe8cfadb485c479ae9cbd52175e1915cc868b952e2e9` |
| execution.json | 1711 | `bdb939c3701b4307dcd2f7b66beea9920e4c640841991188d0ad666113f727a5` |
| RESULTS.md | 4094 | `54ba756368ac91ba343a616c48d56d8f1186f459f5ac321a9c7c5ac3081a15fc` |
| DECISION.md | 1866 | `e86244c1b8d456d70eece5c0df88bfcf21b4853c23b7b2b497148b1b2668cc08` |
| README.md | 1785 | `1f3e0eaf2821ec109183a2713619cd5fa0f56d32c9f9a9631425f173e1602ae1` |

No unresolved mathematical or documentation blocker prevents sealing this analytical result together with its unsuccessful measurement attempt. The numerical check remains incomplete. The full research goal remains active and unachieved, with no established useful core method, measured strong-baseline advantage, multiple-scene validation or reproducible fluid implementation supplied by this task.
