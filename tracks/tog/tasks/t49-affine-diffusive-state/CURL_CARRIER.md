# T49 curl-Gaussian carrier: exact prescribed-flow closure and ordinary reconstruction

This note derives one carrier and its velocity reconstruction in R^3, in exact arithmetic. It adds no numerical experiment, source acquisition, implementation or alternate family. The parent is recording the separate source assessment of the ordinary magnetization formulation u=P m. The curl/vector-potential construction here is treated as ordinary; the derivation is not a novelty claim.

## Definition and normalization

Let C be SPD and let

\[
G_C(z)=(2\pi)^{-3/2}\det(C)^{-1/2}
\exp[-z^TC^{-1}z/2],\qquad z=x-\mu.
\]

The Gaussian has integral one. For a spatially constant covector a, define

\[
m(x)=aG_C(x-\mu),\qquad
\omega=\nabla\times m=\nabla G_C\times a
=G_C\,[a\times C^{-1}(x-\mu)].
\]

This vorticity is smooth, Gaussian-localized and exactly divergence-free. It is a derivative Gaussian, not a constant vector times a Gaussian. Its integral and hydrodynamic impulse are

\[
\int_{\mathbb R^3}\omega\,dx=0,
\qquad
I=\frac12\int_{\mathbb R^3}x\times\omega\,dx=a.
\]

All these integrals converge absolutely. For the impulse, the identity

`x cross (grad G cross a) = grad G (x dot a) - a (x dot grad G)`

and integration by parts give -a+3a=2a before the factor one half. Translation of mu contributes nothing because total vorticity is zero. The equality I=a depends on the normalized Gaussian; an unnormalized Gaussian would require its mass factor. Zero integrated vorticity does not, by itself, make a localized solenoidal representation physically defective.

## Determinant-one affine transport

For an invertible affine map x'=Fx+b with det(F)=1, set

\[
\mu'=F\mu+b,\qquad C'=FCF^T,\qquad a'=F^{-T}a.
\]

The normalized Gaussian obeys G_C'(x'-mu')=G_C(x-mu), and its gradient transforms by F^(-T). The cross-product identity

\[
(F^{-T}v)\times(F^{-T}w)=F(v\times w)
\quad\text{when }\det F=1
\]

therefore gives

\[
\omega'(Fx+b)=F\omega(x).
\]

This is the required incompressible affine vorticity push. The covector transformation of a is essential. The result does not follow by transforming a as an ordinary contravariant vector. The impulse transforms consistently as I'=F^(-T)I; it is not generally invariant under an imposed strain.

## Joint affine advection, stretching and diffusion

Consider the specified velocity field U(x,t)=A(t)x+b(t), with trace A=0, and constant scalar viscosity nu>=0. The target equation is the prescribed-field linear vorticity equation

\[
\partial_t\omega+(U\cdot\nabla)\omega
=A\omega+\nu\Delta\omega.
\]

The carrier closes exactly under

\[
\boxed{
\dot\mu=A\mu+b,\qquad
\dot C=AC+CA^T+2\nu I,\qquad
\dot a=-A^Ta.
}
\]

To check this, the normalized Gaussian with these mu/C equations solves scalar affine advection-diffusion. If g=grad G and D_t=partial_t+U dot grad, then

\[
(D_t-\nu\Delta)g=-A^Tg.
\]

Since a is spatially constant,

\[
(D_t-\nu\Delta)(g\times a)
=(-A^Tg)\times a+g\times(-A^Ta)
=A(g\times a),
\]

where the last equality uses trace A=0. This proves the stated closure, including the interaction between strain and diffusion.

For completeness, let F solve Fdot=A(t)F with F(0)=I. Then

\[
a(t)=F(t)^{-T}a(0),
\]

\[
\mu(t)=F(t)\mu(0)+\int_0^tF(t)F(s)^{-1}b(s)\,ds,
\]

\[
C(t)=F(t)\left[C(0)+2\nu\int_0^t
F(s)^{-1}F(s)^{-T}\,ds\right]F(t)^T.
\]

Thus positive definiteness persists for finite invertible F and SPD initial C. For pure heat, C(t)=C(0)+2 nu t I while mu and a remain fixed. For simultaneous general strain and diffusion, replacing the covariance solution by F C(0) F^T+2 nu t I is not generally valid. An arbitrary time-dependent A still requires solving the matrix/time integrals accurately; finite parameter closure is not free exact time integration, nor a guarantee that an arbitrary discrete covariance update stays SPD.

The impulse follows adot=-A^T a and is conserved under pure heat. This is an imposed-background model, not a proof of impulse conservation for an isolated self-consistent fluid. In particular, prescribing A and b independently of the reconstructed velocity is part of the result's scope.

## Velocity is an ordinary projected vector potential

Use the Fourier convention

\[
\widehat f(k)=\int f(x)e^{-ik\cdot x}\,dx,
\qquad f(x)=(2\pi)^{-3}\int\widehat f(k)e^{ik\cdot x}\,dk.
\]

Suppressing the center phase,

\[
\widehat\omega=ik\times a\,e^{-k^TCk/2}.
\]

The free-space Biot-Savart reconstruction is

\[
\widehat u=
\frac{ik\times\widehat\omega}{|k|^2}
=\left(I-\frac{kk^T}{|k|^2}\right)a\,e^{-k^TCk/2},
\qquad u=P(aG_C).
\]

This is the ordinary Helmholtz projection of m=aG_C. Define the finite Newton potential

\[
H_C(z)=\int_0^\infty G_{C+2tI}(z)\,dt,
\qquad -\Delta H_C=G_C.
\]

Then

\[
u=aG_C+\nabla(a\cdot\nabla H_C).
\]

Its divergence vanishes and its curl equals omega. No divergent scalar potential is introduced here: the scalar Fourier factor exp(-k^TCk/2)/|k|^2 is locally integrable at k=0 in three dimensions.

For one-dimensional quadrature, let s=2t and, for each s>=0, set

\[
D=C+sI,\quad K=D^{-1},\quad v=Kz,\quad \Phi=G_D(z).
\]

The exact velocity is

\[
\boxed{
u(z)=aG_C(z)+\frac12\int_0^\infty
\Phi\,[v(a\cdot v)-Ka]\,ds.
}
\]

For a fixed spatial direction h, put w=Kh, v0=C^(-1)z. Its directional Jacobian is

\[
\boxed{
\begin{aligned}
(\nabla u)h={}&-aG_C(z)(v_0\cdot h)\\
&+\frac12\int_0^\infty\Phi\big[
w(a\cdot v)+v(a\cdot w)
-(v\cdot h)\{v(a\cdot v)-Ka\}
\big]\,ds.
\end{aligned}
}
\]

Three coordinate choices for h produce the full spatial Jacobian at fixed carrier parameters. This is an ordinary Gaussian heat integral involving a Hessian Newton potential and its derivative, not a new reconstruction algorithm established by the notation.

## Exact center value and the old self convention

At the source center, the exact velocity is

\[
\boxed{
u(\mu)=\left[
G_C(0)I-\frac12\int_0^\infty
G_{C+sI}(0)(C+sI)^{-1}\,ds
\right]a.
}
\]

The matrix in brackets is positive definite: its Fourier quadratic form in any nonzero vector h is the positive integral of

`(|h|^2 - (k dot h)^2/|k|^2) * exp(-k^T C k/2)`

with the inverse-transform normalization. Consequently the center velocity is nonzero for every nonzero a, not merely for a generic orientation. In the isotropic case C=sigma^2 I, symmetry and -Delta H=G give

\[
\boxed{u(\mu)=\tfrac23 G_C(0)a.}
\]

The velocity is even about mu and its spatial Jacobian at mu is zero; omega is odd and vanishes at mu. Thus the zero self-velocity convention of a different, ordinary raw vector-Gaussian vorticity source cannot be copied into this carrier's reconstruction. Omitting this center contribution would change the field being evaluated. This is a contract difference, not a newly diagnosed bug in the existing VPM code.

Nor does retaining the exact center value prove that evolving the center under its own velocity preserves this Gaussian carrier. The exact closure above uses the prescribed affine U, while a carrier's own reconstructed u is generally non-affine. A local affine approximation, coupled dynamics, remeshing or time integrator would need separate analysis and evidence.

## Localization, representation and comparison scope

The vorticity is localized as a Gaussian derivative. Its reconstructed velocity is nonlocal: at large |z|, its leading term is the ordinary dipole field

\[
u(z)\sim\frac{3n(n\cdot a)-a}{4\pi|z|^3},
\qquad n=z/|z|,
\]

and its velocity gradient has algebraic order |z|^(-4). A Gaussian cutoff on omega does not authorize the same cutoff on u.

This carrier remains within the same transport/representation operation, but it is not the same source field as T48. Here omega-hat is O(|k|) at low frequency, omega has zero integral and is Gaussian-localized, and u=P(aG_C). T48 projected a raw vector Gaussian by a different covariance-dependent symbol; a single such nonzero carrier generally has directional O(1) low-frequency vorticity and a nonlocal vorticity tail. Even at the same center/covariance, the parity and self-velocity contracts differ. The two cannot be substituted into an equal-source-count accuracy or performance comparison as though they represent the same input field.

Any future same-field reconstruction reference for T49 must evaluate the complete u=P(aG_C) formula, including its local term, integral and center value. Ordinary raw anisotropic Gaussian Biot-Savart, and T48's different source, can inform structural or cost comparisons but are not same-field accuracy references. No representation-error, equal-N, expressivity or task-value advantage has been established here.

## Costs and remaining qualification

A finite covariance/vector state does not make query evaluation constant work at a prescribed accuracy. Preparation includes carrier state updates, SPD handling, factorization or an appropriately oriented eigenbasis, and transformations. The closed parameter ODE still has a time-integration cost for arbitrary A(t). Shared preparation may be reused when the model permits it; an ordinary comparator must receive the same opportunity.

Each source/query requires a direct Gaussian term plus the one-dimensional improper integral. At every integration node, a diagonalized covariance still requires shifted inverses, determinant normalization, Gaussian evaluation and vector contractions; the full Jacobian adds its own contractions. The number of nodes, tail handling, error estimation, refinement and failures must all be counted. For fixed C/z/a, the large-s velocity integrand is O(s^(-5/2)) and the Jacobian integrand O(s^(-7/2)); these asymptotics are not a certified finite-cutoff rule. Small eigenvalues, anisotropy, cancellation between the local and integral terms, and requested error in u/J affect practical qualification.

Direct evaluation over S sources and Q queries therefore scales with the sum of actual integration-node counts over all S times Q pairs, in addition to preparation, accumulation, storage and output. No fixed node bound, spatial acceleration, runtime advantage or optimized implementation has been supplied. The same-field ordinary projection/integral is already available mathematically; its existence neither proves it fast enough nor establishes a new hard bottleneck.

The completed result is exact closure under a specified affine advection-diffusion equation and an ordinary same-field reconstruction formula. It provides no self-consistent flow proof, scene-level capability evidence, numerical validation, novelty finding or TOG contribution by itself.
