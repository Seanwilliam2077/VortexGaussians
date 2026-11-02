# Moving-domain circulation: an ordinary continuum contract

This is a local mathematical derivation, checked separately from the source reading in [SOURCE_NOTES.md](SOURCE_NOTES.md). It is not a new numerical method or a claim that these identities are absent from prior work.

## State and assumptions

Let Omega(t) be a smooth, bounded, connected Euclidean fluid domain transported by a smooth diffeomorphism with unchanged topology. Use incompressible constant-density inviscid Euler flow, conservative body force with a globally single-valued potential, and prescribed wall-normal speed g. A merely curl-free force need not have zero periods on this domain. The wall condition is u dot n=g. No free surface, no-slip enforcement, viscosity, topology changes or two-way coupling is covered.

Require compatible boundary flux integral(g)=0 (hence constant total fluid volume here) and a realizable vorticity field, not just arbitrary samples satisfying a local divergence check. In3D, omega must be a curl; global closed-surface compatibility matters. Initial full velocity, or equivalent vorticity and global period data, must be provided. Smoothness is assumed for every transport/derivative below.

At a fixed instant, define H(t) as fields h satisfying curl h=0, div h=0 and h dot n=0. Its dimension is the real first Betti number b1 under these assumptions. This is not generally the number of obstacles: a spherical exclusion in a3D ball does not create the same first-homology loop as a hole in a2D planar domain. Moving an object does not by itself establish a missing harmonic degree of freedom.

Choose any particular reconstruction u0 with curl u0=omega, div u0=0 and u0 dot n=g. Any other solution is

    u = u0[omega,g,Omega(t)] + sum_j a_j h_j(t).

The difference of two solutions has exactly the defining homogeneous constraints of H. It can therefore be fixed by b1 independent period conditions on representative closed curves C_i(t). With

    Gamma_i = integral_C_i u dot dx,
    b_i     = integral_C_i u0 dot dx,
    P_ij    = integral_C_i h_j dot dx,

the coefficient contract is P a = Gamma-b. A genuine homology basis and harmonic basis make P nonsingular in the continuum. A discrete construction must qualify that property and its conditioning. Single-valued scalar gradients have zero closed-loop periods and cannot supply arbitrary missing ones.

Even if Gamma is constant, a need not be: differentiating gives

    P a_dot = Gamma_dot - b_dot - P_dot a.

Period-normalized h makes P=I; a specially chosen zero-period u0 makes b=0. Those are legitimate ordinary coordinate choices, whose construction/maintenance costs cannot disappear from a comparison.

## Moving curves: the velocity of the curve matters

Let C(t) move with prescribed curve velocity w, which need not equal fluid velocity u. Differentiating a parametrized line integral gives

    Gamma_dot = integral_C [partial_t u + (w dot grad)u + (grad w)^T u] dot dx.

Write Euler as partial_t u=u cross omega-grad(p+|u|^2/2). The remaining transport terms equal -w cross omega+grad(w dot u). Gradients integrate to zero along a closed curve, yielding

    Gamma_dot = integral_C [(u-w) cross omega] dot dx.

The formula uses3D vector notation; planar flow embeds with out-of-plane scalar vorticity. For a material curve, w=u and Gamma is constant. For a geometry-attached or regenerated curve, its motion must be specified and the right-hand side generally remains. Replacing a representative curve with a homologous one also requires the vorticity flux through the connecting surface; it is not a free relabeling when curl u is nonzero.

This does not mean moving walls invalidate Kelvin conservation: a smooth material curve that remains in the fluid still has the stated invariant under the assumed physics. With viscosity or nonconservative force, corresponding line-integral terms return; this task does not claim to solve them.

## A second ordinary route: differentiate an instantaneous orthogonal basis

Choose h_i(t) L2-orthonormal on Omega(t) and u0 perpendicular to H(t), so a_i=integral_Omega u dot h_i. Reynolds transport and Euler give

    a_dot_i =
        integral_Omega (u cross omega) dot h_i
      + integral_Omega u dot partial_t h_i
      + integral_boundary g (u dot h_i).

The pressure-gradient contribution vanishes because div h_i=0 and h_i dot n=0. Eulerian time derivatives at the moving boundary require smooth extensions. For a stationary domain and a time-independent basis, only the first term remains. Thus blindly retaining that first term in a moving orthogonal basis drops geometric transport terms. Conversely, using their exact expression is ordinary differentiation, not yet an efficient or stable discretization.

## Fair alternatives and full cost

One ordinary alternative evolves the complete initial velocity with an accurate velocity-pressure formulation and the same wall motion. A single-valued pressure correction preserves continuum closed-loop periods of the provisional velocity. This is an information statement, not a guarantee of finite-step advection accuracy or a performance claim.

A second reconstructs div-curl with the period conditions above, using either properly maintained material curves or explicitly moving representatives. Both are valid comparison routes; giving the velocity method only vorticity would be an unfair deletion of its state.

For a future comparison, include geometry updates, discretization/mesh or cut-cell maintenance, cycle construction/transport, quadrature, vorticity transfer, basis or constrained solves, conditioning, reconstruction, synchronization and memory. A small b1 only counts global variables; it does not bound their update cost or justify ignoring volume-sized fields.

One precise unanswered computational question is whether accurate global periods can be maintained through moving geometry and flow-map reinitialization without expensive curve/basis maintenance, while matching a complete velocity-pressure baseline at lower full cost. This task supplies neither a measured costly workload nor a new mechanism for doing so. Ordinary identities must not be presented as the answer.
