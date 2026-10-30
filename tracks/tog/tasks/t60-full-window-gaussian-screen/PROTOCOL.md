# T60 — fixed full-window Gaussian screening experiment

The [T59 decision](../t59-direct-coupled-reference/DECISION.md) fixes the scientific question before this run. Does the ordinary complete-tangent Gaussian meet the original finite-time physical requirements under a qualified moving reference? A negative model result can be valid scientific evidence; it is not an execution failure and does not establish a new method.

## Schedule and inputs

One scientific child, <=600 seconds including imports, all setup, simulation, diagnostics, score integration and saving. No pilot, retry, installation, source search, fallback, factor cache, fitting, alternate coefficient or candidate method. Bundled Python 3.12.14/NumPy 2.3.5 is asserted before scientific functions.

Run six fresh trajectories from t=0 to 1, ordered S64/S128/S256/T128/D192/Q128. Grid/domain/dt/angular choices remain T59: (R,nr,nz,dt,angular) respectively (8,64,128,.0025,32), (8,128,256,.0025,32), (8,256,512,.0025,32), (8,128,256,.00125,32), (12,192,384,.0025,32), (8,128,256,.0025,64). Save exactly 0,.25,.5,.75,1. Complete counts are 2800 steps, 5600 transport stages, 5630 direct elliptic solves and 30 field snapshots.

Freeze all current formulation/protocol/source/measurement/supervisor/OS-preflight inputs; the relevant T54 coefficient result and receipts, T55 source/task, T56 reference contract/source, T57 memory/decision/failure, T58 direct solver/qualification, and T59 source/decision/results/receipts/review. Freeze the executable. Source and input bytes must match before/after; an exclusive start marker reserves the one invocation. No previous raw trajectory is reused as a new run.

## Reference qualification: twelve required categories

Preserve the ten T59 physical categories while extending their five-time evaluation; remove only the already-completed old-CG port regression:

1. Initial analytic u/J error each <=.01 for S64 and <=.005 for all other cases.
2. All stages finite/nonnegative, original reconstructed-face bounds, outgoing CFL <=.5, flux divergence <=1e-10, finite positive direct pivots and true original weighted residual <=1e-10 on every solve.
3. Core physical vorticity differences <=.01 for both space pairs and all three controls at every time.
4. Core velocity differences <=.02 for space pairs and <=.01 for controls.
5. Full-box absolute axial circulation-centroid discrepancies <=.01 initial width.
6. Full-box covariance discrepancies <=.01 initial analytic covariance norm.
7. Core nonzero-time spatial vorticity error reduction >=1.5 unless both pair errors <=1e-8.
8. Circulation/outflow ledger relative discrepancy <=1e-10.
9. Saved q-squared relative drift <=.02.
10. Saved axial-impulse relative drift <=.01.
11. D8 physical vorticity differences <=.01 for the same five pairs at all five times.
12. D8 nonzero-time spatial reduction >=1.5 unless both pair errors <=1e-8.

The five pairs are S64/S128, S128/S256, S128/T128, S128/D192 and S128/Q128. Physical field comparisons retain the second-field denominator, without alignment. Core and D8 are separately reported. Reference moments use each case's complete own box. Report D192 circulation and physical-vorticity-squared integral in D12 outside D8 and all existing shell diagnostics; no missing-tail bound is claimed.

Unsafe structural, runtime, positivity or original-residual errors stop immediately. Safe metric failures finish only the fixed reference schedule and remain failures. If any reference category fails, preserve the reference results and **skip Gaussian scoring**; the ordinary model verdict stays unqualified. Do not use failed reference quality to reject the carrier.

## Prespecified ordinary model and scoring

After reference qualification, score only the unchanged projected Gaussian q_G with c=1.5*T54.closed_metrics.beta_best_over_g0; fixed amplitude/width, no fitting or alignment. Perform fixed 8x6 primary and 16x12 confirmation quadrature at all five times against S256 and S128. Require absolute differences between the two relative physical-vorticity L2 scores <=1e-6 for all ten records. The primary 8x6 rule never changes. Record both rules' numerator/denominator, numerical D8 Gaussian Gamma/vorticity-squared mass, analytic all-space totals/fractions, point counts and costs. The mass differences are diagnostics, not an additional selected score gate.

Require the primary S256 axial circulation-centroid displacement from 0 to 1 >=.25 initial widths; otherwise report insufficient reference motion. A Gaussian score-integration failure or insufficient motion prevents a qualified model pass/fail verdict.

If reference, integration and motion qualify, require at every time: D8 world-coordinate physical-vorticity relative L2 <=.10 under the S256 denominator; absolute axial centroid error <=.1 initial widths; covariance Frobenius error <=.1 times the actual initial S256 reference covariance norm. Report S128 scores as resolution sensitivity, not a substitute primary. Retain Gamma, negative-vorticity mass and positivity validity. Finite-domain reference moments and analytic model moments are distinguished through D8/outside-D8 diagnostics.

The completed result distinguishes reference qualification, score-integration qualification, meaningful motion and ordinary-model pass/fail. Both qualified model success and qualified model failure return code 0, because either answers the experiment. Failed reference/integration or insufficient motion returns code 2 with no qualified model verdict. Structural/resource failure has only partial evidence. No outcome is a TOG-contribution verdict.

## Resources and preservation

One OS-only preflight and launch check require >=3 GiB available physical memory. The unchanged T57 observer samples lifetime peak working set every .25 s; stop above 2 GiB, at 600 seconds or on a live observer error. Report private/pagefile counters separately, observation intervals and any unavailable exit query. This is not an allocator cap or reserved memory.

The complete child counts all six Green matrix builds/applications, fresh direct factors/transforms, original residuals, reconstruction, transport, analytic initial checks, both measurement regions, coefficient loading, Gaussian evaluations, both score rules, diagnostics, checkpoint/full-array writes and final output. Nested timers are attribution only. Apply only the predeclared buffer-lifetime changes in FORMULATION; do not adapt memory behavior after the run starts. Save each actual snapshot before writing its completion/hash metadata; present but interrupted files are not validated checkpoints. Release K before final stacking and the next case.

Retain prior T56–T59 supervised child cost 1560.418468699907 seconds, including failures, and add this run for the cumulative sum. Earlier tasks retain their own receipts. The approximately 406-second extrapolation from T59 is only a budget heuristic; the 600-second ceiling and 2 GiB stop remain unchanged even if insufficient.

Every failure closes this task without automatic repair, changed dt/norms/thresholds, extra rule or rerun. A passing ordinary model indicates no demonstrated need for a new method on this case; a failing model under qualified conditions identifies only a specific approximation gap. Either requires a new evidence-based mechanism decision. Art inactive, main unchanged, automation deleted; full research goal remains active and unachieved.
