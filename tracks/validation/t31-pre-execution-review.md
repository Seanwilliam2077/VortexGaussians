# T31 — independent static pre-execution review

29 October 2026. Reviewer: pressure_screen. **No remaining blocking issue found in the revised named files.** This clears preparation of the freeze and the single bounded acquisition, not its eventual qualification. No worker/import, simulation, browser, renderer, package installation, external request or numerical example was executed during this review.

## Exact inspection scope

Read the final versions of T31 `capture.mjs` lines 1–191, `supervise.py` 1–73, `PROTOCOL.md` 1–38, `MODEL.md` 1–17, and `research/p3-design.mjs` 1–70. Read only **demo/index.html 4425–4512** (88 lines) for the original detailed snapshot/reset/step implementation. This is 477 lines in the final named versions; earlier pre-revision versions of the T31 files were also reviewed. No broader demo window or other new source was inspected.

The root separately reports having read demo lines 4751–4817 and confirmed `window.__demo.gl`, `forceSize` and `researchP3` exports. That export evidence is **root-supplied**, not independently read here. The runtime server helper and browser dependencies were not independently inspected or exercised by this reviewer; their existing source identity is to be frozen by root. The protocol preserves the separate earlier exploration-budget overrun rather than relabeling it as compliant work.

## Actionable findings resolved before execution

The original Promise.race could abandon a still-running acquisition, and final status could remain qualified after cleanup failure. The revised worker awaits its work, uses a shared expiry flag/checkpoints, closes its own browser on deadline, and closes a late-returning launch during finally. The outer supervisor bounds a stalled worker and attempts termination of its own process tree; termination failure is recorded, not claimed as success.

Returned frames now receive immediate gzip checkpoints, and final raw-state serialization retains available snapshots even if a later step/gate fails. Qualification occurs only after cleanup, final page-error/request gates, completeness checks, repeated frozen-source verification and a stable freeze hash. Finalization failure sets failed status/exit code. These changes prevent a partial artifact or a late callback from being presented as qualified.

The supervisor reserves `run-01/attempt.json` before Popen, and the worker's start marker uses exclusive creation. Existing run directories stop re-entry. Spawn failures and timeout/cleanup exceptions are caught and lead to a failure receipt; no alternate browser/module path or retry is present. Explicit 100ms API polling avoids relying on requestAnimationFrame after that callback has been suppressed. The network statement now correctly covers routable page requests, not a system firewall or all Edge background traffic.

## API, completeness and field contract

The frozen P3 recipe supplies 600 simulation/render slots, shared3d, seed11/renderSeed101, dt1/60, 180 steps, snapshots90/180, 256x192 and the three specified yaw views. The original API accepts that mode/config, installs a paused scene without the listed extras, resets physical/render RNGs and returns frame/time/hash information. `step(n,dt)` advances exactly its explicit loop; `snapshot({detail:true})` clones all physics/render particles and appends render IDs. The worker calls one reset and two step batches and checks snapshot frame/time against the prescribed values. It records step receipts and source hashes for later saved-data verification.

Input gates check nonempty complete particle counts <=600, declared totals, shared arrays except snapshot ID, finite positions/T/d, nonnegative density and optical weights, and aggregate density/temperature/optical-density agreement under the explicit relative-or-absolute tolerance. No render override or selective visibility filter enters the carrier. The raw detailed snapshot preserves more fields than the lift requires. Here `complete_state` denotes complete declared particle inputs for the authored field, **not a demonstrated resumable simulator checkpoint** or general replay guarantee.

The lift's h=R/sqrt(6), k=w*tau*d, isotropic extinction normalization and integrated-3D-strength expression agree with MODEL.md. Its fire ramp, smoothstep intervals, emission factor and smoke mix match the declared binary64 convention. Finite nonnegative RGB is checked; values above one remain present. This is explicitly a new continuous field, removing the original billboard's truncation/pedestal/perspective behavior, not a recovered image-preserving conversion or physical combustion claim.

Captured finite camera parameters and the documented restrictions define the real-arithmetic camera basis. MODEL.md specifies all pixel centers, yaw units, black background, HDR linear RGB and projection-plane-to-unit-ray clip conversion. No rays or images are evaluated here. A future adapter must still verify actual finite ray calculations, stable Gaussian interval tails and radiance-aware omitted-extinction bounds. Neither the old splat output nor T22's [0,1] fixture qualifications becomes a same-field reference automatically.

## Remaining execution boundary

The 90-second acquisition flag, outer 120-second wait and bounded cleanup are failure controls, not proof that browser launch/WebGL/extensions or the simulation will succeed. Every artifact has its declared 20MiB raw cap and exclusive write; final raw/carrier identities are recorded. Frozen source bytes are checked before and after acquisition. Root must construct the stated complete freeze, including this review, before invocation; this review does not authenticate a freeze that does not yet exist.

If the one invocation fails, its partial evidence remains unqualified and no fix-and-rerun follows. If it succeeds, it establishes an authored input only. Ordinary integration correctness, complete rendering cost, bottleneck, novelty, creator demand and TOG relevance remain unproved. No T29/T30 method or source/training route is reopened by this static clearance.

## Reviewed final identities

The demo hash identifies the whole original file; semantic inspection remained limited to the stated 88-line window.

| File | Bytes | SHA256 |
| --- | ---: | --- |
| T31 `PROTOCOL.md` | 8207 | `5615c0702c0993b9674a7c8930c84ec6268d2a79d0b7b469a0b751c6d878ad23` |
| T31 `MODEL.md` | 3652 | `2fb5315f175f058509080fb4ba09b0e77ecac75206b7325662766adf88f66814` |
| T31 `capture.mjs` | 12362 | `fe09f9407dbab0f1134c9b5892ccd51ff13e85ca9b32e95b8c1a0b67bbd76aee` |
| T31 `supervise.py` | 3421 | `f297a9bcddacefacacb374eb7831e6fa8d05cbc230119b816105de84d3251a20` |
| `research/p3-design.mjs` | 3969 | `a9c6069993c1e8a2ec77ebd9d6ff82676ce195bd0136bbfd82bb6d0e329639b2` |
| `demo/index.html` | 314044 | `e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0` |
