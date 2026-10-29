# T48 velocity reconstruction: an ordinary one-dimensional heat integral

This is a real-arithmetic derivation for one fixed carrier in free space R^3. No source acquisition, numerical or symbolic-computation execution, implementation, timing or solver validation was performed. The parent independently derived the same one-dimensional formula and supplied it as a cross-check; the factors, signs and directional Jacobian below were then checked against the derivative heat-integral construction. This is a collaborative algebra check, not an independent experimental reproduction or novelty claim.

## Convention and carrier

Use the Fourier convention

\[
\widehat f(k)=\int_{\mathbb R^3}f(x)e^{-ik\cdot x}\,dx,
\qquad
f(x)=(2\pi)^{-3}\int_{\mathbb R^3}\widehat f(k)e^{ik\cdot x}\,dk.
\]

Let the source center be mu, set z=x-mu, and hold the SPD covariance Sigma and vector parameter c fixed during spatial differentiation. The center contributes the usual Fourier phase. Suppressing that phase, the proposed carrier is, for k nonzero,

\[
\widehat\omega(k)=
\left[I-\frac{\Sigma k k^T}{k^T\Sigma k}\right]c
e^{-k^T\Sigma k/2},
\qquad
\widehat u(k)=\frac{ik\times\widehat\omega(k)}{|k|^2}.
\]

Write p=|k|^2 and r=k^T Sigma k. Then

\[
\widehat u(k)=
\frac{i(k\times c)}{p}e^{-r/2}
-\frac{i(k\times\Sigma k)(k\cdot c)}{pr}e^{-r/2}.
\]

The first term is exactly the ordinary Biot-Savart reconstruction of the raw anisotropic vector Gaussian c times N(0,Sigma). The second is the extra term from the specified carrier. Neither term implies a self-consistent time-dependent flow solver.

## Derivative heat integrals, with the infrared issue explicit

For SPD C, define the normalized Gaussian

\[
\Phi_C(z)=(2\pi)^{-3/2}\det(C)^{-1/2}
\exp[-z^T C^{-1}z/2].
\]

The identities 1/p=integral_0^infinity exp(-tp) dt and 1/r=integral_0^infinity exp(-sr) ds give

\[
u_0(z)=\int_0^\infty \nabla\Phi_{\Sigma+2tI}(z)\times c\,dt,
\]

\[
u_1(z)=\int_0^\infty\!\int_0^\infty
\nabla\times\left[\Sigma\nabla(c\cdot\nabla)
\Phi_{(1+2s)\Sigma+2tI}(z)\right] \, dt\,ds,
\qquad u=u_0+u_1.
\]

The second expression uses third spatial derivatives; its directional spatial Jacobian uses fourth derivatives. For fixed SPD Sigma these derivative integrals converge absolutely. They can therefore define u and its Jacobian directly.

In contrast, the naked double integral of Phi, corresponding formally to the scalar symbol exp(-r/2)/(pr), diverges at low frequency in three dimensions. It must not be presented as a finite scalar potential without a subtraction or other distributional convention. One possible subtraction is Phi_C(z)-Phi_C(0); the derivatives used above are unchanged. No divergent scalar potential is needed for this derivation.

## Reducing the double integral to one dimension

In u1, set

\[
a=1+2s,\qquad b=2t/a,\qquad
C=\Sigma+bI,\qquad K=C^{-1}.
\]

Then a ranges from 1 to infinity, b from 0 to infinity, the Gaussian covariance is aC, and

\[
ds\,dt=\frac{a}{4}\,da\,db.
\]

For each b define

\[
v=Kz,\quad q=\tfrac12 z^T Kz,\quad
N=(2\pi)^{-3/2}\det(C)^{-1/2},
\]

and the scalar functions

\[
J_p(q)=\int_1^\infty a^{-p}e^{-q/a}\,da
=\int_0^1 y^{p-2}e^{-qy}\,dy,
\qquad p>1.
\]

Thus Jp(0)=1/(p-1). For positive q, it also equals q^(1-p) times the lower incomplete gamma function gamma(p-1,q). The needed half-integer functions can be expressed using

\[
J_{3/2}(q)=\frac{\sqrt\pi\,\mathrm{erf}(\sqrt q)}{\sqrt q},
\qquad
J_{p+1}(q)=\frac{(p-1)J_p(q)-e^{-q}}{q},
\qquad
J'_p(q)=-J_{p+1}(q).
\]

These formulas are identities, not a recommended floating-point implementation near q=0, where the recurrence subtracts nearly equal values. A convergent local series is

\[
J_p(q)=\sum_{n=0}^\infty
\frac{(-q)^n}{n!\,(p-1+n)}.
\]

In particular, J5/2(0)=2/3, J7/2(0)=2/5, and J9/2(0)=2/7.

The third derivative of Phi_aC consists of a cubic product of v and the three permutations of K times v. Multiplication by the Jacobian a/4 and integration over a give their respective factors J7/2 and J5/2. Contracting with the cross product, Sigma and c yields the following two vectors:

\[
D=v\times\Sigma v=v\times z,
\]

\[
E=(Kc)\times\Sigma v+v\times\Sigma Kc
=(Kc)\times z+v\times c.
\]

The simplified equalities use Sigma K=I-bK. Hence the exact velocity is the single integral

\[
\boxed{
u(z)=\frac14\int_0^\infty N
\left[
-2e^{-q}(v\times c)
+EJ_{5/2}(q)
-D(c\cdot v)J_{7/2}(q)
\right] \, db .
}
\]

The raw-Gaussian comparator is precisely the first term of this same integral:

\[
u_0(z)=\frac12\int_0^\infty N e^{-q}(c\times v)\,db.
\]

The displayed algebra does not prove a general elementary closed form. It does establish that a two-dimensional numerical quadrature is unnecessary: one ordinary improper integral plus half-integer scalar functions suffices.

## Explicit directional spatial Jacobian

For a fixed query-space direction h, set

\[
w=Kh,\quad \ell=v\cdot h,\quad
s_c=c\cdot v,\quad s_h=c\cdot w,
\]

\[
D_h=w\times z+v\times h,\qquad
E_h=(Kc)\times h+w\times c.
\]

Since the directional derivative of q is ell, differentiating the preceding integral gives

\[
\boxed{
\begin{aligned}
(\nabla u)h=\frac14\int_0^\infty N\big[&
-2e^{-q}\{w\times c-\ell(v\times c)\}\\
&+E_hJ_{5/2}(q)-\ell E J_{7/2}(q)\\
&-(D_hs_c+Ds_h)J_{7/2}(q)
+\ell D s_c J_{9/2}(q)
\big] \, db .
\end{aligned}
}
\]

Evaluating this for the three coordinate directions produces the full Jacobian, whose columns are spatial derivatives of velocity. This is differentiation at fixed carrier parameters; it is not a material derivative through changing Sigma, c or source position. Velocity and Jacobian can share the same per-node C/K/N/v/q and scalar-function preparation if a quadrature scheme is later implemented.

## Limits and normalization

For Sigma=lambda I, D=0 and E=0 identically. The extra integral vanishes, leaving ordinary isotropic Gaussian Biot-Savart and its usual erf expression. In this limit the solenoidal source projection changes the raw vorticity representation, but its correction is parallel to k and therefore disappears under k cross in velocity reconstruction. The correction must not be interpreted as a universal positive extra cost when this special case can be recognized analytically.

For all fixed SPD Sigma, the integrands have no lower-end singularity at b=0. At z=0, velocity is zero by oddness; the Jacobian has a finite limit. At large b and fixed Sigma/z/c, the ordinary velocity/Jacobian integrands decay at least as b^(-5/2), and the correction integrands as b^(-7/2). These are asymptotic descriptions, not certified finite-cutoff bounds or a demonstrated quadrature rule. The algebraically equivalent D/E expressions can have different floating-point cancellation behavior; near-isotropic cancellation and small-q recurrence stability require explicit treatment in any implementation.

The carrier is not a localized raw Gaussian merely because its Fourier symbol contains a Gaussian factor. For nonzero c, the directional limit of the source symbol as k approaches zero is generally direction-dependent. Thus c cannot automatically be identified with an absolutely convergent integral of physical vorticity. The solenoidal completion has a nonlocal, generically algebraic vorticity tail (order |z|^(-3)); a Gaussian-only spatial cutoff would omit that part. This nonlocality already occurs for the ordinary isotropic projected Gaussian and is not a newly discovered defect. A det-one affine push and the source-symbol constraint alone do not supply physical circulation, energy, or full solver validation.

## Complete cost and the fair ordinary comparator

The Fourier multiplier being a 3-by-3 expression does not make spatial evaluation fixed cost. A future implementation must account for all of the following:

- **Carrier preparation:** validate SPD covariance, construct its factorization/eigendecomposition, and transform source/vector data. A right-handed eigenbasis allows ordinary cross products in diagonal coordinates. Repeated shared covariances can reuse this preparation, equally for the raw anisotropic comparator. Changing affine state requires the corresponding updates.
- **Every source/query pair:** form the displacement, transform it, obtain integration bounds or an improper-domain map, and evaluate the integrand at all selected nodes. In a diagonal frame, each node still needs three shifted eigenvalue inverses, determinant normalization, vector operations, exp(-q), and the needed J functions. A full Jacobian adds its directional contractions; it is not supplied for free by the velocity.
- **Accuracy and integration:** choose and charge all quadrature nodes, tail control, refinement/error assessment, stopping logic and failures. Node counts can depend on covariance conditioning, query location, strength, and the required absolute/relative errors in u and J. SPD alone gives no uniform practical bound on this work as the smallest eigenvalue approaches zero or anisotropy grows. A per-source error budget must also support the final accumulated-field tolerance.
- **Accumulation and output:** sum all source contributions, transform results back and account for retained state, caching, memory and output. With S sources, Q queries and variable node counts n_ij, direct integration costs scale with the sum of n_ij over S times Q pairs, plus preparation and accumulation. No acceleration or amortization beyond explicitly shared preparation has been established here.

Ordinary raw anisotropic Gaussian Biot-Savart already has the one-dimensional heat integral u0 above and its differentiated Jacobian. The proposed carrier adds scalar functions and vector contractions within the same dimensional integration class. It may require more or fewer nodes under a particular error controller, but no such behavior has been measured or bounded here. Comparing only against the browser's scalar-width closed/LUT kernel would also change the source model; that is not evidence that a new reconstruction method is needed.

The result is an exact integral reduction, not a new algorithm claim. It supplies no evidence of a distinct hard bottleneck, a useful speedup, a self-consistent flow model, or a TOG contribution. Any later computation would need a separately frozen accuracy/cost question and the complete two-term one-dimensional formula above as its same-field accuracy reference. The ordinary raw anisotropic Gaussian term u0 alone represents a different source field and serves here only as a cost/structure comparison. This derivation alone does not authorize an implementation or experiment.
