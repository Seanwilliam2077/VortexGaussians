# Next finite task: a finite-view pointwise remainder, before any experiment

The new question is narrower than generic compression: can the exact moment cancellation in T44 yield a conservative finite-change pointwise optical-depth bound using a constant-size record per already formed common-footprint group? This would address a different accuracy contract from the existing U3/U2 integrated L1 bounds. No benefit or novelty is established by writing the question. The same contract and information must be available to ordinary alternatives.

The next task is algebra only: one proposed remainder construction, full cost/retained-state accounting and one independent review. No scene, numerical evaluation, implementation, rendering, new source search or parameter/seed sweep. Stop after proving a valid finite bound or finding the obstruction. Do not replace a failed remainder with another metric or call a first Taylor term a certificate. A valid result still would not automatically authorize a numerical qualification or establish a TOG contribution.

## Fixed construction to check

Keep T44's normalized positive Gaussian mixture, common initial orthographic footprint, common invertible affine motion, fixed mass/extinction and full-line optics. Choose the initial orthonormal coordinates (P0,n0) and write

```text
mu_i=(a0,z_i),     Sigma_i=[[S0,b_i],[b_i^T,d_i]],
```

where d_i is the depth variance, not a standard deviation. Let weighted averages be z_bar,b_bar,d_bar, and let v_z=sum_i w_i(z_i-z_bar)². For current Q=P F put A=Q P0^T and h=Q n0. Relative to the current projected moment Gaussian g=N(a_g,S_g), component parameter differences are exactly

```text
xi_i = h (z_i-z_bar),
Delta_i = A(b_i-b_bar)h^T + h(b_i-b_bar)^T A^T
          +(d_i-d_bar-v_z)hh^T.
```

Thus `sum w_i xi_i=0` and `sum w_i(Delta_i+xi_i xi_i^T)=0`. The proposed route expands a Gaussian along the parameter segment `(a_g+t xi_i,S_g+t Delta_i)`, t in [0,1]. Its fixed differential operator is

```text
D_i = -xi_i:grad + (1/2)Delta_i:grad².
```

The first parameter-order term and the mean-mean part of the second cancel after weighted aggregation. What remains has third/fourth spatial derivatives at g plus the exact third parameter-order integral remainder, requiring spatial derivative orders three through six along the segment. Establish all signs, constants and remainder weights; do not assume an infinitesimal expansion holds over a finite angle.

A possible uniform covariance floor is `lambda=min_i lambda_min(Sigma_i) * lambda_min(Q Q^T)`. Verify it for both endpoint covariances and their convex segment. Bound uniform spatial derivatives using an explicit Gaussian Fourier integral (or another fully specified exact-real bound); retaining positivity alone without a quantitative floor is insufficient. The proposed stored nonnegative quantities are `|z_i-z_bar|`, `||b_i-b_bar||`, and `|d_i-d_bar-v_z|`, through total-degree-three weighted moments, plus the covariance floor and ordinary merged moments. The next analysis must verify that a finite fixed list actually suffices to evaluate every coefficient without rereading the fine components.

## What would change the decision

Require a finite pointwise bound for all image-plane positions, zero when h=0, with no hidden per-component runtime work and no missing Gaussian-tail term. A symbolic limit in which it tends to zero is not a measured useful acceptance rate. Distinguish normalized density, physical optical depth, transmittance, finite-pixel averages and arbitrary RGB. Specify exact arithmetic versus a future floating-point implementation.

Count group formation, O(k) retained-statistic preparation if achievable, record size, per-frame matrix/bound work, invalidation under component-specific/nonlinear motion, and storage needed for later unmerging. Retaining child Gaussians in a hierarchy is allowed, but then do not claim their memory disappeared. A destructive merge cannot be undone merely because a guard later rejects it.

Compare with ordinary stored U3, reevaluated U2, Gaussian overlap and generic derivative/interval error methods on the identical requested accuracy contract. Binary groups already have constant-cost ordinary checks. If the result is merely a generic bound with no justified useful regime, record that rather than starting a benchmark to manufacture one. A concrete mathematically valid and distinguishable cost/accuracy opportunity would be necessary, but not sufficient, for later source/implementation/workload selection.
