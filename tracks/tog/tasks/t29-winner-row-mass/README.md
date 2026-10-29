# T29 — winner-row probability mass does not add an accepted case

29 October 2026. **Qualified saved-data analysis; candidate admission fails.** One permitted invocation completed all48 original development rays,399 labels and3272 pairs. At the unchanged tolerances, the row optimization accepts exactly the same cases as T21 and the cheaper row envelope. The fixed decision is `archive_row_optimization_on_fixed_scope`. No cost comparison, further variant, new fixture, training or source acquisition is queued by this result. The full research goal remains active and no TOG core contribution is established.

## What was tested

T21 bounds each differing-winner event independently. This experiment additionally uses the fact that one sorted winner cannot produce several actual winners in the same realization: row mass is at most `q_i=P_i*alpha_i`. For each sign and color channel, an ordinary fractional-knapsack problem allocates that mass under the inherited pair capacities. The saved primal allocation and a nonnegative dual cutoff make the result independently checkable. This is an elementary probability/optimization construction, without a novelty claim.

The required cheap control clips each independent row sum by `q_i` times its largest contributing color coefficient. Both simple and Jensen pair capacities are evaluated; Jensen alone determines admission. The sorted RGB, reference data, populations and tolerances stay unchanged. See the pre-execution [protocol](PROTOCOL.md), [derivation](DERIVATION.md), [freeze](freeze.json) and [static review](../../../validation/t29-pre-execution-review.md). Support wording, the exact-capacity cutoff wording and persistent partial journals were corrected before freeze; there was no post-execution repair or retry.

## Result and attribution

The common-unsolved population contains the same28 non-control rays with at least four labels. It excludes previously declared common exact and G/2 shortcuts; it does not assert failure of every ordinary method.

| Absolute RGB tolerance | T21 accepted | Cheap row accepted | Row LP accepted | Added by LP beyond cheap and T21 |
|---|---:|---:|---:|---:|
| .001 | 1/28 | 1/28 | 1/28 | 0 |
| .01 | 4/28 | 4/28 | 4/28 | 0 |

This table is identical for simple and Jensen capacities. At.001 only `structured-04-n4-span3` passes. At.01 `generic-11-n8`, `generic-14-n4`, `structured-04-n4-span3` and `structured-08-n8-span3` pass. Neither cheap control adds an accepted case, and Jensen adds no acceptance beyond simple. The two epsilons were not widened by numerical check allowances.

Some bounds do tighten without meeting either tolerance. In the primary28-ray Jensen population, LP decreases maximum-channel E by more than the existing1e-12 arithmetic allowance on two rays beyond the cheap control:

| Ray | T21 E | Cheap E | Row LP E |
|---|---:|---:|---:|
| generic-16-n16 | .6735734548533894 | .6732233285308025 | .6333693713099705 |
| generic-07-n8 | .0926695817115267 | .0926695817115267 | .09240400167501535 |

The remaining thresholds are far below these bounds. This diagnostic is descriptive, not an alternative admission rule. Across all48 rays, Jensen LP tightens three maximum-channel bounds versus T21, two beyond cheap; one of the three is a control already handled by a common path. Simple tightens seven versus T21 and six beyond cheap; in the28-ray population those counts are six and six. Full case values and flags are in [result-summary.json](result-summary.json).

The saved references also explain why the two primary improvements cannot produce an accurate accepted output: their actual sorted-output errors against GL64 are.21175960946546646 (`generic-16`) and.039155559591249056 (`generic-07`), both above.01; the other saved references agree on that rejection. A better valid bound alone cannot fix these outputs. Conversely, among the28 rays, saved GL64 errors are within.001 on two rays and within.01 on ten, while LP accepts one and four respectively. Some conservative rejection therefore remains elsewhere. These reference observations are post-result explanation only, never formula inputs, a new gate or permission to select new fixtures/refinements.

All48 cases pass the fixed structural, allocation, duality, dominance and saved-reference checks. Maximum reconstruction discrepancy is2.220446049250313e-16, primal/dual gap and row-budget excess are each1.1102230246251565e-16, and observed reference enclosure excess is5.440092820663267e-15. Dominance excess is zero. These satisfy the pre-fixed1e-12 arithmetic and1e-9 enclosure allowances; they are empirical binary64 checks, not outward-rounded certificates. The [independent saved-certificate review](../../../validation/t29-saved-certificate-review.md) checks stored evidence without rerunning the candidate or integration.

## Work and reproducibility

The sole [supervised invocation](run-01/execution.json) exits0 without timeout in0.5173684 seconds against its60-second cap; worker work before serialization is0.2295189 seconds. Recorded arithmetic includes399 row-budget products,3272 pair traversals,6544 prefix-cap products,4788 coefficient-sort calls,11036 sorted items/greedy visits,10899 budget subtractions,42684 row-objective products and25668 fsum calls. There are zero new Gaussian CDF, exponential, integrand or quadrature evaluations, zero source calls, and no model/tensor/imported renderer work. The reduction uses only the standard library.

This time pays saved-data analysis and serialization, not a complete rendering delivery. Production would also pay masses, prefixes, pair caps, output construction, failed shortcuts and any fallback. The straightforward row algorithm sorts per row/sign/channel, with O(N² log N) sorting and O(N²) stored pair detail; the cheap control is O(N²) after the shared pair preparation. Because the acceptance gate fails, no speed comparison is prepared and no performance gain follows from this runtime.

All detailed allocations, cutoffs, checks and48 cases are preserved in [results.json.gz](run-01/results.json.gz), a280009-byte lossless gzip of4615730 result bytes. [publication.json](publication.json) records exact raw/compressed/log/journal identities and a verified decompression roundtrip. Duplicate raw results and journals remain ignored. The [evidence manifest](audit-manifest.json) binds public artifacts and unchanged history. Frozen scripts preserve the original single-invocation contract; they are archival evidence, not an instruction to retry the experiment.

## Decision boundary

The real row constraint is nonredundant on some development values, but its measured tightening supplies no additional usable acceptance under the original output and accuracy contract. Archive this optimization on the tested scope. Do not automatically add a column/global LP, shift the output, relax thresholds, create selected fixtures, start a cost study or reopen the closed training/source route. A negative development screen does not prove the bound is useless for every workload.

T19 remains failed/incomplete with stable wins NOT EVALUATED; T22's small, overlapping complete-cost differences remain unchanged; T28's acquisition route remains closed pending concrete usable carrier/environment evidence. There is no queued successor experiment from T29. Continuing toward the full goal requires a separately justified substantive mechanism or usable workload evidence, rather than another refinement of this failed admission screen. Original core, art and main are unchanged.
