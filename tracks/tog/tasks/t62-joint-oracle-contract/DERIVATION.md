# T62 — joint capacity of one axisymmetric curl-Gaussian

This is an analytic contract following [T61's decision](../t61-saved-output-qualification/DECISION.md), not a fit or a new evolution method. No array, Gaussian integral or optimizer was evaluated here. The endpoint is \(t=1\): the other four saved times already have qualifying ordinary Gaussian witnesses. Combining a new terminal witness with them establishes only representability at those sampled times, not a continuous physical trajectory.

## Family, measure and original moment gates

Use

\[
q_G(r,z)=A f(r,z),\qquad
f=\exp\left[-\frac{r^2}{2s_r^2}-\frac{(z-z_0)^2}{2s_z^2}\right],
\quad A,s_r,s_z>0.
\]

The physical vorticity is \(\omega_\theta=rq\). Thus its squared three-dimensional L2 difference on \(D8=[0,8]\times[-8,8]\) uses \(W(r)=2\pi r^3\), exactly as [T60 measurement](../t60-full-window-gaussian-screen/measurement.py). Reference \(q_R\) remains the saved T56 piecewise-linear reconstruction, not a new interpolant.

As in T60, model centroid/covariance are **full-space** moments under normalized \(rq_G\,dr\,dz\); reference moments are the saved finite-box moments. Write \(\gamma=(4-\pi)/2\). The model mean and covariance are

\[
\mu_G=(\sqrt{\pi/2}\,s_r,z_0),\qquad
C_G=\operatorname{diag}(\gamma s_r^2,s_z^2).
\]

Only the **axial** centroid has an original acceptance gate. A radial-centroid difference may be reported, but cannot become a new veto.

Let the endpoint S256 reference have mean \(\mu_z\), covariance \(C_R=\bigl(\begin{smallmatrix}a&b\\b&d\end{smallmatrix}\bigr)\), and let \(D_0=\|C_R(0)\|_F\), the same original initial S256 normalization. Put \(x=\gamma s_r^2,y=s_z^2\). The exact joint moment region is

\[
|z_0-\mu_z|\le .1,\qquad
(x-a)^2+(y-d)^2\le\rho^2,
\quad \rho^2=(.1D_0)^2-2b^2,\quad x,y>0.
\]

The unavoidable normalized covariance error is \(\sqrt2|b|/D_0\). A value **strictly above** .1 excludes this family; equality can still admit \(x=a,y=d\). The saved endpoint scalars are

```
a  = 0.42605219413657314
b  = -0.07305360087353913
d  = 1.0359696982488587
D0 = 1.0882203729522952
```

They imply \(2b^2<(.1D_0)^2\), so this exclusion does not apply. Also \(a>.1D_0\ge\rho\) and \(d>.1D_0\ge\rho\). Consequently

\[
\frac{a-\rho}{\gamma}\le s_r^2\le\frac{a+\rho}{\gamma},\qquad
d-\rho\le s_z^2\le d+\rho
\]

have strictly positive lower bounds. Together with the axial interval this is a compact geometry domain; no arbitrary minimum width is needed. A convenient search coordinate is \(x=a+\rho u,y=d+\rho v,z_0=\mu_z+.1w\), with \(u^2+v^2\le1,|w|\le1\). These positivity conclusions are specific to the saved scalars; in general a disk reaching zero width would require separate treatment.

The first ordinary candidate should be **moment-matched geometry** \(x=a,y=d,z_0=\mu_z\). Its axial error is zero and its covariance error is exactly the off-diagonal lower bound. This cheaply supplies an admissible geometry, not a guarantee of field accuracy. A field failure there does not prove that another admissible geometry fails.

## Eliminate free amplitude, not a conservation equality

For each admissible geometry define

\[
B=\int_{D8}Wq_Rf,\quad M=\int_{D8}Wf^2,\quad
C=\int_{D8}Wq_R^2>0.
\]

The reference is nonnegative and nonzero; \(f>0\), hence \(B,M>0\). Completing the square gives

\[
\|Af-q_R\|_W^2=M(A-B/M)^2+C-B^2/M,
\qquad A_*=B/M,
\quad E_*^2=1-\frac{B^2}{CM}.
\]

Amplitude affects neither moment constraint. The field gate is \(E_*\le .10\); use the squared form only with the same nonnegative-error semantics. Continuity and positive \(M\) on the compact geometry domain ensure an attained optimum, but do not make an ordinary search globally certified.

There is deliberately **no circulation equality**. Imposing one would change \(A_*\) and narrow the tested family. Report the analytic full-space quantities

\[
\Gamma_G=A s_r^2\sqrt{2\pi}\,s_z,\qquad
I_{z,G}=2\pi s_r^2\Gamma_G,\qquad
\|\omega_G\|_2^2=\pi^{3/2}A^2s_r^4s_z.
\]

Their discrepancies are informative, not additional gates. The freedom makes this a generous offline capacity test, not a conservative solver.

## Exact cell contractions for the existing reconstruction

For cell \(i,j\), use the stored quantities \(q_{ij},p_{ij}=qr_{ij},t_{ij}=qz_{ij}\), radial annular centroid

\[
r_{c,i}=\frac{2(r_+^3-r_-^3)}{3(r_+^2-r_-^2)},
\]

and axial midpoint \(z_{c,j}\). [T56 evaluate_saved](../t56-coupled-reference/reference.py) defines

\[
q_R=q_{ij}+p_{ij}(r-r_{c,i})+t_{ij}(z-z_{c,j}).
\]

Replacing \(r_c\) by the geometric midpoint would change the reference. Define finite-interval moments

\[
R_n(l,u;s)=\int_l^u r^n e^{-r^2/(2s^2)}dr,\quad
Z_n(l,u;z_0,s)=\int_l^u z^n e^{-(z-z_0)^2/(2s^2)}dz.
\]

Suppressing their cell bounds, the cross term is exactly

\[
B=2\pi\sum_{ij}\left[
(q_{ij}-p_{ij}r_{c,i}-t_{ij}z_{c,j})R_3 Z_0
+p_{ij}R_4 Z_0+t_{ij}R_3 Z_1\right].
\]

Equivalently use the centered form

\[
2\pi\sum_{ij}\left[q_{ij}R_3Z_0+
p_{ij}(R_4-r_{c,i}R_3)Z_0+
t_{ij}R_3(Z_1-z_{c,j}Z_0)\right].
\]

Here radial moments use \(s_r\), axial moments \(z_0,s_z\). The full-box squared Gaussian norm is

\[
M=2\pi R_3(0,8;s_r/\sqrt2)Z_0(-8,8;z_0,s_z/\sqrt2).
\]

Finite-D8 circulation is \(A R_1(0,8;s_r)Z_0(-8,8;z_0,s_z)\); its squared vorticity norm is \(A^2M\). Distinguish these from the full-space quantities above.

For \(E_s(x)=e^{-x^2/(2s^2)}\),

\[
R_0=s\sqrt{\pi/2}\,[\operatorname{erf}(u/(\sqrt2s))-\operatorname{erf}(l/(\sqrt2s))],
\quad R_1=s^2[E_s(l)-E_s(u)],
\]
\[
R_n=s^2[l^{n-1}E_s(l)-u^{n-1}E_s(u)]+(n-1)s^2R_{n-2}.
\]

The recurrence applies for \(n\ge2\); only orders through four are needed. Shift \(l,u\) by \(z_0\) to obtain \(Z_0\), and

\[
Z_1=z_0Z_0+s_z^2[E_{s_z}(l-z_0)-E_{s_z}(u-z_0)].
\]

The reference norm \(C\) is independent of the fit. Its cell integrand is polynomial of degree at most five in \(r\) and two in \(z\); the existing 3-by-2 Gaussian rule integrates that polynomial exactly in real arithmetic. Preserve the saved value and qualify its reconstruction before search.

Separable moments require \(O(n_r+n_z)\) special-function work per geometry; the three cell contractions cost \(O(n_rn_z)\). Row-block accumulation avoids allocating a new Gaussian sample volume. Count all setup, loaded reference arrays, contractions, optimizer calls and final confirmations; cheap moment construction does not make the whole objective \(O(n_r+n_z)\).

## Concrete first evaluator: the original fixed quadrature, factorized

The exact recurrences explain the continuous objective; implementing them is unnecessary for the first finite test. Same-side tail subtraction needs math.erfc, nearby exponent differences need math.expm1, and high-order moment recurrences can still cancel. No analytic-primitive implementation, adaptive quadrature or new SciPy dependency is selected.

Instead replace each cell moment by its **fixed 8-point radial / 6-point axial Gaussian sum**. For example, with the original mapped nodes and positive integration weights,
\[
\widehat R_{n,i}=\sum_{\ell=1}^{8}w^r_{i\ell}r_{i\ell}^n
e^{-r_{i\ell}^2/(2s_r^2)},\qquad
\widehat Z_{n,j}=\sum_{m=1}^{6}w^z_{jm}z_{jm}^n
e^{-(z_{jm}-z_0)^2/(2s_z^2)}.
\]
Use the same cell contraction for \(B_8\), and squared Gaussian values for \(M_8\). This is algebraically the **same tensor-product primary rule** as direct 8-by-6 evaluation, not a new approximation rule. Its \(C_8=C\) in real arithmetic because both rules integrate the reference polynomial exactly. The quadrature-optimal amplitude is \(A_8=B_8/M_8\), not an assertion that finite quadrature equals the continuous \(A_*\).

Positive quadrature weights preserve the discrete least-squares identity and Cauchy–Schwarz inequality in real arithmetic. Use centered one-dimensional sums for \(\widehat R_4-r_c\widehat R_3\) and \(\widehat Z_1-z_c\widehat Z_0\), avoiding subtraction of nearly equal moment totals. NumPy exponentials/contractions and the already available fixed Gaussian rules suffice. Count \(8n_r+6n_z\) exponential evaluations per geometry, all moment sums and the \(O(n_rn_z)\) contractions; no result is cost-free because it is factorized.

Require finite positive \(B_8,M_8,C,A_8\). A negative computed \(C-B_8^2/M_8\), inconsistent reference denominator or exceeded arithmetic allowance is a qualification failure; do not clip silently. Independently compute the selected tuple's residual directly as nonnegative sample contributions with **8-by-6 primary** and **16-by-12 confirmation**. The contracted and direct primary relative scores must agree within the predeclared absolute \(10^{-9}\); the original primary/confirmation difference remains \(\le10^{-6}\). Neither rule may replace an inconvenient primary outcome.

The old fixed model \(A=1.5,s_r=s_z=1,z_0=c\) supplies the saved endpoint score check. Keep **that fixed amplitude**, not \(A_8\), when comparing with T60. It is a numerical control although its covariance fails the joint endpoint gate. Hold the selected tuple \((A,s_r,s_z,z_0)\), including amplitude, fixed when scoring S128, with the same original \(D_0\). S128 cannot select or refit parameters. Rule agreement and arithmetic agreement are empirical qualifications, not a formal continuous-field certificate.

## What the endpoint decision can establish

Test moment-matched geometry first; if its optimally scaled output passes all frozen score and moment checks, stop with a constructive witness. Otherwise only the already budgeted ordinary constrained search is allowed. A later joint-feasible witness plus the four existing witnesses demonstrates sampled capacity. It neither supplies causal dynamics nor proves that the tested trajectory's error was exclusively a closure defect.

A local search miss is unresolved. A valid family-wide lower bound could exclude this scoped family; an unconstrained global field minimum above .10 would also suffice. Conversely, a field optimum violating a moment gate does not exclude another joint-feasible point. No result here is an impossibility statement for an unrestricted twelve-parameter carrier, mixtures, or another task. Finite search/confirmation budgets and stop rules belong to the separately frozen endpoint test; this derivation authorizes no execution.
