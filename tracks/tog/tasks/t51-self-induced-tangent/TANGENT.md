# T51 — the existing isotropic carrier is not exactly self-closed

This is one hand-derived membership argument in exact arithmetic, using only the existing T49 carrier and reconstruction. There is no numerical or symbolic-software evaluation. The conclusion concerns exact instantaneous closure, not the accuracy or convergence of a finite-particle approximation.

## State, field and the complete tangent

Work in R^3 without forcing or viscosity. Translation invariance lets the initial center be zero without constraining its time derivative. Put s=sigma^2>0 and define

\[
G(x)=g(r)=(2\pi s)^{-3/2}e^{-r^2/(2s)},\quad
r=|x|,\quad a\ne0,\qquad
m=aG,\quad \omega=\frac{G}{s}(a\times x).
\]

The prescribed state manifold is the full existing family with arbitrary SPD C. Only the initial covariance is restricted to C=sI. Let

\[
v=\dot\mu\in\mathbb R^3,\qquad
b=\dot a\in\mathbb R^3,\qquad
D=\dot C=D^T\in\mathbb R^{3\times3}.
\]

Every symmetric D is an admissible tangent at an SPD matrix: sI+tD stays SPD for sufficiently small |t|. No trace-free, isotropic or center-gradient constraint is imposed on D, and no constraint is imposed on b or v in advance. The normalized Gaussian derivative is

\[
\frac{\dot G}{G}
=\frac{x\cdot v}{s}-\frac{\operatorname{tr}D}{2s}
+\frac{x^TDx}{2s^2}.
\]

Differentiating omega=G[a cross C^{-1}(x-mu)] at this state gives the complete physical tangent

\[
\boxed{
\begin{aligned}
T_{v,b,D}(x)=G\bigg[&\frac{b\times x}{s}
-\frac{a\times v}{s}-\frac{a\times Dx}{s^2}\\
&+\frac{a\times x}{s}
\left(\frac{x\cdot v}{s}-\frac{\operatorname{tr}D}{2s}
+\frac{x^TDx}{2s^2}\right)\bigg].
\end{aligned}}
\]

The v terms are even under x -> -x; the b,D terms are odd. This parity split retains all twelve parameter derivatives, whether or not their tangent images are linearly independent.

## Exact self-induced velocity and nonlinear derivative

Use T49's ordinary free-space reconstruction

\[
u=aG+\nabla(a\cdot\nabla H),\qquad -\Delta H=G,
\]

with the decaying Newton potential H. It is radial and regular at r=0. Integrating its radial Poisson equation gives, for r>0,

\[
H'(r)=-\frac{1}{r^2}\int_0^r q^2 g(q)\,dq.
\]

The usual 4pi factors cancel here: g is the three-dimensional density, and its total mass is 4pi times the radial integral. Define

\[
B(r)=\frac{H'(r)}r,\quad
h(r)=\frac{B'(r)}r,\quad f(r)=g(r)+B(r),\quad
\tau=a\cdot x,\quad W=a\times x,\quad k(r)=g(r)/s.
\]

Then the exact velocity and vorticity are

\[
u=f(r)a+h(r)\tau x,\qquad \omega=k(r)W.
\]

For r>0, u dot x=tau(f+h r^2), a cross u=h tau W, while W dot x=W dot a=0. Consequently

\[
(u\cdot\nabla)\omega
=\tau\left[\frac{k'}r(f+h r^2)+kh\right]W,
\qquad
(\omega\cdot\nabla)u=kh\tau W.
\]

The two kh terms cancel in the inviscid physical right-hand side. Since k'=-rk/s and f+h r^2=g+H''=-2H'/r, define

\[
L(r)=-\frac{2H'(r)}r
=\frac{2}{r^3}\int_0^r q^2 g(q)\,dq.
\]

The exact self-induced nonlinear vorticity derivative is therefore

\[
\boxed{
N(x)=-(u\cdot\nabla)\omega+(\omega\cdot\nabla)u
=\frac{G(x)}{s^2}L(r)(a\cdot x)(a\times x).
}
\]

All expressions extend smoothly to the center. In particular,

\[
L(0)=\frac23 g(0),\qquad N(0)=0.
\]

The scalar L is positive and not constant. Indeed, for r>0,

\[
L'(r)=\frac{2g(r)-3L(r)}r<0,
\]

because g(q)>g(r) for 0<=q<r gives
3 integral_0^r q^2 g(q)dq > r^3 g(r).
Normalization also gives L(r)~1/(2pi r^3) as r -> infinity. These are exact monotonicity/asymptotic statements, not sampled values or finite numerical error bounds.

## Membership contradiction with every tangent freedom available

Suppose N=T_{v,b,D} everywhere. N is even, since G,L are radial and both tau and W are odd. Taking even and odd parts of this equality forces the odd b,D contribution to vanish as a function. There is no need to assume b=D=0 or solve its possible parameter redundancy; it cannot supply any part of the even target.

Thus equality would require

\[
N(x)=G(x)\left[-\frac{a\times v}{s}
+\frac{(x\cdot v)(a\times x)}{s^2}\right].
\]

At x=0, N(0)=0 and G(0)>0 imply a cross v=0. Because a is nonzero, v=beta a for a single spatially constant scalar beta. Equality away from the center then requires

\[
\big[L(r)-\beta\big](a\cdot x)(a\times x)=0
\quad\text{for every }x.
\]

For every radius r>0 one can choose x neither parallel nor perpendicular to a, so both factors are nonzero. Hence beta would have to equal L(r) for every r>0, contradicting its strict decrease. This excludes **all** v,b and symmetric D, not merely a center-affine parameter update.

**Result:** for each s>0 and nonzero a, the exact self-induced inviscid physical derivative of this isotropic curl-Gaussian is outside the full tangent of the existing single-carrier Gaussian family. Therefore no differentiable path inside that family can solve the exact self-consistent Euler vorticity equation through this state. This last implication is only the necessary tangent condition for an exact family solution.

## Explicit residual and decision limits

An ordinary center-affine update would use u(0)=L(0)a, grad u(0)=0, hence v=L(0)a, b=0, D=0 in this inviscid instance. Its exact instantaneous physical residual is

\[
\boxed{
R(x)=N(x)-T_{L(0)a,0,0}(x)
=\frac{G(x)}{s^2}\big[L(r)-L(0)\big]
(a\cdot x)(a\times x).
}
\]

It vanishes on the axis, equatorial plane and center, but is nonzero for all other x. Thus checking the center, or those symmetry sets alone, would miss the failure. The all-tangent contradiction above is stronger than this one update's residual and does not rely on that update being the best approximation. No norm, best-fit parameter choice, finite-time error, accuracy threshold or computational cost is evaluated here.

This is a vorticity residual and is unaffected by adding a gradient to the impulse potential. It is distinct from T50's gauge-reinitialization nonclosure. It is also distinct from a time-discretization defect: even exact integration of a parameter ODE cannot make this finite manifold exactly invariant through the stated state. The result does not quantify how well a projected tangent, additional carriers, refinement or another approximation could represent the physical evolution, and no such repair is constructed or tested in this task.

The zero-coefficient state is excluded by the protocol and would give the trivial zero flow. No conclusion about exact closure of other families, exact solutions outside this initial instance, practical usefulness, novelty or TOG readiness follows. T49's prescribed-affine/heat result remains valid in its original scope.
