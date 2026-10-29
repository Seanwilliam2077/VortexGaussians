# T25 independent kernel and loader review

29 October 2026. Reviewer: `volume_screen`. **CLEAR: the static evidence supports a guarded, whole-primitive volume-rendering approximation and concrete loader requirements. It does not qualify a complete production adapter, an accurate continuous-overlap reference, or a trained carrier. No applicability-measurement protocol is justified by this audit alone.**

Review was limited to the frozen protocol, ledgers, three technical notes and already acquired main/dependency source, with relevant inherited T24 facts. No external request, import, compilation, configuration evaluation, PLY loading, numerical/model invocation, sample generation, asset access or old-file mutation occurred. Provenance hashing/counting and the exact state-transition reasoning below do not execute scientific code. Only this new review was written.

## Identities, scope and budget

The acquired main `.gitmodules` resolves the actual remote to `chinmay0301ucsd/slang-gaussian-rasterization`. Its exact dependency commit is `5eca1185550c35e3236c511c311aee3eb9129169`, with complete returned tree `8134d53da3ff7be143355fa0a92954061878f58e`; the main pin remains `dd175d52938264770a783cbb7929e20572675544`. This follows the observed gitlink rather than substituting an upstream or HEAD.

Independent checks verified all 28 content/wrapper files against the acquisition ledger's sizes and SHA256 hashes. For acquired blob resources, recomputed Git blob SHA1 and advertised sizes agree with their pinned main/dependency trees. All nine code-file line counts agree with the inventory. Actual totals are five metadata requests, nine code requests (three main plus six dependency), 91,131 code bytes, 2,123 unique acquired/inspected code lines, 119,769 returned content bytes and 259,077 wrapper-representation bytes. These remain below the 4,500-line, 256 KiB per-file and 2 MiB content limits. Representation bytes are not network measurements. No origin HTTP status was exposed; success is supported by returned content and identities.

The ledger's Windows path-length storage recovery reused the same saved responses. It records no repeated external source request, scientific retry or additional source. Metadata/code allowances are exhausted; unused line/byte capacity does not authorize another file. No asset, new paper or numerical acquisition was recorded.

## Mathematical and implementation checks

**Primitive evaluator:** dependency `utils.slang:574–617` matches the note's `qbar=max(1e-7,d^TQd)`, numerator gate, regularized width, exponential peak, `2.506*kappa*sigma*p` optical mass and .99 alpha cap. Ordinary opacity is loaded but does not enter this expression. The conditional unguarded unit-ray/full-line Gaussian interpretation is correct, while the actual guards and extra epsilon prevent asserting exact equality. A positive peak parameter does not remove the negative-parameter Gaussian tail; rejecting a nonpositive peak does not integrate the remaining forward tail. This is neither finite-interval CDF integration nor a half-line integral.

Substitution of T24's `ours` getter cancels its division by 2.506 against this evaluator's factor in real arithmetic. The notes correctly treat this as the released latent-to-optical-depth convention, not proof of exact equality with the paper coefficient or the T21/T22 continuous reference. No static asymmetry is promoted to a measured image failure.

**Geometry and colors:** covariance/inverse-covariance builders (`utils:658–713`) require the supplied normalized quaternion and valid scales. Transforming both through the same camera rotation (`utils:264–269`) requires an orthonormal rotation for inverse consistency. The blend caller normalizes its pixel-center direction (`alphablend_volr_shader.slang:59–65`), resolving the physical-length factor only under that camera assumption. Vertex selection, projected support and finite tiles remain separate approximations. A single stored RGB per primitive/view is confirmed (`vertex_shader.slang:79,136–138`); the blend does not reevaluate color along the ray. This establishes constancy of the stored value, not the uninspected SH basis, direction convention, activation implementation, range or color space.

**Blend and exit:** `alphablend_volr_shader.slang:25–30,74–115,225–274` implements premultiplied front-to-back updates, skips alpha below 1/255, and tests candidate transmittance below 1e-4 **before assigning the candidate state**. Thus the crossing primitive and subsequent primitives are omitted. The exact algebraic illustration is valid: entering T=1/200 and alpha=99/100 gives candidate T=1/20000 and omits current color contribution 99/20000*c. For a unit channel that is .00495, not an error bounded by 1e-4. This is a statement about the branch for a specified state, not a constructed ray, runtime observation, frequency estimate or new benchmark. A residual bound needs the old T and an explicit color bound. Many skipped small alphas cannot be charged as one cutoff-sized error.

**API and cost:** the volume API's assertions require black background and prohibit the listed override/Python paths. The wrapper returns RGB only; no background is later added. The fourth shader component is residual transmittance. All-ones scale factors, vertex preparation, tile prefix sums, key generation, sorting, range construction, allocation, blend and diagnostic scans appear in the acquired callers. Their execution latency was not measured. Early pixel inactivity does not remove the enclosing shared-memory rounds. The actual key generator/sort implementation, SH body, RenderGrid and Slang registration remain uninspected; symbol names alone do not prove a compiled dispatch or its ordering/ties. The notes preserve these limitations.

## Loader and carrier checks

All three acquired main files were cross-checked. `render.py` defaults to `slang`; explicit `slang_volr` selects the volume API/model and forces the softplus flag. `get_combined_args` merges cfg values with every non-None parsed CLI default, then grouped extraction filters fields. No acquired rendering route restores `reparam_type` or reruns setup after construction. Combined with the preserved T24 model definition, it retains `ours`; this need not decode a nondefault-mode artifact correctly, but no such artifact or failure was observed. The model-field sentinel treatment does not make the backend default or pipeline defaults sentinel values.

Scene still obtains cameras/images from the original source dataset and loads the selected PLY; its output `cameras.json` is not the input camera route here. The final loader note correctly limits iteration handling to truthy values and states that requested zero follows initialization. Caller white background conflicts with the selected API's black-background assertion. These facts make a PLY alone insufficient portable state. No usable existing trained carrier, its actual cfg/mode, finite tensors, complete support or asset rights were acquired. The dependency README contains implementation/install context, not a trained-carrier specification.

## Conclusion and limits

The three notes accurately distinguish the conditional ideal integral, guarded primitive evaluation, culled ordered renderer and caller configuration. T21's bound can address a defined ideal ordered output for the same components and any specified permutation; it cannot automatically bound this shader after domain changes, regularization, alpha clamp, support omissions and early exit. Nor does static compatibility qualify the earlier ordinary GL solver on an unseen scene.

The remaining uninspected bodies and trained-carrier context are substantive gaps. Closing this finite audit without an automatic measurement, scene, optimization or source extension is consistent with the protocol. The broad research objective remains open. T22's isolated local benefit and modest batch result, all historical gates and the absence of a demonstrated TOG contribution remain unchanged.

## Final reviewed document hashes

Paths are relative to `tracks/tog/tasks/t25-volume-kernel-contract/`. The inventory and request ledger authenticate the locally checked source/response bytes and inspected ranges.

| File | SHA256 |
| --- | --- |
| `PROTOCOL.md` | `0f65afe8bb91859ef3e37c0d925ef01b27664dd1327dbe5f80bb093f14ac2d5b` |
| `freeze.json` | `17b0fa46982030745d960c8e62c0c29877bae627498bf8739a67ff7097e5e9be` |
| `acquisition-requests.json` | `a3e53fdc54d8c123a1c30c0a1b749db766358106074756b9754685b2683d698c` |
| `source-inventory.json` | `e72d6e3c582845c27815be15dba9aa524d667032b4d7bb2a02547325a86ee48e` |
| `BLEND_CONTRACT.md` | `ade802cea2e479bc362c4722906053523415b7ff321358e69f32a970d2913785` |
| `LOADER_CONFIG.md` | `111b7e2518150ace7afd619aa398d61d5cb9d785edb390e908d4fa64fb4f7409` |
| `KERNEL_MODEL.md` | `44a57b9af93deccfcbf3e3889fffefca0f0573c455125ea53afbc6850ce693ac` |
