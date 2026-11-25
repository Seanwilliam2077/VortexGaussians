# Keeping the simulated branch after a speculative preview

On four development edits, deferred material updates reduced median end-to-end time when the preview was discarded. Keeping the simulation at the event and advancing one full native step recovered much of that time advantage. Firewoods BA shows the clearest tradeoff, with median savings of 125 ms on discard and an additional 33 ms on keep. No keep-frequency measurement exists for a creator.

| Edit | First frame | Discard, ordinary → slice (ms) | Keep and continue, ordinary → slice (ms) | Slice logs pending at decision |
|---|---:|---:|---:|---:|
| Firewoods AB | 216 | 285.5 → 249.8 | 262.7 → 255.5 | 3 steps |
| Firewoods BA | 230 | 453.5 → 328.9 | 430.0 → 463.1 | 50 steps |
| Dead Tree Trunk AB | 230 | 338.1 → 154.1 | 346.4 → 349.7 | 50 steps |
| Dead Tree Trunk BA | 231 | 396.6 → 230.3 | 439.1 → 411.9 | 51 steps |

Each cell gives the median of four rotated trials after one warmup. Timing starts when the editor sends the second brush. The editor sends the decision in a second request **after** receiving the preview. The timed interval includes both browser/host trips and excludes user think time. A technical run can have a lower keep median than its discard median even though keep adds work. The preview path is identical until the second request and its observed times vary across waves. Raw records distinguish those two phases.

## What can be resumed

Both implementations share T102's active-recipient material cache. Ordinary replay advances the complete field through preceding frames, suspends the crossing scan at the first witness, then resumes from the next index to finish that step on keep. A proven slice keeps its initial full material buffer, projects the shell, and logs every native gas heating sample into binary64 storage. A keep request rebuilds material only; it never reruns gas from the start of the block. If a sliced scan stopped on a positive witness before emission, it reconstructs the full ignition scan and executes the true feed once at the repaired frontier. After exact materialization both backends advance one complete physical step with the same active graph.

Discard restores the **post-click** editing cut, leaving the second brush applied there. Keep leaves the fully advanced physical state live. The outer harness alone restores pre-click state for the next independent trial. Each arm also has an untimed independent full-native trajectory. The checks compare all material buffers byte-for-byte, frontier order, feed cursor, per-particle properties and ordering, RNG draw count, time and solver phase. Both backends matched at the crossing and the next frame on all four edits. Every measured and warmup call returned the native first frame and a valid witness (80/80 calls). All four edits crossed before H60; this dataset provides no no-event or final-step keep evidence.

At the returned preview the slice retained 154,108 / 394,748 extra typed bytes for Firewoods AB/BA, and 459,600 / 464,720 for Dead Tree AB/BA. These are the extra full-size heat buffer and pending logs above the common fork, excluding allocated object headers and caches. On Firewoods AB, two block expirations already required reconstruction of 32 of 35 sliced steps, leaving only three unresolved. The other three edits retained their full sliced prefix.

## Frequency sensitivity

With action-specific costs D and K, the cost at a hypothetical keep fraction p is (1−p)D+pK. Substituting the endpoint medians gives crossings at p=0.790 on Firewoods BA and p=0.982 on Dead Tree AB; the other two median lines favor slicing throughout. Using conditional arithmetic means gives 0.853 and 0.997 respectively. Pooling the identical pre-decision paths across keep and discard before adding action costs gives 0.758 for Firewoods BA and reverses the small Dead Tree AB keep difference.

Four waves provide a sensitivity analysis, not a population confidence interval. On Firewoods BA, two waves crossed at 0.48 and 0.79 in the median direction; a third favored slicing for keep and a fourth favored it under both actions. On Dead Tree AB, two crossed at 0.94–0.95 and two favored slicing throughout. On Firewoods AB three waves crossed between 0.14 and 0.80; on Dead Tree BA just one crossed at 0.97. No single cutoff is established for an editor. These results describe an investigator-defined operation on the two development assets and one browser/CPU; a deployed user's keep frequency and artist demand remain unmeasured.

## Reproduce

Build the T93–T102 plugins as for the [matched active-graph benchmark](../t100-material-repair/), then run the following from the T103 directory. Each run requires a fresh output folder. Use the original pinned demo, Node, browser and Playwright from the T86 runtime receipt.

```text
node build.mjs
node run.mjs --out fresh-firewoods --methods ordinary-discard,slice-discard,ordinary-keep,slice-keep --repeats 4
node run.mjs --out fresh-trunk --methods ordinary-discard,slice-discard,ordinary-keep,slice-keep --repeats 4 --recipe ../t92-transfer-workload/recipe.json --asset ../t92-transfer-workload/local/scene.ply --reference ../t92-transfer-workload/evidence/capture-report.json --traces ../t92-transfer-workload/evidence
python score.py firewoods
python score.py dead-tree
```

The scorer reads the sealed [captures](evidence/), checks every event and post-action state receipt, and reconstructs the cost and sensitivity tables. Benchmark source, protocol and executable hashes travel with each capture.
