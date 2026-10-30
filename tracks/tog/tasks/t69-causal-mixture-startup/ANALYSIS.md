# T69 — exact initialization and ordinary causal mixture updates

This is an analysis-only response to the [T68 decision](../t68-compact-mixture-capacity/DECISION.md). The six scientific inputs are T55 TASK, T52 ANALYSIS, T54 result, T60 FORMULATION, T67 DERIVATION and T68 result. No field, array, integral, root, fit or trajectory is numerically evaluated. The algebra below defines ordinary comparator mechanisms, not novelty or a finite-time result.

## 1. Same field, measures and initial condition

Write theta=(rho,nu,z_c), with rho=s_r^2>0 and nu=s_z^2>0, and

    g_theta(r,z) = exp[-r²/(2rho)-(z-z_c)²/(2nu)] / N_theta,
    N_theta = rho sqrt(2pi nu),
    q = Gamma [(1-eta)g_1 + eta g_2],  0 <= eta <= 1.

The circulation measure is r dr dz; every g has unit circulation. The full-space physical-vorticity inner product for q is H: <a,b> = integral 2pi r³ a b dr dz, since omega_theta=rq. Evolution fitting here uses H, consistent with T52's complete-tangent problem. Later task scoring retains T55/T60's D8 field metric and full-space model moments; these norms are not conflated.

The exact initial field is q0=(3/2)exp[-(r²+z²)/2], so Gamma0=(3/2)sqrt(2pi), theta0=(1,1,0). No finite initial component displacement is permitted as an unreported approximation. T68's fitted final parameters and reference snapshots are not predictor inputs.

## 2. Exact positive initialization and rank

If Gamma[(1-eta)g_1+eta g_2]=Gamma0 g_0 and 0<eta<1, integration gives Gamma=Gamma0. Let x=r²/2. The radial circulation marginal is a positive mixture of exponential densities rho_i^-1 exp(-x/rho_i). Its Laplace transform is

    (1-eta)/(1+rho_1 s) + eta/(1+rho_2 s) = 1/(1+rho_0 s).

Distinct negative poles cannot cancel because their nonzero residues are positive. Thus rho_1=rho_2=rho_0. The axial marginal's moment generating function is the positive sum of exp(z_i t+nu_i t²/2). Comparison as t tends to positive and negative infinity first fixes the maximal variance and its centers to nu0,z0. The coefficient of the dominant term must be one, so a positive component with smaller variance cannot remain. Consequently both axial variances and centers equal the original ones. Unequal positive weights are allowed, but distinct positive components cannot exactly reproduce this single Gaussian. At eta=0 or 1, the inactive component can be arbitrary.

At coincidence with an interior weight, a differentiable parameter path gives

    q_dot = Gamma_dot g0
          + Gamma0 Dg0[(1-eta)theta1_dot + eta theta2_dot].

The eta derivative vanishes. The four functions g0, partial_rho g0, partial_nu g0 and partial_zc g0 are independent: after division by positive g0 their polynomial factors span 1,r²,(z-z0)²,z-z0. Thus the eight-parameter Jacobian has rank four, with four null directions. Fixing Gamma leaves rank three. If full-space axial impulse I_z=2pi Gamma [(1-eta)rho_1+eta rho_2] is also fixed, the coincident feasible tangent has rank two, retaining axial variance and translation. T52's optimal translation is feasible in each of these cases.

This describes the Jacobian for differentiable parameter paths. It does **not** classify the entire density-space tangent cone or prove a two-component trajectory must fail.

## 3. Splits and non-smooth parameter paths

For fixed eta in (0,1), set theta1=theta0-eta delta d and theta2=theta0+(1-eta)delta d. With positive widths for sufficiently small delta,

    (1-eta)g(theta1)+eta g(theta2)
      = g0 + eta(1-eta)delta² D²g0[d,d]/2 + O_H(delta³).

Taking delta proportional to sqrt(t) produces an additional candidate density derivative while individual parameters are not differentiable at t=0. These are constructed tangent-cone branches, not a proof of complete cone coverage. Ordinary finite-step projection is not restricted to the coincident Jacobian.

A pure symmetric axial split with unchanged variance has leading term delta² partial_zc² g0/2 = delta² partial_nu g0, already in the old tangent. If its two variances are reduced to nu0-delta², the equal-weight centers z0±delta preserve initial circulation, centroid, covariance and impulse, but the density becomes

    f_delta = g0 - delta^4 partial_zc^4 g0/12 + O_H(delta^6).

It is still an approximate initial density whenever delta is nonzero. The initial Euler q derivative and the optimal translation residual are odd in z; this fourth-order symmetric direction is even and is orthogonal to them in H. Moment preservation alone therefore cannot establish an improvement. More general centered splits can have other leading terms. No nonzero split is installed as the initial state in the selected comparator.

## 4. Ordinary alternative A: one-sided component birth

At eta=0, choose a possible new component g_theta using only current-state information. For fixed circulation a feasible path is

    q(t)=Gamma0[(1-t beta)g(theta0+t v)+t beta g_theta], beta>=0.

Its derivative is Gamma0 Dg0 v + beta d_theta, where d_theta=Gamma0(g_theta-g0). Let V be the allowed old linear tangent, P its H-orthogonal projection, R=(I-P)F(q0) and e_theta=(I-P)d_theta. For fixed new geometry,

    beta* = max(0,<R,e_theta>) / ||e_theta||²,
    residual² = ||R||² - max(0,<R,e_theta>)² / ||e_theta||².

If e_theta=0, choose no birth. At positive gain an interior geometric stationary point obeys <R-beta*e_theta,partial_theta e_theta>=0; otherwise boundary candidates must be considered. A zero-gain tie chooses no birth; a positive-gain tie requires a fixed geometric order. The formula is ordinary constrained least squares, not a global geometric solution.

If impulse is additionally fixed, v_rho+beta(rho_theta-rho0)=0. The compensated direction is

    d_theta^I=Gamma0[g_theta-g0-(rho_theta-rho0)partial_rho g0],

and V retains only axial variance and translation. For small t, rho_active(t)=(rho0-t beta rho_theta)/(1-t beta) preserves impulse exactly while remaining positive. Requiring the new component alone to have rho_theta=rho0 would unnecessarily weaken this alternative. Axial centroid and covariance are not Euler invariants.

This is a valid ordinary alternative, but numerical selection requires a current-state geometric search plus a qualified tangent/rank solver and continuation through boundaries. It is not chosen for the next implementation. Its absence from a run must not be converted into a claim that all causal mixtures fail.

## 5. Ordinary alternative B: finite-step field projection

From the current model q_n, form y_h=q_n+h F(q_n), where F is the same free-space axisymmetric no-swirl Euler derivative. Select a positive two-component approximation to y_h. The target depends only on the current state and step size. Starting with exact q0 does not require perturbing parameters, and optimization of fields avoids inverting the coincident parameter Jacobian.

For fixed new geometry, let b_i=<y_h,g_i>, M_ij=<g_i,g_j>, f_eta=(1-eta)g1+eta g2, B=b1+eta(b2-b1), M=<f_eta,f_eta>>0. Unlike the positive endpoint reference, y_h can be signed and b_i need not be positive. The nonnegative-scale optimum is therefore

    Gamma*(eta)=max(0,B/M),
    improvement J(eta)=max(0,B)²/M.

Write beta0=b1, beta1=b2-b1, m0=M11, m1=2(M12-M11), m2=M11-2M12+M22. On B>0, J' is proportional to

    A0+A1 eta,
    A0=2 beta1 m0-beta0 m1,
    A1=beta1 m1-2 beta0 m2.

Evaluate eta=0,1, an interior -A0/A1 when A1 is nonzero, and the interior B=0 boundary when beta1 is nonzero. At most four weights suffice in exact arithmetic. Constant/identical cases use deterministic endpoint representatives. There is no Gram-matrix inversion or quartic reference-moment constraint. A selected zero-amplitude field has undefined normalized moments and must be reported as a failed physical state, not silently clipped/replaced. Finite positive-width geometry boxes make this a well-defined bounded search, not a global family optimum.

The new comparator does not use T67's reference centroid/covariance feasible set: that would leak the future solution. Circulation and impulse are diagnostics in this selected free-scale variant, exactly as specified prospectively. The optional invariant-constrained birth algebra does not silently constrain this different variant.

## 6. Current-state velocity from ordinary heat potentials

The T60 free-space equation is -Delta_5 phi=q, with Delta_5=partial_rr+3 partial_r/r+partial_zz. Regard r as the radius of four auxiliary coordinates; no new physical dimension is introduced. The meridional velocity is

    u_r=-r phi_z,   u_z=2phi+r phi_r,
    F(q)=r phi_z q_r-(2phi+r phi_r)q_z.

For a current component q_i=A_i exp[-r²/(2rho_i)-(z-z_i)²/(2nu_i)], where A_i=Gamma w_i/N_i, define R_i=rho_i+2tau, V_i=nu_i+2tau and k_i=(rho_i/R_i)² sqrt(nu_i/V_i). Gaussian heat propagation gives

    phi_i(r,z)=A_i integral_0^infinity
        k_i exp[-r²/(2R_i)-(z-z_i)²/(2V_i)] d tau.

Indeed the integrand is exp(tau Delta_5)q_i, so integration of its time derivative gives -Delta_5 phi_i=q_i; the propagated Gaussian tends to zero at infinite tau. Decay and regularity select the free-space solution. Differentiation under the convergent integral yields phi_r and phi_z. This is an ordinary inverse-Laplacian representation, not a new fluid method or a numerical result. For the normalized initial Gaussian, phi(0)=A0/3=1/2 and u_z(0)=1, providing an exact calibration.

Expanding F over ordered current-component pairs i,j gives the integrand

    A_i A_j k_i exp(E_i+E_j)
      * [ r²(z-z_i)/(V_i rho_j)
          + (2-r²/R_i)(z-z_j)/nu_j ],

where E_i uses the broadened heat widths and E_j the original q_j widths. This retains both self and cross interactions, including their signs.

## 7. Collapse target cross products, not all validation costs

For a candidate normalized component g_l, define lambda_i=1/V_i, lambda_j=1/nu_j, lambda_l=1/nu_l and

    rho*=(1/R_i+1/rho_j+1/rho_l)^(-1),
    nu*=(lambda_i+lambda_j+lambda_l)^(-1),
    mu*=nu*(lambda_i z_i+lambda_j z_j+lambda_l z_l),
    E=sum_{a<b} lambda_a lambda_b (z_a-z_b)² / sum_a lambda_a,
    Z0=sqrt(2pi nu*) exp(-E/2), R3=2rho*², R5=8rho*³.

The nonnegative pairwise expression for E avoids subtracting large squared centers. Exact Gaussian radial/axial integration leaves

    <F_ij,g_l> = (2pi A_i A_j/N_l) integral_0^infinity k_i Z0
        * [ R5(mu*-z_i)/(V_i rho_j)
            + (2R3-R5/R_i)(mu*-z_j)/nu_j ] d tau.

Therefore b_l=sum_j Gamma w_j <g_j,g_l> + h sum_ij <F_ij,g_l>. Gaussian Gram entries use the all-space closed form already in T67. Up to four scalar one-dimensional ordered-pair integrals per candidate component suffice for the target cross product. No future-reference array or hidden grid solve is required by this mathematical evaluator.

This reduction supports ranking and scale/weight elimination. It does **not** make C=||q+hF||² free: ||F||² generally introduces two heat variables. Any reported absolute/relative target error needs a separately paid direct evaluation or qualified independent expression. All numerical heat quadrature, candidate contractions, Gram entries, failed searches, direct checks and memory/setup remain costs. Convergence/tail treatment of the improper integrals is not established by writing the formula.

The selected finite algorithm and unresolved numerical prerequisites are in [COMPARATOR.md](COMPARATOR.md). There is no new numerical evidence or TOG contribution in these analytic reductions.
