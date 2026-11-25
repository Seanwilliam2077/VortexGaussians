# Exact checkpoint reuse across two alternative brush strokes

The delivered action compares two real strokes at the same edited state in two existing calibrated shots. A lighter stroke runs first. When it misses the shot’s quarter-opacity target, a previously saved state can be turned into the heavier brush’s state, and its simulation can continue from there. Every method returns the selected stroke per camera, the earliest crossing, cumulative count, opacity and a contributing site, then restores the live parent. A joint request evaluates both cameras against one physical future for each attempted stroke. [Frozen protocol](PROTOCOL.md) · [Action integration](sibling.js) · [Native transport](../t118-sibling-native-transport/README.md)

## Decision and work

On Firewoods, the light brush missed by step 90 and the full brush crossed at +44 for the primary camera. Neither brush qualified in camera 124. The sibling calculation executed all 90 light steps, read the exact +24 checkpoint, then executed 20 full steps for camera 0 or 66 full steps jointly. Its checkpoint contained 589,679 typed material bytes and 2,974 gas particles, plus the ordered frontier and other branch state. It prepared 288 brush sites and reconstructed the 214 additional sites. On Playground, the two views accepted light at +53 and +76. The sibling calculation still prepared all 2,058 full-brush sites and saved a +16 checkpoint with 1,360,391 typed material bytes and 2,273 particles. Neither Playground request reused that state. [Parent-only qualification](../t117-sibling-prefix-transport/README.md) · [Original shot choices](../t111-playground-shot-choice/README.md)

## Delivered times

Warm host-delivered median milliseconds, displayed in process order.

| Scene / process | Cameras | Ordinary | Repair | Sibling | Cold ordinary | Cold repair | Cold sibling |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Firewoods 1 | 0 | 728.2 | 596.1 | 623.9 | 600.3 | 566.5 | 516.2 |
| Firewoods 1 | 0, 124 | 1020.5 | 852.9 | 1038.2 | 869.6 | 781.8 | 768.1 |
| Playground 1 | 0 | 365.4 | 349.2 | 367.9 | 297.3 | 279.7 | 299.9 |
| Playground 1 | 0, 153 | 565.1 | 566.6 | 558.4 | 451.7 | 439.3 | 449.4 |
| Playground 2 | 0 | 365.7 | 358.1 | 375.6 | 294.6 | 289.7 | 298.7 |
| Playground 2 | 0, 153 | 591.3 | 572.0 | 560.4 | 455.9 | 444.2 | 466.8 |
| Firewoods 2 | 0 | 1065.9 | 809.6 | 891.1 | 813.9 | 859.7 | 736.1 |
| Firewoods 2 | 0, 124 | 1785.4 | 1383.5 | 1694.2 | 1495.6 | 1304.9 | 1332.6 |

The six columns vary the time integration algorithm and flame-contact lookup. Ordinary uses the full active material solver. Repair projects and reconstructs material in chronological order. Sibling performs full-state evolution and shares the certified prefix across treatments. Cold denotes the T116 spatial index for currently cold material; all three receive it. Six warm calls per cell cover all six method-order positions once. Each row is a median within a fresh process. Within-scene estimates come from two processes on one host. The two camera scopes and six repetitions within a process share an editor state and inputs. [Every host clock, process ratio, cold cost and mechanism count](SCORE.json) · [T116 spatial control](../t116-cold-flame-contacts/README.md)

On the woodpile primary view, cold sibling took 0.860 and 0.904 times the cold ordinary latency across the two processes, and 0.911 and 0.856 times cold repair. In the joint woodpile request it still improved on cold ordinary (0.883 and 0.891); cold repair and cold sibling exchanged the lead (0.982 and 1.021). Using the legacy lookup, sibling lost to repair in all four woodpile scope/process cells. The second Firewoods process was considerably slower for all methods; comparison of paired ratios within each independent launch is essential.

On Playground, primary cold sibling cost 1.009 and 1.014 times cold ordinary, and 1.072 and 1.031 times cold repair. The corresponding joint ratios were 0.995/1.024 and 1.023/1.051. The branch saves simulator steps only when the second brush must be considered. Eagerly preparing F and its checkpoint cost time even on the first-attempt success; the cold-sibling median F-preparation phase was 1.25–1.40 ms on Playground, with another 0.2–0.3 ms to checkpoint. These subphase timings cover a subset of the complete clock. Six warm calls per cell do not establish a population-level crossover.

## Exactness and cost boundary

All 336 complete actions, including 48 cold warmups, matched the native decision, direct brush counts, per-camera count, opacity, contributing ID and original parent. In each process both sibling backends produced the native lighter and heavier 90-frame mass/count curves. Their integrated full-stroke fingerprints matched the independently executed ordinary branch at the certified boundary, its successor, +44 and +90. The original T118 verifier also directly compared every physical array and the ordered future onset identities. Original native gas, material and RNG continued correctly to frame 360 for both branches in every process. No guard triggered fallback. These fixed cases had zero eligible exterior ignitions and zero suppressed births during their shared prefixes, so their data do not test recovery of an already nonzero exterior count. [Audit implementation](audit-worker.txt) · [Raw process receipts](evidence/)

Every delivered clock includes the parent and preview forks, measured brush actions, query setup, active index use, k calculation, any checkpoint, full branch materialization and return to the parent. The sibling also times a trial full stroke to obtain its zero-time footprint before the light decision. All backends use the same camera-level stopping rule. Static camera projection, input loading, the original parent simulation and view uploads precede the action. Both earlier Firewoods projections took about 0.8 s each, with load/write excluded. Playground reuses the T111 calibrated weight files; T119 did not time regenerating them. The receipts record decode, upload, browser launch and independent native audit times. Typed material bytes exclude gas object and other runtime allocations. [Firewoods projection costs](../t107-visible-burn-progression/evidence/cost.json) · [Playground geometry](../t111-playground-shot-choice/STATIC.json)

This is a retrospective complete-action test on one two-attempt and one one-attempt trajectory. It adds a measured condition for useful reuse. No independent production trace, artist decision, unseen geometry, prevalence estimate or guarantee on workloads outside the capped simulator was obtained. Both alternative brush sizes, views and deadlines were fixed by previous studies. [Evidence reconstruction](score.py)

Run `python score.py` here to verify the committed captures and regenerate the score with the standard library. To repeat simulation, stage the T109 Firewoods and T111 Playground inputs and the T111 compiled action, run the [T116 build](../t116-cold-flame-contacts/README.md), then run `node run.mjs --check`. The timing driver runs four serial fresh processes with `node run.mjs` in a fresh output tree. The extra native plugin is built from the pinned T116 compiler output and the original T118 material transport. [Source composition and exact digests](build.mjs) · [Process driver](run.mjs)
