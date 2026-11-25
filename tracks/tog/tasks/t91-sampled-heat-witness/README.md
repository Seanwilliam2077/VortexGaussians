# Sampling-aware bounds sometimes resolve the complete regional question

A one-step enclosure provably selects a subset of the carriers that the native ignition scan must sample. Heat contributions from those carriers can prove a regional ignition, while the corresponding upper enclosure can rule one out for the first frame. A longer query is answered directly only if a witness proves an immediate ignition. The tested implementation otherwise returns the exact callable regional result through fallback. [Protocol](PROTOCOL.md) · [One-step argument](PROOF.md) · [Causal implementation](estimate.js)

| Asset | Definite decisions over 6 distinct next scans | Regional queries answered directly / 18 | Ordinary all-hot upper bound / 18 | Delivered T91 / native regional, median query ratio |
| --- | ---: | ---: | ---: | ---: |
| Firewoods, both stroke orders | 1 yes, 3 no | 6 | 1 | 1.022 |
| Dead Tree Trunk, both stroke orders | 1 yes, 2 no | 5 | 2 | 1.020 |

On Firewoods the positive witness is material 4437 at the A→B cut at frame 300. On Dead Tree the immediate positive arises at the B→A frame-300 cut. Each positive test resolves three registered horizons sharing that same starting state, hence six and five directly answered queries correspond to four and three distinct cut decisions. Every issued yes names a site that ignites at the next native scan. Every issued no matches the native events. These are two assets and two investigator-defined edits per asset.

T91 direct answers avoid forking. On the directly resolved subsets, the median paired end-to-end cost was 0.228× direct regional replay on Firewoods and 0.222× on Dead Tree. Those subsets are retrospective. Across all queries, sending the predicate before ordinary fallback took slightly longer than replay. The positive-only material shortcuts of T88 had not witnessed any positive; service-aware gas bounds add decisions on both assets, but do not demonstrate aggregate authoring acceleration. The stronger exact first-scan methods of T93 are included in the [joined timing record](CALLABLE.json). Each query uses its seven-repeat median excluding the scheduled warm-up. All windows, including abstentions, enter the summary. [Reference benchmark](../t90-callable-regional-query/README.md)

The [one-sided stress check](challenge.mjs) independently materializes displacements, post-advance survivors, native sampling and material heating for 160 artificial states under 24 admissible velocity assignments each. It includes uncertain domain culls, ties in Morton keys, capacity saturation and temperatures near eligibility gates. It found no false yes or no, including 22 witnessed positives that residual heat alone could not prove. This check exercises culling/rank edge cases; the browser tests use the native field on both actual workloads.

## Reproduce

From this directory use Node and Python 3. The standalone tool takes the optional T86_PLY environment variable for the pinned external Firewoods foreground. The generated transfer asset is provided by T92's recipe. Both recorded trajectories and all query decisions remain available in the repository.

```shell
node challenge.mjs
node standalone.mjs
python check.py
node standalone.mjs --transfer
python check.py --transfer
python join_timing.py
```

[Causal predictions](PREDICTIONS.json) and [pointwise checks](SCORE.json) on Firewoods; [causal predictions](TRANSFER-PREDICTIONS.json) and [checks](TRANSFER-SCORE.json) on the preselected transfer asset. The unchanged predictor source was committed before the transfer outcomes. Standalone Node timings are diagnostics; the end-to-end results above are the shared in-browser measurements.
