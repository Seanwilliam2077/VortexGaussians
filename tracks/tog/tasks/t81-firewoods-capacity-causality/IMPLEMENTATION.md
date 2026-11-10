# T81 executable contract

Prepared 10 November 2026 after explicit technical resumption. Art stays paused. These new files implement the original frozen brief; no browser or scientific execution occurred during preparation.

`stage.mjs` verifies the original demo SHA256, inserts the unchanged tracked T42 camera adapter plus T81 observation API, replaces only the admission predicate and adds two emission/outcome observation hooks. It reverses all changes byte-for-byte and parses the full inline script without execution. No main-branch revision is merged.

`adapter.js` keeps particle IDs and emission-source labels in a WeakMap; no native particle object is modified by observation. Source labels identify the emitter, not ancestry of propagated combustion. Per-step offers include source index, target layer, local/global occupancy, both fullness decisions, outcome and fixed/new-B membership. Natural attrition is the loss of previously observed particle identities, checked against the particle balance. All original conditional RNG consumption and arithmetic in the native step remain. Global full is pre-emission total >=5400; the per-layer expression is unchanged in that policy. Unused global capacity is measured at the offer, not inferred only from endpoints.

Every frame uses the native research step order and one render followed by `gl.finish`. All four 180-frame prefixes must agree in full exported recorded state and timing-free per-step traces. Historical prefix and original block AB endpoint must match T42 hashes/counts. Mismatch terminates the single attempt without a causal conclusion. Native hashes are selected-field hashes, not complete-state certificates.

The full pre-B and endpoint image/state captures occur synchronously after rendering, before the default framebuffer can be cleared. Complete recorded gas objects, observation labels, material snapshots and original auxiliary values are retained locally. They are detailed observations, not an implemented restart interface. Source geometry and images remain under ignored `local/`. Each after-intervention material/gas state is also recorded. The PNG and RGBA exports share the same framebuffer; the RGBA record enables independent byte-level paired differences without another browser.

Pre-execution review correction: each boundary capture is saved before historical/prefix/GL qualification, and recorded checks contain actual observed/expected values. GL diagnostics are retained from both the frame and the state export after image/readback calls. On failure, completed rows already returned by the browser are flushed to a separately named partial log when the existing deadline and byte cap permit; no extra step is performed. The supervisor catches secondary process-tree cleanup failures so its failure receipt can still be written. The original candidate is retained by hash under ignored preparation history before explicit replacement.

`capture.mjs` uses one headless browser with four sequential pages: per-layer AB, per-layer A, global AB, global A. Each executes exactly360 native steps, with only the declared zero-time policy/B intervention at frame180. No warm-up/pilot. Runtime versions and all frozen used inputs are checked before and after; errors, deadlines, conservation of counts and output bounds stop the run. Output reserve is one MiB below the64MiB brief cap for final receipts. Setup, native step including observation hooks, render+GPU completion, observation, bridge, export, compression/IO, page/browser/server cleanup and whole-worker cost are distinguished. Hardware/frame timings include instrumentation and are not optimized FPS claims.

`run_once.py` creates a permanent tracked invocation guard before process launch, exclusively creates `local/run-01`, polls total output size and enforces a640-second termination trigger with cleanup/receipt headroom inside660seconds. Worker deadline is600seconds. A failure consumes the attempt. Do not delete the guard or automatically retry.

`prepare.py` performs only source hashing, syntax/AST checks, staging, executable version metadata and the24 historical T42 file identity checks. It refuses refreeze after invocation. The freeze hashes used source/data, staged HTML, Node/Edge executables and Playwright package/entry. This is not a claim to hash every runtime DLL.

`audit_saved.py` reads completed saved files, verifies their identities, checks prefix and outcome accounting, then computes raw RGB8 absolute paired differences and reports allocation/cost changes. It runs no solver and adds no visual success gate. Preserve T42's unqualified visual task and do not interpret ordinary admission changes as a TOG method.

The saved audit also rehashes the20 frozen inputs, verifies the invocation/freeze link, exact four-arm/360-step inventory, all historical prefix counters/hashes and block AB endpoint, zero-time intervention hashes, saved frame/capture GL flags, actual saved output size including the supervisor receipt, and empty capture failures. It compares the original opaque native hash values; it does not claim an independent FNV recomputation or a complete-state certificate.

After independent static review, the only execution entry is:

    python tracks/tog/tasks/t81-firewoods-capacity-causality/run_once.py

After a successful complete capture, saved readback is:

    python tracks/tog/tasks/t81-firewoods-capacity-causality/audit_saved.py

No command above has been executed during preparation except `prepare.py` and static syntax checks.
