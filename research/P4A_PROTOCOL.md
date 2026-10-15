# P4a — finite-capacity gas–surface thermal exchange

Protocol prepared for root's final source freeze, 2026-10-15. Root has approved the mathematical contract, 21-case matrix, and thresholds below. Fixture definitions, case identifiers and runner commands have been checked against `p4a-design.mjs` and `p4a-run.mjs`. No formal outcome has been used to choose this design.

## Scope and research claim

This phase establishes a standard numerical substrate for later true-3D gas–scene coupling. It tests fixed-geometry, finite-capacity, pairwise heat exchange with explicit physical measures. It does not implement combustion, gas motion, fuel depletion, cooling, radiation, occlusion, material inference, or a complete VPM feedback loop. It is not a new heat-transfer method or evidence of SIGGRAPH readiness.

Temperature is in kelvin. Surface node `s` has authored area `A_s` and areal heat capacity `cA_s`; gas node `g` has authored volume `V_g` and volumetric heat capacity `cV_g`. Capacities are `Cs=A_s*cA_s`, `Cg=V_g*cV_g`, in J/K. These quantities are physical inputs, not opacity, Gaussian covariance volume, analysis weights, or fitted output normalizers.

The kernel is `W_h(r)=3/(pi*h^3)*max(0,1-r/h)`. Its integral over 3D space is one. Pair conductance is `G_sg=beta*A_s*V_g*W_h(r)`. With `beta` in W/(m² K), `G` is in W/K. Only surface–gas pairs exchange heat. Geometry, support radius, capacities, and conductances stay fixed during a trajectory.

The finite-dimensional ODE is `Cs*dTs/dt=sum_g G_sg*(Tg-Ts)` and `Cg*dTg/dt=sum_s G_sg*(Ts-Tg)`. This is a declared phenomenological exchange model, not a resolved model of gas boundary layers or true contact/visibility. Nearby disconnected surfaces may exchange through shared gas support; this phase cannot validate whether that represents a physical barrier correctly.

## Update and API contract

`buildThermalGraph(scene,{h,beta})` returns `{graph,state}`. `stepThermalGraph(state,graph,dt,{safety:.9,maxSubsteps:100000})` returns a new `{state,ledger}` without modifying its inputs. `thermalEnergy(state,graph)` returns `{surface,gas,total}`.

Each substep reads the same old temperature vector for all pairs. It computes `Q=G*(Tg-Ts)*substepDt` once, accumulates `+Q` for the surface and `-Q` for the gas, then applies all accumulated increments simultaneously. It never clips temperatures to make an unstable update look valid.

`maxRate=max_i(sum_j G_ij/C_i)`. For an outer interval `dt`, the number of substeps is `max(1,ceil(dt*maxRate/safety))`; `substepDt=dt/substeps`. Formal safety is 0.9. The resulting update has a convex-combination/maximum-principle interpretation when conductances and capacities are nonnegative. The stress test checks this mechanism, not a claim of accuracy at arbitrary large outer timesteps. An empty/no-edge graph uses one substep; `dt=0` is legal.

IDs are strings or nonnegative safe integers, unique across both node classes after `String(id)`. Measures, capacity-per-measure, `h`, and `beta` are finite and strictly positive; temperatures are finite and nonnegative; positions and `dt` are finite, with `dt>=0`. Invalid values, arithmetic overflow, or an excessive substep request are rejected explicitly. No simulation state or energy is silently discarded.

Graph exports include IDs, positions, measures, capacity-per-measure, capacities, `sumG`, `maxRate`, and `edges[{i,j,G}]`; `j` is the global gas index. Input order is retained. State exports include temperatures, time, outer step count, and cumulative signed surface/gas transfers, substeps, and edge evaluations. Each outer step retains its temperature vector and ledger: `dt`, safety, rate, substeps, substep size, maximum CFL, edge work, before/after compartment energies, net transfers, compartment energy changes, and total residual.

## Fixed experiment matrix

All trajectories last 1 second and retain every outer step, including the initial state. Default `h=.65`, `beta=2`; outer `dt=1/60` unless listed otherwise.

| Family | Cases | Contract |
| --- | ---: | --- |
| Two reservoirs | 3 | `dt=1/30,1/60,1/120`; one surface `A=.5,cA=2`, one gas `V=.125,cV=4`, separation `.2`; initial temperatures 600/300 K. |
| Reverse temperature difference | 1 | Same pair, initial temperatures 300/600 K. Checks the signed exchange in the opposite direction. |
| No-edge pair | 1 | Same capacities/temperatures, separation outside kernel support; no evolution. |
| Stiff pair | 1 | Pair with `beta=100`, outer `dt=.1` (10 outer steps); exposes automatic CFL substepping. |
| Corner representation family | 10 | Base `n=4`; both classes split 2×, 4×, variable multiplicity; surface-only 2×; gas-only 2×; reverse order; fixed shuffle; rigid transform; both 4× plus shuffle. |
| Corner temporal refinement | 2 | Base `n=4` with `dt=1/30` and `1/120`, compared with the existing `1/60` base. |
| Corner spatial refinement | 2 | `n=2` and `n=6`, compared with existing `n=4`. Diagnostic only. |
| One-sided negative control | 1 | Same declared corner geometry/capacities, but a transfer credited to the surface is not debited from the gas. This deliberately changes the ODE and is not a legitimate physical competitor. |
| Total | 21 | All cases complete before scientific interpretation. |

The corner comprises two perpendicular surfaces, `x=0` and `y=0`. Each spans local coordinates `[.1,.9] × [-.4,.4]`, area .64. Gas occupies `[.1,.9]² × [-.4,.4]`, volume .512. Cell-centred quadrature gives `2*n²` surface nodes and `n³` gas nodes: total counts 16/96/288 for n=2/4/6. Surface `cA=2`, gas `cV=3`. Surface initial temperature is `300+120*u+60*v`, where u/v are normalized in-plane coordinates. Gas initial temperature is `500-105*xnorm-60*ynorm+30*znorm` on normalized domain coordinates. Exact fixture coordinate/ID/multiplicity/shuffle/rigid-transform definitions are serialized in the frozen design and every case scene; they are not selected after results.

Formal case IDs, in order: `pair-dt30`, `pair-dt60`, `pair-dt120`, `pair-reverse-temperature`, `pair-disconnected`, `pair-cfl-stress`, `corner-base-dt60`, `corner-uniform2`, `corner-uniform4`, `corner-variable`, `corner-surface-only2`, `corner-gas-only2`, `corner-reverse`, `corner-shuffle`, `corner-rigid`, `corner-uniform4-shuffle`, `corner-dt30`, `corner-dt120`, `corner-refine-coarse`, `corner-refine-fine`, `corner-undebited-negative`.

The disconnected separation is .8 m. Variable multiplicity is `1+((cell[0]+2*cell[1]+3*cell[2]) mod 4)`, using `(panel,u,v)` for surfaces and `(x,y,z)` for gas. Reverse/shuffle operate separately within the two node classes. Shuffle uses the fixed xorshift32 seed 73013 and the frozen Fisher–Yates implementation. The rigid case applies `Rz(pi/7)*Rx(pi/5)` then translation `[1.25,-.7,2.1]`; initial temperature is transported as a scalar, not re-evaluated from transformed world coordinates.

Coincident splitting divides the parent's area or volume among its children, preserving capacity-per-measure, temperature, anchor identity, and total capacity. Splitting changes neither the represented geometry nor material. Nonuniform splitting challenges local weighting; it does not change physical vegetation/fuel density. Exact splitting is an algebraic invariance check, not a real reconstructed-PLY experiment.

## Independent references and gates

The independent Python audit reconstructs conductances from the saved input geometry, capacities, `h`, and `beta`; it does not accept the runtime edge list as the reference. It may then compare that independently constructed graph with the exported graph.

For the conservative graph, let `C` be diagonal capacity and `L` the symmetric weighted graph Laplacian. The exact solution of the **spatially discrete, continuous-time ODE** is obtained using the symmetric matrix `B=-C^(-1/2)*L*C^(-1/2)` and `T(t)=C^(-1/2)*exp(B*t)*C^(1/2)*T(0)`. This exact finite-graph solution is not a continuum truth. The two-node pair additionally has an analytic capacity-weighted equilibrium and exponentially decaying temperature difference with rate `G*(1/Cs+1/Cg)`.

Separate from that temporal reference, the audit independently reproduces the actual declared Euler substeps and checks the exported numerical trajectory. These are different tests: matching Euler verifies implementation; approaching the matrix exponential verifies temporal refinement for this finite graph.

Hard criteria, fixed before formal outcomes:

- Conservative relative total-energy drift and signed-transfer ledger residual are at most `1e-12`, with reference scale `max(abs(initial total energy),1)`. Capacity/total-energy matching between equivalent representations uses relative `1e-12`.
- Every conservative temperature stays within the initial global minimum and maximum with `1e-9 K` numerical tolerance, including the stiff case. No clipping may manufacture this result.
- Independent actual-substep Euler maximum absolute temperature discrepancy is at most `1e-9 K`.
- Every child in split/order/rigid-transform cases has temperature discrepancy from its unsplit common anchor at most `1e-9 K` at all matching outer checkpoints. This checks individual child temperatures, not only their weighted mean. Report actual maxima; do not require bitwise identity across floating accumulation orders.
- For both the pair and base corner, final capacity-weighted RMSE against the finite-graph matrix-exponential solution must strictly decrease from `dt=1/30` to `1/60` to `1/120`. Report errors, error ratios, and actual substep schedules. If automatic substepping makes schedules equal, mark them non-independent and do not claim refinement from those runs. No post-outcome timestep or threshold adjustment is allowed.
- The stiff case must use more than one substep per outer step; it tests CFL exposure, extrema/energy, and independent Euler correctness. It does not carry an additional continuous-solution accuracy threshold. The `.1` outer step was fixed before formal execution from the analytic rate: `beta=100` with `dt=1/60` would not activate substepping, whereas `.1` requires four substeps under the declared fixture.

Capacity-weighted RMSE is `sqrt(sum_i(C_i*(Ti-Tref_i)^2)/sum_i C_i)`. The one-sided control is excluded from conservative-energy/maximum-principle success claims; its drift and altered temperatures are reported explicitly. A valid negative control can execute successfully while violating the conservative physical contract. It cannot make the conservative method novel or establish superiority over a fair two-way baseline.

Spatial refinement is descriptive: independently solve the exact finite graph at each n, compute capacity-weighted surface and gas mean temperatures, and report differences relative to n=6. This isolates temporal integration error but does not make n=6 a continuum reference. No spatial monotonicity or continuum-convergence gate is imposed.

## Reproducibility and interpretation

Freeze source hashes, design, full scene inputs, invocation, environment, and audit scripts before formal execution. Record all 21 outcomes, including the negative control, rather than stop after an appealing subset. Software execution, evidence completeness, numerical-contract success, and any later research hypothesis are separate statuses.

Passing supports the fixed-model thermal implementation, finite-capacity accounting, tested representation symmetries, and observed temporal refinement. It does not establish real-world temperature prediction, combustion correctness, conservation through future particle creation/removal, inference of physical area from visual Gaussians, efficient VPM integration, or a SIGGRAPH contribution. A later method must still compare against independent physical surface samples with the same renderer and comparable inputs/budgets.
