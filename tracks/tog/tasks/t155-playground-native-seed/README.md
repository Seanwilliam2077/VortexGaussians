# Fire-X GS Playground seeds the air differently before the first update

The registered Playground ignition brush fails the exact gas-sharing prerequisite. Its three edited wood voxels reach seven open face neighbors. Initializing the 620 K arm sets all seven gas cells to 620 K. The 790 K arm sets them to the native cap of 750 K. The shortest path through wood to an exposed wood cell has **zero edges**. Pulling a common gas state from an ordinary cache at initialization would already produce the wrong field for one alternative. The case ends here under the original stopping rule. [Registered brush](../t152-playground-brush-clearance/PROTOCOL.md) · [Two full grid digests, differing cells and temperatures](SEEDS.json)

| Geometry and source checks | Value |
|---|---:|
| Original fitted Gaussians | 1,268,409 |
| Ordered crop rows matching full model coordinates exactly | 80,023 |
| Maximum error outside registered source cell, in source-voxel units | 0.00000314 |
| Fitted Gaussians passing the native collision filters | 72,819 |
| Grid cells occupied by those collision Gaussians | 7,764 |
| Wood cells after native closing and filling | 2,659 |
| Total solid cells including wood, fitted obstacles and floor | 34,640 |
| Changed wood cells at the frozen center and 4.4 cm radius | 3 |
| Candidate open neighbors from T152 | 8 |
| Confirmed open neighbors | 7 |
| Difference at initialization in each of those cells | 130 K |

The full collision mask closes the earlier candidate at (40,42,17). The other seven indices appear in the machine-readable result. All eight candidate centers lie 0.502–0.582 m above the fitted floor. None contains a point within 0.000002 of either native opacity or scale cutoff in the collision box. The complete foreground alignment, wood-grid digest and painted indices match T152. The two seed grids are independently initialized over 88 × 88 × 104 cells. Each open site uses the hottest adjacent wood face above 450 K and caps the assigned temperature at 750 K. [Measured coordinates and floor clearances](SEEDS.json) · [Original preparation](https://github.com/zju3dv/PhysStudio/blob/3e084fe7a71eface1cf42720a9fe896c993b967e/firex_gs/prepare.py#L40-L79) · [Native mask construction](https://github.com/zju3dv/PhysStudio/blob/3e084fe7a71eface1cf42720a9fe896c993b967e/firex_gs/scenes.py#L208-L243) · [Native initialization](https://github.com/zju3dv/PhysStudio/blob/3e084fe7a71eface1cf42720a9fe896c993b967e/firex_gs/wood_thermal.py#L6-L60)

The original archive member passed the central-directory length and CRC checks. Its 314,566,964 decoded bytes have SHA-256 `3d6dcb62f5ec85b592ed9e2c419ad81585dbb6d300aa472c637feb6dc3a50588`. The serial acquisition reached its 420 s deadline with 21 recorded ranges. Its 279,869,241 decoded prefix bytes were retained. A preregistered parallel recovery took 52.43 s, replayed each earlier compressed range, compared the previous decoded prefix byte for byte, and validated the entire member. The geometry process then took 3.01 s on CPU, including startup. This elapsed time describes the geometry qualification only. [Original public FieryGS archive](https://drive.google.com/file/d/1NFXzr0YU3q1_ezjWVEgTmd-R8JX4J0lL/view) · [Partial transfer](FIRST_TRANSFER.json) · [Registered recovery](RECOVERY_PROTOCOL.md) · [Final receipt](ACQUISITION.json) · [CPU environment and timeout](RUN.json)

The worker executes the pinned PyTorch quaternion conversion and robust ground-fit functions on CPU, with the original float32 point attributes and native float64 least-squares fits. NumPy/SciPy reproduce the material and obstacle voxelization and the six-neighbor initial gas rule. This qualifies the declared geometry and initializer. We did not run the Warp gas dynamics, observe a rendered difference, compare wall-clock speed of solvers or establish an artist need. It leaves T149's conditional conduction bound applicable to a genuinely buried edit. The original fixed Playground brush is exposed, so this branch requires no later dynamics or timing experiment. [Ground implementation](https://github.com/zju3dv/PhysStudio/blob/3e084fe7a71eface1cf42720a9fe896c993b967e/rainy_gs/scene.py#L162-L186) · [Earlier conditional bound](../t149-firex-exchange-support/README.md)

## Reproduction

Use a fresh private asset directory, the same [T152 mapping and label assets](../t152-playground-brush-clearance/README.md), the [T101 original foreground](../t101-playground-holdout/fetch.py), and a local checkout of PhysStudio at `3e084fe7a71eface1cf42720a9fe896c993b967e`. The scene loader is referenced by its SHA-256 in `full_seed.py`. A locally retained original PLY can be used directly when it matches the final receipt. To acquire the single member from the public ZIP, run `python -B acquire.py PRIVATE_CACHE --receipt LOCAL_RECEIPT.json`. The recovery script additionally requires the interrupted first receipt and its matching partial file. Keep ranges and models outside Git.

From this directory run the following with CPU PyTorch, NumPy and SciPy. Compare the resulting indices, counts, gas digests and D with `SEEDS.json`. The floor fit may differ by roundoff between linear algebra implementations.

```text
python -B full_seed.py PRIVATE_CACHE/scene_point_cloud.ply T152_MAPPING_DIR PHYSSTUDIO_CHECKOUT ORIGINAL_FOREGROUND.ply --out LOCAL_SEEDS.json
```
