# T17 — order-inversion bound for whole-primitive compositing

28 October 2026. This document proves the real-arithmetic formulas fixed in [PROTOCOL.md](PROTOCOL.md). It contains no numerical result or novelty assertion. The construction concerns the existing C emission–absorption integral. It does not change that operation, rehabilitate T15's generic interval-bound proposal, or identify T16's peak-opacity RF implementation with a volume integral.

## Model and quantities

On a finite interval `[a,b]`, let `s_i(t)>=0` be integrable ray extinction densities for finitely many labels, with constant linear RGB colors `c_i`. For the qualification, these are Gaussian restrictions and `c_i in [0,1]^3`. Write

```text
A_i(t) = integral_a^t s_i(u) du
tau_i  = A_i(b)
alpha_i = 1-exp(-tau_i)
T(t) = exp(-sum_i A_i(t))
L_exact = integral_a^b T(t) sum_i s_i(t)c_i dt + T(b) background.
```

Fix an order `1,...,N`. The protocol obtains it by stable increasing mean, with input index breaking ties, but the proof holds for any fixed order. Whole-primitive compositing means

```text
L_sorted = sum_i exp(-sum_{k<i} tau_k) alpha_i c_i
           + exp(-sum_i tau_i) background.
```

The optical masses here are the exact **clipped** masses for `[a,b]`. This formula uses `1-exp(-tau_i)`, not learned opacity times a peak Gaussian value. Neither scattering nor a physical interpretation of learned 3DGS opacity is assumed.

All absolute values, color ranges and final error inequalities below are componentwise. The same proof works for any finite bounded constant channel values. Gaussian densities are continuous, so ties between stochastic arrival locations have probability zero; atomic layers with an unspecified tie convention are not needed here.

## N-label first-arrival coupling

For each label `i`, introduce an independent inhomogeneous Poisson process on `[a,b]` with intensity `s_i(t)`. Let `F_i` be its first event location, or infinity if it has no event. Then

```text
P(F_i > t) = exp(-A_i(t))
P(label i is nonempty) = alpha_i.
```

The earliest event of all labels is at `t` with label `i` with density `T(t)s_i(t)`. Thus the expectation of the earliest label's color, returning background when every label is empty, is exactly `L_exact`.

On the **same** random sample, choose instead the smallest ordered index with any event. Its probability of being label `i` is `exp(-sum_{k<i} tau_k)*alpha_i`; its expected color is `L_sorted`. Both rules return background on the identical all-empty event, with probability `exp(-sum_i tau_i)`. The background terms therefore cancel, even if the background differs from all primitive colors.

If the two chosen labels differ, let `j` be the exact earliest label and `i` the sorted label. Necessarily `i<j`, both are nonempty, and `F_j<F_i<=b`. Define

```text
W_ij = {sorted rule chooses i and exact rule chooses j},  i<j
E_ij = {F_j < F_i <= b}.
```

The `W_ij` events are disjoint: each differing sample has exactly one winner pair. Since `W_ij` is contained in `E_ij`, the triangle inequality gives

```text
abs(L_exact-L_sorted)
 <= sum_{i<j} abs(c_i-c_j) P(W_ij)
 <= sum_{i<j} abs(c_i-c_j) P(E_ij).
```

This is an N-label proof. It does not assume only two primitives overlap, nor does it count all inversion pairs as independent events.

## Exact pair-event probability and the simple bound

Independence of the two label processes yields

```text
D_ij := P(E_ij)
      = integral_a^b exp(-A_i(t)) s_i(t) [1-exp(-A_j(t))] dt.
```

The ordering matters: `i` is intended to come first, while `j` is actually encountered first on an inversion. The inversion optical mass is

```text
I_ij = integral_{a<=u<v<=b} s_j(u)s_i(v) du dv
     = integral_a^b s_i(t) A_j(t) dt
     = integral_a^b s_j(t) [tau_i-A_i(t)] dt.
```

Using `exp(-A_i)<=1` and `1-exp(-A_j)<=A_j` gives `D_ij<=I_ij`. Also `E_ij` requires both independent label processes to be nonempty, hence `D_ij<=alpha_i*alpha_j`. Therefore any conservative `Ibar_ij>=I_ij` gives the protocol's simple bound:

```text
B_simple_ij = min(Ibar_ij, alpha_i*alpha_j).
```

An equivalent infinitesimal-layer interpretation is consistent with this result: swapping two adjacent layers of optical depths `x,y` changes their contribution by `(c_i-c_j)*(1-exp(-x))*(1-exp(-y))`, multiplied by preceding transmittance. The coupling proof avoids needing a continuum bubble-sort construction to justify the N-label inequality.

## Jensen saturation in both directions

First suppose both optical masses are positive. The measure

```text
exp(-A_i(t))*s_i(t) dt / alpha_i
```

is a probability measure on `[a,b]`. The function `f(x)=1-exp(-x)` is increasing and concave for `x>=0`. Applying Jensen to the exact pair probability gives

```text
D_ij <= alpha_i * f(integral exp(-A_i)s_i A_j dt / alpha_i)
     <= alpha_i * f(I_ij / alpha_i).
```

The second inequality uses `exp(-A_i)<=1` and monotonicity of `f`; it does not replace the weighted average by an equality.

For the other direction, condition on the first event of `j`:

```text
D_ij = integral_a^b exp(-A_j(t)) s_j(t)
                    [exp(-A_i(t))-exp(-tau_i)] dt
     = integral_a^b exp(-A_j(t)) s_j(t) exp(-A_i(t))
                    f(tau_i-A_i(t)) dt.
```

Dropping the factor `exp(-A_i)<=1`, then applying Jensen with the probability measure `exp(-A_j)s_j dt / alpha_j`, gives

```text
D_ij <= alpha_j * f(integral exp(-A_j)s_j [tau_i-A_i] dt / alpha_j)
     <= alpha_j * f(I_ij / alpha_j).
```

For fixed `I>=0`, the function `g(h)=h*(1-exp(-I/h))` is nondecreasing for `h>0`: with `x=I/h`, its derivative is `1-(1+x)exp(-x)>=0`. Taking the smaller of these two Jensen bounds, replacing `I_ij` by its conservative upper bound, and retaining the nonempty-events bound gives exactly

```text
h = min(alpha_i,alpha_j)
B_jensen_ij = min(alpha_i*alpha_j, -h*expm1(-Ibar_ij/h)).
```

If `h=0`, the pair event is impossible and both pair bounds are defined as zero. The Jensen expression is no larger than `Ibar_ij`, because `1-exp(-x)<=x`. Consequently `B_jensen_ij<=B_simple_ij` in real arithmetic. This is an algebraic tightening; it is not a measured speed advantage or a claim that the result is new to the literature.

## Gaussian inversion mass and finite clipping

For the protocol's complete one-dimensional densities

```text
s_i(t) = w_i * normal_pdf(t; mu_i,sd_i),
```

the full-line optical mass is `w_i`. Draw independent locations `X_i` and `X_j` from the corresponding normalized Gaussians. Then the full-line inversion integral is

```text
I_full_ij = w_i*w_j*P(X_j<X_i)
          = w_i*w_j*Phi((mu_i-mu_j)/sqrt(sd_i^2+sd_j^2)).
```

This verifies the sign: when the presumed first component has a substantially smaller mean, its inversion probability is small. The variance in the denominator is the **sum** of the two variances. The result is valid for unequal standard deviations.

Restricting both integration locations to `[a,b]` can only decrease a nonnegative double integral. Independently, `I_ij<=tau_i*tau_j`. Hence the fixed conservative choice is

```text
Ibar_ij = min(I_full_ij, tau_i*tau_j).
```

The full-line CDF factor must multiply **full-line weights** `w_i*w_j`. Multiplying that factor by clipped `tau_i*tau_j` is not generally safe: conditioning both locations to the interval changes their ordering probability. For example, with equal widths and distinct means, a sufficiently narrow interval on which both densities are positive makes the conditional ordering probability tend to one half, even when the unconditioned probability is much smaller. The actual compositor still uses clipped masses. This distinction is preserved rather than repaired by changing fixtures after observing results.

## Global cap and exact controls

Let `Q=1-exp(-sum_i tau_i)`. Both the exact volume contribution and the sorted volume contribution are nonnegative mixtures of the same colors, with total weight `Q`. In each channel both therefore lie in `[Q*min_i c_i,Q*max_i c_i]`. The background contribution is identical, so an independent upper bound is

```text
G = Q*(max_i c_i-min_i c_i).
```

Combining independent valid upper bounds by taking their minimum gives the protocol's `E_simple` and `E_jensen`. Empty and zero-mass scenes have zero error. A single component, or any number of components with the same color, has zero compositing error in real arithmetic. These zero-error statements do not remove floating-point error from an implemented renderer.

For the equal-profile two-component control, each component has the same clipped optical mass `tau` and `alpha=1-exp(-tau)`. With red first and blue second, the exact volume contribution is

```text
(red+blue)/2 * (1-exp(-2*tau)),
```

because the local mixture color is constant. Sorted compositing instead gives

```text
alpha*red + exp(-tau)*alpha*blue.
```

Their signed difference `sorted-exact` is `(+alpha^2/2,0,-alpha^2/2)`, so the absolute red and blue errors are exactly `alpha^2/2`. Both include the same attenuated background. This formula uses the clipped mass, not the full weight; it remains valid under clipping when the two profiles are identical. More generally, coincident normalized profiles with unequal weights have constant optical-mass-weighted mixture color, furnishing the other coincident-profile analytic references fixed by the protocol.

## Cost and claim limits

The direct construction evaluates `N*(N-1)/2` pair terms, including Gaussian CDFs and color differences. Computing clipped masses, sorting, ray-to-Gaussian reduction, preprocessing and any floating-point guarantee also costs work. The saturation expressions do not remove this quadratic pair cost. An informative numerical bound might still cost more than ordinary integration of the same continuous model; the fixed qualification cannot establish efficiency.

This proof is over real numbers. Ordinary binary64 `Phi`, `exp/expm1`, clipping, masses and sums are not outward-rounded intervals. Underflow of a small positive inversion probability to zero can invalidate a claimed certificate; so can underestimated clipped masses or a downward-rounded final bound. An actual numerical guarantee must additionally bound errors in the input/ray parameters, transcendental functions, accumulation and the compositor itself. Agreement between numerical references or passing fixed tolerances is empirical qualification, not that guarantee.

No literature priority, production need, rendering speed, TOG contribution or submission readiness follows from the proof. The only authorized next empirical work is the finite qualification already fixed in PROTOCOL.md; no extra scenes, hierarchy, splitting or tile reuse is proposed here.
