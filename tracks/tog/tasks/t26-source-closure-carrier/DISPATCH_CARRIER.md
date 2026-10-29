# T26 — dispatch, full setup cost and official carrier route

29 October 2026. Static source inspection and public metadata only. No imports, compiler/JIT, CUDA launch, numerical model, training or asset download occurred.

## Named binding is now resolved at source level

At dependency5eca1185550c35e3236c511c311aee3eb9129169, [slang_modules.py lines18–32](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/slang_modules.py#L18) passes the adjacent vertex_shader.slang and tile_shader.slang files to slangtorch.loadModule, and registers classic and volume blend files separately for4x4,8x8,16x16. The volume dictionary points to alphablend_volr_shader.slang with matching PYTHON_TILE_HEIGHT/WIDTH defines. This closes the T25 symbol-to-file gap for the default16x16 volume call. It does not prove the external compiler can build or execute this combination in the present environment.

[RenderGrid lines17–24](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/render_grid.py#L17) uses ceil(image_height/tile_height) and ceil(image_width/tile_width), retaining original dimensions; T25's shader bounds checks handle partial edge tiles. This class performs no validation of zero/invalid dimensions.

[sort_by_keys/__init__.py lines1–7](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/sort_by_keys/__init__.py#L1) uses torch.utils.cpp_extension.load on the adjacent sort_by_keys.cu. Consequently, merely importing these source modules can invoke compilation/loading; this audit only reads text. No external compiler/library semantics or installed versions were inferred.

## Complete cost implication

Module setup can include two shader module loads plus three classic and three volume specializations, and native-sort extension compilation/loading. The source requests these loads; cache hits, actual compilation count and elapsed time depend on slangtorch/PyTorch/toolchain state, which were not exercised. Later costs must distinguish first usable delivery from amortized repeated delivery and declare what cache state is shared.

The acquired [native sort lines15–50](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/sort_by_keys/sort_by_keys.cu#L15) checks shape/type/CUDA placement, allocates two output tensors and obtains contiguous views/copies. It queries CUB temporary-storage size, cudaMalloc's that storage, invokes the radix sort over selected bits, then cudaFree's it on each call. This is additional to T25's geometry/SH, tile duplication, prefix sums, key/range buffers, blend and diagnostics. No cost estimate, timing result, safe asynchronous behavior or memory bound follows from counting these statements.

The [color/order note](COLOR_ORDER.md) now resolves the key layout and source-level sorting call. The precise equal-key ordering and external library/runtime behavior were not validated. An independent renderer can specify a deterministic permutation for a mathematical target, but cannot claim byte-identical official ordering on tied keys without further evidence.

## Official trained-carrier check — this route closes

The live public releases endpoint was read once for each official repository, page1 with per_page30. Both returned the JSON array [] with no tool error. These are observations of those public listing responses at this audit time, not a global search or claim that draft/private/elsewhere artifacts do not exist.

The already linked [official project page](https://chinmay0301.github.io/vol3dgs/) returned75 extracted lines. Its visible links include paper/code and illustrations; the inspected response provides no trained-checkpoint download entry. No illustration, linked paper, license target or alternate project was opened. The website-license notice was not promoted to rights for an unavailable model or dataset. This project-page finding uses the returned text/link representation, not an exhaustive crawl.

Together with the previously inspected fixed README's training recipes, the two empty lists and project response do not identify an existing usable trained carrier. Three of five metadata calls were used; no same-document paging or linked carrier description was needed or justified. No source call failed, no retry occurred, and no binary/asset endpoint was opened. The request ledger preserves both2-byte release bodies and the project tool response separately from wrappers; the web response is not raw HTML or measured network bytes.

## Consequence for the next decision

The named source gaps from T25 are substantially closed: SH formula/direction, tile-center depth key, module binding, grid and camera helper bodies are explicit. Artifact-dependent finite inputs, original density mode/SH degree/camera state, color space and usable carrier remain unverified; runtime/compilation is also untested. The volume pipeline remains an approximate renderer, not an ordinary high-accuracy continuous-overlap reference.

Do not spend further turns repeating these same official asset lookups. The next useful decision is a separately budgeted feasibility assessment of obtaining or producing a researcher-trained workload: existing local hardware/toolchain, the fixed release's dependency contract, a provenance/permission/size-qualified observation source, explicit training cost and an abort rule. This is a proposed evidence decision, not a training or measurement protocol and not authorization to download/install/run here. Failure of that route would require revisiting workload strategy, not silently substituting a favorable toy or weak baseline.

Training images and reconstruction loss would not themselves prove the continuous-rendering task valuable or the ordering method novel. T22's single incremental local prefix win and overlapping-range batch costs remain the only measured evidence for that mechanism. Full-cost scene evidence and a distinct useful method are still required for the original submission goal.

## Inspection ownership

Root read all24 RenderGrid lines,32 module-loader lines and7 native-extension binding lines; the order reviewer read the native implementation and root cross-checked it. Two other reviewers cover335 color/key/native-sort lines and159 camera lines. Thus all557 new code lines across eight files are inspected once in the unique-line ledger, even when independently reread. Exact hashes and tree matches are recorded in source-inventory.json. Earlier T24/T25 source/notes were reused locally, not reacquired.
