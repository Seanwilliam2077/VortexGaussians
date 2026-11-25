# Can an unlit material site be certified after particle trajectories diverge?

On two point-pick orders of one Firewoods reconstruction, the local temperature- and distance-weighted rule certified 373,913 of 535,437 eligible site–window pairs (69.8%). Counting reachable hot particles with unit weights already certified 328,626 (61.4%). Both had zero observed false certificates. Each of the 18 queries contained undecided sites. Returning the complete label set via prediction and native fallback cost a median 1.60 times native replay, before preprocessing and output. This closes the proposed complete-domain acceleration for this implementation. A certificate can still serve a different output whose undecided sites are acceptable.

## What was measured

From two 360-step takes at 60 Hz, read the edited simulation at frames 210, 240 and 300. For each currently cold, fuel-positive splat, ask if it stays unlit through every scan of the next 1, 4, or 8 frames. Use the same 34,687 material splats and seed 11, reversing the staged A/B strokes in the second take. The cuts are inputs. Predicted labels do not reconstruct the edited state from the original cached take. The 18 windows overlap. Counts weight each splat equally. Both the edits and the question are investigator-defined. [Frozen protocol](PROTOCOL.md) · [Native capture receipt](public/capture-report.json) · [All predictions](PREDICTIONS.json.gz) · [Per-window and pooled scores](SCORE.json)

| Rule | All 535,437 | Positive initial heat, 74,580 | Initial heat ≥0.5, 8,685 | False / windows needing native fallback |
| --- | ---: | ---: | ---: | ---: |
| Global gas bound | 0 | 0 | 0 | 0 / 18 |
| Gas support exclusion | 274,874 | 11,591 | 742 | 0 / 18 |
| Reachable carriers with unit weights | 328,626 | 19,344 | 905 | 0 / 18 |
| Reachable carriers with thermal and radial weights | 373,913 | 27,121 | 1,199 | 0 / 18 |

Each number in the three middle columns counts certified unlit site queries. All rules share current heat and the material-graph bound. Support excludes any possible hot gas contact. The unit-weight rule uses the same hot-carrier and geometry filter as the weighted rule. Persistence, which reports every eligible site as unlit, misses 1,108 ignition queries, of which 928 were already at least halfway to threshold. All 1,108 fall within the weighted rule’s 161,524 abstentions. Near threshold the additional yield over unit weights is 294 cases.

The weighted rule certified 184,044/273,339 on A→B and 189,869/262,098 on B→A. A→B frame 210 at horizon 8 has zero certifications. Round-robin service can wrap during the window, leaving 218 potential emitter offers without a proven location. B→A frame 210 at the same horizon still certifies 19,432. Both shots ended with 5,400 particles. The number of burning material sites at frame 360 was 5,057 on A→B and 8,427 on B→A. The development take agrees pointwise with the published T84 material labels over frames 180–360, including censoring. These results establish transfer across stroke order on this asset only.

## Computation and costs

[predict.py](predict.py) bounds reachable particle groups in fixed-depth layers, future source positions including birth jitter, cooling and compact heating kernels. It permits up to 160 sampled carriers and 48 births per step. It propagates upper bounds through each binary32 heat accumulation, decay, threshold scan and subsequent graph deposition. It permits broad source locations after an uncertain cursor wrap. Positive fuel survival through the fixed horizon can identify the native serviced graph prefix. An internal technical reader checked the code against the native event order and did not identify a one-sided violation for the pinned operator/settings. This inspection and event replay have different scopes.

The no-render native in-memory query took a median 59.7 ms. Weighted computation after preprocessing took 37.5 ms; adding separately measured per-window native fallback gave 92.8 ms median (median of paired ratios 1.60). Timings are single observations on one host. Full native windows remain the fallback for this experiment. Cutting the terminal step at the final ignition scan could improve the ordinary reference for this output, but has not been timed here. Geometry preparation took 7.4 ms once. Each cut needed 20–43 ms to read/hash/decode and 71–94 ms to preprocess. Output list construction is timed across all three horizons per method; allocating it to one specific horizon would give spurious precision. Combined evidence serialization took 300 ms across all methods. Total predictor run 2.651 s, excluding interpreter startup. Native reference collection took 17.398 s including opening the browser and observation; the 720 native steps took 3.986 s and 5.032 s by arm. These scopes overlap. An editor starting at the click also pays for the prefix to the cut; per-query native prefix totals are in SCORE.json. [Recorded Python costs](COSTS.json)

## Reproduction

Public verification and scoring require only Python 3. From this directory:

```shell
python audit_capture.py
python score.py
```

The public directory contains the six cut projections (eligibility and initial heat), both complete per-frame native onset traces and their hashes, timings and validation receipt. PREDICTIONS.json.gz preserves sorted IDs for each method and was committed before independent scoring. Re-running score.py uses those saved masks and the public projections; it does not read end states from the predictor inputs. To regenerate the simulation and the masks, use the original hash-pinned Firewoods foreground PLY, Node, Playwright/Chromium and Python with NumPy. Consult [the capture](capture.mjs) for the optional fresh output directory and explicit `T86_PLY`, `PLAYWRIGHT_MODULE`, and `BROWSER_EXECUTABLE` paths. From this directory with those variables set:

```shell
node capture.mjs local-reproduction
python predict.py --asset PATH_TO_FOREGROUND_PLY --input-dir local-reproduction --output fresh-predictions.json.gz --costs fresh-costs.json
```

The six [native input checkpoints](checkpoints/) (3,496,043 compressed bytes) are also public. They contain gas particles, frontier/cursor, heat, state, fuel and controls without scene appearance or per-site static geometry. To regenerate masks without running the simulator, use `python predict.py --asset PATH_TO_FOREGROUND_PLY --input-dir checkpoints --output fresh-predictions.json.gz --costs fresh-costs.json`. `python audit_capture.py --checkpoints checkpoints` checks the archived checkpoint identities and all six public projections. Native capture wall times vary. The external PLY comes from the [FieryGS dataset release](https://github.com/PKU-VCL-Geometry/FieryGS/tree/f70fbe26d22431c7acd93a745861dd47ba4307d7) and must match the SHA256 in the receipt. [Regional follow-up](../t87-stroke-halo/PROTOCOL.md) · [Paper working draft](../../submission/sig2027/paper.tex)
