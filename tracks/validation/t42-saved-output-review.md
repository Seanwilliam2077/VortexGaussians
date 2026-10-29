# T42 independent saved-output review

Result: **saved data consistent; visual task qualification remains separate**. After root confirmed that the sole dynamic worker had terminated, I invoked the frozen `audit_saved.py` once with Python `-I -B -u -X utf8`. It exited 0 with 521,226 passing predicates and no failures. Most predicates are per-point consistency checks, not independent scientific tests. No browser, simulation, original demo import, or additional trajectory was run. The auditor and raw output were not repaired or changed after execution.

The audit recomputed the terminal inventory's file sizes/SHA256 values, all six state gzip/raw identities, PNG chunk CRCs and decoded dimensions. Each checkpoint contains all 34,687 unique `ply:index` IDs in the declared lexical order, finite material values and fixed positions. Complete parameters, seed, buffer, camera vectors/matrices, frame/time, material bounds, frontier membership and scene aggregates passed. The six post-render GL checks also passed; pre-render state checks alone were not used to qualify rendering. The original source/asset entries of `freeze.json` were not independently reread by this auditor; the freeze document's identity was recorded, and the capture's input checks were reported successful.

| Checkpoint | Frame | Burning material points | Gas-particle count |
|---|---:|---:|---:|
| Initial | 0 | 0 | 0 |
| Immediately after A | 0 | 145 | 0 |
| Before B | 180 | 3,374 | 2,394 |
| Immediately after B | 180 | 3,662 | 2,394 |
| Endpoint | 360 | 3,662 | 2,433 |
| Reset | 0 | 0 | 0 |

Independent saved-position sphere checks recovered all 145 A neighbors and all 288 B neighbors. Both sets were eligible at their respective ignition times, and exactly those points changed from cold to burning. Across each zero-time ignition, all point fields other than the permitted state changes matched exactly; the previous frontier remained an unchanged prefix, and the return count matched the appended set. Frame/time, random-draw count, counters, parameters and camera were unchanged. All exported gas aggregates and the program's particle-state hash were unchanged. **Complete gas arrays were not exported:** the latter is an opaque, non-cryptographic program hash, not independent elementwise gas-state verification.

The original 145 A points continued without reset. Their fuel sum was 145 immediately after A, 72.50058770179749 before and after B, and 0.00044612025703827385 at the endpoint. Their char sum progressed from 0 to 85.29423356056213 to 145. All 145 still had `state=1` at the endpoint, so this review does not call them fuel-exhausted merely because char reached 1. The initial and reset serialized states were byte-identical after decompression (6,424,104 bytes, SHA256 `42a0685559ec81cbd806c7a8a80c87075b6cb160c1dac9821d2c1aa1cd2efb61`); their gzip bytes also matched.

All six PNGs decoded as 940×528 RGBA8, with nonblack pixels and no post-render GL errors. The saved `draw_count` was 0 in every checkpoint; it is preserved as an uninterpreted exported counter and is not evidence of zero actual rendering or a validated instance count. This reviewer did not assess visual identifiability. Nonblack images and state correctness do not establish that both authored operations are visually legible.

The worker recorded 30.5378862 s, including capture/cleanup. Its twelve stepping phases totaled 6.7850480 s; six state-export phases totaled 18.8770166 s; state writes 0.4968730 s; render/export 0.2153271 s; PNG writes 0.0126405 s. These phases include API and capture overhead and are not a renderer or optimized-solver benchmark. Supervisor time to the terminal/live check was 31.1530631 s, inventory hashing 0.0129843 s, and elapsed time before receipt writing 31.1660551 s. The final small supervisor receipt write/stdout flush is excluded. The audit itself reported 4.6918372 s. No FPS claim follows.

Reviewed identities (SHA256):

| File | SHA256 |
|---|---|
| `audit_saved.py` | `4fea88b5f0897a117d87fa98347b72cbdff0a1b4d1ed1a0c0794579a02d1da96` |
| `result-audit.json` (35,252 bytes) | `6b9d58ef92fdf4bb7a7e07ecc63c69b98a8af47cca457d2cce8f8806cd319dbc` |
| `PROTOCOL.md` | `1719d3cd48dd08c1d6bd16f4b48ce7fc1e7d7063ad4769f5737e91a9ca994ef2` |
| `recipe.json` | `982c98d3187ab26e95e251de562950adaab9a2101d1f1ff6371c93e7f6383013` |
| `freeze.json` | `2dc93f1b2d0d4bf2edfaac9f6fa3c6bac4d8fa595de35c149c7506c55dd83bb9` |
| External `run-01/result.json` | `4d086b367da10afe23bf34bdd2a1670edf18501acdfef5091cb892cab4b4ffac` |
| External `run-01/supervisor.json` | `415d0ea0a23488b74a23a8dbc47025336f8a2c77fbdb913368162683408bb8ec` |

This establishes consistency of the one saved ordinary workflow. It does not establish physical combustion, sampling-density invariance, superiority to another method, a creator requirement, or a TOG contribution. The disclosed failed 3-pixel preparation rule remains failed; the successful pre-freeze 10-pixel revision was not reclassified by this audit.
