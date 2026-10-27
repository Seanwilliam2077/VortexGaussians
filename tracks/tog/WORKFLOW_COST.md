# What ordinary editing currently costs

27 October 2026. These are observed costs on one developed 32³ passive-smoke input. They are not production latency, repeated timing estimates or a speed ranking between different solver formulations and starting points.

The [subsequent workflow review](ORDINARY_WORKFLOW_DECISION.md) also limits what these costs mean: T02/T06's target generator already constructs the fixed-view alpha images by ordinary 2D warping and ROI compositing. T05–T08 establish feasibility and cost inside the specified 3D control model, not that a creator needs that model. An actual fixed-view delivery must allow an applicable image workflow as a baseline; changing viewpoint alone may call for volume deformation rather than fluid re-simulation. No such external workflow has been executed or timed here.

## Qualified ordinary cold start

[T05](tasks/t05-framewise-cold-start/README.md) reaches all 25 editing and 50 protection checks from x=0, using the same 76-constraint objective qualified in T04. It uses 26 returned steps and 84 complete model rollouts. [Independent saved-array review](../validation/t05-review.md) verifies the zero start, final accepted state and original gates. The source is the published `result-summary.json`, SHA256 `2883db0d4651a0c2d7388061c3f5918a68cc155eea1ee5ec36cf10f780d0aa5c`.

| Measured component | Count | Synchronized seconds |
|---|---:|---:|
| Objective/gradient closures | 57 | 46.8482 |
| Additional accepted-state forward evaluations | 27 | 11.4205 |
| Complete solve, including accepted-state evidence IO and driver work | 84 model rollouts | 60.4013 |
| Complete worker, including imports, initialization and prior-G0 authentication | Same 84 new model rollouts | 76.3454 |

Closure plus acceptance time is contained in solve time, which is contained in worker time. Do not add these overlapping totals. T03/T04 development cost is a historical research expense, not the cold-start solve time. T05 authenticates the previously paid 9-forward G0 and does not execute a new G0.

## Removing redundant ordinary work

In the T05/T07 driver, every returned L-BFGS step triggers another complete forward rollout, even if its parameter vector is exactly the same as one just evaluated by a closure. That independent acceptance pass helps audit the prototype, but it is not intrinsically required by constrained optimization. The 11.4205 seconds above includes the necessary initial forward and quality/force calculations; it is **not** a measured removable-cost estimate.

T08 implements detached closure-output reuse for acceptance only when returned x is byte-exact and model/input identities match. It falls back to a real forward on a miss, invalidates on input or solver-state changes, retains no autograd graph, preserves rollback, and pays for a final real verification. The result below establishes actual work reduction on T07's task. Any future candidate comparison must include this ordinary improvement and fairly match evidence-IO policy.

## Why protection reuse does not automatically save differentiation

The actual objective combines editing, protection and force terms after **one** `model.rollout`; `value.backward()` differentiates their scalar sum. Protection has no separate full-trajectory backward pass in this implementation. The model must still advance and render to evaluate the edit. Replacing only the protection response therefore does not automatically remove a full forward/backward operation.

A useful reuse mechanism would need to reduce whole trajectory evaluations, failed line searches or repair iterations enough to pay for construction, refresh and true verification. The earlier R20 response construction took 53.764 seconds on its own exploratory workload; it is a warning about setup cost, not the price or a formal break-even point of an unimplemented T07 method.

The published `acceptedHistory` also limits the bottleneck story. In T05, editing first passes at returned step25 while protection fails, followed by joint success at26. In T07, editing first passes at32, which is also joint success; **none of its33 accepted states passes editing while failing protection**. Protection does matter along the T07 path (39/68 closures have active protected branches), but the record has no accepted-state tail devoted solely to repairing protection after a finished edit. These observations do not isolate causality or show that removing protection would be free. They do prevent presenting71 seconds as measured protection-only repair time.

## The next decision

T06 fixes a second image edit with a delayed onset and the same final bend. T07 used qualified T05 control and the unchanged ordinary mathematics with fresh solver state. It passed all original gates in101 solve rollouts:68 closures and33 acceptance forwards,71.1901 solve seconds (55.0382 closure and13.6883 acceptance seconds contained within it). New G0 used9 forwards/1backward and4.3911 seconds; whole worker91.5085 seconds. These values are independently audited in [T07 review](../validation/t07-review.md). T05 and T07 have different targets, so their times do not establish a warm-start speedup.

T08 completed one frozen run on exactly the T07 input, starting control and mathematics. It uses **70 real forwards =68 closures +1 initial +1 final verification**, with68 backward calls and32 cache hits/0 misses. The32 removed acceptance forwards are offset by one extra final verification: **31 fewer net forwards**, with unchanged returned-step and backward counts. All25 editing and50 protection gates pass. Unchanged derivative qualification is authenticated from T07 rather than rerun.

| Observed T08 component | Seconds |
|---|---:|
| Complete solve, including evidence IO and final verification |59.8928993|
| Closures, including0.0164432 s cache cloning |55.9859960|
| Acceptance, including initial forward and force checks |0.9577334|
| Extra final verification |0.4191882|
| Whole worker, including prior-G0 authentication |75.9206307|

These subtotals overlap and are not to be added to solve time. The single observed solve pair is71.1901340→59.8928993 seconds; it is not a repeated statistical speed estimate. Whole-worker times are not a matched speed comparison because T07 includes new G0 execution. Maximum retained cache payload is1,916,928 bytes, not a full-process memory measurement.

[Independent post-audit](../validation/t08-post-audit.md) confirms T08's final state and extra real forward are byte-identical. Across33 T07/T08 accepted states, only the initial x/q/frames are byte-identical;96 later arrays differ, with maximum absolute differences x2.889e-11, q1.444e-11 and frames1.121e-11. Their cause was not isolated; do not claim exact cross-run trajectory equivalence. All original gates still pass without adjusting tolerances. No protection-response model, approximation or new algorithm is involved.

Close this two-edit development sequence without investing in a dedicated protection-response cache for it. The experiment has removed an ordinary confound but has not established a production bottleneck, a user latency requirement or a distinct mechanism. The next input is [an actual sourced creative revision](CREATIVE_TASK_PACKET.md), followed by comparison to an applicable ordinary workflow. More toy targets or tighter invented gates would not resolve the missing evidence.
