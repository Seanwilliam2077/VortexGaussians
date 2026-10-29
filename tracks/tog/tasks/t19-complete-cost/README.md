# T19: complete-cost comparison stopped by an accuracy failure

29 October 2026. **The single permitted invocation stopped at delivery232 of2880.** The first231 deliveries pass their individual accuracy checks; delivery232 fails, and the remaining2648 are unexecuted. No warm pass began. There is **no admissible performance comparison**, and no retry or repaired T19 run. The pair-bound construction is neither established nor scientifically rejected by this incomplete comparison.

The active research goal continues. T17's failed qualification and T18's subsequent qualification remain unchanged. Art files and main remain unchanged; the deleted hourly automation is not recreated. No TOG contribution is established.

## Fixed comparison and actual execution

The [governing contract](../t18-reference-robustness/NEXT_EVIDENCE.md) and [pre-execution supplement](PROTOCOL.md) specify48 unchanged development inputs, epsilons .001/.01, five arms and six rotated passes. Ordinary Simpson, refined GL and direct tail truncation share analytical/global-center shortcuts with the simple/Jensen pair arms. All preparation, failed bounds and fallback are timed. Only unit GL rules may be cached; truth and fixture identifiers never reach the method API.

Static reviews found and corrected candidate-specific alpha work charged to ordinary methods, unnecessary quadratic prefix accumulation in tail rejection, missing failed-work counters and summation of nonadditive state counters. These changes preceded all T19 execution. The frozen source identities are in [attempt.json](run-01/attempt.json); they are unchanged after execution. No numerical preflight, installation, new scene, new source query, GPU work or retry occurred.

| Actual accounting | Amount |
|---|---:|
| Supervisor / worker before final serialization | 1.6210819 / 1.4663567 s |
| Module import / input-reference parsing | .7469421 / .0287703 s |
| Sum of recorded delivery intervals | .5000827 s |
| Recorded / individually passing / failing / unexecuted | 232 /231 /1 /2648 |
| Simpson / GL integrand evaluations | 18,888 /11,472 |
| Pair visits / pair CDF evaluations | 372 /298 |
| Completed first-use batches / warm passes started | 0 /0 |

These intervals are nested; do not add them as independent costs. Setup, validation and evidence IO lie outside delivery timing but within the enclosing execution. The partial arm totals and all counters are in [saved-data-accounting.json](saved-data-accounting.json); unequal incomplete workloads are accounting, not speed rankings. The supervisor records return code2 and no timeout. The shell tool exposed exit status1; the preserved worker/supervisor records describe the controlled accuracy stop, with empty stderr.

## The failure and what is known

The failure is `clipping-07`, first-use pass, epsilon .001, **tail_fallback_simpson**. Tail rejected its shortcut at the first bin and then integrated the original full continuous model. It did not return a truncated color. No initial interval was omitted, and no omission charge was incurred.

| Quantity | Saved result |
|---|---:|
| Required max-channel tolerance, including fixed allowance | .0010000005 |
| Maximum observed error against saved T18 GL64 | .005683689227868216 |
| Reported Simpson blue-channel error estimate | .00009055570326495719 |
| Actual blue error / reported estimate | 62.76456 |
| Simpson evaluations / accepted leaves / maximum depth | 23 /5 /2 |
| Immediately preceding GL16 delivery's maximum error | 2.553513e-15 |

The fallback's empirical error estimate is below its nominal epsilon/4 budget while the returned color violates the requested error. Therefore this estimate is inadequate on this fixed input at this tolerance. The failure does not establish that ordinary integration is incapable: the preceding GL arm already succeeds on the same case. The precise segment or stencil responsible cannot be identified from the saved aggregate T19 records; no new samples or rerun were used to fill that gap. The tight T18 Simpson reference used2115 evaluations and agrees with GL32/64, but those old qualification costs are not a replacement T19 delivery.

There is also an independent **necessary conservation check** using only saved output and input colors. This fixture has red and blue components with `c_R+c_B=1` and `c_G=0`. For the continuous model, with `T` the final transmission,

```text
emission_R + emission_B = integral T(t)*sigma(t) dt = 1-T.
```

The saved green channel and known nonzero green background give `T=.04720030571697585`, so the required emission sum is `.9527996942830241`. Simpson returned `.9584385682227908`, a residual of `.005638873939766698`. At least one of these two emission channels must err by at least half that residual, `.002819436969883349`, already above the original tolerance without consulting reference RGB. This post-result check rejects this result; it is not a general channelwise error certificate and has not been substituted into the sealed run. The preceding GL result obeys the same identity to approximately2.4e-15.

## Decision and preserved evidence

T19 closes as **incomplete/invalid; no performance claim; no retry**. Its stable-win rule was not evaluated. An empty printed wins list is not evidence of zero measured stable wins, and the no-win scientific closure rule is not triggered. The returned pair acceptances and incomplete cold timings cannot justify a speed claim, a favorable new scene, or an architecture expansion. The real-arithmetic T17 derivation and its sparse informative case remain limited mathematical evidence.

[results.json](run-01/results.json) contains all232 records, including the failure. The incremental JSONL is a local byte-hashed duplicate of those records and is ignored in Git. Attempt, setup, execution and logs remain published. The [independent saved-data review](../../../validation/t19-cost-review.md) verifies schedule, outputs, errors, costs, the conservation argument and source identities without importing the methods or recomputing integration. [audit-manifest.json](audit-manifest.json) records publication identities and unchanged historical artifacts.

The [next finite evidence task](NEXT_EVIDENCE.md) concerns the accuracy contract of ordinary integration and a specifically identified prior-work gap. It does not repair/restart T19 or launch another timing batch. A meaningful same-model comparison still needs accurate delivery across the full required workload; a failed empirical estimate is not the missing TOG contribution.
