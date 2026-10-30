# T69 comparator — bounded ordinary Euler-target projection

This selects alternative B of [ANALYSIS.md](ANALYSIS.md) for later numerical qualification. It is a deterministic, finite-search ordinary comparator contract in exact arithmetic. Its heat integrals, floating-point weight decisions, numerical accuracy and runtime are **not yet qualified**. No implementation or scientific invocation is authorized by this document alone.

## Information and exact initialization

Input to a step is only its own nonzero positive mixture q_n, a predeclared positive step h and original physical parameters. q0 is exactly (3/2)exp[-(r²+z²)/2], represented canonically by Gamma0=(3/2)sqrt(2pi), eta=0 and both geometries (sr,sz,z)=(1,1,0). No split occurs before the first step. A zero-weight component is discarded when constructing current-state search anchors; it cannot encode a hidden endpoint hint. Exactly identical active components are combined for current-state calculations.

No reference trajectory, future velocity, reference moments, T63 selected tuple or T68 final geometry/weight/scale enters a step. The inherited T54 scalar is available for initial calibration, not a replacement for current-state velocity at arbitrary mixtures. Reference snapshots are used only by a later independent score evaluator. This remains a development algorithm informed by prior research, not a claim of blind method design.

## Evolution target and objective

Use the full-space heat-potential operator derived in ANALYSIS: obtain phi from the current q_n, construct u_r=-r phi_z, u_z=2phi+r phi_r and F=-u dot grad(q_n). Keep all ordered current-component self/cross contributions. Form y_h=q_n+hF(q_n) and minimize ||y_h-q_new||_H² over the finite search described below, where H has weight 2pi r³ on r>=0,z in R. The numerical procedure is a forward-Euler target followed by nonlinear projection; no time order, stability or convergence theorem for the resulting singular family is asserted.

y_h may be signed. The next model uses nonnegative scale and weights, so this is a positivity-constrained projection, not clipping the target. Circulation and impulse are not constrained in this selected variant; report their analytic full-space values after every accepted step. No new conservation threshold is added to old endpoint results. Current-state centroid/covariance define search scales only, not target/reference gates.

Let current normalized active weights be w_j and define

    a = sum_j w_j z_j,
    R = sqrt(sum_j w_j sr_j²),
    Z = sqrt(sum_j w_j [sz_j²+(z_j-a)²]).

Both scales are positive. Construct the 45 geometries

    sr/R in {3/4,1,5/4}, sz/Z in {3/4,1,5/4},
    (z-a)/Z in {-1,-1/2,0,1/2,1},

and include every current active geometry (at most two). Remove exact duplicates and sort by (z,sr,sz). The bank contains at most 47 entries, or exactly 45 at the initial isotropic single component. These rational relative offsets are chosen here before numerical startup evidence; they do not reuse the endpoint-fitted T63/T68 tuple.

Search bounds for each component are:

    sr in [min(R/2, min current sr), max(3R/2, max current sr)],
    sz in [min(Z/2, min current sz), max(3Z/2, max current sz)],
    z  in [min(a-3Z/2, min current z), max(a+3Z/2, max current z)].

Each step has a compact positive-width box containing its entire current state and bank. This is a stated restriction, not the unrestricted mixture family. Bounds are recomputed from the predictor's current state only. No future endpoint or failed quality test expands them.

## Inner problem and singular cases

For each canonical unordered pair including identical pairs, obtain the two target cross products and three analytic H-Gram entries. Use the four-or-fewer eta candidates from ANALYSIS, evaluate M with the nonnegative barycentric form

    (1-eta)² M11 + 2eta(1-eta) M12 + eta² M22,

and Gamma=max(0,B/M), J=max(0,B)²/M. This avoids a singular two-component matrix inverse. Treat exact constant/linear/identical-component cases explicitly. A positive scale defines a valid state; zero scale is retained as the boundary result for accounting but cannot supply normalized physical moments.

An unchanged-current-field control evaluates its saved Gamma and eta on its own geometry and computes J_control=2Gamma B-Gamma²M. That is one additional weight/scale evaluation. It is not a refit or a hidden reference. The exact prescribed search contains a projection at least as good as this control; later numerical qualification must check that fact, not silently replace a bad selected result by the control.

Candidates rank by descending J, then lexicographic canonical pair keys ((z1,sr1,sz1),(z2,sr2,sz2)), then ascending eta. A candidate's scale is determined by its weight. Exact ties follow this order; a later numerical implementation must record its arithmetic/tie treatment. Near-cancellation or indeterminate scalar classification cannot be declared a complete inner optimum. Qualifying one candidate is distinct from certifying the entire inner problem.

## Finite outer search

1. Propose all N(N+1)/2 bank pairs, in sorted triangular order. With N<=47 this is at most 1128; the original single-Gaussian first step has 1035. Evaluate or charge each exact duplicate through a cache. No early stop based on a promising score.
2. After the entire bank, retain up to four distinct canonical geometry pairs with positive fitted scale, ranked by the rule above. If none exists, return a zero-state/no-positive-candidate failure with costs; do not install an alternate initial condition.
3. For each start, visit three levels. The (sr,sz,z) coordinate step sizes are respectively (.10R,.10Z,.20Z), (.05R,.05Z,.10Z), and (.025R,.025Z,.05Z). At each level make at most eight complete polls. A poll proposes all twelve signed neighbors of the fixed pair at the start of that poll, traversing component 1 then 2, coordinates sr,sz,z, negative then positive.
4. Canonicalize each proposal; reject and count any out-of-box coordinate, without clipping. Reuse exact cached pairs and component bases, counting the attempted work. After all twelve neighbors, move to the greatest strictly improving J using the same tie order. If none improves, stop that level and continue to the next. A successful move on poll eight still ends that level.
5. Complete all scheduled starts/levels and select the best eligible candidate among all evaluated pairs. Preserve the unchanged tuple for independent direct confirmation. No alternate winner, extra start, larger box or component escalation after failed confirmation.

This gives at most 1152 neighbor proposals and **2280 total proposals per step**. The returned tuple is only the best encountered by this finite algorithm. It is not an exact global nonlinear projection, and bounded search resolution may affect small-step behavior. A stall or miss does not establish an unavoidable causal-mixture limitation.

## Paid work and failure semantics

For K<=2 active current components, each new candidate component needs at most K²<=4 heat cross integrals, plus at most K analytic current/candidate Gram terms. A neighbor changes one component, so there are at most 47+1152=**1199 distinct component bases** per step, hence at most **4796 distinct scalar improper cross integrals for primary search**. Cached reuse is counted once for computation and separately as a hit. Re-evaluation under another rule or in qualification is additional numerical work and must be counted separately. Quadrature-node work must also be counted; the number of mathematical integrals is not its evaluation cost.

At most three analytic candidate Gram entries are computed per distinct pair; at most four scalar weight attempts per proposal plus the one unchanged-state control gives the conservative **9121 weight/control-attempt bound**. Count rejected/duplicate proposals, all heat-rule setup, logarithms/exponentials, Gram evaluations, current-state source setup, target contractions, selection, numerical qualification and output. No implicit free grid velocity solve, derivative solver or precomputed future flow is allowed.

Ranking does not require C=||y_h||². The chosen absolute-residual and target-relative-error confirmation route will compute C separately and charge it; an improvement difference could instead cancel this common constant algebraically. Direct Euler-target evaluation and its norm require separate paid work, including current-state velocity at all check points. The one-dimensional contraction formula does not cover those costs automatically. Full physical scoring against saved references is also separate from prediction and must be charged.

Nonfinite fields, nonpositive widths, invalid normalized state, unresolved required quadrature accuracy, unqualified arithmetic, resource limits or direct-confirmation failure produce a recorded failed step, with no retrospective gate change or uncharged retry. A partial search cannot be treated as the completed scheduled comparator. Preserve the best provisional tuple separately from any accepted physical state. The next numerical contract must make these statuses and all limits executable.

## Remaining qualification before a trajectory

The mathematical map, information boundary and finite search are now specified. The missing prerequisite is numerical evidence for the current-state heat potential/cross contractions and selected projection. A later fixed-budget qualification must independently check the initial velocity/derivative against T52/T54, signed-target amplitude boundaries and degenerate components, and compare one-dimensional contractions with direct field integration while accounting for improper-integral and spatial tails. It must fix heat/spatial quadrature rules, tolerances, permitted test states, step sizes and resource caps before execution.

The first qualification should use the exact original initial state and no endpoint snapshot. It must not be promoted to full t=1 success. Subsequent trajectory claims still require the original five times, unchanged D8 field/centroid/covariance requirements, step/reference sensitivity and all-source cost. Numerical failure would leave this ordinary comparator unresolved; it would not establish a new mechanism's superiority.
