# Where the brush alternatives become visible

[Camera-calibrated figure (PDF)](woodpile-mattes.pdf) · [PNG](woodpile-mattes.png) · [Native T109 trajectories](../evidence/native/) · [Projection and validation receipts](validation.json)

Both brush alternatives use the same seed-53 Firewoods parent. Orange on the substrate represents an initially eligible shell site that ignited between the second brush and frame 270, 90 steps later. Teal shows the remaining eligible shell. The plotted overlays use the same optical-transmittance weights and calibrated cameras as the timing task. The warm-gray surface is an independently drawn surface of binned material-center density. All candidates from one camera share a single crop and background.

| View | Initial shell mass (micro-pixels) | Light ignited mass | Full ignited mass | Light / full share |
|---|---:|---:|---:|---|
| Camera 0 | 282,825,750 | 33,067,868 | 98,510,146 | 11.692% / 34.831% |
| Camera 124 | 829,199,132 | 90,899 | 608,836 | 0.011% / 0.073% |

Across views, 190 sites ignited under the light brush and 493 under the full brush. The numerator and denominator include all eligible sites and their entire on-screen contribution in the original registered raster. Label percentages use integer micro-pixels rounded per site before summation. Color masks use unrounded, front-to-back pixel contributions. In camera 124 the contribution of all newly ignited sites together is below one pixel of unit opacity even for the full brush. The near absence of orange is the measured result.

## Source appearance and attribution

Qianfan Shen et al. made the FieryGS Firewoods scene available through an external Drive archive. The pinned project repository contains an Apache-2.0 license. The repository and project page identify the dataset link. We found no asset-specific republication grant for appearance data on these pages or in the 527-member archive inventory (no file named for a license, terms, copyright, notice, or README). This check does not establish authorization to distribute the fitted appearance or source photographs. [Pinned dataset link](https://github.com/PKU-VCL-Geometry/FieryGS/tree/f70fbe26d22431c7acd93a745861dd47ba4307d7#data) · [Pinned project license](https://github.com/PKU-VCL-Geometry/FieryGS/blob/f70fbe26d22431c7acd93a745861dd47ba4307d7/LICENSE) · [Authors and paper](https://pku-vcl-geometry.github.io/FieryGS/)

The published diagrams visualize spatial measurements from the original material centers. We aggregate their counts into 0.014-unit cubic bins, cap each bin at three observations, smooth the counts with a separable (1,2,1)/4 kernel and triangulate the density-0.18 surface by marching tetrahedra. A single artificial light shades the resulting surface using original, neutral diagram colors. Gaussian SH coefficients, source photographs, source textures, and raw geometry are omitted from the published figures. The measured opacity overlay still uses the pinned covariance, opacity, camera, and native labels. The full crop is shown for each camera's relevant foreground extent, clipped to its original image borders.

## Reproduce

Use the original foreground PLY and calibrated cameras.json in the directory supplied as `--source`. Requires Python, NumPy, Pillow, ReportLab, and Poppler for the companion PNG. The intermediate arrays and binned geometry stay in the ignored `local/` directory.

```text
python project.py --source PATH_TO_FIREWOODS
python figure.py --source PATH_TO_FIREWOODS
pdftoppm -r 200 -png -singlefile woodpile-mattes.pdf woodpile-mattes
```

Projection checks include six independently evaluated pixels in each camera (deduplicated/in-frame as in T107), total alpha mass conservation, agreement with the archived per-site shell weights, and exact agreement of integer numerators and denominators with the native ground-truth table. The archive ZIP tail SHA-256 used in the license-file inventory was `2e5426d14af138b2378a0525abe4a2dcd5faa1aad81e48e3f7e390f303003f6a`. File identities for the measured inputs are in the validation receipt. [Registered camera metric](../../t107-visible-burn-progression/PROTOCOL.md)

The two candidate panels for camera 0 use the same pixel crop, (130, 117) to (298, 202), in the original quarter-resolution raster. Both panels for camera 124 use (49, 99) to (371, 263); the upper bounds are exclusive. The generator checks that each displayed crop contains the full shell and both burnt-mass integrals. The one-page 500 × 303 pt PDF and its 200 dpi PNG companion were rasterized and visually checked. Their respective SHA-256 hashes are `7cab49d83a90f42f8252380ede81a1d027b5551c0eb781e4aad6c914be025780` and `13713a6b74381aab713fee9a06753c75a8897214a75d29e89f6bc20a1e8fda33`.
