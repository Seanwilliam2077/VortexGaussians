# T33 — one visible mixed-color ray qualifies; the subset remains incomplete

Completed 30 October 2026. **T33 failed at a reference per-ray cell cap.** This is the second cumulative authored-entry qualification, with one invocation in each of T32 and T33 and no retries. T32 remains failed under its own frozen rules.

## Result under the frozen contract

[T33's protocol](PROTOCOL.md) changed only the reference stopping requirement: directly check the fixed ordinary output against both independent interval endpoints at absolute tolerance0.001, instead of also demanding a0.0001 reference midpoint radius. It retained the T31 fields, geometric selection, ordinary BVH/GL entry, interval construction and all other gates/budgets. [Static review](../../../validation/t33-pre-execution-review.md) and [freeze](freeze.json) precede the run.

The sole supervised invocation took2.5327363 seconds; worker computation before packaging took2.0843771 seconds. Seventeen rays completed: the same16 computationally blank rays plus one nontrivial mixed-color ray. The next ray stopped unresolved. Only the first56-pixel schedule was constructed; zero of six groups completed. The336-ray maximum is not an evaluated sample count.

| Saved result | First visible ray, qualified | Next ray, unresolved |
|---|---:|---:|
| Frame / view / pixel | 90 / front / (132,73) | 90 / front / (130,77) |
| Full-field analytic alpha | 0.1959615658668975 | 0.35546431745556567 |
| Ordinary output red | 0.18927751611345842 | 0.360990986154835 |
| Ordinary GL order | 8 | 8 |
| Reference retained components | 28 | 57 |
| Reference created cells | 2,701 | 8,192 |
| Red reference half-width | 0.0009765609695761568 | 0.0011017391378658759 |
| Largest endpoint distance | 0.0009974283275828444 | 0.0011098267905199077 |
| Alpha distance to ordinary | 2.3229251577827625e-9 | approximately1.22e-8 |

The first visible ray satisfies every geometry, omission, leaf-ledger, output/alpha/range check and the mixed-color criterion in this invocation. Its ordinary output is identical to T32's saved value, but T33 constructs and checks its own reference interval. This is one qualified nontrivial development ray, not a retrospective T32 pass or a qualified image/subset.

## What the failure tells us

The failed ray's saved red interval is [0.35989733466962315,0.3621008129453549]. Its half-width exceeds0.001 even before considering where the ordinary answer lies. Consequently **no scalar output, including the exact true value, could satisfy the endpoint test against this particular interval**. The current interval is too broad to decide the requested accuracy. It contains the GL output and has no disjoint channels; the saved decision is `unresolved`, not `output_disproved`.

The reference used286 initial cells and3,953 bisections, reaching8,192 created cells and4,239 current leaves. The global cell total10,893 and computation deadline were not exhausted. Reference omission radius is at most4.21e-13, far below the unresolved width. GL4/8 agreement around1.4e-14 and proximity to the interval midpoint remain empirical observations, not true-error evidence.

Thus removing T32's auxiliary precision requirement was sufficient for the first visible ray, but insufficient for the full subset. This is a concrete limit of the current reference construction under the fixed budget. It does not demonstrate ordinary rendering inaccuracy, unachievable tolerance, useful renderer latency or a candidate-method advantage. The next decision must address the source of interval slack, rather than increase the cell limit or select different rays.

## Retained evidence and accounting

- [Attempt](run-01/attempt.json), [execution](run-01/execution.json), [worker receipt](run-01/result.json) and [full results](run-01/results.json.gz):1,371,474 bytes of raw JSON retained in497,390-byte lossless gzip, including both visible rays and the failed4,239-leaf partition.
- [Independent saved-result review](../../../validation/t33-saved-result-review.md) and [machine audit](../../../validation/t33-saved-result-audit.json) check identities and stored arithmetic without new projection, CDF/exp, integration or method execution.
- All13 frozen identities match before and after execution. No launch/cleanup error, timeout, retry, new asset, capture, installation, browser/GPU run or source search occurred.

The invocation made18 ordinary calls,16 computed-zero paths,5,664 GL evaluations, two GL rule builds and two hits. Reference counters record1,657,516 CDF endpoint calls and1,111,844 exp-family calls. The failed reference stage took1.4805898 seconds and its ordinary integration0.1472574 seconds in this single process. These are named implementation counts and qualification-stage timings, not stable speed comparisons or complete rendered-frame cost. The actual numerical envelopes are binary64 evaluations of real-arithmetic formulas, without directed rounding or a formal floating-point certificate.

[The next evidence decision](NEXT_EVIDENCE.md) must preserve this failure and the entire previous history. T31 remains an authored continuous-field input with unvalidated physical/creative relevance. Strong full-renderer comparisons, genuinely distinct scenes and a core TOG contribution remain missing.
