# T33 independent saved-result review

30 October 2026. **T33 remains failed.** It qualifies seventeen individual records, including one nontrivial mixed-color ray, but completes no frame/view group. The eighteenth ray stops with an unresolved reference cell-budget failure, not an output-disproved result. T32 remains failed and unchanged.

## Scope and identities

The [machine audit](t33-saved-result-audit.json) records 573 passing saved-result consistency checks. It uses standard-library file/hash/JSON/gzip inspection and arithmetic on stored scalars, including exact rational sums/comparisons. No T33/T32 method was imported or executed; no new projection, CDF/exp, density bound, quadrature, simulation or sampling was performed. Only this review and the audit JSON were written.

All thirteen frozen artifacts match before and after the audit. Freeze SHA256 is `e145ffe76842e2ab23f2e14eb229db768ff0128d536d808da473997c731c5d5a`. The attempt, supervisor receipt, worker receipt and result share that identity. Compressed results are 497,390 bytes, SHA256 `c295eef6f762646f489459105f2ce076259b9f56061de42ab343eb8ca6d60c9b`; decompression gives 1,371,474 bytes, SHA256 `262a2bdea17ded89018fec037ffd21c24ccebda48a83d94b8c843bd95a845501`. Stdout equals the worker receipt; its hash and empty stderr match the supervisor receipt. The local journal's completed records and failure equal the final result.

One reserved invocation exited 2, without timeout, launch/cleanup error, surviving child or retry. Computation took 2.0843771 seconds; supervisor time was 2.5327363 seconds, below the unchanged 180/210-second limits. Serialization took 0.1394666 seconds. Publication and final source checks succeeded while retaining failed status. The raw result is below 32 MiB.

## Seventeen completed records

All records follow the first seventeen scheduled pixels of frame 90 / front, with the full 48-point grid still present in the 56-pixel schedule. Saved geometry comparisons, complete/disjoint BVH partitions, omitted-node partitions and mass charges, reference source mappings, leaf ledgers, endpoint decisions, alpha/range checks and coverage counters are consistent. Where the raw operands are available, the audit independently recomputes the algebra. Exponential masses/charges and discarded ordinary per-component projection arrays are not freshly recomputed; their recorded checks and unchanged source contract remain explicit limits.

The first sixteen records remain computationally blank: ordinary `computed_zero_mass`, reference `empty`, no retained reference components. Their largest saved full alpha is `3.1577831205518485e-193`; this is not a claim of exact physical vacuum.

The seventeenth record at **(132, 73)** is a qualified nontrivial mixed-color ray under T33's frozen rule:

| Quantity | Saved or audited value |
|---|---:|
| Full-field alpha | 0.1959615658668975 |
| Ordinary alpha error | 2.3229251577827625e-9 |
| Largest endpoint RGB distance | 0.0009974283275828444 |
| Reference red half-width | 0.0009765609695761568 |
| Ordinary / reference retained components | 34 / 28 |
| Sources with finite optical mass >= 0.0001 | 10 |
| Maximum color span among those sources | 0.07015111059696033 |
| Created cells / leaves | 2,701 / 1,421 |

Its reference reports `output_endpoint_accepted`; independently computed endpoint errors match exactly. The leaf partition covers the whole saved ray interval. Absorption-sum error is `2.7207004103036224e-17`; RGB endpoint reconstruction discrepancies are at most `2.510954214479113e-18`. This is an actual additional completed ray in the new invocation, not a retroactive T32 pass. One group now has one nontrivial and one mixed-color record, but the group and full subset remain incomplete.

## Eighteenth-ray failure

At **(130, 77)**, the saved ordinary GL8 output is `[0.360990986154835, 0.08721908841773367, 0.012048256869983806]`. The reference keeps 57 components and retains a complete, ordered partition of 4,239 leaves over `[0.05019326737669692, 50.19326737669692]`. Its 286 initial cells and 3,953 bisections account for all 8,192 created cells. Another split would require 8,194 and exceed the fixed per-ray cap. Across both nonempty rays, 10,893 cells and 5,233 refinements reconcile with the global counters; the 200,000-cell cap was not reached.

The failed ledger is explicitly `partial_unqualified`, with available bounds. Its absorption-sum discrepancy is `2.948462922410224e-18`; lower/upper RGB reconstruction discrepancies are at most `1.3030306728041702e-17`. Every saved leaf passes the finite, nonnegative and color-range checks. Ordinary omitted finite mass is `1.8857435210502217e-8`, below its charged `2.964922322907969e-5`; the largest reference omission radius is only `4.2050806003502847e-13`.

| Channel | Reference half-width | Ordinary maximum endpoint distance |
|---|---:|---:|
| Red | 0.0011017391378658759 | 0.0011098267905199077 |
| Green | 0.0002661181766433207 | 0.0002677453880957914 |
| Blue | 0.000036784187076218874 | 0.00003702127128664759 |

Red fails the fixed `.001 + 1e-10` endpoint gate. The red interval itself is wider than twice that tolerance, so no proposed red output can be certified by containment in this *current* interval. Nevertheless, it overlaps the allowed interval around the saved output: `disjoint_channels=[]`, `output_disproved=false`, `failure_kind=unresolved`, `failure_cause=budget`. This identifies insufficient interval resolution within the allowed work; it neither proves GL inaccurate nor qualifies the ray. No checks/accepted reference were attached to that failed ray.

The failed reference stage records 1.4805898 seconds. Total counters include 18 ordinary calls, 16 zero paths, 5,664 GL evaluations, two GL rule builds and two rule-cache hits; reference work includes 1,657,516 CDF endpoint calls and 1,111,844 exp-family calls. The expm1 count is a subset of the exp-family count and must not be added again. These named counts and single-process timings retain failed verification work; they are not full-frame latency, FPS or a stable speed comparison.

## Research interpretation

Direct endpoint stopping removed the unnecessary precision obstruction on the previous failure ray, but did not complete even the first group. The failure now directly concerns interval resolution for the requested output decision. The saved data justify that diagnosis, not a claim that ordinary rendering lacks an adequate solution. The post-result [REFERENCE_DIAGNOSIS](../tog/tasks/t33-output-accuracy-qualification/REFERENCE_DIAGNOSIS.md) now identifies a specific numerator/denominator dependency relaxation and proves a complete density-box correction. [NEXT_EVIDENCE](../tog/tasks/t33-output-accuracy-qualification/NEXT_EVIDENCE.md) limits follow-up to at most one separately reviewed and frozen qualification with that correction, unchanged fields/sampling/tolerances/budgets and all other gates. There is no pilot or retry; failure closes this density-box reference route on the fixed fields. This is result-informed verification work, not a new rendering method. No implementation or next invocation was performed by this audit.

The audit checks identities and saved algebra, not a fresh mathematical enclosure proof or directed-rounding certificate. It supplies neither full-image accuracy nor a rendering bottleneck, production requirement or TOG contribution.

## Post-result claim and mathematical review

Read the new README, REFERENCE_DIAGNOSIS and NEXT_EVIDENCE in full, without editing them; identities are recorded in the audit. No blocking claim or mathematical issue was found. Their retained failure, incomplete coverage, non-disjoint interval and binary64 limitations match the evidence. Saved-data arithmetic additionally confirms the 57 retained components have red minimum 0.9320010346900842, maximum 1.217375068507919 and equal stored widths. These statistics motivate the analysis; they do not establish how much tightening will occur.

For positive summed lower density, the sign of each color coefficient minus an extremal ratio forces the relevant lower/upper endpoint, so the sorted N+1 threshold corners include a real-arithmetic optimum. For zero summed lower density, the exact positive-denominator extrema are the minimum/maximum colors among positive upper bounds; an all-zero upper box must fail. The resulting channelwise extrema enclose the mixture, dominate the old independent quotient/range enclosure and translate with a common color offset. The documents correctly acknowledge that existing range clipping already fixes equal-color channels.

The proposed single correction must charge sorting and stable prefix/suffix scans, retain the original full-field color maximum for omission, and keep ordinary output out of bound construction and priority selection. Bounds may change priority values, but not its selection rule. These are pre-execution obligations and elementary linear-fractional facts, not a numerical result or novelty claim. The stated one-attempt closure prevents this analysis from silently authorizing an unlimited sequence of reference variants.

Audit JSON SHA256: `fbe50f33366a0d2a4cd861e1926add9e4fdac84c31262f9c7bc33e1e3faaa749`.
