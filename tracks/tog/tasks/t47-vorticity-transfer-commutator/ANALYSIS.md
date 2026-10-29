# T47 — what does a deformed vortex source transport?

This is a continuous operator calculation, not a simulation or a new fluid solver. The [scope](SCOPE.md) was recorded after recognizing that raw vector-Gaussian sources being non-solenoidal is already explicit in P5c. The new question is the order of projection and affine transport. The [four-file audit](LOCAL_MODEL.md) prevents attribution to an unimplemented code path; the [named-source screen](SOURCES.md) records existing alternatives.

## 1. State, domain and transport

Work on R³ with smooth decaying real vector fields, interpreted through their Fourier transforms. Statements below concern k ≠ 0; choosing P(0) = I does not change the result. Boundaries, harmonic components, discrete differentiation, floating-point error and component-specific flow maps are outside this calculation.

Let eta be the raw source and let

    P(k) = I - k k^T / |k|²,
    u = curl (-Delta)^(-1) eta,
    omega = curl u = P eta.

The last equality follows from the Fourier multiplier of curl: i k cross, hence curl curl (-Delta)^(-1) has symbol P. The reconstructed velocity is divergence-free even when eta is not. This is already acknowledged by the local reference; it is not claimed as a discovery.

Choose one constant real F with det F = 1 and define the Cauchy pushforward

    (T_F eta)(x) = F eta(F^(-1) x).

A translation adds a common Fourier phase and does not affect commutation. For normalized Gaussian sources,

    eta(x) = sum_i Gamma_i G_(Sigma_i)(x - mu_i),

T_F eta is represented exactly by Gamma_i -> F Gamma_i, mu_i -> F mu_i, and Sigma_i -> F Sigma_i F^T. This is a proposed full-field operation; P5c's unchanged scalar sigma and the demo's display covariance do not implement it. No assertion is made that an anisotropic evaluator is already available.

The competing meanings are

    A = P T_F eta      (transport the raw source, reconstruct afterward),
    B = T_F P eta      (transport the originally reconstructed vorticity).

Both are solenoidal: for B, constant-F Cauchy transport preserves divergence. This does not imply equality. Nor is arbitrary prescribed F necessarily a flow map produced by its own Biot–Savart velocity. A correct vorticity transport still requires velocity reconstruction; pushing the old velocity by F is not generally the same operation.

## 2. Exact commutator and equality cases

Set q = F^T k and M = F F^T. Since det F = 1,

    Fourier(T_F eta)(k) = F eta_hat(q).

Direct multiplication gives

    C_F(k) = P(k) F - F P(q)
           = [M k / (k^T M k) - k / |k|²] q^T.                 (1)

Thus A_hat(k) - B_hat(k) = C_F(k) eta_hat(q). The bracket is perpendicular to k, so C_F is transverse and has rank at most one. A divergence check alone cannot distinguish these states.

Because q is nonzero and M is positive definite:

- At fixed k, the operator is zero exactly when M k is parallel to k, i.e. k is an eigenvector of M.
- At a fixed input mode, the difference is zero exactly when that direction condition holds or q^T eta_hat(q) = 0.
- Every already-solenoidal eta therefore commutes with this transport, for any allowed F.
- Equality for every input at every frequency requires every direction to be an eigenvector of M. This is equivalent to M = a I. Since det M = 1, a = 1, and F is a proper rotation.

These are exact real-arithmetic statements about the continuous model. They do not quantify errors of the existing numerical solver.

## 3. Gauge example with its representation limit

Let phi be an isotropic nondegenerate normalized Gaussian and eta = grad phi. Then P eta = 0 and its initial Biot–Savart velocity is zero. Define phi_F(x) = phi(F^(-1)x). The chain rule gives

    T_F grad phi = M grad phi_F.

This is generally not an ordinary Euclidean gradient. In particular, take the symbolic parameters

    F = diag(s, s^(-1), 1), s > 0, s != 1,
    k = kappa (1, 1, 0), kappa != 0.

Since eta_hat(q) = i q phi_hat(q),

    A_hat(k) = i P(k) M k phi_hat(q)
             = (i kappa / 2)(s² - s^(-2))(1,-1,0) phi_hat(q) != 0,
    B_hat(k) = 0.                                             (2)

Continuity makes the difference nonzero in a neighborhood of this frequency; it is not a single-mode measure-zero artifact. A raw gradient that represented zero physical vorticity can produce nonzero projected output after the specified raw-source transport. This is representation/gauge dependence, not physical creation of vorticity.

Crucially, grad phi is a Gaussian with a linear prefactor, not a single Gaussian times a constant vector. This continuous example does not establish an exact discrete gauge freedom in a finite constant-vector Gaussian dictionary. Equation (1) still applies to sources in that dictionary, but no finite-particle benchmark, measured error, or existing-code failure follows from (2).

## 4. Ordinary transformed projection

The direct remedy is B = T_F(P eta). If the stored state is instead b = T_F eta, conjugate the projection:

    Q_F = T_F P T_F^(-1),
    Q_F(k) = F P(F^T k) F^(-1)
           = I - M k k^T / (k^T M k).                        (3)

Then Q_F b = B by construction. It satisfies Q_F² = Q_F, range Q_F = k-perp and kernel Q_F = span(M k). It is generally oblique in the Euclidean metric and orthogonal in the M^(-1) metric: M^(-1) Q_F = M^(-1) - k k^T/(k^T M k) is symmetric.

In physical space this is the constant-coefficient weighted Helmholtz decomposition

    div(M grad psi) = div b,
    Q_F b = b - M grad psi.                                  (4)

It annihilates the transported gauge M grad phi_F. No new algorithm is needed to derive this repair: it is ordinary projection conjugated by a coordinate transport. This classification follows from the displayed derivation, not a claim that the two inspected papers state exactly (1)–(4).

## 5. Full cost and decision boundary

Transforming N Gaussian parameters costs O(N) arithmetic and stores the transformed covariances/strengths; storing one common F or symmetric M adds constant state. This accounts only for raw source transport. P eta generally has nonlocal tails and need not remain in the original finite constant-vector Gaussian family.

The 3-by-3 formula in (3) costs constant arithmetic per available Fourier mode. Obtaining those modes from particles, representing the domain, applying the inverse transform or weighted elliptic inverse, handling boundaries, and reconstructing velocity remain costs. It is not an O(1) scene update or an O(1) per-Gaussian physical repair. No grid size, accuracy target, transform cost, particle quadrature or timing is qualified here. Analytic field pushforward and a divergence-free representation are ordinary alternatives whose evaluation and evolution costs must also be charged fairly.

The screen establishes a sharper state contract: distinguish scalar smoke/render density, raw vector kernel source, reconstructed vorticity, and reconstructed velocity. It rejects treating coefficient/covariance deformation plus a fixed Euclidean projection as exact transport of an arbitrary previously reconstructed vorticity. It does not reject Cauchy transport of genuinely solenoidal vorticity, establish a current simulator defect, or select a new method.

No numerical or implementation task is queued. Further work would need a concrete operation on the actual carrier, a distinct mechanism beyond (3), and an accuracy/cost or creative-task reason to compare it with ordinary field transport/reconstruction. This finite result is progress toward correct problem selection; the TOG core contribution remains unestablished.
