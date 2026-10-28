# T16 source, budget and inference review

28 October 2026. **The recorded acquisition budget and the narrow source-level decision are supported. No renderer was runtime-qualified, benchmarked or certified.** This review made no network request and did not import or execute third-party source, install dependencies, construct a scene, or run a numerical/GPU test.

The review first read T15's `NEXT_EVIDENCE.md`, `C_VOLUME.md`, the current status and the acquisition ledger. It then independently checked all nine saved files' byte lengths and SHA256 values, read the entry/import/metadata files and critical RF, PRB and common-helper paths, and compared the resulting claims with the four T16 documents below. It did not inspect the unacquired dependency implementation or independently recreate the acquisition requests. This is an evidence and reasoning review, not full-engine code verification.

## Reviewed publication identities

Paths in this table are relative to `tracks/tog/tasks/t16-ordinary-volume-reference/`. These hashes identify the versions reviewed after the terminology and source-line corrections.

| File | SHA256 |
|---|---|
| `README.md` | `27e81ad3b4938e4afb83b5b0fdeb6a2c11983d2c7299675eeff2d01a51cc952d` |
| `COST.md` | `68ecb00de7835e6c6ea3bb56620baf9b693b14891c21b1bb6638032537ff395f` |
| `SEMANTICS.md` | `c5a4e21bff60b2b094708b6315dcd309e3cb2c7dcc142485d0e5a42693b09f46` |
| `access-ledger.json` | `5c9adab5a3ed0f570053e1ba4cf80d6ff208474e42df308faaab4bee5a6eb025` |

The external and repository copies of the final ledger have identical hashes. The ledger records revision `622fabdac87aa446ca84131da97ebb9ac7d3d20c`, discovered by `git ls-remote --symref ... HEAD`; all saved raw-file URLs use that revision. The initial unpinned repository landing is recorded as discovery, not fixed-version implementation evidence.

## Saved source identities independently checked

Local source root: `C:/Users/seanzjxiao/Documents/Codex/2026-10-13/https-github-com-jiarui-liu-ideascientist/work/research-t16-source-audit/sources`.

| Source-relative path | Bytes | SHA256 |
|---|---:|---|
| `README.md` | 6761 | `183c3bd1389b42d99edc4778515a341af147b6861044af70075e93c4b36f3779` |
| `requirements.txt` | 67 | `d1d997c3d75e2f002d5470452eb9a1810bb80bc37cb69ff1fe256363b96f350b` |
| `environment.yml` | 202 | `d0c18f23905d3a8a00e7da3998a7b5a8ba18f53b1efd316c39df6e11bc9a4124` |
| `examples/render_3dg_asset.py` | 2920 | `9ac609a25a3d8fb7eee8c567b8b4ff238130b7307823056b41b1b3d520dd947a` |
| `volprim/__init__.py` | 425 | `9fa8bab4199a35c2c6aad14770c802de902ffe6b498abcb2131726168905181e` |
| `volprim/integrators/__init__.py` | 286 | `6a916ed042afbf2e96417a7fd44c00381786fa1f9657b8192626802377bc92a6` |
| `volprim/integrators/volprim_rf.py` | 8352 | `b45efa6f9cf2095aa0092c6ce94701237fd38c9e23b1f59e3db9f26e8d9175f1` |
| `volprim/integrators/common.py` | 24747 | `d8f020bacd9f7b775d7f7eb02de80bd0ffcec004753db2e94bca35a122ff5a8c` |
| `volprim/integrators/volprim_prb.py` | 30009 | `95729d9464c81963996e8b29b8379a400ef384e4a10c081b8018365820c92a25` |

All nine saved byte lengths and hashes match their ledger entries. There are exactly six code files, one README and two dependency metadata files. Their saved bodies total **73,769 bytes**, including 66,739 code bytes, within the 2,097,152-byte body cap. This is not a measurement of all network traffic. The ledger correctly leaves total network bytes and research wall time unknown.

## Acquisition and failure accounting

The final ledger has eleven acquisition records (nine saved bodies and two failed inventory attempts) plus two discovery records. The API tree attempt returned rate-limit HTTP 403; one normal webpage tree fallback also failed. No repeated successful raw-file download is recorded. File selection follows the named example and inspected imports within the six-file cap; uninspected imports do not count as acquired implementation evidence.

The first local output failure occurred after four bodies were saved: GBK stdout could not encode a README emoji before the ledger flush. Recovery used those existing files. HTTP status is retained as 200 for README, while three lost statuses remain null rather than invented successes. Later records retain their statuses. A file hash proves the identity of a saved body, not a missing HTTP timestamp or status, and the documents preserve this distinction.

The ledger and work record report zero third-party execution, installations, downloaded scene assets, numerical experiments and GPU runs. Inspection and checksum calculation are the performed checks; those zero counts are not zero-error test results. The reviewer did not install or run anything to strengthen a source-only claim.

## Source conclusions cross-checked

**RF model.** In `volprim_rf.py:63–80`, the inspected transmission function evaluates a Gaussian at its ray-peak location and returns `1-min(opacity*density,0.9999)`. Its caller accumulates `beta*(1-transmission)*emission` and updates `beta`. The presence of a Gaussian segment-integral helper elsewhere, or constructor flags affecting that helper, does not turn this call into `exp(-integral sigma)`. SH emission and default post-accumulation sRGB conversion add further contract differences. The source finding is sufficient to reject this route as the unchanged C integral without timing it.

**PRB model.** The checked forward path requires `sigma_t` and `albedo`, samples a medium interaction using segment optical depth, multiplies throughput by the weighted albedo, and adds environment escape/next-event contributions. The inspected `eval_albedo` primal helper returns the weighted albedo; its other radiance-related operations are in the non-primal branch. The forward `L` increments do not supply C's prescribed self-emission `j=sum_i s_i*c_i`. This conclusion is about the acquired entry points, not all repository files, releases or author methods. Neither named absorption-only functionality nor an uninspected plugin is silently treated as failed or as a matching reference.

**Intervals and guarantees.** Main primitive tracing includes surface-limited segments, while other transmittance paths and support conventions have distinct limits documented in `SEMANTICS.md`. The review does not upgrade these observations to a measured bug. Fixed depth, throughput and inversion-step rules are not a componentwise RGB-error certificate. An empirical reference image would not establish directed-rounding or truncation guarantees either. No such image was rendered here.

**Cost.** `common.py:423–560` visibly rescans active primitives, scans stored vertices to choose an endpoint and conditionally shifts entries on removal. The PRB callback and inversion routines add active-primitive integral evaluations. These are source-level work items; they are not observed operation counts for a scene, elapsed time or proof of an overall quadratic bottleneck. Stack internals, backend intersections, Dr.Jit scheduling, overlap distributions and memory behavior remain uninspected or unmeasured. `COST.md` correctly includes those limits and separates scene preparation from the example's named render timing region without claiming its asynchronous behavior is known.

## Decision and continuation boundary

Stopping this named source route and declining to prepare a numerical experiment follow T16's prior gate: no acquired entry point supplies the same colored self-emission model, and no specific accuracy/cost question beyond known semantic differences has been established. A mathematical ordinary quadrature route still exists in principle; this audit neither disproves it nor identifies a worthwhile measurement by merely noting that one could write it. The current source findings do not select a new method or a fourth candidate.

Stopping the **automatic work queue** requires an additional operational fact; it does not follow from the scientific no-go alone. Root reports that no running computation, pending publication or external event remains to advance or monitor. Under that fact, removing an otherwise repetitive scheduled wakeup is consistent with the empty queue. This review does not independently certify the desktop process inventory or automation deletion; those actions have their own tool evidence. The source review itself does not cancel continuing research authorization, mark the TOG goal complete, constitute a user-requested pause or prove that research must permanently end. Resumption need not depend on the user inventing an idea or supplying private material.

There is no blocking inconsistency in the four sealed documents under these limits. The small review clarifications were applied before the hashes above: static formulas are called implemented/inspected rather than executed; path-weight truncation is distinguished from performance throughput; and the recorded example import location is line 23. No added simulation or benchmark is needed to support this source-audit outcome.
