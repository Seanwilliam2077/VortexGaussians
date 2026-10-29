# T18: account for unresolvable initial segments in the ordinary reference

29 October 2026. Fixed before implementation completion or execution. The preceding goal turn was **progress**: T17's derivation, two attempts, complete saved evidence and independent review were committed and pushed as `c577005870e3deecd9a62e39d0f840ebe03a2b53`. T17 remains incomplete (41/48 qualified); neither historical attempt is overwritten. No task process was live at the start of this continuation.

This implements the finite follow-up already specified in [T17 NEXT_EVIDENCE](../t17-order-inversion-bound/NEXT_EVIDENCE.md). It is an engineering prerequisite for assessing the same order-inversion construction, not a new method, dataset or independent confirmation. This is at most the **third** full-qualification invocation cumulatively across T17/T18. The deleted hourly automation remains deleted; the author-authorized research goal continues.

## Immutable inputs and scientific checks

Read the original T17 `inputs.json` in place (SHA256 `5cccf0238c679e14bc50e67d2d24726a58295b484b1d3464bf77d4eca0491cb7`). No generation or added fixtures. Reuse the sealed T17 implementation (SHA256 `d648567e27b030c454ba37fdbee11b0df1b7de6b9e2a78c10a66cc0031557831`) and original protocol (SHA256 `4c631c90d08d1e5b9ac19ebc6e52cbd2c902c267af105ccbedeb1cccc292586c`). The new process may explicitly replace only its imported `adaptive_simpson` function; record that override and the complete source identity chain. No T17 file edits.

Keep all 48 input records, continuous emission/extinction semantics, full analytic cumulative attenuation, background, stable mean order, pair formulas, GL32/64 orders and nodes construction, breakpoints, controls and gates. Reference/analytic differences remain at most `5e-10`; observed bound excess remains at most `1e-9`. All 48 must pass; GL agreement does not substitute for a missing adaptive reference. Report the original .001/.01 informative-case counts, including the simple-bound comparison, without tuning.

## Selected segment treatment

Inspect every **original** segment `[l,r]` in the saved-input-derived breakpoint list before reference integration. Use the same binary64 midpoint and quarter-point operations as T17. A segment is initially unresolvable only if its midpoint or either quarter point coincides with one of that subinterval's endpoints. Do not merge breakpoints or treat any nonzero width as zero by an arbitrary epsilon. Save the precise triggering equality and all coordinates.

For each such segment, use zero for its emission integral and charge the common channel bound

```text
U = (r-l) * sum_i (w_i / sd_i).
```

This deliberately conservative envelope is chosen before execution. In real arithmetic, the normalized Gaussian density is below `1/sd_i`, `0<=T<=1`, and `0<=c_i[k]<=1`, so its omitted channel emission lies in `[0,U]`. The downstream integrand still uses the **entire original** cumulative extinction, and background attenuation is unchanged. No mass or downstream shadow is removed from the model.

Compute the width as `Fraction.from_float(r)-Fraction.from_float(l)` and each ratio/sum using exact standard-library rational arithmetic on the stored binary64 parameters. Convert each positive U to a float rounded upward, checking the conversion against the exact fraction; preserve exact numerator/denominator strings and the rounded charge. Charge zero exactly when the bound is zero. Sum the rounded charges exactly and round the recorded charge total upward. Take the remaining budget from the exact rational value of the original binary64 `1e-11`, conservatively subtracting the recorded charge total, and round the positive remainder downward. Failure to retain positive budget is a reference failure.

For the other original segments, allocate this remaining budget in proportion to their **exact** lengths and round each allocation downward. Their allocation sum plus the charged total must not exceed the original budget in exact rational arithmetic. If all intervals are unresolvable and the total charge fits, return zero emission plus the unchanged background; record that no adaptive segment remains. A required positive allocation that underflows to zero is failure. No geometric case ID controls this treatment.

Keep ordinary recursively adaptive Simpson/Richardson evaluation for every resolvable segment, max depth24, max200,000 integrand evaluations per ray. Preserve the original midpoint/quarter-point guard inside recursion: a later unresolvable interval remains a reference failure, with no new rescue branch. Returned error estimates must include the charged omitted-emission total in every channel. Save the initial-segment ledger, exact/rounded charges and allocations, recursive error estimate, combined estimate, evaluation/depth counts, and whether the global budget check passes. Budget-account failure is failure, not a warning.

The exact rational envelope concerns this selected omission alone. The rest of Simpson's error estimate, analytic Gaussian evaluation and output arithmetic remain empirical binary64 computations. Do not describe the resulting reference or renderer as a complete floating-point certificate.

## Execution budget and publication

One supervised invocation of all 48 inputs, capped at300 seconds including worker startup/output; **no repair/re-execution allowance**. Use the existing Python/NumPy environment, standard-library Fraction and the already repaired scalar GL construction. No installation, GPU, source search, new scene/asset, renderer or timing experiment. The default entry point must not execute numerical work. Root and a reviewer inspect the code before executing.

Use a new output directory, exclusive file writes, captured stdout/stderr, incremental per-case records, a full aggregate result and before/after identities for this protocol, new script and every inherited source/input. Preserve failure output, even when the worker terminates before a complete result. Publish the small complete result; duplicated per-case checkpoints may remain ignored with their identities recorded. Record worker/supervisor times and all cumulative T17/T18 attempt costs; prior diagnostics remain separate and no failed attempt is called warm-up.

Independent saved-data review recomputes budget arithmetic, fixture identity, pair outputs, analytic/control checks and original gates without rerunning ray integration. T17's GL outputs and scientific pair quantities should remain identical; record any discrepancy. Do not turn a successful correction into a retroactive T17 pass.

## Decision after the one run

- Any reference, identity, accounting or scientific-gate failure: retain it, stop this task's execution, and assess the unresolved defect's decision value; no retry or subset performance claim.
- All48 pass but no originally defined eligible informative case remains: close this direct pair-bound opportunity under the inherited rule.
- All48 pass with at least one eligible informative case: prepare a separately fixed complete-cost comparison, offering ordinary methods identical information and including their recognized analytical/global-range/tail-truncation shortcuts. Do not run that comparison within T18 or proceed to a hierarchy, split policy, tile reuse or scene production.

Only the correctness prerequisite can be satisfied here. Novelty, useful total cost, a genuine task/scene regime and a credible SIGGRAPH/TOG submission remain unproved.
