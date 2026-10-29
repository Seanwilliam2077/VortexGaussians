# T32 — ordinary entry stops at the reference cell cap

Completed 30 October 2026; one invocation, no retry. **The fixed-subset qualification failed.** The result is an identified reference-qualification obstruction, not an ordinary renderer accuracy failure, a rendering bottleneck or a TOG contribution.

## What was attempted

[The frozen protocol](PROTOCOL.md) uses the two immutable T31 authored Gaussian fields, three existing cameras, and at most 336 geometry-selected pixels. It compares an ordinary sphere-BVH / Gaussian-aware Gauss–Legendre (GL) entry with an independently projected, analytic-mass radiance enclosure. The output tolerance is 0.001 per RGB channel and alpha. This particular protocol additionally requires the reference midpoint half-width to be at most 0.0001. No original field, camera, density, color or sampling rule was adjusted after observing results.

The single supervised invocation took 1.3827239 seconds, including 0.9825742 seconds of worker computation before packaging. It completed 16 empty-retained reference rays in the first frame/view. The 17th ray, frame 90 / front / pixel (132, 73), exhausted the per-ray reference budget. No frame/view group completed; no later frame/view ran. The first constructed schedule contains 56 pixels; 336 is the protocol maximum, not the number evaluated.

## The retained failure

| Quantity at the failed ray | Saved value |
|---|---:|
| Original components / ordinary BVH retained / reference retained | 270 / 34 / 28 |
| Full-field analytic alpha | 0.1959615658668975 |
| Reference created cells / current leaves | 8,191 / 4,166 |
| Completed bisections / initial cells | 4,025 / 141 |
| Reference red midpoint half-width | 0.0003317207355572338 |
| Reference green / blue half-width | 0.00007603933595447948 / 0.00001073370175794057 |
| Required reference half-width | 0.0001 |
| Ordinary red / green / blue | 0.18927751611345842 / 0.043074561765932266 / 0.006092713879154582 |
| Largest ordinary distance to a saved interval endpoint | approximately 0.000334382 |
| Final output tolerance | 0.001 |
| Largest reference omission radius | approximately 1.26e-13 |

Another bisection would create two cells and exceed the frozen 8,192-created-cell cap. The worker stopped there. The saved interval is red [0.1889484565651139, 0.18961189803622833], green [0.042999098820666555, 0.043151177492575514], blue [0.006082059173744056, 0.006103526577259937]. Omission uncertainty is negligible relative to these widths. The failure diagnostics retain all 4,166 leaves, all-source optical weights and masses, and both outputs; no further subdivision or integration was performed to improve them.

GL4 and GL8 differed by only about 1.67e-14 in red, but that empirical agreement is not a sufficient accuracy guarantee. The saved interval would already fit the **final** 0.001 endpoint-distance requirement. Nevertheless, the additional reference-precision gate failed, the worker never reached this ray's qualification stage, and the full subset and coverage gates remain unevaluated. We do not retroactively pass T32 or count this ray among its 16 completed records. Binary64 erf/exp and interval arithmetic are not directed rounding; neither the stored intervals nor saved-data review constitute a formal floating-point certificate.

## Evidence and cost scope

- [Freeze](freeze.json): ten source/input/review identities checked before and after execution, including the unchanged T22 GL source. [Pre-execution review](../../../validation/t32-pre-execution-review.md) disclosed the earlier, pre-result reference-radius choice.
- [Attempt reservation](run-01/attempt.json), [supervisor receipt](run-01/execution.json), [worker receipt](run-01/result.json) and [lossless full results](run-01/results.json.gz). The full 1,054,391-byte JSON is preserved in 374,592 bytes of gzip; no failed record was dropped.
- [Independent saved-result review](../../../validation/t32-saved-result-review.md) and [machine audit](../../../validation/t32-saved-result-audit.json) check saved identities and arithmetic without rerunning projection, quadrature or reference construction.

The invocation made 17 ordinary calls (16 computed-zero paths), 2,052 GL evaluations and two GL rule builds. Reference accounting records 701,116 CDF endpoint calls and 479,719 exp-family calls. These are named implementation counters, not all arithmetic operations. The failed ray's ordinary integration took 0.0512807 seconds and preparation 0.0004718 seconds in this single qualification process, with no repeats and shared rule cache. These numbers are not full-frame latency, a stable performance comparison or a GPU result. Failed reference work remains included in complete invocation time.

## Decision

Seal this failed invocation. The evidence points first to an unnecessary auxiliary precision requirement in this verification task, rather than requiring a new rendering method. [The stopping-contract analysis](STOPPING_CONTRACT.md) establishes why the same independent intervals can directly decide the unchanged output tolerance. [The next finite task](NEXT_EVIDENCE.md) is a separately reviewed and frozen qualification using that rule on the identical fields and geometric subset. It does not change T32, add samples, increase budgets or start a cost benchmark. A tighter density/color envelope is not mandatory merely because it can be derived.

T31 remains a qualified authored input, with its explicitly new continuous-field convention and unvalidated creative relevance. T28's trained-carrier route and T29/T30's specified method routes remain closed. No core method, strong full-renderer comparison or multi-scene paper evidence has been established.
