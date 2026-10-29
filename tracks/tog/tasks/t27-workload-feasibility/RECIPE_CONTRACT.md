# T27 — installation and training recipe contract

29 October 2026. Static inspection of five acquired text files, **166 lines** total. Main sources are pinned to `dd175d52938264770a783cbb7929e20572675544`; dependency setup is pinned to `5eca1185550c35e3236c511c311aee3eb9129169`. No installation, shell-script execution, package import, environment probe, remote download or training was performed by this reviewer. Prior source audits supply explicitly identified defaults; actual machine capability is root's separate inquiry.

## Versions and installation actions

| Recipe | Inspected source facts |
|---|---|
| [environment.yml L1–14](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/environment.yml#L1-L14) | Environment `vol3dgs`; pytorch/conda-forge/defaults channels; CUDA toolkit11.7, Python3.9.20 and pip24.2. `plyfile`, tqdm, wandb and matplotlib are unpinned. This file alone does not install a specified torch version. |
| [requirements.txt L1–18](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/requirements.txt#L1-L18) | Pins torch2.0.1, torchvision0.15.2, torchaudio2.0.2, slangtorch1.3.7, mkl2024.0, Cython0.29.36 and open3d0.18.0; constrains NumPy<2. Other listed packages are unpinned. No torch wheel/CUDA-index URL is fixed here. |
| [install.sh L1–84](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/install.sh#L1-L84) | Writes activation/deactivation hooks under the current conda prefix; discovers/falls back to a CUDA root and exports library/include/linker paths. The include search hardcodes `lib/python3.9/site-packages/nvidia`. It then invokes requirements installation, simple-knn, fused-ssim, diff-gaussian-rasterization and editable slang-gaussian-rasterization installation. |
| Acquired dependency `setup.py` L17–30 | Declares package version0.1.0 and Apache2.0 metadata, but requires only unversioned `slangtorch` and `torch`. This does not independently reproduce the main requirements pins. One shader path is named in package_data; that declaration alone does not verify an installed wheel's complete runtime contents. |

The script assumes Bash/POSIX commands and Unix library paths; it is not a verbatim PowerShell recipe. Its deactivation hook unsets CUDA_HOME/LDFLAGS but does not restore all modified library/include paths. The inherited [README L21–32](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/README.md#L21-L32) additionally asks for submodules and a system CUDA/nvcc toolkit, and reports Ubuntu22.04, driver525.147.05 and a3090Ti test configuration. This is historical recipe evidence, not a measured requirement or a verified configuration of this machine.

Package acquisition/build actions embedded in these recipes were **not invoked**. These files are not a fully resolved dependency lock: transitive versions, exact wheels, compiler compatibility, external build inputs and installed contents remain unverified.

## Different training recipes remain different

[scripts/all_datasets.sh L1–18](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/scripts/all_datasets.sh#L1-L18) contains thirteen commands using author-local absolute input paths. All select `slang_volr`, evaluation, `num_cams=-1`, disabled opacity reset, softplus RGB and percent_dense=.01. They are training commands, not checkpoint-download records.

| Group and scenes | Distinguishing literal flags |
|---|---|
| MipNeRF360: bicycle, bonsai, garden, flowers, counter, kitchen, room, treehill, stump (L2–10) | Minimum-opacity threshold .05; split/clone thresholds `1e-7`/`5e-5`; densification interval200; scene_extent_mult2; wandb enabled. |
| Tanks and Temples: train, truck (L13–14) | Threshold .01; split/clone `9e-6`/`5e-4`; interval100; extent multiplier5; **AbsGS enabled**; wandb enabled. |
| DeepBlending: drjohnson, playroom (L17–18) | Threshold .03; split/clone `1e-7`/`5e-5`; interval200; extent multiplier1.5; no AbsGS flag; wandb only on playroom. |

All specify opacity_volr_lr=.03, feature_lr=.003, and initial/final position learning rates `.00016`/`.00001`. None overrides iterations, resolution or reparameterization mode. The already inspected pinned argument defaults give30,000 iterations, densification start/end500/15,000, and resolution−1; the camera helper's default width policy can downsample above1600. These are configured values, not observations of completed iterations, effective scene complexity or training time. Mode provenance still needs the [T25 loader contract](../t25-volume-kernel-contract/LOADER_CONFIG.md).

The inherited README's Lego example instead sets densify_from_iter50,000, beyond its default training length. That disables its scheduled densification; it must not replace the thirteen different recipes without disclosure. The Tanks commands' AbsGS flag also differs from the README statement that the paper did not use AbsGS. This is a source-level recipe distinction, not evidence that any reported result was reproduced incorrectly.

Literal output directories repeat across all MipNeRF360 commands and across both DeepBlending commands. Any future bounded run would need explicit output separation. No original directory or checkpoint was opened here.

## Feasibility boundary

These texts specify candidate training procedures, not an existing learned volume. They establish no acquired scene bytes, usable checkpoint, peak GPU/RAM requirement, elapsed runtime, completed optimization, usable-ray frequency or artifact permissions. Executing the entire multi-scene script would exceed a single-scene feasibility probe. No run, scene choice, reduced iteration count or recipe change is authorized by this note; root must combine the source evidence with its separate environment and scope decision.

## Inspected hashes

| Acquired file | Lines | SHA256 |
|---|---|---|
| `1-environment.yml` | 1–14 | `28b799cc254f6763aba1492bf72af3499cf66f76aa37a7e3e686ecffda7b8047` |
| `2-install.sh` | 1–84 | `54d8557a7455b2e65c99487326002cf8e9e7978fa7e2a1051cb13ce39f14d4a6` |
| `3-requirements.txt` | 1–18 | `b9c9e589f05366bb4fc19b5784b56fadc0af516158bee675b869cdaf47ecfb62` |
| `4-all_datasets.sh` | 1–18 | `be06fe8aedc3ccac6a6b1103a018f1befbd2ee7b62a02f45c025e4489880f242` |
| `5-setup.py` | 1–32 | `633eef0c89a85e4d6c81a2acfef32fa6b75bf425bf0d001399bda519e368fa99` |
