# T18 independent saved-array and budget review

29 October 2026. Reviewer: pressure_screen. This reviews the separately budgeted T18 invocation, not a third T17 attempt. **The saved T18 run qualifies all 48 frozen cases under the inherited numerical gates.** T17 remains 41/48 with its native-initialization failure and seven adaptive-reference failures retained.

This is a reference robustness result. The same one eligible case is informative at both fixed thresholds, and the simple bound already passes it. No new Jensen-only success, speed advantage, floating-point certificate, novelty claim or TOG core contribution follows.

## Scope and method

Read T17 NEXT_EVIDENCE, the sealed T17 protocol/source/input/result, T18 protocol/source, attempt/execution metadata, aggregate result, all 48 per-case checkpoints, progress/output logs and saved quadrature rules. Root confirmed its and volume_screen's source review preceded execution; those reviews were agent messages, not an additional static-review file. This reviewer independently inspected the actual source and saved arrays after execution.

All additional computation here used standard-library JSON, hashing, Fraction and scalar closed-form arithmetic. No NumPy import, qualification-module import, ray-integrand call, quadrature execution, input generation, RNG reseeding, new fixture, web request, Git operation or task-file change was performed. The only new repository file owned by this review is this document.

The review independently reconstructed each segment's floating-point midpoint/quarter-point trigger, exact rational width and envelope, directed rounding and allocations. It also recomputed the saved closed-form masses, sorting/compositing, all pair quantities, controls and comparison gates. It does not reconstruct unsaved recursive sample values or independently integrate the rays. Exact accounting of stored empirical estimates is not proof that Simpson estimates bound its true error.

## Identity and immutability

- All 48 unique fixtures, in original order, equal T17 input records: 8 controls, 16 generic, 16 structured and 8 clipping; 399 primitive entries and 3,272 pairs. No new cases were generated.
- The 48 parsed checkpoint records equal the 48 aggregate records. The 48 progress entries have the matching indices/IDs and passed status; stderr is empty and no worker-failure file is present.
- All five source/input identities equal their before-worker, after-worker and supervisor records and the current file hashes. The input, inherited source and original protocol equal the predeclared pins.
- For every case, all 20 non-reference scientific fields equal T17's saved run-02 fields exactly: fixture/order/masses/alpha/transmission, ordered RGB, global/simple/Jensen bounds and pair sums, every pair record, breakpoints/segment count, analytical color and the red/blue analytical error. This gives 960 whole-field comparisons.
- GL32 and GL64 records equal T17's records exactly after excluding elapsed time. The quadrature-rule JSON is byte-identical, including all nodes, weights and diagnostics. No GL order or construction changed.
- A separate scalar rederivation checked 37,825 closed-form scalar quantities, including all 3,272 pairs, clipped masses, original sorted output and analytical controls. Maximum numerical difference from saved values was zero in this environment. This is closed-form arithmetic, not additional ray integration.

Static inspection confirms the only inherited function binding replaced is `adaptive_simpson`. The original Integrand still evaluates cumulative extinction from the original interval start using every primitive and its entire analytic density integral. T18 does not delete a primitive's extinction when it omits emission on a small initial segment. Returned RGB includes the original total-transmission background term.

## Exact rational omission and budget account

All 988 original segments were checked; 978 were adaptively integrated and 10 were omitted with a charge. The omitted segments occur in exactly the seven rays whose T17 Simpson reference failed. Their triggers are actual equalities of the original binary64 midpoint/quarter-point operations, not an epsilon threshold or breakpoint merge.

For each segment, the reviewer recomputed

```
width = Fraction(right) - Fraction(left)
rate = sum(Fraction(weight_i) / Fraction(sd_i))
U = width * rate
```

from the stored binary64 values, checked every numerator/denominator, and independently verified the upward-rounded charge. For the 978 active segments, it checked exact active-length sums, downward-rounded length-proportional allocations and their exact sum. Across every ray:

```
recorded_charge_total + sum(recorded_allocations) <= Fraction(binary64(1e-11))
```

holds. All remaining budgets and required allocations are positive. The smallest remaining budget is **9.996003197111349e-12**. All 48 global budget checks pass.

| Ray | Omitted segments | Sum of rounded segment charges |
| --- | ---: | ---: |
| control-05-equal-color | 2 | 2.6645352591003757e-15 |
| structured-03-n4-span1.2 | 1 | 1.9984014443252818e-15 |
| structured-07-n8-span1.2 | 1 | 1.9984014443252818e-15 |
| structured-11-n16-span1.2 | 1 | 1.9984014443252818e-15 |
| structured-12-n16-span3 | 2 | 3.9968028886505635e-15 |
| structured-15-n32-span1.2 | 1 | 1.9984014443252818e-15 |
| clipping-06 | 2 | 2.5188184871183239e-15 |

The largest individual segment charge is **1.9984014443252818e-15**; the largest per-ray total is **3.9968028886505635e-15**. Across all ten segments in seven different test rays, the sum is approximately **1.717376241217039e-14**. This cross-ray total is disclosure only; the error budget is separately per ray.

Eight omitted widths are 2.220446049250313e-16; clipping-06 additionally has widths 5.551115123125783e-17 and 2.7755575615628914e-17. The endpoint coordinates and exact trigger lists remain in the saved result. No other original segment is silently skipped.

The mathematical envelope is valid here because weights are nonnegative, standard deviations positive, each color channel lies in [0,1], transmission is at most one, and the normalized Gaussian density is below 1/sd. It intentionally drops the sharper 1/sqrt(2*pi) and color factors. It bounds only the selected omitted emission in real arithmetic.

The reviewer also summed every saved per-segment empirical-error Fraction, verified each segment's estimate does not exceed its allocated budget, verified the recursive and combined aggregates, and verified upward-rounded returned estimates. The largest returned combined estimate is **4.061908672612773e-12**, below 1e-11. Segment emission sums plus the unchanged background exactly reproduce the saved adaptive RGB. Evaluation counts agree with the full binary refinement-tree relation `evaluations = 4*accepted_leaves + active_segments`; observed maximum depth is 9 and each ray stays within 200,000 evaluations.

The all-original-segments-unresolvable branch and underflow/insufficient-budget failures were inspected in source but are not exercised by these 48 fixtures. Later recursive endpoint collisions still fail; no recursive rescue or post-run repair was added. Gaussian CDF evaluation, Simpson's error estimator and ordinary binary64 RGB arithmetic remain outside a rigorous floating-point certificate.

## Numerical gates and opportunity counts

The reviewer recomputed all saved RGB differences/slacks, analytic and red/blue-control comparisons, finiteness, reference agreement, Jensen-versus-simple checks and global budget gates. All references return results and all 48 pass; no subset substitution is needed.

| Quantity | Largest observed value | Fixed allowance |
| --- | ---: | ---: |
| Any pair of reference RGBs | 7.671641100159832e-14 | 5e-10 |
| Reference versus analytical control | 2.55351295663786e-14 | 5e-10 |
| Observed error minus a tested bound | 5.440092820663267e-15 | 1e-9 |

These are empirical values on this frozen array. The tiny positive bound excess is below the fixed tolerance; it is not a claim of exact floating-point nonviolation. Shared-integrand agreement also does not substitute for an independent physical-model validation.

There are **28 eligible, numerically qualified** non-control cases with at least four primitives. At both 0.001 and 0.01, the sole informative case is `structured-04-n4-span3` for **both** simple and Jensen variants. The seven recovered references add no informative case. Jensen adds **zero** successes over simple at either threshold.

## Attempts, evaluations and complete disclosed timing

There was one supervised T18 invocation, with exit code 0, no timeout, no launch error and stable identities. It is cumulative full-qualification invocation **3**, not a reset history. T18 had no repair/re-execution allowance and none was used.

| Stage | Supervisor seconds | Worker seconds | Outcome |
| --- | ---: | ---: | --- |
| T17 run-01 | 6.061168999993242 | No completed worker timing | Native initialization exit 3228369023; zero cases |
| T17 run-02 | 3.85225450003054 | 2.843802500050515 | Exit 2; 41/48 qualified |
| T18 run-01 | 5.322885499917902 | 4.203987000044435 | Exit 0; 48/48 qualified |

The three supervised intervals total **15.236308999941684 seconds**. The four retained T17 runtime diagnostics total **8.350453799939714 seconds**, including the failing isolated leggauss initialization. Combined identified execution intervals total **23.5867627998814 seconds**. The failed attempt and diagnostics are not called warm-up.

T18 contains 83,182 adaptive evaluations, 31,616 GL32 evaluations and 63,232 GL64 evaluations: **178,030** total. Including T17's 174,217 evaluations, some from failed partial references, the cumulative count is **352,247**.

T18 saved per-reference wall sums are 1.8116773999063298 seconds for adaptive Simpson, 0.7070615001721308 for GL32 and 1.3892578997183591 for GL64. The 48 case wall intervals sum to 3.9388885002117604 seconds. These nested values are already inside worker/supervisor time and must not be added again.

Input generation, earlier environment probes, coding, review and research wall time are not comprehensively instrumented. The 23.5868-second total is therefore the identified execution history, not end-to-end research cost. There is no separately timed complete method comparison or bound-only speed claim. The additional exact Fraction bookkeeping and mandatory references also prevent reading these task-run durations as renderer performance.

## Decision

T18 satisfies its limited robustness and empirical qualification prerequisite on the original data, while preserving the negative T17 record. The fixed decision admits **preparing** a separate complete-cost protocol because the one informative case remains. It does not admit a hierarchy, splitting policy, tile reuse, new scene or renderer work within T18.

A later comparison must offer ordinary methods the same parameters, breakpoints and recognized analytical/global-range/tail-truncation shortcuts, count the cost of actually delivering a color and retain all dense/opaque cases. Simple versus Jensen must remain visible. Whether any useful total-cost region exists is unresolved. Passing this engineering prerequisite is not evidence that a TOG contribution has been established.

## Sealed evidence identities

Paths below are repository relative. These hashes were recomputed while reviewing the saved artifacts.

| File | Bytes | SHA256 |
| --- | ---: | --- |
| `tracks/tog/tasks/t18-reference-robustness/PROTOCOL.md` | 7501 | `e510ef0970b35a2bfb5e87a34e152bcc3b5a63582667bcde613afad5481d05b4` |
| `tracks/tog/tasks/t18-reference-robustness/qualification.py` | 22528 | `397ad0684a0a701d27471fab41c7bc604b95da4e79ef34c557cdf2edea0e6c74` |
| `tracks/tog/tasks/t18-reference-robustness/run-01/attempt.json` | 1986 | `e576b9b43a0c1d23c19500a56ac2270fd4ffa967c1933756e2e1b10ea1b06329` |
| `tracks/tog/tasks/t18-reference-robustness/run-01/execution.json` | 3516 | `1a982ef62ac5e4e749a90e369d3e7ab65c5aec90b95908eb0348776aee34b5e8` |
| `tracks/tog/tasks/t18-reference-robustness/run-01/results.json` | 4682658 | `fa4fb6887c6b38e800f18e919634821b3ee51c2fb0122cd0dbb4047eead7873d` |
| `tracks/tog/tasks/t18-reference-robustness/run-01/quadrature-rules.json` | 11836 | `886349f4d1ed63221a3afd317bbe5e4ab13532054f293207281135d5b1669375` |
| `tracks/tog/tasks/t18-reference-robustness/run-01/progress.jsonl` | 5934 | `39b59014373411cf9525bf302f14a4272d816e795fe0bd4914ef742f17114738` |
| `tracks/tog/tasks/t18-reference-robustness/run-01/worker-stdout.log` | 1878 | `f65498eaf872d0a9949a3918810fd657d6e065c26b620df97954dd2eb8908f59` |
| `tracks/tog/tasks/t18-reference-robustness/run-01/worker-stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `tracks/tog/tasks/t17-order-inversion-bound/NEXT_EVIDENCE.md` | 6770 | `9a4b173fe3919d9b816c2284102b7d43df8c7116a5224e2877e96ab3fad641a4` |
| `tracks/tog/tasks/t17-order-inversion-bound/inputs.json` | 72396 | `5cccf0238c679e14bc50e67d2d24726a58295b484b1d3464bf77d4eca0491cb7` |
| `tracks/tog/tasks/t17-order-inversion-bound/qualification.py` | 33223 | `d648567e27b030c454ba37fdbee11b0df1b7de6b9e2a78c10a66cc0031557831` |
| `tracks/tog/tasks/t17-order-inversion-bound/PROTOCOL.md` | 8118 | `4c631c90d08d1e5b9ac19ebc6e52cbd2c902c267af105ccbedeb1cccc292586c` |
| `tracks/tog/tasks/t17-order-inversion-bound/run-02/results.json` | 2276326 | `63203cad05febfad1adf5c1a56a3341a61dbd7489110f46e0fc7b012ba5d95d2` |

All 48 per-case checkpoint hashes are summarized by SHA256 **`f74f887c5620b70b303deeb4e1eb1bb3861c4bf96aba2bb2be71156f05da9bc5`**, defined as the SHA256 of the UTF-8 concatenation, in filename order, of `filename + TAB + lowercase_file_sha256 + LF`. Their parsed contents were also compared individually against the aggregate. The unchanged T17 quadrature-rule hash is shared by T18.
