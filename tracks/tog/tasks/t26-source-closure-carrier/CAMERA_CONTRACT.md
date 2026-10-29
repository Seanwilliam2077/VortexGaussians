# T26 — camera helper contract and remaining input checks

29 October 2026. Static inspection at main commit **`dd175d52938264770a783cbb7929e20572675544`**. Read `utils/camera_utils.py` L1–82 and `utils/graphics_utils.py` L1–77: **159 unique new code lines**. Revisited only the already acquired `utils/general_utils.py` L80–86 for image layout, with prior [camera/dataset](../t24-official-release-contract/CAMERA_ASSET.md) and [loader](../t25-volume-kernel-contract/LOADER_CONFIG.md) evidence. No import, numerical execution, network access or asset inspection.

## Pose, center and projection bodies now resolved

[graphics_utils.py L31–49](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/utils/graphics_utils.py#L31-L49) builds the homogeneous matrix `H=[R^T,t;0,1]`. `getWorld2View2` inverts H, extracts its translation as camera center C, replaces that center by `(C+translate)*scale`, then inverts again and returns float32. It retains the inverse matrix's upper-left block; it does not multiply that block by scale or transform Gaussian parameters.

This is a generic inverse-based construction, not validation that supplied R is orthonormal. For invertible `A=R^T`, the algebraic center is `C=-A^-1*t`; substituting `-R*t` additionally requires a rotation assumption. Prior dataset evidence establishes transposed COLMAP rotations and the Blender Y-up/Z-back to COLMAP Y-down/Z-forward axis flips; actual input poses remain unverified.

[camera_utils.py L49–52](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/utils/camera_utils.py#L49-L52) passes no translate/scale overrides. The inspected Camera defaults therefore remain zero translation and scale1. Scene's separately computed radius is not fed into this camera constructor by this path. A general center-rescaling helper must not be described as proof of automatic scene normalization.

[graphics_utils.py L51–77](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/utils/graphics_utils.py#L51-L77) constructs symmetric FoV bounds with positive-Z projection and homogeneous `w=z`. In exact algebra, near/far map to normalized depth0/1. Trigonometric FoVs are in radians; focal conversions use pixel dimensions. These are projection conventions, not a definition of extinction's distance measure or integration endpoints. Camera's existing matrix transposes implement its stored row-vector convention. The separate point-transform helper (L22–29) multiplies homogeneous row points and divides by the last coordinate plus `1e-7`; this inspection does not establish that the active volume kernel calls it.

## Resolution, observation colors and alpha

[camera_utils.py L19–41](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/utils/camera_utils.py#L19-L41) selects resolution from the requested factor/width and resolution_scale. The default `-1` reduces widths above1600; factor cases use rounding, other cases integer conversion. FoVs are retained when constructing Camera. Effective pixel dimensions therefore depend on these settings; a future ray selection must use the actual rendered resolution.

The inherited [PILtoTorch body, L80–86](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/utils/general_utils.py#L80-L86) resizes, divides image-array values by255 and returns channel-first layout. Neither this helper nor the newly inspected loader establishes a linear-light transfer function. Taking the first three channels, then Camera's clamp/mask handling, concerns observations, not learned Gaussian SH bounds.

**Static alpha-axis discrepancy:** camera_utils L43–47 takes RGB from channel axis0, but detects an alpha mask using `shape[1]==4`. For the established CHW layout, that tests image height. An RGBA observation with height other than4 would not pass its alpha through this branch. No such observation was loaded here; this is a conditional source consequence, not a measured rendering failure. The prior synthetic reader already composites RGBA into RGB before this helper, so the discrepancy must not be generalized to every dataset path.

## Camera JSON and remaining validation

[camera_utils.py L62–82](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/utils/camera_utils.py#L62-L82) inverts the raw `R^T,t` matrix and stores its center/orientation plus focal lengths computed from the supplied dimensions. Prior Scene code calls it on camera-info records before resized Camera construction. Thus exported dimensions need not equal a later render resolution. T25 established that the rendering loader rebuilds cameras from source data rather than restoring this JSON.

The missing helper **implementations** are now inspected. Still input-dependent are finite/invertible poses, orthonormality if rotations are assumed, valid FoV/resolution, actual image layout/range, mode/background configuration, and the correspondence between images and camera records. Physical scene units and linear radiance are not established. Pixel-center/ray normalization and the integration/culling domain belong to the separately audited rendering path; this helper note does not certify them or the completeness of Gaussian support. No trained carrier or applicability measurement is qualified here.

## Source identities

| Local acquired source | Inspected lines | SHA256 |
|---|---|---|
| `1-camera_utils.py` | 1–82 | `a450a6bcd3630a183f0a6be1b75a89e91444471b12f460613b8bbeb23a9c3bcef` |
| `2-graphics_utils.py` | 1–77 | `d6e75de8161e98b72c2691e8a944a842e1b6625d2306035d079c868ac632edfc` |

The previously acquired general-utils SHA remains `0fa5c53974962d4e93ceb757c6638ae3b1336b98f86d7abbb7184cd245600ae8`; its seven revisited lines are inherited evidence, not additional newly acquired code.
