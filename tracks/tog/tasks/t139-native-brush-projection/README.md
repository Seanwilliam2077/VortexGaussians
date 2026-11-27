# The native footprint rules separate the two Bonsai brush rays

The fixed left and central rays selected original splats **205385** and **437231** in this CPU evaluation of the Vortex scene shader. Both selections survived half-precision destination alpha accumulation. The near-camera primitive 867267 that stopped T136 contributes zero to either ray. The previous experiment remains a failed input qualification. [Prospective correction](PROTOCOL.md) · [Results and scene parameters](RESULTS.json) · [Earlier failure](../t136-bonsai-shot/README.md)

| Primary view at 1560 × 1040 | Left | Center |
| --- | ---: | ---: |
| Continuous ray, pixel-center convention | (670.44, 519.5) | (779.5, 519.5) |
| Positive-alpha contributors | 91 | 246 |
| First rank to reach half opacity | 50 | 129 |
| Accumulated opacity before / after crossing | .4659 / .5160 | .4895 / .5093 |
| Native-style pick ID | 205385 | 437231 |
| Nearest physical pixel (ties down) | (670, 519) | (779, 519) |
| Pick ID at that pixel | 205385 | 340163 |

The two continuous display requests came directly from the T136 rays. The second straddles actual pixel centers. Its nearest fixed pixel selects a different surface contributor. Preserve that distinction when validating with browser readback. The CPU code follows the native near cutoff and far clip, capped ellipse, normalized truncated alpha and original depth-bucket ordering. It evaluates Gaussian means and footprint shapes in camera coordinates, with float32 shader intermediates. Actual GPU matrix rounding, rasterization at pixel centers, framebuffer precision and blending depend on the backend. These snapshots identify exactly which native pixel observations would verify the reconstruction; they contain no GPU readback.

The camera baseline normalizes the scene by 0.721235 world units per reconstruction unit. Brush A encloses 217 geometric sites. The two B brushes enclose 179 and 405, and their exterior shell contains 1,041 sites before the common-parent simulation. The second registered camera, ID 146, sees B at depth −2.06915 world units. Every site in the radius-.26 shell has depth at most −1.80915, hence its center is clipped by the native shader. Its visible shell weight is exactly zero even before eligibility pruning. Its 25% criterion is undefined. An equally informed ordinary operator can omit that camera and avoid any second-candidate simulation attributable solely to it. The primary view still requires actual eligibility, rendered gas images and cost tests. [Native source and shell bounds](RESULTS.json)

Run `python verify.py` with NumPy to check all four archived contributor sequences and both accumulation modes. To reproduce from the full fit, use the [T136 acquisition](../t136-bonsai-shot/acquire.py) then `python project.py --check`. It rebuilds all observations from the private PLY and original camera table and verifies the published data. The inputs for a later browser run are `native_input` in RESULTS.json, T136's locally staged `scene.ply`, `t139-cameras.json` and `t139-geometric-shell.npy`. Set `__demo.P.sceneMax = 2000000` before loading the original PLY, check that the native parser kept exactly 1,244,819 records, then apply the recorded parameters and calibrated pose. [Probe](project.py) · [Ordered IDs, alpha and buckets](contributions.npz)
