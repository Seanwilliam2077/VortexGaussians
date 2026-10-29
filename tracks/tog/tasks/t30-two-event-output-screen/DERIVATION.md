# T30 — two-event output and its necessary tail screen

29 October 2026. This is an exact-real derivation. The [protocol](PROTOCOL.md) authorizes only an exact-rational necessary screen on stored masses and colors. It does not authorize computing pair moments, corrected RGB, actual errors or performance. No candidate values were computed while writing this note.

## Count-conditioned output

On the unchanged finite interval, let nonnegative continuous Gaussian densities be `s_i(z)`, their clipped masses `tau_i`, and constant bounded RGB colors `c_i`. Define `sigma=sum_i s_i`, `j=sum_i c_i*s_i`, `A(z)=integral_a^z sigma`, `tau=sum_i tau_i`, and `p0=exp(-tau)`. The combined independent Poisson processes have total count `M~Poisson(tau)`. Returning the earliest event's color, or background if none, has expectation equal to the continuous emission-absorption output.

Zero events contribute `p0*background`. One event contributes `p0*M1`, where `M1=sum_i c_i*tau_i`. For distinct labels define

```text
I_ij = integral_a^b s_i(v) integral_a^v s_j(u) du dv.
```

This is optical mass with j before i. Continuity makes event-position ties negligible and gives `I_ij+I_ji=tau_i*tau_j`. Exactly two events contribute `p0*M2`, with

```text
M2 = sum_i c_i*tau_i^2/2
   + sum_(i<j) [c_i*(tau_i*tau_j-I_ij) + c_j*I_ij].
```

The self term accounts for two events of the same label. Each cross term assigns the earlier label's color. These coefficients are nonnegative and sum to `tau^2/2`. Pair enumeration uses a fixed label order; no mean-based rendering order is needed for this identity.

## Finite Gaussian pair intervals and radius

For complete Gaussian weights `w_i`, means `mu_i` and positive standard deviations `sd_i`,

```text
I_full_ij = w_i*w_j*Phi((mu_i-mu_j)/sqrt(sd_i^2+sd_j^2))
U_ij = min(tau_i*tau_j, I_full_ij)
L_ij = max(0, tau_i*tau_j-U_ji).
```

Restricting a nonnegative full-line integral gives `I_ij<=U_ij`. Applying the reverse upper bound and the complement identity gives `L_ij<=I_ij`. The reverse full-line probability is the complementary Gaussian ordering probability. Its weights remain the full-line weights, not clipped masses. The inherited saturated *probability* bounds B do not bound this optical moment in the required way and cannot replace it.

Use one midpoint `Ihat_ij=(L_ij+U_ij)/2` in all RGB channels to form `M2hat`. With input-color box center `m=(c_min+c_max)/2`, range `d_rgb=c_max-c_min`, and

```text
p3 = 1-p0*(1+tau+tau^2/2),
Lhat = p0*(background+M1+M2hat) + p3*m,
R_rgb = p0/2 * sum_(i<j) abs(c_j-c_i)*(U_ij-L_ij)
        + p3*d_rgb/2,
```

the componentwise inequality `abs(L_exact-Lhat)<=R_rgb` follows from interval midpoint errors and bounding the remaining event colors by their channel extrema. The background contribution is exact and identical.

The two-event midpoint coefficients remain a common nonnegative color mixture. The RGB box center need not be in the colors' common convex hull; the complete output is therefore only claimed to be bounded channelwise. Also `p3=O(tau^3)` in a thin-density scaling does not make R third order: finite-clipping interval widths can remain `O(tau^2)`. An upper endpoint alone is not a signed correction.

## Ordinary expansion and inexpensive comparator

The continuous integrand satisfies `exp(-A)=p0*exp(tau-A)`. Keeping the first two terms of this exponential gives

```text
p0 * integral [1+(tau-A(z))]*j(z) dz = p0*(M1+M2).
```

The remaining scalar emission mass is p3, with a nonnegative weight. Thus this is an ordinary exponential-weight/Poisson expansion with a bounded residual, not independent evidence of novelty. Subdivision to keep each interval thin becomes ordinary piecewise exponential or moment integration.

A cheap O(N) comparator retains M1 and the known same-label term `D2=sum_i c_i*tau_i^2/2`. Its unknown mass is

```text
rcheap = p3 + p0*(tau^2-sum_i tau_i^2)/2.
```

Returning `p0*(background+M1+D2)+rcheap*m` has radius `rcheap*d_rgb/2`, without pair construction. The inherited optical-mass mixture approximation and qualified direct GL are also required ordinary comparators before any later output experiment. None is evaluated by T30.

## Exact-rational necessary screen

Every declared maximum-channel radius is at least `p3(tau)*d/2`, where `d=max_channel d_rgb`. This floor constrains this certificate, not true output error or other tail treatments.

Interpret saved binary64 masses, colors and epsilon as exact rationals. Sum masses exactly and set `t=min(tau,1)`. Define the fixed polynomials

```text
S_m(t) = sum_(k=0)^m (-t)^k/k!,  m in {12,13}.
```

For `0<=t<=1` the Taylor terms decrease in magnitude and alternate. The alternating-series remainder therefore gives `S13<=exp(-t)<=S12`. Multiplication by positive `H=1+t+t^2/2` and subtraction from one reverse these inequalities. Consequently

```text
lo = max(0,1-H*S12) <= p3(t)
hi = min(1,1-H*S13) >= p3(t), when tau<=1.
```

Moreover `p3'(x)=exp(-x)*x^2/2>=0` for nonnegative x. Thus `lo<=p3(tau)` also when tau>1, and then the fixed upper bound `hi=1` is valid. Multiplication by nonnegative `d/2` yields the protocol's floor interval. Empty input has tau=d=0 without taking color extrema. All polynomial arithmetic and comparisons can be exact rational operations; no exponential evaluation or adaptive tightening is needed.

Only a lower endpoint strictly greater than epsilon proves exclusion. Equality or a straddling interval survives this necessary test, without proving acceptance. This rational enclosure applies to the stored-mass scalar model; it does not certify the original Gaussian CDFs, clipping, parameters, pair intervals or a binary64 output implementation.

## Required full cost and claim boundary

A future complete delivery must pay parameter preparation, clipped Gaussian masses, full-line pair probabilities, interval construction, O(N²) pair/color work, output construction, certificate decisions and any discarded work or fallback. Shared data, preprocessing and reuse require explicit accounting. The O(N) tail screen cannot be reported as the complete method's cost. T30 supplies no output, timing, workload, novelty or TOG-contribution result and reopens neither T29 nor T28.
