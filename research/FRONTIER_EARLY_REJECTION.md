# Graph-frontier early rejection

2026-10-15. This is a standard implementation optimization of the existing
layered preview, not a new simulation method or SIGGRAPH contribution.

The graph-frontier callback already returns immediately when the target scene
state is not zero. Its hash query now checks that same state before computing
distance/sqrt. Only this graph call supplies the optional state array. The old
callback guard remains. Eligible neighbors keep the same bucket/index order,
distance arithmetic, Float32 updates and RNG calls; ignite and flame calls keep
the previous default path. There is no neighbor cache, approximation, quota
change, or disabled combustion clock. The runtime change is three lines.

Six fresh headless Edge 149 / AMD Radeon 890M processes were run in fixed order
reference/candidate/candidate/reference/reference/candidate on the complete
45,808-point synthetic campfire. Each used 120 warm steps, full reset, then 720
steps with fixed ignition, wind edits and 60-degree view rotation at 1280x720.
All seven saved public observations and six PNGs per run matched the current
reference exactly, including parameters, exposed states, hashes and counters.
This is sampled equivalence plus a source-level argument, not independent
replay of every hidden intermediate state or physical-quality validation.

Primary completed-frame medians (709 preselected frames/run) were 40.8, 41.9,
42.2 ms for references and 24.4, 24.5, 24.2 ms for candidates; candidate p95 was
26.0 ms in all three. Adjacent ratios of run medians were 0.598039, 0.584726,
0.573460. Their median corresponds to 41.53% less elapsed time on this workload.
These are not per-frame ratio medians or a statistical significance claim.
Step-to-render-completion via gl.finish is not continuous UI FPS,
input-to-photon, or pure GPU timing. JS/GPU peak memory was not measured.

All original data, old/new source bytes, protocol, diff and saved-data checker
are in the separate local evidence archive, not silently available on GitHub:

- `VortexGaussians-early-reject.zip`: 21,003,169 bytes
- SHA-256: `9a981576601ba1e10c00a6d55948f89ea3800dceb52a9ba9c5d3430285fa6410`
- old reference commit: `815bae0e18863dacacf7f49589a73c28181aecec`
- reference demo bytes SHA-256: `a37b3e22f7855d40a684f1030462bd7f61a5ea3ba56cd39940ef2ba4bbf2adbb`
- candidate demo bytes SHA-256: `3db09579c2d8c99fa0e72e7010c78d153d9f6b46d7bfd7bc01d076a0d4fbfc2f`

The independent data check covered 4,320 frames, 432 statistics, 42 public
observations, 36 PNGs, source fingerprints and the exact three-line patch.
Re-running that check from a fresh ZIP extraction matches the original result
apart from its generated timestamp. It is a data/integrity check, not a new
browser run or physical audit. Preserve the old reference when reproducing;
do not benchmark two copies of the now-optimized live demo.

This one development asset does not establish multi-scene benefit. The next
research step is real reconstructed asset ingestion and a fair system-level
comparison; continued micro-tuning on this synthetic scene is not a substitute.
