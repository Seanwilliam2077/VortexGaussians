# P3b: cached fields for independent render tracers

P3b measures a world-grid cache against the P3a direct tree query using identical
physical and tracer birth random streams. It changes field evaluation only;
physical particles, optical measure, footprint radius, visual cooling and
density evolution remain fixed. The cache stores induced velocity and normalized
dynamic temperature at grid vertices; trilinear interpolation precedes applying
external forces and the speed clamp at the actual tracer position. Every step
builds a fresh cache. This tests an implementation tradeoff, not a new numerical
method or physical ground truth.

The frozen protocol is [P3B_PROTOCOL.md](P3B_PROTOCOL.md); exact settings and the
selection rule are in [p3b-design.mjs](p3b-design.mjs). P3a files/results are retained
unchanged. Use the Node/Playwright setup and optional `PLAYWRIGHT_MODULE` /
`BROWSER_EXECUTABLE` overrides described in [README.md](README.md).

```sh
node --test research/tests/p3b.test.mjs
node research/p3b-smoke.mjs --out research/runs/p3b-smoke-final
node research/p3b-run.mjs --suite pilot --out research/runs/p3b-pilot
node research/p3b-run.mjs --suite all --out research/runs/p3b-full
```

Run from the repository root. `quick` uses 15 frames with one stationary pair;
`pilot` uses the full horizon with that pair. Both are exploratory. `quality`
runs the 36 quality trajectories and `timing` the 60 independent timing
repetitions. `all` runs both sequentially. Existing manifests cannot be
overwritten. Freeze all source/protocol files before the formal run; source
fingerprints are checked before and after it. Avoid competing browser/GPU/CPU
loads during timing.

The three conditions are a stationary source, crosswind, and crosswind with
procedural curl. They are source/forcing conditions, not distinct reconstructed
scenes. Three paired physical/render seeds test variation without a full Monte
Carlo cross product. Each pair compares direct tree with grid spacings .035,
.07 and .14 at fixed `Nsim=600`, `Nrender=9600`, source rate 180/s, `eps=.07`,
`dt=1/60`, and a three-second horizon.

Only stationary physics seed 11/render seed 101 selects a cache spacing. A
candidate must keep pooled foreground RGB and alpha NRMSE at most 5%, each
15-frame checkpoint's position RMSE at most .007, its p99 distance at most
.035, and have no unmatched birth IDs or capacity/cache fallback. Among those
candidates, select the fastest by median of five independent run medians.
Heldout outcomes never change that choice. Continuing this implementation route
additionally requires all eight other condition/seed pairs to pass and, in all
three conditions, at least 1.5× central speedup with no slower tail statistic.
These are predeclared engineering screening thresholds, not physical validity
thresholds. A failed screen remains a valid experimental result.

Timing repeats use new pages, 20 warmup frames, reset, and 41 synchronized
samples from the fixed 1–3 second physical-time window. Population grows during
this window. `gl.finish()` drains previous work before the timer and completes
the measured draw after submission. Reported total is completed wall latency,
not pure GPU time or display FPS. Cache construction includes map/key/stencil
work and vertex tree queries. Cache lookup includes interpolation, external
forces and any fallback query. Those stages are parts of `tracerMs`, which is
already inside `totalMs`; do not add them again. The direct tree query/advection
stage is recorded separately. Readback, snapshots, hashes and diagnostic probes
are outside timed intervals.

Central timing is **median of five per-run frame medians**. Tail timing is
**median of five per-run frame p95 values**, not a pooled-frame p95. All 205 raw
frame timings, five run summaries and the worst run p95 remain available; frames
within a run are not independent experimental repeats.

Each case JSON retains 181 physical/RNG/birth trace rows, sampled counters,
field time, raw fixed-world probe results and binary file references. The 48
predeclared world probes compare tree and cached fields at identical positions
using the same frozen pre-integration tree. They are diagnostics, not selection
inputs. Tree-node no-support and tracer/probe no-support use different
denominators and must not be conflated.

`particles/*.f64` stores little-endian float64 rows in the exact column order
`id,x,y,z,vx,vy,vz,T,d,life`; JSON records provide row counts and SHA256. Stable
birth IDs pair paths after reordering or culling; unmatched IDs are explicitly
reported. Visual `T,d,life` must remain exactly equal for matching IDs. These
files preserve doubles rather than rounding positions before measuring small
cache errors.

Linear RGBA32F images, PNG previews and masks follow the P3a format. Foreground
is the paired tree image's `alpha>.01`, fixed for that pair/time/view. RGB NRMSE
is `sqrt(sum RGB difference² / sum tree RGB²)`, and alpha NRMSE is analogous;
six fixed captures are pooled by sums. The same-seed tree image is the cache
reference, so changing render sampling cannot masquerade as a cache benefit.
`manifest.json` separates execution status, approximation gates, selected
spacing and route screening. Missing cases or zero signal cannot pass a gate.
