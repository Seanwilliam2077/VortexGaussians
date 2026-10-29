# T24 independent release-contract review

29 October 2026. Reviewer: `volume_screen`. **CLEAR for the stated bounded conclusion:** actual storage/caller evidence advanced, but neither the complete volume operator nor an existing usable official trained carrier is qualified. Do not prepare an applicability-measurement protocol from this audit alone.

This review used only already acquired local metadata and the six authorized code files, plus the expressly authorized inherited T23 paper receipt at extractor lines 185–193. It made no external request, source reacquisition, installation, external-code import, numerical/model evaluation or asset access. Byte/hash/line-count checks are local provenance checks, not execution of the inspected code. Only this new review file was written.

## Provenance and budget

The saved revision resolves to `dd175d52938264770a783cbb7929e20572675544` and tree `3be1153bb1825daedbb0864d51eff9c909c5c981`; the recursive tree reports `truncated=false`. All 20 inventory entries independently match current byte lengths and SHA256 hashes. For all six code files, recomputing Git blob SHA1 from the exact local bytes also matches the pinned tree entry and advertised size. Their line counts match the inventory.

The recorded requests are four repository-metadata calls followed by six pinned code-file calls, all through the installed connector. None exceeds the 128 KiB per-file limit. The six files total 77,924 bytes and 1,705 unique lines; all returned content including revision/tree/README/license totals 106,724 bytes, below 1 MiB. Connector response representations total 227,718 bytes and are counted separately. These are local representation sizes, not measured network traffic. No origin HTTP status was exposed; returned content plus pinned identity checks establish the recorded success, not an assumed HTTP 200.

The first revision request succeeded, so the protocol's failure-stop branch was not triggered. There was no submodule expansion, repeated source acquisition, clone/archive, added paper family or asset-metadata request. The unused two-page asset allowance is an upper limit, not a requirement to treat observation datasets as pretrained models. The recorded Windows command-length failure occurred in local receipt transport; the ledger does not present it as an extra source or scientific invocation.

## Source claims checked

The code ranges below are subsets of the already acquired 1,705-line population; this review does not claim an exhaustive audit of the repository or unacquired dependencies.

- **Density versus raw storage:** `scene/gaussian_model_volr.py:27–136,252–342` and `utils/general_utils.py:18–64` support the reported separate ordinary-opacity and volume-density routes. Both volume getters call the same activation/conversion. The constructor selects `ours`; changing the mode alone does not rebuild activation functions. PLY stores raw opacity variables, log-scales, quaternion and SH arrays, without a mode tag. Capture also omits `reparam_type` and maximum SH degree. Loading/restore therefore needs external configuration; these are not self-describing density tensors.
- **Scale and covariance:** model lines 27–37/135–136 and utilities 122–168 support exponential scales, scalar-first quaternion normalization, covariance construction and packed order. No loader validity guarantee follows from these formulas. In particular, the builder has no zero-quaternion normalization guard.
- **Normalization and reverse helpers:** the `ours` forward getter divides by 2.506. The retained T23 receipt's equation 20 does not contain that factor; this is a local check of an inherited source, not a new paper access. For fixed scale mean m, the algebraic inverse would be `(1-exp(-2.506*density/m))/0.99`; the inspected reverse helper instead subtracts an exponential already divided by 0.99 and then clamps. The `ever` reverse likewise uses maximum scale where the forward uses minimum and omits the inverse 0.99 factor. Model lines 438–489 use these helpers in densification. These are static formula differences, not demonstrated runtime/image bugs or grounds to reject a saved tensor's forward decoding. The uninspected kernel may determine the coefficient convention; it cannot make the reverse helpers general algebraic inverses, but their intended operational role is not established by this audit.
- **Actual backend:** `train_volr.py:310–356` and the full acquired 100-line root renderer confirm that `slang_volr` imports `slang_gaussian_rasterization.api.inria_3dgs_volr`, whereas the root renderer is the classic `inria_cuda` alternative. The latter's sigmoid opacity and optional lower-clamped SH path cannot be attributed to the former. The tree supplies only the `submodules/slang-gaussian-rasterization` gitlink at `5eca1185550c35e3236c511c311aee3eb9129169`. No submodule implementation or `.gitmodules` remote mapping was read.
- **Run state and output:** training lines 29–98,170–190,215–280 set the mode and call setup after construction/restore, choose background, and distinguish raw training loss input from clamped display/evaluation images. The cfg writer receives the dataset argument; without the uninspected argument definitions and rendering loader, this does not establish a particular artifact's complete decoding flags. Image clamps do not prove raw component colors are bounded or define the T22 continuous target.
- **Camera and input carrier:** `scene/cameras.py:18–56,79–125` and `scene/dataset_readers.py:52–183,186–269` support the stated transforms, projection bounds, observation conversions, split and initialization-PLY behavior. Projection near/far values do not establish optical integration limits or normalized world-space rays. Point-cloud RGB/positions and training observations are not a trained density/covariance/SH carrier.

## Asset, operator and permission limits

The inspected README links training datasets and commands producing local output models, then renders a supplied output path. It does not identify a downloadable pretrained Vol3DGS density checkpoint with the needed mode, camera/context, size and permission information. This is a bounded statement about the inspected material, not proof that no compatible checkpoint exists elsewhere. Zero asset-page requests cannot validate any uninspected page's contents, and no such validation is claimed.

The root MIT license and retained Inria file-header notices are accurately recorded as distinct source notices. Neither was converted into a blanket statement about asset, submodule or dataset permission.

The unresolved volume dependency still controls how the decoded coefficient maps to extinction/transmittance, ray units, SH/color evaluation, culling, termination and accumulated output. Caller names, field getters, camera bounds or classic-renderer behavior do not complete that contract. There is therefore no qualified continuous-overlap executable reference or complete-support policy from this source slice.

## Review outcome

No blocking discrepancy was found in `DENSITY_STORAGE.md`, `CAMERA_ASSET.md` or `RENDER_PATH.md`. Their positive statements are tied to actual acquired code; their gaps remain qualified. The first-access failure in T23 remains historical, while T24's disclosed connector recovery supplies new static evidence. Neither source recovery nor local hash checks change T22's one-case, modest-batch result, establish novelty, or justify an automatic numerical/asset task. Closing this finite audit with no future measurement protocol is consistent with its gate.

## Final reviewed document identities

Paths are relative to `tracks/tog/tasks/t24-official-release-contract/`. The authenticated source inventory contains the six source and receipt hashes checked above.

| File | SHA256 |
| --- | --- |
| `PROTOCOL.md` | `700e98d5ea9e940d959c8da11063c16e492879bc10c35a7f4e09bd7801f83ddb` |
| `freeze.json` | `7adbdbbe35f1be9ba7a8f6cad0dc299f9a6354f047611c2c95ce0310223eaeaf` |
| `acquisition-requests.json` | `cd55768bd8a231a4b7bce4aec57f83039efb1679e99e5606fab87404467130b8` |
| `source-inventory.json` | `bba3f53b59fba410b918c4d2574ecea9e418e1b85451ecc1da00d7523fb921b8` |
| `DENSITY_STORAGE.md` | `262c770f230176b9d92f37aefa171b228911ea4d6c5d5b74abc14e61099bc127` |
| `CAMERA_ASSET.md` | `b7deafc6a0991d233694f2d60a8756d6dc13698a16328fca124a8555b2981a81` |
| `RENDER_PATH.md` | `96245310f757fb5d055abffc86b5971b82b8d5832f329ce4766818edf72f03c8` |

The inherited T23 receipt `acquired/vol3dgs-paper/01-html.web.txt` has its previously authenticated SHA256 `dfa8fd62e37baefadc41937f3be60c055c212892e0fa30db858ba7eb025a406d`; only its already retained equation-20 passage was revisited here.
