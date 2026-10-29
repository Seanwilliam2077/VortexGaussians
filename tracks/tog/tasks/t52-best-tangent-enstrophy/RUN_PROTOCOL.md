# T52 — fixed scalar measurement protocol

Frozen before the single scientific invocation. Analytic preparation is disclosed in [SCOPE.md](SCOPE.md); this is a check of derived constants and a conditional approximation measure, not an independent discovery/held-out benchmark. [ANALYSIS.md](ANALYSIS.md) fixes the full-state least-squares question and all formulas.

## Runtime and numerical budget

- Existing `C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/python.exe`, Python standard library and already available NumPy. SciPy was absent in two read-only preparation probes; nothing is installed. No GPU, source fetch, scene, simulation or symbolic package.
- Exactly one child invocation of the frozen `measure.py`, supervised with a 60-second child-process timeout. Imports, node generation, all three rules, comparisons and JSON writing are inside that child budget. The supervisor separately reports total wall time including start/hash/log handling; this is not a hard watchdog over every supervisor disk operation.
- Use dimensionless radius rho in [0,12]. Evaluate ordinary Gauss-Legendre rules with exactly 128, 256 and 512 nodes, each returning all three J moments. All three preselected orders run regardless of earlier results; there is no adaptive order change or retry. Node count is 896 total, not three separate sets per moment. NumPy computes ordinary float64 nodes/weights; Python `math.fsum` accumulates the integrands.
- For rho<=1/4 evaluate ell with 12 terms, n=0..11, of `2 sum (-rho^2/2)^n / [n! (2n+3)]`. Its real-arithmetic alternating remainder is at most `2 (1/32)^12 / (12! 27)` on that interval. Else evaluate `2 [sqrt(pi/2) erf(rho/sqrt(2)) - rho exp(-rho^2/2)] / rho^3`. No cutoff, branch or term-count tuning follows the result.
- Since 0<ell<=2/3, the omitted tails for J1 and J2 are bounded by 2/3 and 4/9 times the J0 tail. At R=12, a sufficient real-arithmetic J0 tail bound is `exp(-R^2) [R^5/2 + 5R^3/4 + 15R/8 + 15/(16R)]`. This and the series bound do not certify library roundoff or finite-rule quadrature error.

## Fixed consistency checks and outputs

For each of the three moments and every order, relative difference from its closed expression must be <=1e-9. Also require the maximum relative difference between adjacent orders, normalized by the closed moment, <=1e-9. Require finite positive moments and the expected variance inequalities `0<J1^2<J0 J2`, with nonnegative residual squares. Passing these checks means numerical consistency of these constants, not a formal floating-point certificate or proof of the source derivation. The mathematical readback is separate.

Report the three moment values for every rule, closed values, differences, all actual node-generation/evaluation times, total child/supervisor times, versions and frozen code identity. Report the ordinary optimal and center coefficients relative to g0, their derivative-relative residuals E_*/E_c, the zero-derivative reference E=1, the error reduction ratio, and the initial time-normalized scales kappa_N/kappa_*/kappa_c. Use both the closed expressions and the finest rule so any disagreement is visible. Retain output/log identities and the full cost of this one invocation, including a failed attempt if it fails.

The consistency threshold is an evaluator check, not an application-quality acceptance threshold. No fixed acceptable simulation error or human preference is available. Compare the ordinary fit honestly: any reduction from center update is available to every future method as a baseline. The residual floor applies only to the chosen instantaneous norm, representation and input symmetry. Do not call E a relative fluid-state error, extrapolate kappa to a whole traversal time, or infer a need for a particular repair.

## Stop

On timeout, inconsistent identities, exception or nonfinite result, save the failure and stop; no retuning, alternate norm or second invocation. On success, complete one result/decision and independent readback, then publish. No fluid rollout, multi-carrier test, source batch, enrichment or implementation follows automatically. Frozen inputs remain unchanged after execution.
