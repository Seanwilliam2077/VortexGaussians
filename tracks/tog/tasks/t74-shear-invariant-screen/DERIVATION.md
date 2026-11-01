# T74 — a material shear has a local gain and a kinetic-energy obstruction

This is an analysis-only derivation under the committed [brief](BRIEF.md) and [numerical protocol](PROTOCOL.md). No numerical evaluation, trajectory, endpoint fit, code execution or literature claim is used below. The scientific worker, if invoked separately under that protocol, confirms these predictions rather than discovering them. The original development task and historical acceptance gates are unchanged.

The candidate is an ordinary volume-preserving deformation of the exact initial field. Its additional tangent direction improves the initial derivative fit. However, every nonconstant pure axial shift that keeps radial cross-sections fixed strictly lowers the initial Gaussian's physical kinetic energy. Thus the family does not supply a nontrivial exactly energy-conserving Euler trajectory. Approximate finite-time usefulness is not disproved by this obstruction, but neither it nor originality has been established.

## 1. Physical coordinates, norms and initial derivative

Use the original normalized widths and write

\[
x=r^2/2,\qquad q_0=Ae^{-x-z^2/2},\qquad A=3/2.
\]

The circulation measure is \(r\,dr\,dz=dx\,dz\). The physical vorticity is \(\omega_\theta=rq\), so the physical-vorticity inner product is

\[
\langle u,v\rangle_H=\int 2\pi r^3uv\,dr\,dz
=4\pi\int_0^\infty\int_{\mathbb R}xuv\,dz\,dx.
\]

These two measures must not be interchanged. The free-space potential and velocity retain T69's definitions:

\[
-\Delta_5\phi=q,\qquad
u_r=-r\phi_z,\qquad u_z=2\phi+r\phi_r,
\]
\[
F(q)=r\phi_zq_r-(2\phi+r\phi_r)q_z.
\]

At the spherical initial state, \(q_r=-rq_0\), \(q_z=-zq_0\), and \(r\phi_z=z\phi_r\). The radial terms cancel, giving the exact identity

\[
\boxed{F_0=2z\phi_0q_0.}
\]

For \(R^2=2x+z^2\), equivalent initial-potential expressions are

\[
\phi_0=\frac A2\int_1^\infty s^{-5/2}e^{-R^2/(2s)}\,ds
=A\int_0^1v^2e^{-R^2v^2/2}\,dv,
\]
\[
\phi_0(R)=A\left[
\frac{\sqrt{\pi/2}\,\operatorname{erf}(R/\sqrt2)}{R^3}
-\frac{e^{-R^2/2}}{R^2}\right]\quad(R>0),
\]
\[
\phi_0(R)=A\sum_{k=0}^\infty
\frac{(-R^2/2)^k}{k!(2k+3)},\qquad \phi_0(0)=A/3.
\]

The removable singularity in the erf expression is not a singular physical field. These are exact identities; the protocol's finite local series is a separately qualified numerical implementation.

## 2. Shear direction, orthogonality and closed gain

Consider

\[
q_{c,a}=Ae^{-x-[z-c-a(x-1)]^2/2}.
\]

At \(c=a=0\), its translation and shear derivatives are

\[
e_0=zq_0,\qquad e_1=z(x-1)q_0.
\]

For a trial shear \(z(x-c_*)q_0\), orthogonality to translation requires

\[
c_*=
\frac{\int_0^\infty x^2e^{-2x}\,dx}
{\int_0^\infty xe^{-2x}\,dx}=1.
\]

The amplitude and both width derivatives of the original Gaussian are even in \(z\), whereas \(e_0,e_1\) are odd. Thus \(e_1\) is orthogonal to the complete original single-Gaussian tangent after the translation direction has been removed; the result is not based on a deliberately restricted old tangent.

Elementary Gaussian moments give

\[
\|q_0\|_H^2=A^2\pi^{3/2},\quad
\|e_0\|_H^2=\frac{A^2\pi^{3/2}}2,\quad
\|e_1\|_H^2=\frac{A^2\pi^{3/2}}4,\quad
\langle e_0,e_1\rangle_H=0.
\]

To verify the target cross products independently, insert the heat expression for \(\phi_0\) and integrate \(x,z\) first. With \(C=4\pi A^3\sqrt{2\pi}\), the results are

\[
\langle F_0,e_0\rangle_H
=C\int_1^\infty\frac{s}{(2s+1)^{7/2}}\,ds,
\]
\[
\langle F_0,e_1\rangle_H
=-C\int_1^\infty\frac{s}{(2s+1)^{9/2}}\,ds.
\]

The two remaining integrals equal \((2/5)3^{-5/2}\) and \((8/35)3^{-7/2}\), respectively. Therefore

\[
\frac{\langle F_0,e_1\rangle_H}{\langle F_0,e_0\rangle_H}
=-\frac4{21},
\]
\[
\boxed{b_0=\frac{\langle F_0,e_0\rangle_H}{\|e_0\|_H^2}
=\frac{16A}{45}\sqrt{\frac23},\qquad
b_1=\frac{\langle F_0,e_1\rangle_H}{\|e_1\|_H^2}
=-\frac8{21}b_0.}
\]

Let \(G_0=b_0^2\|e_0\|_H^2\) denote the derivative squared norm captured by optimal translation. The shear's additional captured quantity is

\[
\boxed{G_1=b_1^2\|e_1\|_H^2=\frac{32}{441}G_0.}
\]

This is a projection gain, not a kinetic-energy gain. In particular, \(32/441\) is not the fraction of the old residual removed. Using T52's independently closed constants

\[
J_0=15\sqrt\pi/16,\quad J_1=\sqrt{2\pi/3}/3,\quad
J_2=\sqrt\pi\left[2\arctan\frac1{2\sqrt2}-\frac5{6\sqrt2}\right],
\qquad \eta_0=\frac{J_1^2}{J_0J_2},
\]

the translation and translation-plus-shear derivative-relative residual squares are

\[
1-\eta_0,\qquad 1-\left(1+\frac{32}{441}\right)\eta_0.
\]

The fraction of the remaining translation residual square removed is

\[
\frac{(32/441)\eta_0}{1-\eta_0}.
\]

These exact formulas do not replace the protocol's independent direct nonnegative residual integrations.

## 3. An omitted cubic direction and its ordinary mixture witness

Define

\[
n=(z^3-3z/2)q_0.
\]

Gaussian moments show

\[
\langle n,e_0\rangle_H=\langle n,e_1\rangle_H=0,\qquad
\|n\|_H^2/\|e_0\|_H^2=3/2.
\]

The same target integration as above gives

\[
\langle F_0,n\rangle_H=\frac32\langle F_0,e_1\rangle_H,
\quad
\frac{\langle F_0,n\rangle_H}{\langle F_0,e_0\rangle_H}=-\frac27,
\quad b_n=-\frac4{21}b_0.
\]

Consequently this direction, which the shear family omits, captures

\[
G_n=b_n^2\|n\|_H^2=\frac8{147}G_0=\frac34G_1.
\]

This comparison is between orthogonal derivative directions at one state. It is not a result about a complete solver or a comparison against an optimized two-Gaussian trajectory.

The cubic direction is also accessible to an ordinary positive two-Gaussian family. Fix \(0<\eta<1\), \(\eta\ne1/2\), and let

\[
\nu_\delta=1-\eta(1-\eta)\delta^2>0,
\]
\[
q_\delta=Ae^{-x}\nu_\delta^{-1/2}\left[
(1-\eta)e^{-(z+\eta\delta)^2/(2\nu_\delta)}
+\eta e^{-[z-(1-\eta)\delta]^2/(2\nu_\delta)}\right].
\]

This mixture has the exact initial circulation, impulse, axial centroid and axial variance. A Taylor expansion, using \(\partial_\nu q=\tfrac12\partial_c^2q\), cancels the first- and second-order split terms and yields

\[
q_\delta=q_0+
\frac{\eta(1-\eta)(1-2\eta)}6\delta^3\partial_c^3q_0
+O_H(\delta^4),
\qquad \partial_c^3q_0=(z^3-3z)q_0.
\]

Projecting the cubic term off the old translation tangent leaves precisely \(n\). A field path with \(\delta\) proportional to \(t^{1/3}\), with an ordinary translation adjustment if desired, therefore has this additional first-order field direction despite nonsmooth component coordinates at coincidence. The symmetric split \(\eta=1/2\) removes the cubic term, consistently with T69's fourth-order even direction. No finite initial displacement is required.

This is a constructive ordinary competitor direction, not a new startup algorithm, an all-Casimir-preserving mixture path, a complete tangent-cone classification or a finite-time claim.

## 4. Conditional skewness is absent from every pure-shift family

At each fixed \(x\), every state

\[
q_f=Ae^{-x-[z-c-f(x)]^2/2}
\]

has a normalized Gaussian axial conditional distribution with variance one and third central moment zero. The exact initial Euler derivative has a different property. The conditional mass derivative is zero by parity, but the conditional mean derivative is generally nonzero; it must be included when differentiating a central moment.

For \(Z\sim N(0,1)\), the correctly centered derivative is

\[
\boxed{\dot\kappa_3(x)
=2\mathbb E[(Z^4-3Z^2)\phi_0(x,Z)]
=2\mathbb E[Z^3\phi_{0,z}(x,Z)].}
\]

The second equality follows by integration by parts against the normalized Gaussian: \((z^3e^{-z^2/2})'=(3z^2-z^4)e^{-z^2/2}\). From the compact potential integral,

\[
\phi_{0,z}(x,z)=-Az\int_0^1v^4e^{-xv^2-z^2v^2/2}\,dv,
\]

and hence

\[
\boxed{\dot\kappa_3(x)
=-6A\int_0^1\frac{v^4e^{-xv^2}}{(1+v^2)^{5/2}}\,dv<0}
\]

for every finite \(x\ge0\). This proves the sign independently of the protocol's four sampled radii. Even an unrestricted radial function \(f(x)\) cannot reproduce the complete initial Euler derivative while retaining Gaussian axial conditionals. The omitted cubic direction is consequently a physical shape diagnostic, not merely a finite search artifact.

## 5. Preserved quantities and admissibility of the deformation

The meridional map \(S_f(x,z)=(x,z+f(x))\) has unit Jacobian and preserves \(x\ge0\). For every integrable observable in question, change of variables gives

\[
\int\Phi(q_f)\,dx\,dz=\int\Phi(q_0)\,dx\,dz,
\quad
\int x^k\Phi(q_f)\,dx\,dz=\int x^k\Phi(q_0)\,dx\,dz.
\]

The unweighted case contains the physical \(q\)-Casimirs. Because \(x\) is fixed, the family preserves additional weighted quantities not generally conserved by Euler. In particular,

\[
\Gamma=A\sqrt{2\pi},\qquad
I_z=2\pi\int xq\,dx\,dz=2\pi\Gamma,
\qquad \|q_f\|_H^2=A^2\pi^{3/2}.
\]

Thus physical vorticity enstrophy is artificially fixed throughout the family. The entire radial circulation marginal is fixed as well.

A simple sufficient regularity class is \(f\in C^\infty([0,\infty))\) with \(f\) and the derivatives required by an operation growing at most polynomially. It contains the proposed linear shear. The resulting \(q_f\) is positive, smooth at the axis when expressed in \(r^2\), and has finite required polynomial moments. Its Cartesian vorticity \((-X_2q_f,X_1q_f,0)\) is smooth and divergence free. Less regular shifts can still define a measurable density and the energy inequality below, but unspecified "integrability" does not imply smoothness or finite axial moments.

The chart velocity of a time-dependent pure shift has \(u_r=0\), \(u_z=\partial_tf(x)\). Any nonzero such globally defined velocity is independent of \(z\), so it does not have finite free-space kinetic energy. This does not invalidate the density as an approximation family. It does prohibit identifying the chart generator with the decaying velocity induced by that density. A prospective projection method must still compute the latter from \(-\Delta_5\phi=q_f\).

## 6. General pure-shift kinetic-energy obstruction

For a sufficiently regular free-space state, integration by parts gives the physical kinetic energy

\[
E=\frac12\int_{\mathbb R^3}|u|^2
=\pi\int r^3(|\phi_r|^2+|\phi_z|^2)\,dr\,dz
=\pi\int r^3q\phi\,dr\,dz.
\]

For example, the \(4r\phi^2\) term from expanding \(r(2\phi+r\phi_r)^2\) cancels the integrated cross term \(4r^2\phi\phi_r\). This explains why the expression uses the auxiliary five-dimensional radial measure rather than the physical circulation measure.

Extend \(q\) to \(\mathbb R^5\) by using \(r=|Y|\), \(Y\in\mathbb R^4\). Since \(|S^3|=2\pi^2\),

\[
E=\frac1{2\pi}\int_{\mathbb R^5}q(-\Delta_5)^{-1}q,
\qquad G_5(X)=\frac1{8\pi^2|X|^3}.
\]

This is a representation of physical energy; it does not assert that physical fluid volume is five dimensional.

Let \((Y,Z),(Y',Z')\) be independent standard Gaussian points in \(\mathbb R^4\times\mathbb R\), and put

\[
R^2=|Y-Y'|^2,\qquad
m=f(|Y|^2/2)-f(|Y'|^2/2).
\]

The map \((Y,Z)\mapsto(Y,Z+f(|Y|^2/2))\) also preserves five-dimensional volume, so the Green double integral for the deformed state is

\[
E(q_f)=2A^2\pi^2\mathbb E\left[
\big(R^2+(Z-Z'+m)^2\big)^{-3/2}\right].
\]

Use \(v^{-3/2}=(2/\sqrt\pi)\int_0^\infty t^{1/2}e^{-tv}\,dt\). Conditional on \(Y,Y'\), the axial difference is \(N(0,2)\), giving the positive-integrand formula

\[
\boxed{E(q_f)=4A^2\pi^{3/2}\int_0^\infty t^{1/2}
\mathbb E_{Y,Y'}\left[
\frac{e^{-tR^2}}{\sqrt{1+4t}}
\exp\!\left(-\frac{tm^2}{1+4t}\right)
\right]dt.}
\]

All exchanges here are justified by nonnegativity. The last exponential is at most one. If \(f\) is not constant almost everywhere under the radial Gaussian law \(x e^{-x}dx\), independent draws give \(m\ne0\) with positive probability, and the inequality is strict. This measure has positive density for every \(x>0\), so the condition is equivalently nonconstancy up to Lebesgue-null subsets of that half-line. Therefore

\[
\boxed{E(q_f)\le E(q_0)=A^2\pi^{3/2}/3,}
\]

with equality exactly for constant shifts up to null sets. Global axial translation has no energy effect. The formula also proves finite energy for every finite-almost-everywhere measurable shift: its positive integral is bounded by the finite initial energy. Smoothness and moment qualifications remain separate.

This closes the entire fixed-radial-cross-section pure-shift class, not only \(f=a(x-1)\). There can be no nontrivial exactly energy-conserving trajectory from \(q_0\) confined to that class. A nonzero initial shear rate is nevertheless compatible with zero *first* energy derivative: the energy decrease begins at second order. Tangent invariance alone is insufficient to integrate a physical invariant-preserving trajectory within the chosen family.

There is no contradiction with true Euler evolution. In physical volume coordinates its characteristics satisfy

\[
\dot x=-2x\phi_z,\qquad \dot z=2\phi+2x\phi_x,
\qquad \partial_x\dot x+\partial_z\dot z=0.
\]

They generally redistribute radius. Their auxiliary five-dimensional velocity divergence is instead

\[
\nabla_5\cdot u=2u_r/r=-2\phi_z,
\]

which is generally nonzero. The genuine dynamics need not stay on the additional five-dimensional rearrangement orbit or preserve the weighted Casimirs imposed by the shear. The obstruction concerns that extra constraint, not all axisymmetric flow maps.

## 7. Independent derivation of the frozen linear-shear energy ratio

For \(f(x)=a(x-1)\), set \(D=Y-Y'\) and \(S=(Y+Y')/2\). The vectors \(D\sim N(0,2I_4)\) and \(S\sim N(0,I_4/2)\) are independent, and \(m=aS\cdot D\). Conditional on \(D\), the total axial difference has variance \(2+a^2|D|^2/2\). Consequently

\[
E(a)=4A^2\pi^{3/2}\int_0^\infty t^{1/2}
\mathbb E_D\left[
\frac{e^{-tR^2}}{\sqrt{1+4t+a^2tR^2}}\right]dt.
\]

Here \(R^2\) has density \(u e^{-u/4}/16\). Substituting \(u=4w/(1+4t)\) gives

\[
E(a)=4A^2\pi^{3/2}\int_0^\infty
t^{1/2}(1+4t)^{-5/2}
\int_0^\infty\frac{we^{-w}}{
\sqrt{1+[4a^2t/(1+4t)^2]w}}\,dw\,dt.
\]

Now set \(s=\sqrt{4t/(1+4t)}\). Then

\[
t^{1/2}(1+4t)^{-5/2}dt=\frac{s^2}4ds,
\qquad \frac{4t}{(1+4t)^2}=s^2(1-s^2).
\]

At \(a=0\), the resulting outer integral is \(1/12\), confirming \(E_0=A^2\pi^{3/2}/3\). Normalization gives exactly the frozen protocol expression:

\[
\boxed{\frac{E(a)}{E_0}
=3\int_0^1s^2\int_0^\infty
\frac{we^{-w}}{\sqrt{1+a^2s^2(1-s^2)w}}\,dw\,ds.}
\]

It is even in \(a\), equals one at zero, and strictly decreases with \(|a|>0\). To check the small-amplitude coefficient, let \(c=s^2(1-s^2)\) and expand in \(a^2\). The needed moments are \(\int w^2e^{-w}=2\) and \(\int w^3e^{-w}=6\), yielding

\[
\boxed{\frac{E(a)}{E_0}
=1-\frac6{35}a^2+\frac6{77}a^4+O(a^6).}
\]

Indeed the quadratic deficit coefficient is

\[
3\int_0^1s^4(1-s^2)\,ds
=3(1/5-1/7)=6/35.
\]

The expansion is justified by a Taylor remainder bounded by an integrable polynomial in \(w\) for \(a^2\ge0\); no uniform smallness of \(a^2cw\) over the unbounded domain is assumed. Thus both the frozen ratio and its \(6/35\) limit are independently verified analytically. For a path \(a(t)=b_1t+o(t)\), this yields the state-family deficit \((E_0-E(t))/E_0=(6/35)b_1^2t^2+o(t^2)\), not a measured trajectory drift.

## 8. Ordinary alternatives, remaining costs and nonclaims

An ordinary volume-preserving deformation or characteristic-map method can include this very same shear, and ordinary least squares obtains the rates above. Ordinary positive mixtures also supply the cubic witness. Added directions and preserved Casimirs therefore do not establish an advantage over those methods. T68 has already demonstrated ordinary two-Gaussian endpoint capacity, and T70 has already removed exact coincident startup as an immediate barrier; neither issue is reopened here.

For nonzero linear shear the source exponent contains \(zr^2\) and \(r^4\). The Gaussian heat closure used in T69 no longer directly applies to this source. The induced velocity exists, but no equally cheap evaluator, weak contraction formula or complete cost bound is established here. A future method must pay for its own velocity, projection, candidate failures and validation; ordinary comparators must receive the same usable analytic information. The present Green and heat identities are tools for the screen, not a proposed heat-kernel contribution.

The conditional-skew and energy results are decisive analytic limitations of this specific representation. They are not a theorem that finite-dimensional approximations, Gaussian mixtures, volume-preserving maps or the wider research direction cannot work. They do not impose a new retrospective energy gate on earlier numerical records. They do not prove finite-time error, practical speed, broad generalization, originality or TOG readiness. The remaining question is whether a mechanism that permits the necessary radial redistribution and conditional axial deformation can establish a useful advantage over strong ordinary methods; this document supplies no such mechanism and authorizes no further implementation.
