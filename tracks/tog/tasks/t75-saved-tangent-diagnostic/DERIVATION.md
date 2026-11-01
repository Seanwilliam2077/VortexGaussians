# T75 — nested ordinary tangents at one saved T71 state

This derivation implements the mathematical scope of [T74's decision](../t74-shear-invariant-screen/DECISION.md) and the [frozen T75 protocol](PROTOCOL.md). It uses one already saved state and its recorded weight-only successor. It performs no numerical evaluation or new evolution. The protocol fixes all routes, tolerances and failure handling before the sole invocation. This is a local ordinary-method diagnostic, not a proposed solver or representation exclusion.

## 1. Exact input and coordinate convention

The designated input is `paths[1].steps[20].state` in T71's original `result.json`, at `h=1/32`, `time=5/8`. Its fields are

\[
\Gamma=3.75615008934964,\qquad \eta=0.279627593252541,
\]
\[
(s_{r1},s_{z1},z_1)=(1,1,0),\qquad
(s_{r2},s_{z2},z_2)=(0.936952772942467,0.7220788034569413,0.7689570190588).
\]

T70 `physics.py` interprets `geometry` in exactly the order `(sr, sz, z0)`, not variance coordinates. Set

\[
\rho_i=s_{ri}^2,\quad \nu_i=s_{zi}^2,\quad
N_i=\rho_i\sqrt{2\pi}\,s_{zi},\quad
g_i=\frac{e^{-r^2/(2\rho_i)-(z-z_i)^2/(2\nu_i)}}{N_i},
\]
\[
c_1=\Gamma(1-\eta),\qquad c_2=\Gamma\eta,\qquad
q=c_1g_1+c_2g_2.
\]

Here \(c_i\) is a component circulation coefficient. T70's field amplitude `A` is instead \(A_i=c_i/N_i\). Holding one of these fixed while differentiating geometry is not the same operation. The complete eight-dimensional spans agree after the amplitude directions are included, but columns, rates and conditioning depend on the convention.

The normalization is \(\int r g_i\,dr\,dz=1\). The fitting inner product remains the original physical-vorticity norm

\[
\boxed{\langle u,v\rangle_H=\int_0^\infty\int_{\mathbb R}2\pi r^3uv\,dz\,dr.}
\]

The circulation measure \(r\,dr\,dz\), physical-vorticity measure \(2\pi r^3dr\,dz\), and finite reference-scoring domain must not be interchanged.

## 2. Eight analytic columns and the nested comparison

Use coordinates \((c_i,\log s_{ri},\log s_{zi},z_i)\) for each component. Their exact field derivatives are

\[
T_{c_i}=g_i,
\]
\[
\boxed{T_{\log s_{ri}}=c_ig_i\left(-2+\frac{r^2}{\rho_i}\right),\quad
T_{\log s_{zi}}=c_ig_i\left(-1+\frac{(z-z_i)^2}{\nu_i}\right),\quad
T_{z_i}=c_ig_i\frac{z-z_i}{\nu_i}.}
\]

In raw width coordinates, divide the respective logarithmic-width column by \(s_{ri}\) or \(s_{zi}\). If peak amplitude \(A_i\) were held fixed instead, the width derivatives would omit the normalization terms \(-2\) and \(-1\); that is a different column convention and is not used here.

The two nested subspaces are

\[
W=\operatorname{span}\{g_1,g_2\},\qquad
V=\operatorname{span}\{T_{c_i},T_{\log s_{ri}},T_{\log s_{zi}},T_{z_i}:i=1,2\},
\qquad W\subset V.
\]

The original \((\Gamma,\eta)\) weight columns are \((1-\eta)g_1+\eta g_2\) and \(\Gamma(g_2-g_1)\). Their span is exactly \(W\) because \(\Gamma>0\). Infinitesimal rates convert by

\[
\dot c_1=(1-\eta)\dot\Gamma-\Gamma\dot\eta,\quad
\dot c_2=\eta\dot\Gamma+\Gamma\dot\eta,
\]
\[
\dot\Gamma=\dot c_1+\dot c_2,\qquad
\dot\eta=\frac{(1-\eta)\dot c_2-\eta\dot c_1}{\Gamma}.
\]

No future physical reference enters these spaces or the current target \(F(q)\). T70's `field` evaluator forms the velocity of the current state, retains both weighted components and all four ordered self/cross interactions, and returns

\[
F(q)=-u_rq_r-u_zq_z.
\]

The proposed diagnostic changes neither those physical equations nor the original state.

## 3. Exact rank here, numerical qualification separately

For this state both \(c_i>0\), and \(\rho_1\ne\rho_2\). The complete tangent has exact rank eight, not merely a generic expectation. Within one component its four columns span

\[
g_i\operatorname{span}\{1,r^2,z,z^2\}.
\]

Suppose \(g_1P_1(r^2,z)+g_2P_2(r^2,z)=0\), with each \(P_i\) in that polynomial span. At fixed \(z\), dividing by one positive Gaussian leaves one polynomial in \(r^2\) plus another multiplied by an exponential with a nonzero coefficient of \(r^2\), because the radial variances differ. The exponential and polynomial growth as \(r^2\to\infty\) cannot cancel unless both polynomials vanish. Varying \(z\) forces all their coefficients to vanish. Thus the eight columns are independent in \(H\), and the two weight columns are independent as well.

A computed lower rank at this particular state is therefore a failure to resolve the full ordinary tangent numerically, not evidence of a physical rank reduction. Exact independence does not promise benign conditioning.

Use positive quadrature weights and form the tall weighted design matrix rather than solving normal equations. A natural common scaling, independent of the route, is

\[
G_{jk}=\langle T_j,T_k\rangle_H,\qquad d_j=\sqrt{G_{jj}},\qquad
B_{nj}=\sqrt{W_n}\,T_j(r_n,z_n)/d_j,\quad
y_n=\sqrt{W_n}\,F(r_n,z_n).
\]

The analytic all-space Gram matrix below supplies these positive column scales. A protocol using per-route scales must explicitly transform comparisons back to one common scale; singular spectra from different conventions are not directly interchangeable.

For \(B=U\Sigma V^T\), solve the ordinary least-squares problem with the frozen relative singular cutoff \(10^{-10}\sigma_{\max}\). A result is qualified as the complete comparison only if both models retain their expected ranks, two and eight, and satisfy the separately stronger condition

\[
\sigma_{\min}/\sigma_{\max}\ge10^{-6}.
\]

Report the complete normalized spectrum, retained ranks and condition numbers. If qualification fails, retain the failure and stop; do not lower the cutoff, remove columns, choose a more favorable route or call a truncated result the complete tangent. Forming \(B^TB\) squares the condition number, so its eigenvalues are useful reported diagnostics and checks, not a reason to replace the tall SVD solve by a Gram inversion.

If the SVD returns normalized-column coefficients \(\beta_j\), the actual parameter rates are \(a_j=\beta_j/d_j\). The fitted field is \(v=\sum_jT_ja_j\). Physical fitted fields and residuals should be compared across routes; coefficient agreement alone can be misleading for correlated columns. Column normalization removes arbitrary multiplicative unit scales, but does not make conditioning invariant under arbitrary changes that mix columns.

The frozen rank-resolution check additionally divides the Frobenius norm of the discrepancy between the common-scaled analytic Gram and \(B^TB\) by the smallest measured squared singular value, requiring a ratio at most \(10^{-3}\). Quadrature agreement is empirical error evidence, not a rigorous Weyl bound unless the perturbation itself is rigorously bounded.

## 4. Independent analytic Gram from Gaussian product moments

Write each column as \(T_j=g_iP_j(u,z)\), where \(u=r^2\), and

\[
P_{c_i}=1,\quad
P_{\log s_{ri}}=c_i(-2+u/\rho_i),\quad
P_{\log s_{zi}}=c_i[-1+(z-z_i)^2/\nu_i],\quad
P_{z_i}=c_i(z-z_i)/\nu_i.
\]

For a pair of component labels \(i,k\), let

\[
\rho=(\rho_i^{-1}+\rho_k^{-1})^{-1},\qquad
\nu=(\nu_i^{-1}+\nu_k^{-1})^{-1},\qquad
\mu=\nu(z_i/\nu_i+z_k/\nu_k).
\]

T70's exact-real `Physics.gram(geometry_i, geometry_k)` expression is

\[
K_{ik}=\frac{4\pi\rho^2\sqrt{2\pi\nu}}{N_iN_k}
\exp\!\left[-\frac{(z_i-z_k)^2}{2(\nu_i+\nu_k)}\right].
\]

Under its normalized product \(H\) measure, \(U=r^2\) and \(Z=z\) are independent, with

\[
U\sim\operatorname{Gamma}(\text{shape}=2,\text{scale}=2\rho),\qquad
Z\sim N(\mu,\nu).
\]

In particular,

\[
\boxed{\mathbb E[U^m]=(m+1)!(2\rho)^m,\qquad
G_{j\ell}=K_{ik}\mathbb E[P_j(U,Z)P_\ell(U,Z)].}
\]

Only radial powers through two and axial powers through four are required. The axial raw moments are

\[
1,\quad\mu,\quad\mu^2+\nu,\quad\mu^3+3\mu\nu,\quad
\mu^4+6\mu^2\nu+3\nu^2.
\]

Centered shifted moments can be used to avoid unnecessary subtraction. This gives every Gram entry without a spatial rule or finite differences of geometry. Its binary64 implementation still requires direct-rule agreement and positivity/symmetry checks; an algebraic closed form is not a floating-point certificate.

## 5. Direct residual decomposition and route checks

In exact arithmetic write

\[
v_W=P_WF,\quad v_V=P_VF,\quad r_W=F-v_W,\quad r_V=F-v_V,\quad d=v_V-v_W.
\]

Nesting gives the useful decomposition

\[
\boxed{r_W=r_V+d,\qquad \langle r_V,d\rangle_H=0,\qquad
\|r_W\|_H^2=\|r_V\|_H^2+\|d\|_H^2.}
\]

Report the two residual squares normalized by \(\|F\|_H^2\), the additional capture \(\|d\|_H^2/\|F\|_H^2\), and its fraction of the remaining weight-only residual \(\|d\|_H^2/\|r_W\|_H^2\). The last fraction is undefined if the denominator is numerically indistinguishable from zero; do not force it to a finite value. Use direct positive-weight sums of \((F-v)^2\) and \((v_V-v_W)^2\), rather than accepting subtraction of two large fitted norms. Check normal residual correlations with the normalized columns and the Pythagorean identity.

The proposed five frozen routes are

- D12, spatial orders 64 by 128, heat order 128;
- D12, spatial orders 64 by 128, heat order 256;
- D12, spatial orders 96 by 192, heat order 128;
- D12, spatial orders 96 by 192, heat order 256;
- D8, spatial orders 96 by 192, heat order 256.

Here D12 means \([0,12]\times[-12,12]\) and D8 means \([0,8]\times[-8,8]\). The largest tensor grid has 18,432 points, equal to T70's existing flat-field point cap. These are evaluation routes of the same saved state, not extra physical cases. Holding space fixed isolates heat-rule sensitivity; holding heat fixed isolates spatial-rule sensitivity; comparing the two boxes supplies an empirical domain check. The frozen primary route is D12 with 96 by 192 spatial nodes and heat order 256.

Freeze primary-route fitted rates and directly reevaluate those same fields and residuals on the confirmation routes. Independently refitted confirmation solutions may also be reported if predeclared, but they cannot replace the held-coefficient check or silently become the selected answer. Check all numerical integrals and design entries for finite values, positive diagonal norms and positive quadrature weights. Do not clip negative cancellation results, alter rank decisions or refit a new state after a failed qualification.

The analytic Gaussian Gram is all-space. The direct \(F\) norm and residual integrations are finite-box approximations to the intended all-space \(H\) problem. D8/D12 and rule agreement provide empirical confirmation, not rigorous exterior or continuum error bounds. Count all five evaluations, decomposition work and checks in the complete scientific child cost.

## 6. Relation to the recorded weight-only successor

The saved successor at `paths[1].steps[21]` is at \(t=21/32\), with identical geometry and

\[
\Gamma_+=3.752273925278773,\qquad \eta_+=0.2936337006283067.
\]

Because geometry is unchanged, its exact field secant is

\[
v_{\rm saved}=\frac{q_+-q}{h}
=\sum_i\frac{c_{i,+}-c_i}{h}g_i\in W.
\]

Use the exact component coefficients formed separately from each stored \((\Gamma,\eta)\), rather than applying an infinitesimal coordinate Jacobian to their finite increments. The latter omits a finite product term.

For fixed geometry, minimizing the Euler-target field error has the exact change of variables

\[
\min_{c_i+h\dot c_i\ge0}
\left\|q+hF-\sum_i(c_i+h\dot c_i)g_i\right\|_H^2
=h^2\min_{c_i+h\dot c_i\ge0}\left\|F-\sum_i\dot c_ig_i\right\|_H^2.
\]

Thus, if the ordinary unconstrained weight projection has positive proposed coefficients at this \(h\), it also solves the fixed-geometry positive Euler-target problem in exact arithmetic. Comparing it with the stored secant can separate a weight-subproblem discrepancy from the available additional geometry directions. This is a local algebraic comparison, not a new candidate search or step. If the unconstrained proposed coefficients are not positive, the finite-step positivity constraint must be reported; it does not invalidate the infinitesimal weight tangent at an interior state.

## 7. Positivity, conservation and limits of inference

Both saved component coefficients and both widths are strictly positive. Every finite tangent rate therefore admits a sufficiently short feasible parameter curve: choose logarithmic widths and keep the coefficient perturbations smaller than their positive margins. The local tangent uses unrestricted rate signs. This does not assert that a linear extrapolation at \(h=1/32\) is feasible or accurate. Large dimensionless rates, such as \(h\dot c_i/c_i\), \(h\dot{\log s}_{ri}\), \(h\dot{\log s}_{zi}\) or center changes measured in current widths, are relevant diagnostics of this limitation if prospectively included; they are not an authorization to advance a trajectory.

The comparison is unconstrained, consistently with T71's free-scale projector. It must not silently add conservation constraints to one or both spaces. Under the stated coordinates,

\[
\dot\Gamma=\sum_i\dot c_i,\qquad
\dot I_z=2\pi\sum_i\rho_i\left(\dot c_i+2c_i\dot{\log s}_{ri}\right).
\]

These may be reported as instantaneous diagnostics. Orthogonal projection in \(H\) does not automatically preserve circulation, impulse, energy or the full \(q\)-Casimirs. Axial centroid and covariance are not Euler invariants. A lower derivative residual is not a conservation theorem.

A resolved large additional geometry capture establishes that this saved state has useful ordinary infinitesimal geometry directions beyond weights alone. It supports a local geometry-search limitation but does not establish a useful improvement at the frozen finite search step, explain the entire T71 time sensitivity, or prove that changing its search would pass the physical task. A small additional capture identifies only the ordinary local Jacobian residual here. It does not exclude nonlinear finite-step projection, a different future path, boundary birth or nonsmooth splitting elsewhere, and cannot establish insufficiency of the two-Gaussian family.

Neither result establishes a new method, full-window accuracy, a quality-cost advantage, generalization or a TOG score change. Qualification failure is retained as numerically unresolved and ends this task; it is not evidence for a new representation. No new trajectory, extra saved state, half-neighbor search, endpoint fit or physical scene follows automatically.
