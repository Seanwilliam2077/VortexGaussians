# T40 independent mathematical review

30 October 2026. **No unresolved mathematical blocker found after two accounting corrections.** This review read only T40 PROTOCOL/README and the saved T39 README. It independently checked the real-arithmetic derivations below; it did not acquire sources, execute numerical examples, inspect renderer code, construct another estimator or assess publication novelty. The protocol correctly identifies its scope as recorded after preliminary algebra rather than an empirical preregistration.

## Checks

1. **Hit-conditioned expectation and two-component bound.** Given the true first event, earlier ordered components have independent residual exponential thresholds. Thus the stated G is the conditional expectation of S, including the fact that component j is certainly active. On the hit space, E[G]=L_sort/A and both Z and Y have expectation L. For two components, I=2 implies J=2, so 0<=v<=p. The residual is the color contrast times D=1_{J=2}(1-exp(-r_1)); 0<=D<=1-q and E[D]=p-v. Therefore E[D^2]<=(1-q)E[D]. The two subsequent inequalities use v<=q and p-v<=p, with nonnegative factors. They are valid, including zero masses and equal colors with A>0. The result compares the stated label-valued estimators, not all equally informed ordinary methods or equal work.

2. **Three-Gaussian limiting family.** Truncation to [-1,4] has normalization tending to one. Multiplying the third Gaussian by exp(2/epsilon^2) makes its cumulative hazard vanish at every fixed t<1 and diverge at every fixed t>1; at t=1 the remaining Gaussian-tail prefactor tends to zero. Coupling all epsilon values through the same finite exponential threshold gives its first-event time tending to 1. The first two active event times tend to 0 and 2. The limiting winner consequently has color one, while G takes values 1 and 1/2 on events of probability 1/2. L_sort tends to 3/4, giving the stated corrected values 3/4 and 5/4 and variance 1/16. The latter value is permissible without clipping. A tends to one, so conditioning on hit does not alter these limits. Bounded convergence applies to colors and corrected samples even though the third optical mass diverges. This is a symbolic counterexample, not an admissible finite-precision implementation or measured workload.

3. **Oracle coefficient.** On the hit space, X is Bernoulli. Cov(X,G)=Var(X)(E[G|X=1]-E[G|X=0]), so its absolute value is at most Var(X) when G is in [0,1]. Here Var(G) tends to 1/16. For every finite positive epsilon, component 2 has positive winning probability and other components also can win, so Var(X)>0; the relative-variance expression is defined. Thus rho^2<=Var(X)/Var(G) tends to zero, beta_* tends to zero and the optimal residual variance divided by Var(X) tends to one. This conclusion is limited to the specified control and family.

4. **Derivative collapse.** Differentiation of the ordered remaining-mass composition gives partial F/partial r_j=G(j,t)-F. With r'_j=-s_j and T'=-sigma T, this yields (TF)'=-T sum_j s_j G(j,t), the endpoints TF(a)=L_sort and TF(b)=0, and the stated K identity. The prefix scan is linear in the component count; it adds work to an already linear ordinary integrand and supplies no automatic reduction in quadrature nodes.

5. **Stronger ordinary comparison.** The conditional label law at distance t is s_j(t)/sigma(t), wherever the hit-distance density is positive. Both distance-conditioned expressions follow. For the shared proportional profile, c_bar=1/2 exactly, whereas D_bar varies strictly with u for m>0 under a positive density on (0,1). The ordinary expression has zero variance and the unspecialized correction has positive variance. Both must receive the same analytic shortcut; this algebra is not justification for a deliberately weakened implementation comparison.

6. **Skip-empty work and cost.** Independent Poisson increments on concatenated mass blocks allow jumping to a selected block's first event and restarting at its right boundary without changing other blocks' first-event laws. The initial gap conditioned on any hit has the stated truncated-exponential formula. This changes expected active-block/inversion count from sum_i alpha_i to sum_i alpha_i/A. Mass-prefix construction, searches, inversions and conditional evaluation remain paid. The oracle work condition follows from V_*=V_X(1-rho^2) for positive variances, with the common A^2 image scaling cancelling in the asymptotic ratio. Finite cost must include setup, at least one stochastic sample when the constant is not analytically known, and any coefficient estimation. It is an expected variance/MSE criterion, not a hard pixel-error guarantee.

## Corrections and decision

Before finalization, this review requested (i) explicit division by A for the hit-conditioned skip-empty expected count and (ii) max(1,ceil(V/v)) for the generic stochastic sample budget, separating a known analytic branch. Both corrections are present in the final README; the gap count is appropriately stated as at most K_active+1. No numerical run was needed or performed.

The narrow positive theorem and the negative extension are both retained. The final decision to select no implementation is supported: the algebra identifies no inexpensive distinct evaluator, qualified useful task or measured variance-per-total-work advantage. It does not establish that every possible stochastic method fails. The stopping rule correctly ends this mathematical boundary task without opening a new variant or qualification loop.

## Reviewed identities

Hashes were recorded after root confirmed final text and newline normalization:

| File | SHA-256 |
|---|---|
| T40 README.md | `9868dc07bc1d27aa9c9c69673635b6a5228973a98d252e6ad497e02e6e80399f` |
| T40 PROTOCOL.md | `0cce53ac99b356ff1e8efe1a000b9c21e0eaab82f58e251ecbda58bbdc1a062b` |
| T39 README.md | `02acbfb8670481e6cb2565b1ff8c6376d6d6354ee94431d4e1965a0cc9dde3c1` |
