# T39 — coupled event correction: valid expectation, no selected new method

30 October 2026. **NO_GO for implementing this construction as the next research method.** A proposed Gaussian first-event sampler is already described in prior work. Coupling it to sorted compositing gives a standard control variate, and a fixed unit coefficient can increase single-sample variance from nearly zero to1/4. Conditional expectation repairs that particular failure but adds work without an identified distinct cost mechanism. These are mathematical screening results, not numerical measurements, a complete novelty survey or proof that every stochastic refinement fails.

## Concrete construction and expectation

This is our derivation in real arithmetic. Fix a ray interval[a,b], nonnegative Gaussian extinction functions s_i(t), and per-component colors c_i in[0,1]^3. Let H_i(t)=integral_a^t s_i(u)du and m_i=H_i(b). Use a fixed center order1,...,n, with deterministic tie-breaking. For independent E_i~Exp(1), set

```text
F_i = inverse_H_i(E_i), if E_i < m_i; otherwise infinity.
J   = argmin_i F_i, or none if all are infinity.
I   = smallest index i with E_i < m_i, or none.
X   = c_J on a hit, otherwise 0.
S   = c_I on a hit, otherwise 0.
```

The probability that all component events lie after t is exp(-sum_i H_i(t)). The probability density that j supplies the first event is s_j(t)exp(-sum_i H_i(t)). Hence E[X] is exactly the declared continuous emission–absorption RGB integral. Independently,

```text
L_sort = E[S] = sum_i c_i (1-exp(-m_i)) exp(-sum_{k<i}m_k).
Y_N    = L_sort + (1/N) sum_r (X_r-S_r).
E[Y_N] = E[X].
```

Total alpha=1-exp(-sum_i m_i) and a background contribution exp(-sum_i m_i)c_background can be added deterministically. This uses optical masses, not the original demo's billboard opacities; it does not make those models equivalent. Finite-precision inverse-CDF/tail handling would still need qualification. No implementation or formal floating-point guarantee is supplied here.

Individual corrected RGB samples can be negative or exceed the color range. Clamping them, or clamping the final estimator, generally destroys unbiasedness. Those are ordinary Monte Carlo implementation obligations, not extra novelty.

The exact sampling ingredient is already explicit in [StochasticSplats v1, section3.4 and supplement4](https://arxiv.org/html/2503.24366v1): sample component free-flight distances and select their minimum for volumetric intermixing. Our additive expectation/residual identity is the classical control-variate form, as set out in [Crespo et al., section3.3, equations5–7](https://arxiv.org/html/2008.06722v1). This mapping disqualifies claiming either ingredient alone as new; it does not assert that these sources implement every proposed coupling or conditional variant.

## Variance and a counterexample

For one color channel and independent samples,

```text
N Var(Y_N) = Var(X-S)
           = Var(X)+Var(S)-2 Cov(X,S).
```

A unit correction reduces variance only when 2Cov(X,S)>Var(S). Small mean bias E[X-S] alone does not imply this inequality. The correction is nonzero only if winner J differs in color from first-active index I. Since J>=I on a hit, its second moment is exactly

```text
E[(X-S)^2] = sum_{i<j} (c_j-c_i)^2 P(I=i,J=j).
```

This is an event/contrast description, not a cheap computable probability formula. Bounds on independent sampled density positions cannot silently replace probabilities of first Poisson events. No old certificate or T31/T37 result is transferred to this estimator.

A variance counterexample uses two fixed positive Gaussian profiles on the finite interval, with center order mu_1<mu_2 and colors c_1=0,c_2=1. Fix m_1=log(2) and scale only the second amplitude by K→infinity. For every t>a, H_2(t)→infinity, so F_2→a almost surely, while F_1>a or infinity. Therefore

```text
X → 1;                     Var(X) → 0.
S → 1_{E_1 >= log(2)};      Var(S) → 1/4.
X-S → 1_{E_1 < log(2)};     Var(X-S) → 1/4.
```

Bounded convergence justifies these moment limits. Thus ordered centers do not guarantee a useful coupling. This is an algebraic limiting counterexample, not a manufactured benchmark or an executed Gaussian scene. A variable coefficient beta has the ordinary optimum Cov(X,S)/Var(S), tending to zero here. Estimating beta from the same finite samples can introduce bias; independent pilot data or a justified estimator would have to be counted. No such procedure was run.

## Stronger ordinary remedy: conditional expectation

The counterexample does not justify dismissing every coupled estimator. Condition on the exact first event(J=j,t). Let r_i(t)=m_i-H_i(t). Independent Poisson increments after t imply

```text
G(j,t) = E[S | J=j,t]
       = sum_{i<j} c_i (1-exp(-r_i)) exp(-sum_{k<i}r_k)
         + c_j exp(-sum_{k<j}r_k).
Y_RB   = L_sort + c_j - G(j,t).
```

For no event, X=S=G=0 and the sample correction is zero. This is Rao–Blackwell conditioning of the unit control variate: its variance cannot exceed Var(X-S), but need not beat Var(X) at equal cost. In the counterexample limit it removes the extra Bernoulli noise. It requires up to j-1 additional cumulative-depth evaluations and a prefix composition per hit. This conditional rule follows from ordinary independent increments; no Gaussian-specific cheap evaluator or distinct novelty has been identified. It is recorded to avoid rejecting a whole family using only the weak unit-coefficient case.

## Complete work and decision

The proposed coupled construction pays ray reduction, finite optical masses, any culling/tail policy, ordering and L_sort setup. The ordinary X-only first-event sampler needs neither center sorting nor L_sort. An unpruned sample visits n components and draws n exponential variates; the expected number of active inverse-CDF evaluations is sum_i(1-exp(-m_i)). Selecting both winners is linear. Conditional correction adds remaining-mass CDF evaluations and prefix accumulation. A small correction does not skip this work automatically. Alternative tracking, valid spatial bounds and shared setup must be equally available to ordinary comparators. None of these costs has been timed.

A fair later comparison would include the continuous-intermixing sampler identified above, equally informed ordinary control variates/conditioning, and deterministic same-model quadrature with analytic optical depth. It would compare total setup+render cost at equal image error/noise and include temporal behavior. Neither a surface-alpha renderer nor the old scalar Python solver alone is a strong baseline. T39 acquired no executable reference and selected no qualifying task.

The useful next ingredient is absent: a specific cheap joint/conditional sampler, variance reduction per total work beyond those ordinary remedies, and an independently justified useful workload. Do not open a renderer, sample-count sweep or old-plume rerun to make generic unbiasedness look like progress. The [bounded source record](sources.json) contains two queries and three primary pages; no fourth page was needed. [Adversarial review](../../../validation/t39-mechanism-review.md) checks the math, not publication novelty. The separately considered [A/B algebra](OTHER_OPERATIONS.md) also selects no implementation. The full goal remains active; this result does not satisfy TOG contribution, strong-baseline or multi-scene requirements.
