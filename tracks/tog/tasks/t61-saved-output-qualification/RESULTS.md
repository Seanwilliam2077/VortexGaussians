# T61 results — acceptance of existing full-window observations

## Outcome

The one permitted qualification child returned zero. [result.json](result.json) records `qualified_saved_reference_ordinary_model_fail`; [execution.json](execution.json) records `completed_qualified_saved_reference_ordinary_model_fail`. `accepted_saved_evidence=true`, `reference_qualified_full_window=true` and `full_t1_task_pass=false` describe different decisions: the evidence is eligible, and the tested model misses the task requirements.

T60's original failed receipt remains byte-identical: 22168 bytes, SHA256 `3eaf3d644c649ed26dc10d9a1f52546232b635a4e2c598ac47564c78197c727e`. Its numerical result remains 136401 bytes, SHA256 `8908fe090dd50c2c60291ffde31a52fb0e525063d9a66646462c6d3e6ba88954`. T61 accepts these saved observations under a separately specified path contract; it does not repair or reclassify T60. No new independent numerical sample was obtained.

## What was checked

The validator re-derives all twelve original reference predicates from saved scalar/log records: initial analytic accuracy; stage solver/positivity/CFL/divergence conditions; core field, velocity, centroid and covariance disagreements; spatial reduction; circulation ledger; q-squared and impulse drift; D8 field disagreement and reduction. Every predicate passes with the original thresholds and small-error waivers. Ordered records cover six fresh cases, 2800 steps, 5600 stages, 5630 solves and thirty snapshots. Thirty-six raw NPZ files were streamed only for identities.

All ten stored model scores at five times on S256 and S128 retain their primary 8x6 and confirmation 16x12 rules. Twenty stored numerator/denominator calculations reproduce the scores and their original agreement gate. The saved maximum rule difference is 1.3877787807814457e-17, below 1e-6. The original evaluation count is 196608000 Gaussian points, not new T61 work. The S256 reference axial displacement is 0.35276936493470806, above the unchanged 0.25 motion requirement.

The sole changed contract concerns `local/checkpoints.jsonl`, `local/reference-evaluation.json` and `local/ordinary-model-screen.json`. Each saved backslash spelling resolves to the exact expected artifact, with matching bytes/SHA256 and containment. Six accepted and seventeen rejected literal path checks passed before freezing. Those checks did not create a symlink fixture; containment was also inspected statically. All other acceptance meanings remain unchanged. Readback arithmetic uses relative 3e-11/absolute 3e-14 consistency tolerances; these are not altered physical gates.

## Qualified ordinary-model observations

The frozen T54 complete-tangent coefficient yields constant speed c=0.43546484316145384 in qG=1.5 exp[-(r²+(z-ct)²)/2]. No coefficient or frame was fitted to the reference. Its primary S256 measurements are:

| t | Relative physical-vorticity L2 error on D8 | Absolute axial-centroid error | Relative covariance error |
|---|---:|---:|---:|
| 0 | 0.000291900 | 3.25e-18 | 0.000003414 |
| 0.25 | 0.029241972 | 0.020485499 | 0.024116325 |
| 0.50 | 0.058402137 | 0.041046736 | 0.048659602 |
| 0.75 | 0.087409620 | 0.061758839 | 0.074027104 |
| 1.00 | 0.116193272 | 0.082695478 | 0.100569102 |

Each of the three gates is <=0.10 at every sampled time. Covariance error uses the actual initial S256 reference covariance Frobenius norm, 1.0882203729522952. Field and covariance gates fail only at the final sample; axial-centroid passes. The covariance excess is small and must not be presented as a robust standalone separation.

S128 sensitivity at t=1 gives field error 0.11616090595736346, centroid error 0.08263481129724187 and covariance error 0.10075853335898956. These comparisons support the direction of the observed discrepancy; they are not rigorous bounds on the continuum error. Reference qualification is empirical on the fixed grids/domain, not a proof that every reported digit is physically accurate.

## Cost and preservation

| Work | Supervised child seconds | Interpretation |
|---|---:|---|
| T56–T60 scientific history, including failures | 1976.6796338998247 | Unchanged cumulative experimental cost |
| Of that history, T60 scientific child | 416.26116519991774 | Six complete reference trajectories and score work |
| T61 qualification child | 0.9663960000034422 | Standard-library hashing, JSON/log parsing and scalar readback only |

T61 child time before writing its result was 0.8606901998864487 seconds. Supervisor elapsed time before receipt writing was 1.5406554999062791 seconds. The preparatory literal path check reported 0.0046048000222072005 seconds before writing its own receipt. These timings are distinct scopes, not a speedup comparison or a complete accounting of human/agent preparation time.

All 151 frozen repository inputs, one historical executable and the bookkeeping executable match before and after the child; 153 file identities were covered. The freeze is 31766 bytes, SHA256 `ed4e5a7b8392f4ffaea6fa0705d4715edd0a5aab9792b74030066b0f061d616d`. The qualification result is 3936 bytes, SHA256 `c6ac286c4527ad4925e1d85b4cd0cfc897ea5ceced413c810496dd716a0cd679`. Scientific invocations and trajectories added by T61 are both zero. Logs and the earlier large raw files remain ignored local artifacts with identities, not public asset uploads.

## Limits and implication

No arrays, Gaussian evaluations or integrals were recomputed in T61. Core field measurements remain saved scalars, supported by the [earlier saved-array review](../../../validation/t60-full-window-review.md); that review did not independently reproduce Gaussian score integration. Unsaved intermediate face upper bounds rely on the frozen producer assertions, while logged minimum/solver/CFL conditions were rechecked. The original command did not disable assertions. The [T61 review](../../../validation/t61-saved-output-review.md) discloses its pre-run participation and does not constitute numerical replication.

The result applies to D8 and five sampled times of the researcher-defined isolated vortex-ring task. It is not a whole-space or continuous-time certificate, visual-quality study, creator need validation, held-out result, universal single-Gaussian impossibility or method novelty. It does establish an eligible finite-time failure for this strong ordinary tangent-projected trajectory. The [next decision](DECISION.md) tests whether the gap lies in this evolution rule or in the permitted representation before proposing a new method.
