# T04 — proposed ordinary framewise feasibility check

2026-10-27. **Design review only; not frozen, implemented or executed.** T03 and its evidence remain unchanged. This follow-up is explicitly motivated by observed T03 results and is not an independent preregistered replication or a new optimization method.

## Why this one follow-up is defensible

An independent CPU read of T03's saved joint endpoint gives mean normalized edit MSE **0.5687342661235176**, while frames 39 and 40 have normalized MSE **1.132112441891724** and **1.4959404324629721**. Frame 38 is 0.9539266917461561. Thus an average objective below one does not imply all-frame acceptance. This is a concrete objective/acceptance mismatch, not proof of the cause of budget failure. T03 also failed one protection gate and stopped during line search; it remains a nonconvex, budget-limited solve.

The proposed correction makes the already declared edit requirements explicit inequalities. It does not modify the target, tolerances, control space, model, camera, regularization or numerical optimizer settings. Control max 0.3939053 and RMS 0.0289840 at the old endpoint do not approach the 0.5/0.2 limits, but unused parameter amplitude is not a proof of reachability.

## Fixed mathematical change

Use the exact T02 crop, approved images and initial fields already frozen by T03. For each edit frame t=16..40, define

`tauE[t] = min(.05 * RMS(target[t]), .01)`

`cE[t] = mean((image_edit[t] - target[t])**2) / tauE[t]**2 - 1`.

Keep the original 50 protection constraints and coefficient RMS constraint. The ordered constraint vector is **[50 protection, 25 edit, 1 RMS]**, length 76. All are enabled. Apply the same PHR formula to every entry:

`PHR(c, lambda, rho) = (max(0, lambda + rho*c)**2 - lambda**2) / (2*rho)`.

Keep the original mean normalized edit objective and `1e-4 * mean((q/.2)**2)` regularizer. Thus edit error is present as both a smooth mean objective and individual feasibility inequalities. This redundancy is declared, not tuned away. Final acceptance remains the original direct per-frame relative **and** absolute checks, plus signal/finite/nonnegative/control/actual-force gates; a small total loss never substitutes for them.

## Paid start, optimizer and stopping

Load only the saved `x` from T03's published joint-final.npz (SHA256 `9c9760fb50a07810aafd2f394d254e4a071e4cba71d8af394ece02921aad459c`). It is the last accepted point, not the last line-search trial. Reuse no forward state, image cache, multiplier, penalty or quasi-Newton history. Every rollout starts from the same original v0/rho0. Initialize all 76 multipliers to zero, rho to one, and a fresh L-BFGS history. Record this reset as a new formulation, not continuation of the old AL state.

The first full warm-control validation counts toward the **120-rollout** optimization budget. Retain R21's three outer iterations, 20 returned steps per outer, rho growth 10 up to 100, violation reduction factor .5, all L-BFGS settings, acceptance reservation and rollback. Initial, closure, line-search and accepted-state forwards all count. If a line search would consume its reserved validation slot, restore the last accepted x and its corresponding records. No second start, parameter scan, best-checkpoint selection or extra iteration after budget exhaustion.

One new whole worker has a **600-second** limit including imports, qualification, validation, solve and IO. A derivative failure, numerical failure, timeout or fixed budget failure ends this one follow-up. It is not followed by altered finite differences, penalties or budgets to rescue the result.

## New scalar gradient qualification

Before optimization, qualify the actual 76-constraint scalar loss at the original fixed nonzero random point, **not** at a control selected for favorable optimization behavior. Use x=.12 Rademacher(seed 2026102701), two RMS-one Rademacher directions(seed 2026102702), h=1e−5 and 1e−6, qualification-only lambda=2 for all 76 entries and rho=1. Nine forward calls and one backward call. Require finite outputs/derivatives, positive actual margins on every PHR branch, and all `abs(FD−gradientDot)/max(abs(gradientDot),1e−8) <= 1e−4`. No gate change if it fails.

Source review must verify the 50/25/1 ordering in the loss, lambda/rho update and logging; the first 25 edit inequalities must agree with the unchanged image acceptance formula. The loaded warm x is authenticated by raw/file SHA. Recompute q with the same Torch `.5*tanh(x)`; do not invert saved q or demand NumPy/Torch transcendental bitwise identity. A CPU check of the old x/q pair differs by at most 5.55e−17, consistent with this backend distinction rather than a new tolerance on image gates.

## Evidence, cost and conclusions

Preserve every accepted x/q/full image/constraint/AL record, final velocity/density, full qualification arrays, failure logs and source/input fingerprints. Publish compact summaries and final arrays; preserve the complete local run separately. The report distinguishes trial points from accepted points and identifies failing frame/ROI gates.

Mandatory warm-start dependency cost is the prior **119 T03 joint rollouts and 86.6583043 seconds**, plus new qualification and all new solve/setup/IO costs. Report these components without double counting; this partial dependency subtotal excludes the earlier shared qualification and setup. For total chronological exploration cost, additionally show the full T03 worker's **187 rollouts** (9 G0 + 59 edit-only + 119 joint) and **157.7731068 seconds**, followed by all T04 cost. This is neither cold-start performance nor a T03 speedup/success.

- If all original gates pass, this establishes a jointly feasible answer found by this paid ordinary-solver path for this one development target.
- It cannot isolate whether improvement came from extra budget, explicit edit inequalities, the warm start or their combination; no matched-budget causal claim is justified.
- If it fails, the conclusion is only that this fixed ordinary configuration did not find a qualifying solution within its budget. It is not proof of infeasibility or a failure of constrained optimization in general.
- Even success would not establish a new method, a reusable response model, artist usefulness or a TOG-level contribution. It would resolve the immediate task-feasibility uncertainty before any such claim.

**Recommendation:** permit this one fixed ordinary feasibility follow-up after source/protocol review; stop it at its original gates and budget. Its motivation is concrete, while its interpretive scope remains deliberately narrow.
