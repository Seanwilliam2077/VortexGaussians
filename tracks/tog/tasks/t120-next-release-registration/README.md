# T120 · Prospective lower-band edit on the Playground reconstruction

The official FieryGS data table at commit `f70fbe2` supplies two fitted-scene archives. Firewoods and Playground have both been used in this project. The current default branch points to the same commit. Git lists zero tags, GitHub Releases lists zero releases, and the authors' project-page links lead to the paper, code and credits without a further downloadable fitted scene. The Dead Tree control in T92 came from a mesh. This inventory establishes a gap in the checked public release. It does not settle the availability of data from other sources. [Pinned upstream data table](https://github.com/PKU-VCL-Geometry/FieryGS/blob/f70fbe26d22431c7acd93a745861dd47ba4307d7/README.md#data) · [Authors' site](https://pku-vcl-geometry.github.io/FieryGS/) · [GitHub Releases](https://github.com/PKU-VCL-Geometry/FieryGS/releases) · [Inventory receipt](UPSTREAM.json) · [T92 provenance](../t92-transfer-workload/README.md)

## Registered edit

The preregistration chose a second edit on the existing 80,023-site Playground reconstruction. The two target sites come from the nearest Gaussian centers to fixed lower-band bounding-box fractions. The seed is the first 32 bits of a specified SHA-256 digest. Camera IDs come from the lower and upper quartiles of the 307 calibrated release cameras. Each choice preceded geometric diagnostics. The earlier Playground study used upper-band sites 79793 and 36480, seed 59 and cameras 0 and 153. The new condition changes edit, seed and cameras together, so a future result can test their joint transfer on one fitted reconstruction. It cannot isolate their individual effects or establish transfer to another scene. The task is defined by the researchers. [Pre-geometry protocol at f8ac7a6](https://github.com/Seanwilliam2077/VortexGaussians/blob/f8ac7a6/tracks/tog/tasks/t120-next-release-registration/PROTOCOL.md) · [Earlier Playground study](../t111-playground-shot-choice/PROTOCOL.md)

| Step | Native site | World center (x, y, z) | Radius | Geometric sites |
| --- | ---: | --- | ---: | ---: |
| A at frame 0 | 80004 | (−0.424337, 0.408103, 0.009538) | 0.12 | 1,910 |
| Light B from frame 180 | 77626 | (0.063180, 0.220539, 0.006588) | 0.08 | 920 |
| Full B from the same frame 180 | 77626 | (0.063180, 0.220539, 0.006588) | 0.12 | 1,504 |

The full stroke contains all light-stroke sites and 584 further sites, and shares zero geometric sites with A. The fixed B shell `(0.12, 0.26]` contains 8,621 sites before applying state or camera eligibility. Seed **2234068899** and calibrated cameras **76 and 230** are frozen. Both camera rotation matrices are orthonormal with determinant +1 to within 10⁻⁶. Their native calibration is 2014 × 1093. These are static geometry and calibration checks. Whether the shell stays cold, has any visible mass in both views, or reaches the threshold remains unknown. [Full-precision centers, checksum and poses](REGISTRATION.json) · [Native recipe](recipe.json) · [Ordered shell IDs](shell.json.gz)

## Acquisition and coordinates

The upstream archive is 1,049,696,735 bytes. The registered range readers need 17,965,855 compressed bytes for the foreground and 39,564 for the camera file, plus ZIP header and download-form traffic. Both extracted members were already present and their sizes, CRC-32 and SHA-256 were rechecked. The input manifest records expected byte offsets, member paths, and hashes of the extracted and staged PLYs. The repository has an Apache-2.0 `LICENSE`; its README's `LICENSE.md` link is missing at the pinned commit. The public data table supplies no separate grant for the Drive files. This folder publishes the acquisition recipe, IDs and measurements. [Archive/member manifest](REGISTRATION.json) · [FieryGS repository license](https://github.com/PKU-VCL-Geometry/FieryGS/blob/f70fbe26d22431c7acd93a745861dd47ba4307d7/LICENSE) · [Foreground fetch](../t101-playground-holdout/fetch.py) · [Camera fetch](../t111-playground-shot-choice/fetch_cameras.py)

For material dynamics, T101 subtracts the source bounding-box midpoint, scales positions uniformly by 0.7768849039018435, and stores them as float32. The demo subtracts the staged foreground mean and adds a world y lift of 0.75. The affine scale applies equally to the Gaussian radii, preserving source site order. The registration verifies every staged material center from the original. For the shot readout, use original Gaussian centers/covariances and original release cameras with `(p - camera_position) @ rotation`. The camera field in `recipe.json` controls the demo orbit during dynamics. Readout camera IDs and row hashes are in `REGISTRATION.json`. [Similarity preparation](../t101-playground-holdout/prepare.py) · [Camera projection and opacity weights](../t107-visible-burn-progression/measure.py)

From the repository root, Python and NumPy suffice for the local rebuild. The first three commands stage the two members on a fresh machine. On a machine with the cached files the fetchers use those files. The fourth command regenerates the recipe, shell and registration and compares them to the frozen copies. The fifth command explicitly refreshes the bounded upstream metadata check with Git and network access.

```text
python tracks/tog/tasks/t101-playground-holdout/fetch.py
python tracks/tog/tasks/t101-playground-holdout/prepare.py
python tracks/tog/tasks/t111-playground-shot-choice/fetch_cameras.py
python tracks/tog/tasks/t120-next-release-registration/register.py
python tracks/tog/tasks/t120-next-release-registration/inventory.py
```

## Boundary for the next experiment

After T119 identifies a transferable operation, freeze the exact methods and full-cost matched baseline, measurement schedule, process budget and correctness checks before producing this edit's matte weights or trajectories. Use dt = 1/60 and 90 steps after the second click. Round each eligible site's static opacity to integer micro-pixels and cross at `ceil(total / 4)` in each of the two cameras. Return the lightest qualifying stroke for the joint shot, preserving zero-mass undefined and both-fail outcomes. Include all attempted sibling work in end-to-end cost. The original T111 driver and its weight files use cameras 0/153, so the next runner must read these new IDs and weights explicitly. No matte, reference label, RNG observation or latency has been generated for T120. [Frozen protocol](PROTOCOL.md) · [T111 integer-matte reference](../t111-playground-shot-choice/reference.py)
