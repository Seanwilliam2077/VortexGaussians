# Exact ordinary comparator for a planar elliptical Gaussian

The mathematical analyst independently derives these identities. They are a standard potential-kernel organization, not a claimed new method. Source access and workload limits are separate in [SOURCE_NOTES.md](SOURCE_NOTES.md). There is no floating-point qualification or timing measurement here.

Let omega(x,y)=Gamma/(2 pi a b) exp[-x²/(2a²)-y²/(2b²)], with standard deviations a>=b>0. Let J(x,y)=(-y,x), Sigma=diag(a²,b²), K_s=(Sigma+sI)^-1, v_s=K_s r and q_s=exp(-r^T K_s r/2)/sqrt(det(Sigma+sI)).

    u(r) = Gamma/(4 pi) J integral_0^infinity q_s v_s ds.
    grad u(r) = Gamma/(4 pi) J integral q_s (K_s-v_s v_s^T) ds.

The Hessian of the unrotated vector integrand has components

    q_s [v_i v_j v_k - K_ij v_k - K_ik v_j - K_jk v_i].

Thus velocity, its Jacobian and its Hessian can share the same integration work. The velocity integral converges; the potential itself has an irrelevant logarithmically divergent constant in this2D heat representation. Rotations into/out of a proper principal-axis frame give the arbitrarily oriented ellipse. This is a planar logarithmic Green function, not this repository's axisymmetric5D inverse-Laplacian model or its rendering covariance update.

## A special-function form avoids aspect truncation

For delta=a²-b²>0, let rho=b/a,

    z=(x+i y)/sqrt(2 delta),
    zeta=(rho x+i y/rho)/sqrt(2 delta),
    chi=x²/(2a²)+y²/(2b²),
    W(z)=exp(-z²) erfc(-i z).

The change of variables t=sqrt((b²+s)/(a²+s)) turns the heat integral into the exact expression

    u_y+i u_x = -i Gamma/[2 sqrt(2 pi delta)]
                  * [W(z)-exp(-chi)W(zeta)].

Its linear center limit is u_y=Gamma x/[2 pi a(a+b)] and u_x=-Gamma y/[2 pi b(a+b)]; the center curl is Gamma/(2 pi a b), as required. Its leading far-field complex velocity is Gamma/[2 pi(x+i y)]. These are analytic normalization checks, not numerical tests.

When a=b, use the isotropic expression

    u=Gamma/(2 pi) J r / |r|² * [1-exp(-|r|²/(2a²))],

with its continuous center value and stable expm1 evaluation. Close to isotropy or the center, subtracting nearly equal special-function values needs a stable limit or qualified quadrature branch. Reflections into the upper half-plane avoid gratuitous large lower-half-plane exponentials. Differentiation uses W'=-2zW+2i/sqrt(pi), with higher recurrences, but cancellation in these recurrences can degrade far-field derivatives. An exact expression is not proof of stable evaluation at all scales.

The long-axis physical distance, not merely distance in minor-axis units, controls legitimate far-field treatment. A small positive b is valid; b=0 is outside this smooth model. No fixed-cost claim follows as b/a tends to zero.

## Comparison boundary

Allow shared geometry-conditioned quadrature, stable special-function evaluation with documented fallback, and ordinary tail-aware far-field aggregation. Do not compare only against a low-order aspect expansion or recompute identical setup for one method while allowing the other to cache it. Charge geometry transforms, all required derivatives, special-function/internal quadrature work, branch/fallback costs, batching and full interaction traversal.

An isolated kernel diagnostic may measure whether ordinary implementations meet a declared accuracy target; it cannot prove a solver speedup, large-system complexity, physical convergence or TOG contribution. This exact expression does not reduce the number of interactions or handle boundaries.
