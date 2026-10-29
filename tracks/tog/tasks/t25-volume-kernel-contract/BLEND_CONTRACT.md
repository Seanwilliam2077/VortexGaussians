# T25 — forward blend, approximation boundary and complete cost

The actual remote is chinmay0301ucsd/slang-gaussian-rasterization, resolved from the fixed main .gitmodules, not assumed from an upstream name. Dependency commit5eca1185550c35e3236c511c311aee3eb9129169 and tree8134d53da3ff7be143355fa0a92954061878f58e are fixed. All dependency line references below use that commit. This is a static audit, without shader loading, compilation, numerical execution or measured image failures.

## Observed call chain and output contract

[Volume API](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/api/inria_3dgs_volr.py#L22) lines22–44 obtains activated geometry, ordinary opacity, volume density and SH from the model and transposes the camera transforms back. Lines47–66 require unit scaling modifier, no color override, no Python SH/covariance/debug path, and **black background**. It passes the softplus flag and tile_size16 into the volume wrapper. A white-background main dataset configuration is therefore an incompatible combination in this path; no execution was attempted.

[Volume wrapper](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/alphablend_volr_tiled_slang.py#L24) lines24–48 uses an all-ones scale3d_factor and passes volume density to vertex/tile preparation. Lines58–81 pass the prepared camera-space means, inverse covariance, both opacity fields and per-primitive RGB to the blend; output is the first three channels, permuted to CHW. Lines85–156 allocate float output/contributor buffers, compute focal lengths from FOV, select alpha_blend_volr_shaders and launch splat_volr_tiled. The fourth shader channel is residual transmittance, not opacity. No background term is subsequently added.

[Tile wrapper](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/tile_shader_slang.py#L20) lines20–125 calls the vertex stage, builds a prefix sum of tiles_touched, allocates duplicated index/key buffers, invokes generate_keys, sort_by_keys and compute_tile_ranges. The inspected caller establishes these stages and their inputs, **not the key bit layout, ordering direction, tie behavior or precise depth metric**: tile_shader.slang and native sort bodies were not acquired. In particular, do not substitute per-ray Gaussian peak depth for the unresolved actual key. The Slang module registration and RenderGrid bodies are also outside the six-file dependency budget; matching kernel symbol names and calls are source evidence, not a successfully compiled dispatch.

## Blend semantics and distinct error sources

[Blend shader](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/alphablend_volr_shader.slang#L24) lines24–29 implement C_new=C_old+T_old*(alpha*c) and T_new=T_old*(1-alpha). Lines59–64 use camera-space pixel centers x+.5,y+.5 and normalize the ray. This resolves the nonunit-ray factor for this inspected forward kernel, assuming a rigid world-to-camera transform; it does not establish physical world units.

Lines74–107 consume the supplied ordered tile list, evaluate one entire primitive at a time and implement:

1. alpha<1/255 skips the primitive completely, including its extinction.
2. A candidate new transmittance<1e-4 ends that pixel **before assigning the candidate state**. The threshold-crossing primitive is omitted as well as all subsequent primitives.
3. Only otherwise is the new state retained. Shared-memory rounds continue structurally, although the pixel's inner blend becomes inactive.

The evaluation helper separately rejects nonpositive projected peak numerator, regularizes denominators, uses a full-line-style mass and caps alpha at.99; vertex selection separately culls center depth and projected tile support. See [kernel analysis](KERNEL_MODEL.md). These are different operations from sorted compositing of all original finite-domain optical masses. T21's error enclosure applies to that defined ideal sorted output; it cannot simply be attached to this shader's image.

A threshold label is not an RGB certificate. As algebraic illustration only, an entering T=1/200 and alpha=99/100 gives candidate T=1/20000<1e-4, so this branch omits the current contribution99/20000*c. That is.00495 for a unit channel, already larger than1e-4. This is an exact state-transition example, not a new sampled ray, rendered scene, measured failure or claim that such states are prevalent. Under an additional uniform channel bound Cmax, the discarded residual can be bounded using the **old** T; without such a bound on raw SH-derived colors, the opacity threshold alone gives no absolute RGB guarantee. Likewise, arbitrarily many alpha<1/255 omissions cannot be charged as one1/255 error.

## Scope of the mathematical comparison

For a chosen finite list, specified ray/domain, SPD covariance and finite constant-per-ray colors, T23's peak-density reduction gives the exact 1D continuous-overlap target. For a chosen permutation of those SAME components, T21 can bound the ideal whole-component ordered result. The proof need not assume the permutation is sorted by projected mean, but the actual comparator's permutation must be reproduced if comparing its output. Independently account for domain/full-line substitution, regularization, selection, clamp, skipped attenuation, early exit and floating-point arithmetic. Display clamping cannot retroactively validate a raw radiance tolerance.

The release supplies an approximate renderer of a related Gaussian extinction/emission model; **it is not an accurate ordinary overlapping-emission integrator**. Existing GL qualification remains limited to the48 frozen development rays. Neither source similarity nor a matching coefficient map qualifies it on an acquired trained scene.

## Full cost boundary for any later comparison

The source-level delivery includes model decode/camera and SH setup, vertex geometry/color, covariance and tile support, prefix sums, key/index duplication, sorting and range building, buffer allocations, blend evaluation, skipped/failed work and GPU launch/readback/synchronization. The inspected wrapper additionally performs isNaN/isInf scans and Python conditional checks on CUDA tensors (lines138–148); vertex preparation performs NaN checks too. Their actual latency is unmeasured, and a mathematical work count must not be presented as wall time. Shared-memory fetches need not disappear when a particular pixel exits. Training backward, loss and optimizer work are separate from a forward-only delivery and must be included if the eventual task is training rather than rendering.

No timing, bottleneck, effect size, new algorithm or TOG contribution follows from this audit. A complete adapter still needs the omitted key/SH/module bodies, verified context for a trained carrier, a chosen exact target/domain and ordinary-reference qualification on that target. No measurement protocol is prepared here.

## Inspection

Root inspected complete acquired API88 lines, volume wrapper205, tile wrapper258 and blend shader407:958 unique lines. The two kernel files are independently analyzed by the density reviewer; the three main files by the loader reviewer. Source hashes and acquisition versus inspection ranges are in source-inventory.json. Dependency README19 lines identifies this as the Vol3DGS rasterizer and links its upstream; no trained carrier is listed in that text. LICENSE is acquired in full202 lines; identification/notice ranges1–15 and175–202 were inspected. It declares Apache2.0 for this dependency, distinct from the main repository's separate notices; this is source attribution, not an asset-rights conclusion.
