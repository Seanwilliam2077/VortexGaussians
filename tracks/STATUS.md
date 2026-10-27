# Dual-track status

Updated 27 October 2026. Active exploration authorized by the author. TOG and Art Papers contributions are both unestablished.

## Current cycle D01: make both tracks runnable and reviewable

| ID | Task | State | Completion evidence |
|---|---|---|---|
| T01 | Portable shared smoke model, artist-brief specification, target provenance, and validation CLI | Complete | [Independent CLI checks](evidence/INTEGRATION_REVIEW.md); default imports no Torch and runs no simulation; saved R22 still fails |
| A01 | “Combustible Digital Memory” rehearsal: observe, intervene, reset, and export creative notes | Complete as an interface | [Real browser checks and screenshots](validation/README.md); 2,483 scene points ignited, finite one-second advance, pause/reset/export passed |
| E01 | Bring R19–R22 decisions and compact evidence into the repository | Complete within catalog scope | [Source-pinned catalog](evidence/README.md); small summaries and figures, explicit external-archive boundaries |
| I01 | Check the two entries, preserve historical files, commit and publish a research branch | Complete | Commit `dfbd538` pushed to `origin/research/dual-track-exploration`; all 425 sealed R19–R22 files retain their hashes ([record](validation/history-preservation.json)) |

The [GitHub research branch](https://github.com/Seanwilliam2077/VortexGaussians/tree/research/dual-track-exploration) includes the previously local research commits and the new dual-track entry. Main has not been merged or deployed. An optional draft-PR creation returned GitHub integration HTTP 403 (resource not accessible); no PR was created. Branch publication succeeded independently before that attempt.

## Active cycle D02: make the creative target concrete

- T02 complete: [one frozen researcher-authored upper-plume bend](tog/tasks/t02-authored-upper-bend/README.md), generated from approved images independently of optimizer controls or a successful witness. Zero control passes editing on frames 16–21 and fails on 22–40; all protection checks pass. Root image review confirms a visible upper bend. The image warp also narrows the upper plume and may leave a top-edge seam. This is development input, not external artist validation, and physical reachability is unknown. Historical R22 is unchanged.
- T03 complete: [one ordinary two-arm screen](tog/tasks/t03-ordinary-conflict-screen/README.md). Edit-only passes editing but only 17/50 protection checks; joint ends at its fixed budget with editing 23/25 and protection 49/50. [Independent saved-array audit](validation/t03-review.md) confirms the final rollback and that no accepted state passed every gate. [Plots](validation/t03-20261027-v2/README.md) are from these saved states. A protection conflict has been observed on one editing path; joint feasibility and a new method remain unestablished.
- T04 design under review: the joint final mean normalized editing MSE is .568734, but frames 39/40 violate per-frame acceptance. Consider an ordinary formulation that also puts the 25 editing gates into the constraints, with the same target, model and tolerances. Any new finite feasibility attempt must be separately frozen and count the previous solve used for initialization; it must not relabel T03 or claim cold-start acceleration.
- A02: [three first-party artistic precedents and one bounded rehearsal question](art/RELATED_PRACTICE.md) are documented. The next creative evidence requires a specific space and actual authorial choices. Automated smoke tests cannot supply those observations.

Continuation is active at the author's request. An hourly thread heartbeat checks for unfinished work and continues the next finite task when execution and account limits allow. It does not buy credits or reset quotas. The research is not marked complete.

## Next scientific/creative decisions

- TOG: turn the editable brief into a concrete authored target with independently stated protection requirements. Validate its feasibility and then ordinary optimization difficulty. The prior low-rank cache is not the default implementation task.
- Art: rehearse one coherent intervention in a clearly identified space. Compare its saved-space, altered-space, and reset phases, record creative choices, and identify what requires a real captured scene or human response.
- Shared: maintain separate result and claim tables. A functional interface or a passing fixture does not close either paper's contribution gap.

The [direct control prior-art review](tog/PRIOR_ART_CONTROL.md) documents why weighted targets and image-based fluid editing alone are not new. It also corrects an earlier search label: the 2013 view-dependent multiscale paper concerns forward simulation, not target-image control. The [pre-result decision rules](tog/DECISIONS.md) remain the interpretation guide.

## Inherited evidence

R20 found a compact, locally stable protection response in a small passive-smoke model. R21's ordinary baseline completed two simple edits in median 17.128 seconds while the measured response-model construction cost was 53.764 seconds; protection penalties were inactive. R22 generated a protected, nontrivial deformation but missed its preregistered upper-region displacement, so no optimizer comparison ran. See [the evidence catalog](evidence/README.md).

The previous pause ended with the author's new dual-track instruction. This status does not retrospectively change the paused execution state recorded in historical R22 artifacts.
