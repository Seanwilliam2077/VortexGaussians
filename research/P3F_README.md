# P3f: fixed-budget local correction diagnostic

This experiment tests whether a seven-query curvature heuristic can spend a fixed
correction budget more usefully than one deterministic hash selector. It is an
exploratory implementation experiment in one stationary source condition, using
one previously observed seed pair and one previously unrun seed pair. It does not
establish physical validity, broad generalization, or statistical superiority over
random selection. The frozen rules are in [P3F_PROTOCOL.md](P3F_PROTOCOL.md).

## Run

Use Node and Playwright as described in [README.md](README.md). `PLAYWRIGHT_MODULE`
may point to an existing Playwright installation; `BROWSER_EXECUTABLE` or
`--browser-executable` selects an installed Chromium-compatible browser. No host
path is embedded in these scripts.

```text
node --test research/tests/*.test.mjs
node research/p3f-smoke.mjs --out research/runs/p3f-smoke-final
node research/p3f-run.mjs --suite quick --out research/runs/p3f-quick
node research/p3f-run.mjs --suite all --out research/runs/p3f-full --baseline research/runs/p3e-full --baseline-archive ../../outputs/p3e/VortexGaussians-P3e.zip
```

Run browser measurements serially without other browser workloads. Existing output
manifests are never overwritten. `quick` runs only 15 frames per case and never
permits timing, regardless of its observed errors. There is no timing-only bypass.

## Fixed experiment

Six quality trajectories are DD, curvature correction and hash correction at
physics/render seed pairs `(11,101)` and `(59,409)`, in that order. A seventh
trajectory replays the old uncorrected affine method at `(11,101)` solely for
regression. DD and the old affine trajectory must exactly reproduce authenticated
P3e records, including all old snapshot fields, 181 tracer hashes, particle bytes
and images. The archive checksum and three JSON checksums live in
`lib/p3f-baseline.json`; source and baseline fingerprints are checked before and
after the run. Portable reproduction may use these authenticated JSON records
without the old binary files; absent old bytes are explicitly counted and are
never described as read or verified.

Physics, rendering and source settings remain fixed: 600 physical-particle cap,
9600 render-particle cap, 180 physical births/s, `dt=1/60`, 180 steps and the P3e
optics. Each corrected method groups its own current input positions, builds all
seven raw model queries per group, and directly queries every member of
`ceil(0.1*K)` chosen groups. Both policies evaluate the same scores. Curvature uses
the diagonal second differences of `(ux,uy+buoy*Tb,uz)` and summed squared
per-member remainder estimates; hash uses the fixed frame/birth-ID integer mixer
and salt `0xa511e9b3`, without consuming simulation RNG. This heuristic omits mixed
derivatives, support discontinuities and the final clamp. Both methods deliberately
pay all model queries even for selected groups, making hash a mechanism control;
this is not an optimized hash performance baseline.

With no retirement, `N=48*frame`, `K=3*frame` and every group has 16 members. Actual
per-step populations, group counts and extra query counts must match between the
two selectors. Retirement or missing identities invalidates this equal-budget
claim and fails the scientific gate without discarding the completed trajectories.

## Evidence and conditional timing

All seven quality trajectories finish before deciding whether to measure cost.
Each records 181 lightweight physical/birth traces and separate tracer hashes,
13 Float64 particle arrays, and six raw linear RGBA32F images plus PNG previews.
This gives 91 particle arrays and 42 images. Four corrected trajectories also
record 180 compact selection summaries and 12 complete production observers each.
The 48 observer JSON files contain actual pre-advection inputs, all model members
and stencils, scores, ranks, selected identities and only the direct queries the
production algorithm actually performed. No all-point oracle contributes to
production. Saved records can independently reconstruct partitioning, score
arithmetic, selection, force application, velocity and Euler transport.

`manifest.quality` contains four comparisons, two budget locks, two immutable
regressions, twelve shared DD ROI records, 48 selection file records and the
per-seed selection gate. Per-image and path errors use the same P3b/P3e metrics.
Each seed must pass the original absolute quality constraints for curvature and
strictly improve both its worst sampled position RMSE and worst sampled p99 over
hash. There is no cross-seed averaging to rescue a failed pair. Equal, missing or
nonfinite comparisons cannot count as improvements. Finite empty candidate images
and retired particles are valid negative scientific outcomes; invalid provenance,
missing raw evidence, nonfinite state or physics/RNG drift are execution failures.

A valid negative experiment has `status: passed`,
`stageStatus: stopped_after_quality`, `protocolComplete: true` and an explicit
`timingSkipped` reason. Absolute `accuracyPassed` remains separate from the stricter
`selectionPassed`. Parameters and budgets are not adjusted after seeing results.

Only if both seed gates pass, ten independent DD/curvature timing runs use the old
pair `(11,101)`: five alternating orders AB/BA/AB/BA/AB, which are not perfectly
position-balanced. Each has 20 warmup frames followed by reset, then measures
completed frames 60–180 every third frame with `gl.finish` before and after the
timed work. Grouping, seven-query model construction, scoring/sorting, correction
queries, interpolation, advection and rendering all count. No dense particle
snapshot or production observer runs inside the timing loop. Quality/timing
endpoint state and selection traces must match outside timing. The central
statistic is the median of five per-run medians; tail is the median of five per-run
p95 values, not pooled-frame p95. All 205 measured frame records are retained.

Engineering continuation requires complete evidence, both selection gates and at
least 1.5× median speedup over DD without worsening the defined tail statistic.
The single-condition conditional timing is not a general performance claim. The
256×192 image resolution remains a diagnostic setting.
