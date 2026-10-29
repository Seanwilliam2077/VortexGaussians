# T19 independent code, saved-delivery and cost-accounting review

29 October 2026. Reviewer: pressure_screen. **T19 stopped correctly on an accuracy failure after 232 of 2,880 planned deliveries: 231 passed, one failed and 2,648 were unexecuted.** This does not qualify the complete-cost comparison. Stable wins were **not evaluated**, rather than measured to be zero. No performance-superiority or scientific rejection of the pair construction follows.

The single failed delivery is the tail arm's **ordinary Simpson fallback**, at `clipping-07`, epsilon 0.001, first-use pass. The tail shortcut rejected; it did not return an inaccurate retained-color approximation. The same fixture's immediately preceding ordinary GL16 delivery passed. Both facts are retained without extending a partial run into a method-wide conclusion.

## Review scope and independence

Before execution, this reviewer read T18 NEXT_EVIDENCE, T19 PROTOCOL and all three implementation files. The review identified avoidable per-primitive original-alpha preparation charged to ordinary methods, missing exception work counters, and inappropriate summation of depth/order state counters. These were corrected and disclosed before any method execution. The final tail update also removes repeated prefix fsum/array reductions: it uses constant-time rejection-only partial accumulation, then one complete fsum before acceptance. Final source hashes were independently checked before root's single invocation.

After execution, the reviewer read every saved delivery in both JSONL and aggregate JSON, the attempt/execution/setup records, stdout/stderr, inherited inputs/references and root's saved-data-accounting JSON. Additional computation here used standard-library parsing, hashing, integer/floating arithmetic and counter aggregation only. No delivery function, integrator, benchmark module, NumPy import, Gaussian sample, quadrature rule or RNG was executed. No new fixture, web request, package installation, retry, Git operation or task-source change was made.

The only new repository file owned by this review is this document. Static source review cannot establish numerical reliability at the looser requested budget; the saved run demonstrates that limitation.

## Static fairness and timing checks

The finalized implementation conforms to the intended information and timing boundaries:

- The delivery API accepts exactly seven physical-parameter fields. It receives no ID, group, analytical-control label, reference RGB, previous output or acceptance list. Truth lookup and accuracy evaluation occur only in the harness after the timed call.
- Immutable tuple conversion is common input parsing outside timing. Working-array conversion, clipped masses, recognition, required sorting, bounds, breakpoints, integration, rejected shortcut work and result construction are inside each call.
- Ordinary Simpson and GL do not sort primitive means or compute original per-primitive alpha. The pair arms compute their required alpha only after common shortcuts fail; tail computes retained alpha only when its own shortcut accepts.
- All arms receive the same recognized vacuum/zero-mass/equal-color/proportional cases and the global-enclosure center shortcut. Pair early rejection checks the channelwise capped partial bound; acceptance requires completing the necessary pair scan.
- Tail deletion uses the color range including background. Its partial removed-mass estimate is used only to reject; final acceptance requires all bins and the complete removed-mass sum. Fallback uses the same continuous integrand, not an oracle replacement.
- Each arm has an independent initially empty cache, whose only mutable contents are unit-interval GL rules. No masses, order, ray decisions or outputs persist. Required lazy GL rule construction and checks are timed.
- All Simpson paths use epsilon/4, initial sliver accounting, original full cumulative extinction, the recursive endpoint guard, maximum depth 24 and 200,000 evaluations. GL uses its fixed 4/8/16/32/64 ladder and the same requested nominal budget.
- The timer stops before JSON normalization, oracle comparison, exception formatting and evidence output. Failure counters are retained. Depth/order are state values rather than additive work totals.
- The one-run stop rule is implemented: on the first accuracy failure, later schedule entries are not executed. Default invocation is plan-only.

These checks remove specific implementation unfairness; they do not establish that these three ordinary implementations cover all competitive integration/enclosure methods or that their empirical estimates are certificates.

## Schedule, records and identity

All 232 parsed JSONL records equal the aggregate records in order. The reviewer independently rebuilt the planned 2,880-entry schedule from 48 original inputs, two epsilons, five arms and six passes, including rotation by `(pass + fixture_index) % 5`. The saved data equal its exact prefix.

All recorded entries belong to pass 0 and epsilon 0.001. The first 46 fixtures completed all five arms. At fixture 47, `clipping-07`, the scheduled order was:

```
gl, tail, simple, jensen, simpson
```

GL was sequence 231 and passed; tail was sequence 232 and failed. The direct Simpson, simple and Jensen calls for this fixture were **not executed**. Thus the saved output directly establishes a failure of the shared Simpson implementation when called through tail fallback, not an observed direct-arm failure at that fixture.

The record groups are 40 control, 80 generic, 80 structured and 32 clipping deliveries. No epsilon-0.01 entry, warm pass or complete first-use batch exists. The missing count is exactly 2,648 and stays in the fixed planned denominator.

All seven before/after source/input/reference identities match the attempt, worker result, supervisor result, pre-run reviewed hashes and current file bytes. The inherited reference fixtures exactly match the original input records. Execution exited 2, with no timeout or launch error; stderr is empty and no worker-failure exception file exists. This was one T19 invocation with retries disabled.

The audit independently recomputed each RGB error, finiteness and accuracy gate against saved T18 GL64. The first 231 records pass; sequence 232 has exactly `accuracy_violation`. The summary correctly omits timing comparisons and stable-win arrays and sets `performance_comparison_admitted=false`.

## Observed failure and what it supports

The failing input has interval [0.1, 1.0], means [-0.2, 0.4], standard deviations [0.8, 0.1], full optical masses [0.2, 3.0], red/blue component colors and background [0.1, 0.2, 0.3]. The original breakpoint list is [0.1, 0.4, 0.7000000000000001, 1.0].

The tail path rejects after its first empty retained bin. Its recorded partial deletion bound is 0.055788042142784496, larger than epsilon; it invokes Simpson with the original full physical model.

| Saved quantity | Value |
| --- | --- |
| Requested epsilon plus fixed reference allowance | 0.0010000005 |
| Nominal Simpson budget | 0.00025 |
| Simpson delivered RGB | [0.025698026039792644, 0.00944006114339517, 0.9516206644697885] |
| T18 GL64 reference RGB | [0.025742841327894082, 0.00944006114339517, 0.9459369752419203] |
| Actual absolute error RGB | [4.481528810143867e-05, 0, 0.005683689227868216] |
| Reported Simpson estimated error RGB | [3.2620181491230284e-05, 0, 9.055570326495719e-05] |
| Integrand evaluations / accepted leaves / maximum depth | 23 / 5 / 2 |
| Omitted initial-segment charge | 0 |

The largest actual error is about **5.684 times epsilon** and **62.765 times the reported largest estimate**. All three initial segments were active; this failure is not an unresolvable initial sliver or missing-budget-account failure. The recorded tree counts satisfy `23 = 4*5 + 3`.

At the same input, sequence 231 refined through GL4/8/16, used 84 evaluations and delivered maximum error 2.55351295663786e-15. This is a saved ordinary-method success witness on the failed input; it is not a completed GL benchmark or a speed comparison.

The inherited T18 tighter-budget Simpson result also agreed with GL64, using 2,115 evaluations and a largest empirical estimate 4.061908672612773e-12. This historical evidence remains unchanged. Passing at 1e-11 did not guarantee that the looser epsilon/4 stopping criterion would be reliable.

The output proves that the current empirical stopping/result path delivered insufficient accuracy under this request. The saved evidence does not include recursive leaf sample values, so this audit cannot locate the exact interval or cancellation responsible or exclude all implementation details as causes. It must not claim that a new integration was performed or that every ordinary Simpson formulation fails.

## Additional saved-only conservation check

This fixture has `c_R + c_B = 1` and `c_G = 0` for every component. In the specified continuous model,

```
true emission_R + true emission_B = 1 - T(b).
```

The recorded total transmission from T18 is 0.04720030571697585, also equal to the failed delivery's green channel divided by its 0.2 green background. Both arithmetic routes give required red-plus-blue emission **0.9527996942830241**.

The failed delivery's saved red-plus-blue emission is **0.9584385682227908**. Its signed residual is **0.005638873939766698**. By the triangle inequality, at least one of those two channel errors must be at least half the residual, **0.002819436969883349**, larger than the requested accuracy gate. The necessary relation therefore independently rejects this particular result without new ray samples. The preceding GL16 delivery's residual is only 2.4424906541753444e-15.

This uses an analytical identity evaluated from saved quantities; ordinary binary64 evaluation is not a complete formal numerical enclosure. More fundamentally, a small scalar conservation residual can hide opposing channel errors. It is not a general channelwise accuracy certificate, a new accepted criterion, or a post-result change to T19's gates.

## Partial costs and actual work

These are disclosed costs of the **incomplete schedule**, including the failed delivery. They are not comparable complete batches, warm medians or speedup claims.

| Arm | Recorded | Passed | Actual timed-call nanoseconds paid | Integrand evaluations |
| --- | ---: | ---: | ---: | ---: |
| simpson | 46 | 46 | 82933300 | 4813 |
| gl | 47 | 47 | 164707200 | 11472 |
| tail | 47 | 46 | 85183900 | 4831 |
| simple | 46 | 46 | 84100000 | 4622 |
| jensen | 46 | 46 | 83158300 | 4622 |

All timed calls total **500,082,700 ns (0.5000827 seconds)**. Actual integration work totals **30,360 evaluations**, comprising 18,888 Simpson and 11,472 GL. Pair work totals 372 visited pairs and 298 pair CDF evaluations. Normal-CDF endpoint/point counters total 1,066,560 under the code's declared counting convention.

Each arm used eight shared exact deliveries in the recorded prefix; no shared global-center acceptance occurred. Tail recorded one retained-color acceptance and 38 Simpson fallbacks, including the failed one. Simple and Jensen each recorded eight actual pair acceptances and 30 fallbacks. Seven of each arm's eight acceptances are N=2 inputs; the only eligible N>=4 accepted input in this partial pass is the already known `structured-04-n4-span3`. There are no five-sample warm sets. Those acceptance counts cannot be relabeled stable timing wins.

All recorded ordinary deliveries have zero unnecessary primitive-sort/pair-alpha counters. Shared paths have zero integration/sort work. Pair visited/zero-skip/CDF counts reconcile, and every accepted pair path completes its scan. For recorded Simpson calls, evaluation/tree/active-segment counts reconcile; GL evaluation counts equal segment count times the sum of actually evaluated orders.

Only the GL arm's unit-rule cache is nonempty at termination, containing degrees 4, 8 and 16. It builds 4/8 on sequence 44 and 16 on sequence 123; recorded builds total three and moment checks total 34. Construction is inside the timed calls, with 77 subsequent rule-cache hits recorded. Other arm caches remain empty.

The saved setup times are 746,942,100 ns for module import, 28,770,300 ns for input/reference parsing plus immutable record construction, and 1,700 ns for empty-cache setup. Worker elapsed time **before final result serialization** is 1.4663567 seconds; supervisor time is **1.6210819 seconds**, including startup and final output. Nested setup/call/worker values must not be added to the supervisor interval again.

Across T17's two attempts, T18's one attempt and this T19 attempt, the recorded supervisor intervals sum to **16.857390899941684 seconds**. With the previously retained T17 runtime diagnostics, identified execution intervals sum to **25.2078446998814 seconds**. The corresponding cumulative integrand-evaluation count is **382,607**. Uninstrumented coding, input preparation, review and research time are not represented; no failed attempt is discarded as warm-up.

Root's `saved-data-accounting.json`, including every partial arm sum and its added conservation fields, was independently recomputed and matches the raw saved records.

## Decision and limits

The only valid T19 outcome is **INCOMPLETE_OR_INVALID_NO_PERFORMANCE_CLAIM_NO_RETRY**. The single-invocation budget is exhausted. No completion of the interrupted schedule, repaired invocation, tuned tolerance or subset-only performance argument belongs to T19.

The predefined stable-win condition cannot be evaluated because no warm samples exist. It is incorrect to report either a measured stable win or a measured absence of wins, or to apply the scientific no-win closure rule to this implementation/accuracy failure. Likewise, the common Simpson fallback failure does not falsify the analytical pair bounds, vindicate Jensen over simple, or establish an unsolved renderer problem.

The useful new evidence is narrower: the delivery-level accuracy contract caught a failure that its empirical error estimate missed; the same-case ordinary GL route succeeded; and a saved-only necessary conservation relation also rejects this output. Any later task needs a separately fixed rationale and budget. This review neither authorizes retrying T19 nor turns the engineering issue into a TOG contribution.

## Follow-up scope review

The published T19 README correctly distinguishes incomplete numerical delivery from a scientific no-win result. Its T20 preparation proposes a bounded ordinary accuracy-contract/source audit, not a replacement T19 execution: one previously identified Cornell primary family, at most one metadata access and two full-text attempts, at most 32 inspected pages, no new integration or timing. This is a concrete remaining gap because T17 did not obtain that full text and an empirical indicator has now failed the delivery contract.

The planned distinction among necessary conservation, empirical differences and sufficient local enclosures is appropriate. The constant-color decomposition is an identity, not a residual-error guarantee or a new contribution. A successful mapping may justify preparing a separate qualification protocol; unresolved access or semantics must remain unresolved. No architecture expansion or fabricated favorable workload is justified by T19's failure. The finalized preparation explicitly retains the two earlier T17 HTTP-429 full-text failures separately from newly budgeted attempts, rather than resetting source history. T20 itself remains unexecuted at this review.

## Sealed evidence identities

Paths are repository relative. SHA256 hashes were recomputed from the actual files; the JSONL content was also compared record by record against the aggregate.

| File | Bytes | SHA256 |
| --- | ---: | --- |
| `tracks/tog/tasks/t19-complete-cost/PROTOCOL.md` | 8296 | `1b718de439eff6fade61ca55b899e9974c8246fc3c0fe287ca3b3acee9ecc5e0` |
| `tracks/tog/tasks/t19-complete-cost/benchmark.py` | 19861 | `1537cb8f1e329a3ad232f8cc4e4d9f6d16c93553466f7cf6c3e16ffeb75243be` |
| `tracks/tog/tasks/t19-complete-cost/methods.py` | 14536 | `2369efea4f60d4cf546f926b9b6322bfa12a4109fa1332b92f2b22f94779ecb2` |
| `tracks/tog/tasks/t19-complete-cost/integrators.py` | 16091 | `94c6ab6748c42c40c8446ec5af01adf3b7b4ff66a6a45f7f9aba26bc651113af` |
| `tracks/tog/tasks/t19-complete-cost/run-01/attempt.json` | 2429 | `631dbd80eddf67ed56b4be75ba5f4cef860b03162c3d0d0e281748bb45651b25` |
| `tracks/tog/tasks/t19-complete-cost/run-01/execution.json` | 4597 | `d5c39de1e028a669e2e7859c4d0c1c47c7a792d2c3ee3de0289518707ea53599` |
| `tracks/tog/tasks/t19-complete-cost/run-01/results.json` | 529135 | `7002bc85badaddab89fe074106b331bd5f29b527d4bc678b56c7458289f2ddd9` |
| `tracks/tog/tasks/t19-complete-cost/run-01/deliveries.jsonl` | 374668 | `fbe0b3aeac265745a7604e1669848449d742ae7e2ed30ad5a042bb9540ac96b5` |
| `tracks/tog/tasks/t19-complete-cost/run-01/setup.json` | 459 | `955224ce00b2a6bab791ed39bf86c349166b3b4746a3e512667c4e275e1152e5` |
| `tracks/tog/tasks/t19-complete-cost/run-01/worker-stdout.log` | 253 | `d1130543731f51cbb7e47aa3a9b9b8e8ed30e1c56627f87ce1d87ae00de380a8` |
| `tracks/tog/tasks/t19-complete-cost/run-01/worker-stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `tracks/tog/tasks/t18-reference-robustness/NEXT_EVIDENCE.md` | 11065 | `e0c420eb663c09d4eb1ae041253c7561cd154227a3db23fe87dcf133c599aec2` |
| `tracks/tog/tasks/t18-reference-robustness/run-01/results.json` | 4682658 | `fa4fb6887c6b38e800f18e919634821b3ee51c2fb0122cd0dbb4047eead7873d` |
| `tracks/tog/tasks/t17-order-inversion-bound/inputs.json` | 72396 | `5cccf0238c679e14bc50e67d2d24726a58295b484b1d3464bf77d4eca0491cb7` |
| `tracks/tog/tasks/t19-complete-cost/saved-data-accounting.json` | 10535 | `5e30f184672d1617205050afdee31cdb334db9bd0eccb9d90419a25d077e7c5e` |
| `tracks/tog/tasks/t19-complete-cost/README.md` | 6547 | `566aa92d39bbc1cb4da8d6018379d59545531fce40a2e61eae67ce125f1b6e25` |
| `tracks/tog/tasks/t19-complete-cost/NEXT_EVIDENCE.md` | 5066 | `624ad9105efdb775892bf2690a4cac7de9ed49d12a5df1b3a3a5d3a7ada6015c` |
