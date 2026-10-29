# T38 — historical kitchen demonstration does not yet supply a new research task

30 October 2026. **Decision: NO_GO for replaying this historical demonstration or preparing an algorithm from it.** The fixed inspection establishes an existing qualitative capability, but identifies neither matching replay inputs nor a demonstrated unmet operation. This closes this replay route under [the prior decision rule](../t37-cheap-frame-screen/NEXT_ENTRY.md); it does not establish that captured-scene interaction is solved or impossible. The full research goal remains active and the TOG contribution remains unestablished.

## What was inspected and observed

The [protocol](PROTOCOL.md) allowed four local text/source files and600 charged lines. Actual acquisition used three files and417 lines:178 for README/EVIDENCE_STATUS and239 for demo/index.html, including search matches and repeated lines. No directly referenced kitchen provenance/configuration file was identified in these excerpts; the fourth slot was unused. The [documentation ledger](source-ledger-docs.json), [demo ledger](source-ledger-demo.json), [asset inventory](asset-inventory.json) and [media record](media-inspection.json) retain scope and byte identities. There was no external search, download, installation, demo execution, simulation, integration or GPU run.

Exactly six complete, unmodified frames were decoded from the existing43-second nominal kitchen video. The visible subject is a yellow toy/model bulldozer on a cloth-covered table, with plants and household objects behind it. The following are researcher observations of historical media, not measured simulation states or creator/audience feedback.

| Frame | Video time (s) | Visible simulated-time label (s) | Observation |
|---|---:|---:|---|
|0|0.0|0.0|Yellow model; no obvious flame or extensive darkening.|
|516|8.6|21.6|Bright orange/red flame-like plume beside the front/left body.|
|1032|17.2|31.4|Plume and a small dark patch near the front/left body; viewpoint differs.|
|1548|25.8|60.0|Front/left flame and a darker patch on the cloth behind it.|
|2064|34.4|167.0|More darkening of the front assembly, with bright flame/edges.|
|2579|42.9833|256.9|Larger darkened portions of the front/body, remaining yellow and glowing edges.|

The six views show changing fire and char-like appearance and apparent viewpoint changes. They cannot establish the actual control sequence, material response, physical spread, temporal stability or correct occlusion. The simulated-time labels do not advance proportionally to video playback; neither60fps video metadata nor these labels establish interactive rendering performance. Extracted PNGs remain ignored locally; the repository already contains the source video and the media record specifies exact frame selection and reader identity.

## Existing operation and replay gap

| Item | Evidence within this inspection | Consequence |
|---|---|---|
|Existing operation|README63–70 describes orbit/source controls;84–89 describes PLY loading, alignment and ignition. Demo883–892 loads a supplied PLY, stores its center/extent, chooses scale and builds burn state;1131–1143 contains ignition/fuel operations.|Loading a captured scene, placing fire and changing appearance are already available capabilities, not proposed contributions. Static inspection does not rerun them.|
|Scene/fire composition|Demo894–917,967–991 and2838–2898 describes/uses depth-bucket interleaving and internal alternatives; defaults1418–1435 enable sorting.|A backdrop or alpha-threshold depth ablation is not a reproduction of a strong external method. No matched runtime defect was established.|
|Matching scene|Scoped tracked-name inventory contains the kitchen video, three kitchen stills and static/test_scene.ply. README86 explicitly identifies that PLY as a synthetic campfire.|No matching kitchen PLY was identified. Names and the inspected references do not prove absence from every location, history or format. The campfire is not a replay substitute.|
|Camera/control/configuration|No kitchen-specific camera trajectory, control stream, seed or parameter snapshot identified in the acquired excerpts.|The historical operation cannot be reproduced from the acquired record. General reset/step/hash support is not the missing historical input stream.|
|Code identity|Current demo has an exact recorded hash; no code commit matched to the video was identified.|Current source cannot be asserted to have produced the historical recording.|
|Reference/cost|README historical FPS claims and demo904–917 PSNR/bucket timing comments lack matched raw runs/configuration in this acquisition.|Preserve them as historical author claims, not new validated timing, quality or ground truth. No external renderer source was acquired in T38.|

## Task value and ordinary remedy

The recognizable operation is introducing fire and progressive appearance damage into a captured scene. The video already shows that qualitative result. No specific unsatisfied target, failed action, or measured quality/cost requirement is attached to it in the inspected evidence. **Retained demonstrated bottlenecks: zero.** This is insufficient evidence, not a proof that no bottleneck exists.

For recreating the qualitative effect, the ordinary first attempt would be the existing loader, placement/ignition controls and sorted scene/fire composition, with a fully recorded input/configuration/control/code contract. For investigating an alleged compositing defect, it would additionally need a specified failing view and a matching-model ordinary reference; the internal backdrop/threshold alternatives alone are not that reference. Neither attempt is currently qualified by this historical record. Missing assets are a reproducibility problem, not an algorithmic novelty argument.

Stop this historical replay route. Do not run the unrelated campfire, tune the T31 narrow plume, manufacture an occlusion failure, refine its reference or start a numerical protocol from this inspection. Reopening requires matching scene provenance, a replay contract and an explicit assessable operation that the ordinary workflow has not already satisfied. An independently justified researcher-authored task remains possible, with its synthetic provenance stated, but none was selected or created here. See [decision boundary](NEXT_ENTRY.md) and [independent review](../../../validation/t38-task-review.md).
