# P3a: fixed 3D physics, independent render sampling

This diagnostic asks whether increasing independent passive Gaussian samples
improves numerical agreement with a dense tracer image while preserving one
fixed 3D VPM trajectory. It uses one source and three views. It does not compare
layered and 3D physical accuracy or cost, test scene combustion, or establish
physical or perceptual ground truth. The 256×192 images are diagnostic images,
not evidence for display-resolution performance.

The preregistration is [P3_PROTOCOL.md](P3_PROTOCOL.md), with exact machine-readable
settings in [p3-design.mjs](p3-design.mjs). Defaults and old P0/P1/P2 runs are
unchanged. The common optical renderer is an opt-in P3 renderer.

## Run

Use Node 20+ and the Playwright/browser setup in [README.md](README.md). Browser
and module overrides remain `BROWSER_EXECUTABLE` and `PLAYWRIGHT_MODULE`; no
host-specific paths are required.

```sh
node --test research/tests/p3.test.mjs
node research/p3-smoke.mjs --out research/runs/p3-smoke-final
node research/p3-run.mjs --suite pilot --out research/runs/p3-pilot
node research/p3-run.mjs --suite all --out research/runs/p3-final
```

Run from the repository root. `--suite quick` uses 12 frames and one physical
and render seed for plumbing checks. `pilot` uses the declared full horizon but
one physical/render seed; both are labelled exploratory. `quality` runs the 48
quality trajectories only; `timing` runs the 25 timing repetitions only. `all`
runs both, sequentially. Existing output manifests cannot be overwritten.

Formal runs must start only after all source/protocol files are frozen. The
manifest records hashes before and after execution and fails a formal run if
they differ. Avoid other browser/GPU workloads during timing. A measured frame
drains prior GPU work before the timer and calls `gl.finish()` after drawing.
This is completed wall latency, not pure GPU time or display FPS. Each timing
repetition creates a fresh page, warms up for 20 frames, resets, and measures 41
frames across the fixed 1–3 second physical-time window. Population grows during
that window; it is not a steady-state test. Hash computation, serialization,
readback, and screenshots are outside those timed intervals.

## Raw evidence

`manifest.json` contains the full matrix, machine/browser details, source
fingerprints, case status, every-step physical-hash comparisons, image errors,
and reference stability gates. Each case has a JSON file containing snapshots,
source/capacity/query ledgers, actual counts, and its full physical-hash trace.
Timing cases additionally have raw stage timing rows and CSV. Five independent
repetitions are kept separate; do not treat 41 correlated frames as 41 trials.

`images/*.rgba.f32` stores interleaved, little-endian float32 RGBA in linear
space before postprocessing, with bottom-left origin. Its companion JSON gives
dimensions, orientation, SHA256, framebuffer precision, and signal statistics.
The framebuffer must be RGBA32F with float blending; no silent lower-precision
fallback is allowed. PNGs show the canvas only as previews. They are not used in
the numerical metric. Fixed reference-ensemble foreground/hole masks are saved
as uint8 byte arrays with hashes and dimensions in the manifest.

For each physical seed and each of three independent tracer repetitions, errors
are pooled over both times and all three views. Full-frame and fixed foreground
RGB/alpha errors remain separate. The 32× versus 64× reference error must be at
most 25% of low versus 32× reference error in all four metrics, across all nine
repetitions. Empty foreground or zero signal does not pass. A failed reference
gate prevents declaring a quality winner even when all software checks pass.
Hole fraction is auxiliary; additional opacity or blur is not automatically
better. Source injection is normalized by optical weight, without changing
kernel radius or compensating survivors after culling.

The baseline queries the physical tree separately for each passive tracer. Its
cost measures this implementation, not a lower bound on decoupled rendering.
Increasing `Nrender` need not preserve tracer sample prefixes or tracer paths;
it must preserve the full physical state and physical RNG exactly. A dense
reference tests this tracer transport/optical model only. Multiple scenes,
matched-error cost comparisons, and appropriate physical/appearance validation
remain future work.
