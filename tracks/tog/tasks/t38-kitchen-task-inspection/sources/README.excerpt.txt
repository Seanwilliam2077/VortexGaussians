README.md:3: **Two ongoing research tracks:** [TOG-oriented smoke editing](tracks/tog/README.md) and [Combustible Digital Memory — art research](tracks/art/README.md) now share this repository. The original browser prototype remains the creative platform; the technical contribution and artistic argument are being investigated separately. Start with the [dual-track workspace](tracks/README.md), [current tasks](tracks/STATUS.md), and [compact historical evidence](tracks/evidence/README.md). Neither track currently claims publication readiness.
README.md:5: ### [[Project Page](https://seanwilliam2077.github.io/VortexGaussians/)] [[Historical manuscript (PDF)](static/vortex_gaussians_paper.pdf)] [[Evidence status](research/EVIDENCE_STATUS.md)] [[Live Demo](https://seanwilliam2077.github.io/VortexGaussians/demo/)] [[Solver Comparison](https://seanwilliam2077.github.io/VortexGaussians/compare.html)] [[Video](static/video/vortex_gaussians_supplemental.mp4)] [[Captured-scene clip](static/video/vortex_gaussians_kitchen.mp4)] [[Omniverse clip](static/video/vortex_gaussians_farmland_ov.mp4)]
README.md:13: *Vortex Gaussians is a browser prototype for vortex-driven fire and smoke rendered as Gaussian splats. The default layered mode maps vortex-particle positions and visual attributes to render primitives: temperature controls emissive color, density controls opacity, and velocity gradients drive an anisotropic covariance. This shared storage is an implementation choice; simulation kernels and rendering covariances are not asserted to define the same field. The layered VPM uses regularized vortex-kernel evaluations and a Barnes–Hut approximation. Depth-interleaved splat compositing combines the dynamic effects with reconstructed 3DGS scenes. Separate research paths test numerical correctness and alternative state representations; they do not establish a new method advantage or physical accuracy for the complete fire system.*
README.md:14: 
README.md:15: The linked PDF and media are historical materials. Their claims and measurements predate the current audit; see [Evidence status](research/EVIDENCE_STATUS.md) for current results and limitations.
README.md:16: 
README.md:17: - **Interactive browser demo, no build step.** Simulation, sorting, rendering and UI are in one dependency-free HTML file. The author historically reported ~60 FPS at 9 layers × 600 particles on a desktop RTX 3080 at 1280×800, with single-threaded CPU JavaScript simulation. This layered-mode measurement was not rerun in the current audit.
README.md:18: - **Grid-free layered VPM mode.** This mode uses a Barnes–Hut treecode (θ = 0.9) without a fluid grid or pressure projection. The author reported up to 15.3× over exact summation at matched particle counts in the historical configuration; this was not remeasured here. The VIC comparison uses grids, and separate research paths have their own discretizations.
README.md:19: - **Heuristic fire spread on captures.** Heat / fuel / char / glow states live on loaded scene splats; threshold heating changes their appearance and can re-seed layered plumes. These visual controls are not calibrated material properties. The separate fixed-parcel 3D thermal tests do not validate this combustion model.
README.md:32: ```
README.md:33: 
README.md:34: The demo panel's top section chooses the solver: **Grid Mode** (the VIC baseline, one 32×48 velocity grid per slice) or **Grid-Free** (the Gaussian VPM). [`compare.html`](https://seanwilliam2077.github.io/VortexGaussians/compare.html) synchronizes the seed, timestep, renderer and control stream, with per-side cost measured live on your machine. This is an implementation comparison, not a matched-accuracy physical benchmark.
README.md:35: 
README.md:36: Deterministic replay: `window.__demo.reset(seed)` + `.step(n)` + `.hash()` supports simulation-state comparisons for fixed code, configuration, inputs and runtime. Replay does not make wall-clock timings or results across platforms bit-reproducible.
README.md:38: ## Coupling Research Diagnostics
README.md:39: 
README.md:40: Start with [Evidence status](research/EVIDENCE_STATUS.md), which separates the historical demo, browser correctness repairs, the isolated standard physical reference, and the shared-state/proxy architecture screens. The following commands run the original P0 harness.
README.md:41: 
README.md:42: The self-contained [research harness](research/README.md) runs a synthetic 2×2 coupling ablation and tests sensitivity to splat duplication, input order, and processing quotas. It requires Node.js 20+ and Playwright with Chromium or Edge; the interactive demo still has no build step. The [experiment protocol](research/PROTOCOL.md) defines the controls and the limits of these measurements.
README.md:43: 
README.md:44: ```shell
README.md:45: cd research
README.md:46: npm install
README.md:47: npx playwright install chromium
README.md:48: npm test
README.md:49: npm run smoke
README.md:50: node run.mjs --suite all --out runs/p0
README.md:51: ```
README.md:52: 
README.md:53: Each run saves the source fingerprints, browser and hardware metadata, complete configuration, per-splat combustion snapshots, and sampled CSV measurements. The experimental API adds stable scene IDs, separate flame-to-scene and scene-to-solver switches, complete external-source cutoff for layered VPM, and actual heat/emission/quota counters. The released coupling equations and default quotas are preserved. These synthetic diagnostics establish implementation behavior; they do not measure full-scene frame latency or establish physical accuracy.
README.md:54: 
README.md:55: The subsequent [P1 comparisons](research/P1_README.md) test opt-in elapsed combustion clocks and cold-particle reuse. The original policies remain the defaults; the P1 protocol measures both their intended effects and their graph-propagation and discarded-state tradeoffs.
README.md:56: 
README.md:57: The [P2 comparisons](research/P2_README.md) test explicit surface-area weights for graph heating and scene-to-particle feedback. They distinguish coincident-splat splitting from actual spatial refinement, with fixed-domain uniform and adaptive grids. Area mode is an opt-in synthetic research path; it requires authored measures and does not infer a physical surface area from ordinary 3DGS covariance or opacity.
README.md:58: 
README.md:59: ## Controls
README.md:60: 
README.md:61: | Control | Effect |
README.md:62: | --- | --- |
README.md:63: | **drag canvas** | orbit the camera (auto-orbit resumes on release) |
README.md:64: | **Shift + drag** | move the fire source; the plume follows with vortical lag |
README.md:65: | **`1` / `2` / `3`** | all layers procedural / VIC baseline / grid-free Gaussian VPM (hot-swap, same renderer) |
README.md:66: | **`F` / `S`** | fire / smoke shading of the same particle state |
README.md:67: | **`Space` / `R`** | pause / reset |
README.md:68: | **`Sim Layers` slider** | per-layer solver hot-swap (0 … N) |
README.md:69: | **`View-aligned / World-fixed`** | slice-orientation ablation (edge-on collapse of world-fixed) |
README.md:70: | **panel sliders** | buoyancy, baroclinic gain β, cooling, coupling c, inter-slice κz, covariance gain, exposure/bloom, … |
README.md:71: 
README.md:72: ## Key Parameters
README.md:73: 
README.md:74: | Parameter | Default | Effect |
README.md:75: | --- | --- | --- |
README.md:76: | `layers` × `ppl` | 9 × 600 (1300 quality) | view-aligned slices × particles per slice; every slice runs an independent grid-free solve |
README.md:77: | `couple` (c) | 0.5 | velocity blend toward a coarse guiding field: tree-derived in VPM mode, a 16×24 grid in VIC mode — 0 = independent slices, 1 = fully guided |
README.md:78: | `baro` (β) | 1.4 | baroclinic source Γ̇ = β·∂T/∂x — the temperature → buoyancy → vorticity loop that rolls plume edges |
README.md:79: | `covStretch` | 1.3 | flow-driven covariance Σ̇ = LΣ + ΣLᵀ, determinant-renormalized with an aspect clamp |
README.md:80: | `interZ` (κz) | 0 (off) | inter-slice vorticity exchange `ω_k += Δt·κz·(ω_{k−1}+ω_{k+1}−2ω_k)`; conserves circulation. An exchange rate, not a diffusivity (no 1/Δz²), so not comparable across slice counts |
README.md:81: 
README.md:82: ## Custom Scenes
README.md:83: 
README.md:84: Load your own Gaussian-splatting reconstruction and light a fire inside it:
README.md:85: 
README.md:86: 1. Train a scene with [Inria 3DGS](https://github.com/graphdeco-inria/gaussian-splatting), or use any binary little-endian `.ply` in that format. To try it immediately: [`static/test_scene.ply`](static/test_scene.ply) (45,808 splats, the synthetic campfire scene from the paper).
README.md:87: 2. In the demo panel, open **Scene** and load the `.ply` (subsampled to a configurable budget, default 800k splats).
README.md:88: 3. The scene and fire are depth-interleaved: the dynamic stream is exactly sorted, while scene depths are bucketed. This supports approximate per-primitive occlusion (`sceneSorted` toggles the naive draw-after baseline).
README.md:89: 4. Place the fire with `sceneScale` / `sceneYaw` / `sceneLift`, then ignite it: `P.spreadOn` + `__demo.ignite(x, y, z, r)`.
README.md:103: ## Status
README.md:104: 
README.md:105: Preprint. Historical materials include author-reported layered-mode timings, visual examples on captured `.ply` scenes, and a negative-leaning energy-spectrum comparison with a 3D implementation. They are not newly replicated full-system measurements.
README.md:106: 
README.md:107: Current audits verify narrower contracts: finite-capacity 3D thermal coupling (P4b), a native thermal-query repair (P5b), and an isolated standard Gaussian-vortex reference (P5c). The P7b controlled screen found that 2048 independent thermal states could meet the same 2% response/display tolerances as 8192 shared states, with a median paired CPU-to-display-temperature-buffer time ratio of 0.2730 and lower accounted array storage. This is a prescribed-motion thermal task, not a renderer, VPM or full-frame speedup. Full-system physical accuracy, real-scene material calibration and a distinct method advantage remain unestablished. See [Evidence status](research/EVIDENCE_STATUS.md) for protocols, provenance and limitations.
