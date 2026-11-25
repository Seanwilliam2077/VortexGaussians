# A callable exact regional ignition question

Starting from a loaded simulation checkpoint, the caller asks whether currently cold, fuel-positive material in the shell around the second brush ignites in the next 1, 4 or 8 frames. A positive answer includes its first frame and a native witness ID. The function restores the caller's state before replying. Every one of the 2,016 calls on two assets returned the reference answer and a valid witness when needed. Reference continuation passed all 1,440 native frames' onset IDs, counts and RNG-draw counts, all checkpoints and both pairs of final state hashes.

## Exact native controls

`full` checks shell membership during the ordinary ignition scan and completes the first event step (or the final requested step). `trim` returns from material simulation as soon as the first regional witness is found, or at the end of the last requested scan. `regional` additionally restricts terminal-step flame deposits and ignition tests to the region on the known last requested frame. Earlier frame hits return immediately from its native scan. These modes share a static shell index and dynamically check native eligibility.

The JavaScript function executes inside the current simulator. For destructive execution, it copies mutable material, particle and RNG state and restores the live references afterward. The native scratch tree is rebuilt on the next step under the verified controls. One pure T91 positive (or H=1 negative) avoids copying the branch. Shell-index construction and geometric setup are one-time costs for the fixed authored brush. The result times include native stepping, checking region membership, cloning and restoration when needed, materializing a Boolean/first frame/witness, and the browser/Node Playwright round trip. They exclude asset load, replaying the initial prefix, one-time index construction and the offline validation. These are single-host automation round trips with the calculation and state in one browser process. Browser-only, compute-only, branch copy, rollback and setup times are separately recorded. Measuring an editor click before obtaining the cut would require additionally charging its setup/replay path.

## Paired measurement

One warm-up and seven measured calls per method and window. On each window the seven methods each occupied every order position once during measurement. The table gives the median of within-query medians in ms, followed in parentheses by the median paired delivered-time ratio to regional. Ratios can differ from a quotient of table medians. Windows overlap; repeats do not supply additional scenes. [Firewoods](evidence/firewoods/SCORE.json) · [Dead Tree Trunk](evidence/dead-tree/SCORE.json)

| Method | Firewoods, 18 queries | Dead tree, 18 queries |
| --- | ---: | ---: |
| Full native step | 30.32 (1.528) | 37.40 (2.222) |
| Trim native step | 18.56 (0.979) | 14.45 (1.015) |
| Region-targeted native | 19.17 (1.000) | 14.05 (1.000) |
| [T91 bounded one-step heat](../t91-sampled-heat-witness/PROTOCOL.md) with fallback | 20.01 (1.022) | 15.75 (1.020) |
| [T93 selective exact terminal gas](../t93-exact-terminal-gas/PROTOCOL.md) | 17.41 (0.918) | 13.64 (0.947) |
| Survivor-rank-only selection | 17.06 (0.897) | 13.70 (0.978) |
| All carriers | 19.06 (0.998) | 14.14 (0.997) |

For H=1, the paired selective/regional ratios were 0.424 and 0.348 across six cuts per asset. H=4 gave 0.945 and 0.988; H=8 gave 1.009 and 0.981. Terminal selection has greatest leverage before any preceding steps need to complete. T91's direct answers occurred on six and five windows; including its failures to decide, its median paired time exceeded ordinary replay on each asset. Spatial pruning versus rank-only does not show a uniform gain. Agent-designed tasks on one reconstructed asset and one mesh-derived material asset do not establish general creator utility. Total scientific worker wall times were 67.712 s and 84.035 s, including browser initialization, all queries and validation. All results were observed before choosing any further algorithm for these data.

## Reproduce

Run `python score.py firewoods` and `python score.py dead-tree` from this folder. These standard-library checks independently recover expected events from the public ledgers and verify all warm-up/measured outcomes, order balance, stable counters, checkpoint/endpoint receipts and derived timings. [Firewoods raw calls](evidence/firewoods/CAPTURE.json) · [Transfer raw calls](evidence/dead-tree/CAPTURE.json)

To regenerate on the pinned native runtime, prepare the Firewoods PLY and [the transfer PLY](../t92-transfer-workload/PROTOCOL.md), build the T93 browser plugin using its `build.mjs`, and run the following from the repository root with a fresh output path. Use Node and Playwright/Edge matching the pinned T86 runtime. For transfer also supply `--asset`, `--recipe`, `--reference` and `--traces` from the T92 task (respectively `local/scene.ply`, `recipe.json`, `evidence/capture-report.json` and `evidence`).

```shell
node tracks/tog/tasks/t90-callable-regional-query/profile.mjs --out fresh-profile --methods full,trim,regional,t91,t93,rank-only,all-carriers --plugin tracks/tog/tasks/t91-sampled-heat-witness/estimate.js --plugin tracks/tog/tasks/t93-exact-terminal-gas/local/plugin.js --repeats 7
```

[First protocol](PROTOCOL.md) · [Joint protocol frozen before either measurement](JOINT_PROTOCOL.md) · [Native callable](query.js) · [Measurement driver](profile.mjs)
