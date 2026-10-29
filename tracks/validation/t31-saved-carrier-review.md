# T31 independent saved-carrier review

**CLEAR — qualified authored input only.** Independent standard-library JSON/gzip parsing, hashing and scalar arithmetic passed 4,970 checks over all 810 particle rows (270 at frame90; 540 at frame180). No capture module was imported, simulation replayed, browser launched, ray formed, integral evaluated or source acquired. The detailed audit is [t31-saved-carrier-audit.json](t31-saved-carrier-audit.json), SHA256 `579e134bafcf431563278b5c82c071b4664c5a36cf935f6b9f15f249d0adf80c`.

## Identity and lifecycle

All eight frozen artifacts match their recorded byte counts and SHA256 values. Freeze SHA256 is `3c7a29482f7cdcf1f092c87d9cf56f469b4f85be7bef066c17c0b4f8c67584c5`, identical in attempt, worker result and execution receipts. Both complete gzip files and both immediate frame checkpoints match compressed and decompressed identities; their raw sizes satisfy the20MiB cap. Each checkpoint equals its corresponding final snapshot and step receipt.

The chronology is freeze → attempt → worker start → acquisition start/finish → supervisor finish. Receipts report exactly one browser launch/reset,180 steps, both prescribed snapshots, exit0, no timeout, no worker/cleanup/browser error and no blocked page request. Worker time is3865.6127ms; supervisor time is4.388339700060897s, within90/120s limits. Log hashes and stdout summary match. Source checks are also enforced before and after acquisition in the frozen worker. These observations establish receipt consistency; they do not independently trace process cleanup, OS networking or deterministic replay.

## Complete arithmetic and metadata checks

Every render row equals its physics row after removing the snapshot-added `id`; every carrier row retains its exact source index and position, without selection or omission. All weights are implicit1. Every saved numerical value inspected is finite; density, weights, extinction strengths and colors are nonnegative, and widths are positive.

Independent reconstruction of `h=.045/sqrt(6)`, `k=max(0,w*.2*d)` and all four smoothstep color blends with original fire/emission parameters gives maximum absolute discrepancy **0** for position, width, strength and RGB. Sequential aggregate reconstruction also differs by **0**. More accurate `math.fsum` aggregation differs by at most **3.410605131648481e-13**, within the frozen tolerance. Counts, hot counts, optical sums, integrated3D strength, color extrema and emission accounting agree. Maximum frame-time discrepancy from frame/60 is **5.773159728050814e-15**.

Both snapshots preserve every reset parameter/configuration: shared-s11, seeds11/101, shared3d,600-particle limits, layers3/rate180, radius.045/tau.2, fire/emis2.2. Camera metadata is consistent (distance4.4, elevation.12, vertical FOV.85);256x192, all three fixed yaws, black background and projection-plane clips are retained. Camera domains are valid; no ray adapter was exercised. Recorded acquisition graphics are AMD Radeon890M through ANGLE, not an independently measured RTX rendering path.

## Limits

The continuous lift is a declared new field, not an image-preserving reconstruction of the original billboards. RGB reaches2.3430615086998454; normalized-color error bounds require explicit HDR adaptation. One simulation, two times and three camera specifications do not establish scene diversity, external creator demand, physical fidelity or a TOG contribution. No image, renderer accuracy, useful bottleneck or cost comparison was measured. Ordinary same-field reference integration, conservative pruning and complete delivery costs remain unqualified.
