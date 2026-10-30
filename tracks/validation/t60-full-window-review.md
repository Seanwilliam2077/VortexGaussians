# T60 full-window saved-evidence review

## Verdict and provenance

**Accept the final documentation as a faithful account of a failed acceptance task; do not qualify or reclassify T60.** The authoritative receipt remains `failed_result_validation_no_retry`, with `complete_result_validated=false` and ordinary-model verdict `unqualified`. The worker's different internal result is preserved as saved evidence. No unresolved documentation blocker remains.

Reviewer `t48_review` inherited T48–T59 collaboration history and participated in T60's pre-run contract, actual source, supervisor and 49-input freeze review. This was not blinded review. The pre-run review reported no blocker and missed the Windows path-string acceptance defect; the later diagnosis does not erase that review limitation. After termination, the reviewer performed one independent reduction of existing arrays/logs and scalar records, then read the final README, RESULTS, DECISION and author-owned diagnostic source/output. No scientific source was imported, and no solver, FFT, Green integration, evolution, Gaussian field evaluation or 8x6/16x12 score integration was rerun. No task source, result, receipt or historical gate was edited.

## Contract and acceptance defect

The minimal T59 fork preserves the original transport/reconstruction equations, original weighted residual check and fresh direct factors. Explicit pre-freeze buffer releases follow their last use. Six fresh trajectories extend to t=1 at five samples; the full schedule is 2800 steps, 5600 stages, 5630 solves and 30 snapshots. D8 comparisons use physical-vorticity weight 2*pi*r^3, the second-field denominator and common finer partitions. The 3x2 polynomial rule is sufficient for the piecewise-linear q products. Model scoring uses the frozen T54 `closed_metrics.beta_best_over_g0`, speed `1.5*beta`, the fixed primary and confirmation rules, and the actual initial S256 covariance normalization. Reference-refinement covariance retains its separate analytic normalization.

The reviewer independently observed the offending saved path and frozen predicate. At `run_once.py:229`, `local\checkpoints.jsonl` is compared to the POSIX literal `local/checkpoints.jsonl`; analogous later predicates occur at lines 231 and 272. The diagnostic source extracts only the saved-result validation block, checks prohibited call/name use, and does not call the supervisor or launch science. Its saved unchanged replay fails at line 229. Its separate in-memory control changes precisely those three path comparisons and completes the original validation block. Six protected identities match before/after. The reviewer read this diagnostic and its receipt, but did not rerun it. This supports the path-representation diagnosis, not retrospective acceptance or a new numerical result.

## Independent saved-data findings

All 49 frozen input identities, the executable, manifest and result identity matched. All 36 NPZ files (342109364 bytes), 30 checkpoint metadata records and linked logs matched their recorded identities. Each checkpoint's eight retained fields and coordinates matched its full-case snapshot exactly; initial J matched J0 and all saved J values were finite. The complete ordered logs contain 5630 direct solves, 5600 stages and 2800 steps, with the prescribed snapshot positions. Logged pivots, residuals, CFL, divergence, nonnegativity and ledger bounds agree with the stored summaries. This does not independently reconstruct unsaved intermediate flow states.

Using explicit 3x2 nodes, the reviewer independently reduced all 30 saved q circulation/moment/q-squared/impulse/vorticity-squared records and all 25 D8 polynomial comparisons. All agree within readback roundoff (rtol 3e-11, atol 3e-14); these matching tolerances do not replace scientific gates. Maximum D8 disagreement is .006007447209717373. Maximum logged residual is 1.7374625722690776e-14; CFL .07997729211069457; divergence 5.684341886080802e-15; ledger discrepancy 3.5433192415851367e-16.

The twenty already stored Gaussian numerator/denominator records reproduce their relative scores by scalar arithmetic. Coefficient, analytic full-space constants, reference denominators, model moment errors, point counts and rule-difference arithmetic agree. No Gaussian integral was independently reevaluated. At t=1, saved S256 vorticity error is .11619327199178484, centroid error .08269547822674578 and covariance error .10056910228577531. S128 gives .11616090595736346 and .10075853335898956 for vorticity/covariance. The stored model crosses the .10 vorticity and covariance gates only at the final sample; reference displacement is .35276936493470806. Maximum stored score-rule difference is 1.3877787807814457e-17. These corroborated observations remain unqualified under T60's failed receipt. The covariance excess is especially marginal; sensitivity is not a rigorous uncertainty bound.

Saved-array/log reduction took .7430422001052648 s; total including imports and identity checking was 1.2948631000472233 s. This reviewer code ran from stdin and was not retained as an independently reproducible script. It was saved-data verification, not independent method replication or a replacement qualification run. The author-owned path diagnostic is separately anchored below.

## Costs, limits and next task

One scientific child took 416.26116519991774 s and returned 0; final acceptance nevertheless failed. Observed peak working set was 2067156992 bytes across 1662 samples, below the 2 GiB observed stop, not a hard allocation certificate. The scientific history totals 1976.6796338998247 s, including prior failures. The numerical child includes both score rules and all six reference preparations; nested timers do not establish equal-work speedup.

Final documentation accurately distinguishes artifact completion, worker checks and failed aggregate acceptance. D8/five-sample limits, finite reference versus analytic model moments, empirical controls, researcher-defined task status and absence of a TOG contribution are retained. T61 selects only a separately frozen, one-child, 60-second standard-library saved-output qualification: constrained logical-path normalization, identity and original acceptance checks, no numerical arrays or science, and no T60 history rewrite. Its success is not presumed. No fitting/oracle or numerical follow-up is selected here.

## Sealed evidence identities

The input manifest anchors all 49 frozen inputs; the execution/result anchor retained artifacts. Final documentation and the read-only diagnostic are sealed here without repeating the full inventory. Hashes were generated directly from file bytes.

| Task-relative file | Bytes | SHA256 |
|---|---:|---|
| `input-manifest.json` | 10984 | `007dea68a26f3aeb476ac89db6990f7b06d0678ebf7a3d2fb987575277a39023` |
| `execution.json` | 22168 | `3eaf3d644c649ed26dc10d9a1f52546232b635a4e2c598ac47564c78197c727e` |
| `result.json` | 136401 | `8908fe090dd50c2c60291ffde31a52fb0e525063d9a66646462c6d3e6ba88954` |
| `local/readback_diagnosis.py` | 6799 | `7cee43ac58892d1cd87d3fbf3e5222d7b3e21cbe872670d28429bef878c05dcd` |
| `local/readback-diagnosis.json` | 3341 | `f32af7272918b376a7907f9b2ec39bfeeb47e74d37882c8f5f85f14b716f8918` |
| `README.md` | 1683 | `ec64c01e1a4761c99fe3006e2fb2b6d4e4c4d31a3f75e8a46c63a360652cb85f` |
| `RESULTS.md` | 7616 | `428d4961804028be610edca1782def1a42841fc8eee21dd3973c8e1a652c001d` |
| `DECISION.md` | 4335 | `39f5cbad6dc376b46b3249c108f89c412c19b3d216701747688bea9e0d8fd47f` |
