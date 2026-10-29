# T42 — real Firewoods sequential ignition: consistent state, ambiguous second event

**Decision: task unqualified for visual identifiability.** One frozen trajectory on the recovered Firewoods reconstruction completed. Both discrete ignitions added the expected material points without resetting prior state, and reset restored the saved initial state. However, the full-frame images do not clearly distinguish the second ignition from the first burn's continuation. This closes the finite T41 workflow check without selecting a new method or another run. It establishes neither an ordinary-method bottleneck nor a TOG contribution.

The researcher-authored purpose was to stage two successive ignitions on different visible parts of an existing woodpile. It is not an externally validated creator requirement or a physical combustion experiment. The [pre-execution protocol](PROTOCOL.md), [recipe](recipe.json), [freeze](freeze.json), [pre-execution review](../../../validation/t42-preexecution-review.md), [saved-data audit](result-audit.json), [independent review](../../../validation/t42-saved-output-review.md) and [decision evidence](decision-evidence.json) separate preparation, execution, engineering consistency and visual judgment.

## What ran

All 34,687 foreground Gaussians were loaded. The original demo at parent `9343f9e957595b6bba1abcccd382a9cc6c8852b1` remained unchanged; only a temporary camera/inspection/export insertion was used, with exact reversal to source bytes verified. The existing layered VPM uses world coordinates, nine simulated layers and 600 particles per layer. It retains heuristic graph propagation, elapsed material clocks, legacy measure mode and block admission. This is not the P3 3D carrier, a continuous Gaussian volume model or calibrated combustion. No physical areas were invented for the reconstruction.

The new authored placement uses unit scale, zero rotations/XZ offsets and Y lift 0.75. Source camera 0 is transformed with the same placement and rendered at 940 × 528. Locations A=`ply:22158` and B=`ply:26728` have disjoint radius-0.12 neighborhoods inside the declared world-coordinate domain. Their geometry comes from reconstructed centers, not measured surface contacts or metric material ground truth.

Preparation inspected four original implementation files and 776 displayed source lines within the 800-line allowance. [Two offline selector invocations](preparation-history.json) are disclosed: the first failed to find an eligible A center within 3 pixels of its fixed photographic target. Before any dynamics, the common rule was revised once to 10 pixels, leaving both targets, opacity cutoff, radius, placement and simulation unchanged. The selected centers were 3.26846 and 1.14051 pixels from their targets. The failed 3-pixel rule remains failed; no dynamic result informed selection.

Exactly one browser/page and seed 11 were used. After initial capture, A was ignited, followed by 180 steps at 1/60 s. B was then ignited with no intervening step or reset, followed by another 180 steps. Six complete checkpoints/full frames include the final explicit reset. No second trajectory, A-only counterfactual, alternate framing, position change, parameter sweep, installation or acquisition followed. All original stepping, ignition, propagation and rendering expressions remained intact.

## Saved-state evidence

| Checkpoint | Frame | Simulated seconds | Burning material points | Gas particles |
|---|---:|---:|---:|---:|
| Initial | 0 | 0 | 0 | 0 |
| Immediately after A | 0 | 0 | 145 | 0 |
| Before B | 180 | ≈3 | 3,374 | 2,394 |
| Immediately after B | 180 | ≈3 | 3,662 | 2,394 |
| Endpoint | 360 | ≈6 | 3,662 | 2,433 |
| Reset | 0 | 0 | 0 | 0 |

The independent saved-data audit ran once after worker termination: 521,226 consistency predicates passed, zero failed. These mostly repeat per-point conditions; they are not independent scientific tests. It checked all six complete material exports, identities, bounds, finite fields, camera/controls/times, spherical ignition eligibility, frontier membership and PNG integrity. Both A's 145 and B's 288 eligible points were exactly the newly ignited sets. Across zero-time B, every fuel/heat/glow/char value was unchanged, as was the existing frontier prefix.

For A's original 145 points, summed fuel progressed from 145 to 72.50058770 to 0.0004461203; summed char progressed from 0 to 85.29423356 to 145. All 145 still had state 1 at the endpoint because fuel remained positive. Reaching char 1 is not reported as complete fuel exhaustion. Initial and reset serialized material/state records were byte-identical, including the 6,424,104-byte uncompressed state.

Gas aggregates and the program's opaque, non-cryptographic particle hash were unchanged across instantaneous ignition. Complete gas arrays were not exported, so elementwise gas-state equivalence was not independently established. All six PNGs were valid, nonblack 940 × 528 RGBA8 images with successful post-render GL checks. The exported `draw_count` remained 0; it is an uninterpreted counter, not a verified instance count or proof that no rendering occurred. The worker's original `completed_capture_pending_saved_audit` label is preserved; the later audit and visual decision are separate records.

## Why the task is unqualified

Root and an independent agent inspected the three unique full-frame images: initial, before B at 3 s and endpoint at 6 s. The initial woodpile is recognizable. At 3 s, the front log has a pronounced yellow-white bright region and an orange/red plume below it. At 6 s that front region still dominates, with a weaker orange patch on the right log. Knowing B's location makes the patch noticeable, but the images alone do not establish a clear second ignition event.

The woodpile occupies a modest portion of the full frame, the front brightness hides material detail, and the diffuse lower plume competes with both locations. These are agents' observations of static images, not human feedback or a perceptual study. No A-only counterfactual isolates the endpoint difference caused by B; this limits causal interpretation and is not an added acceptance gate. Initial/after-A images are identical, as are before-B/after-B images; this is consistent with hand ignition changing state before stepping and is not itself a failure. The frozen requirement was identifiable events in the full-frame record, which remains unmet.

Saved counters also expose the existing service/admission context:

| Second 180-step interval | Recorded value |
|---|---:|
| Graph frontier processed | 252,000 = 180 × 1,400 |
| Graph frontier deferred | 407,160 = 180 × 2,262 |
| Material clocks processed | 659,160 = 180 × 3,662 |
| Scene feed attempts | 8,640 |
| Capacity-blocked attempts | 8,553 (98.9931%) |
| Scene seeds emitted | 43 |

B's appended sources have zero-based frontier ranks 3,374–3,661, and the post-B/endpoint frontiers are identical. Given the already inspected fixed-prefix graph service, stable ordering with only new burning points appended and spent points permanently removed, and no rotation or reinsertion under one-way material state, they receive no outgoing graph-source service during this interval, while elapsed clocks still advance them. This is a conditional code deduction supported by saved counts, not a new measurement of per-source service. Identical endpoint arrays alone would not prove the intervening service history. Aggregate feed counts do not identify which sources emitted the 43 particles. No counterfactual establishes that these policies caused the visual ambiguity.

Known scheduling/admission remedies, separate material/render state and area weighting where meaningful remain ordinary alternatives. This run does not test their best implementation or prove they cannot solve the workflow. Default-policy limitations cannot be repackaged as a new method gap.

## Cost and evidence availability

| Scope | Seconds |
|---|---:|
| Worker through cleanup, excluding final progress/result receipt writes | 30.5378862 |
| Twelve stepping calls, including API overhead | 6.7850480 |
| Six state exports | 18.8770166 |
| State writes | 0.4968730 |
| Render/export calls | 0.2153271 |
| PNG writes | 0.0126405 |
| Supervisor through worker terminal/live check | 31.1530631 |
| Subsequent output inventory hashing | 0.0129843 |
| Supervisor elapsed before final receipt write | 31.1660551 |
| Independent saved-data audit | 4.6918372 |

These scopes overlap; do not sum every row. Full phase records include load/setup/reset/cleanup in the decision evidence. The final small supervisor receipt write/stdout flush is excluded. The worker exited 0 and its parent process was absent at the final check; this is not independent proof that every descendant exited. Node v24.16.0, installed Playwright 1.62.1, Edge 149.0.4022.52 and ANGLE/AMD Radeon 890M were used. Capture and export dominate this instrumented run. It is not an FPS result, optimized-renderer benchmark or strong-baseline cost comparison.

The 19 external run files total 7,817,363 bytes. Raw arrays, six PNGs and third-party assets stay outside Git at `outputs/t42-firewoods-sequential-workflow/run-01` relative to the outer workspace. Their identities are in [decision-evidence.json](decision-evidence.json); the [publication manifest](audit-manifest.json) links frozen inputs and historical evidence. Source/protocol/recipe/audit scripts are retained, but this is **not yet a portable public benchmark bundle**: the harness pins local runtimes, external input paths, historical adapter ancestry, the pre-run parent and an exclusive run directory. Do not treat a fresh checkout as sufficient to replay it, or rerun the consumed attempt in place.

## Research consequence

This is the first dynamic result in this recovered Firewoods workflow; T41's three historical captures remain static. The current ordinary interface demonstrably appends ignition and preserves the exported material state, while the intended two-event visual task remains unqualified. Historical failures and criteria remain unchanged.

No follow-on experiment or method is selected. Do not improve this picture by automatically changing framing/timing/locations, adding another scene, or implementing a capacity fix and calling it research. Any subsequent technical step must state a concrete mechanism question, explain why ordinary alternatives leave it open, and identify evidence that would change the decision before selecting a new budget. The full research goal remains active and unachieved; art stays inactive, and main is neither merged nor deployed.
