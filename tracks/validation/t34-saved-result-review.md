# T34 independent saved-result review

30 October 2026. **The saved evidence supports `qualified_fixed_subset_only`: all 336 prescribed rays and all six frame/view groups completed.** Each group contains eight nontrivial mixed-color rays. T32 and T33 remain failed; this result does not reclassify them or establish full-frame accuracy, a performance bottleneck or a TOG contribution.

## Scope and identity

The [machine audit](t34-saved-result-audit.json) contains 11,229 passing consistency checks, grouped counts and an empty failure list. It checks all 336 saved records using file identities and arithmetic on stored values, including exact rational ledger sums/comparisons. No T34/T33/T32 numerical module was imported or executed; no projection, CDF/exp, density bound, box optimization, quadrature or new sampling occurred. Only this review and its audit JSON were written.

All thirteen frozen identities match before and after the audit. Freeze SHA256 is `8616f52d15065bb7d468ff0e297ce6fccfc02a57b4868e5f575066516ea8ee85`. The 2,536,082-byte result gzip has SHA256 `b9d9e2b98da24092962a9918140d0f94c407266018bf2f8fdcb9067d14f2c9c7`; its 8,945,763-byte raw JSON has SHA256 `abace20f34f112ec7090847aa22c5e1769881512a0375435b9bbffba6c277bd0`. Both match the receipt and remain below the raw-size cap. Attempt, supervisor, worker and result identities agree; stdout equals the worker receipt, stderr is empty, and the local journal's 336 completed records equal the final result.

The only T34 invocation exited 0 with no timeout, launch/cleanup error, surviving child, publication error or retry. It is the third cumulative authored-entry qualification. Computation took 27.5656856 seconds and supervisor time 28.7540014 seconds, within the unchanged 180/210-second limits. Final source checks passed.

## Accuracy and coverage checks

All saved schedules retain the 48 grid points and eight prescribed original-source center samples per group, with deterministic source tags, deduplication and row/column ordering. All records match those schedules. Every group has 56 completed records, eight qualifying nontrivial rays and eight mixed-color rays.

The audit checks saved unit geometry and independent-ray agreement; complete/disjoint BVH and omitted-node partitions; actual omitted masses and their recorded charges; source/retained mappings; finite masses and selection thresholds; every available leaf's range and complete partition; absorption and interval reconstruction; endpoint acceptance and independent alpha error; ordinary output ranges; and coverage counters. All pass within the frozen allowances.

| Aggregate | Audited value |
|---|---:|
| Largest RGB endpoint distance | 0.0009900183196412948 |
| Largest alpha distance | 0.0000037368930378423038 |
| Allowed RGB/alpha distance | 0.001 + 1e-10 |
| Largest reference half-width | 0.0009851367678958 |
| Largest leaf absorption-sum discrepancy | 1.0595966286351343e-16 |
| Largest endpoint-ledger reconstruction discrepancy | 1.5775286644854044e-16 |
| Largest reference omission RGB radius | 1.222231427752412e-12 |
| Created cells / saved leaves / bisections | 11,097 / 10,713 / 384 |
| Maximum created cells per ray / depth | 392 / 4 |

The largest endpoint distance occurs at frame 90 / front / (125, 139); the largest alpha distance occurs at frame 90 / side / (125, 99). Every reference reports `output_endpoint_accepted`, and recomputed endpoint distances match the stored values. Empty and equal-color analytic records have the appropriate empty ledgers and analytic retained colors.

Ordinary paths are 287 `computed_zero_mass`, 48 `gl_no_fallback` and one `ordinary_color_box`. All 48 GL paths stop at order 8. Reference paths are 286 `empty`, 49 `enclosure` and one `equal_color`. These path counts differ legitimately because reference projection/retention and ordinary pruning are independent.

**All 48 nontrivial rays have source-center tags; none of the 288 grid-tagged samples has full alpha >= 0.001.** The coverage gate is satisfied exactly as declared, but visible support, silhouette/transition pixels and the unsampled image are not comprehensively covered. The two states are authored fields from the same local demonstration, not independent scenes or validated creative tasks.

## New bound accounting

Eighteen counter identities reconcile with the saved records and implementation contract. They include three channel calls per created cell; three color sorts per non-analytic ray; eight scans per positive-lower channel; product/scan/corner/division relationships; zero-lower support accounting; and the five add/sub operations per Neumaier update plus corner combinations and residual restoration. No density box was reconstructed or optimized during this audit.

The saved work includes 147 sorts, 263,976 scans over 11,985,792 terms, 2,996,448 weighted products and 3,062,442 corner ratios. The reference performed 2,261,584 CDF endpoint calls and 1,166,322 exp-family calls; expm1 is a subset, not an additional count. Ordinary GL performed 135,156 evaluations, with two rule builds and 94 rule-cache hits. These are named implementation counts, not all FLOPs.

Summing saved stage times gives about 0.2031 seconds ordinary preparation, 7.8619 seconds ordinary solve, 0.9761 seconds independent projection and 17.7429 seconds reference work. These are accounting for this single qualification process. The selected workload, shared rule cache and verification overhead prevent interpreting them as full-frame latency, FPS or a stable speed comparison.

## What this establishes and the next question

The corrected ordinary reference can complete this fixed authored subset within the original resource limits, and the unchanged ordinary BVH/GL entry meets its prescribed numerical gates. There is no demonstrated need for a new rendering method on these rays. The box-extrema correction is verification-tool work; mathematical exactness over a density box does not establish novelty.

The saved coverage justifies a complete-image feasibility question, now bounded in [NEXT_ENTRY](../tog/tasks/t34-box-reference-qualification/NEXT_ENTRY.md): one separately frozen full frame at the existing sequence's first group, frame 90 / front, at the original 256x192 resolution. This deterministic first step is not a substitute for the other views/states or independent scenes. Use the same ordinary/reference/field and numerical gates, with fixed display mapping and no crop or exposure selection. The new full-pixel task may allow at most 600 seconds computation / 630 seconds outer wait plus 10 seconds cleanup, while retaining the 8,192 per-ray / 200,000 total reference-cell limits. That declared workload allowance does not revise any old result. Multiplying subset time by a pixel ratio or treating verifier time as renderer latency would not answer complete cost. No next experiment was executed here.

Limits remain explicit: transcendental masses/alpha, exponential charge formulas and Gaussian density extrema were not re-evaluated. Ordinary per-component projection arrays were not retained; the audit checks their saved maximum discrepancies and immutable implementation. The geometric projection used to choose source-center samples was not regenerated. Compensated binary64 arithmetic and these saved consistency checks are not directed rounding or a formal floating-point certificate.

## Final documentation review

Read the new README and NEXT_ENTRY in full without edits; their identities are recorded in the audit. No blocking claim/scope issue was found. Saved arithmetic confirms that the 288 grid-tagged samples have maximum full alpha approximately 1.29e-8, reinforcing the disclosed coverage limitation. The documentation correctly separates a scalar Python correctness entry from an optimized paper baseline, and complete ordinary cost from reference-verification cost.

The future full-frame contract still needs an explicit compact storage layout and per-pixel/aggregate checks sufficient to support every claimed geometry, pruning, ledger, endpoint and alpha gate. RGB/alpha/endpoints plus a valid/completed mask prevent unfinished pixels from becoming apparent black background; saving them alone does not automatically prove every other gate. This is an implementation-review obligation, not a defect in the current task boundary. The document requires one exclusive invocation, predeclared display mapping, at most 32 MiB raw numeric output and preservation of partial valid results on the first failure, with no pilot, repair-and-rerun or automatic cap increase. A result would concern one authored image, not a formal certificate, six-view evaluation or contribution.

Audit JSON SHA256: `1b33138cf90a07406c6df9df1e5284deb50c7a3ba433bb9ae934328b88d84855`.
