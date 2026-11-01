# T74 decision and bounded next evidence

The shear has a real local projection gain. The general pure-shift energy inequality and missing conditional skew rule out interpreting that gain as an exactly conservative Euler model. Stop this particular full-solver development route. Approximate uses remain possible, but no demonstrated accuracy/cost separation justifies implementation now. Do not turn the newly derived lemma into an unverified originality or graphics-contribution claim.

The broader compact-vorticity question remains open. The current ordinary two-Gaussian baseline has endpoint capacity and causal startup, but its full-window result is time-sensitive. T74 adds a reason to demand radial redistribution and conditional axial shape change; it does not identify which limitation caused T71. Replacing the representation before separating those issues risks addressing a bottleneck the ordinary baseline does not actually have.

## Next bounded task: one saved-state local residual decomposition

Prepare a fixed protocol for exactly the already identified fine-path T71 state at t=5/8, `paths[1].steps[20].state` in the original T71 `result.json`. The next saved update changes only weights. Use these original states as inputs, without a new trajectory, reference endpoint fit, optimized candidate search, extra half-neighbors or additional physical scene.

The state uses Gamma=3.75615008934964, eta=0.279627593252541, geometries (1,1,0) and (0.936952772942467,0.7220788034569413,0.7689570190588), with geometry convention (sr,sz,z0). The scalar field is Gamma times a unit-circulation two-Gaussian mixture with weights (1-eta,eta). The next saved update, t=21/32, has Gamma=3.752273925278773, eta=0.2936337006283067 and identical geometries.

At this one distinct-component state, compare the actual Euler derivative with nested ordinary tangent spaces: the two weight directions, then all eight amplitude/geometry directions. Report the Gram spectrum/conditioning and explicitly qualify numerical rank; a linear solve is not free or automatically stable. Use a fixed direct residual confirmation, not only cancellation-prone norm differences. The exact integral rules, tolerances, rank policy, full cost cap and single-invocation limit must be frozen before any new numerical execution. This decision creates no completed measurement or ready-to-run protocol.

The useful output is a decomposition of local derivative error, not a threshold designed to pass a candidate. A large extra full-tangent capture would support ordinary geometry-search limitation locally. Little extra capture would identify a local linearization residual worth studying, while still allowing nonlinear finite-step projection and future parameter evolution to differ. Near degeneracy, nonsmooth splitting directions can also be missed by the ordinary Jacobian tangent; do not equate that tangent with the full family. Either result alone does not establish the cause of the finite-window error, representation insufficiency, a family impossibility, a new method or a rating increase.

This is intentionally distinct from T72's twelve additional finite-search neighbors. It asks whether the omitted ordinary geometry directions matter at all before a baseline repair or a richer family is selected. Do not run both diagnostics automatically or expand to more saved states after seeing a convenient outcome. If the local distinction is numerically unresolved, retain that result and stop the task instead of silently relaxing the contract.

An additional [post-confirmation algebraic note](FOLLOWUP_NOTE.md) identifies an ordinary Hamiltonian generator coupling the shear and omitted cubic direction. This is a constructive research lead, with global flow, energy, velocity cost and originality unresolved; it is neither an implemented alternative nor a second numerical queue.

No additional scientific task is executed in T74. Original numerical gates and failures remain. Art is paused by the user; no art author/reviewer is triggered. The historical TOG2/6 score remains a historical judgment, not a fresh review of this screen.
