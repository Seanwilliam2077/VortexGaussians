# P3c: component attribution at fixed grid spacing

This diagnostic separates grid interpolation of induced velocity from interpolation of normalized temperature Tb. It revisits the same conditions and paired seeds already observed in P3b. It is exploratory attribution, not a new heldout test, a search for a better grid spacing, a physical validation, or evidence of a hybrid performance gain. The full frozen specification is in [P3C_PROTOCOL.md](P3C_PROTOCOL.md).

The four arms are DD (direct velocity/direct temperature), GD (grid velocity/direct temperature), DG (direct velocity/grid temperature), and GG (both grid). All use the same 600-slot physical simulation, 9,600-slot passive renderer, source rate 180/s, dt=1/60, three-second horizon, and grid spacing 0.035. Each hybrid deliberately pays for an additional direct query; this phase has no timing matrix.

Run from the repository root with Node.js and Playwright:

```text
node --test research/tests/*.test.mjs
node research/p3c-smoke.mjs --out research/runs/p3c-smoke-final
node research/p3c-run.mjs --suite quick --out research/runs/p3c-quick
node research/p3c-run.mjs --suite all --out research/runs/p3c-full
```

Install the research dependencies using the existing `research/package.json`, or set `PLAYWRIGHT_MODULE` to an available Playwright module. `BROWSER_EXECUTABLE` or `--browser-executable` selects an installed Chromium/Edge executable. No machine-specific path is embedded. Output directories refuse to overwrite existing manifests. `quick` has four 15-step trajectories; `pilot` has four full-length trajectories; `all` has 36 trajectories. Only `all` completes the registered matrix. All suites remain scientifically exploratory.

Each trajectory records all 181 per-step physical/birth-RNG trace rows, 13 particle checkpoints (including frame zero), and six linear RGBA32F images at 1.5/3 seconds and three fixed views. Full output has 468 Float64 particle files, 216 RGBA files, 216 display PNGs, and 108 byte-mask files. These counts exclude smoke outputs. Binary metadata records layout, dimensions, orientation, and SHA256. PNGs are display previews; quantitative errors use the raw linear buffers.

DD captures every eligible ID divisible by 97 after that step's births but before advection, including newborns. Each capture stores its actual old position and age and probes all four field combinations at exactly that position and frozen physical time. The observer and probe must not modify any production state. No world-grid sampling or manually selected tracer is substituted for these inputs.

`manifest.json` stores the specification, source hashes at start/end, environment, planned cases, visible case failures, physical/birth locks, and `analysis`. Each raw case JSON stores `trace`, `snapshots`, `checkpoints`, and `captures`. DD checkpoints additionally contain `inputs`, `inputPhase`, `fieldTime`, and complete `probe.samples` with raw fields, pre-clamp quantities, and final velocities. The other arms leave those fields null.

`analysis.comparisons` compares GD/DG/GG against DD by stable birth ID and contains per-checkpoint paths, directional and age-bin statistics, pooled squared-error image statistics, and a descriptive `accuracyCheck` using P3b's frozen thresholds. A failed accuracy check is a measured result, not a software execution failure. Missing evidence, physical/RNG drift, changed matched T/d/life, capacity limitation, and grid fallback fail execution validity. Missing live IDs and their optical weights remain explicit.

`analysis.groups` reports the four-arm vector interaction `eI=(GG-DD)-(GD-DD)-(DG-DD)`, separately at each checkpoint and pooled over particle-checkpoint observations. It preserves common/union/excluded counts and component squared sums. RMS ratios use GG as denominator and return null for zero GG error. They are not additive percentage contributions; no dominant-component threshold is imposed. Late checkpoints have more particles, so pooled statistics weight more observations and should be read beside each checkpoint.

Directional sufficient statistics are `count`, `ySum`, `ySquared`, `xzSquared`, and `positionSquared`; derived fields include signed y bias, y RMSE, xz RMSE, and position RMSE. Age bins use `round(life/dt)` with residual below 1e-9, at step boundaries 30, 60, and 120. Empty bins return null metrics. Each checkpoint also records age-bin position p99; pooled age bins aggregate sums and RMS only, never average checkpoint percentiles. Trajectory ages are post-step; captured input ages are pre-step.

Input summaries include direct thermal support yes/no crossed with grid support zero/partial/full. Full support uses a 1e-12 rounding tolerance. Each of six groups preserves counts, signed Tb sum, squared Tb and induced/final velocity errors; empty groups return null. Cache support is diagnostic even in GD, where production uses direct Tb. All full-run source hashes must remain unchanged. These measurements isolate implementation behavior under the current model, not physical ground truth or submission readiness.
