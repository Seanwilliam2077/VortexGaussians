# T25 — pinned rendering loader and configuration contract

29 October 2026. Static local inspection at main-repository commit **`dd175d52938264770a783cbb7929e20572675544`**. This reviewer inspected only the three newly acquired main files below and the prior T24 density/render notes. No network request, import, configuration evaluation, PLY load or rendering was executed. The dependency implementation is root's separate audit.

## Selected backend and pipeline flags

[render.py L62–91](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/render.py#L62-L91) registers `--render_backend` with default `slang`. Explicit `slang_volr` selects `slang_gaussian_rasterization.api.inria_3dgs_volr` and replaces the global model class with `GaussianModelVolr` (L82–84). After pipeline extraction it forcibly sets `softplus_rgb=True` (L87–90). This verifies the flag supplied to the volume API, not the API's actual activation formula. Each view reaches that selected renderer through L34–36.

`PipelineParams` defines `softplus_rgb=False` among its ordinary defaults ([arguments/__init__.py L64–70](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/arguments/__init__.py#L64-L70)); the volume branch overrides it. A filename containing `volr`, or a saved configuration field alone, does not select the volume branch.

## Configuration merge is not restoration of every model setting

The loader reads `<model_path>/cfg_args`, evaluates its Namespace representation, copies that namespace, and overwrites keys with every non-None parsed command-line value ([arguments L108–128](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/arguments/__init__.py#L108-L128)). Rendering constructs ModelParams with `sentinel=True`; its parser defaults become None via L20–38, allowing saved model fields to survive absent explicit overrides. Pipeline defaults and the separate backend default are not sentinel values. In particular, the default `slang` value overrides a cfg `render_backend` value unless the caller explicitly selects another backend.

`ParamGroup.extract` subsequently retains only fields declared in that group (L40–45). `ModelParams` declares SH degree, source/model paths, image directory, resolution, white-background flag, device and evaluation flag, then absolutizes the source path (L47–62). Neither `render_backend` nor `reparam_type` belongs to this extracted dataset. Merging an extra cfg key therefore does not demonstrate that the model consumes it.

The cfg reader catches TypeError only (L113–121); a missing file at an otherwise valid path is not covered by that handler. This is a static branch observation, not an observed execution failure. No cfg file was acquired or evaluated here.

## Density mode and PLY reconstruction

[render.py L48–51](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/render.py#L48-L51) constructs the selected model with `dataset.sh_degree` only, then constructs Scene with a requested load iteration. None of the three inspected files sets `reparam_type`, calls `setup_functions` after construction, or invokes the captured-checkpoint `restore` route.

The inherited [T24 density audit](../t24-official-release-contract/DENSITY_STORAGE.md) established the constructor's `ours` mode/setup, mode-dependent decoding, and that PLY omits the mode tag. Combining those source facts with this caller shows that the inspected rendering route retains constructor-default `ours`; a cfg field does not restore `ever` or string `None`. T24 separately recorded that the training caller explicitly sets its mode and reruns setup. These are different caller paths.

Scene resolves `-1` to the latest available iteration, or retains a truthy requested iteration ([scene/__init__.py L35–40](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/scene/__init__.py#L35-L40)). A requested iteration of zero is falsy in this branch and follows initialization. Its load branch calls `load_ply` on `point_cloud/iteration_<iteration>/point_cloud.ply`; otherwise it creates a model from the initial point cloud (L78–84). The mode ambiguity matters because the same stored latent value can decode differently across modes. This does **not** prove a released model was trained in a nondefault mode or that any rendered image is wrong. An `ours`-trained carrier may agree with this path; its provenance must establish that fact.

## Cameras and black/white background

Even when loading trained parameters, Scene first recognizes the original `source_path` as COLMAP or Blender data, reads its scene information, and constructs train/test cameras ([Scene L45–76](https://github.com/chinmay0301ucsd/Vol3DGS/blob/dd175d52938264770a783cbb7929e20572675544/scene/__init__.py#L45-L76)). It does not read the output directory's `cameras.json` here. That file is written only on the initialization branch (L53–65). Rendering passes `shuffle=False` and later obtains these camera lists through Scene's getters (render L51/L56–60; Scene L90–94). The uninspected camera utility's detailed conversion remains outside this three-file inspection.

The same extracted `white_background` flag is passed to Blender observation loading (Scene L47–49) and chooses the render background tensor `[1,1,1]` or `[0,0,0]` (render L53–54). This resolves the caller's deterministic background choice; it does not establish the actual value in an unavailable artifact's cfg. The raw rendered tensor is passed to image saving and compared with `view.original_image` (render L36–42); this excerpt does not prove component-color bounds, linear-light semantics or a continuous-overlap reference.

## Carrier consequence

A PLY path is not a complete portable rendering state. This entry point additionally requires compatible SH degree and density-mode provenance, an appropriate cfg/source dataset with cameras and images, and the intended backend/background. The camera/domain and asset-use requirements from T24 also remain. Static loader inspection can specify these requirements but cannot supply an existing trained carrier, prove validity of its tensors, or qualify the continuous target. No applicability experiment is prepared by this note.

## Inspected identities

The full local contents of all three files were inspected; total **313 unique new code lines**. The source links above remain pinned to the same main commit.

| File | Inspected lines | SHA256 |
|---|---|---|
| `render.py` | 1–91 | `6b3875253ce47ea1fb54437d7fb5ff303a53d2eec4823afbdfbfbc26a57a7ef5` |
| `arguments/__init__.py` | 1–128 | `2fd2a1c4c1cc41c13aba25689b955623953a2e1beaaf3b5b6192021c99138ee2` |
| `scene/__init__.py` | 1–94 | `2fca8688427e25c63b246aeb6cdb013ece690724639a0aedac5317c942a8eed7` |
