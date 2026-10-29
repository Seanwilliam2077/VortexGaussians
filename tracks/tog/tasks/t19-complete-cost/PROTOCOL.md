# T19: one fixed complete-cost comparison

29 October 2026. This records implementation choices before any T19 method execution or timing. The preceding goal turn made progress: T18 qualified all48 frozen rays and prepared the fair comparison, committed/pushed as `2bf97ad1e193ec6a3546f158e128b21f80993b78`. Repository/process inspection found a clean tree and no existing T19/qualification process. The active research goal continues; no heartbeat automation is recreated.

## Governing contract and immutable evidence

The full scientific/task contract is [T18 NEXT_EVIDENCE](../t18-reference-robustness/NEXT_EVIDENCE.md), SHA256 `e0c420eb663c09d4eb1ae041253c7561cd154227a3db23fe87dcf133c599aec2`. Its five arms, shared shortcuts, complete-cost requirements, accuracy criterion and decision rule are binding. This supplement does not revise them.

- Original48 inputs: T17 `inputs.json`, SHA256 `5cccf0238c679e14bc50e67d2d24726a58295b484b1d3464bf77d4eca0491cb7`.
- Saved high-accuracy truth: T18 `run-01/results.json`, SHA256 `fa4fb6887c6b38e800f18e919634821b3ee51c2fb0122cd0dbb4047eead7873d`, using its GL64 RGB only for post-timing evaluation.
- Five arm identifiers, in initial order: `simpson`, `gl`, `tail`, `simple`, `jensen`.
- Epsilons in order: `.001`, `.01`.
- Six passes: pass0 is first use, passes1–5 are warm. Each pass visits both epsilons and all48 fixtures in their original order. For pass p and zero-based fixture index f, rotate the arm list left by `(p+f)%5`. The two epsilons use the same defined rotation. Planned deliveries: `6*2*48*5 = 2880`.

All input groups and failures retain their original denominators. This is a development-input comparison, not held-out confirmation or a full3D renderer evaluation.

## Implementation and timing boundaries

`methods.py` owns common parameter preparation, exact/global-center recognition, tail truncation and pair shortcuts. `integrators.py` owns ordinary numerical integration and unit GL rule construction. `benchmark.py` owns supervision, immutable inputs, timing, validation and summary. Distinct owners review each other's interfaces; root and the independent reviewer inspect final code before the single invocation.

Every timed call is `deliver(arm, parameters, epsilon, cache, deadline_ns)`. The parameters contain only n, interval, means, widths, masses, RGB and background; no fixture ID, group, analytic-control tag, truth, previous output or stored decision. The harness builds immutable nested tuples outside timing as common parsed input, but all per-call working-array conversion, mass evaluation, actual recognition, sorting when needed, breakpoints, CDFs, bound work and fallback occur inside delivery. Method dispatch and return construction count too. Every arm has its own empty cache at run start, retaining **only unit-interval GL rules**; no per-ray data can survive a call.

Use `perf_counter_ns()` immediately before/after the delivered call. Truth lookup, finite/error validation, result formatting, hashing and file writes occur outside that interval and are separately part of whole-run time. No method receives oracle data. Store the actual method order and all 2880 individual durations/outputs/work counters if the invocation completes. A first-use batch is not discarded as warm-up.

Ordinary Simpson uses the T18 initial-sliver envelope and conservative rational budget allocation at requested budget `epsilon/4`, with the unchanged Gaussian-aware breakpoints and recursion/evaluation guards. The lean implementation may use `math.fsum` on empirical leaf estimates instead of retaining per-leaf Fraction/debug ledgers; initial omitted-emission charges remain explicit. It produces no numerical-certificate claim. The same implementation is shared by ordinary delivery and all fallback paths.

The GL arm constructs only required4/8/16/32/64 rules lazily within its timed calls, using scalar bounded Legendre/Newton iteration. Rule validity checks use moments0 through `min(12,2*n-1)`; requiring higher exact moments from GL4 would be an implementation error. Cache construction and checks are counted on first use. Consecutive refinements operate on the same Gaussian-aware original segments, with threshold `epsilon/4`; exhausted refinement invokes the same Simpson and retains all costs.

All other details are inherited: shared exact cases plus G/2 center delivery, direct retained-color tail delivery with background-inclusive deletion bound, simple/Jensen bounds for the original sorted color, correct channelwise early rejection, and no premature pair acceptance. Before execution, choose the same sensible evaluation-order optimization for both tail and pair arms: calculate their required masses/order/bound first, and defer actual RGB accumulation until acceptance; rejected work still counts before fallback. Per-primitive alpha from original clipped masses is needed only by pair arms and is computed only there; ordinary/common paths do not pay this candidate-specific preparation. Tail also receives safe early rejection once its nonnegative partial removed mass makes the deletion bound exceed epsilon; acceptance still requires all bins. The inherited contract specifies the delivered outputs rather than requiring unnecessary accumulation on rejection. No ordinary integration is charged an unnecessary sort or pair loop. No hierarchy, new scene, response cache, GPU kernel, package installation or source search belongs to this task.

Static review precedes all method execution. Mathematical work counters are summed, whereas state counters such as maximum recursion depth and final GL order are reported as extrema/distributions. Failed delivery records retain actual counters attached by the method; exception formatting occurs after its timer ends.

## Execution, failure and stored evidence

One supervised invocation with a300-second wall cap including worker startup and output; no numerical preflight or additional input run before it, and no repair/re-execution afterward. The default command is plan-only. Preserve source/protocol/input/reference identities before/after the process and incremental per-delivery records in an exclusive new directory. Capture stdout/stderr. Report import, input parsing, module/arm setup and worker/supervisor intervals separately without adding nested costs twice.

On the first method exception, nonfinite result, identity violation or color error above `epsilon+5e-10`, preserve the failing record and stop the invocation. Missing remaining deliveries are unexecuted, not successful or removed from the planned denominator. A native crash/timeout likewise preserves available partial output. Such an implementation/accuracy failure forbids a timing superiority conclusion and cannot be automatically reclassified as scientific falsification.

After a fully valid invocation, report first-use and each warm full-batch total for every arm, both epsilons, all groups and every case. Also report branch/fallback counts, actual integration/pair/CDF work, medians, spreads, absolute nanoseconds and ratios. No truth-selected successful subset or new precision target is permitted.

## Decision and scope

Use the sealed contract's stable-win definition: non-control N≥4; common exact/global-center paths did not solve it; the pair shortcut itself accepts in all recorded passes; then `max(5 candidate warm durations) < min(5 durations of each of the three ordinary arms)`. Shared-path/fallback fluctuations are not mechanism wins. Check complete batch costs separately. Same-process repeatability is not a confidence interval or hardware-independent result.

No stable eligible win closes this direct-shortcut opportunity on this fixed development scope, without claiming universal impossibility. A win only admits deciding whether it represents a useful task regime and whether related-work gaps can be resolved; it does not authorize manufacturing a favorable scene or automatic architecture expansion. The frozen source screen is not exhaustive and the ordinary optical-depth enclosure alternative remains relevant prior art.

All outcomes are evidence toward the unchanged SIGGRAPH/TOG goal. Numerical correctness, a sparse-only speed result or this finite benchmark alone is not the contribution or submission-ready end state.
