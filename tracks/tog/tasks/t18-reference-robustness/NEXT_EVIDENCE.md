# T19 preparation: complete cost of accurate RGB delivery on the fixed rays

29 October 2026, after T18's one invocation qualified all48 original rays. **This comparison has not executed.** T17 remains incomplete; T18 supplies a corrected empirical reference on the same development data, not a new dataset or independent confirmation. The one informative sparse case and dense-case limitations remain unchanged.

## Question, scope and fixed budget

Does either direct pair-bound shortcut reduce the total cost of delivering an accurate color relative to equally informed ordinary methods, once common shortcuts, preparation and fallback are included? The output is an approximation to the same continuous colored self-emission integral within absolute maximum-channel error epsilon. It is **not** a requirement to return the original sorted-compositor color or to evaluate a certificate for that particular color.

The next task, T19, may implement and statically review the methods below, then make **one** supervised invocation, capped at300 seconds, with no repair/re-execution allowance. Use exactly the existing48 input records and epsilons `(.001,.01)`; no resampling, changed scene, added ray, new source query/family, installation or GPU work. T18's saved GL64 color is the high-accuracy evaluation reference; comparison and output serialization stay outside timing. No new expensive reference integration is needed. Every delivered color from every recorded pass is checked, not just the best timing or one selected case.

The contract starts from the already defined one-dimensional ray parameters. Report file parsing/import and solver setup separately and include all per-ray mathematical preparation in delivery time. This is not a complete3D renderer benchmark: ray/scene transformation, acceleration structures, learning, frame coherence and production data are absent. Python timings cannot establish hardware-independent algorithmic efficiency or novelty.

## Common information and shortcuts

All arms receive identical means, widths, full masses, clipping interval, linear colors and background, and may derive identical analytic cumulative extinction and breakpoints. They must not read stored reference colors, actual errors, acceptance lists or fixture IDs when choosing a branch. No generated target or oracle acceptance is an input to a method.

All arms first use the same cheap, parameter-recognized cases: vacuum/zero mass; identical colors; and identical normalized Gaussian profiles (exact equality of means and widths, with the optical-mass-weighted color). Recognize these from input values, not the control names. The resulting analytical RGB is a delivered result. Charge recognition, masses and arithmetic to every arm that uses them.

All arms also get a global enclosure **center** shortcut. With `Q=1-exp(-sum tau_i)` and componentwise color extrema, return

```text
L_center = Q*(c_min+c_max)/2 + T(b)*background
```

when `max(Q*(c_max-c_min)/2)<=epsilon`. Its bound is half the global range; an ordinary method must not be forced to test the weaker bound for a preselected sorted output. Parameter parsing into working arrays, all masses, extrema and any sorting still count where required. Do not sort an ordinary arm that does not need sorting.

## Five fixed arms after common shortcuts

1. **Ordinary adaptive Simpson.** Integrate the continuous target with total nominal absolute budget `epsilon/4`, including the T18 initial-segment accounting, original recursion guard, depth24 and200,000-evaluation limit. The scientific comparison is at the requested epsilon, not T17's unnecessarily tight1e-11 qualification budget. The empirical estimate does not imply a numerical certificate.
2. **Ordinary refined Gauss–Legendre.** Use the common original breakpoints. Evaluate GL4 then GL8; accept the higher-order result when their maximum-channel difference is at most `epsilon/4`. Otherwise continue through16,32,64 with the same consecutive-rule criterion. If no refinement agrees, use the same Simpson fallback and charge all prior work. Standard scalar Legendre/Newton construction avoids the already diagnosed NumPy initialization path. Pre-review the fixed rule construction and its moment checks; no outcome-driven order tuning. The refinement criterion is empirical and every final color still faces the external accuracy check.
3. **Ordinary disjoint-bin truncation, then Simpson.** Sort means; set fixed adjacent-mean midpoint boundaries, with unbounded outer bins intersected with the original clipping interval. Empty bins, including tied means, are allowed. Integrate each Gaussian's retained optical mass in its own ordered bin and composite those disjoint pieces exactly. Let `R` be removed total optical mass. The channel bound for delivering this retained color directly is `(1-exp(-R))*range(component colors plus background)`. If its maximum is within epsilon, return the retained color; otherwise use Simpson. Do not add a penalty for its difference from the original sorted color: that would unfairly constrain the ordinary method's output. Charge its sorting, CDFs, bound and discarded work on fallback.
4. **Simple pair bound, then Simpson.** Compute the original full sorted color and simple color-weighted reversal bound from T17. Return that color only when the componentwise bound's maximum is within epsilon; otherwise deliver Simpson's color and include all prior cost.
5. **Jensen pair bound, then Simpson.** As arm4 with the fixed Jensen saturation. There is no new pair formula, hierarchy, split, tile reuse or cached response model.

Pair work may use the evident nonnegative-sum early **rejection**: reject only once some channel has `min(G[channel],partial_pair_sum[channel])>epsilon`. Testing only the maximum partial sum can be wrong when the corresponding channel's global cap is already small. Never accept before all necessary nonzero-contrast pairs have been bounded. Skipping exactly zero terms is allowed and must be reflected in separate visited-pair/CDF counters. Use the same implementation conveniences in the simple and Jensen arms. No arm may use later measured truth to skip work.

The tail-truncation inequality follows from deletion coupling: discarded events have total optical mass R; they can change the first-arrival color only when at least one is present, with color difference bounded by the range including background. Ordered disjoint retained bins are exactly compositable. This is an elementary ordinary comparator, not a claimed contribution. Floating-point evaluations of all mathematical bounds still need qualification and do not automatically become certified enclosures.

## Timing and accuracy records

Implement lean numerical paths: count actual arithmetic, allocation, clipping, sorting, CDFs, error estimation, required rule construction and fallback. Exclude evidence formatting, JSON writing, cryptographic hashes, oracle comparison and debug ledger serialization consistently across arms. Do not time a verbose qualification wrapper against an uninstrumented candidate. Retain small branch/work counters from the actual invocation and audit them afterward.

Make one first-use pass followed by five warm passes, each over both epsilons and all48 inputs. Rotate the five-arm order deterministically by pass and fixture index; record the actual schedule. Give every arm independent solver-rule caches. Unit-interval GL rules are the only allowed reuse across rays/passes; no ray-specific mass, sort, pair, truth or output cache. Include lazy rule construction in that arm's first-use delivery or explicit setup total, never drop it as unreported warm-up. Record both the complete first-use batch and all five warm batch totals. Report import/input parsing and other measured common setup separately; do not add nested timings twice.

For each pass/epsilon/fixture/arm, save delivered RGB, wall time (with unrounded nanosecond measurements), selected path, preprocessing/work counters, fallback work and any solver failure. Outside timing, require finite output and maximum-channel error relative to T18 GL64 at most `epsilon+5e-10`; the5e-10 is the inherited reference-agreement allowance, not a fitted margin. Any method failure or accuracy violation remains visible in the fixed denominator. It must not silently disappear from timing statistics or be replaced with an oracle reference.

An implementation/gate failure ends this finite task without a repair run or a performance claim. Statically reviewed code and all outputs are preserved; this engineering failure is not automatically a scientific rejection of the construction. If the300-second cap interrupts a pass, report incomplete data, not extrapolated speedup.

## Pre-result interpretation

Only after every arm completes all required deliveries within accuracy may the screen report comparative timing. Show every group and epsilon, with first-use and warm costs, fallbacks, evaluation counts and timing spread; include controls and dense/opaque cases in full-batch totals. Do not equate reduced quadrature evaluations with reduced complete cost.

A **stable per-case timing win** for a pair arm first requires that the shared exact/global-center shortcuts do not already solve the input and that the pair shortcut actually accepts and delivers its sorted color in every recorded pass. Then its slowest of five warm samples must be faster than the fastest of five samples of **each** ordinary arm on the same non-control N≥4 input and epsilon. Shared-path or fallback timing fluctuations cannot count as benefits of the pair mechanism. Also report absolute times, ratios, the less conservative medians and all spreads without silently upgrading them to stable wins. This rule screens repeatability in this process on this machine; it is not a statistical confidence interval or a production latency requirement.

If neither pair variant has any stable eligible win, close the direct pair-shortcut opportunity **on this fixed development scope**, retaining the mathematical result and timings. This does not prove there is no advantage on any other scene. If a win exists, state whether it is limited to the already known sparse witness and whether it survives whole-batch cost accounting. A sparse-only win or absence of aggregate benefit is limited evidence, not permission to manufacture a favorable scene. Any subsequent step must separately justify actual task/scene relevance and resolve related-work coverage before architecture expansion.

The ordinary optical-depth bracketing construction already identified in T15 also remains relevant prior knowledge; this finite screen does not implement or beat every ordinary enclosure method. Simpson, Gaussian-aware GL and direct tail truncation suffice for this bounded opportunity screen, not a state-of-the-art superiority claim.

No outcome here establishes a SIGGRAPH/TOG contribution. Novelty, scene-level utility, robust cost across workloads/hardware and a coherent paper remain separate requirements of the active goal.
