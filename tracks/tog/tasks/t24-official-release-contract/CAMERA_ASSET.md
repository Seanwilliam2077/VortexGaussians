# T24 camera, observation-data and asset-carrier audit

29 October 2026. Local inspection only, pinned to Vol3DGS commit **`dd175d52938264770a783cbb7929e20572675544`** recovered by root's connector audit. No source request, imported code, numerical execution or asset retrieval was performed by this reviewer.

Inspected all of [scene/cameras.py L1–126](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/scene/cameras.py#L1-L126), [scene/dataset_readers.py L1–274](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/scene/dataset_readers.py#L1-L274), [README L1–89](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/README.md#L1-L89), and [LICENSE L1–21](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/LICENSE#L1-L21). The unique code inspection totals **400 lines**. Helper modules and downstream rendering/training were outside this allocation; their behavior is not inferred from function names. The T24 protocol and [T23 conditional mapping](../t23-model-workload-audit/SEMANTICS.md) supplied the audit questions.

## Confirmed implementation observations

| Area | Pinned evidence | Confirmed behavior |
|---|---|---|
| Camera transforms | `cameras.py` L18–28, L47–56; L89–98 | Cameras retain R/T and FoVs. They call `getWorld2View2(R,T,trans,scale)`, transpose its result, combine it with a transposed projection, and obtain a center from the inverse view transform. Defaults are zero translation and scale1. |
| Projection bounds | `cameras.py` L47–54, L89–96, L114–125 | Camera/ZipnerfCamera pass near .01 and far100 to the projection helper. MiniCam accepts caller-supplied bounds/transforms. These declarations do not define a continuous ray integral. |
| COLMAP observations | `dataset_readers.py` L75–112, L139–162 | Quaternion rotation is transposed; translation is retained. Only undistorted SIMPLE_PINHOLE/PINHOLE branches are accepted. Focal lengths and image dimensions determine FoVs. Images are opened from the dataset; ordered image names determine the default every-eighth evaluation split. |
| Scene scale descriptor | `dataset_readers.py` L52–73 | Camera centers determine a mean translation and maximum-radius-times1.1 descriptor. The function returns this metadata; it does not establish physical units or show how downstream normalization is applied. |
| Synthetic cameras and backgrounds | `dataset_readers.py` L186–233, L235–245 | NeRF camera-to-world matrices have their Y/Z columns flipped, are inverted, and provide transposed R plus T. RGBA observations are divided by255 and composited over selected white/black background before byte RGB conversion. Train/test transforms come from separate JSON files. |
| Image versus field colors | `cameras.py` L38–45, L79–87; `dataset_readers.py` L114–120 | Camera images are clamped then multiplied by an optional mask. Point-cloud byte RGB is divided by255. Neither operation establishes bounds for learned Gaussian SH colors. |
| Initial geometry | `dataset_readers.py` L164–183, L247–268 | COLMAP points become an initialization PLY; when a synthetic point cloud is absent, the reader generates random points/colors. This inspected PLY path carries positions, RGB and normals, not a pretrained density/covariance field. |

## Still unresolved for the T21/T22 operation

This allocation does not define normalized pixel-ray directions, camera-depth versus world-distance parameterization, physical scene units, or the precise projection-helper conventions. Thus near/far cannot be substituted for T23's `[a,b]` without a justified mapping. A complete Gaussian-support policy and any rasterizer culling or early termination remain outside these files.

The shown observation conversions contain no explicit transfer-function decoding. They do not establish a linear-radiance color scale throughout the pipeline, nor that Gaussian colors are constant along a ray or confined to `[0,1]`. Likewise, synthetic-image background compositing does not establish the renderer's supplied background. These are specific missing links, not claims that another code path cannot provide them.

## What the README actually supplies

[README L40–56](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/README.md#L40-L56) links NeRF-synthetic, MipNeRF360 and other training datasets, then shows a training command writing a local output model. [L58–64](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/README.md#L58-L64) renders from a supplied output-model path. The inspected README does **not identify a downloadable pretrained Vol3DGS density checkpoint**, its density/covariance/SH fields, size or asset-use terms. This is a statement about that README, not an exhaustive absence claim for the project.

Training observations and initialization points must not be relabeled an existing learned-volume carrier. Producing a carrier by training would be new computation, outside this audit. The separate tomography-repository pointer at L73–74 is not permission to expand this source scope or a demonstrated equivalent colored-emission asset.

## Permission evidence and metadata value

The root LICENSE states MIT terms at L1–21. Both inspected code files retain an Inria header at L1–9 referring to non-commercial research/evaluation use under `LICENSE.md`. This records distinct notices; it does not resolve their applicability or imply that root MIT terms relicense third-party code, submodules, datasets or pretrained weights. No dataset-use terms were acquired by this reviewer.

For root's remaining bounded metadata choice, the directly linked [MipNeRF360 page](https://jonbarron.info/mipnerf360/) and [3DGS project page](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) could clarify observation/camera provenance, advertised extent and permissions. They have limited value for the decisive pretrained-Vol3DGS-carrier question: any listed model would still need its own verified density semantics and provenance. The Kaggle synthetic-data link is also an observation-data pointer in this README. None of these endpoints was fetched here, and their actual contents are not asserted.

**Decision for this allocation:** camera and observation-format evidence has become concrete, but no usable pretrained density asset is established. Do not prepare an applicability run from these files alone. Root's separate field/rasterizer and metadata audits must resolve the remaining release contract; dataset availability by itself cannot satisfy it.
