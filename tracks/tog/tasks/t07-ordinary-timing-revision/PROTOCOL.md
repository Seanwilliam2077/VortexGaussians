# T07 — ordinary warm solve for the fixed T06 timing revision

Prepared 2026-10-27 before execution. This is the second authored edit in one development sequence. T06's timing was specified before T05's outcome and is immutable: keep the approved left plume through frame24, reach the common T02 endpoint at40, unchanged amplitude4, spatial rule, ROIs and image/control gates. It is a researcher-authored image target, not an externally approved creative requirement or known physical trajectory. No new cold-start or edit-only comparison arm is introduced.

## Fixed source, model and mathematics

T05 passed every original gate, so the predeclared source is its final accepted x. Authenticate the T05 final file/raw-x hashes, completed source summary, joint pass and recorded source cost. Read only x from that NPZ. Do not initialize from prior velocity/density/frames, multiplier, rho or optimizer history. Every forward starts from original approved v0/rho0, including the first warm-control validation. Lambda resets to0, rho to1, L-BFGS history is fresh.

The R20 Float64 32³ MAC core,40 steps,dt .025,camera,25 accepted frames16..40 and6144 controls q=.5 tanh(x) remain unchanged. Before GPU use, require Objective/acceptance/force_stats AST identity to the sealed T04 implementation. Only the target input and task identifier differ.

Ordered constraints are the original50 protection ROI/frames,25 edit frames,1 coefficient-RMS inequality. Let tauP=min(.02 approvedROI_RMS,.005), tauE=min(.05 target_RMS,.01). Each image constraint is MSE/tau²−1; the last is mean(q²)/.2²−1. The unchanged loss is mean normalized edit MSE +1e−4 mean((q/.2)²) +sum over76 PHR terms `(max(0,lambda+rho*c)²−lambda²)/(2rho)`. All76 entries govern objective, multiplier updates, violation tests and acceptance.

Keep three outer iterations,20 returned L-BFGS steps per outer, rho growth10 up to100 if positive violation fails to halve; lr1,max_iter1,max_eval25,history10,tolerance_grad1e−9,tolerance_change1e−12,strong_wolfe. Reset history after each AL change. No parameter or target search.

## New target-specific qualification and sole solve

Do not reuse T02's G0 for this changed target. Run the original fixed independent qualification point x=.12 Rademacher(seed2026102701), two RMS-one directions(seed2026102702), central h1e−5 and1e−6, qualification-only lambda2 on all76 entries and rho1. Nine full forwards and one backward. Require finite data, all76 analytic PHR branches active, and each `abs(FD−gradDot)/max(abs(gradDot),1e−8)`≤1e−4. Failure stops without changing the finite-difference step or tolerance.

After qualification, the first full warm-control acceptance costs one of at most120 solve forwards. If already jointly acceptable, stop without optimization. Otherwise count all closure/line-search/acceptance forward calls, reserve one validation call, and roll back to the last accepted x and cached results if the line-search budget expires. No best-trial substitution, restart, second initialization or budget extension. One fresh worker≤600 seconds includes imports, source checks, new G0, solve, force checks, validation and IO. Timeout or exception is preserved; no automatic retry.

Success still means every25 edit frames passes relative RMS≤.05 AND absolute≤.01 and every50 protection ROI/frames relative≤.02 AND absolute≤.005. Reference RMS≥.01; finite x/q/images/last fields/constraints; density≥0; alpha in[0,1]; coefficient max≤.5 and RMS≤.2; expanded force maximum component≤.5. Mean loss is not the stopping gate. T06 has no additional R22 two-pixel semantic condition.

## Cost, retention and interpretation

Record the source solution separately: T05 used84 solve calls and60.4012885 seconds solve wall,76.3454182 seconds whole worker. These are historical source-acquisition costs, not this revision's online latency. Record T07 new G0, closure, returned-state acceptance, force checks, IO, solve and complete worker/supervisor costs separately. Do not add T03/T04 exploration to the new edit's latency.

This implementation retains the reviewed independent acceptance-forward logic. Matching closure output could potentially be reused by an ordinary implementation; that optimization is not implemented or measured. Therefore do not call this the strongest possible ordinary solver or interpret apparent expense as evidence for a new cache without first addressing such ordinary redundancy. One execution is not a statistical performance comparison.

Save all qualification probes, accepted x/q/full frames/constraints/lambda/rho, final velocity/density, trial-versus-accepted records, rollback, PHR groups, source hashes and memory. Preserve the full fresh raw run under ignored `runs/run-01`; publish compact summary and recomputable final arrays without deleting raw history. Pin source/input before and after. The runtime is the same Python3.12/Torch2.11 CUDA build,4 CPU threads, pinned RTX5070 Laptop UUID and child-only local DLL/MKL policy.

A cheap qualified ordinary answer argues against specialized reuse for this fixed two-edit sequence. A slow or failed solve establishes neither infeasibility nor the benefit of any proposed method. No further authored variants are selected to manufacture difficulty.

Default `python -I -B runner.py` prints a plan only. Freeze and execute only after root accepts T05's independent audit and T07's independent source review, then authorizes one GPU window. Use a fresh output directory; never overwrite existing results or modify T05/T06.
