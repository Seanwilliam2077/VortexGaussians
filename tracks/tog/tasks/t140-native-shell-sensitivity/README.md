# The woodpile choice survives a native tag-matte measurement

Replacing the offline target projection with the original WebGL renderer changed the amount of visible gas over the target. At the main camera's +90 deadline the lighter brush reached **46.84%** of the native target and the full brush **50.85%**, versus 39.62% and 42.57% previously. The registered quarter-target editing decision still accepts the lighter brush. Direct native tags of the wood sites actually ignited by the same deadline give **12.28%** and **36.35%**. The material criterion still requires the full brush. Both criteria return neither brush in camera 124. This sensitivity test addresses the original observed choice. Its time was measured previously with the original offline weighting. [Complete numerical results](evidence/SCORE.json) · [Frozen sensitivity protocol](PROTOCOL.md) · [Original delivered-choice timings](../t129-native-image-choice/README.md)

| Camera | Steps | Gas, light, previous → native | Gas, full, previous → native |
| --- | ---: | ---: | ---: |
| 0 | +44 | 36.9860% → 39.7894% | 68.4792% → 73.9786% |
| 0 | +90 | 39.6201% → 46.8411% | 42.5720% → 50.8520% |
| 124 | +44 | 0.0000% → 0.0000% | 4.4899% → 3.2487% |
| 124 | +90 | 0.0059% → 0.0026% | 0.0024% → 0.0009% |

| Camera | Native target mass in 470 × 264 sampling units | Prior target mass | Material at +90, light, previous → native | Material at +90, full, previous → native |
| --- | ---: | ---: | ---: | ---: |
| 0 | 271.764 | 282.826 | 11.692% → 12.280% | 34.831% → 36.347% |
| 124 | 847.879 | 829.199 | 0.011% → 0.065% | 0.073% → 0.321% |

The source-calibrated 940 × 528 native raster supplied projected mass for 2,371 original target splats and two endpoint subsets (190 light, 493 full). Every tagged draw kept all 34,687 fitted splats and their opacity. Red accumulated tagged material, green accumulated all material, and blue accumulated its complement. The matte passes used the original projection, native anisotropic footprints, opacity, clipping, depth buckets, blending and floating-point framebuffer, with rest state and no visible dynamic stream. Green agreed with native alpha at every pixel, red and blue each stayed below total opacity, and the largest absolute red-plus-blue versus green residual was 0.013855 over the seven draws. The scorer uses direct red opacity. Repeating camera 0 after both views reproduced both downsampled arrays byte for byte. The browser run took 3.75 seconds including setup and export. All sixteen historical color and wood-only images matched their original hashes. Only the weights supplied to the eight original contrast masks changed. [Camera, channel checks and matte hashes](evidence/CAPTURE.json) · [Original contrast definition](../t127-woodpile-native-camera/observer-contract.md)

Run `python verify.py` for a standard-library check of all eight scores and four material endpoints using the per-view capture receipts and the [nonspatial contrast histograms](evidence/CONTRAST.json.gz). The original fit and appearance PNGs are needed to repeat acquisition. First run `python prepare.py ASSET_DIRECTORY T127_IMAGE_DIRECTORY FRESH_LABELS_JSON`. Then run `node capture.mjs ASSET_DIRECTORY FRESH_LABELS_JSON NEW_PRIVATE_MATTE_DIRECTORY NEW_PUBLIC_DIRECTORY/CAPTURE.json` with the T127 browser runtime, followed by `python score.py ASSET_DIRECTORY T127_IMAGE_DIRECTORY NEW_PRIVATE_MATTE_DIRECTORY --output NEW_PUBLIC_DIRECTORY`. The [instrumentation](native-matte.mjs) also exposes top-left Float32 arrays directly inside a paused page for a subsequent decision implementation. No treatment was simulated in this experiment.
