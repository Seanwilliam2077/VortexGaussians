# T59 coupled-reference source and saved-data review

**Verdict: no unresolved blocker.** The saved evidence supports `completed_qualified_short_reference_only` for the frozen [0,.25] contract: six new trajectories, 700 steps, 1400 transport stages, 1418 direct solves, 18 validated checkpoints and all eleven predicates pass. T56 remains failed and T57 remains timed out. This qualifies the ordinary short reference and solver port on the tested region/controls; it does not establish independent replication, unrestricted free-space accuracy, t=1 performance, candidate advantage or a TOG contribution.

## Provenance and pre-run review

I retain earlier T48–T58 collaboration context and participated before this run. I read T58 DECISION, the original T56 equations/metrics and the actual new formulation, protocol, source, supervisor, OS probe and freezer. Another agent authored the implementation; root owned the protocol/execution. Before freeze I identified the source's freeze.json/input-manifest.json mismatch and the risk of counting merely present, interrupted case JSONs as complete; root independently found and corrected both. I read back these fixes, the runtime assertion and failure-record guard before reporting no blocker. They preceded the only scientific invocation and changed no numerical gate.

After completion, one authorized NumPy readback loaded existing arrays and independently reduced fields/moments, reconstructed derivatives and applied the original assembled stencil. I did not import task/base/solver modules, execute FFT/DST/Thomas/CG, rebuild Green matrices or advance a flow. Explicit fixed 3x2 Gauss nodes/weights were used without regenerating a rule. Array/log work took .5035089999437332 s; imports/hashing/reductions to before printing took .9133640000363812 s. These are separate review costs, not another scientific run or a benchmark. Only this review was written; publication remains root-owned.

## Source invariance and stopping contract

The in-memory Poisson binding is the sole numerical replacement in the unchanged imported T56/T55 routines. The case wrapper preserves both SSPRK2 updates, positivity/face/CFL checks and stage-specific current-q Green boundaries. Every T58 direct call rebuilds factors, then an independent assembled original FV matrix/RHS checks the W-weighted RHS-relative residual <=1e-10. No transformed residual or fictitious CG iteration count substitutes for it.

Field comparisons retain the original common core, common finer partition, q-vorticity weight 2*pi*r^3, velocity weight 2*pi*r and second-field denominators. Full-box axial centroid/covariance and their analytic reference-refinement normalization remain unchanged. Port regression uses compare(new,old), preserving the old T56 denominator; it is distinct from the q-squared invariant norm. All ten original categories plus port regression are present.

Each checkpoint NPZ closes before its metadata/hash is written and completion is logged. The supervisor parses and verifies checkpoint/case metadata and raw identities before counting completion. Partial files and terminal-failure records cannot qualify the task. K is released after final dependent work and before final stacking/save, with no returned reference to it. One exclusive invocation, 600 s and the observed 2 GiB stop apply without retry/fallback; all setup and output count.

## Saved evidence and independent reductions

All **40 frozen input identities** and the executable match. Manifest/freeze/start receipts, source identities, result, all linked logs/metadata and raw identities also match independent hashing. The reviewed manifest, execution and result hashes below anchor the complete per-file identity lists; they are not duplicated here. The start marker intentionally has zero children before Popen, and the final receipt one. Six case JSONs equal result entries, and the checkpoint ledger has the exact per-case start/kernel/three snapshots/completion sequence.

All **24 NPZs** were loaded with allow_pickle=False: six complete cases and eighteen checkpoints. Checkpoint fields and coordinates match the corresponding complete-case slices bit-for-bit; checkpoint statistics/current records agree. All eighteen saved u/J reconstructions match exactly, including the six initial J0 fields. Shapes, coordinates and finite/nonnegative q are valid.

The six complete step-log sequences reproduce 700 steps, 1400 stages and 1418 solves. Every logged solve has the direct method, fresh factors, positive pivots and a passing original residual; all reported stage/step bounds, maxima, operation counts and phase sums agree. Intermediate q is not stored at every step, so I checked those logged assertions/source rather than claiming to reproduce transport. Checkpoint masses were separately checked against cumulative logged boundary outflow and pass the ledger tolerance.

The audit recomputed **18 full-box moment sets, 15 physical comparisons and six port comparisons**. Circulation, centroid/covariance, q-squared, impulse, physical-vorticity-squared integrals and drifts agree. Relative 3e-11/absolute 3e-14 readback tolerance handles summation and near-zero cancellation; it does not replace scientific thresholds. All eleven scientific predicates were separately evaluated at their frozen thresholds and remain true.

At t=.25, coarse/fine vorticity discrepancies are .00434755971345098 and .0011194294771802431. Nonzero-time reductions agree with 3.9192799246041163 and 3.8837280972823303 without waiver. Port maxima are 3.4959035202887957e-12 for physical vorticity and 2.2131697312249624e-10 for velocity, below 1e-7. Initial u/J norms recomputed against the saved fixed oracle arrays also pass; the oracle was not rerun.

Applying the original assembled stencil to the **18 saved** phi/q/boundary states gives maximum residual **1.685766565029655e-14**. The **1418 logged** solve states have maximum **1.720283167461335e-14**; these maxima cover different sets. Maximum CFL is .07997729211069457, q-squared drift .0005312557010599406 and impulse drift .00017068032280320722. S256 at .25 has centroid_z=.0883807114632788 and covariance_rz=-.0184854969456449; these are short-window observations, not a t=1 motion verdict or model score.

## Cost and resource evidence

The child returned 0 in **242.85603079991415 s**. Internal before-result time is 242.45010559994262 s; supervisor before-receipt time is 243.6079251000192 s. The preserved prior cost 1317.5624378999928 s gives **1560.418468699907 s** through T59. Older history remains separately charged. Per-case timers end before case JSON writes and solver subphase timers overlap outer timers; whole child time is authoritative.

Independent record sums give Green construction 188.37908320012502 s, boundary applications 28.40512139745988 s and internal checked-direct work 8.582220498588867 s. All 1418 factor/transform/residual calls are charged. Six grids contain 311296 cells, with 8343519232 scalar kernel pairs. The 24 ignored NPZs total **217263132 B**. These different work sets do not support an equal-work speedup claim or imply a new method.

Preflight/launch available memory is 27415478272/27396128768 B, above 3 GiB. All 970 memory observations are valid and ordered. Maximum observed lifetime working set is **2056495104 B**, below **2147483648 B**; sampled private maximum is 1976680448 B and peak pagefile 2037846016 B. Private/commit are diagnostic, not additional gates. The last successful query is at 242.85524760000408 s, with no query error. This is observed headroom with sampling/exit-tail limits, not an allocator cap or future-memory guarantee. Case/checkpoint validation-error lists and failure-record list are empty.

## Final decision check

README/RESULTS correctly limit qualification to this window, region and controls. T60 remains separately prepared: six fresh trajectories, five samples, 2800 steps/5600 stages/5630 solves. Its additional D8 vorticity/refinement gates and fixed 8x6 versus 16x12 score confirmation do not rewrite historical controls. Reference moments remain full-box; the model shape gate uses the actual initial S256 covariance norm, distinct from the analytic refinement normalization. The integration rule cannot be switched after output.

Hand checking q_G=1.5*exp(-(r^2+(z-c*t)^2)/2) gives circulation 1.5*sqrt(2*pi), centroid (sqrt(pi/2),c*t), covariance diag((4-pi)/2,1), and 3D physical-vorticity-squared integral (9/4)*pi^(3/2). The stated speed c=1.5*beta_best_over_g0=beta_star*a_z retains amplitude correctly. Numerical D8 diagnostics are distinguished from analytic all-space moments; outside-D8 measurements do not prove tail bounds.

The K+4*(child-K) runtime estimate is labelled a heuristic, with future setup/score costs and limited memory margin retained. Any failed reference/integration gate prevents a qualified model verdict. Passing the ordinary Gaussian would demonstrate no need for a new method on this task; failure would establish only a specific approximation gap. No new toy, fitting, threshold tightening, repair or TOG-success claim follows automatically. No T60 implementation or numerical run was performed in this review.

## Final reviewed task identities

These 13 task-file identities were generated from their actual final bytes. Later publication metadata/audit-manifest and root publication helpers are not claimed in this review. This report's own identity is reported separately.

| File | Bytes | SHA256 |
|---|---:|---|
| `.gitignore` | 7 | `a7d8bdcefba82a95ebc021d87c629fdea21f13af953bf01e28b7cf8b0eeceb41` |
| `FORMULATION.md` | 3275 | `c680766e71f8b59cb436d2a0b7a6ade51d1dbc7f1f7ccca66fc47c0df2a4a52f` |
| `PROTOCOL.md` | 5897 | `d5b7d45c31cfed0e0f7ef1cbbd2b061a7b8d470783baa5eadaf304afff4dcc07` |
| `reference.py` | 23596 | `341003961d69eaab70578b04d8ab55fa82aff7c0cb066f8e3a8c9395edf803a1` |
| `run_once.py` | 11930 | `7eea711efe99adeb4e95b9ca2dffa7dba4c349af8b002523bc0941ebf96cdbf5` |
| `resource_preflight.py` | 1589 | `d15bcbd4fa41b9e31608b94313d01a9cd8360b4b9ee65be874575e4e1b49ef47` |
| `resource-preflight.json` | 906 | `41b19a0a07e979d4ef6a80df63c4b8cf26e88c60b0af3e9a21d8cbf173861c21` |
| `input-manifest.json` | 9135 | `b1d67d1b5ee3a7e0bc4da2989fb0f3c885b5f106e43196247ccdc080ad7d8ff6` |
| `execution.json` | 15732 | `fec3ad0d7795cff5d79531cfe127f10653bd3eb78412621d90d3cbd9701d7f6d` |
| `result.json` | 58706 | `87085827f56a34a19e688fc8d05e467f0d3996ed93484e0cac049ae75fc159c6` |
| `RESULTS.md` | 8530 | `340360a34b340a2752464e00ad1e062bde98bb874cc5bf1d57c8f11f23f4afd7` |
| `DECISION.md` | 9352 | `9c628d2e047aea964fee9941e2dbfa03abed689fc6586653d66e8478429f2806` |
| `README.md` | 1627 | `46ff07bf7c4bcb4cde9f7f0bc759b016f508de8dbdb6e7d271f2147f7c697145` |


The review accepts only the recorded short-reference qualification. Full-time physical performance, broader tasks, a useful new mechanism and publication contribution remain unresolved.
