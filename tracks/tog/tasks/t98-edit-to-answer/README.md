# One- and three-second queries issued with a second brush stroke

On all four edits the first eligible material site ignited within 36–51 simulated frames of the second stroke. Extending the requested preview from one to three seconds left the earliest answer unchanged on every edit. The T95 regional material solver was the fastest tested method for all three requests its whole-horizon safety check admitted. A conventional retained donor-neighbor cache won the other five, including all four three-second requests. The same-session result narrows the claim supported by the earlier four- and eight-frame previews. [Registered question](PROTOCOL.md) · [Timing schedule](SCHEDULE.md) · [Reference answers](REFERENCE.json)

## Time from second stroke to verified answer

Each cell gives median host-delivered milliseconds across six measured trials on the live, loaded scene. The returned answer identifies a material point and the absolute native frame of its ignition. Ties count all eligible sites that ignited on that first frame. The shell excludes the immediate brush contacts and is recomputed after every actual second stroke at frame 180.

| Asset and order | Horizon | Eligible points | First frame (ties) | Native regional | Rank only | T94 gas sweep | T95 material slice | Cold cache | Retained cache |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Firewoods A→B | 60 | 2,371 | 216 (3) | 642.3 | 652.1 | 647.5 | 632.0 | 374.2 | **343.3** |
| Firewoods A→B | 180 | 2,371 | 216 (3) | 651.5 | 639.1 | 673.7 | 645.7 | 412.8 | **323.0** |
| Firewoods B→A | 60 | 2,441 | 230 (1) | 1,056.5 | 1,063.4 | 1,157.4 | **357.5** | 599.3 | 514.6 |
| Firewoods B→A | 180 | 2,441 | 230 (1) | 1,153.0 | 1,089.9 | 1,320.9 | 1,177.2 | 636.6 | **552.4** |
| Dead tree A→B | 60 | 5,697 | 230 (45) | 1,837.0 | 1,862.9 | 1,868.2 | **147.2** | 547.9 | 422.1 |
| Dead tree A→B | 180 | 5,697 | 230 (45) | 1,822.7 | 1,831.4 | 1,839.7 | 1,823.5 | 530.8 | **406.2** |
| Dead tree B→A | 60 | 6,979 | 231 (17) | 1,246.0 | 1,232.2 | 1,242.6 | **200.6** | 501.7 | 407.0 |
| Dead tree B→A | 180 | 6,979 | 231 (17) | 1,241.0 | 1,270.2 | 1,273.5 | 1,259.2 | 521.9 | **423.7** |

The horizon switch isolates a cost of the proof strategy. Firewoods B→A asks for the same first ignition at frame 230 in both cases. The one-second request qualified and cost 357.5 ms, whereas the three-second request fell back and cost 1,177.2 ms. Ordinary retained-cache replay took 514.6 and 552.4 ms. Across the four requests per geometry, median paired T95/retained-cache time was 1.920 on Firewoods and 1.733 on the trunk. The ordinary cold cache also cut median paired time relative to native regional replay to 0.575 and 0.350, respectively. Fractional method times are computed on each matched request before taking their median. [Per-window Firewoods scores](evidence/firewoods/SCORE.json) · [Per-window trunk scores](evidence/dead-tree/SCORE.json)

Stroke application took 0.20–0.70 ms and shell construction 1.75–2.65 ms across the per-method, per-query medians. These costs, the disposable preview branch and restoration, the solver, answer extraction, and host delivery are included in every listed time. Establishing the two first retained caches on separate Firewoods takes cost 69.6 and 87.7 ms and allocated 6.96 and 8.92 MB of typed payload. On the trunk the corresponding values were 171.1 and 95.4 ms, 23.27 and 18.19 MB (decimal). The retained-cache column assumes these rows are already available after the warmup. The cold column includes a new graph build on each trial. Initialization of the live shot is separate. Reaching frame 180 after the first brush alone took 1.59–1.84 s on Firewoods and 4.25–6.90 s on the trunk. Complete worker wall time including validation was 141.07 and 209.49 s. Fixture reset between identical benchmark trials is separate from the timed preview fork and restore. [Firewoods raw calls and timings](evidence/firewoods/CAPTURE.json) · [Trunk raw calls and timings](evidence/dead-tree/CAPTURE.json)

All 288 measured and 48 warmup trials recovered the expected Boolean, first frame, and a valid material witness. The independent score checks the rotation and the step count to that frame. The native capture verifies every frame of the four full unbranched continuations, the pre-edit and post-edit states, eligible material membership and the recorded checkpoint/endpoint identities. The two horizons share a physical trajectory and outcome on every edit. These four author-defined editing examples contain zero censored outcomes. Only Firewoods was trained as a Gaussian reconstruction. The trunk uses a separate mesh sampled at its distinct vertices. Creator utility, negative long requests, behavior under other service schedules, and the cost against a control that also targets only active graph recipients remain open. [Reference extractor](reference.py) · [Native runner](run.mjs) · [Score checks](score.py)

## Reproduce

From this folder the offline reference and timing checks use standard-library Python.

```shell
python reference.py
python score.py firewoods
python score.py dead-tree
```

For new native runs, follow the T90 runtime and asset staging instructions. From the repository root build the pinned browser plugins and use fresh output paths. The optional `--capture-dir` scores a fresh run in its own directory. [Native runtime and geometry instructions](../t90-callable-regional-query/README.md) · [Transferred geometry preparation](../t92-transfer-workload/README.md)

```shell
node tracks/tog/tasks/t93-exact-terminal-gas/build.mjs
node tracks/tog/tasks/t94-resumable-gas-query/build.mjs
node tracks/tog/tasks/t95-multistep-material-slice/build.mjs
node tracks/tog/tasks/t97-ordinary-cached-graph/prepare.mjs
node tracks/tog/tasks/t98-edit-to-answer/run.mjs --methods regional,rank-only,sweep-spatial,slice-rank,cold-cache,asset-cache --repeats 6 --out fresh-firewoods
node tracks/tog/tasks/t98-edit-to-answer/run.mjs --methods regional,rank-only,sweep-spatial,slice-rank,cold-cache,asset-cache --repeats 6 --out fresh-trunk --recipe tracks/tog/tasks/t92-transfer-workload/recipe.json --asset tracks/tog/tasks/t92-transfer-workload/local/scene.ply --reference tracks/tog/tasks/t92-transfer-workload/evidence/capture-report.json --traces tracks/tog/tasks/t92-transfer-workload/evidence
python tracks/tog/tasks/t98-edit-to-answer/score.py dead-tree --capture-dir fresh-trunk
```
