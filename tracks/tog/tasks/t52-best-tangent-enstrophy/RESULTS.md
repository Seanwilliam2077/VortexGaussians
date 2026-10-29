# T52 — analytical result, unsuccessful numerical check

**The ordinary best tangent is available analytically. The single numerical verification attempt failed without producing a result.** These outcomes remain separate. No decimal error estimate, quadrature convergence result or numeric-consistency pass is reported.

## Analytical consequence

[The frozen derivation](ANALYSIS.md) gives an all-parameter L2 projection, with ordinary update b=0, D=0 and

\[
\dot\mu=\beta_*a,\qquad
\beta_* = g_0\frac{16}{45}\sqrt{\frac23}.
\]

The complete three-center/three-covector/six-covariance tangent was available. This optimum does not result from suppressing ordinary freedoms. Its exact residual is given by the fixed J0/J1/J2 expressions; no fitting optimizer or new simulation method was developed.

The already frozen formulas imply

\[
0<E_*<1<E_c.
\]

Strict positivity and E_*<1 follow from the positive weighted variance of nonconstant L and J1>0. For the center update, its fixed expression yields

\[
E_c^2-1=\frac{4}{9J_2}(J_0-3J_1)>0,
\]

because J0/sqrt(pi)=15/16 exceeds 3J1/sqrt(pi)=sqrt(2/3): squaring positive quantities compares 225/256 with 2/3. This exact-algebra consequence was recorded after the failed invocation, without changing frozen inputs or evaluating numerical constants. It is not a substituted numerical run.

Thus the center-affine update is worse than the zero-derivative scale anchor in this particular instantaneous norm, while the ordinary optimal tangent is better. The zero reference is not a useful fluid solver. The result demonstrates a weakness of center-only comparison for this isolated state; it does not prove the ordinary optimum is practically sufficient or supply a new contribution. The magnitude of E_* is specified analytically but has not passed the planned independent numerical consistency check.

## Actual execution

[The frozen input manifest](input-manifest.json) records pre-run mathematical/code review. [The execution receipt](execution.json) records:

| Item | Observed outcome |
|---|---|
| Scientific child invocation attempts | 1, with a 60-second timeout |
| Return code | 3228369023 |
| Supervised child wall time | 4.807828599936329 seconds |
| Supervisor elapsed before receipt write | 4.814353100024164 seconds |
| stdout / stderr | Both empty, zero bytes; identities retained |
| Saved numerical result | None; `result.json` does not exist |
| Frozen input identities | All unchanged |
| Measurement status | Failed child, no retry |

The process ended before reporting its final output. No phase markers were emitted, so the record cannot establish whether failure occurred during import, node generation, integration or another step. It cannot identify a missing DLL, a NumPy defect or another cause. Module-discovery success during preparation did not validate runtime execution. No exception diagnosis, alternate interpreter, narrower numerical calculation or second invocation was attempted after this failure.

The failed attempt's complete observed wall cost is retained. Its duration is not solver timing or a usable comparison metric. No rule timings, moment values, evaluator versions emitted by the child, residual percentages, convergence estimate or pass/fail result for the numerical consistency checks are available. The fixed script and protocol specify what was attempted, not what is proven to have executed internally.

## Limits

The independent mathematical review supports the exact formulas and the ordinary-fit comparison. The empirical numerical cross-check remains incomplete. This norm is the all-space L2 error of the **physical vorticity derivative**, not the time derivative of scalar enstrophy, a finite-time flow error, visual quality or a creator acceptance threshold. The initial kappa formulas cannot be extrapolated to a whole traversal time without additional trajectory evidence.

No fluid rollout, multi-carrier case, novel method, application-quality requirement, repair or performance advantage was established. The failed scientific invocation remains failed in all summaries.
