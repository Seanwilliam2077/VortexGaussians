# T24 — density storage and activation contract

29 October 2026. Static inspection only, by pressure_screen. Official revision: `dd175d52938264770a783cbb7929e20572675544`. Read all 594 lines of `scene/gaussian_model_volr.py` and all 255 lines of `utils/general_utils.py`: **849 unique source lines**. No additional source, import, numerical evaluation or asset access. This note complements the root's separate renderer/training audit; it does not infer their behavior from these two files.

## Source facts

The [model, lines 34–43](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/scene/gaussian_model_volr.py#L34) selects scale exponential, ordinary opacity sigmoid, and a separate volumetric activation. Let `z` denote stored `_opacity_volr`, `s=exp(_scaling)` and `a` its activated value. The getter calls the following branches in [general utilities, lines 18–40](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/utils/general_utils.py#L18):

| `reparam_type` | Activated value | Coefficient returned by both `get_density` and `get_opacity_volr` |
| --- | --- | --- |
| `ours` | sigmoid(z) | `-log(1-0.99*a) * mean(1/s) / 2.506` |
| `ever` | sigmoid(z) | `-log(1-0.99*a) / min(s)` |
| string `None` | softplus(z) | `a` |

The two getters are identical ([model, 125–133](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/scene/gaussian_model_volr.py#L125)); neither returns the separate sigmoid `_opacity`. The constructor chooses `ours` and initializes the activation functions ([46–65](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/scene/gaussian_model_volr.py#L46)). Changing the flag alone does not rerun that initialization. The root's separate `train_volr.py:41–42` audit confirms that its training caller explicitly sets the flag and calls setup; this reviewer did not inspect that third file. The string `None` branch is distinct from Python `None`; other strings do not define a complete conversion branch.

Covariance uses `L=R*diag(scaling_modifier*s)` and `Sigma=L*L^T`, packed as xx, xy, xz, yy, yz, zz. The quaternion is normalized in the builder, with scalar component first ([model, 27–37 and 135–136](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/scene/gaussian_model_volr.py#L27); [utilities, 122–168](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/utils/general_utils.py#L122)).

PLY serialization writes float32 vertex properties: positions, zero placeholder normals, SH coefficients, both **raw** opacity variables, **raw log-scales**, and raw quaternion components ([model, 252–285](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/scene/gaussian_model_volr.py#L252)). Loading requires `opacity_volr`, reconstructs SH arrays against the constructor's `max_sh_degree`, restores raw tensors, and sets active degree to that maximum ([299–342](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/scene/gaussian_model_volr.py#L299)). It does not decode density into the stored property.

`capture/restore` includes raw tensors, active SH degree, optimizer state and spatial learning-rate scale, but not `reparam_type`, activation selection or maximum SH degree ([67–101](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/scene/gaussian_model_volr.py#L67)). PLY likewise contains no such mode tag, camera, background, ray interval, world-unit declaration or color-space contract. The feature getter only concatenates SH arrays ([115–119](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/scene/gaussian_model_volr.py#L115)); actual color evaluation is outside this two-file audit.

## Independent interpretation and limits

- **Paper/code normalization:** the `ours` getter includes division by 2.506, absent from paper equation 20 as recorded in T23. The released getter must not be replaced silently by the paper formula. The factor may belong to the actual rendering kernel's convention; that kernel was not inspected in this task. These two files do not establish an implementation error or final-image mismatch. T23's conditional ray mapping uses a generic coefficient kappa and does not fix this normalization factor.
- **Reverse helpers are not algebraic inverses as written.** In [utilities, 43–61](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/utils/general_utils.py#L43), the `ours` branch divides only the exponential by 0.99 before subtracting from one; the inverse of the forward expression would divide the whole difference. The `ever` reverse uses maximum rather than minimum scale and omits the inverse 0.99 factor. Clamping further prevents general inversion. These are source-level algebraic observations, not executed failure cases. The helpers participate in densification ([model, 438–489](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/scene/gaussian_model_volr.py#L438)); their asymmetry does not by itself invalidate decoding a particular saved tensor through the forward getter.
- **Numerical assumptions:** finite positive scales, a nonzero scaling modifier/quaternion and finite latent values are required for a usable positive-definite covariance/density. The inspected loader does not enforce these. Builder normalization has no zero-norm guard, and density diagnostics print rather than enforce validity. Raw SH storage supplies no [0,1] output bound or linear-radiance guarantee.
- **Carrier decision:** static code supplies a conditional decoding route, provided the original activation mode/setup, SH configuration and remaining renderer/camera semantics are known. Serialization functions do **not** establish that a pretrained file exists, contains valid data, has usable permissions, or supplies the missing context. No actual carrier is qualified by this note.

Both file headers attribute Inria/GRAPHDECO and describe noncommercial research/evaluation use subject to a license file (lines 1–9). This records source-header wording only; it is neither an asset license nor a legal conclusion about repository-wide permissions.

## Inspected local identities

| Pinned source | Bytes | SHA256 |
| --- | ---: | --- |
| `scene/gaussian_model_volr.py`, lines 1–594 | 30308 | `59410e4707b7628b013f2cece72a440be69bad3d5830f889617ef7a14893ef2a` |
| `utils/general_utils.py`, lines 1–255 | 8705 | `0fa5c53974962d4e93ceb757c6638ae3b1336b98f86d7abbb7184cd245600ae8` |
