# T05 — proposed ordinary framewise cold start

2026-10-27; plan only, no execution yet. T04 demonstrated a qualifying joint solution through a paid warm start. Its T03+T04 exploratory cost is not the necessary cost of a strong ordinary baseline. This follow-up asks whether the same fixed76-constraint ordinary formulation can solve the same development target from zero, within the unchanged budget.

- Keep T04's full Objective, direct acceptance and force-check mathematics AST-identical:50 protection +25 edit +1 RMS, original mean edit objective/regularizer, original target/model/ROIs/gates, full6144 controls.
- The only optimization initialization change is x=0. Lambda=0, rho=1 and empty L-BFGS history, as already specified in T04. All forwards restart from original v0/rho0. Do not load any former accepted x/q or cached state.
- One120-rollout solve including zero initial validation, closures and returned-state validation; same reserve/rollback, three AL outer iterations and fixed L-BFGS parameters. One600-second fresh worker; no scan/retry/extra budget.
- Do not rerun G0. Before any new forward, authenticate T04's already passed76-constraint qualification record and its original source/core/input hashes; compare current Objective/acceptance/force-check AST and numerical configuration; independently recompute the stored central-FD scalar arithmetic and gates. Any mismatch rejects the run. This reuse verifies a prior qualification, not a new derivative experiment.
- Report current setup/authentication/solve/IO, calls and memory separately. State the pre-existing qualification as a development prerequisite, with its original cost available. Do not charge T03's failed initialization workflow to this baseline or call reused qualification zero historical effort.
- Success qualifies this ordinary cold-start baseline for this one development input and its observed cost. Failure remains a fixed-budget solver failure, not infeasibility (T04 already found a joint solution). One run is neither an independent holdout nor statistical speedup evidence.

Freeze the new source/protocol/input references and obtain independent source review before the single execution. Preserve complete local raw records and publish the same compact final-state/summary evidence. T04 remains untouched.
