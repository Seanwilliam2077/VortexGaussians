# T08 — ordinary returned-evaluation reuse

Prepared 2026-10-27 before execution. One implementation check on the exact T07/T06 development task, not a new optimizer, response surrogate, statistical speedup experiment or rescue of a failed task. T07 already passed. No T07 or earlier file changes.

## Unchanged mathematical problem

Use the fixed T06 target, approved v0/rho0, T05 final x only, Float64 32³/40-step MAC core, camera, frames16–40 and 6144 controls q=.5*tanh(x). Every rollout restarts from original v0/rho0. Reset lambda=0, rho=1 and L-BFGS history. Objective, acceptance and expanded-force functions must be AST-identical to T07 and T04. Keep the same ordered 50 protection +25 edit +1 RMS inequalities, mean normalized edit objective, 1e−4 regularizer, PHR formula, AL and strong-Wolfe L-BFGS parameters. No target, tolerance, step or budget search.

All 25 edit frames must satisfy relative RMS≤.05 and absolute RMS≤.01; all 50 protection ROI/frames relative≤.02 and absolute≤.005. Reference RMS≥.01, finite data, density≥0, alpha in[0,1], q maximum≤.5, q RMS≤.2 and expanded force component≤.5 remain required. Mean objective is not acceptance. T06 has no R22 two-pixel semantic gate.

## The sole implementation change

After each successful closure forward/backward with finite loss and gradient, retain only the latest x and frames/final velocity/final density via detached clones. No autograd graph, gradient, loss, constraints, multipliers or old PHR value is cached. A returned x may reuse those outputs only when dtype/shape/device match and contiguous uint8 views are equal, distinguishing +0 from −0, and the fixed model/input identity matches. Identity includes pinned core/model/task/input hashes plus tensor identity, shape, dtype, device and in-place mutation version for immutable model attributes and v0/rho0/approved/target inputs. Optimizer x and derived q mutation versions are excluded; x is checked separately by bytes. Detect changes during the closure as well as at lookup. No code uses `.data` to mutate fixed tensors.

On a hit, recompute acceptance, force checks and PHR under current lambda/rho from the returned x and saved forward outputs. Any miss executes and pays for a complete real forward. Initial warm acceptance always executes a real forward. Invalidate the closure cache on AL/history change and budget rollback. Rollback preserves only the last accepted x and its outputs; no line-search trial becomes accepted.

On every normal termination, execute one additional real forward at the last accepted x. Apply all original gates and compare frames, velocity, density and constraints to the saved accepted results by dtype/shape and raw byte equality. Save both accepted final and independent final-verification arrays, including raw hashes and descriptors. Mismatch is a recorded failure, never silently replaced by verification output. Exceptions/timeouts preserve failure and do not retry or claim final verification.

## Budget and costs

At most120 real solve forwards, including initial acceptance, every closure, acceptance misses and final verification. Before a closure reserve two slots: one possible returned-point miss and one mandatory final forward. This conservative reservation can stop earlier than T07 near the budget; report it rather than asserting trajectories must match. Hits do not consume a forward. Count every backward separately. Three outer iterations and20 returned steps per outer remain unchanged.

One fresh worker≤600 seconds includes imports, authentication, solve, cache handling, acceptance, final validation and IO. No automatic retry. Record closure total (cache clone time nested within it), cache hit/miss lookup and acceptance/force time, acceptance real-forward time, final real-forward/gate time, total solve wall, worker wall, memory and maximum cache payload. Optimizer-step time nests closure time; do not add it again. IO is included in solve wall, not claimed as independently timed. Report real forward and backward counts separately. T07's 68 backward calls are the relevant expected-work comparison if accepted trajectories agree; T08 does not execute T07's new G0, so whole-worker wall comparisons do not establish speedup.

## Reused qualification and CPU preflight

Before Torch import or GPU use, authenticate T07 completed G0, original source/config/core/input hashes and exact mathematical AST. Its nine forwards/one backward are a separate historical prerequisite. Recompute the scalar PHR and directional FD arithmetic from the compact proof's25 non-frame arrays (q,76 constraints, analytic gradient,directions) with the original FD gate1e−4; no new AD or forward. The proof was extracted only after verifying all11 original G0 NPZ files and raw-array hashes. Nine frame arrays are omitted; this is not an independent image-to-constraint or force re-evaluation. Authenticate runtime versions/device against the qualified run after initialization.

Only new cache-risk CPU tests are added: exact hit, wrong x, signed-zero miss, input/model version miss, detached-clone isolation/no graph, invalidation/rollback and final-slot reservation. The pre-byte-review test record remains separate; freeze the final current-source passing test. No smoke-model fitting or GPU preflight experiment is run.

Freeze source, protocol, configuration, cache helper/test, compact G0 proof, relevant original manifests, core and inputs after independent review. Execute only after root authorizes the sole GPU window. Preserve all accepted/raw outputs under ignored `runs/run-01`; publish compact final arrays and summary. Independent post-audit compares every accepted x/q/frames against T07 and explains any miss or trace difference. Agreement only demonstrates removal of redundant evaluations for this execution, not a new optimization method or protection-response cache benefit.
