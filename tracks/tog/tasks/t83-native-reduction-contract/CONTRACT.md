# T83 operator contract: no drop-in common weight for the native state

10 November 2026. **Decision: close the narrow drop-in multiplicity hypothesis.** A coefficient encoded only by changing existing particle fields cannot, in general, preserve the native intensive queries, signed source evolution, index-selected material heating and optical composition together. An explicitly weighted model remains possible; it changes the operator and requires a separate justification. This is not a theorem against approximate reduction, weighted fluid methods, or transported-response fitting.

This analysis follows [BRIEF.md](BRIEF.md). It uses source algebra and existing-record schema/count inspection, with no new numerical probe, optimization, browser or trajectory. It is a contract qualification, not a scientific performance result or a TOG contribution.

## Scope and existing evidence

The native demo identity is SHA256 `e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0`. The six intended units were `stepSpread`, `vpmFieldAt`, `vpmDirectAll`, `vpmBuildDirector`, `stepSimVPM`, and the render path with its particle shader. A fixed line slice around `vpmBuildDirector` inadvertently displayed the opening excerpt of the adjacent `vpmDirVel` helper; no claim below depends on that extra excerpt, and no further helper investigation followed. The render blend state was explicitly checked, rather than inferred solely from a comment.

The existing [T81 summary](../t81-firewoods-capacity-causality/SUMMARY.json) records a qualified ordinary pooling test. The [public global-AB endpoint](../t81-firewoods-capacity-causality/public/global-AB-endpoint.dynamic.json.gz) has 5,400 generated particles, with layer counts `[0,0,1734,1288,1033,1274,71,0,0]`. Its sample native record contains `x,y,G,T,d,vx,vy,seedp,life,sxx,sxy,syy,sg,Tb`; its observation identity is separate. There is no native multiplicity field in the source constructor. These are saved-state facts, not a compression experiment. The T81 result does not establish compression necessity: ordinary pooling resolved observed direct B-source capacity rejection, and the later full pool did not reject B-source offers.

The public projection omits static recipient geometry and some auxiliary continuation state. Therefore it is neither a self-contained material-interaction benchmark nor a restart certificate. Actual native evolution also requires the appropriate array order, clocks, RNG/control state, scheduled inputs and external geometry/placement. No such future evolution is performed here.

## Operator map

Here `G` is the code's signed vortex source strength, `Tb` its dynamical temperature proxy, `T` its display/feedback temperature proxy, and `d` a visual density parameter. This table does not assign calibrated mass, energy or material units to these fields.

| Field/state | Where it enters | Algebra at a fixed query/state | Why a single existing-field weight is insufficient |
| --- | --- | --- | --- |
| `G`, position, physical width `sg` | Direct velocity and velocity-gradient kernel sums; tree approximation; director construction | Direct sums are linear in `G` when positions, widths and query data are frozen. Production tree construction/traversal is not asserted linear after changing its inputs. | Native `G` also receives an additive per-particle baroclinic increment and a fixed clamp. Director centroids contain `abs(G)+1e-4`, not a multiplicity field. |
| `Tb`, positions, `sg` | Shepard temperature and moment-normalized temperature gradient; buoyancy and baroclinic update | Temperature is numerator/denominator; the gradient is another ratio with threshold/clamp. Source temperature is intensive. | A weight must enter the denominator, self contribution and gradient moments as well as the numerator. Scaling `Tb` alone cannot do this. |
| `T`, array order, layer order | Material flame heating, hot-particle test, display color, cooling and retirement | For a fixed selected set and hot/recipient eligibility, deposited heat is a sum of coefficients times `T`. Selection and eligibility are discrete. | The selected set takes array indices `0,7,14,...`, then the first at most160 eligible hot entries across layers. Deletion changes the operator before any field error occurs. Scaling `T` also changes gates, nonlinear cooling and color. |
| `d`, `T`, visual deformation `sxx,sxy,syy`, phase `seedp` | Splat footprint, clamped alpha, color/texture and retirement | A fixed primitive produces premultiplied emission and alpha; front-to-back composition is nonlinear in alpha. | `d` changes footprint and opacity together; it is not an independent optical-depth or multiplicity variable. Visual deformation is distinct from physical kernel width `sg`. |
| Position and layer membership | Vortex kernels, nearest-slice birth placement, geometric heat support, rendering depth and culling | Fixed-position source queries can be represented by a matrix after declaring the operator. | Moving a representative changes all these queries and sorting/support decisions; matching a few moments does not preserve them automatically. |
| Material state, frontier/cursor, particle-array lengths and RNG | Graph heat, material clocks, round-robin offers, admission and birth attributes | The legacy offer budget and admission depend on integer populations; birth consumes conditional RNG. New particles start with `G=0`, randomized `T,d`, and `Tb=T`. | Replacing several carriers by one changes slot counts and future admission/RNG. Existing thermal or visual fields cannot encode those scheduling semantics. |

Relevant source anchors are `stepSpread` around lines1145–1326, direct/tree queries around1888–1953, director construction around1961–1993, `stepSimVPM` around2086–2121, the particle shader around389–443, footprint construction around2716, and blend setup around2834. Source identity, rather than these navigational line numbers, is authoritative.

## Counterexample 1: signed source evolution is affine, not homogeneous

Consider the local `G` update while granting the reduction the favorable assumption that it preserves the queried temperature gradient `b=dtx`. Write `a=dt*baro*b` and `lambda=1-0.1*dt`. The code performs

`D(G,b) = clip[-60,60](lambda*(G+a))`.

If one representative stands for `m>1` identical source copies, the unchanged fixed-geometry direct velocity sum requires its signed source strength to be `Gamma=m*G`. In an unsaturated branch, the sum of the original copies after the update is

`m*D(G,b) = lambda*(m*G+m*a)`,

whereas the unchanged update of the representative is

`D(m*G,b) = lambda*(m*G+a)`.

Their difference is `(m-1)*lambda*a`, nonzero for a nonzero native baroclinic increment. The case `G=0` already suffices. This is a symbolic component-level counterexample, not a measured trajectory or a newly constructed scene. Clipping gives an additional mismatch: the copies can have total source strength up to `60*m`, while the representative remains capped at60.

Scaling the represented gradient to `m*b` would alter an intensive query and its other uses; it would not preserve the assumed native query contract. A modified weighted update can instead use `Gamma_new = w*D(Gamma/w,b)` for positive `w`, but that explicitly changes the evolution rule. The argument closes unchanged-field multiplicity encoding; it does not exclude a deliberately approximate fit on particular states or a newly weighted solver.

## Counterexample 2: a temperature numerator cannot hide a missing denominator

Use the direct thermal operator, retaining a query particle with intensive temperature `A`. Let `m` coincident source copies have temperature `B` and the same positive off-self kernel value `k`. The native self term is one. Holding positions/physical widths fixed gives

`Theta_original = (A + m*k*B)/(1 + m*k)`.

After replacing the copies by one source with any chosen temperature `B_prime`, the unchanged operator gives

`Theta_reduced = (A + k*B_prime)/(1 + k)`.

No single `B_prime` independent of the query temperature can make these equal for all `A`: their coefficients of `A` are respectively `1/(1+m*k)` and `1/(1+k)`. `G,d,T` and visual deformation do not supply the missing denominator factor. Fitting one query may succeed; that is an approximation at that query, not a general multiplicity interpretation. Changing source width/position is a separate kernel approximation, not a common coefficient on the original source column.

A genuine weighted ratio can multiply both numerator and denominator contributions while retaining intensive temperatures. This counterexample does not prohibit that ordinary construction. The separate normalized-gradient numerator/denominator and native self convention must also be specified; the LUT's coincident neighbor value and the explicit self value should not silently be treated as interchangeable.

## Counterexample 3: the native heat operator is not a function of an unordered particle measure

Before the frozen160-hot-sample cap is reached (`P.spreadSampleCap` is configurable in the source), consider an eligible hot particle at array index1 and an ineligible cold particle at index0, with other sampled indices ineligible. For an unburned material recipient with initially zero heat within the hot particle's radius, the former ordering contributes no heat from that hot particle. Swapping these two entries preserves every unordered particle moment but selects the hot particle at index0 and produces the positive contribution

`dt*spreadHeat*T*(1-distance/radius)`.

This analytic ordering counterexample uses the literal selection rule; it does not claim that this exact swap was executed on T81. Any representation only of `sum_i w_i*delta(state_i)` loses information the native operator actually uses. Reproducing it requires an explicit selection/order contract. Keeping inactive slot placeholders or a separate selected-source list may be possible, but then actual memory, traversal and capacity accounting must be stated; mere deletion and reweighting do not preserve native semantics.

## Optical subcase: alpha scaling is not multiplicity

The inspected render path clears scene alpha to zero and uses `gl.blendFunc(gl.ONE_MINUS_DST_ALPHA,gl.ONE)`, so it is premultiplied front-to-back composition, not a purely additive particle pass. Two coincident equal-color/equal-footprint copies, composed contiguously with no intervening contribution and per-pixel alpha `a`, have combined alpha `2*a-a*a`. More generally integer `m` such copies have `1-(1-a)^m`.

For the legacy shader branch used by T81, even in a fixed-footprint coefficient subcase `a=A*g(pixel)`, two copies require `2*A*g-A*A*g*g`; changing a scalar opacity coefficient supplies only `A_prime*g`. The extra `g*g` term cannot be matched for all pixels by a scalar coefficient when `A` is nonzero. This is a conditional optical algebra statement, not a claim that every native fire pixel or shader mode has that simplified form. Native `d` additionally changes the footprint and enters clamps, so multiplying it does not implement the required per-pixel transmittance transform.

The inspected shader already contains an ordinary optical-depth alternative when `uP3>0.5`: `alpha=1-exp(-max(0,v_fade*uP3Tau*v_dens*g))`, with a comment concerning half-weight copies. At a fixed footprint and nonnegative optical depth, scaling that optical depth by `w` implements `alpha_w=1-(1-alpha)^w`. Selecting this existing path changes the rendering model relative to T81's legacy branch; it is not a new optical innovation. It also does not establish dynamic multiplicity or equivalence for unequal footprints, phases, colors and depth interleaving. The legacy optical subcase supports only the narrow conclusion, not a proof that all native modes or possible visual representative fits fail.

## Required weight-one identity for any future model

Let `I(S)` retain every original carrier in the original order and append `w_i=1`. A future weighted operator `Phi_tilde` must satisfy

`project(Phi_tilde(I(S),inputs)) = Phi_native(S,inputs)`

for the same complete native state, inputs, RNG semantics and runtime, before any reduction is credited. No such implementation or regression has been performed in T83.

An ordinary candidate construction can use explicit weighted source strengths, weighted Shepard numerator/denominator and gradient moments, and the extensive source update described above. At weight1 those algebraic formulas reduce to the original component expressions. That component identity alone does not certify the whole solver: tree aggregation/self handling, director statistics, clamping, source scheduling, shader semantics and floating-point evaluation order also matter. Dispatching the all-ones case to the untouched native path can establish a clear implementation reference, but does not validate reduced weights or guarantee exact equivalence to coincident copies for arbitrary weights.

Weights must have a declared meaning for capacity: actual retained carriers determine storage, while represented multiplicity is different. Which quantity controls admission is a model decision. It cannot be chosen implicitly by multiplying an existing scalar. Likewise, replacing index sampling by an all-particle heat sum is a disclosed new interaction model, not a fidelity improvement relative to the unchanged native operator by definition.

## Ordinary controls, costs and final boundary

For a future explicitly defined weighted problem, ordinary spatial bins, signed-source/moment fitting, current-rate NNLS, binned and warm-started NNLS, and a zero-horizon response control must be allowed. A direct reference at declared queries can separate compression error from Barnes–Hut error; this need not replace the production model globally. Baselines need the same operator/weight meaning and actual support budget. Independent temperature and optical state must be allowed where the shared-state design creates unnecessary constraints.

Charge state extraction, partitioning, kernel/response queries, predictor construction, optimization, support maintenance, tree rebuild/traversal, all post-reduction dynamics, rendering, memory and any full-state fallback. Retaining the original states for certification has a real memory cost. A heat-query coreset that retains all particles may reduce interaction work, but it does not reduce particle storage or free admission slots. A frozen-velocity response fit does not validate a coupled rollout.

T81 supplies an ordinary allocation success and instrumented cost observations, not an unmet compression requirement. The source counterexamples close only the proposed drop-in common weight through unchanged fields/operators. They leave approximate methods and explicitly changed weighted models open in principle. Neither is selected for implementation here: a worthwhile residual task and fair model contract are still needed, and no later ignition, harder scene, stricter historical gate, new numerical run or paper score follows this static result.
