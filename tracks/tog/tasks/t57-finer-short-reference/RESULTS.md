# T57 — finer short-reference qualification did not complete

**Terminal status: `timeout_no_retry`.** The unique scientific child was stopped by the 1200-second time budget. It completed **zero of four** planned new trajectories. S256 has 73 completed step records out of 100, reaching t=0.1825 in the step log. T128, D192 and Q128 never started. There is no new NPZ, completed case JSON or result.json, so no new full-field spatial/control comparison, analytic-initial gate, drift gate or finer-reference qualification verdict exists. The task failed its resource/completion contract; this is not evidence that a Gaussian representation failed.

The two saved T56 cases were loaded for the planned comparison but not rerun. Their previous agreement stays old evidence. T56 remains `completed_failed_checks`, with its complete 116.53663460002281-second cost retained. No pilot, retry, fallback, resolution change, source query, install, candidate trajectory or t=1 task occurred.

## What was actually recorded

| Partial S256 evidence | Recorded value |
|---|---:|
| Complete logged steps | 73 |
| Complete logged transport stages | 147 |
| Complete logged elliptic solves, including snapshots | 149 |
| Snapshot solve records at steps | [0, 50] |
| Logged CG iterations | 180283 |
| Maximum iterations per logged solve | 1226 |
| Logged CG direction restarts | 0 |
| Maximum logged true weighted residual | 9.997855588309177e-11 |
| Maximum logged outgoing CFL | 0.07997729211806799 |
| Maximum logged volume divergence | 5.684341886080802e-15 |
| Maximum completed-step circulation ledger error | 2.362212827723424e-16 |
| Minimum completed-step Euler-stage q | 3.04947628821925e-28 |
| Minimum logged face q | 2.598861814481879e-28 |

All completed logged stages/steps satisfy the original checks represented in those records. This does not certify an interrupted in-flight solve or the whole scheduled trajectory. The recorded iteration count excludes any interrupted, not-yet-logged solve. Parsing found 0 malformed lines. Snapshot **solve records are not field checkpoints**: unchanged solve_case retains arrays/statistics in memory and writes them only after a complete case. Even the intermediate snapshot fields were therefore not saved. No inferred or fabricated checkpoint is supplied.

## Complete invocation cost and partial phase attribution

| Cost | Seconds |
|---|---:|
| This child, supervised including launch/termination | 1200.257536700 |
| Supervisor through validation, before receipt write | 1200.329542200 |
| Prior complete T56 invocation, including failed/control work | 116.536634600 |
| T56 + T57 supervised child cost | 1316.794171300 |
| Logged completed Poisson solves | 1059.845616200 |
| Logged boundary matrix-vector products | 10.845489900 |
| Logged reconstructions | 2.844647500 |
| Logged transport evaluations | 3.933630100 |

Logged Poisson solves alone account for 88.302% of the full failed invocation. Remaining time includes geometry, imports, old-array loading, initial-oracle/statistics work, unlogged in-flight work and overhead. The killed case never wrote its kernel-build timer or case summary, so exact geometry-build seconds cannot be recovered. The fixed source constructs a 1,075,838,976-byte S256 matrix; that formula is not a process-memory estimate. No equal-work speedup, asymptotic conclusion or inherent limitation of ordinary methods is claimed. These totals do not include the whole earlier research history, whose separate receipts remain preserved.

The 1200 s cap is observed by a .25 s supervisor loop; kill/wait and scheduling introduce termination latency, reported in the full wall time rather than hidden or rounded down. Return code is 1. The supervisor terminated only its own child and did not retry.

## Memory and preserved inputs

The OS-only preparation observed 26,864,070,656 B available physical memory. Immediately before launch, 26,696,884,224 B was available, above the fixed 3 GiB requirement. The monitor saved 4790 observations; maximum observed OS lifetime peak working set was **2,052,538,368 B (1.911575 GiB)**, below the 2 GiB stop threshold. Maximum observed private usage was 1,967,009,792 B; OS peak pagefile usage reached 2,032,242,688 B. Private/commit counters were reported but were not the frozen stop criterion.

The last memory sample occurred at 1200.000404700 s. Query-unavailable-after-exit flag: `False`. These are observed process counters, not an allocation cap or formal bound over an unobserved final exit/kill tail. In particular a false query-error flag does not imply the supervisor sampled after killing the child.

All 28 frozen input identities and the scientific executable remain unchanged. Python/NumPy versions were asserted at child entry; the preflight records Python 3.12.14 and the frozen scientific expectation is NumPy 2.3.5. No final child result exists from which to claim a completed runtime/version report. `execution.json` records complete identities for stdout, stderr, memory samples and the partial step log; these are retained in ignored local storage. Source/protocol/preflight/execution and this report are public; large raw arrays and private notes are not committed.

[The review](../../../validation/t57-finer-short-review.md) must be read with its pre-run participation disclosed; it is a source/log/preservation audit, not an independent fluid replication. [The next decision](DECISION.md) selects a separately frozen ordinary same-operator solver qualification. No new solver qualification or new fluid invocation has occurred in T57. Full TOG contribution remains unestablished; art is inactive, main unchanged and the deleted automation unchanged.
