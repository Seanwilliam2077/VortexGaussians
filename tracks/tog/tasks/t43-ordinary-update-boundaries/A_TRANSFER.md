# A — a view-preserving merge that ordinary moment matching already supplies

This is an algebraic boundary within T15-A, not a new method, numerical qualification or general impossibility claim. T15 disproved that mechanical moments preserve every ray. T39 showed why retaining an exact signed optical residual supplies no free compression. Here the narrower question is whether adding a current view's optical moments changes the ordinary merge.

## Model and ordinary merge

Let positive masses m_i, positive-definite covariances Sigma_i and means mu_i define

```text
rho(x) = sum_i m_i phi_3(x; mu_i, Sigma_i).
M = sum_i m_i, w_i = m_i / M,
mu = sum_i w_i mu_i,
Sigma = sum_i w_i [Sigma_i + (mu_i-mu)(mu_i-mu)^T].
```

The merged density is M phi_3(x;mu,Sigma). Let P be a 2×3 matrix with orthonormal rows specifying an orthographic image plane. Extinction per unit mass kappa is constant and common. Integrate complete parallel lines, with no near/far clipping or foreground occluder. Gaussian marginalization gives

```text
tau(y) = kappa sum_i m_i phi_2(y; P mu_i, P Sigma_i P^T).
```

Suppose every input has the same projected mean y_bar and covariance S:

```text
P mu_i = y_bar,       P Sigma_i P^T = S.
```

Then P mu=y_bar, and P(mu_i-mu)=0 makes the between-mean term vanish under projection. Hence P Sigma P^T=S. Both the original mixture and merged Gaussian have

```text
tau(y) = kappa M phi_2(y; y_bar, S)
```

for every image-plane point y. The entire orthographic optical-depth image, and thus exp(-tau), is exact in real arithmetic. This class is nonempty: depth means, depth variances and image-plane/depth correlations can differ while projected marginals coincide. Ordinary three-dimensional moment matching already produces this result; no extra optical constraint or specialized update is required.

## Why low-order view constraints are redundant here

Without the common-footprint assumption, the optical image still obeys

```text
integral tau(y) dy       = kappa M,
integral y tau(y) dy     = kappa M P mu,
integral yy^T tau(y) dy  = kappa M P (Sigma + mu mu^T) P^T.
```

Thus preserving full spatial moments through degree two automatically preserves these optical-depth moments in every orthographic view. Adding them to the same moment-matching problem adds no independent condition. They are moments of tau, not moments of exp(-tau), opacity or RGB. Spatial second moments are reconstruction constraints, not a universal physical conservation law; an algorithm retaining only mass and momentum need not already retain them.

## Mechanical affine state

For component velocities u_i(x)=v_i+C_i(x-mu_i), retain the velocity-position cross moment as well:

```text
v = sum_i w_i v_i,
B_vx = sum_i w_i [C_i Sigma_i + (v_i-v)(mu_i-mu)^T],
C = B_vx Sigma^(-1),
u_merged(x) = v + C(x-mu).
```

Mass, first and second spatial moments match by construction. The total linear momentum is Mv. The original and merged raw cross moments integral rho u x^T are both M[v mu^T+B_vx]. Total angular momentum is the corresponding antisymmetric contraction of this matrix, so it also matches about the same origin. This is a statement about the declared continuous affine momentum densities. It does not identify Sigma with an APIC stencil tensor, transfer an unrelated discretization's theorem, preserve kinetic energy/local velocity or local incompressibility, or guarantee the subsequent dynamics. The inverse notation specifies a linear solve; it is not advice to form a numerical inverse. Positive-definite input covariances make Sigma positive definite in real arithmetic, but do not guarantee good conditioning.

## Limits and complete comparison

The exact optical result requires complete parallel rays and identical projected marginal distributions. Finite clipping, occlusion, perspective rays, approximate footprint matching or a changed camera require their own error treatment. Even exact total optical depth is insufficient for arbitrary depth-dependent color mixing. A common color with no interleaved differently colored volume gives the usual color times 1-exp(-tau), plus transmitted background; that special case must also be available to the ordinary baseline.

For an already known group of k components, moments and compatibility tests take O(k) fixed-dimensional arithmetic, plus one 3×3 solve for C. Group construction/search, footprint testing, reclassification under camera motion, reconstruction and simulation continuation are additional work. No costs were timed. A fair ordinary merge uses the exact same formulas and information, hence the same result and cost. Separate physical/render representations can also exploit identical rendered footprints while retaining fine physical state.

The construction supplies a positive, precisely scoped optical-preservation case, but no distinct low-cost update. General approximate finite-view compression remains possible; it is not selected by this identity. No numerical test or implementation follows.
