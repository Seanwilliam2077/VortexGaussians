# T41 — recover the real Firewoods workflow contract

**Decision: the existing real input survives; one ordinary sequential-ignition workflow is worth inspecting. No new method is selected.** This is a source/record inspection, not a dynamic execution, new asset acquisition, or reopening of T38's historical kitchen replay. The purpose is to move beyond the narrow T31 carrier to an actual reconstructed object without inventing a harder synthetic protection edit.

## What survives and what was actually tested

The outer workspace's `work/real-asset-ingest` retains the Firewoods foreground PLY, camera JSON, source photograph, configuration and ingest manifest. All five match the October 16 freeze. The PLY has 34,687 Gaussians, 8,603,906 bytes, SHA256 `906460f162f704b89666b159ae5b4744e53e6dc11baf448a550de581506919b0`. The saved provenance identifies the FieryGS archive and commit `f70fbe26d22431c7acd93a745861dd47ba4307d7`; this turn did not revisit the external source or inspect that repository's renderer.

The historical adapter, driver, preparation script, protocol, source/candidate HTML and runtime survive. Twelve of thirteen frozen files match at their original locations. The exception is the current repository's later `demo/index.html`; the exact old file survives in both staging and the archive verification directory. The current demo must be treated as a new execution input, not silently called the old version. [The compact evidence record](evidence.json) retains both identities and selected saved values; third-party assets and binary exports are not added to Git.

The actual saved driver/result establish these settings, beyond the earlier mathematical camera probe:

| Capture | Actual placement | Actual dynamic state |
| --- | --- | --- |
| Normal camera | scale 2.306; zero yaw/pitch/translation | frame/time 0; no dynamic particles, burning, heating or char |
| Source camera 0 / image 00000 | same placement | same zero state |
| Transformed source camera | scale 1.5; yaw .62; pitch −.48; translation [−.18,.24,.30] | same zero state |

The buffer is 1879×1055. The driver uses seed 11, faithful rendering, SH degree 3, unit exposure/scene light and sorted scene splats, with spread/emitter/post effects disabled. `01-orbit` names the normal camera capture; `orbit=false`, so it is not an orbit animation. The actual scale 2.306 differs from the earlier probe's unrounded 2.3057971994… . The source-camera adapter follows the scene transform and sets camera basis and `.05/50` clips; its `fireUV` projects the fixed point `(0,.06,0)`. This static record does not qualify image picking, dynamic source positions, camera-dependent simulation, or flame/wood occlusion. It does not prove those behaviors fail either.

Root inspected the two existing diagnostic composites. The source-camera woodpile is recognizable and aligned with the photograph, with softer rendered texture. The normal camera cuts off the pile at the lower image boundary. The displayed alpha contour is the renderer's output, not independent geometry truth. These are researcher visual observations of old images, not fresh quality measurements or user feedback. The historical strict GPU-half check remains **102/103, failed**; nothing here repairs or reclassifies it.

## What the present code already offers

At the current parent commit, `demo/index.html:1131–1136` converts the supplied world point and radius to source coordinates, then sets only previously cold, fuel-positive indices to burning and appends them to the frontier. It does not rebuild existing material state. Fuel/glow/char evolve at lines1195–1207; lines1241–1279 feed scene burning into the gas simulation. The public `__demo.ignite` exposes that operation. Consequently **A first, then B while retaining A's state** is expressible with existing controls. This is code evidence, not proof that the two events are visibly distinguishable on Firewoods.

“Then B” means a second discrete ignition, not translating a continuous heat source. “Retain A” means preserving and evolving its existing state; it does not demand that B have no influence on A. There is no protected ROI, inverse target, hidden witness control or new R22 threshold. [The next entry](NEXT_ENTRY.md) fixes this distinction before a possible execution.

## Representation dependence: real limitation, ordinary remedies

The delegated inspection read 294 relevant demo lines, including search matches. In the legacy branch, while the recipient remains cold, each serviced burning source contributes

```text
delta_h[j] = dt * spreadRate * sum_i (1-d[i,j]/R)_+ * (1+2.2*u[i,j]).
```

The directional factor uses the current world-up correction. If a burning source is cloned q times at the same position and state, and service caps do not change which sources are processed, its real-arithmetic contribution multiplies by q. Opacity, covariance and a physical source capacity do not appear in that expression. This does not establish a Firewoods error magnitude, an exact q-fold floating-point update, or the response to arbitrary split/LOD operations. Cloning a cold recipient alone need not change each copy's ignition time. Per-index `fuel=1` is a state convention, not proof that physical energy has been duplicated.

The same source already contains an authored-area branch: source contributions are multiplied by `authoredArea(i)/spreadReferenceArea`, and emission aggregates coincident positions with the same group. Equal total area under coincident subdivision removes the leading multiplicity dependence under matched state and uncapped service, in real arithmetic. That mode requires supplied area; ordinary imported Firewoods points do not thereby acquire measured physical area.

An ordinary separate material grid/particle state also breaks the binding: evolve material capacities/topology independently, then sample that field for display. This does not solve material inference, contact, thin structures or sampling error, but it is a valid baseline, not a new proposal. T15 A and T39 A already allow separate physical and optical state. Neither the multiplicity observation nor missing material metadata selects a new method or demonstrates TOG novelty.

## Scope, costs and next decision

This scope is recorded **after exploratory inspection**, not a preregistered numerical experiment. Root read existing status/policy, the October evidence/world-up notes, reproduction/protocol/visual metadata, saved ingest metadata, selected current demo/API windows, and existing T15/T31/T39/T40 records. The input agent read freeze/camera-probe summaries, then exactly adapter.js, run.mjs and result.json; it checked byte identities and output existence without decoding particle arrays. Root viewed two saved PNG composites and extracted selected old JSON fields. No simulation, browser replay, graph construction, render, ray integration, numerical estimator, installation, download or fresh web query ran. Hashing and metadata extraction are bookkeeping, not scientific timing.

The useful next question is limited: can the existing ordinary workflow visibly deliver sequential ignition with continuing state on this real object? One execution can resolve actual input/behavior gaps that static captures cannot. Success closes that brief as already served. A failure must first be separated into coordinate/domain/camera/interface/capacity/visibility causes; it does not license a new architecture. A blurry or ambiguous output is inconclusive, not a designed failure of a strong baseline. No parameter sweep, re-training, replacement scene, new protection task or renderer development follows automatically.

[Independent review](../../../validation/t41-workflow-review.md) checks that this is an appropriate ordinary-workflow question and preserves the distinction between operation feasibility and a research contribution. The complete TOG goal remains active and unachieved; art remains inactive, and main/automation are unchanged.
