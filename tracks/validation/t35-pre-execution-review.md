# T35 independent pre-execution review

30 October 2026. **No unresolved static blocker was found in the reviewed version.** It is ready for the specified freeze and single bounded invocation. This review neither qualifies a pixel nor predicts completion within time/cell limits.

## Scope and identities

Read all four new files in `tracks/tog/tasks/t35-first-complete-frame` (46,216 bytes / 698 lines), reread T34 NEXT_ENTRY, and reused the already reviewed ordinary/reference/worker contracts. Verified that T34 reference/run and T32 ordinary still match their reviewed hashes. Standard-library AST parsing checked syntax only. No numerical or evidence module was imported/executed, no pixel or display was evaluated, and no pilot occurred. Only this review was written for the formal review; the separately requested local saved-data auditor is not part of the scientific invocation.

| File | SHA256 |
|---|---|
| PROTOCOL.md | `5e3d93d64778a67397f0d64410e98ba70cd33cc9cc438547d1246a66c67af786` |
| evidence.py | `1bbcc1848bb13892b47fc96df40b86cd4fe9b14df4f19e60c4e0a04d3e452829` |
| run.py | `e77310c1f60a52569acfe4038c88762bac74f22a52069c6b1b4d0d3fc1fab28a` |
| supervise.py | `24621589dfd4ba3688887c099d7295809f0d1220bf21cafa15339a609ee38cd3` |

These files, this review, immutable numerical sources/input and governing documents must be frozen before launch.

## Scientific and workload contract

The worker selects stored frame 90 / front and all 256x192 pixels in fixed row-major order. There is no radiance-based sampling, crop, new field, candidate or numerical-method modification. It imports the unchanged T32 adapter/ordinary, T22 GL kernel and T34 reference. Ordinary RGB is computed before independent reference work and remains fixed. The original geometry/projection, complete/disjoint selection, omission, leaf domain/range/absorption/reconstruction, endpoint, alpha and RGB-range gates are retained. Full-frame coverage requires all 49,152 committed records plus nontrivial and mixed content; the partial prefix cannot satisfy that condition.

The 600-second computation / 630-second worker wait plus 10-second termination is the declared budget of this different full-pixel task. It does not revise T32/T33/T34. Reference caps remain 8,192 created cells per ray and 200,000 globally, with first-failure stopping. No runtime or visual-complexity guarantee follows from T34's subset pass.

## Binary evidence and publication

The independently inspected schema is little-endian `<31d10I`, 288 bytes per pixel, with `<9d`, 72-byte leaf records. Full pixel allocation is 14,155,776 bytes; at most 200,000 accepted leaves add 14,400,000 bytes, leaving 4,998,656 bytes below 32 MiB for numeric metadata/failure state. The worker and supervisor also check the actual combined raw binary, frame, failure and result extents. Overflow remains a failure with evidence preserved, not permission to omit cases.

Each successful write appends its leaves, writes a status-zero pixel payload, then commits the four-byte qualified status last. Its index must be the next row-major index. The worker clears `active` immediately after successful commit, so a subsequent deadline/coverage/source error cannot overwrite the last accepted pixel as failed. Uncomputed and failed statuses remain distinct. The packager checks contiguous accepted leaf offsets/counts against the complete leaf extent, preserves unreferenced/partial tail bytes, and does not assign them to accepted pixels.

Accepted records retain all leaf ledgers, enabling an independent saved-data audit of domain, adjacency, ownership, absorption, cell ranges and endpoint reconstruction. Stored RGB/alpha/endpoints and omission/error aggregates support their algebraic gates. Per-source projections, source-ID partitions, finite masses and mixed-color operands are not duplicated. Their normalized residuals/aggregate/flags can be checked, but a later audit must not claim independently to reconstruct those underlying operations. This limitation is explicit in the protocol.

The packager's `all_pixel_records_qualified` is only a data-completion summary. The worker separately requires coverage, numerical success and final source checks; the supervisor separately requires a successful exit, normal termination and source integrity. Thus full-looking arrays alone cannot establish full-frame qualification.

## Failure, accounting and displays

Initial/final source-check results are explicit. A returned reference is attached to active failure state before the next deadline/qualification check; thrown reference diagnostics retain their existing partial-state semantics. Stage times include progress writes, stream writing has its own stage, and final packaging is separate from computation. A checksummed overwritten progress record supports bounded diagnosis after an external kill; terminal receipts preserve process and cleanup status. Hard-timeout handling does not import methods or start packaging recovery beyond the worker wait. Raw files remain available.

Inherited diagnostic limits remain: deadline/unwrapped errors may lack local reference leaves, and an external interruption may leave an incomplete progress or uncommitted record. These are failure/partial evidence, never completed black pixels. Deterministic packaging preserves byte-identical outputs and rejects conflicting existing publications.

Display mappings are fixed before execution: exposure-one `L/(1+L)` with sRGB transfer, linear alpha and retained-count/270, all at the original resolution. Invalid pixels are magenta and the validity image distinguishes them. Linear HDR values remain available. These mappings are display aids, not physical truth or tuned visual evidence.

## Limits

A completed result would concern one authored image with the existing finite-workload binary64 contract. It would not establish directed-rounding guarantees, the other views/states, independent scenes, a useful creative task, an optimized paper baseline or a TOG contribution. Complete ordinary cost must remain separate from reference-verification time; no FPS, speedup or sample-time extrapolation is justified. No pilot, retry, automatic cap increase or next experiment is authorized by this review.
