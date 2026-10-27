# T05 — ordinary framewise feasibility from zero controls

2026-10-27. Prepared after T04 found a joint answer on the fixed T02 development input. This is one ordinary cold-start solve, not an independent holdout, parameter search, new method, or statistical speed comparison. T03/T04 remain unchanged. Their exploratory optimization costs must not be presented as costs required by this cold-start baseline.

## Exact inherited mathematics

Use the same pinned R20 core, approved initial velocity/density/images, and authored T02 target/brief as T04. Float64 32³ MAC model, 40 steps, dt .025, camera and accepted frames16..40 unchanged. The full 6144 controls remain q=.5 tanh(x). The Objective, acceptance and force_stats ASTs must be identical to the qualified T04 runner before any GPU action.

The 76 PHR constraints remain ordered [50 protection,25 edit,1 coefficient RMS]. For each frame, tauP=min(.02 approvedROI_RMS,.005), tauE=min(.05 target_RMS,.01); constraints are MSE/tau²−1, followed by mean(q²)/.2²−1. The scalar objective remains mean normalized edit MSE +1e−4 mean((q/.2)²) +sum PHR, where PHR=(max(0,lambda+rho*c)²−lambda²)/(2rho). All constraints participate in loss, multiplier updates, rho tests and acceptance. No new weight or threshold.

## Unique initialization and fixed solve budget

Initialize x=0, all76 lambda=0, rho=1 and fresh L-BFGS history. Do not open T03/T04 optimizer x/q, final state, rendered answer or optimizer history. Every forward starts from original v0/rho0. The first zero-control full validation counts toward120 total solve forward calls. No warm-start branch or fallback is permitted.

Keep T04 numerical settings exactly: three outer iterations with20 returned L-BFGS steps each, rho growth10 up to100 when positive violation fails to halve; lr1, max_iter1, max_eval25, history10, tolerance_grad1e−9, tolerance_change1e−12, strong_wolfe. Reset history after an AL change. Count every initial, closure, line-search and returned-state validation forward. Reserve an acceptance call; interruption during line search restores the last accepted x and cached state. No best-trial selection, restart, extra budget or second run. The whole fresh worker has a600-second limit, including imports, authentication, solve, validation and IO.

## Reuse existing G0, before GPU access

No new G0 forward/backward is allowed. Pin T04 runner/config/freeze/result-summary/raw-run-manifest and the common core/input files. Verify the prior completed unchanged-source record, exact model/task/input numerical configuration, exact Objective/acceptance/force_stats AST, and original all76-active G0: independent random x=.12 Rademacher(seed2026102701), two RMS-one directions(seed2026102702), h1e−5/1e−6, lambda2/rho1, relative FD gate1e−4 with denominator floor1e−8. Configuration comparison excludes only the obsolete solve initialization; it does not open the old warm-start array.

`g0-proof.npz` is a compact **partial raw proof**: all25 non-frame arrays from the original11 G0 NPZ files (random x/q, gradient, directions, constraints, lambda, mask, rho). It contains no optimization arrays. Extraction checks original complete file SHA/size and every original array rawSHA, then omits nine full-frame arrays. `g0-proof.json` retains those original descriptors and the exact retained-key map. Repacking does not reproduce original NPZ file hashes; those originals remain in the sealed local T04 run.

At T05 startup, before importing Torch or querying/allocating a GPU, verify every retained rawSHA/dtype/shape and exact key set against the pinned T04 raw manifest. Recompose G0 scalar loss from saved q/constraints, and gradient-dot-direction from saved gradient/directions. Recompute central differences and apply the same1e−4 gate. Scalar record agreement uses abs1e−10/rel1e−12 only for CPU versus original GPU reduction order, not to relax the derivative gate. Also recheck the original recorded scalar FD arithmetic. This authenticates existing finite-difference/AD evidence; it is not a new forward, AD, image-to-constraint calculation or force evaluation. The omitted frame arrays were independently checked in the sealed T04 audit. A mismatch stops before GPU work.

After proof authentication, require the same actual Torch/NumPy/CUDA-build/dtype/thread/device/UUID environment as the qualified run, before the first rollout. Use the existing Python3.12/Torch2.11 environment, four CPU threads, RTX5070 Laptop UUID, child-only MKL SEQUENTIAL and local DLL policy. No package/environment changes.

## Acceptance, failure and retained evidence

Success requires every25 edit frames to meet relative RMS≤.05 AND absolute≤.01, every50 protection ROI/frames relative≤.02 AND absolute≤.005, reference RMS≥.01, finite x/q/images/final fields/constraints, density≥0, alpha in[0,1], coefficient max≤.5 and RMS≤.2, and expanded force maximum component≤.5. Mean objective alone is insufficient. T02 has no R22 two-pixel semantic gate.

Save every accepted x/q/full frames/76 constraints/lambda/rho, final velocity/density, closure and validation counts, rollback state, PHR group statistics and allocator memory. Complete raw logs/arrays remain in Git-ignored fresh `runs/run-01`; preserve failures and timeouts. Publish a compact summary, final arrays and hashes, without deleting the raw accepted history. Recheck all source/input pins afterward. A solver budget failure does not establish task infeasibility; successful execution is distinct from passing all task gates.

## Cost and scope

Report current startup (including proof authentication), solve/validation/IO, total worker/supervisor wall time and actual forward count. Report the inherited G0's9 forward/1 backward/5.7131403 seconds separately as an existing development prerequisite; zero new qualification calls are charged. Do not charge prior T03/T04 optimization to this ordinary cold solve or claim it was necessary. Their full discovery costs remain historical context. One development target, one run, and any timing difference provide no statistical speedup or generalization claim.

Default `python -I -B runner.py` only prints the plan. **Preparation is not execution authorization:** no freeze/run until root forwards the independent source-review clear and authorizes the GPU window. Then a source/input `freeze.json` permits the single `python -I -B runner.py --execute --out runs/run-01` bounded run. Existing output directories are rejected.
