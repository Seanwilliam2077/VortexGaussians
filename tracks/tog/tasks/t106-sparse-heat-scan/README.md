# A full-state ordinary control that scans only nonzero heat

In the native operator, all sites with stored heat above zero decay each step, including burning and charred sites. In twelve archived development cuts 17.4–37.8% of sites had positive heat. An ordinary bitmap implementing exactly that scan modestly reduced median delivery latency on three edits and increased it on one. Only the slowdown kept its sign in all four measured waves. Slicing still gained time on the three edits where the first regional event fell inside the initial safe block.

| Development edit and first native frame | Dense full (ms) | Sparse full (ms) | Dense slice (ms) | Sparse slice (ms) | Sparse / dense full, range across four paired waves |
|---|---:|---:|---:|---:|---:|
| Firewoods AB, 216 | 365.8 | 351.6 | 343.4 | 335.9 | 0.961 [0.813, 1.364] |
| Firewoods BA, 230 | 504.0 | 561.0 | 392.6 | 391.1 | 1.113 [1.017, 1.366] |
| Dead Tree Trunk AB, 230 | 807.8 | 746.8 | 284.9 | 298.2 | 0.924 [0.683, 1.033] |
| Dead Tree Trunk BA, 231 | 718.4 | 708.5 | 396.0 | 373.9 | 0.986 [0.907, 1.075] |

Latency includes the actual second click, shell registration, full-state fork, calculation, restoration and delivery. Each cell gives the median of four rotated waves following one warm-up. The ratio estimate uses the corresponding two medians. T102's immutable material anchor and T93's event-only terminal are identical on each side. This comparison uses the same browser run for all four methods. Absolute times across separate runs varied.

## How much work was available?

For each native deposit into a cold recipient, the bitmap records whether the resulting float32 heat is positive. Both flame and substrate graph depositions update it. On the first full or repaired material step, the implementation scans the entire branch's heat buffer, including preexisting burning/charred heat. Each later ignition scan reads bitmap words in ascending order, consumes their least significant set bit, and applies the original native decay, threshold, and frontier append. No neighbors, states, emission events, or random draws are omitted. A changed heat-array identity triggers a rebuild. During slicing, the full-state index tracks the retained original heat, and the projected copy stays separate. The sparse method is branch-local and includes a visited-site counter.

Across the archived cuts, between 3,307 and 9,482 **burning** sites had positive heat. No charred site had positive heat in these particular cuts. Positive sites occupied 81.8–98.2% of 32-site words, so the scanner can skip individual values much more frequently than it can skip entire words. The active bitmap occupied 4,336 bytes on Firewoods and 6,364 bytes on Dead Tree Trunk. Building it during an ordinary call took 0.10–0.30 ms (per-edit medians). The 36–51 scans per ordinary query visited 190,743–475,818 values. This band includes the native early witness cut, which can interrupt the last scan before its final site. [Archival counts](OCCUPANCY.json)

On Firewoods AB, repair reached 33 full heat scans on a 36-step query, including material reconstruction following guard expiries. With the same sparse backend, slice/full was 0.955. On the other three edits, the slice answered inside the safe block and performed **zero** full heat scans or bitmap builds. Their corresponding sparse slice/full ratios were 0.697, 0.399 and 0.528. Variation between dense and sparse sliced timings on these three cases cannot be attributed to a sparse heat kernel that never executed.

## Verification and reuse

All 80 timed and warmup answers matched the native first frame and eligible witness. Each arm produced eight successive complete sparse states and one additional native continuation agreeing with full native material, ordered frontier, gas fields, RNG and solver phase. At the historical Firewoods AB cut at 210, both material backends matched full native at guard expiry 212 and the next frame (hashes 99ed6f0b, a40fb6c4). The four workload queries all reached an event by H60. There are two development assets, two brush orders each, four measured waves, and no fitted-scene timing in this study. Full-state correctness, the density qualification, and the bitmap alone carry no novelty claim. [Raw paired calls and audit receipts](evidence/)

From this directory, build T93–T102 as for the [active-graph controls](../t100-material-repair/) and use the pinned browser environment from T86. The score commands read the sealed raw files.

```text
node occupancy.mjs
node build.mjs
node run.mjs --out fresh-firewoods --methods active-anchor,sparse-active,repair-active,sparse-repair --repeats 4
node run.mjs --out fresh-trunk --methods active-anchor,sparse-active,repair-active,sparse-repair --repeats 4 --recipe ../t92-transfer-workload/recipe.json --asset ../t92-transfer-workload/local/scene.ply --reference ../t92-transfer-workload/evidence/capture-report.json --traces ../t92-transfer-workload/evidence
python score.py firewoods
python score.py dead-tree
```
