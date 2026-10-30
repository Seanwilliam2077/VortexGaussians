# T59 — next measure the original finite-time task against the ordinary Gaussian baseline

The short-window reference and solver port pass all eleven checks. This supports a concrete next measurement: **T60, the original [T55 physical task](../t55-axisymmetric-reference/TASK.md) through t=1**, with the already available ordinary complete-tangent Gaussian trajectory. It does not establish a new method, justify omitting the baseline or make the project submission-ready.

## One new full-window reference, no short pilot

Prepare and freeze six fresh-from-initial trajectories with exactly the T59 physical model, grids, dt, angular rules and case order: S64, S128, S256, T128, D192, Q128. Extend only the horizon to [0,1] and save 0,.25,.5,.75,1. This means 2800 steps, 5600 transport stages, 5630 elliptic solves and 30 saved snapshots. Do not splice a T59 checkpoint into the new conservation ledger or claim old work as a fresh run.

Reuse the same ordinary direct solver, true original residual check and current-q dense Green boundaries. Freeze and review the minimal wrapper/time/output changes before any execution. All factors and Green setup still count. Retain immediate checkpoint completion records and release K before final stacking; account for five snapshots and all later comparison buffers. Any further change to memory lifetime must be explicit and reviewed before freeze, not introduced during execution.

The original ten physical qualification categories retain their thresholds and definitions, evaluated at the five new times. Initial u/J thresholds remain .01 for S64 and .005 for the others; core vorticity disagreement <=.01, spatial velocity <=.02, control velocity <=.01, axial centroid <=.01 width, covariance <=.01 analytic initial norm, nonzero-time spatial vorticity reduction >=1.5 unless both <=1e-8, and the same positivity/face/CFL/divergence/true-residual/ledger/drift rules. T59 already validated the solver port; do not mechanically reuse its old T56 snapshot indices, whose times differ. No additional old-CG port category is selected for T60.

## Explicit measurement domain and score qualification

T59's field norms cover r<=4, |z|<=4. Preserve those core controls, but do not use them as unqualified all-space evidence for the full physical task. Add a separately reported common full computational box

    D8 = {0 <= r <= 8, -8 <= z <= 8}.

For every space/time/domain/angular pair, require reconstructed physical vorticity disagreement <=.01 on D8 at every new saved time, using the same second-field denominator and 3x2 piecewise-polynomial integration on the finer partition. Require the same nonzero-time spatial reduction condition on this full-box norm. Keep the old velocity thresholds; this new full-box vorticity gate does not rewrite historical qualifications. S256 is the prespecified primary reference; S128 supplies resolution sensitivity of the ordinary model's scores.

Full-box circulation-weighted axial centroid and covariance remain computed over each simulation's own domain. For D192 additionally report circulation and physical-vorticity-squared integral in D12 outside D8, plus the existing exterior-shell diagnostics. They expose finite-domain sensitivity but do not rigorously bound missing free-space solution error. The full-window conclusion must remain explicitly limited to D8, these controls and five samples; do not imply continuous-time supremum or unconditional whole-space accuracy.

Gaussian-to-piecewise-linear cross terms are not polynomials, so the old 3x2 exact-polynomial argument does not qualify their integration. Fix a tensor 8x6 Gauss rule per reference cell for the model's D8 vorticity score, with one prespecified 16x12 confirmation at every saved time for both S256 and S128. Require the absolute difference between the two reported relative L2 errors <=1e-6. The 8x6 rule remains the primary score regardless of output; a confirmation failure closes measurement qualification without substituting the other rule or retuning. These are empirical integration checks, not formal rounding/error certificates.

Compute the Gaussian's D8 circulation and vorticity-squared mass diagnostics with those same two fixed numerical rules, label them numerical and report their differences and fractions of the known all-space integrals. Do not describe numerical diagnostics as analytic values. Its all-space circulation and moments can be given analytically: Gamma=1.5*sqrt(2*pi), centroid=(sqrt(pi/2),c*t), covariance=diag((4-pi)/2,1), and squared physical-vorticity integral=(9/4)*pi^(3/2). Report the finite-domain limitation alongside those analytic full-space statistics.

## Ordinary comparator, fixed without fitting

Use the verified T54 closed coefficient, loading its frozen result rather than recomputing or fitting it:

    c = 1.5 * beta_best_over_g0
      = approximately .435464843161454,
    q_G(r,z,t) = 1.5 * exp(-(r*r + (z-c*t)^2)/2).

The actual speed is beta_star*a_z, not beta_star alone. [T57's decision](../t57-finer-short-reference/DECISION.md) explains why full-space translation equivariance of Euler and its complete-tangent L2 projection carries this ordinary optimum along the whole translated Gaussian trajectory. This is the full existing parameter-space projection for this symmetric isolated state, not a restricted center-only baseline, a reference-snapshot fit or an extrapolation of initial residual times duration.

Keep its amplitude, width and projected speed fixed. No alignment, fitting, new primitive, oracle correction or learned parameter is allowed. No center-update comparator or additional candidate trajectory is needed in this task. Its analytic parameter trajectory has no ODE stepping cost, but actual coefficient loading, field evaluation, quadrature, diagnostics and storage must all be reported; do not infer a fair real-time speed ratio against the reference qualification pipeline.

## Original physical decision gates

Only after all full-window reference and integration checks pass may the ordinary trajectory receive a qualified task verdict. Require primary-reference axial circulation-centroid displacement at t=1 >=.25 initial widths. Failure means insufficient motion for this researcher-defined task, not method failure.

Then apply the original screening requirements at every saved time:

- D8 world-coordinate relative physical-vorticity L2 error <=.10, with weight 2*pi*r³ for q and primary-reference denominator; no alignment.
- Absolute axial circulation-centroid error <=.1 initial widths.
- Circulation-weighted meridional covariance Frobenius error <=.1 times the **actual initial S256 reference covariance norm**. This original model-scoring denominator is distinct from the analytic normalization in the reference-refinement gates.

Report circulation, negative-vorticity mass and positivity validity. Reference and analytic-model moments use the definitions above, retaining finite-domain diagnostics. Report the S128 score alongside S256 at every time, especially near a decision threshold; observed convergence differences are not rigorous uncertainty intervals. A failed reference/integration gate prevents a validated model success/failure claim. Save the cause and existing evidence without fitting or extending the run.

If the ordinary projected Gaussian meets all gates, this single-carrier task has not demonstrated a need for a new method. If it fails under a qualified moving reference, it establishes a specific finite-time approximation gap; that still does not prove a useful novel repair or reject all Gaussian representations. Either outcome must guide a new mechanism decision, not automatically trigger another toy, tighter threshold, fit or scene.

## Fixed resource ceiling and stopping rule

Allow one new scientific child, **600 seconds total**, >=3 GiB available host memory at one OS-only preflight and launch, and the same 2 GiB observed lifetime peak-working-set stop with .25 s sampling. No pilots, retries, installs, new source batch, factor cache or fallback. Any numerical, score-integration, preservation or resource failure closes T60 without rerun. Safely evaluable metric failures remain failures; no post-output gate changes.

The ceiling has a concrete but non-guaranteed cost rationale. T59 took 242.8560308 s, including 188.3790832 s of Green setup. Keeping setup once and multiplying all other measured child work by four gives approximately 406.2868736 s; this deliberately also scales some output overhead more than the five-to-three snapshot increase. The 600 s ceiling leaves time for the explicitly added full-box and double-rule comparisons. It is a preparation heuristic, not a promised runtime or speedup.

T59 observed peak working set 2,056,495,104 bytes, only about 91 MB below the stop. Five saved fields and later output/score buffers can change that peak. The new task must accept a resource failure and retain valid checkpoints; the extra time margin is not memory capacity. Preserve all earlier costs, including T56/T57 failures: T56+T57+T58+T59 child time totals 1560.418468699907 s before any T60 execution.

This document selects preparation only; no T60 implementation or numerical run occurred in T59. Full research goal remains active and unachieved. Art stays inactive; main and the deleted automation remain unchanged.
