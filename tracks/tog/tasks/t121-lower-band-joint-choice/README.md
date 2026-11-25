# T121 · Can either brush reach the lower-band shot target?

On the frozen lower-band Playground edit, **neither available brush met the two cameras' targets**. The lighter brush directly lit 920 sites and the heavier one lit 1,504. Both cameras had a measurable target. The outer shell contained 8,621 eligible sites accounting for 1,223.864 effective foreground pixels in view 76 and 2,339.193 in view 230. Across 90 frames, neither simulation ignited any of those sites. Each camera returned `none` after trying both treatments. The task was defined by the researchers. [Input chosen before geometry](../t120-next-release-registration/PROTOCOL.md) · [Frozen methods and decision rule](PROTOCOL.md) · [Independent per-frame curves](REFERENCE.json)

The solver remained active elsewhere. Outside the initially ignited sites, both trajectories acquired 3,830 new ignitions with exactly the same ordered IDs in every frame. The heavier brush initially added 584 sites outside the shell. None ignited naturally under light during this interval. Those sites therefore did not test the algorithm's handling of a later light-branch birth already inserted by full. [Per-frame onset attribution](PREFIX.json) · [Native light ledger](evidence/native/AL-trace.json.gz) · [Native full ledger](evidence/native/AF-trace.json.gz)

## What the transport proves here

The initial donor and emitter frontier remained sufficient for the full 90-frame query under the registered guard. The sibling operation simulated 90 light frames, saved 1,360,391 typed material bytes and 3,975 particles plus other branch state at the deadline, reconstructed the full-brush material state there, and executed zero additional full gas steps. At frame 270 the reconstructed full state matched the original T86 native observer's full fingerprint (including ordered material arrays, frontier, gas, counters and clock). The complete native reference also reproduced the parent and all 360 frames of each physical branch in the process workers. These are numerical state and decision checks; the readout measures static foreground opacity attributed to newly burning material. [Boundary and source-state record](PREFIX.json) · [Independent physical precheck](evidence/physical-precheck/CAPTURE.json) · [Original calibrated readout](../t107-visible-burn-progression/measure.py)

A simpler query-specific baseline follows directly from this case. When a pre-click nested-brush guard certifies the full horizon, the extra direct sites lie outside the query shell and both branches share its entire ignition curve. After observing light, a query can reuse that output for full and omit reconstructing the heavier physical state. Computing the full candidate footprint, checking the guard, reading the first outcome and restoring the editor still carry costs. The three-way comparison below measures full-state transport against ordinary replay and chronological regional repair. It provides no measured advantage against this output-only shortcut. The earlier Firewoods and upper Playground examples had certified prefixes of 24 and 16 steps, respectively, below the 90-step deadline. [Guard and action implementation](../t119-cross-sibling-actions/sibling.js) · [Earlier shot decisions](../t119-cross-sibling-actions/README.md)

## Delivered cost

Each entry is the median warm host-delivered latency in milliseconds, over six calls to the same method in that process. The timer includes all attempted treatments and returns the restored editor parent. All 84 delivered actions (12 cold and 72 warm) and all four sets of forced complete light and full curves passed their checks. The ratios compare process medians.

| Fresh process | Ordinary | Chronological repair | Sibling transport | Sibling / ordinary | Sibling / repair |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 1128.2 | 784.8 | 572.2 | 0.507 | 0.729 |
| 2 | 1111.2 | 811.2 | 568.9 | 0.512 | 0.701 |
| 3 | 1107.8 | 789.2 | 560.4 | 0.506 | 0.710 |
| 4 | 1100.4 | 792.1 | 563.9 | 0.512 | 0.712 |

Both comparisons met the registered gate (ratio <0.90 in at least three processes and <1.0 in every process). First-use costs ranged from 1130.6 to 1246.6 ms for ordinary, 817.1 to 839.8 ms for repair, and 588.1 to 595.6 ms for sibling transport. Pre-click shared setup and static projection are reported separately. The two camera projections took 1.81 and 1.70 seconds. Four independent processes repeat one held-out edit on a previously examined fitted asset. [Raw warm and cold rows](SCORE.json) · [Corrected captures](evidence/corrected/) · [Projection cost](projection-cost.json)

## Reproduction

To check the committed results from this directory using Python's standard library, run:

```text
python reference.py
python prefix.py
python score.py
```

To reconstruct the original PLY and camera member by range, follow T120. From this directory, `python prepare.py` reruns the two calibrated static projections with NumPy. Run `node capture.mjs /path/to/fresh-native-output` for independent native ledgers. The T111 compiled action and T116 cold-grid plugin must be built as described in T119. To repeat the whole comparison without overwriting receipts, use a separate checkout at `c1ee57a`, stage the input members and generated plugins there, then run `node run.mjs --verify 1` before `node run.mjs`. The four fresh browser/Node processes use the order and repetitions in the protocol, with all three competing kernels frozen in the same T119 plugin. [Limited data acquisition](../t120-next-release-registration/README.md) · [Plugin dependency chain](../t119-cross-sibling-actions/README.md) · [Process driver](run.mjs) · [Scorer](score.py)

The first process exposed a clock omission in the newly written native audit adapter, which produced a different particle fingerprint despite matching threshold decisions. Its costs were discarded and its receipt is archived. The corrected physical check calls the original T86 observer. It passed separately before the four new timing processes began. [Failure and diagnosis](AUDIT_FAILURE.md) · [Corrected observer](audit.js)
