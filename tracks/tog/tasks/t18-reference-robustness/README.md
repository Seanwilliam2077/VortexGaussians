# T18: reference robustness passes on the unchanged 48 rays

29 October 2026. **All 48 cases now pass the inherited numerical qualification, including the seven whose T17 Simpson references failed.** This single T18 invocation accounts explicitly for ten initially unresolvable segments; it does not change the input, scientific bound, comparison thresholds or downstream attenuation. T17 remains recorded as incomplete, with both original attempts preserved. This is a repaired correctness prerequisite, not a new rendering contribution or performance result.

## What changed, and what did not

The [pre-execution protocol](PROTOCOL.md) fixes the new reference's sole adjustment. When an original segment's midpoint/quarter points collide with endpoints in binary64, omit only that segment's emission and charge the conservative upper bound `(r-l)*sum_i(w_i/sd_i)` to the original `1e-11` budget. Exact rational arithmetic on the stored floats and directed conversion prevent this accounting from spending more than the budget. The integrand and background continue to use all original extinction.

The remaining budget is distributed conservatively across other original segments. Later recursive resolution failures still fail; no new rescue branch was added. The real-arithmetic envelope applies only to the omitted contribution. The rest of adaptive Simpson and analytic Gaussian evaluation still use empirical floating-point arithmetic: **there is no complete numerical certificate**.

[qualification.py](qualification.py) imports the pinned T17 module and replaces only its in-memory `adaptive_simpson` binding. Inputs, pair formulas, ordered color, GL32/64 construction/evaluation, controls and scientific checks are inherited. Five source/input identities were checked before and after execution. Two agents reviewed the protocol/code independently of implementation; the saved-data reviewer did not rerun integration. No historical file was edited.

## Actual execution and results

One invocation; no retry. [Execution](run-01/execution.json) reports exit0 and no timeout. [Full results](run-01/results.json) include all48 cases, original pair quantities, both GL references, adaptive results and exact/rounded budget ledgers. [Progress](run-01/progress.jsonl), [GL rules](run-01/quadrature-rules.json) and captured logs are retained. The4.68MB result contains all duplicate per-case checkpoint records; the duplicates remain local and ignored.

| Measure | Result |
|---|---:|
| Cases numerically qualified | 48/48 |
| Cases needing the declared segment treatment | 7 |
| Charged initial segments | 10 |
| Largest charge on any one ray | 3.996803e-15 |
| Sum of charges across all rays (separate budgets) | 1.717376e-14 |
| Largest combined returned error estimate | 4.061909e-12 |
| Largest reference disagreement | 7.671641e-14 |
| Largest analytical-control discrepancy | 2.553513e-14 |
| Largest observed bound excess | 5.440093e-15 |

The original comparison allowances remain5e-10 for reference/analytic agreement and1e-9 for bound excess. Every exact charge/allocation account and returned-error budget passes. These empirical checks support the implementation on this set; they do not prove the reference's floating-point accuracy for arbitrary inputs.

| Previously failed case | Charged segments | Total ray charge |
|---|---:|---:|
| `control-05-equal-color` | 2 | 2.664535e-15 |
| `structured-03-n4-span1.2` | 1 | 1.998401e-15 |
| `structured-07-n8-span1.2` | 1 | 1.998401e-15 |
| `structured-11-n16-span1.2` | 1 | 1.998401e-15 |
| `structured-12-n16-span3` | 2 | 3.996803e-15 |
| `structured-15-n32-span1.2` | 1 | 1.998401e-15 |
| `clipping-06` | 2 | 2.518818e-15 |

The informative-bound count is **unchanged**: all28 non-control cases with N≥4 now qualify, but only `structured-04-n4-span3` meets the predetermined global-versus-pair criterion at either .001 or .01. The simple bound also accepts that case. Jensen contributes no additional accepted case; dense/opaque limitations from T17 remain. The five newly qualified eligible cases do not supply additional evidence of a useful region.

## Recorded costs and scope

T18 worker time is4.203987 seconds; supervisor time is5.322885 seconds. Worker timing starts after NumPy import and ends before aggregate JSON writing; supervisor timing includes startup/output. The adaptive reference performs83,182 evaluations, GL32 performs31,616, and GL64 performs63,232, for178,030 total. Summed reference times are1.811677, .707062 and1.389258 seconds respectively; they are nested inside worker/supervisor time and must not be counted again.

This is cumulatively the **third** full-qualification invocation across T17/T18. Both T17 supervisors plus T18 total15.236309 seconds; the four retained T17 initialization diagnostics add8.350454 seconds, giving23.586763 seconds of identified execution intervals. Untimed input generation, prior environment probes, development/review effort and whole research wall time are excluded, not assumed zero. No cost advantage follows from these qualification timings, and the extra rational accounting is not a candidate renderer feature.

No package installation, web search, source-family expansion, new input, scene/asset, renderer or GPU work occurred in T18. Art and original demo/model files remain unchanged. The active research goal continues; the previously deleted hourly automation remains deleted.

## Decision and reproduction

The corrected numerical prerequisite is satisfied on this development set. The next task is the separately fixed [complete-cost screen](NEXT_EVIDENCE.md), which has **not run** here. It must compare delivered colors using identical information, include ordinary analytical/global-range/tail-truncation alternatives and account for all candidate work plus fallback. No scene expansion or contribution claim follows automatically from a sparse witness.

[Independent saved-data review](../../../validation/t18-array-review.md) checks exact budget arithmetic, original source identities, scientific gates and unchanged GL/pair quantities. `audit-manifest.json` identifies the published evidence. The full goal still lacks novelty clearance, an ordinary-method limitation at useful cost, scene/task evidence and a submission-ready method.

```sh
# Plan only; no numerical execution:
python -I -B -X utf8 tracks/tog/tasks/t18-reference-robustness/qualification.py

# Reproduction command; use a fresh directory and preserve historical results.
# This documentation does not authorize another attempt in the completed T18 task.
python -I -B -X utf8 tracks/tog/tasks/t18-reference-robustness/qualification.py run --input tracks/tog/tasks/t17-order-inversion-bound/inputs.json --out NEW_DIRECTORY
```

The fixed sibling T17 source, protocol and input are required. No default execution, input-generation command or automatic repair loop is provided.
