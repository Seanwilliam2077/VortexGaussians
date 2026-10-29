# T32 independent saved-result review

30 October 2026. **T32 remains failed and the ordinary entry is not qualified.** The saved records identify a reference cell-budget failure, not an observed ordinary-solver accuracy failure. Good-looking endpoint distances do not override the frozen reference-radius or subset-completion gates.

This review used existing receipts, the compressed result, frozen-file identities and previously reviewed source contracts. Standard-library arithmetic checked stored scalars, using exact rational sums/comparisons where specified in [the audit](t32-saved-result-audit.json). No T32/T22 module was imported, and no Gaussian projection, CDF, exponential, integrand, quadrature, sample, simulation or render was evaluated. An initial PATH `python` invocation resolved to the Store alias and launched no interpreter; subsequent saved-data audits used the existing interpreter named by root. Only this review and its audit JSON were written.

## Identity and execution

All ten frozen artifacts still match their declared byte counts and SHA256 values. Attempt, execution, worker receipt and result share freeze SHA256 `fd60ada647d1e20a78c86894a39826ae29de7810e220cf5fed320c016a935135`. Compressed results are 374,592 bytes, SHA256 `044d591adc42945209cd368c359caaab3b237f097e52efac01d387ea240b3dc8`; decompression gives 1,054,391 bytes, SHA256 `d716646a9520f5a266e3304c68b31218a5d2cd05852ac64cff39bed348a26c58`. This is below the32MiB raw cap. Stdout/stderr identities match the execution receipt; stdout's JSON equals the worker receipt.

One invocation returned exit2 with no timeout, launch/cleanup error or running child. Computation took0.9825742s and recorded supervisor time1.3827239s, below180/210s. Publication succeeded and retained `status=failed`; final source checks passed. These timings include qualification work and do not establish renderer throughput.

## Completed records and failed ledger

The304 audit checks pass as **saved-result consistency checks**. The16 completed records match the first16 scheduled pixels of frame90/front. Each uses ordinary `computed_zero_mass` and reference `empty`, with no retained reference components. Their saved geometry, partitions, omissions, intervals, endpoint/alpha gates and necessary output ranges satisfy the fixed checks. The largest saved full alpha is only `3.1577831205518485e-193`: these are computationally blank rays, not evidence of nontrivial rendering coverage or exact physical vacuum.

The next scheduled pixel, `(i,j)=(132,73)`, failed at `reference_enclosure`. Its saved ordinary result is GL8 with no fallback, RGB `[0.18927751611345842, 0.043074561765932266, 0.006092713879154582]`. The reference retained28 components; ordinary pruning retained34. These different selections are permitted and independently accounted for.

The failed reference diagnostics contain a complete current partition of4,166 leaves, explicitly marked `partial_unqualified`. The leaves are ordered, adjacent and cover the full saved interval `[0.050291694148335286,50.29169414833528]`. Their absorption sum differs from saved retained alpha by `2.8775073846640744e-17`. Reconstructing lower/upper RGB sums with the saved omission uncertainty gives discrepancies at most `5.524869401368046e-18`. Every saved leaf satisfies its finite/nonnegative and color-range checks. Retained weights/means match their full-projection source entries.

The counts explain the stop exactly:141 initial cells plus2×4,025 refinements equals8,191 created cells; the next two children would exceed8,192. The global200,000-cell and time caps were not reached. Maximum depth is8. Final reference half-widths are

```text
[0.0003317207355572338, 0.00007603933595447948, 0.00001073370175794057].
```

The red half-width exceeds the frozen `.0001` gate. Reference omission mass is only `5.400927096589486e-14`; saved sums also show ordinary omitted finite mass `2.889072074512326e-9` below its charged `6.4653559743036e-6`. This supports the recorded interval-refinement-budget attribution, without recomputing any mass or claiming all later gates executed.

## Interpretation and next finite evidence

Arithmetic against the saved failed interval gives ordinary maximum endpoint distance `0.00033438192276991074` and alpha distance `2.3229251577827625e-9`. Both are below`.001`, but this is an additional diagnostic on an unqualified reference, **not a seventeenth passing record**. The original run stopped before that ray's qualification stage. Only one group was constructed and zero of six groups completed; no qualified nontrivial or mixed-color coverage exists.

The post-result **stopping-contract analysis is now complete** in [STOPPING_CONTRACT](../tog/tasks/t32-ordinary-volume-entry/STOPPING_CONTRACT.md). For a true enclosure, maximum endpoint distance bounds the error of a fixed ordinary output; whole-interval containment is sufficient, strict disjointness demonstrates inaccuracy, and other overlap is inconclusive. This elementary argument does not supply a formal binary64 certificate. The justified next evidence is one separately named, independently reviewed and frozen output-accuracy qualification under [NEXT_EVIDENCE](../tog/tasks/t32-ordinary-volume-entry/NEXT_EVIDENCE.md), not another analysis credited as progress. It remains result-informed development rather than held-out confirmation. No successor invocation was performed or authorized by this audit.

The audit validates ledger identities and arithmetic, not fresh density extrema, transcendental mass/alpha evaluation or directed-rounding guarantees. It supplies neither a full-image result nor evidence of a TOG contribution.

## Post-result document review

The new README, STOPPING_CONTRACT and NEXT_EVIDENCE were read in full, without edits. Their final identities are recorded in the audit JSON. No blocking claim or mathematical issue was found. They preserve T32's failure, the sixteen completed computationally blank records, zero completed groups, unqualified seventeenth ray and the lack of a formal floating-point certificate.

The proposed stopping rule is legitimate conditional on a valid enclosure. The ordinary output is fixed before reference work and affects only the stopping decision; projection, omission, retention, interval construction, heap priority and splitting must remain independent of it. All other numerical, geometry, ledger, identity and coverage gates remain necessary. Saving actual widths prevents a wider decisive interval from being represented as a 0.0001-accurate reference.

The successor boundary is sufficiently specific: identical authored fields and geometric subset, including dark rays; unchanged tolerances and resource limits; no new envelope, sample replacement or repair-and-run retry; stop at the first failed gate or unresolved budget. A successful successor would qualify only that subset. These conditions prevent the documented change from silently reclassifying T32 or searching for favorable cases; implementation and freeze must still be reviewed before that single invocation.

Audit JSON SHA256: `cc0fecd51b6bcbf7ec663401b988e11e2d730d9c61ba99c8e1719f1a6d961963`.
