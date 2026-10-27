# What ordinary editing currently costs

27 October 2026. These are observed costs on one developed 32³ passive-smoke input. They are not production latency, repeated timing estimates or a speed ranking between different solver formulations and starting points.

## Qualified ordinary cold start

[T05](tasks/t05-framewise-cold-start/README.md) reaches all 25 editing and 50 protection checks from x=0, using the same 76-constraint objective qualified in T04. It uses 26 returned steps and 84 complete model rollouts. [Independent saved-array review](../validation/t05-review.md) verifies the zero start, final accepted state and original gates. The source is the published `result-summary.json`, SHA256 `2883db0d4651a0c2d7388061c3f5918a68cc155eea1ee5ec36cf10f780d0aa5c`.

| Measured component | Count | Synchronized seconds |
|---|---:|---:|
| Objective/gradient closures | 57 | 46.8482 |
| Additional accepted-state forward evaluations | 27 | 11.4205 |
| Complete solve, including accepted-state evidence IO and driver work | 84 model rollouts | 60.4013 |
| Complete worker, including imports, initialization and prior-G0 authentication | Same 84 new model rollouts | 76.3454 |

Closure plus acceptance time is contained in solve time, which is contained in worker time. Do not add these overlapping totals. T03/T04 development cost is a historical research expense, not the cold-start solve time. T05 authenticates the previously paid 9-forward G0 and does not execute a new G0.

## A stronger ordinary implementation may remove redundant work

In the present driver, every returned L-BFGS step triggers another complete forward rollout, even if its parameter vector is exactly the same as one just evaluated by a closure. That independent acceptance pass helps audit the prototype, but it is not intrinsically required by constrained optimization. The 11.4205 seconds above includes the necessary initial forward and quality/force calculations; it is **not** a measured removable-cost estimate.

A standard implementation may retain detached closure outputs and use them for acceptance only when the returned x and all model/input identities match exactly. It must fall back to a real forward on a miss, invalidate after model/input changes, avoid retaining autograd graphs, preserve rollback, and retain real final verification. This optimization has not been implemented or timed here. Before a positive candidate-speed claim, remove or fairly match this ordinary overhead and evidence-IO policy. T07 keeps the existing driver for a bounded negative screen; if even that workflow is cheap, a dedicated mechanism has less opportunity.

## Why protection reuse does not automatically save differentiation

The actual objective combines editing, protection and force terms after **one** `model.rollout`; `value.backward()` differentiates their scalar sum. Protection has no separate full-trajectory backward pass in this implementation. The model must still advance and render to evaluate the edit. Replacing only the protection response therefore does not automatically remove a full forward/backward operation.

A useful reuse mechanism would need to reduce whole trajectory evaluations, failed line searches or repair iterations enough to pay for construction, refresh and true verification. The earlier R20 response construction took 53.764 seconds on its own exploratory workload; it is a warning about setup cost, not the price or a formal break-even point of an unimplemented T07 method.

## The next decision

T06 fixes a second image edit with a delayed onset and the same final bend. T07 will allow the qualified T05 control, run the unchanged ordinary mathematics with fresh solver state, and report the new qualification, initial validation, closure and acceptance costs separately. No new cache is being built.

If the ordinary revision is cheap, close this two-edit sequence as evidence against investing in a dedicated protection-response cache for it. If it is costly or fails, first inspect whether the cause is the edit, the protection constraints, the control representation or ordinary driver overhead. An unresolved numerical example is not evidence of a TOG mechanism. A genuine creative workflow and comparisons to applicable existing methods are still required.
