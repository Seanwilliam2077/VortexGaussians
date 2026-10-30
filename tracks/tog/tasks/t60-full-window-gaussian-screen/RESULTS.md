# T60 results — computation completed, final acceptance failed

## Authoritative outcome and cause

The [execution receipt](execution.json) is `failed_result_validation_no_retry`, child return code 0. Its `complete_result_validated`, `reference_qualified_full_window` and `qualified_model_outcome` are false; the accepted ordinary-model verdict remains `unqualified`, with `full_t1_task_pass=null`. In contrast, the numerical worker's [result](result.json) reports `qualified_reference_ordinary_model_fail`. These records describe different stages and are both retained unchanged.

The first failed supervisor predicate is `run_once.py:229`: the worker stores `checkpoint_index.path` as `local\checkpoints.jsonl`, while the supervisor requires the literal `local/checkpoints.jsonl`. Analogous predicates at lines 231 and 272 concern the reference-evaluation and ordinary-model evidence paths. The worker obtains these strings with Windows-native `str(relative_to(...))`; the result files themselves exist and their hashes match.

A standard-library-only diagnostic extracted the saved-result validation block without importing/calling the supervisor, launching a child, loading NumPy, or running a method. Its unchanged replay fails at line 229. A separate in-memory control changes only those three comparisons to `PureWindowsPath(...).as_posix()`; the full original validation block then completes. This isolates the rejected representation, but is a diagnostic, not permission to revise T60's failed receipt or automatically assign scientific qualification. Six protected source/result/receipt/freeze files match before and after.

Retained local diagnostic identities: `readback_diagnosis.py`, 6799 bytes, SHA256 `7cee43ac58892d1cd87d3fbf3e5222d7b3e21cbe872670d28429bef878c05dcd`; `readback-diagnosis.json`, 3341 bytes, SHA256 `f32af7272918b376a7907f9b2ec39bfeeb47e74d37882c8f5f85f14b716f8918`. No scientific retry, source edit, threshold change, alignment or coefficient fitting occurred.

## Saved numerical observations, pending separate acceptance

All six cases reach 0,.25,.5,.75,1: 2800 steps, 5600 transport stages and 5630 fresh direct solves. The worker records all twelve reference categories passing. The supervisor validates six case records and thirty checkpoint records before rejecting the final aggregate result. These artifact counts do not override the failed end-to-end qualification.

| Pair | Maximum core vorticity difference | Maximum D8 vorticity difference | Maximum core velocity difference |
|---|---:|---:|---:|
| S64/S128 | .006007323791 | .006007447210 | .003099685344 |
| S128/S256 | .001645468379 | .001645502055 | .0007741252365 |
| S128/T128 | 4.999721491e-7 | 4.999716772e-7 | 1.324771070e-7 |
| S128/D192 | 2.261096735e-7 | 2.261101205e-7 | 2.041557890e-6 |
| S128/Q128 | 5.111033033e-16 | 5.111032452e-16 | 2.390135349e-15 |

Nonzero-time D8 spatial reduction factors are 3.883707773, 3.789031973, 3.708772639 and 3.650829356. Maximum original weighted residual is 1.7374625722690776e-14; CFL .0799772921107; flux divergence 5.6843418861e-15; circulation-ledger discrepancy 3.5433192416e-16. Maximum saved q-squared and axial-impulse drifts are .00238836928531 and .000651351142558. These are empirical controls, not a rigorous free-space certificate.

The stored primary S256 centroid advances .352769364934708 initial widths, above .25. The ordinary unchanged projected Gaussian has speed .43546484316145384, loaded from T54; no fitting or stepping is used for its parameter trajectory.

| Time | S256 physical-vorticity relative L2 | S128 sensitivity L2 | S256 axial-centroid error | S256 covariance error / actual initial covariance norm |
|---|---:|---:|---:|---:|
| 0 | .000291899528 | .001161309667 | 3.24715955e-18 | .000003413642 |
| .25 | .029241971826 | .029277263354 | .020485499327 | .024116324600 |
| .5 | .058402137094 | .058424573371 | .041046736226 | .048659601705 |
| .75 | .087409619858 | .087411421220 | .061758838834 | .074027104234 |
| 1 | .116193271992 | .116160905957 | .082695478227 | .100569102286 |

The saved scores cross the original .10 vorticity and covariance gates at t=1, while centroid remains below .1. S128's t=1 covariance score is .100758533359. The covariance excess is small; neither the resolution comparison nor the very small integration difference provides a rigorous uncertainty interval. The maximum 8x6-versus-16x12 relative-score difference is 1.3877787807814457e-17 over ten records. The primary rule was not substituted.

All field claims concern D8 and five samples. Reference moments use each finite computational box; model moments are analytic all-space quantities. Within D12, maximum circulation and physical-vorticity-squared fractions outside D8 are 1.3910112612e-14 and 1.0357506731e-26; these are diagnostics, not missing-tail bounds. This remains a researcher-defined isolated-ring task, without creator validation or proof that all Gaussian representations fail.

## Cost, preservation and independent readback

The one child costs **416.26116519991774 s**, including all Green construction/applications, direct solves, transport, measurements and output. Internal time before final JSON writing is 415.9067361999769 s; supervisor time before receipt writing is 417.61889619997237 s. Core comparisons, D8 controls and ordinary-model measurement cost .291367800, .330151400 and 8.749823300 s respectively. The latter includes four fixed quadrature rules, twenty rule-integrals and 196608000 Gaussian evaluations/reference reconstruction points. Named counts are not FLOPs, and nested timers must not be added twice or turned into an equal-work speedup.

There are 1662 memory observations. Observed lifetime peak working set is 2067156992 bytes, below 2147483648; maximum private usage is 2046726144 bytes, peak pagefile usage 2046730240 bytes. Last observation occurs at 416.260160800 s. Available host physical memory at launch is 27252137984 bytes. These are observed counters, not reserved capacity or a hard allocation cap.

All 49 frozen inputs, the manifest and executable remain unchanged. There are 36 retained NPZ files totaling 342109364 bytes, six step logs and thirty checkpoint metadata files, with no case/checkpoint-validation errors and no worker failure file. Result identity: 136401 bytes, SHA256 `8908fe090dd50c2c60291ffde31a52fb0e525063d9a66646462c6d3e6ba88954`. Failed execution receipt: 22168 bytes, SHA256 `3eaf3d644c649ed26dc10d9a1f52546232b635a4e2c598ac47564c78197c727e`.

The [independent saved-data review](../../../validation/t60-full-window-review.md) verifies all NPZ/checkpoint equivalences and log counts, independently reduces thirty saved q moments and twenty-five D8 polynomial comparisons, and checks the scalar arithmetic of twenty stored Gaussian integrals without reevaluating Gaussian fields or rerunning a solver. Its measured array/log audit costs .743042200 s, total with imports/identities 1.294863100 s. The reviewer participated in pre-run review; this is not a blinded replication. Standard-library path diagnosis and publication bookkeeping are additional support work, not new scientific invocations; their elapsed time is not included in the scientific-child total.

Prior T56–T59 scientific-child cost 1560.418468699907 s plus T60 gives **1976.6796338998247 s**. T56/T57 failures and all historical gates remain unchanged. T60's final failure also remains unchanged. A specific, separately frozen read-only qualification can assess these saved observations without another trajectory; that is the [next decision](DECISION.md), not a completed result here.
