# T40 — conditional correction has a two-component guarantee, not general superiority

30 October 2026. **No implementation selected.** This finite mathematical continuation of [T39](../t39-coupled-event-screen/README.md) proves a useful two-component variance bound, identifies a three-Gaussian counterexample to its extension, and rewrites the correction as an ordinary one-dimensional residual integral. It also strengthens the ordinary comparison. None is an empirical performance result, a claimed new theorem or a TOG contribution. No numerical evaluation, scene, code implementation, source acquisition or simulation occurred.

## Shared model and fair hit conditioning

Use T39's finite ray interval[a,b], extinction s_i, cumulative H_i(t), mass m_i, colors c_i and fixed center order. Write sigma=sum_i s_i, T(t)=exp(-sum_i H_i(t)), A=1-T(b)>0. Independent exponential optical thresholds define the true first event(J,t) and first nonempty ordered component I. X=c_J and S=c_I on a hit; both are zero otherwise. L_sort=E[S].

Condition both candidate and ordinary sampler on at least one event, and pay its sampling cost. With r_i(t)=m_i-H_i(t),

```text
G(j,t) = E[S | J=j,t]
       = sum_{i<j} c_i(1-exp(-r_i))exp(-sum_{k<i}r_k)
         + c_j exp(-sum_{k<j}r_k).

ordinary sample:  Z = A c_J
corrected sample: Y = L_sort + A(c_J-G(J,t)).
```

Both have expectation L=integral_a^b T(t)sum_i s_i(t)c_i dt. A background term T(b)c_background is deterministic and common. These are real-arithmetic statements. Independent averages divide variances by sample count; no floating-point certificate, sampling implementation or hard per-image error bound follows.

## Positive result: two components

For two components define q=exp(-m_1), p=P(J=2|hit), v=P(I=2|hit)=q(1-exp(-m_2))/A. Since I=2 implies J=2, 0<=v<=p. Also v<=q because1-exp(-m_2)<=A. The normalized scalar correction is

```text
D = 1_{J=2}(1-exp(-(m_1-H_1(t)))),
0 <= D <= 1-q,
E[D] = p-v.
```

Therefore, with mu=p-v,

```text
Var(D) <= (1-q)mu - mu^2
        = mu(1-q-p+v)
       <= mu(1-p)
       <= p(1-p).
```

For any color channel k, Y's single-sample variance is A^2(c_2k-c_1k)^2 Var(D), while Z's is A^2(c_2k-c_1k)^2 p(1-p). Thus this conditional correction cannot increase variance relative to this equally hit-conditioned, label-valued ordinary estimator for two components.

The statement holds for any such nonnegative profiles, not specifically Gaussians. It does not compare evaluation costs, does not cover n>2, and does not dominate ordinary methods that also integrate out the component label. Equal color, zero mass and other analytic branches remain shared ordinary cases. This positive result is retained even though the development decision is negative.

## Extension fails: an explicit three-Gaussian limit

On[-1,4], let g_(mu,epsilon) be the normal density with mean mu and standard deviation epsilon, normalized over this interval. For every epsilon>0 choose finite positive Gaussian extinctions

```text
s_1 = log(2) g_(0,epsilon),       c_1=1,
s_2 = log(2) g_(2,epsilon),       c_2=0,
s_3 = exp(2/epsilon^2) g_(3,epsilon), c_3=1.
```

This is a symbolic limiting family, not an executed high-opacity benchmark. Centers stay in order0<2<3. First-event times for active components1/2 converge to0/2; each is active with probability1/2. For fixed a<t<1, the third cumulative mass tends to zero; for1<t<3 it diverges. Its Gaussian-tail exponent is [2-(3-t)^2/2]/epsilon^2, which changes sign at1. At t>=3 it also diverges. Consequently the third first-event time tends to1 almost surely. H_3(1) itself tending to zero does not change this event-time limit.

The winner is asymptotically component1 when it is active, and component3 otherwise. Hence X tends to1 and A tends to1, giving Var(Z)→0. Meanwhile L_sort tends to3/4. On the component1 outcome G=1; on the component3 outcome, remaining masses of components1/2 tend to0/log(2), so G tends to1/2. Therefore

```text
Y -> 3/4 with probability1/2,
     5/4 with probability1/2.
E[Y] -> 1,    Var(Y) -> 1/16.
```

Bounded convergence justifies the moments; all relevant colors, G and corrected samples are uniformly bounded. This disproves universal variance improvement after T39's conditioning, even with ordered Gaussian centers and equal hit conditioning. It does not disprove all coefficients or all workload-specific variants. In this limit the ordinary optimal control coefficient tends to zero. The value5/4 is allowed for an unbiased corrected sample; clipping would change the estimator.

Even an oracle coefficient has no asymptotic relative variance gain in this family. For hit-conditioned X and G, write V_X=Var(X), V_G=Var(G) and rho their correlation. The optimal coefficient is beta_*=Cov(X,G)/V_G and its residual variance is V_*=V_X(1-rho^2). Since X is Bernoulli and G is in[0,1], |Cov(X,G)|<=V_X. Here V_G tends to1/16 and V_X tends to0, so rho^2<=V_X/V_G tends to0, beta_* tends to0, and V_*/V_X tends to1. These limits concern the fixed center-order control, not every possible grouping or surrogate.

## The apparent pairwise correction collapses to one dimension

For a fixed t let

```text
R_i(t) = exp(-sum_{k<i}r_k(t)),   R_1=1,
Q_j(t) = sum_{i<j} c_i(R_i-R_{i+1}),
F(t)   = sum_i c_i(R_i-R_{i+1}).
```

F is the sorted color of the remaining optical masses. Then
G(j,t)=Q_j+c_jR_j and c_j-G(j,t)=(1-R_j)c_j-Q_j.
Thus the residual integrand

```text
K(t) = T(t) sum_j s_j(t)[(1-R_j(t))c_j-Q_j(t)]
```

requires one prefix scan, not an explicit pairwise double loop. Differentiating F with respect to a remaining mass gives partial F/partial r_j=G(j,t)-F(t). Since r'_j=-s_j,

```text
F' = sigma F - sum_j s_j G(j,t).
B(t)=T(t)F(t)  =>  B'=-T sum_j s_j G(j,t).
B(a)=L_sort,   B(b)=0.
K(t)=T(t)sum_j s_j(t)c_j + B'(t).
L = L_sort + integral_a^b K(t)dt.
```

This is the original one-dimensional integral plus the derivative of a function with known endpoint values. It identifies a standard boundary-corrected residual formulation; it supplies no new Gaussian closed-form integral. Even for two components the residual contains products of cumulative Gaussian exponentials.

At a deterministic node, ordinary emission integration uses the H_i/CDFs, s_i/PDFs and color reduction. K uses the same quantities and additional ordered prefix/exponential work. The O(n) scan avoids an unnecessarily quadratic implementation; it does not improve on the ordinary O(n) integrand evaluation. Whether its shape reduces the number of required nodes is unmeasured and no favorable task has been identified.

## Fair stronger ordinary comparison

Conditioning a first-event sample on its distance also integrates out its label. Given hit, t has density T(t)sigma(t)/A. The ordinary estimator can use

```text
c_bar(t) = sum_i s_i(t)c_i / sigma(t),
Z_time  = A c_bar(t).
```

The equally conditioned correction is Y_time=L_sort+A D_bar(t), with
D_bar=sum_j s_j[(1-R_j)c_j-Q_j]/sigma. This is ordinary importance sampling of K. Conditioning reduces each method's variance relative to its own label-valued version; it does not order their variances against each other.

An exact shared-branch case demonstrates that distinction. Let s_1=s_2=m f(t), m>0, integral_a^b f=1, and colors0/1. A common normalized Gaussian is admissible. With u=integral_a^t f,

```text
A=1-exp(-2m),                 c_bar(t)=1/2,
D_bar(t)=(1/2)(1-exp(-m(1-u))),
density(u | hit)=2m exp(-2mu)/A on(0,1).
```

Z_time=A/2 is constant and has zero variance. D_bar is nonconstant on a positive-density interval, so Y_time has strictly positive variance. Both methods must receive the proportional-profile analytic shortcut; this example is a mathematical boundary, not a license to benchmark a deliberately weakened candidate or baseline. It shows why the positive two-component theorem alone is insufficient.

## Complete cost includes ordinary sparse sampling

T39's n exponential draws describe an unpruned implementation, not a necessary lower bound. A generic alternative concatenates component optical-mass blocks into cumulative prefixes. A unit-rate Poisson process on that axis can jump over empty blocks. In a selected block, invert H_i at its first optical event, then skip the rest of that block and sample the next exponential gap from its right boundary. Independent increments give exactly the component first-event distribution. With K_active nonempty blocks, inversions number K_active; unconditionally E[K_active]=sum_i(1-exp(-m_i)). Draws are at most K_active+1, counting a final overshooting gap, and binary-search block locations cost O(K_active log n), after O(n) mass-prefix setup.

For hit conditioning, the first global optical gap may be sampled as -log(1-U A), followed by ordinary exponential gaps after selected block boundaries. Now E[K_active | hit]=sum_i(1-exp(-m_i))/A; the expected gap count is at most this value plus1. This avoids assuming a free inverse of sum_i H_i(t). The plain sampler can choose any fixed block order and need not pay center sorting; the proposed sorted correction does. Both may use this generic skip-empty technique. Spatial traversal, finite masses, inverse CDFs, prefix construction and all conditional density/CDF evaluations still count. This is an ordinary comparator improvement derived from Poisson increments, not a selected new method or an executed optimization.

## Decision

The relevant asymptotic cost comparison is c_RB V_* < c_X V_X, not V_*<V_X alone. With oracle coefficient this requires rho^2>1-c_X/c_RB. For a finite per-channel variance target v>0, setup costs K and integer sample counts also matter: compare K+c*max(1,ceil(V/v)), with V measured in the final image scale and coefficient-estimation cost included. A known analytic branch may instead use zero stochastic samples with its evaluation cost included in K; zero variance alone does not reveal an otherwise unknown constant without any sample. This is an expected squared-error comparison for fixed unbiased estimators, not a deterministic pixel-error guarantee. In the three-Gaussian limit there is no asymptotic relative variance gain, so a persistent positive relative cost overhead would lose; actual costs were not measured.

There is a valid narrow variance guarantee, but no general one, no identified reduction in required density evaluations, and no qualified useful workload with an equal-total-cost advantage. The conditional formula is reducible to a standard residual integral and must compete with stronger ordinary conditioning and sparse event sampling. **Do not implement this refinement or start a numerical sweep on present evidence.**

The analysis stops here under the [finite scope](PROTOCOL.md). It does not select another coefficient, estimator variant, toy scene or source batch. Reopening requires a concrete distinct efficient construction plus an assessable task; collecting more algebraic qualifications alone is not the full research objective. See [adversarial review](../../../validation/t40-mathematical-review.md). The full goal remains active and all earlier failures, art/main state and deleted automation are unchanged.
