# Vortex Gaussians: Real-Time Simulation-Driven Fire and Smoke as Native Gaussian-Splatting Content

### [[Project Page](https://seanwilliam2077.github.io/VortexGaussians/)] [[Paper (PDF)](static/vortex_gaussians_paper.pdf)] [[Live Demo](https://seanwilliam2077.github.io/VortexGaussians/demo/)] [[Video (soon)]()]

Anonymous Author(s)<sup>1</sup>

<sup>1</sup> Anonymous Institution &mdash; author list withheld while the paper is under double-blind review.

[![teaser](static/images/teaser.jpg)](https://seanwilliam2077.github.io/VortexGaussians/)

*We present the first system that generates fire and smoke by forward physical simulation in real time and renders them as native Gaussian-splatting content. Our key insight is a structural isomorphism: Lagrangian vortex particles and 3D Gaussians are the same class of point primitive, so one particle set serves simultaneously as simulation state and render primitive — position maps to the Gaussian mean, temperature to emissive blackbody color, density to opacity, and velocity gradient to an anisotropic covariance — with no voxelization, meshing, or simulation-to-renderer conversion anywhere. A pressure-free two-level layered vortex-in-cell solver, with a new inter-slice vorticity-coupling operator, drives the particles; one depth-sorted emission–absorption rasterizer composites flame, smoke, embers, and reconstructed 3DGS scenes with per-primitive mutual occlusion.*

## News

- **[2026-07]** Inter-slice vorticity-coupling operator (`interZ`) added: bidirectional, circulation-conserving z-Laplacian exchange across slices; cross-slice velocity correlation rises 0.21 → 0.39 → 0.61 with operator strength.
- **[2026-07]** Loaded `.ply` reconstructions are now merged into the global depth order by an asymmetric exact/bucketed two-stream interleave — foreground scene objects correctly occlude the flame, at no measured overhead.
- **[2026-07]** Initial release: paper draft, project page, and the single-file WebGL2 real-time prototype.

## Cloning the Repository

```shell
git clone https://github.com/Seanwilliam2077/VortexGaussians.git
```

## Quick Start

The entire system — simulation, sorting, rendering, UI — is one dependency-free HTML file. **No installation, no GPU compute, no build step.**

```shell
# option 1: just open it
demo/index.html          # double-click; any WebGL2 browser (Chrome / Edge / Firefox)

# option 2: serve locally (needed only if your browser blocks file:// workers)
python -m http.server 8000
# then open http://localhost:8000/demo/
```

Runs at real-time rates (~60 FPS at defaults) with the simulation single-threaded in CPU JavaScript.

### Interactive controls

| Control | Effect |
| --- | --- |
| **drag canvas** | orbit the 3D camera (auto-orbit resumes on release) |
| **Shift + drag** | move the fire source; the plume follows with vortical lag |
| **`1` / `2`** | all layers procedural / all layers vortex-in-cell (hot-swap, same renderer) |
| **`F` / `S`** | fire / smoke shading of the same particle state |
| **`Space` / `R`** | pause / reset |
| **`Sim Layers` slider** | per-layer solver hot-swap (0 … N) |
| **`View-aligned / World-fixed`** | slice-orientation ablation (edge-on collapse of world-fixed) |
| **panel sliders** | buoyancy, baroclinic gain β, cooling, coupling c, inter-slice κz, covariance gain, exposure/bloom, … |

### Key simulation parameters

- `layers` (N = 9): number of view-aligned slices; each runs an independent 32×48 vortex-in-cell solve.
- `couple` (c = 0.5): velocity nudge toward the 16×24 coarse global solver — 0 = independent slices, 1 = slaved to bulk motion.
- `interZ` (κz = 0, optional): bidirectional inter-slice vorticity exchange `ω_k += Δt·κz·(ω_{k−1}+ω_{k+1}−2ω_k)`; conserves total circulation, raises neighbor coherence.
- `baro` (β = 1.4): baroclinic source Γ̇ = β·∂T/∂x — the temperature → buoyancy → vorticity loop that rolls plume edges.
- `covStretch` (1.3): flow-driven covariance Σ̇ = LΣ + ΣLᵀ with determinant renormalization and aspect clamp.

## Custom Scenes

Load your own Gaussian-splatting reconstruction and light a fire inside it:

1. Train a scene with [Inria 3DGS](https://github.com/graphdeco-inria/gaussian-splatting) (or use any binary little-endian `.ply` in its format).
2. In the demo panel, open **Scene** and load the `.ply` (subsampled to a configurable budget, default 120k splats).
3. The scene is merged into the same global depth order as the fire — foreground geometry occludes the flame per primitive (`sceneSorted` toggles the naive draw-after baseline for comparison).
4. Adjust `sceneScale` / `sceneYaw` / `sceneLift` to place the fire where you want it.

## Repository Structure

```
index.html        # project page (self-contained; occlusion comparison slider, embedded demo)
demo/index.html   # the complete system: single-file WebGL2 prototype (~83 KB)
static/           # paper PDF + compressed figures
PUBLISH.md        # page-deployment checklist (GitHub Pages)
```

## TODO

- [ ] Supplemental video (orbit capture, interaction reel, ablation cuts)
- [ ] Named-hardware benchmark table (FPS vs. layers / particles / scene splats)
- [ ] Energy-spectrum E(k) validation of the inter-slice operator against a true-3D reference solve
- [ ] Occlusion figure on a real captured `.ply` reconstruction
- [ ] Multi-source in-scene ignition

## Citation

```bibtex
@misc{vortexgaussians2026,
  title  = {Vortex Gaussians: Real-Time Simulation-Driven Fire and Smoke
            as Native Gaussian-Splatting Content},
  author = {Anonymous Author(s)},
  year   = {2026},
  note   = {Preprint, under review}
}
```

## Acknowledgements

The layered two-level architecture builds on Horvath & Geiger's production fire system (SIGGRAPH 2009); the rasterizer implements the forward pass of [3D Gaussian Splatting](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) (Kerbl et al. 2023). The project page adapts the layout of [Nerfies](https://nerfies.github.io/) and [FieryGS](https://pku-vcl-geometry.github.io/FieryGS/); the README follows the format of [PhysGaussian](https://github.com/XPandora/PhysGaussian).
