# T22 independent saved-data cost audit

29 October 2026. Reviewer: `volume_screen`. **PASS: the saved evidence supports the frozen local primary prefix-increment decision. No blocking inconsistency found.** It does not establish a broadly useful renderer or a TOG contribution.

This audit used standard-library JSON reading, hashing, comparisons and arithmetic on saved values only. It did not import research modules, evaluate a density/integrand, execute a solver, create a reference/sample, access the network, or rerun the experiment. The system `python` alias failed before launching; the successful audit used the already recorded environment executable. Neither was a scientific worker invocation.

## Integrity and complete qualification

- All 15 frozen artifacts match their current sizes/hashes and the worker/supervisor before-and-after identities. Freeze SHA256 is `e67f874e9a2d11d2687c0f37f48a71be75f0f32553a3a3808d178e726d638769`. Source identities are those in the sealed [preexecution review](t22-preexecution-review.md).
- The one supervisor record has exit 0, no timeout/launch/identity error, and 13.1846729000099 seconds through worker exit, below the 300-second cap. The scientific worker records no fatal failures.
- Parsed journal records equal result records exactly, in order. All 3,648 records independently match their expected stage, pass, epsilon, fixture, arm position and rotation. Stage A contains all 192 accurate calls before the 3,456 Stage B calls; none are missing or duplicated.
- Every RGB error was recomputed against the saved T18 GL64 RGB. Every recorded error and gate agrees. Maximum observed error is `0.0006010194764183296` at epsilon .001 and `0.0073995006561309445` at epsilon .01, both within the fixed `epsilon + 5e-10` gates. These maxima include all arms and both stages; they are not formal integration-error guarantees.
- All 96 case/epsilon comparisons, every group/epsilon/arm aggregate, all initial and subsequent batch totals, medians, minima, maxima, path counts and reported stable-win decisions were independently reconstructed from raw records. Controls and failed-shortcut costs remain included in batch accounting.
- Per-arm caches contain only degrees 4, 8 and 16. Stage A records three rule builds per baseline; Stage B records three fresh builds per arm, all during pass 0. This agrees with the reviewed separate-cache allocation. No actual delivery invoked the preserved GL-to-Simpson fallback; its presence in source was not silently removed.

## Formula consistency and attribution

For all 1,848 non-common pair deliveries in Stage B, actual acceptance equals the corresponding frozen T21 simple/Jensen, signed-only/combined bound decision. All 492 complete pair scans reproduce the saved T21 bound exactly (maximum channel difference 0). Accepted sorted RGB differs from T21 by at most `1.1102230246251565e-16`, below the requested `1e-12` check despite the disclosed prefix implementation difference.

Both prefix arms have five stable joint-delivery case/epsilon wins: the old `structured-04-n4-span3` at both epsilons, and the three added rays at .01. **Only `structured-08-n8-span3` at .01 is a prefix-increment win**, for both primary Jensen and secondary simple. Neither signed-only arm accepts that ray in any of the six passes. The other two newly admitted rays are already accepted by both signed-only arms and therefore do not count as prefix-increment wins.

Five subsequent samples on the sole primary incremental case, in microseconds:

| Arm | Median | Minimum–maximum |
| --- | ---: | ---: |
| Direct GL | 2032.8 | 2013.8–2066.4 |
| Tail → GL | 2020.3 | 2008.7–2044.2 |
| Signed simple → GL | 2120.7 | 2099.4–2166.6 |
| Signed Jensen → GL | 2118.5 | 2115.3–2944.0 |
| Prefix simple | 174.2 | 169.4–185.9 |
| Prefix Jensen | 174.0 | 170.0–193.8 |

The Jensen candidate's worst subsequent sample is below every comparator's best sample, and its actual shortcut accepts in all six passes. Its median direct-GL ratio is 11.6828. Thus the predeclared primary decision `RETAIN_LOCAL_PRIMARY_PREFIX_INCREMENT_COST_OBSERVATION` is correctly triggered by this one development case. No new threshold, selected formula, alternate primary or omitted comparator is needed to obtain that decision.

## Complete workload costs remain modest

All 48 cases and both epsilons, per arm, milliseconds. The initial column is initial rule use after Stage A in the same process.

| Arm | Initial | Five subsequent batch median | Minimum–maximum |
| --- | ---: | ---: | ---: |
| Direct GL | 302.7506 | 304.7900 | 303.1118–306.5661 |
| Tail → GL | 303.1634 | 305.0116 | 304.0938–307.7966 |
| Signed simple → GL | 299.9891 | 302.0217 | 300.6117–306.0989 |
| Signed Jensen → GL | 299.5780 | 303.4523 | 300.9591–308.5783 |
| Prefix simple → GL | 299.0056 | 303.1917 | 300.6833–306.8649 |
| Prefix Jensen → GL | 299.7749 | 300.6289 | 298.3573–303.2137 |

Both epsilons separately, subsequent batch medians in milliseconds:

| Arm | Epsilon .001 | Epsilon .01 |
| --- | ---: | ---: |
| Direct GL | 152.5000 | 151.6983 |
| Tail → GL | 153.6042 | 151.5782 |
| Signed simple → GL | 152.8419 | 149.4290 |
| Signed Jensen → GL | 153.5928 | 149.8595 |
| Prefix simple → GL | 155.3931 | 148.3462 |
| Prefix Jensen → GL | 152.9530 | 148.2335 |

The primary's combined batch median is approximately 1.37% below direct GL and 0.46% below signed simple. Its combined range overlaps the direct-GL range, and it does not beat signed simple in every paired batch. At .001 its median is slightly slower than direct GL; at .01 it is approximately 2.28% lower. These are complete-workload observations on this Python implementation, not robust broad speedup or production evidence. The large isolated-case ratio must not replace these workload results.

## Paid work and counter interpretation

Stage A delivery time totals 606.0776 ms (GL 302.6600; tail 303.4176), within a 616.8993 ms stage window. Stage B delivery time totals 10,913.7896 ms within 11,125.3260 ms. Imports cost 715.7947 ms; input/reference parsing and validation 27.7618 ms; hardware metadata 158.6798 ms. Recorded output validation costs 4.2878 ms in A and 91.6704 ms in B. Journal serialization/flush costs 117.6391 ms, summary construction 117.6600 ms, and final result serialization/write 225.8779 ms. Identity checks, raw snapshots, cache creation and attempt publication are also retained in setup accounting. These are nested in enclosing stage/worker/supervisor windows and must not be added to those windows again.

All recorded counter aggregates were recomputed. In particular, `integration_evaluations = gl_evaluations + simpson_evaluations`, and `normal_cdf_calls = 2 * normal_interval_calls + pair_cdf_evaluations` on every record. These are overlapping summaries, not extra work to sum together. `pair_total_possible` is potential pair count, not actual visits. B records 154,872 possible pairs, 20,592 visited pairs and 15,774 pair CDF evaluations. The 1,356 early pair rejections and 438 tail rejections include their preparation plus fallback costs.

In B, both signed-only arms each accept 120 deliveries and fall back on 342; both prefix arms each accept 126 and fall back on 336. Each arm also shares 114 common-path deliveries. The prefix increment is six additional acceptances: one ray/epsilon repeated across six passes, not six independent cases. Signed-only records no prefix exponentials/products. Accepted prefix composition reuses 720 nonzero prefix components in total and records no repeated composition exponentials. GL rule builds are six in A and eighteen in B, with all work charged to the requesting arm.

## Saved artifact hashes and bounded conclusion

Hashes below authenticate uncompressed contents even if publication later compresses them losslessly.

| Artifact | SHA256 |
| --- | --- |
| T22 `run-01/results.json` | `b1e2863098e17d5c975b863f52f582042769e1dc7676df3c7cad7439e3500bd0` |
| T22 `run-01/deliveries.jsonl` | `62979e0650a61eff816263516ec5eeab12d74c83cef245ba665168787ee7ca95` |
| T22 `run-01/execution.json` | `09e1cbf59ef1da660dc3cbaf3b9dd9e62907d56618389381cbb198fc3a9cc1de` |
| T22 `run-01/attempt.json` | `a3486a2c585687fd67a0678fce6c40c41316debf1c761d86d1d9f13b1de78d71` |
| T22 `run-01/publication-accounting.json` | `4124dcec8eb97aee32b0da08fe06284b2166cc96255c4aff93d8bec840e721b0` |
| Frozen T21 `run-01/results.json` | `94d3ad607ba70ee6d7192643e6ad39ec3802f2a269b12df8cbfe87e59917bf83` |

The sole run is complete, accurate on the frozen workload and consistent with its registered local decision. Its added prefix evidence remains one development ray at one tolerance, with modest whole-workload benefit and no universal numerical certificate, Gaussian-specific novelty, scene relevance or TOG core contribution established. T19 remains a separate failed, incomplete experiment; no timings or historical gates were pooled. This audit authorizes no follow-up execution or expansion.
