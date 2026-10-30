# T71 — ordinary causal full-window measurement

**Completed: numerically qualified, time-sensitive and inconclusive.** Both ordinary causal paths reach t=1 and all eight numerical categories pass. Reference sensitivity passes; time sensitivity fails. The coarse path passes every original physical checkpoint against both references; the finer path misses the final covariance gate. This does not establish a stable full-window physical pass or a family-wide failure.

Receipt status: `completed_time_or_reference_sensitive_inconclusive`. Retained worker verdict: `time_or_reference_sensitive_inconclusive`.
The original execution receipt and worker result remain unchanged. This is one development measurement, not a new method or TOG contribution.

## Fixed question and actual progress

[Protocol](PROTOCOL.md) and [input identities](input-manifest.json) define two independent ordinary two-Gaussian paths from exact q0, with h=1/16 and1/32. Prediction must be sealed before reference access. The five original times use world-coordinate D8 field error<=.10, axial-centroid error<=.10 and covariance error / original D0<=.10; all17 shared times receive the separate fixed time-sensitivity comparison. No endpoint fit supplies predictive information.

- h=0.0625: reported 16 updates; 17 stored states.
- h=0.03125: reported 32 updates; 33 stored states.

Saved search records: 48. Reported completed updates: 48. These counts describe retained data and do not by themselves establish qualification.

| h | Reference | t | Field error | Axial centroid | Covariance / D0 | Joint |
|---:|---|---:|---:|---:|---:|---|
| 0.0625 | S256 | 0.0 | 0.0002918995275417307 | 1.0304223512656163e-18 | 3.413641800215211e-06 | True |
| 0.03125 | S256 | 0.0 | 0.0002918995275417307 | 1.0304223512656163e-18 | 3.413641800215211e-06 | True |
| 0.0625 | S256 | 0.25 | 0.020509655072914988 | 0.005639549234747451 | 0.02279823670668213 | True |
| 0.03125 | S256 | 0.25 | 0.02040426476720008 | 0.005297973303946893 | 0.02170464265888357 | True |
| 0.0625 | S256 | 0.5 | 0.04087368837588203 | 0.0061951883247660655 | 0.04114363157082793 | True |
| 0.03125 | S256 | 0.5 | 0.04072840426336488 | 0.005311124329657246 | 0.03899097490774967 | True |
| 0.0625 | S256 | 0.75 | 0.06363041762991081 | 0.018068241553362147 | 0.06098268877733434 | True |
| 0.03125 | S256 | 0.75 | 0.06475996235637625 | 0.0077862645117903195 | 0.06863289316223506 | True |
| 0.0625 | S256 | 1.0 | 0.08026183172847268 | 0.014363284599397508 | 0.056935691858066045 | True |
| 0.03125 | S256 | 1.0 | 0.09475414116343878 | 0.0020703978257362587 | 0.10944814650172537 | False |
| 0.0625 | S128 | 0.0 | 0.0011613096674279286 | 4.440683294304291e-18 | 2.7088248040789983e-05 | True |
| 0.03125 | S128 | 0.0 | 0.0011613096674279286 | 4.440683294304291e-18 | 2.7088248040789983e-05 | True |
| 0.0625 | S128 | 0.25 | 0.020569935482236665 | 0.005654432781465449 | 0.022881174170438966 | True |
| 0.03125 | S128 | 0.25 | 0.020460441407904303 | 0.0053128568506648904 | 0.02178357637220977 | True |
| 0.0625 | S128 | 0.5 | 0.04094717220453212 | 0.006225148392463464 | 0.0412782962413006 | True |
| 0.03125 | S128 | 0.5 | 0.04079170807535862 | 0.005341084397354645 | 0.039111889382597645 | True |
| 0.0625 | S128 | 0.75 | 0.06377865643504094 | 0.018113446411826245 | 0.061205890255497074 | True |
| 0.03125 | S128 | 0.75 | 0.06489425948116544 | 0.007831469370254418 | 0.06886143974717272 | True |
| 0.0625 | S128 | 1.0 | 0.08041189469492611 | 0.014423951528901247 | 0.05705483607228038 | True |
| 0.03125 | S128 | 1.0 | 0.09494250704452314 | 0.0021310647552399975 | 0.10978997573949333 | False |

## Qualification, cost and provenance

Receipt acceptance: `True`. Qualified full-task predicate: `False`. The two paths first exceed a time-sensitivity gate at t=.75. At t=1 their direct field difference is .0323876056015902, axial-centroid difference .0122928867736612 and normalized covariance difference .0774483311036347, each above its original .01 threshold. Maximum S256/S128 score differences are .000869410139886198 (field), .0000606669295037388 (centroid) and .00034182923776796 (covariance), all passing. Finer h being worse here does not identify whether finite search, integration or representation is responsible. See [evidence.json](evidence.json) and the [independent source/saved-record review](../../../validation/t71-causal-full-window-review.md).

All 48 searches complete: 69294 proposals, 9538 component evaluations, 189462 weight attempts and 48 unchanged controls. The 176 field calls include 663748608 component heat-point visits; 9730 cross calls contain 37648 ordered integrals and 4866560 heat integrand points. The scalar journal contains 80628 events. Circulation and impulse drift are retained in the result; there is no conservation repair.

The supervised scientific child interval is 26.20414529996924 seconds; cumulative recorded scientific-child interval is 2017.6732525997795 seconds. Observed peak working set is 68268032 bytes. The supervisor interval includes child time and must not be added to it. This is not total project cost or a speed comparison.

## Saved records and limits

- [result.json](result.json)
- [predictions.json](predictions.json)
- [execution-started.json](execution-started.json)
- [stdout.txt](stdout.txt)
- [stderr.txt](stderr.txt)
- [memory.jsonl](memory.jsonl)
- [Original execution receipt](execution.json), [compact scalar evidence](evidence.json), [export identities](exports.json).
- [Next bounded decision](DECISION.md).

The 165632166-byte detailed scalar journal stays in ignored local storage; its complete byte/hash identity and structural summary are published in exports.json. The full result and sealed trajectories are public. A fresh checkout therefore lacks this original detailed journal and the historical raw reference assets; exact record-only replay needs the retained local inputs. The reporting helper does not rerun the simulation or claim full standalone reproducibility.

This remains one researcher-defined development task, with finite sampling and empirical binary64 integration controls. It establishes no new method, formal error certificate, family impossibility, production demand or TOG contribution. Art, main, historical failures, reviews and global research state are outside this preparation script's write scope.
