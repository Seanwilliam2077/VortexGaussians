# T24 — the active volume renderer is a pinned dependency

29 October 2026. Static inspection only, at official commit dd175d52938264770a783cbb7929e20572675544. Source identities and byte counts are in [source-inventory.json](source-inventory.json). Root inspected all100 lines of gaussian_renderer/__init__.py and all356 lines of train_volr.py. No external module was imported or run.

## Confirmed caller paths

[train_volr.py](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/train_volr.py), lines317 and330–338, distinguishes three backends. The volume branch imports slang_gaussian_rasterization.api.inria_3dgs_volr and selects GaussianModelVolr. The default backend string is slang; a filename containing volr alone does not select the volume path. The official README's example explicitly supplies slang_volr.

The acquired root gaussian_renderer/__init__.py is the inria_cuda alternative. Its lines14–16 import the classic rasterizer/model; lines55/90 pass get_opacity, and lines73–78 optionally evaluate SH with a lower clamp. These observations must not be attributed to the separately imported volume backend. Acquiring this file exposed a path distinction; it did not obtain the volume kernel.

The pinned recursive tree is complete (truncated=false) and identifies submodules/slang-gaussian-rasterization as a gitlink at5eca1185550c35e3236c511c311aee3eb9129169. Its implementation bodies are outside this task's no-submodule-expansion contract. The mapping between that dependency's density input and its normalization, ray parameter, SH evaluation, culling, alpha threshold, early termination and accumulated RGB is consequently unresolved. No same-model executable reference or certified tail policy was acquired.

## Output and run-state distinctions

- Training lines33–44 construct the model/scene, restore if requested, then set reparam_type and call setup_functions. White/black background depends on dataset.white_background; line90 optionally uses a random background. The model serialization evidence must therefore be read together with actual run flags and caller setup.
- Lines92–98 pass the returned image directly to the training loss. GUI output at68 and evaluation/report paths at227/278 clamp images to[0,1]. A displayed or metric image does not establish bounded raw component colors or the unprocessed continuous-integral target. A later comparison must specify which output is judged and apply its rule fairly to every method; T22's old target is unchanged.
- Lines170–174 save captured tensors/checkpoints. Lines186–190 write cfg_args from the argument object passed to the logger; training line31 passes dataset. This audit did not inspect arguments/__init__.py or render.py, so it does not infer the complete saved configuration or the separate rendering loader's default behavior. In particular, it cannot verify a particular artifact's decoding flags from a README command.

## Consequence

The main repository supplies an actual density-model serialization route and a concrete backend dependency. It does not yet supply a fully inspected continuous-overlap operator or a qualified existing trained asset. Caller names and tensor fields cannot replace the missing dependency and artifact evidence. These gaps prevent preparing an applicability experiment under this task's gate. No dependency source request, compilation, training, benchmark, alternate renderer or new accuracy claim follows from this note.
