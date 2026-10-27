# T04 — same-task post-hoc ordinary solver revision

2026-10-27, fixed before this execution. This is **同一任务的事后普通求解器修订**. It is not a new task, independent preregistered replication, new method or cold-start comparison. T03 is unchanged and remains a budget-limited failure to find a joint answer. The scientific motivation and limitations are recorded in PROPOSAL.md.

## Unchanged task and sole formulation change

Use byte-pinned T02 target-edit.npy/brief, approved.npz (v0/rho0/frames), and the portable R20 core. Float64 32³ MAC model, 40 steps, dt=.025, same camera and frames16..40, full 6144-dimensional q=.5 tanh(x). All original ROI, signal, image and control gates stay unchanged. Target reachability remains unknown; no target/parameter search.

Let tauP=min(.02*approvedROIRMS,.005), tauE=min(.05*targetROIRMS,.01). The **ordered 76-vector** is:

1. Original 50 protection inequalities, mean(error²)/tauP²−1, ROI0 frames16..40 then ROI1 frames16..40.
2. New 25 edit inequalities, mean(error²)/tauE²−1, frames16..40.
3. Original coefficient RMS inequality, mean(q²)/.2²−1.

All 76 constraints use the ordinary PHR `(max(0,lambda+rho*c)**2-lambda**2)/(2*rho)`. Keep the original mean over normalized edit MSEs **and** 1e−4 mean((q/.2)²) regularizer. Edit error occurs both in the objective and feasibility inequalities; this is declared, not a tuned weight. Loss, lambda update, rho violation test, G0 and records all use this same ordering. Direct per-frame acceptance remains authoritative.

## Paid warm start and fixed budgets

Load **only x** from the byte-pinned T03 joint-final.npz, the last accepted point, not its last trial. Every new forward recomputes the trajectory from original v0/rho0. No previous velocity, density, rendered frames, multiplier, rho or optimizer history is used to advance or initialize the solve. All 76 multipliers reset to zero, rho to one, and L-BFGS starts fresh. First warm-control full validation counts toward the new 120-rollout budget.

Same R21 numerical settings: three outer iterations, 20 returned L-BFGS steps per outer, rho growth10 up to100 if maximum positive violation fails to halve; lr1, max_iter1, max_eval25, history10, tolerance_grad1e−9, tolerance_change1e−12, strong_wolfe. Reset history after changing AL multipliers/rho. All initial/closure/line-search/validation forward calls count. Reserve one validation call; a budget interruption during line search rolls back to the last accepted x and corresponding cached results. No restart, best-checkpoint selection or extra step. One fresh worker, at most600 seconds including startup, authentication, G0, optimization and IO. A failure ends this follow-up without continuing a same-target search.

## Mandatory new scalar derivative qualification

The full new 76-constraint objective must pass before optimization. Fixed x=.12 Rademacher(seed2026102701), two RMS-one Rademacher directions(seed2026102702), central h1e−5 and1e−6, qualification-only lambda2 on all76 entries and rho1. This is the original nonzero qualification point, not the selected warm solution. Nine forward calls and **one backward**. All quantities finite; every actual PHR branch margin positive; every relative derivative discrepancy `abs(FD−gradDot)/max(abs(gradDot),1e−8)` ≤1e−4. No adjustment if failed. G0 is separate from the120 optimization calls but included in600 seconds and all cumulative costs.

## Unchanged final gates and records

At every independently evaluated accepted state, all25 edit frames satisfy relative RMS≤.05 **and** absolute RMS≤.01; all50 protection ROI/frames satisfy relative≤.02 **and** absolute≤.005. Reference RMS must be≥.01. Also require finite x/q/images/last fields/constraints, density≥0, alpha in[0,1], coefficient max≤.5 and RMS≤.2, expanded force max-component≤.5. Mean loss below one is not success. T02 has no R22 two-pixel semantic gate.

Save complete G0 arrays, every accepted x/q/fullframes/76constraints/lambda/rho, final velocity/density and all trial/acceptance counts. Store protected/edit/RMS PHR groups separately. Raw runs remain in Git-ignored `runs/`, never deleted to reduce publication size. Compact summary, final arrays and their hashes are public. Source/input pins before/after execution; any mismatch, nonfinite result, exception or timeout remains an explicit failure. No retry. The worker uses the existing Python3.12/Torch2.11 CUDA environment, four CPU threads and the same declared RTX5070 Laptop UUID; local DLL/MKL policy is inherited from the reviewed T03 supervisor. No package changes.

## Cost and permissible inference

Report T03 joint's **119 calls /86.6583043s**, then all new G0/solve/setup/IO. This warm dependency subtotal omits older shared setup/qualification and must be labeled partial. Also report full chronological exploration: T03 **187 rollouts /157.7731068s worker** (9G0+59edit-only+119joint), followed by T04. Times are observed sequential costs, not a cold-start or isolated formulation speedup. Do not relabel T03 as successful.

Success establishes one qualifying joint solution found by this paid ordinary-solver path. Extra budget, warm start and the new inequalities all changed; success cannot isolate the mean-versus-framewise issue as T03's sole cause. Failure establishes only that this fixed revised solver did not find a solution in budget, not infeasibility. Neither outcome is a new-method or TOG contribution claim.

Default `python -I -B runner.py` plans only. After source review and freeze, `python -I -B runner.py --execute --out runs/run-01` performs the one bounded run. Existing output paths are rejected.
