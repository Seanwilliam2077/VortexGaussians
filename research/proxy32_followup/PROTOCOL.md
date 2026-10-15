# P7b: one fixed 2048-state material-proxy follow-up

Protocol approved by root, 2026-10-15. This is registered **after observing P7**, before any proxy32 result. Scope, thresholds, parent reuse/re-audit, and the single-follow-up stop rule are approved. New source review, tests, independent-auditor review, and an external freeze are still required before execution. P7 and all earlier files remain immutable.

## 1. Why this follow-up exists and where it stops

P7's fixed proxy16 (512 surface temperatures) passed panel and regional response limits but failed the display limit. Its panel, regional, and display errors were respectively 0.7894862252%, 1.7807099119%, and 3.5573231694%, against the unchanged 2% limit. Shared64 (8192 surface temperatures) passed at 0.5329596493%, 0.6609144774%, and 0.7736385908%. The conditional reference rule accepted R3. P7 correctly skipped timing; its scientific decision remains `PROXY_QUALITY_STOP`.

P7b tests exactly one stronger, standard baseline: proxy32, with 32x32 material temperatures on each of the same two panels, hence 2048 surface states and 32 gas states. Its output remains the same 8192-site display-temperature buffer. The experiment changes only this material resolution. It does not introduce a new solver, adaptive method, reconstruction, interpolation, or physical claim.

This is a post-result follow-up, not a previously registered P7 arm or a confirmatory test independent of P7. No result may be relabelled as the original P7 outcome. There is no proxy48, proxy64, further budget scan, changed interpolation, changed kernel, new scene, or relaxed tolerance in this screen, regardless of outcome. This single follow-up ends the development-scene budget screen. Its failure would not prove that tying thermal state to visual samples is necessary; its success would not establish a new research contribution.

## 2. Immutable parent evidence and authenticated reuse

The external parent artifact is:

```
outputs/p7/VortexGaussians-P7-shared-state-screen.zip
SHA256 e09b48282f81034a724db19dfb29f4b6bd7eacdde92b3f963e90f66ae746b32d
bytes 254696730
members 34
source checkpoint 4dd298d597a88f31d14e6485f763f20e5a0ff32a
```

The ZIP SHA is the primary immutable identity; the checkpoint records provenance and does not substitute for byte authentication. The parent protocol SHA is `ba4afa4b0d72dac0ec38190a11b75b3c4ab18e07b92999c161a7896a2eb99211`. Its frozen independent auditor SHA is `8586760bb47bbce84fd35aee55e0c62873d9ad3d17d9a281df287eeecd336e20`.

P7b reuses exactly the accepted parent reference `dev-ref256-r480` and parent quality arm `dev-shared64-r120`. The reference-selection decision is fixed to R3. No reference is regenerated, reselected, truncated, or chosen by proxy32's errors. The parent proxy16 failure remains present in provenance and the report. R0/R1/R2 remain available through the complete parent archive for auditing the original reference decision.

Before the new run, create and freeze a baseline pin manifest containing the archive identity, original parent manifest/freeze/audit file hashes, all eight parent source hashes, the two reused case JSON hashes, their compressed and raw history hashes, and their input/endpoint identities. Authenticate the complete parent archive and every reused dependency against these pins. Never update a pin to match a changed file or silently regenerate missing parent trajectories.

The reused case identities recorded by the parent manifest are:

| Artifact | SHA256 |
|---|---|
| R3 JSON | `c8d1908ab6b0f3e681ce335b56ee03da8c2b887aec9541dc4676123962609fd8` |
| R3 compressed temperature history | `c204691aa0a12d9155a2b41f52ea62af405528d21540a1805e912dd64923d532` |
| R3 uncompressed temperature bytes | `d198b417e09247d6e534bebff54f58549e32ccd4f19a26f3ce0b7e420095ada5` |
| Shared64 JSON | `1d508d14a14f7e3faa6437934e377d7eb6c41be6dad69f92d418cd48d6995f66` |
| Shared64 compressed temperature history | `8b4d8436d14b92fbcaf89879fb39335710c206da464edbade8fb6b824848bb9c` |
| Shared64 uncompressed temperature bytes | `c36fc0c821c48144254b609241dabd75e8992c5a5024ffc2f659245f5f1d2bc6` |

The new independent auditor must actually invoke the authenticated frozen P7 auditor on the complete extracted parent data, with the original source directory and freeze, writing a **new** audit result. It must require that audit to pass and to reproduce the accepted R3 reference, shared quality pass, proxy16 quality stop, and skipped timing. Reading an old `passed` flag alone is insufficient. This parent re-audit may run after P7b timing to avoid resource interference; until it succeeds all new findings are provisional. It does not rerun physical trajectories and its checks must be labelled inherited/revalidated, not new P7b simulations.

The new package may depend on the above immutable external ZIP rather than duplicate all parent histories. Reproduction instructions must name its exact filename/SHA, verify it, extract it without altering the original archive, and resolve all imports/inputs from that authenticated extraction. A workspace copy may be used only after exact hash agreement. Missing or mismatched dependencies are `PARENT_EVIDENCE_INVALID`, never a quality failure or an invitation to recompute a favorable parent.

## 3. The only new quality arm

```
{ id: 'dev-proxy32-r120', n: 32, rate: 120, role: 'proxy' }
```

There is one new quality trajectory, 120 outer steps over exactly 1 s. Shared64 and R3 quality trajectories are inherited, not counted as newly executed arms. There are 121 comparison times, t=m/120, m=0..120. R3 uses its already saved every-fourth accepted state at these times.

Use the original P7 exported `qualityArm`, `timedArm`, authored-input, wrapper, and metric functions directly from authenticated parent modules, or use byte-identical authenticated copies with unchanged relative dependencies. A new driver defines the proxy32 arm separately; do not edit the parent's `ARM_DEFINITIONS` or other files. Parent source hashes include:

| Module | SHA256 |
|---|---|
| `design.mjs` | `b1ef9b83df7ccd392d8fb341dd09f3de6fa74b90c55c55ed0fc4aa523544281b` |
| `wrapper.mjs` | `5e346b1cdbf5899f60ddda7fd0e46f1b078202423a386dd5c6857895eab6734f` |
| `metrics.mjs` | `80335f32d46b2c1e5110dbc80cd763d1c27b14c410b8049b0acc142cba16f1a8` |
| `run.mjs` | `e8a5b57445e7f88f800a4fd572ea738d03471ec27e889dd981518ec54d823629` |
| `p6-core.mjs` | `8434987b77928c4346b73ecd9fee88cbbb4c7444d232f9cfd34c4f652019a5fc` |

P7 Sections 2--8 remain normative except for the explicitly replaced arm and inherited/new evidence distinction. In particular, the following are unchanged:

- Two area-0.36 panels: p0=(0.25,y,w), p1=(w,y,0.25), y in [0.1,0.7], w in [-0.3,0.3]. At resolution n use cell midpoints, area 0.36/n², capacity density 2, and initial temperature 300 K. Canonical ordering is panel/j/k.
- The same 32 gas parcels on the 4x2x4 initial grid: x0=0.2+(ix-1.5)*0.05, y0=0.1+(iy-0.5)*0.05, z0=(iz-1.5)*0.05. Each volume is 0.05³, capacity density 30, and initial temperature 600 K. Capacity, source strength, IDs, and ordering do not change with material resolution.
- Prescribed paths x=x0*cos(Omega*t)-z0*sin(Omega*t), y=y0+0.4*t, z=x0*sin(Omega*t)+z0*cos(Omega*t), Omega=pi/2. Recompute from original positions at integer-index times; no trajectory integration or heat feedback to velocity.
- h=0.12, beta=2, safety=0.9, maxSubsteps=100000; the identical strict-support exact spatial-hash graph and symmetric synchronous P6 exchange arithmetic. No surface/surface or gas/gas edge, birth/death, source, cooling, clamp, combustion, VPM, or mechanical obstruction.
- Each step builds the fresh graph at t_n, advances thermal state through all CFL substeps with that geometry frozen, evaluates the accepted gas positions at t_(n+1), then maps the new surface temperatures to the common display grid. No reset of working temperature between steps.
- Identical midpoint bilinear mapping with constant nearest-midpoint extension, the compact 64-entry lower-index/fraction table, and horizontal-then-vertical scalar arithmetic. The shared arm aliases its current temperature array; proxy32 fills an 8192-entry Float64 display array. Interpolated values never feed back into thermal state.

No reference/signal threshold is re-estimated or relaxed. The inherited parent reference must still satisfy its original 0.5% acceptance checks and signal checks under the frozen parent audit.

## 4. Quality, state evidence, and independent replay

Recompute proxy32 and inherited shared64 comparisons against the same R3 observations. Require each arm's three primary errors to be <=0.02 independently:

1. Panel: maximum absolute panel heat-response difference over all panels/times, divided by maximum absolute reference panel heat response.
2. Regional: the corresponding maximum over the same 32 fixed physical regions, divided by maximum absolute reference regional heat response.
3. Display: max_time area-RMS(candidate-reference) divided by max_time area-RMS(reference-300 K), on all 8192 display samples at the 121 common times.

Heat response is the signed sum C_i*(T_i-300), not absolute flux. The reference peak display rise must be >=1 K and display-RMS/panel/regional denominators must be positive. Peak-rise-normalized display error remains diagnostic only. Store all original additional diagnostics; never substitute a favorable one for a failed primary metric. Relative errors are stored as fractions, with percentages used only in presentation.

Quality validity remains finite T within [300-1e-9,600+1e-9] K, maxCfl<=0.9+1e-12, total energy drift and opposite-flux mismatch <=1e-12*max(1,abs(E_initial)), and no provenance or schedule failures. Keep scientific quality failure separate from execution validity.

Persist the new proxy32 initial and every accepted temperature vector: Float64 little-endian, canonical surface-then-gas order, vector length 2080, count 121, raw bytes 2013440, streamed gzip with raw/compressed bytes and SHA256. Preserve all 121 common observations, all 120 step ledgers/graph summaries, and actual geometry/accepted gas positions. Retain initial input, endpoint hashes, memory accounting, and authored-input SHA before/after.

The new independent audit verifies all saved gas coordinates against the analytic path at the correct time within 2e-14 m, and verifies previous accepted/current geometry continuity. It checks every saved state's coverage, finite range, energy, observations, and quality metrics independently. It additionally replays exactly five ending steps [1,30,60,90,120] from the complete saved previous temperature vector and analytically validated saved geometry. Use independent all-pairs conductances and synchronous exchange through the complete CFL schedule. Require exact substep count, maxRate tolerance 1e-12 absolute plus 1e-12 relative, maximum new-temperature error <=1e-9 K, and the original ledger tolerances. This is five new full-step replays, not a claim of independently replaying every new step.

The original R3/shared history, source, raw hashes, and parent reference/quality decisions are authenticated and re-audited through Section 2. Do not inflate the new trajectory or replay counts by counting parent trajectories again. The new manifest distinguishes `inheritedQualityIds`, `newQualityIds`, actual new execution IDs, required IDs, and conditional timing status/reason. The expected new quality set is exactly [`dev-proxy32-r120`].

## 5. Conditional fresh paired timing

If proxy32 fails any 2% gate, retain its full quality evidence and skip timing. A mismatch in the inherited shared quality or reference is an evidence error, not permission to change the reference. Only a valid proxy32 quality pass plus the authenticated inherited shared/reference pass permits timing.

Both timing arms are freshly executed in the same new Node process: shared64 and proxy32. Never reuse historical P7 CPU times, substitute a historical shared denominator, or time only the new arm. Use `node --expose-gc`, one complete untimed warmup per arm, then six fresh-state paired blocks in the exact order [shared,proxy], [proxy,shared], repeated three times. This is 12 measured trajectories, not ten and not independent process trials. Release prior state and force GC outside each trajectory; do not run another heavy workload concurrently. Record all raw times without selective reruns.

Use the unchanged parent `timedArm` and timing boundary. Whole-trajectory wall time begins before state packing/allocation and display-map setup, and ends after final display temperatures are available. It includes analytic paths, every fresh graph/index/candidate build, all thermal substeps, native P6 finite/energy checks, scalar CFL/energy/opposite-flux validation, display mapping, phase bookkeeping, and any incidental GC. It excludes authored-input creation, hashes, archival copies/observations, compression, file I/O, metric reductions, and independent auditing.

Do not insert a quality-only whole-vector temperature-range scan or extra setup energy reduction into timing. Initial energy comes from the first exchange's existing Ebefore.total. Stage times and scalar validationMs remain diagnostic; the enclosing interval, including unattributed overhead, is primary. The measurement is CPU to display-temperature buffer, not render time, full-frame latency, GPU time, or FPS.

Compute the endpoint temperature/display/position hashes outside the timer. Every shared warmup/measured endpoint must match the pinned P7 shared quality endpoint, and every proxy32 endpoint must match its new quality endpoint. Verify authored inputs and relevant memory accounting also agree. No archived production state may initialize a timed trajectory.

For each block r_b=proxy32 total time/shared64 total time. Cost passes only if median of the six ratios <=0.80 and at least five ratios are <1. Report every paired time, ratio, median/min/max, and setup versus recurring stages. These fixed engineering margins are not a statistical confidence interval.

## 6. Unchanged strong storage gate

Use the identical unique-ArrayBuffer accounting and report persistent payload plus maximum live build/exchange-phase payload for each arm. Include actual packed physical positions/measures/capacities/temperature, origins, owned display/map buffers, graph/degree arrays, candidate scratch/cache arrays, and exchange scratch. Do not double-count views or aliases. Unknown JS/Map heap remains unknown, not zero; these are not RSS measurements.

Report both actual shared totals and an optimistic shared baseline obtained by subtracting exactly 196608 bytes (8192*3*8) for potential reuse of the surface-position buffer in a renderer, once from persistent and once from maximum-phase totals. The actual layout must contain those surface-position bytes before the subtraction; both adjusted totals must be nonnegative. Do not subtract gas positions, proxy positions, or temperature/display aliases a second time. This remains a hypothetical renderer reuse allowance, not an implemented renderer or a timing modification.

Strict memory success requires BOTH proxy32 actual persistent bytes <= shared adjusted persistent bytes AND proxy32 actual maximum-phase bytes <= shared adjusted maximum-phase bytes. The inherited shared quality memory record may be reused after authentication, but fresh timing records must match its deterministic accounting. Report unadjusted totals too; they cannot replace the stronger gate.

The unchanged wrapper predicts 166912 persistent typed-array bytes for proxy32 and 395520 actual / 198912 adjusted persistent bytes for shared64. These are algebraic layout checks, not measurements or a prediction that the maximum-phase or timing gate will pass. Maximum-phase payload depends on the actual executed graph history and must be recorded, not inferred from node count alone.

## 7. Decisions and terminal scope

The final report must distinguish:

- `PARENT_EVIDENCE_INVALID` or `EXECUTION_INVALID`: dependency, source, schedule, or numerical bookkeeping failed. No architecture conclusion.
- `PROXY32_QUALITY_STOP`: at least one proxy32 metric exceeds 2%. No timing and no quality-matched speed claim. End this budget screen; do not try another proxy resolution or interpolation. This shows the limits of these two fixed proxy budgets on this task, not the superiority of shared state over every independent/adaptive proxy.
- `QUALITY_PASS_NO_STRICT_DOMINANCE`: both are accurate, but fixed paired cost or strong storage criteria fail. Report the tradeoff and end the budget screen.
- `PROXY32_STRICT_FOLLOWUP_SCREEN`: both are accurate and proxy32 passes cost and both memory criteria. The one-to-one shared-state necessity story is not supported for this controlled task. The result remains a post-P7 development follow-up and a standard baseline result, not a new method or general superiority claim.

Every outcome ends development-scene resolution selection. No automatically triggered further experiment is part of P7b. Any future held-out confirmation must retain proxy32 without further selection, use the already declared P7 held-out gas-origin transform (xz rotation pi/3 and y+0.1), and receive a separate frozen execution plan; it cannot retroactively validate P7's original proxy16 or erase this follow-up's post-result status. No claim about real reconstructed scenes, true fluid evolution, combustion, renderer performance, or publication readiness follows here.

## 8. Freeze, output safety, and reproducibility

Freeze this protocol, new arm/driver, tests, baseline pin manifest, new independent auditor, and authenticated imported source identities before numerical proxy32 output. Require SHA256 agreement before and after quality/timing/audit. Tests may use tiny synthetic fixtures; they must not execute the full proxy32 development trajectory before registration. Any preflight using the exact development trajectory counts as having observed its result and must be disclosed.

Use only a fresh output directory. Never overwrite a nonempty formal directory, parent file, prior audit, or previous failed attempt. Store explicit skipped timing reasons, all scientific negatives, new and inherited artifact inventories, new independent-audit results, and the separately generated parent re-audit result. The package must include a dependency manifest and an executable reproduction path that authenticates the external parent ZIP; a link without a hash check is insufficient. Re-auditing or extraction is outside all timed intervals.

Formal execution awaits the implementation/auditor source freeze and root's execution coordination. Scope approval is complete; no additional user confirmation is required. No experiment has been executed under this protocol.
