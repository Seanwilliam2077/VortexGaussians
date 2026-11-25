# Predicting when a quarter of a camera-visible material selection has ignited

The quarter-matte crossing needed 383 regional ignitions in Firewoods A→B and 833 in B→A. The first regional ignition had arrived 8 and 36 frames earlier, respectively. A repaired regional simulation gave the correct entire progression in both edits. It beat restarting after certificate expiry in both edits. Against the optimized full material solver, it was faster on A→B and slower on B→A. [Pre-registered comparison](PROTOCOL.md) · [Dependency argument for multiple ignitions](EXACTNESS.md)

| Stroke order | Eligible sites | First ignition | Quarter crossing | Ignited mass / initial mass, pixel equivalents | Full active replay | Prefix then restart | Prefix then repair |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A→B | 2,371 | +36 | +44 | 80.522136 / 282.825750 | 275.2 ms | 395.9 ms | **242.5 ms** |
| B→A | 2,441 | +50 | +86 | 174.351476 / 673.582824 | **588.4 ms** | 981.6 ms | 679.7 ms |

Frame offsets are from the second stroke at native frame 180; one frame is 1/60 simulated second. The camera defines a fixed, foreground-only opacity attribution for the original calibrated view. One pixel equivalent is the sum of one unit of composited alpha across the image. All methods receive the same immutable weights. Each site's contribution is rounded to an integer millionth of a pixel equivalent before summation. Every regional ignition in the crossing frame contributes to the reported mass and count. Both integer milestone frames matched the separately evaluated floating matte. Over 180 steps the largest absolute cumulative difference was 0.00000865 pixel equivalents in A→B and 0.00001280 in B→A. [Per-frame native reference](REFERENCE.json) · [Float raster and view dependence](../t107-visible-burn-progression/README.md)

## Where the time goes

Times are median host-delivered milliseconds of three balanced calls after a warmup, including the actual brush, shell configuration, denominator, fork/restore, simulation and result. On A→B, repair advanced 43 projected and one ordinary step. It performed two reconciliations covering 32 material steps, taking 47.3 ms and allocating 220,160 log bytes over the call. Full/restart/repair timing ranges were 274.3–330.5 / 381.0–407.0 / 236.5–242.9 ms. On B→A, repair advanced 86 projected steps. It reconstructed 72 complete material steps at the first boundary, consuming 155.0 ms, and allocated 440,320 log bytes over the call. The ranges were 587.5–599.3 / 956.3–988.7 / 669.7–682.7 ms. The restart controls paid for 30 and 72 projected steps, discarded them, then ran 44 and 86 ordinary steps from the second stroke. Those are within-session results on two historical edits.

The once-per-view foreground matte took 0.785 s to project. Browser upload and conversion of its 4,812 supplied site records to the 277,496-byte indexed weight array took 72.6 and 64.7 ms on the two otherwise independent pages. Reading, inflating and parsing the static camera archive on the host precedes that upload; this I/O has no separately isolated timer. The timed query still recomputes initial eligibility and the denominator. The two first ordinary graph indexes cost 9.0 and 12.3 ms and allocated 179,143 and 180,103 typed bytes; every method had the same retained index opportunity. Reaching frame 180 on the live scene took 1.93 and 1.94 s. Root-to-receipt worker time including validation was 41.96 s. [Raw costs, full-resolution audit curves, cache allocations and all calls](evidence/CAPTURE.json) · [Independent numerical score](SCORE.json)

All 24 timed and warmup calls matched the native result, including mask eligibility, integer initial/achieved mass, complete crossing count and frame. Independently, each of the three methods continued through *all* 180 future frames on each arm, recovering every per-frame count and mass. At the six A→B and seven B→A rules-driven expiries in the full-deadline diagnostic, the serialized full-state fingerprints and native markers of ordinary and repaired branches agreed. These checks test cases in which the local region contains burning sites before the guard expires. The observed mixed latency still leaves open whether a practical policy can anticipate when the repair toll exceeds the work saved. No inference about visible smoke, perceived quality or an artist's benefit follows from agreement with this fixed opacity matte.

## Reproduce

From this directory, `python reference.py` and `python score.py` reconstruct the results from public data with standard-library Python. `python score.py --capture-dir PATH` scores a newly generated profile. For a live rerun, stage the native Firewoods PLY, matching Node/Playwright/browser and the T93, T94, T95, T97, T100 and T102 browser plugins as in their original instructions. The multi-event builder extracts the same ordinary material update and guarded transition, changing how ignitions are counted and when a disposable answer can return. It verifies the frozen upstream hashes. [Native runtime and data](../t90-callable-regional-query/README.md) · [Multi-event implementation](progress.js) · [Offline scorer](score.py)

```shell
node build.mjs
node run.mjs --check
node run.mjs --out fresh-profile
python score.py --capture-dir fresh-profile
```
