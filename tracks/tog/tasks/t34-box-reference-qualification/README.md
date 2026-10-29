# T34 — the fixed ordinary-entry subset qualifies

Completed 30 October 2026. **All336 prescribed rays and all six frame/view groups qualify under the frozen numerical contract.** This is a development-subset result, not full-image accuracy, a strong renderer benchmark or a TOG contribution. T32 and T33 remain failed and count toward the three cumulative authored-entry qualification invocations.

The scope limit matters: all48 nontrivial mixed-color rays are prescribed projected-source-center samples. None of the288 grid samples has full alpha>=0.001 (their maximum is approximately1.29e-8). Thus the pass establishes ordinary accuracy at those specified inputs, while leaving visible support, silhouette and transition pixels largely unexamined. The two snapshots come from one authored demonstration, not independent scenes or a validated creator brief.

## Changed bound and actual outcome

[The protocol](PROTOCOL.md) replaces only the per-cell independent numerator/denominator quotient with exact per-channel extrema over the same density box. Three deterministic color orderings and nonnegative Neumaier prefix/suffix scans enumerate threshold corners. The original density bounds, optical weights, omission charge, ordinary BVH/GL solver, field, sample rule, tolerances and resource budgets stay unchanged. [Static review](../../../validation/t34-pre-execution-review.md) and [freeze](freeze.json) precede the sole invocation; no pilot or retry occurred.

| Audited quantity | Result |
|---|---:|
| Completed rays / groups | 336 / 6 |
| Nontrivial mixed-color rays | 48, eight per group |
| Maximum RGB endpoint distance | 0.0009900183196412948 |
| Maximum alpha distance | 0.0000037368930378423038 |
| Allowed distance | 0.001 + 1e-10 |
| Reference created cells / leaves / bisections | 11,097 / 10,713 / 384 |
| Maximum created cells per ray | 392 (cap8,192) |
| Supervisor / computation time | 28.7540014 / 27.5656856 seconds |

Ordinary paths are287 computed-zero,48 GL and one color-box shortcut. All48 GL calls finish at order8. Reference paths are286 empty,49 cell enclosures and one equal-color analytic result, reflecting its independent all-source retention. The unchanged ordinary solver meets all declared geometry, pruning, ledger, RGB/alpha/range and coverage checks. There is no demonstrated need for a new rendering method on this fixed subset.

## Cost is qualification work

Saved stage times sum to0.2031312 seconds ordinary preparation,7.8619421 ordinary solving,0.9761489 independent projection and17.7428989 reference computation. The remaining wall time includes source/decode, scheduling, tree construction, checks, journal and serialization. The reference's147 sorts,263,976 scans,11,985,792 scan terms and3,062,442 corner ratios are counted. Ordinary GL records135,156 integrand evaluations and6,868,656 scalar component evaluations, with two rule builds and94 hits.

These single-process numbers are not FPS or full-frame latency. The ordinary implementation is Python scalar code with repeated per-component CDF/PDF work; it is a correctness entry, not an optimized paper baseline. A later performance claim requires ordinary batching/compilation or other appropriate strong implementation, complete costs and suitable workloads. Making a candidate beat this scalar implementation alone would not establish a contribution.

## Preserved evidence

[Attempt](run-01/attempt.json), [execution](run-01/execution.json), [worker receipt](run-01/result.json), and [full lossless results](run-01/results.json.gz) preserve all records and cell ledgers. Raw JSON is8,945,763 bytes; gzip2,536,082 bytes. All13 frozen identities match. There was no timeout, launch/cleanup error, surviving child, publication error or retry.

[Independent saved-result review](../../../validation/t34-saved-result-review.md) checks11,229 stored-data conditions, including every record/leaf and18 new counter relationships; [its aggregate audit](../../../validation/t34-saved-result-audit.json) has no failures. It performs no new projection, CDF/exp, box optimization or integration. This checks saved consistency, not directed-rounding guarantees. Real-arithmetic box optimality and compensated binary64 computation do not make a formal floating-point certificate.

[Next entry](NEXT_ENTRY.md) addresses the visible-content and pixel-coverage gap with a separately frozen complete first-frame feasibility task. It does not immediately introduce a candidate or extrapolate sample timing. The original core, art, main and T28/T29/T30 outcomes remain unchanged; genuinely distinct scenes, useful task evidence, a strong complete renderer and a core contribution remain missing.
