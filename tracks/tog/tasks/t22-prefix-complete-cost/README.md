# T22 — one local prefix cost win, small whole-workload benefit

29 October 2026. The sole invocation completed **all3648 accurate deliveries**:192 ordinary qualification calls followed by3456 six-arm cost calls. The primary Jensen-prefix hypothesis meets its fixed local gate on exactly one added ray, `structured-08-n8-span3` at epsilon .01. Its median delivery is174.0 microseconds versus2032.8 for direct GL, with all five subsequent timing ranges separated. Across the entire96-case/epsilon workload, however, the primary median is only1.37% below GL and0.46% below signed simple, with overlapping ranges. This is a local development observation, not broad speedup, novelty or a TOG core contribution.

## Fixed operation and fair comparison

The [binding protocol](PROTOCOL.md) executes T21's previously prepared contract on exactly the original48 researcher-authored rays and epsilons(.001,.01). The operation remains the continuous overlapping colored-emission integral. An ordinary method may return any accurate color; it is not forced to reproduce the candidate's sorted RGB.

All arms share parameter-recognized exact cases and the G/2 global-center shortcut. They independently prepare their own ray parameters and optical masses. Direct GL performs no unnecessary sorting. The six arms are direct GL, ordinary disjoint-bin deletion then GL, signed-only simple/Jensen then GL, and combined prefix/signed simple/Jensen then GL. Only unit-interval GL rules may persist between deliveries; each arm has its own cache. Stage A qualification and Stage B start with separate cache sets, so qualification is neither a source of free rule caches nor unreported warm-up. Initial Stage B rule use follows qualification in the same process and is not a cold-process measurement.

[integrators.py](integrators.py) is byte-identical to T19. It retains the original GL4/8/16/32/64 empirical agreement test and final Simpson fallback. [methods.py](methods.py) preserves common and tail mathematics, explicitly changes shortcut rejection to this GL path, and implements T21's fixed bounds. All four pair arms use consistent zero-term skips, downward partial sums for rejection only, and full nonnegative fsums for acceptance. Accepted prefix arms reuse their already computed prefix values in the same mathematical sorted sum; the largest observed change from T21 saved sorted RGB is1.110223e-16. This permitted reuse was fixed before execution and does not alter the accuracy threshold.

[benchmark.py](benchmark.py) holds references only for external validation/reporting. Delivery receives seven raw parameter fields, epsilon, its own rule cache and a deadline; no fixture ID, saved mass/cap, success list or oracle RGB. All preparation, clipping/CDFs, sorting when needed, bound construction, RGB output, failed shortcut work, integration and rule creation are inside the timed delivery. [supervise.py](supervise.py) supplies the external300-second cap. All15 source/input identities in [freeze.json](freeze.json) were unchanged before and after execution.

## Accuracy and the limited primary result

Every returned RGB is finite and satisfies maximum-channel error<=epsilon+5e-10 against the saved T18 GL64 reference. No new high-accuracy reference was generated. The real-arithmetic bound and finite empirical qualification are not a formal floating-point certificate.

| Stage | Completed / planned | Maximum error at .001 | Maximum error at .01 |
|---|---:|---:|---:|
| Ordinary qualification A | 192 / 192 | .0004781434 | .0073995007 |
| Six-arm comparison B | 3456 / 3456 | .0006010195 | .0073995007 |

GL terminates at order8 or16 in all recorded integration paths; its preserved internal Simpson fallback is never invoked. Qualification succeeded before any Stage B call. No exception, failed gate, timeout, repair or retry occurred.

Both prefix arms have five stable joint-delivery case/epsilon wins against direct GL and tail: the old four-label sparse witness at both epsilons and the three T21 additions at .01. Two additions already succeed with signed-only bounds. **Only the following eight-label case supplies an incremental prefix win**, with neither signed-only arm accepting in any pass.

| Delivery on structured-08-n8-span3, epsilon .01 | Five subsequent median, microseconds | Minimum–maximum |
|---|---:|---:|
| Direct GL | 2032.8 | 2013.8–2066.4 |
| Tail then GL | 2020.3 | 2008.7–2044.2 |
| Signed simple then GL | 2120.7 | 2099.4–2166.6 |
| Signed Jensen then GL | 2118.5 | 2115.3–2944.0 |
| Prefix simple | 174.2 | 169.4–185.9 |
| Prefix Jensen, primary | 174.0 | 170.0–193.8 |

The primary's worst subsequent sample beats each comparator's best, and its shortcut accepts in all six passes. The median direct-GL ratio is11.6828. Simple also passes the predeclared secondary gate; it is not promoted to replace Jensen after observing results. Neither variant gains additional accepted rays over the other. This isolated case was selected from prior development evidence, not held out; five samples in one process do not constitute statistical or hardware-independent validation.

## Complete workload costs

These totals include all48 rays, both epsilons, controls, dense cases and fallbacks. Each row is one complete96-delivery batch for that arm. Medians at the two separate epsilons must not be summed and called the median of the combined batch.

| Arm | Initial rule-use batch, ms | Five subsequent combined median, ms | Combined minimum–maximum, ms | .001 median, ms | .01 median, ms |
|---|---:|---:|---:|---:|---:|
| Direct GL | 302.7506 | 304.7900 | 303.1118–306.5661 | 152.5000 | 151.6983 |
| Tail then GL | 303.1634 | 305.0116 | 304.0938–307.7966 | 153.6042 | 151.5782 |
| Signed simple | 299.9891 | 302.0217 | 300.6117–306.0989 | 152.8419 | 149.4290 |
| Signed Jensen | 299.5780 | 303.4523 | 300.9591–308.5783 | 153.5928 | 149.8595 |
| Prefix simple | 299.0056 | 303.1917 | 300.6833–306.8649 | 155.3931 | 148.3462 |
| Prefix Jensen | 299.7749 | 300.6289 | 298.3573–303.2137 | 152.9530 | 148.2335 |

Primary versus GL reduces combined median time by1.37%, and .01 median by2.28%; at .001 it is slightly slower. Its combined range overlaps GL, and it loses to signed simple in one paired whole batch. The0.46% median difference versus signed simple is small relative to observed spread. Do not substitute the isolated11.68x ratio for whole-workload benefit. Python scalar integration, only small1D inputs and this single machine are further limits; camera/ray generation, acceleration structures, GPU behavior and production distributions were not measured.

In Stage B each signed-only arm accepts120 deliveries and falls back342 times; each prefix arm accepts126 and falls back336 times. All arms also have114 shared-path deliveries. The six extra prefix acceptances per arm are **one ray/epsilon repeated six times**, not six new cases. Actual pair visits total20,592 versus154,872 possible pairs;15,774 pair CDF evaluations and1356 early pair rejections were paid. The method still has quadratic worst-case pair work.

## Paid execution and verification

Stage A delivery time totals .6060776s in a .6168993s stage window; Stage B delivery time totals10.9137896s in11.1253260s. Imports cost .7157947s. Worker time before final serialization is12.7828944s; final result serialization costs .2258779s; the external supervisor through worker exit records13.1846729s. These are nested intervals, not amounts to add together. Full setup, validation, journal, publication and per-stage work is retained in the result and [saved-data-accounting.json](saved-data-accounting.json).

The invocation performs826,596 integrand evaluations,29,958,972 CDF endpoint/pair evaluations and24 GL-rule builds, including qualification. Separate actual exp/expm1 categories total15,779,888 and30,101 calls. Historical alpha/saturation/attenuation counters are aliases, and are not added again to those totals. Reused-prefix composition accounts for720 nonzero components without duplicate composition exponentials. No new input, reference integration, source query, installation, GPU work, scene or art production occurred.

[Pre-execution independent review](../../../validation/t22-preexecution-review.md) checks the method, timing boundary, schedule and external cap. [Post-run independent audit](../../../validation/t22-cost-review.md) recomputes all3648 record identities, schedules, RGB errors,96 case/epsilon comparisons, group/batch totals and fixed win gates without importing methods or rerunning integration. All1848 non-common pair decisions match T21, and all492 completed bounds match its saved values exactly. The audit verifies separate cache/rule costs and the complete journal/result correspondence.

The [complete result](run-01/results.json.gz) is losslessly compressed:7,156,119 original bytes become366,976 published bytes; decompression exactly restores the authenticated raw result. [publication-storage.json](run-01/publication-storage.json) records both hashes. Raw results and the duplicate journal remain local and ignored; all3648 complete records are published in the gzip, not replaced by selected statistics. [audit-manifest.json](audit-manifest.json) identifies every publication and unchanged historical artifact.

## Decision and reproduction

The pre-result primary gate passes on one development ray, so retain a **local incremental cost observation**. The modest whole-workload effect does not justify another tightening variant, favorable scene, hardware claim or renderer architecture. The [next finite audit](NEXT_EVIDENCE.md) is prepared only: check model/prior-method/official-asset compatibility in the already identified Vol3DGS and Hybrid Transparency families before considering real-workload applicability. No T23 source access or code has run here.

T19 remains failed at232/2880; its stable wins are still NOT EVALUATED, and none of its timings were pooled. T20's source mapping and all historical gates remain unchanged. Main and art are untouched; the research goal remains active and no SIGGRAPH/TOG contribution is established.

```sh
# Default command is plan-only; no method executes.
python -I -B -X utf8 tracks/tog/tasks/t22-prefix-complete-cost/supervise.py

# Reproduction syntax only: this completed T22 task permits no second invocation.
python -I -B -u -X utf8 tracks/tog/tasks/t22-prefix-complete-cost/supervise.py run --out NEW_DIRECTORY
```

Use the pinned source/input identities and existing NumPy environment. Read the published result with Python's standard-library gzip.open and json.load. No package installation, automatic retry or input-generation command is provided.
