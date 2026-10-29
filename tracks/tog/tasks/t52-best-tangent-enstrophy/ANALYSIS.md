# T52 — ordinary optimal tangent in enstrophy space

This analysis uses exactly T51's single normalized curl-Gaussian with C=sI, s>0, nonzero a and zero initial center. It derives an ordinary linear least-squares projection of the exact physical vorticity derivative onto the complete existing parameter tangent. The choice of L2 vorticity is explicit: it measures instantaneous enstrophy-space derivative error, not image quality, kinetic-energy error or finite-time solution error.

## Full tangent optimization, not a restricted update

Write N for T51's exact Euler vorticity right-hand side and T_{v,b,D} for its full tangent. The objective is

\[
\min_{v,b,D=D^T}\|N-T_{v,b,D}\|_{L^2(\mathbb R^3)}^2.
\]

T51 establishes that N and the translation tangent are even, whereas the b,D contribution is odd. Even and odd functions are orthogonal in this all-space norm. Therefore the odd contribution has optimal value zero, achievable with b=D=0, without denying those degrees of freedom. Possible parameter redundancy does not change the physical minimizer.

The translation map v -> T_v is injective: if its continuous field vanishes in L2, it vanishes everywhere; its value at the center forces v parallel to a, and its remaining quadratic term then forces v=0. Its Gram matrix is consequently positive definite. The unique translation minimizer must be invariant under all rotations about a, because the target, metric and tangent problem have that symmetry. Hence v=beta a. This is an optimization/symmetry argument; imposing pointwise equality at the center would not by itself justify a restriction in an L2 fit.

Use T51's notation G=g(r), L(r)=2r^{-3} integral_0^r q^2 g(q)dq. The remaining objective is

\[
\|N-T_{\beta a}\|_2^2
=\frac{8\pi |a|^4}{15s^4}
\int_0^\infty r^6 g(r)^2[L(r)-\beta]^2\,dr.
\]

The angular constant is integral cos^2(theta)sin^2(theta)dOmega=8pi/15. Ordinary weighted least squares therefore gives

\[
\beta_*=
\frac{\int r^6g(r)^2L(r)\,dr}{\int r^6g(r)^2\,dr}.
\]

## Three dimensionless moments

Let rho=r/sqrt(s), g0=(2pi s)^(-3/2), and

\[
\ell(\rho)=\frac{L(r)}{g_0}
=\frac{2}{\rho^3}\int_0^\rho q^2e^{-q^2/2}\,dq,
\qquad \ell(0)=\frac23.
\]

Define, with all integrals over [0,infinity),

\[
J_0=\int \rho^6e^{-\rho^2}\,d\rho,
\quad J_1=\int \rho^6e^{-\rho^2}\ell(\rho)\,d\rho,
\quad J_2=\int \rho^6e^{-\rho^2}\ell(\rho)^2\,d\rho.
\]

Then beta_*=g0 J1/J0, while the center-affine update uses beta_c=2g0/3. The relative derivative residuals are

\[
E_*^2=\frac{\|N-T_*\|_2^2}{\|N\|_2^2}
=1-\frac{J_1^2}{J_0J_2},
\]

\[
E_c^2=\frac{J_2-\frac43J_1+\frac49J_0}{J_2}.
\]

The zero-derivative reference has E=1 by definition. It is a scale anchor for this metric, not a useful fluid solver. A nonzero floor here is conditional on the one-carrier tangent and the stated metric. It is not a lower bound against other representations, a finite-time error or a contribution claim.

## Closed expressions independent of quadrature

Gaussian moments immediately give J0=15 sqrt(pi)/16. Swapping the order in J1 yields

\[
J_1=2\int_0^\infty q^2e^{-q^2/2}
\left[\int_q^\infty \rho^3e^{-\rho^2}\,d\rho\right]dq
=\int_0^\infty q^2(q^2+1)e^{-3q^2/2}dq
=\frac13\sqrt{\frac{2\pi}{3}}.
\]

For J2, put A(r)=integral_0^r q^2 exp(-q^2/2)dq. Integration by parts gives

\[
A(r)=\sqrt{\pi/2}\,\operatorname{erf}(r/\sqrt2)-r e^{-r^2/2},
\qquad J_2=4\int_0^\infty e^{-r^2}A(r)^2dr.
\]

For completeness the erf-product integral needed here follows by differentiating in b:

\[
F(a,b)=\int_0^\infty e^{-r^2}\operatorname{erf}(ar)\operatorname{erf}(br)dr,
\quad
\partial_bF=\frac{a}{\sqrt\pi(1+b^2)\sqrt{1+a^2+b^2}}.
\]

With F(a,0)=0 this integrates to

\[
F(a,b)=\frac1{\sqrt\pi}\arctan\!\left(\frac{ab}{\sqrt{1+a^2+b^2}}\right).
\]

The cross term is integral_0^infinity r exp(-3r^2/2)erf(r/sqrt2)dr=1/6; the final Gaussian moment is sqrt(pi)/(8sqrt2). Expanding A^2 therefore gives

\[
\boxed{
J_0=\frac{15\sqrt\pi}{16},\qquad
J_1=\frac13\sqrt{\frac{2\pi}{3}},\qquad
J_2=\sqrt\pi\left[2\arctan\frac1{2\sqrt2}-\frac5{6\sqrt2}\right].
}
\]

These are derived constants, not a fit to numerical observations. In particular beta_*/g0=(16/45)sqrt(2/3), so an isolated isotropic update can use a fixed ordinary coefficient once this metric is chosen; a general multi-carrier fit does not inherit that constant cost or independence.

## Instantaneous scale relative to the field

Derivative-relative error should not be mistaken for relative vorticity error. To provide its time scale, define t_c=sqrt(s)/|u(0)|=3sqrt(s)/(2g0|a|), the initial center-speed traversal time of one Gaussian width. Direct Gaussian/angular integration gives

\[
\|\omega\|_2^2=g_0^2|a|^2\sqrt{s}\,\pi^{3/2},
\quad
\|N\|_2^2=\frac{8\pi}{15}g_0^4|a|^4s^{-1/2}J_2,
\]

and hence

\[
\kappa_N=t_c\frac{\|N\|_2}{\|\omega\|_2}
=\sqrt{\frac{6J_2}{5\sqrt\pi}},
\qquad \kappa_* =\kappa_N E_*,\quad \kappa_c=\kappa_N E_c.
\]

These are initial normalized derivative scales. For differentiable exact and approximate trajectories starting at this state, their initial separation has first-order coefficient ||R||/||omega||; no finite-step or time-t_c error bound follows by multiplying this coefficient by a large duration. No such trajectories are simulated here.

## What the measurement can establish

The fixed evaluation checks the three moment constants by an ordinary scalar quadrature and reports beta_*, E_*, E_c and the initial scales. It is not a solver benchmark. A better ordinary fit demonstrates why a center-only comparison would be weak; a remaining conditional floor specifies a real approximation question but does not establish a useful new algorithm. Any later method must share this ordinary coefficient/field information fairly and supply its own full costs, physical task, error requirement and finite-time evidence.
