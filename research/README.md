# P0 synthetic diagnostics

These experiments provide evidence of implementation behavior and identify failure modes. They are insufficient by themselves to establish physical validity, visual quality, or SIGGRAPH readiness; they are not GPU performance benchmarks. Read [PROTOCOL.md](PROTOCOL.md) for interpretation and invalid/null outcomes.

Requires Node.js 20+ and Chromium/Edge with WebGL2. From this directory:

```sh
npm install
npx playwright install chromium
npm test
npm run smoke
npm run quick
node run.mjs --suite feedback --seeds 11,23,47
node run.mjs --suite sensitivity --seeds 11,23,47
```

An existing Playwright installation can be selected with `PLAYWRIGHT_MODULE` (absolute module directory) or `PLAYWRIGHT_MODULE_ROOT` (directory containing the playwright package). An installed browser can be selected with `--browser-executable PATH` or `BROWSER_EXECUTABLE`. Without an explicit executable, the launcher tries Playwright's Chromium, then installed Edge and Chrome channels. It prints installation instructions on failure; it never downloads dependencies silently. No host-specific paths are embedded in the code.

```sh
node run.mjs --suite quick --frames 60 --sample-every 10 --out runs/my-check
node run.mjs --suite feedback --config configs/example.json --out runs/my-feedback
node smoke.mjs --browser-executable /path/to/browser --out runs/my-smoke
```

`--seconds` and `--frames` are mutually exclusive. Seconds round up to whole steps; actual times and dt are recorded. CLI values take precedence over JSON configuration. All numerical protocol overrides are labelled custom in the manifest. JSON may override nonfactor parameters; it cannot relabel experimental factors or enable the external emitter, embers, view-aligned slices, or non-VPM modes. Changes to geometry radii are checked against the source-target gap. Keep separate output directories: the runner refuses to overwrite an existing manifest.

Each case opens a fresh page, authors the synthetic scene, resets from the frozen complete demo defaults plus the recorded configuration, sets the camera, and ignites the fixed source once. All causal arms have the external emitter disabled from time zero. There is no warmup with different random histories. Simulator seeds remain the existing shared random stream; later arms can consume different numbers of random draws. This harness does not redesign the simulator to force agreement.

The four feedback arms toggle flame-to-scene heat and scene-to-solver particle reseeding. The raised target has 9 source splats at y=.20 and 27 target splats at y=.45/.49/.53. The .25 vertical gap exceeds the default graph (.11) and heating (.14) radii. The connected strip tests ordering and duplicate-density sensitivity. Duplicate density changes the physical number of fuel/heat nodes; area weights apply **only to analysis**, and the common anchor states remain available. The 1681-site disconnected patch binds the actual 1400 frontier cap and tests fuel/char scheduling. It is a scheduler diagnostic, not a plausible scene.

`quick` uses one seed, 3–120 frames per case, and checks the entire pipeline cheaply. `feedback` uses 12 seconds per arm and three seeds. `sensitivity` varies frontier caps, zero/low/default/generous sample/feed caps, stable-ID order, and exact duplicate densities. Cap zeros are structural ablations, not candidate production settings. This first harness does not evaluate layered-vs-3D quality, real reconstructions, camera-motion visual quality, or physical scale invariance.

Outputs include `manifest.json`, one raw JSON file and one sampled CSV per case. Raw JSON preserves every sampled per-splat state, hashes, cumulative counters, seed/configuration, density maps, and first observed ignition times. CSV records groups, area-weighted metrics, particle stats, and cumulative counters. First-ignition timing has the recorded sampling resolution. Manifest records git SHA/dirty status, SHA256 source fingerprints, browser version/renderer, OS, dt and configuration. Wall-clock duration is for troubleshooting, not a benchmark. Failed cases retain errors and partial samples, appear in the manifest, and make the process exit nonzero; absence of target ignition is a recorded outcome, not a failed software check.

Smoke checks cover deterministic replay including combustion hashes, world-fixed camera invariance, synthetic rendering, edge switches, stopping both base emission and source-band reheating after an active emitter, cap counters, and spatial unfairness under input reversal. View-aligned camera response is recorded without requiring a positive difference. Unit tests cover geometry, common-anchor density maps, argument validation, and metric handling. Changing intended simulator behavior may require changing the corresponding smoke expectation with a documented reason.
