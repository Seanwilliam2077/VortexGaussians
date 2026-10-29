# T17: qualify one order-inversion bound for the existing volume integral

28 October 2026, active goal continuation after T16. The previous goal turn made progress by establishing the inspected author-reference mismatch; it was not a verified running wait or proof of a scientific impasse. T15/T16 results remain closed and unchanged. This is a substantive new mathematical construction within C's existing operation, not a fourth operation in the completed selection batch or a claim that the old generic interval bound was novel. The goal continuation remains active; the separate deleted hourly automation is not recreated.

## Question and chronology

Can a pairwise order-inversion optical-mass bound, with a saturation obtained from a first-arrival probability argument, safely bound the error of whole-primitive emission–absorption compositing and sometimes be more informative than the ordinary global color-range bound? The comparator is the identical continuous integral, not T16's peak-opacity RF or scattering PRB implementations. Neither a mathematical bound nor passing this screen establishes novelty, efficiency, production value or submission readiness.

Before this file was written, root issued two exploratory queries (`Gaussian splatting compositing error bound pairwise overlap color transmittance ordering`; `volume rendering commutator error bound compositing order emission absorption Gaussian`) and independent agents checked the proposed algebra. That is disclosed development, not a preregistered novelty search. Source inspection is now capped at the three identified work families: Novins/Arvo/Salesin 1992 adaptive error bracketing; Hahlbohm et al. 2025 hybrid transparency; Jiang et al. CVPR 2025 geometry-field splatting. Failed primary fetches remain unknown; no new search queries or additional work families this task. T15/T16 evidence may be cited as inherited evidence.

This protocol is fixed before input generation or numerical execution. Numerical fixtures and tolerances below are qualification choices, not production requirements or held-out scenes. Inputs are known physical ray-density functions; no learned opacity calibration is assumed.

## Model and fixed formulas

On `[a,b]`, `s_i(t)=w_i normal_pdf(t;mu_i,sd_i)`, with `w_i>=0`, `sd_i>0`, constant linear RGB `c_i in [0,1]^3`. Let `tau_i=integral_a^b s_i`, `alpha_i=1-exp(-tau_i)`, `T(t)=exp(-sum integral_a^t s_i)`. The target is `integral_a^b T(t) sum_i s_i(t)c_i dt + T(b) background`. Background is `(0.1,0.2,0.3)` for every fixture. Whole-primitive compositing uses these exact clipped optical masses, sorted stably by `mu` (input index breaks ties).

For sorted `i<j`, set `I_full=w_i*w_j*Phi((mu_i-mu_j)/sqrt(sd_i^2+sd_j^2))` and `Ibar=min(I_full,tau_i*tau_j)`. Do not replace full weights in `I_full` by clipped weights. Define:

```text
B_simple_ij = min(Ibar, alpha_i*alpha_j)
h = min(alpha_i,alpha_j)
B_jensen_ij = min(alpha_i*alpha_j, -h*expm1(-Ibar/h))   (0 when h=0)
G = (1-exp(-sum tau_i))*(max_i c_i-min_i c_i)
E_simple = min(G, sum_i<j abs(c_i-c_j)*B_simple_ij)
E_jensen = min(G, sum_i<j abs(c_i-c_j)*B_jensen_ij)
```

All minima and color operations are componentwise where relevant. Empty/zero-mass scenes use zero error. This is a real-arithmetic construction. Binary64 evaluation is not a rigorous floating-point certificate; underflow, interval endpoints and sums require separate treatment before that claim could be made.

## Fixed 48-ray qualification set

All intervals are `[-1,1]` unless specified. No scene rendering or simulation.

1. Eight analytical controls: vacuum; three zero-mass components; a single `(mu=0,sd=.3,w=1.2)`; a clipped single `(mu=1,sd=.6,w=3)`; eight equal-color components (`mu=linspace(-.6,.6,8), sd=.4,w=.3,c=(.2,.5,.8)`); four coincident profiles (`mu=0,sd=.3,w=(.02,.03,.04,.05)`); the same with `w=(2,3,4,5)`; two coincident profiles (`mu=0,sd=.3,w=(1,1)`) with red/blue colors. Single colors are `(.2,.5,.8)`; four-profile colors are red, green, blue, white. Vacuum/zero-mass result is background. Equal-color/single results use the exact monochrome formula; coincident profiles use optical-mass-weighted color. Equal-profile red/blue sorted error is exactly `alpha^2/2` per red/blue channel.
2. Sixteen generic fixtures from NumPy `default_rng(20261028)`, consuming consecutive draws per case for `mu`, `sd`, `w`, then `c`: `N=(2,4,8,16)` repeated four times; `mu~U(-1,1)`, `sd=exp(U(log(.05),log(.8)))`, `w=exp(U(log(.01),log(3)))`, colors independently `U(0,1)`. Save all generated parameters before solving.
3. Sixteen structured fixtures: Cartesian product `N=(4,8,16,32)` and span `(0,.3,1.2,3)`, in that order. `mu=linspace(-span/2,span/2,N)`, standard deviations alternate `.2,.25`, `w=2/N`, colors cycle red/green/blue. These are dense and partially separated cases, not production scenes.
4. Eight clipping fixtures: two parameter pairs, `mu=(-.5,.5),sd=(.25,.25),w=(1,1)` and `mu=(-.2,.4),sd=(.8,.1),w=(.2,3)`, each over intervals `(-.02,.02),(-1,.1),(.1,1),(-.05,.05)`, red/blue colors. These explicitly probe the finite-interval issue.

## References, budget and decision

Use an existing CPU Python/NumPy/SciPy environment only. No installation, GPU, renderer or asset download. At most one full 48-case run; if an implementation failure prevents qualification, one disclosed repair/re-execution is allowed with unchanged fixtures/gates, preserving the failed attempt. Wall cap 300 seconds per attempt, total at most 600. Do not add cases after seeing results.

Two ordinary numerical references use the same analytic cumulative extinction and Gaussian parameters: adaptive Gauss–Kronrod vector quadrature (`epsabs=epsrel=1e-11`, bounded subdivision limit 1000), and 32-/64-point Gauss–Legendre per segment. Give both endpoints and each in-range `mu+k*sd`, `k=(-6,-3,0,3,6)` as breakpoints. Record solver evaluation counts, returned error estimates, GL refinement difference and per-run wall time. The references share the integrand implementation, so the analytical controls are essential; numerical agreement alone is not a proof.

Qualification requires all finite outputs; agreement of both references, GL refinements and applicable analytical values within `5e-10`; and no bound violation beyond `1e-9`. Report every failure, not just aggregate success. Record unbounded full-line masses, clipped masses and both bounds with results. No claim of formal floating-point certification follows from these tolerances.

Before any timing comparison, inspect how many non-control cases with `N>=4` have `max(E_jensen)<=.01` while `max(G)>.01`; also report counts at `.001` without tuning. Zero such cases ends this direct pair-bound opportunity at this scope. A nonzero count justifies at most preparation of a full-cost, equally informed ordinary-baseline comparison; it is not a speed result. Quadratic pair work may already outweigh direct quadrature. Record all cases including thick/dense failures and clipping conservatism. No hierarchy, split strategy, tile reuse, new scene or renderer is added to rescue this qualification.

## Environment amendment before fixture generation or numerical execution

The existing `gs-sph-3d` and bundled Python imports both report `ModuleNotFoundError: scipy`; the other existing conda environments/base also lack a SciPy package directory. No installation is made. Replace the adaptive Gauss–Kronrod reference above with a standard recursively adaptive Simpson reference using Richardson correction, error estimate `abs(S_two_half-S_parent)/15`, total absolute budget `1e-11` distributed by interval length, maximum depth 24 per segment and 200,000 integrand evaluations per ray. Exhausting either limit is a reference failure, not acceptance. The independent 32-/64-point Gauss–Legendre reference, breakpoints, 48 fixtures, numerical gates and timing caps are unchanged. This is a disclosed pre-run implementation choice forced by available dependencies, not an outcome-driven change or a performance comparison. All references remain empirical rather than rigorous numerical certificates.
