# T70 — ordinary causal evaluator and two first steps

The single frozen run qualifies the ordinary current-state evaluator and both first-step projections. All eight numerical categories pass; the supervisor accepts the complete record as **completed_ordinary_current_state_evaluator_and_first_steps_qualified**. This establishes a usable ordinary startup from exact q0. It does not establish a new method or the original t=1 physical task.

## What was measured

Both h=1/16 and h=1/32 begin independently at the same exact q0. Prediction uses only that current mixture and its computed velocity; no endpoint, future moment or reference array is loaded. A fixed anisotropic scalar fixture checks the evaluator only. The [protocol](PROTOCOL.md) and [manifest](input-manifest.json) were frozen after [static review](../../../validation/t70-causal-projector-review.md), without a pilot. There was one child and no retry.

The selected tuples each contain two positive, distinct active components. The second geometry is approximately (sr,sz,z)=(.95,.725,.6), with weight .03372738185 for h=1/16 and .01685946415 for h=1/32. The first component stays at (1,1,0). The bounded search chooses these states; no global optimum is certified.

| h | Unchanged q0 error | T54 translation error | Selected error | Circulation change | Impulse change |
|---|---:|---:|---:|---:|---:|
| 0.0625 | 2.058290% | 0.731923% | 0.517850% | -0.050116% | -0.378793% |
| 0.03125 | 1.029308% | 0.365689% | 0.258966% | -0.025058% | -0.189397% |

Errors are relative to each **current-state Euler target q0+hF(q0)**, using the fixed D12/(64,128)/heat128 primary route. They are not errors against a true solution. The selected target error is about 29% lower than the ordinary translation control. Halving h also halves the target residual here; this does **not** establish time-integration convergence because both experiments start at q0 and use different linearized targets. The scale/impulse drift is real and remains unconstrained in this ordinary comparator.

## Qualification and cost

Initial radial closed-form/T54 calibration, full ordered self/cross contractions, seven independent scalar controls, both prescribed searches, unchanged-tuple direct residual checks, moments, counters and identities all pass. Maximum absolute self/cross discrepancy is 3.73035e-14; maximum absolute selected/control confirmation discrepancy is 3.93314e-14. Fixed heat, spatial and box controls agree under their predeclared gates. These are empirical binary64 checks, not rigorous error/tail certificates.

Each search completes 1035 bank pairs plus 396 neighbor proposals, with four starts and 33 complete polls: 1431 proposals, 1360 evaluations, 71 cache hits and no box rejection. Together there are 2862 proposals, 416 component bases, 7560 weight attempts plus two unchanged controls. Sixteen candidate geometries retain floating-point classification flags; neither selected candidate is flagged. The complete journal has 3455 records.

Total counted work includes 30 field calls, 71,582,784 component heat-point visits, 452 cross calls/479 ordered integrals/62,656 heat-cross nodes, 8628 Gram calls and 732 direct reductions over 9,744,384 point visits. Direct target norms and confirmations are included. Five shared rules use 736 nodes and five eigensolves. No array is read or saved.

The complete supervised child takes **1.098377400 seconds**, including imports, setup, controls, both fits, readback hashes and output; observed peak working set is **59285504 bytes**. The supervisor wall interval, including that child and standard-library journal/scalar validation, is 1.311527900 seconds before receipt writing; these two timings are not additive. This is one local cost observation, not a rendering-speed claim or guaranteed rollout estimate. The recorded T56/T57/T58/T59/T60/T63/T65/T66/T68/T70 scientific-child subtotal becomes **1991.4691072998103 seconds**, not total project cost; T61's separate qualification remains separate.

## Reproducible record and limits

- [Result](result.json), [scalar summary](evidence.json), [execution receipt](execution.json), [input manifest](input-manifest.json), [OS preflight](preflight.json).
- [Physics](physics.py), [bounded search](search.py), [worker](measure.py), [supervisor](run_once.py), [preparation](prepare.py).
- [Lossless journal](journal.jsonl.gz), [memory log](memory.jsonl), [export mapping and hashes](exports.json), [review](../../../validation/t70-causal-projector-review.md).

Execution receipts name their original ignored local/ output paths. Public copies preserve their exact bytes; exports.json maps them, and the journal is losslessly compressed from 5,998,924 to 631,361 bytes. Empty stdout/stderr are retained. This records the completed invocation; do not delete the exclusive marker to rerun it. A portable replication needs a new declared run record and matching runtime, without overwriting this evidence.

[Next T71](DECISION.md) addresses causal continuation and original physical scores over the full time interval. No multi-step trajectory, time-sensitivity qualification, external creator demand, new mechanism or TOG core contribution follows yet. T68's endpoint witness, T63's inconclusive search, T60's failure and T61's separate qualification remain unchanged. Art is inactive, main untouched and automation remains deleted; the research goal is active.
