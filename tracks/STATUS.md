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

- T02 complete: [one frozen researcher-authored upper-plume bend](tog/tasks/t02-authored-upper-bend/README.md), generated from approved images independently of optimizer controls or a successful witness. Zero control passes editing on frames 16–21 and fails on 22–40; all protection checks pass. Root image review confirms a visible upper bend. The image warp also narrows the upper plume and may leave a top-edge seam. This is development input, not external artist validation; joint feasibility was subsequently established in T04. Historical R22 is unchanged.
- T03 complete: [one ordinary two-arm screen](tog/tasks/t03-ordinary-conflict-screen/README.md). Edit-only passes editing but only 17/50 protection checks; joint ends at its fixed budget with editing 23/25 and protection 49/50. [Independent saved-array audit](validation/t03-review.md) confirms the final rollback and that no accepted state passed every gate. [Plots](validation/t03-20261027-v2/README.md) are from these saved states. A protection conflict has been observed on one editing path. T04 subsequently establishes joint feasibility without changing this T03 result; no new method is established.
- T04 complete: [one post-result ordinary-solver revision](tog/tasks/t04-framewise-feasibility/README.md) adds the 25 per-frame editing gates to the constraints, preserving the target, model and tolerances. The paid T03 warm start uses x only, original v0/rho0 and fresh solver state. New G0 passes; the solve reaches **25/25 edit and 50/50 protection** in 67 rollouts /20 returned steps /62.572 seconds. Worst edit/protection relative RMS are 4.474%/1.967%. No AL outer update occurs. [Independent CPU audit](validation/t04-review.md) verifies warm-image equality, the final accepted state, all original gates and cost. [Saved figures](validation/t04-20261027/README.md) were visually inspected. Full T03+T04 discovery cost is 263 rollouts /243.325 worker seconds, not cold-start performance. Extra budget, revised constraints and warm start are confounded; this establishes a numerical feasible witness, not a new mechanism or an artistic evaluation.
- T05 in preparation: one zero-control cold start with the same T04 objective, constraints, gates and fixed 120-rollout/600-second budget. Reuse the certified unchanged T04 G0 instead of rerunning it. Peer review and source certification precede execution. This measures one ordinary baseline on a developed input; it does not count historical trial-and-error as baseline solve cost or claim a held-out/statistical speedup.
- A02: [three first-party artistic precedents and one bounded rehearsal question](art/RELATED_PRACTICE.md) are documented. The author has not selected a personal place or object yet. A small synthetic prototype can explore what an interface retains after reset; a real memory, author rehearsal and participant responses remain pending and cannot be supplied by automated tests.

Continuation is active at the author's request. An hourly thread heartbeat checks for unfinished work and continues the next finite task when execution and account limits allow. It does not buy credits or reset quotas. The research is not marked complete.

## Next scientific/creative decisions

- TOG: establish an honest ordinary-solver cost, then test a coherent editing revision with the same protected regions. A feasible single task is now available; an actual repeated-edit bottleneck and new mechanism remain unestablished. The prior low-rank cache is not the default implementation task.
- Art: explore one reversible interaction while the personal source is undecided. A later real-space rehearsal must record actual creative choices across saved, altered and reset phases.
- Shared: maintain separate result and claim tables. A functional interface or a passing fixture does not close either paper's contribution gap.

The [direct control prior-art review](tog/PRIOR_ART_CONTROL.md) documents why weighted targets and image-based fluid editing alone are not new. It also corrects an earlier search label: the 2013 view-dependent multiscale paper concerns forward simulation, not target-image control. The [pre-result decision rules](tog/DECISIONS.md) remain the interpretation guide.

## Inherited evidence

R20 found a compact, locally stable protection response in a small passive-smoke model. R21's ordinary baseline completed two simple edits in median 17.128 seconds while the measured response-model construction cost was 53.764 seconds; protection penalties were inactive. R22 generated a protected, nontrivial deformation but missed its preregistered upper-region displacement, so no optimizer comparison ran. See [the evidence catalog](evidence/README.md).

The previous pause ended with the author's new dual-track instruction. This status does not retrospectively change the paused execution state recorded in historical R22 artifacts.
