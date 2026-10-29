# T48 — the affine orbit of a projected Gaussian carrier

This is an exact continuous-field calculation on R³. It extends the state distinction in T47; it is not a numerical result, a new Euler solver, or a novelty claim. The construction is the volume-preserving Piola/Cauchy pushforward of an ordinary projected isotropic Gaussian. No scientific execution, external source acquisition or implementation was performed for this derivation.

## State and exact affine closure

Use the Fourier convention grad -> i k and a normalized Gaussian G_Sigma, where Sigma is symmetric positive definite. For k != 0 define

```text
Q_Sigma(k) = I - Sigma k k^T / (k^T Sigma k),
omega_hat(k) = Q_Sigma(k) c exp(-k^T Sigma k/2) exp(-i k^T mu).
```

Q_Sigma is idempotent and k^T Q_Sigma=0. For Sigma=sigma² I it is the usual Euclidean Helmholtz projector P, so the initial field is exactly P(Gamma G_(sigma² I)), with c=Gamma. For anisotropic Sigma it is generally an oblique Euclidean projection, orthogonal in the Sigma^(-1) metric.

Apply the common affine map x -> H x+b, with det H=1, using vector transport omega'(x)=H omega(H^(-1)(x-b)). Set q=H^T k. Direct multiplication gives

```text
H Q_Sigma(q) = Q_(H Sigma H^T)(k) H.
```

The Gaussian exponent and center phase transform by the same substitution. Therefore the field family is exactly closed with only

```text
Sigma' = H Sigma H^T,      c' = H c,      mu' = H mu+b.
```

Repeated common affine maps compose exactly. Starting from the isotropic carrier and a map F gives Sigma=sigma² F F^T and c=F Gamma, as proposed. No unrecorded rotation or separate affine-history matrix is needed to determine this field or its next common affine pushforward. A sum of such carriers is also closed under the same common map, by linearity.

The normalization has no missing Jacobian: det H=1, and G_(H Sigma H^T)(H z)=G_Sigma(z). In particular det Sigma is invariant; an isotropic ancestor has det Sigma=sigma^6. Also c^T Sigma^(-1)c is invariant. These are state identities, not claims that kinetic energy, enstrophy or the Euclidean norm of c is conserved.

## Explicit real-space field

Write z=x-mu, r²=z^T Sigma^(-1)z, and define the smooth potential

```text
h_Sigma(z) = erf(r/sqrt(2)) / [4 pi sqrt(det Sigma) r],
```

with its continuous value at r=0. Its Fourier transform is exp(-k^T Sigma k/2)/(k^T Sigma k), equivalently

```text
-div(Sigma grad h_Sigma) = G_Sigma.
```

Then the exact carrier is

```text
omega(z) = c G_Sigma(z) + Sigma [Hess h_Sigma(z)] c.
```

The Hessian is an ordinary radial Hessian in the whitened coordinate y=Sigma^(-1/2)z. If h_0(r)=erf(r/sqrt(2))/(4 pi r),

```text
Hess_y h_0 = (h_0'/r) I + [(h_0''-h_0'/r)/r²] y y^T,
Hess_z h_Sigma = (det Sigma)^(-1/2)
                 Sigma^(-1/2) [Hess_y h_0] Sigma^(-1/2).
```

These formulas have smooth limits at the center, where omega(mu)=(2/3)G_Sigma(0)c. The apparent divisions by r are not physical singularities. Taking divergence of the displayed field gives c dot grad G_Sigma minus the same quantity, so it is solenoidal directly in real space.

This supplies a direct pointwise vorticity evaluator using fixed-dimensional matrix arithmetic and radial special functions. It does not require a mandatory grid or global elliptic solve. Velocity and velocity-gradient reconstruction remain separate evaluations that must be provided and costed; no particular implementation or cost advantage is established here.

## Tail, coefficient meaning and gauge

At large r the leading term is

```text
omega(z) = [3 z (z^T Sigma^(-1)c)/r^5 - c/r^3]
           / [4 pi sqrt(det Sigma)]
           + exponentially decaying terms.
```

For fixed positive-definite Sigma this is a physical-distance O(|z|^(-3)) tail. Thus the field is not a localized Gaussian vector blob, despite its finite state. A nonzero carrier is not absolutely L1-integrable. The coefficient c is the integral of the normalized raw source c G_Sigma; it is not an ordinary absolutely convergent integral of the projected vorticity. Assigning a value to the Fourier multiplier at k=0 does not remove the direction-dependent limit there. Conditional/principal-value or domain-dependent zero-mode conventions require their own specification.

The smooth field is L2. Its Euclidean Biot–Savart velocity is also L2: near k=0 the bounded vorticity multiplier gives a velocity multiplier at most O(1/|k|), which is square integrable in three dimensions; Gaussian decay controls high frequencies. Finite enstrophy/kinetic energy in this mathematical sense does not make the evolution self-consistent or establish numerical accuracy. Exact compact support and Gaussian-tail neighbor rejection do not follow; truncation needs a separate error and divergence account.

For a general raw field, Q_Sigma annihilates Sigma grad psi. Under the common map this gauge becomes (H Sigma H^T) grad[psi(H^(-1)(x-b))], so changing the projection metric with Sigma transports the gauge consistently. This differs from T47's fixed Euclidean projection after raw-source transport. Within one fixed carrier, a nonzero constant c does not represent a pure gauge: at any nonzero k perpendicular to c, Q_Sigma(k)c=c. These statements do not assert an arbitrary exact gauge freedom in a finite constant-vector Gaussian dictionary.

## Limits of this state closure

Closure means exact transport under a prescribed common affine map. It does not say that this map is generated by the carrier's reconstructed velocity or solves Euler. Independently assigning different maps H_i to different carriers keeps each resulting term solenoidal, but does not automatically describe one physical flow map transporting their overlapping global tails. Local affine approximations to a non-affine fluid flow need their own consistency and error analysis.

The single Sigma serves both as Gaussian envelope and projection metric. This coupling also limits ordinary viscosity/core spreading. For the heat equation with diffusivity nu and elapsed time s, exact diffusion gives

```text
exp(s nu Delta) omega_hat(k)
  = Q_Sigma(k)c exp[-k^T(Sigma+2 nu s I)k/2] exp(-i k^T mu).
```

Changing the carrier's single Sigma to Sigma+2 nu s I would also change Q_Sigma, which heat diffusion does not do. Thus the family is not generically closed under this operation for anisotropic Sigma. Isotropic Sigma is a special case because Q_Sigma=P for every isotropic scale; zero diffusion and the zero field are trivial exceptions. This is a limitation of the present state, not a proposal for another state family or an attribution of a measured failure to the existing sigma update.

For N known carriers, parameter updates take O(N) fixed-dimensional work. Direct evaluation at Q query points takes O(NQ) carrier interactions before any separately justified acceleration. Evaluating their global tails, reconstructing velocity and its gradient, obtaining the deformation, and handling boundaries remain part of the full task. The algebra supplies an exact finite-state affine carrier and exposes its nonlocality and diffusion boundary; it does not establish a distinct graphics method, an advantageous cost/accuracy regime, or a numerical queue.
