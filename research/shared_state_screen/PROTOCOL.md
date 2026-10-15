# P7: shared visual thermal states versus an independent material proxy

Protocol candidate, 2026-10-15. Written before numerical outcomes. Root has approved the prescribed-exchange scope, the 2% quality / 0.5% reference / 20% cost-screen thresholds, and the response-RMS, five-step replay, and optimistic shared-alias rules below. Implementation review and an external source freeze are still required before execution. No existing repository or earlier evidence is modified by this document.

## 1. Question and limits

Does one material-temperature state per visual sample provide a necessary advantage over an independent, smaller material quadrature for this particular local heat-response task?

The tested candidate is the existing architectural choice: 8192 visual samples also hold 8192 material temperatures. The comparison is a standard fixed 512-state material proxy. Neither is a new heat solver. Both use the same exact compact-support exchange law and the frozen P6 spatial-hash implementation. A proxy with the same positions, measures, states, and arithmetic as the shared representation would be mathematically identical; this experiment instead varies the material-state resolution and accounts for the actual display-mapping work.

Gas paths are prescribed analytically. Gas temperatures respond to heat exchange, but temperatures do not affect the paths. There is no VPM, velocity solver, buoyancy, pressure, combustion, mechanical solid boundary, appearance reconstruction, or renderer in P7. “CPU to display-temperature buffer” is the measured scope; it is not frame latency or FPS. The result is one development-scene architecture screen, not evidence of a new method or SIGGRAPH readiness.

## 2. Fixed development scene

All coordinates are metres, times seconds, temperatures Kelvin, capacities J/K, and heat transfers joules. Parameters are deliberately authored toy values, not calibrated material data.

There are two stationary thin thermal panels. They exchange heat with gas but do not obstruct its prescribed path. They have no panel-to-panel or within-panel conduction. Their line of geometric intersection has zero area and no special coupling.

| Panel | Fixed coordinate | First in-plane coordinate | Second in-plane coordinate | Area |
|---|---|---|---|---|
| p0 | x = 0.25 | y in [0.1, 0.7] | z in [-0.3, 0.3] | 0.36 |
| p1 | z = 0.25 | y in [0.1, 0.7] | x in [-0.3, 0.3] | 0.36 |

For a panel resolution n, indices j,k run from 0 through n-1. Coordinates are y = 0.1 + (j+0.5)*0.6/n and w = -0.3 + (k+0.5)*0.6/n. Panel p0 maps to (0.25,y,w); p1 maps to (w,y,0.25). Every node represents area A = 0.36/(n*n), has capacity density c_A = 2 J/(m² K), capacity C = A*c_A, and initial temperature 300 K. IDs are `p{panel}-j{j}-k{k}`. Ordering is panel, j, k, ascending. No area is inferred from opacity, covariance, or sample count alone.

There are exactly 32 gas parcels, indexed ix=0..3, iy=0..1, iz=0..3, in ix/iy/iz order with IDs `g-ix{ix}-iy{iy}-iz{iz}`. Their initial positions are

```
x0 = 0.2 + (ix - 1.5)*0.05
y0 = 0.1 + (iy - 0.5)*0.05
z0 =       (iz - 1.5)*0.05
```

Each has volume V = 0.05³ = 0.000125 m³, capacity density c_V = 30 J/(m³ K), capacity 0.00375 J/K, and initial temperature 600 K. Total gas volume is 0.004 m³ and gas capacity is 0.12 J/K. Total panel capacity is 1.44 J/K; initial thermal energy is 504 J and initial excess energy above 300 K is 36 J, up to floating-point accumulation. No parcel is born, removed, split, or clamped.

The common analytic velocity is u(x,y,z)=(-Omega*z,U,Omega*x), with Omega=pi/2 s^-1 and U=0.4 m/s. Every query position is recomputed from its original position:

```
x(t) = x0*cos(Omega*t) - z0*sin(Omega*t)
y(t) = y0 + U*t
z(t) = x0*sin(Omega*t) + z0*cos(Omega*t)
```

This field is divergence-free, but the experiment does not solve a fluid equation. The domain is unbounded for paths; panels have only their finite authored support. Outside the kernel support there is no thermal exchange. No artificial ambient reservoir, periodic wrapping, cooling, or forcing is added.

## 3. Common exchange and time schedule

Use the P6 `pack`, exact `buildGraph(...,'hash')`, and synchronous `exchange` arithmetic, pinned by source SHA. Do not substitute the all-pairs builder as a slow shared-state competitor. A new driver may update packed gas positions and consume temperatures between calls; it must not change the kernel, summation, CFL, or state-update arithmetic. Any necessary core adaptation must be a reviewed wrapper or a separately pinned copy, with a regression against the frozen P6 core, not an edit to P6 evidence.

Parameters are h=0.12 m, beta=2 W/(m² K), safety=0.9, and maxSubsteps=100000. For surface i and gas j,

```
r = sqrt((dx*dx + dy*dy) + dz*dz)
G_ij = beta*A_i*V_j * (3/(pi*h*h*h)) * (1-r/h), if r<h; else 0
```

Use P6's actual multiplication order `beta*A_i*V_j*(normalization*(1-r/h))`. Pair ordering is ascending surface index, then ascending local gas index. Both endpoints receive the same Q with opposite signs. Kahan per-node accumulation reads old temperatures for all edges before any temperature changes. There is no temperature clipping.

An outer step uses s=max(1,ceil(dt*max_i(sumG_i/C_i)/0.9)) substeps, fixed geometry throughout that outer step, and substep size dt/s. More than 100000 or unsafe/nonfinite counts are errors, never truncations.

The development horizon is exactly 1 s. Candidate arms use rate=120, dt=1/rate, and exactly rate outer steps. Integer step index determines t_n=n/rate; time is not incrementally accumulated. Each outer step does, in this order:

1. Evaluate all gas positions from the analytic path at t_n, using common original parcel coordinates.
2. Build a fresh exact graph at those positions, retaining the current temperatures and fixed capacities.
3. Execute one thermal step of dt, including all required CFL substeps, with that graph frozen.
4. Evaluate gas positions at t_(n+1) for the accepted-state record. There is no approximate trajectory integration.
5. Produce the 8192 display temperatures from the new surface temperatures.

This is a declared first-order frozen-geometry thermal discretization. Time refinement tests this discretization. It is not a continuously updated graph inside each CFL substep. Geometry must not be cached across outer steps. Each arm uses the same schedule, including reference arms at their declared finer rates.

## 4. Compared representations and display mapping

The display grid is always two 64x64 midpoint grids on the panels, in the same panel/j/k order. The comparison consumes temperature values, not rendered colors; color-map choice cannot change the error metrics.

| Arm ID | Thermal n per panel | Surface states | Rate | Purpose |
|---|---:|---:|---:|---|
| dev-shared64-r120 | 64 | 8192 | 120 | Existing shared-state architecture |
| dev-proxy16-r120 | 16 | 512 | 120 | Standard independent material proxy |
| dev-ref128-r120 | 128 | 32768 | 120 | Coarse numerical reference |
| dev-ref128-r240 | 128 | 32768 | 240 | Temporal reference check |
| dev-ref256-r240 | 256 | 131072 | 240 | Spatial reference check / nominal final reference |
| dev-ref256-r480 | 256 | 131072 | 480 | One conditional temporal check only |

The first five arms are the complete initial quality plan; reference and signal validation gate execution of the two candidate arms. The sixth is allowed only by Section 6. No proxy budget scan, parameter tuning, extra surface refinement, or 512² panel is part of this first screen.

All nonidentity display maps use ordinary separable bilinear interpolation of the panel's cell-centred temperatures. For display axis index a=0..63 and thermal resolution n, compute q=(a+0.5)*n/64-0.5. If q<=0 use (lo,hi,f)=(0,0,0); if q>=n-1 use (n-1,n-1,0); otherwise lo=floor(q), hi=lo+1, f=q-lo. Thus the outer half-cell strip uses constant extension of the nearest midpoint, not extrapolation or a hidden boundary temperature.

Use the same 64-entry lookup table for both axes and both panels: lowerIndex Uint32 plus fraction Float64, with hi derived as min(lo+1,n-1). This is 768 typed-array bytes, not an artificial 8192x4 index/weight table. Four temperatures are combined by horizontal lerps followed by the vertical lerp, with fixed left-associated scalar arithmetic:

```
a0 = (1-fk)*T[j0,k0] + fk*T[j0,k1]
a1 = (1-fk)*T[j1,k0] + fk*T[j1,k1]
display[j,k] = (1-fj)*a0 + fj*a1
```

At n=64, the shared arm may return a view of its own surface-temperature array. Do not impose a copy on it. The proxy and references fill an 8192-entry Float64 display buffer. Mapping setup is once per run; actual mapping is every outer step. A proxy's interpolated display temperatures do not feed back into the thermal state and are not treated as a conservative heat reservoir. Physical heat diagnostics always use actual thermal states and capacities.

## 5. Recorded observables and quality metrics

Comparison times are t=m/120 for every integer m=0..120. A rate-240/480 reference selects every second/fourth accepted state, never interpolates in time. Persist all accepted thermal states for independent auditing as specified in Section 8; the following metrics use the common comparison times.

Each panel is partitioned into a fixed 4x4 set of equal physical regions using its normalized y and w coordinates. All registered thermal resolutions are divisible by four. Assign node (j,k) to region (floor(4*j/n),floor(4*k/n)); this agrees with its cell's region and does not depend on node index parity. Each region has area 0.0225 m². Region boundary ties use half-open intervals except the final upper edge.

For each panel and each of its 16 regions, define net cumulative heat

`Q_R(t) = sum_{i in R} C_i*(T_i(t)-300)`.

There is no source or intra-panel conduction, so this is also the net signed heat exchanged with gas. It is not a sum of absolute fluxes. Record all 2 panel and 32 region curves, full gas temperatures, display temperatures, actual thermal peak rise, total energy, and pair-exchange ledgers. Gas-temperature errors are reported as additional diagnostics, not silently used to choose a different decision rule.

For an arm A compared with reference B, compute these three primary errors across all 121 times:

1. **Panel response:** max over panels and times of |Q_A-Q_B| divided by max over reference panels and times of |Q_B|.
2. **Regional response:** max over all 32 regions and times of |Q_A-Q_B| divided by max over reference regions and times of |Q_B|. The panel total is never used to dilute a regional error.
3. **Display:** max_time area-RMS(display_A-display_B) divided by max_time area-RMS(display_B-300). Both maxima are over the 121 comparison times. All 8192 display sites have equal area 0.36/4096, but compute/store the declared area weights. Thus the denominator is the magnitude of the reference response field, not its peak temperature and not the 300 K background.

Also report per-panel/per-region errors, signed response differences, peak error, gas-temperature max/RMS error, and the above display metric over time. The former peak-rise-normalized display error is retained only as a diagnostic and never substituted into a gate. A 300 K background is not an error-normalization denominator. For panel or regional responses, a zero denominator with zero numerator yields zero and a zero denominator with nonzero numerator yields an invalid metric. Display reference-RMS must be strictly positive; its zero-denominator case is invalid regardless of numerator.

The candidate quality gate requires all three primary errors <=0.02 separately for shared64 and proxy16. No averaging across metrics or scenes can turn a failure into a pass. A reference maximum display rise <1 K is `INSUFFICIENT_SIGNAL`; retain the data but do not claim quality or cost success. The reference display-RMS, panel, and regional denominators must all be strictly positive. The reference comparisons in Section 6 use this same response-RMS display metric with the unchanged 0.005 threshold.

Execution validity is separate: all temperatures finite and within [300-1e-9,600+1e-9] K; each step's CFL <=0.9+1e-12; actual cumulative total-energy drift and ledger debit/credit mismatch each <=1e-12*max(1 J,|E_initial|); no cap, retirement, clipping, external heat, or undocumented time/geometry change. Independent metric recomputation must not trust producer pass flags.

## 6. Reference acceptance and fixed resource ceiling

References are numerical quadratures, not exact continuum truth. Their error checks apply to the task observables in Section 5, not an unproved bound on every continuum temperature.

First execute R0=ref128-r120, R1=ref128-r240, and R2=ref256-r240. Compute all three primary errors for R0 versus R1, R1 versus R2, and R0 versus R2; the second argument supplies that pair's denominators. The spatial comparison R1 versus R2 must pass <=0.005 for every metric. If it fails, mark `REFERENCE_INVALID` and stop this screen; increasing n beyond 256 or changing h is forbidden.

If all three pair comparisons pass <=0.005, accept R2 as the reference. If the spatial comparison passes but either R0 temporal/combined comparison fails, permit exactly one additional run R3=ref256-r480. Accept R3 only if both R2 versus R3 and R1 versus R3 pass <=0.005 for every metric. Otherwise mark `REFERENCE_INVALID`. There is no further fallback. This rule is fixed before seeing either candidate's errors.

Record all pair errors and the selected reference ID. The 0.5% criterion is a prespecified numerical screening tolerance one quarter of the 2% candidate threshold, not a rigorous continuum error certificate. Do not relax it after outcomes. No reference or candidate parameters may be selected by which arm wins.

Only after a reference is accepted and signal is sufficient are both candidate quality arms evaluated against it. Any execution or reference failure blocks timing claims. A proxy quality failure is a valid scientific negative, not an execution exception; retain the complete two-arm quality evidence if it has been executed.

## 7. Conditional cost and storage screen

Timing starts only if reference validation, signal validation, and both candidate quality gates pass. There is no reference timing competition and no timing of an inaccurate candidate to advertise speed.

Use one untimed full trajectory per candidate as warmup, then six fresh-state paired blocks. Orders are [shared,proxy], [proxy,shared], repeated three times. This is 12 measured trajectories, with exact same inputs and 120 steps each, within one Node process. These are not independent process trials or a statistical confidence interval. Use `node --expose-gc`; release previous run state and force GC outside each timed trajectory. No other heavy workload runs concurrently. Incidental GC inside a measured trajectory is included.

The primary interval starts before packing/allocating the arm's thermal state and constructing its display map, and ends after the final display-temperature buffer is available. Frozen authored input records and module loading are already available. It includes initialization, graph/index/candidate allocation and construction at every step, all exchange substeps and existing energy/flux ledgers, exact gas-path evaluation, display mapping, and necessary control flow. It excludes validation hashes, large history copies, metric reductions, JSON/binary compression, file I/O, and independent auditing. Disable archival observers during timing; do not disable physical validation already inside P6 exchange. No production result is transferred from an earlier quality run.

The validation boundary is explicit: quality runs and the independent auditor scan the full temperature vector for the [300,600] K maximum principle. Timed runs retain all original P6 per-node finite/energy checks but add only O(1) checks of CFL, cumulative energy, and opposite-flux ledgers. They do NOT repeat the quality-only whole-vector `T.some` range scan or perform archival reductions. Take initial energy from the first exchange's existing `Ebefore.total`; do not add a separate setup energy-reduction pass. Endpoint bitwise comparison with the quality run verifies that this observer difference leaves the produced state unchanged. A separately recorded `validationMs`, if present, measures only these scalar ledger checks, never an additional O(N) audit whose cost could inflate an apparent architecture advantage.

Record setup, analytic-path update, graph build, exchange, display mapping, and whole-trajectory wall time. Stage timers are diagnostic; the enclosing whole-trajectory interval is primary and includes any unattributed control/overhead. Take no per-edge timer. Hash endpoint temperatures only after the enclosing interval and require them to match the quality run. No trajectory-history observer or intermediate hash runs inside the timed interval. Use a separate untimed replay for per-step deterministic validation if needed.

For paired block b, let r_b=proxy whole-trajectory time / shared whole-trajectory time. Cost success requires median(r_b)<=0.80 and at least five of six r_b<1. Store every raw time and ratio, median/min/max, and separate setup versus recurring-step totals. These are engineering margins, not significance levels. Do not rerun until a favorable ratio appears.

Storage reporting must distinguish actual owned typed-array payload from unknown JS/Map allocator overhead. Count unique ArrayBuffers, never views twice. Shared temperatures may alias their display buffer. The proxy may use the compact separable lookup above. Include packed positions, measures, capacities, initial/current temperature buffers actually retained, display output, mapping, CSR, degree arrays, exchange scratch, and candidate-cache typed payload. Report persistent bytes and maximum algorithm-owned array payload over build/exchange phases, without calling these process peak RSS. Common input JSON and archival data are outside the algorithm-memory comparison on both sides. Unknown object/index heap bytes remain unknown, not zero.

The implementation uses an implicit visual grid, with no additional common visual-position buffer. Report the actual additional typed-array payload for each arm, then also model an optimistic shared baseline that can reuse positions already present in a renderer: subtract exactly 8192*3*8=196608 bytes for the shared surface positions, once, from both its persistent and maximum-phase totals. This is a separate hypothetical reuse adjustment, not an implemented renderer or a second removal of already-excluded bytes. The actual shared totals must include this complete surface-position payload before the subtraction and each adjusted total must be nonnegative; otherwise accounting is invalid, not silently clamped. Do not subtract gas positions or any proxy physical positions. No other common-geometry deduction is allowed in these totals. Actual aliasing of temperature/display views is already handled by unique-buffer accounting and is not subtracted again.

The strict first-screen memory gate requires BOTH proxy actual additional persistent bytes <= shared optimistic alias-adjusted persistent bytes AND proxy actual maximum-phase payload <= shared optimistic alias-adjusted maximum-phase payload. Report the unadjusted comparison too, but it cannot replace this stronger gate. If the layout cannot support this explicit accounting, memory is unresolved and strict dominance is not declared. This models the shared architecture's best-case reuse opportunity; it does not measure graphics memory or establish process peak RSS. An observed RSS measure may be supplementary but cannot replace clear ownership accounting.

## 8. Evidence, auditing, and no-overwrite contract

Source freeze includes protocol, authored design, driver, tests, metric code, independent auditor, and exact P6-core provenance. Record SHA256 before and after every formal run. No formal output may overwrite a prior nonempty directory. Manifest explicitly separates execution validity, reference acceptance, candidate quality, conditional timing status, and architecture decision. It lists expected and completed IDs and why any conditional run did not occur.

Quality evidence uses streamed binary/gzip, not huge nested JSON temperature arrays. For each arm, store every accepted outer-step temperature vector, including initial state, in canonical [all surface nodes, all 32 gas nodes] order as Float64 little-endian. Preserve every native-rate accepted state: 121, 241, or 481 vectors as appropriate. A sidecar records node ordering, rate, vector count/length, byte order, uncompressed byte count and SHA256, compressed file byte count and SHA256. Gzip must round-trip to the exact raw bytes. Streaming history must not require all reference frames resident in memory. No full graph-edge history is required.

Also retain display values and all observables at the 121 common times, initial authored measures/positions/capacities, per-outer-step analytic time, graph edge/degree/work summaries, substep count, and energy/flux ledgers. Full per-node degrees may be streamed separately if needed by the independent audit; do not embed them as repeated enormous JSON objects. Save all 32 gas positions at every accepted outer-step state including the initial state. The independent auditor regenerates the analytic coordinates from original positions and integer-index times and requires every saved coordinate to agree within an absolute 2e-14 m tolerance. Saved positions at t_n are the actual frozen-geometry inputs for the step ending at t_(n+1); the replay below uses these saved coordinates after their independent path check, rather than introducing cross-language trigonometric differences into the exchange oracle.

With no optional R3, raw temperature history is bounded by the five declared arms; adding R3 adds exactly 481*(131072+32)*8 bytes before compression. Highest surface resolution is always 256² per panel. Do not add larger refinement or extra scenes because the reference is inconvenient. Physical graph data are temporary; no per-frame dense all-pairs matrix is retained.

Before formal execution, tiny tests cover identity and boundary-clamped bilinear mapping, constant/linear in-plane fields where applicable, patch membership/area, analytic path times shared across rates, old-temperature synchronous exchange, no reset between steps, energy, and deliberate metric/reference-gate failures. A reduced fixture may be independently all-pairs replayed for every step. Formal auditing reconstructs geometry/capacities, checks state and energy continuity from streamed histories, independently recomputes all observables/reference decisions/cost ratios, and verifies final states against the recorded ledgers.

For EACH completed quality arm, independently replay exactly five predeclared accepted steps with 1-based ending indices [1,rate/4,rate/2,3*rate/4,rate]. All registered rates are divisible by four. For ending step k, read the complete stored old temperature vector at k-1 and the saved, analytically validated gas positions at (k-1)/rate. Enumerate all surface-gas pairs independently, recompute all conductances and maxRate, derive the CFL substep count, and synchronously reproduce the full new temperature vector through every required substep. Require exact substep-count agreement, maxCfl <=0.9+1e-12, maxRate agreement within absolute 1e-12 plus relative 1e-12, and maximum absolute new-temperature error <=1e-9 K. Also verify the selected step's energy and flux ledger against this replay with the same declared energy tolerance. This is five-step replay per arm, not independent numerical replay of every step. All-step geometry, state coverage, metric, and energy checks remain separate. Reuse P6's audited exact core instead of treating new test counts as a research result.

## 9. Decisions and gated held-out scene

Possible decisions are explicit:

- `EXECUTION_INVALID`: code/provenance/physical bookkeeping failed; no scientific comparison.
- `REFERENCE_INVALID` or `INSUFFICIENT_SIGNAL`: no architecture winner; stop this first screen without tuning.
- `PROXY_QUALITY_STOP`: proxy512 failed at least one 2% metric. This does not establish shared-state superiority over a stronger or adaptive proxy; no cost-success claim.
- `SHARED_QUALITY_STOP`: shared8192 failed its quality gate. Do not claim a quality-matched speed comparison.
- `QUALITY_PASS_NO_STRICT_DOMINANCE`: both accurate, but proxy failed the fixed cost or storage screen. Shared identity still is not a novel contribution; report the measured tradeoff only.
- `PROXY_STRICT_FIRST_SCREEN`: both accurate and proxy meets cost/storage criteria. Stop the necessity claim that local thermal state must be tied one-to-one to visual samples; proceed only to the predefined held-out confirmation below.

The held-out scene is defined now but not executed unless `PROXY_STRICT_FIRST_SCREEN` holds and root authorizes the next run. Rotate every original gas x0/z0 coordinate by phi=pi/3 using the same positive rotation convention, and add 0.1 m to y0. Panels, capacities, temperatures, h, beta, budgets, display map, paths, horizon, rates, reference-selection/resource ceiling, metrics, and cost thresholds remain identical. It tests another contact history, not a different physical model. Use IDs with a `heldout-` prefix and the same arm suffixes. Do not alter the held-out scene after development results.

A successful held-out result would support adopting a standard independent proxy for this controlled task, not a novel Gaussian-native algorithm. Failure would limit the development observation rather than justify another tuned scene. A fixed proxy's failure never counts as beating an unimplemented adaptive proxy. No claim about realistic PLY scenes, full fluid dynamics, renderer cost, or conference acceptance follows from this screen alone.
