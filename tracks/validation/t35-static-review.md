# T35 pre-execution static review

Recorded30 October2026 before freeze and invocation by root from independent pressure_screen reports and direct root inspection. No scientific module was imported and no numerical pilot was run. The implementation author was volume_screen; pressure_screen independently read the complete final worker369lines and supervisor132lines, plus the evidence/storage contract. transfer_screen separately reviewed the storage design and is preparing the later saved-data audit. This is static review, not experimental success.

The independent final review found no blocking issue. T34's numerical checks are preserved: source geometry/projection agreement, complete/disjoint ordinary partition, full-field omission charge, leaf domain/adjacency/absorption/range and interval reconstruction, RGB endpoint/alpha tolerance, necessary color/alpha range, and nontrivial/mixed coverage. The unchanged original first frame90/front uses all49,152 pixels in fixed row-major order. T32 adapter/ordinary, T22 GL and T34 reference are reused without modification. Root directly compared the gates to T34's worker.

Final code identities reviewed independently by pressure_screen:

- run.py:21,579bytes, SHA256 `e77310c1f60a52569acfe4038c88762bac74f22a52069c6b1b4d0d3fc1fab28a`.
- supervise.py:7,012bytes, SHA256 `24621589dfd4ba3688887c099d7295809f0d1220bf21cafa15339a609ee38cd3`.

Root requested and inspected two pre-freeze corrections: initial source status is an explicit variable; returned reference evidence is attached to active failure state before the next deadline check. The worker clears active only after committing a qualified pixel, so a subsequent deadline/coverage/source failure does not erase that accepted pixel. Existing reference exceptions retain their inherited diagnostics; an internal deadline may have less detailed state and is not rerun to improve it.

The compact288-byte pixel layout is14,155,776bytes for the complete frame. At most200,000 accepted leaf records of72bytes add14,400,000bytes, leaving4,998,656bytes under32MiB for failure and numeric metadata. The worker checks their combined total; the supervisor independently checks the raw extent. Complete leaves and pixel payload precede the final status commit. Uncomputed/failed display pixels are magenta, with a separate validity mask. Interrupted unreferenced leaf tails, including partial bytes, are preserved and reported; they never belong to an accepted pixel. Display mappings are fixed before execution.

Pressure_screen identified two pre-freeze evidence fixes that root applied: the packaging summary is named `all_pixel_records_qualified`, avoiding a stand-alone final qualification claim, and partial leaf tail bytes can survive packaging. Final worker success additionally requires coverage, source checks, matching committed counts and capacity; supervisor success additionally requires exit0, no timeout/errors/live child and matching worker status. The630-second wait and10-second termination allowance do not run a packaging recovery or second experiment. Failed raw evidence is preserved. A supervisor hard timeout may leave packaging incomplete.

Per-pixel stored ratios/omission aggregate/partition flag can support consistency checks but do not independently regenerate omitted per-source projection arrays or ID partitions. Saved-data review must state that limit. Full accepted leaf ledgers permit independent interval reconstruction. No binary64 computation here is a formal directed-rounding certificate. Scalar Python timing is not a strong-renderer benchmark, and full-frame success would still cover only one authored scene/frame.

Decision: ready for the sole frozen full-frame feasibility invocation under PROTOCOL.md, subject to freeze identity verification. No new method, wider workload, relaxed gate, additional attempt or TOG contribution is approved by this review.
