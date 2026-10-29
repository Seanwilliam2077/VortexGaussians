# Next finite evidence: repair reference robustness before cost experiments

29 October 2026, written after T17's saved results and independent arithmetic review. T17 used its initial attempt and its one allowed repair. It remains **incomplete numerical qualification**, with seven reference failures. Nothing below authorizes changing those records or adding a third execution to T17.

## Decision and why a follow-up is worthwhile

The pair bound has a checked real-arithmetic proof and one informative qualified case at the fixed thresholds. That supports a narrow follow-up, not a method or speed claim. The seven failures expose a concrete reference implementation defect: distinct binary64 breakpoint values can delimit an interval too short for Simpson quarter points. They are not evidence of a rendering bottleneck. An ordinary reference must work before it can be compared fairly.

The next task is **T18: ordinary-reference robustness on the same frozen input**. It must be a separately recorded engineering prerequisite, with all cumulative attempts disclosed. If it executes, it is the third full-qualification invocation across T17 and T18, not a reset history or an independent confirmation dataset. No numerical execution is performed by this preparation document.

## Fixed repair contract

Keep T17's original input bytes, model, stable mean order, pair formulas, analytical controls, GL32/64 orders and scientific thresholds. Copy/extend the reference implementation under a new task directory; do not edit the sealed T17 source/results.

Before adaptive integration, identify only original segments whose midpoint or quarter points coincide with an endpoint in binary64. For a segment `[l,r]`, with `h=r-l>0`, the nonnegative channel emission obeys, in real arithmetic,

```text
0 <= integral_l^r T(t) sum_i s_i(t)c_i[k] dt
  <= U[k] = h * sum_i w_i*c_i[k]/(sqrt(2*pi)*sd_i).
```

For these unresolved segments only, use zero emission and charge `max_k U[k]` to a single global error account. A more conservative envelope using `h*sum_i w_i/sd_i` is permitted to avoid an unnecessary transcendental constant; it must be declared before executing. **Keep the full analytic cumulative extinction and original background attenuation everywhere.** Skipping the density's downstream attenuation would solve a different problem and is not covered by this estimate.

Subtract the sum of all charged segment bounds from the original `1e-11` absolute Simpson budget. A nonpositive remaining budget is failure. Distribute the remainder by length over the other original segments; retain depth 24 and 200,000 evaluations per ray. Any later unresolved recursion that cannot meet its already allocated error budget is failure, not silent acceptance. Add the charged bounds to the returned error estimate and save every endpoint, width, trigger, bound and budget allocation. There is no learned or fitted tolerance.

The segment inequality is mathematical; binary64 arithmetic and the rest of Simpson's empirical error estimate are not a complete numerical certificate. Do not claim one. Analytical controls and independent GL refinement/agreement remain necessary.

## Budget and stopping rule

- First, a static independent review of the implementation and budget accounting. No new web query, source family, package, scene, asset or GPU work.
- Then at most **one** complete evaluation of the same 48 saved inputs, capped at 300 supervisor seconds. No repair/re-execution allowance in T18. Keep all outputs even if incomplete.
- Retain the original `5e-10` reference/analytic comparison and `1e-9` bound-excess allowances. All 48 must pass; do not substitute agreement between GL32 and GL64 for a failed Simpson result.
- Report attempt counts and costs across T17 and T18, the charged intervals and their largest/total bounds, every failure, and the unchanged informative-case counts.
- If the new reference still fails, do not launch another retry or select a subset for performance claims. Record the remaining defect and review whether further effort has decision value. If all pass but no eligible informative case remains, close the direct pair-bound opportunity under the inherited scientific rule.
- If all pass and an informative case remains, prepare a complete-cost comparison. Do not jump directly to scenes, a hierarchy, primitive splitting, tile reuse or a renderer.

This follow-up is authorized by the active research goal and justified by newly recorded implementation evidence. It is not a new scientific success criterion or an attempt to call T17 successful after its budget ended.

## Requirements for the later cost comparison (not yet admitted)

Every method must receive identical Gaussian parameters, clipped interval, colors, exact cumulative-extinction formula and available breakpoints. Compare delivered colors against the same continuous integral. Include preprocessing, clipped masses, sorting, all pair/CDF work, numerical setup and fallback integration. An accept/reject bound without the cost of delivering a color is not a renderer benchmark. Report all fixed cases, including dense/opaque failures, and both cold setup and declared reuse; never report only the sparse witness.

At minimum compare the simple and Jensen pair variants, ordinary accuracy-controlled integration, the global range shortcut, analytically recognized monochrome/proportional inputs, and a cheap disjoint-bin tail-truncation construction. These checks should be offered fairly as common shortcuts where applicable; knowing the bound must not prevent the ordinary method from using the same parameter information.

For the tail construction, place disjoint bins at fixed neighboring-mean midpoints and retain each Gaussian only in its own ordered bin, intersected with `[a,b]`. Empty bins, including tied means, are allowed. The retained model is exactly compositable. If removed total optical mass is `R`, deletion coupling gives

```text
abs(L_original_exact-L_retained_exact)
 <= (1-exp(-R))*range(component colors plus background).
```

Adding `abs(L_original_sorted-L_retained_sorted)` bounds the error of the **same original sorted output**. Include background in the range, because deletion can expose it. This is an elementary ordinary truncation comparator derived here, not a novelty claim or a measured result. It costs linear mass evaluations after sorting, though it may be loose. An implementation and a finite timing protocol still need to be fixed before measurement.

The present evidence does not establish a useful accuracy/cost region against these ordinary alternatives. Literature coverage, real scene/task qualification, robustness under changing parameters and the eventual paper claim remain separate unresolved requirements.
