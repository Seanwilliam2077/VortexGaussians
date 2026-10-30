# T67 — ordinary two-Gaussian endpoint variable projection

This analytic contract follows the [T66 decision](../t66-saved-product-diagnostic/DECISION.md). It performs no array read, integral evaluation, root solve or optimization. The model and moment conventions extend [T62](../t62-joint-oracle-contract/DERIVATION.md); the positive, discontinuous, zero-extended T66 product is evidence about a larger family, not this mixture's exterior definition. Everything below is a real-arithmetic statement unless explicitly identified as a later numerical check. It is ordinary finite-dimensional least squares, not a new evolution mechanism.

## 1. Family, normalization and complete moments

Let \(r\ge0,z\in\mathbb R\), with two positive widths per component and arbitrary finite axial centers. Set

\[
N_l=s_{rl}^2\sqrt{2\pi}s_{zl},\qquad
g_l=\frac{\exp[-r^2/(2s_{rl}^2)-(z-z_l)^2/(2s_{zl}^2)]}{N_l},
\quad q=\Gamma f_\eta,
\quad f_\eta=(1-\eta)g_1+\eta g_2,
\]
\[
\Gamma\ge0,\qquad 0\le\eta\le1.
\]

The two elementary integrals \(\int_0^\infty r e^{-r^2/(2s_r^2)}dr=s_r^2\) and \(\int_\mathbb R e^{-(z-z_l)^2/(2s_z^2)}dz=\sqrt{2\pi}s_z\) give \(\int r g_l\,dr\,dz=1\). Thus the full-space circulation is exactly \(\Gamma\). No circulation equality is imposed on the fit. The endpoints \(\eta=0,1\) remain admitted; there is no positive lower mixture-weight cutoff.

The inherited centroid/covariance are moments of the \((r,z)\) coordinates under circulation measure \(rq\,dr\,dz/\Gamma\). They are not the Cartesian centroid of an axisymmetric three-dimensional scalar density. Write

\[
\kappa=\sqrt{\pi/2},\qquad \gamma=(4-\pi)/2,
\quad \mu_l=(\kappa s_{rl},z_l)^T,
\quad \Sigma_l=\operatorname{diag}(\gamma s_{rl}^2,s_{zl}^2).
\]

The component raw second-moment matrix is

\[
Q_l=\begin{pmatrix}
2s_{rl}^2&\kappa s_{rl}z_l\\
\kappa s_{rl}z_l&s_{zl}^2+z_l^2
\end{pmatrix}=\Sigma_l+\mu_l\mu_l^T.
\]

For \(d=\mu_2-\mu_1\), the mixture has

\[
\mu(\eta)=\mu_1+\eta d,\qquad Q(\eta)=(1-\eta)Q_1+\eta Q_2,
\]
\[
\boxed{\Sigma(\eta)=(1-\eta)\Sigma_1+\eta\Sigma_2+\eta(1-\eta)dd^T.}
\]

The between-component term must not be omitted. In particular its off-diagonal entry can have either sign. Full-space axial impulse is

\[
I_z=\pi\int r^3q\,dr\,dz
=2\pi\Gamma[(1-\eta)s_{r1}^2+\eta s_{r2}^2].
\]

For completeness, define for every component pair

\[
\rho_{r,lk}^{-2}=s_{rl}^{-2}+s_{rk}^{-2},\quad
\rho_{z,lk}^{-2}=s_{zl}^{-2}+s_{zk}^{-2},\quad
\zeta_{lk}=\rho_{z,lk}^{2}(z_l/s_{zl}^2+z_k/s_{zk}^2),
\]
\[
e_{lk}=\exp\left[-\frac{(z_l-z_k)^2}{2(s_{zl}^2+s_{zk}^2)}\right].
\]

Then, with \(w=(1-\eta,\eta)^T\), the inherited squared norms are

\[
\int 2\pi r q^2=\Gamma^2 w^TK^{(1)}w,
\quad K^{(1)}_{lk}=\frac{2\pi e_{lk}\rho_{r,lk}^2\sqrt{2\pi}\rho_{z,lk}}{N_lN_k},
\]
\[
\|\omega\|_2^2=\int 2\pi r^3q^2=\Gamma^2 w^TK^{(3)}w,
\quad K^{(3)}_{lk}=\frac{4\pi e_{lk}\rho_{r,lk}^4\sqrt{2\pi}\rho_{z,lk}}{N_lN_k},
\]

because \(\omega_\theta=rq\). These are full-space formulas, without a factor of one half. Circulation and impulse discrepancies are diagnostics, not added acceptance gates. The zero-amplitude field has no normalized physical moments, but the nonzero positive-reference least-squares optimum below has \(\Gamma_*>0\).

## 2. The complete feasible weight set for fixed geometry

Use the original S256 endpoint mean \(\mu_{z,R}\), covariance \(C_R\), and unchanged normalization \(D_0=1.0882203729522952\) from the frozen T63 metadata. Both the axial-centroid gate and normalized covariance gate have tolerance \(\epsilon=.10\). Only the axial centroid is gated.

The axial gate is

\[
|z_1+\eta(z_2-z_1)-\mu_{z,R}|\le\epsilon.
\]

If \(z_2=z_1\), it either admits every weight or none. Otherwise the two boundary values give a closed interval, intersected with \([0,1]\). This may be empty or a singleton.

Put \(H_0=\Sigma_1-C_R\), \(H_1=\Sigma_2-\Sigma_1+dd^T\), and \(H_2=-dd^T\). The covariance condition is

\[
P(\eta)=\|H_0+\eta H_1+\eta^2H_2\|_F^2-(\epsilon D_0)^2\le0.
\]

For \(A:B=\sum_{ij}A_{ij}B_{ij}\), its coefficients from constant through fourth degree are

\[
\begin{aligned}
p_0&=H_0:H_0-(\epsilon D_0)^2,&p_1&=2H_0:H_1,\\
p_2&=H_1:H_1+2H_0:H_2,&p_3&=2H_1:H_2,&p_4&=H_2:H_2.
\end{aligned}
\]

The Frobenius convention counts both off-diagonal entries. Intersecting \(P\le0\) with the axial interval gives a compact set \(\mathcal F\) comprising closed intervals and possibly isolated points. A repeated polynomial root can be an isolated feasible weight even when both adjacent open intervals are infeasible. It must not be discarded merely because no sign change occurs. Retain all admissible boundary roots and singleton axial intersections. A constant polynomial admits the whole axial interval if nonpositive, otherwise none; the identically zero polynomial has the same all-interval interpretation. Lower-degree and repeated-root cases use their actual degree, not an assumption of four distinct roots.

These statements specify mathematical feasibility. Finding and qualifying floating-point roots, nearly repeated roots and signs belongs to the separately frozen numerical protocol. An uncertain root classification cannot silently become an empty feasible set or a family exclusion.

## 3. Eliminate scale and minimize over all feasible weights

The original field metric uses \(D8=[0,8]\times[-8,8]\) and \(\langle u,v\rangle_D=\int_{D8}2\pi r^3uv\). Define

\[
C=\langle q_R,q_R\rangle_D>0,\quad b_l=\langle q_R,g_l\rangle_D,
\quad M_{lk}=\langle g_l,g_k\rangle_D.
\]

The qualified nonnegative, nonzero reference and strictly positive components imply \(b_l>0\). Set

\[
B(\eta)=\beta_0+\beta_1\eta,\quad \beta_0=b_1,\quad\beta_1=b_2-b_1,
\]
\[
M(\eta)=m_0+m_1\eta+m_2\eta^2,
\quad m_0=M_{11},\quad m_1=2(M_{12}-M_{11}),\quad
m_2=M_{11}-2M_{12}+M_{22}.
\]

For \(\eta\in[0,1]\), \(B,M>0\), including identical components. Completing the square gives

\[
\|q_R-\Gamma f_\eta\|_D^2
=M(\Gamma-B/M)^2+C-B^2/M,
\qquad \boxed{\Gamma_*=B/M.}
\]

The amplitude normal equation is \(\langle q_R-\Gamma_*f_\eta,f_\eta\rangle_D=B-\Gamma_*M=0\). This is orthogonality to the fixed mixture shape, not automatically to each component separately under active weight constraints. The full-space normalized moment gates do not depend on \(\Gamma>0\), so eliminating scale does not remove a joint-feasible solution. The field optimum for fixed geometry maximizes \(J(\eta)=B^2/M\) on the complete \(\mathcal F\), with relative squared error \((C-J)/C\). Its derivative is

\[
J'(\eta)=\frac{B(\eta)}{M(\eta)^2}
\left[A_0+A_1\eta\right],
\quad A_0=2\beta_1m_0-\beta_0m_1,
\quad A_1=\beta_1m_1-2\beta_0m_2.
\]

Consequently the complete real-arithmetic candidate set consists of every feasible interval endpoint, every isolated feasible point, and \(-A_0/A_1\) if \(A_1\ne0\) and it lies in the interior of a feasible interval. If \(A_1=0,A_0\ne0\), there is no interior stationary point. If both vanish, \(J\) is constant on \([0,1]\); a deterministic feasible boundary representative suffices. A stationary point coinciding with an endpoint need not be evaluated twice. Compactness and continuity establish attainment whenever \(\mathcal F\ne\varnothing\).

Do not invert the two-component Gram matrix: it is singular for identical components although \(M(\eta)>0\) and the reduction remains valid. Likewise component collapse at \(\eta=0\) or 1 is ordinary single-Gaussian behavior, not a failure. No formula here proves global optimality over the six geometric variables or validates a floating-point root implementation.

## 4. Finite-box cross terms and the unchanged reference

For the saved cell reconstruction, retain the annular center \(r_{c,i}\) and axial midpoint \(z_{c,j}\):

\[
q_R=q_{ij}+p_{ij}(r-r_{c,i})+t_{ij}(z-z_{c,j}),
\quad p_{ij}=qr_{ij},\quad t_{ij}=qz_{ij}.
\]

There is no bilinear reference coefficient. Replacing \(r_c\) by a geometric midpoint changes the reference. Define finite-interval integrals

\[
R_n(l,u;s)=\int_l^u r^n e^{-r^2/(2s^2)}dr,
\quad Z_n(l,u;\zeta,s)=\int_l^u z^n e^{-(z-\zeta)^2/(2s^2)}dz.
\]

Using each component's widths/center and each cell's endpoints,

\[
b_l=\frac{2\pi}{N_l}\sum_{ij}\left[
q_{ij}R_{3,i}Z_{0,j}
+p_{ij}(R_{4,i}-r_{c,i}R_{3,i})Z_{0,j}
+t_{ij}R_{3,i}(Z_{1,j}-z_{c,j}Z_{0,j})\right].
\]

Equivalently the first term has coefficient \(q_{ij}-p_{ij}r_{c,i}-t_{ij}z_{c,j}\), followed by \(p_{ij}R_4Z_0+t_{ij}R_3Z_1\). Gaussian product completion gives

\[
\boxed{M_{lk}=\frac{2\pi e_{lk}}{N_lN_k}
R_3(0,8;\rho_{r,lk})Z_0(-8,8;\zeta_{lk},\rho_{z,lk}).}
\]

Finite-box circulation and impulse follow by replacing the component radial power with 1 and 3 respectively:

\[
\Gamma_D=\Gamma\sum_l\frac{w_l}{N_l}R_1Z_0,
\qquad I_{z,D}=\pi\Gamma\sum_l\frac{w_l}{N_l}R_3Z_0.
\]

These finite-domain diagnostics are not substituted for the full-space model moments in section 1. The model has Gaussian tails, not T66's declared zero exterior. The exact primitive recurrences in T62 explain these expressions; they are not a license to accept cancellation-prone special-function arithmetic without qualification.

## 5. Numerical and cost implications for the later protocol

Fixed positive tensor rules can evaluate the same contractions: use component values at the common radial/axial nodes, centered reference moments, and products of component values for all three Gram entries. This makes \(b,M,C\) one consistent discrete inner product. For an 8-by-6 primary rule, two components need at most \(2(8n_r+6n_z)\) scalar exponentials per uncached geometry; the reference cross contractions still cost \(O(2n_rn_z)\). Three Gram pairs cost additional one-dimensional products/reductions. Solving the weight subproblem is small scalar work but its roots, branch checks and rejected proposals must all be counted.

The reference norm is polynomial and admits the inherited 3-by-2 exact-real integration; a Gaussian residual is not polynomial. Subtraction \(C-B^2/M\) alone cannot qualify its field score, and a negative computed result must not be clipped. The later protocol must independently sum nonnegative squared differences at the unchanged selected tuple with the original primary and confirmation rules, retaining their predeclared tolerances. It must also calibrate the unchanged T63 single-Gaussian control: \(\eta=0\) and \(\Gamma=A s_r^2\sqrt{2\pi}s_z\) reproduce that saved tuple. Do not refit its amplitude or count its control evaluation as a fresh success.

Search and selection use S256 only. Exactly the selected geometry, weight and amplitude then face S128, the original three gates and the .001 held-candidate field-score sensitivity test. The six-dimensional outer domain, starts, ordering, ties, work cap and numerical root qualifications must be fixed in the protocol before any run. The moment gates alone do **not** bound all component geometries uniformly as a weight approaches zero; any finite outer box is an explicit coverage restriction, not a derived description of the entire two-component family.

A later qualified witness establishes only compact endpoint capacity. A bounded miss, uncertain root classification, or reference-sensitive result cannot exclude the family, justify another component, or establish a new causal solver. This document authorizes no numerical invocation.
