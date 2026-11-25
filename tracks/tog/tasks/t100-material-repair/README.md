# Exact material reconstruction after a regional preview

A regional query can defer off-region material while its graph donors and ordered gas-emitter services are known. When that interval expires, the implementation reconstructs the omitted material from a compact log of gas deposition and continues from the corrected state. Firewoods A→B required two real repairs and one ordinary step to reach its first event. Reconstruction matched all physical fields and a further native step. It avoided restarting 30 gas steps, but delivered about the same latency as the strongest ordinary solver on this edit. The larger gains on five other edits came from reaching the event within the certified prefix. [Exactness argument](EXACTNESS.md) · [Preregistered protocol](PROTOCOL.md) · [Final seven-arm schedule](FINAL_SCHEDULE.md)

The prospective Playground experiment used an independently fitted Gaussian scene with fixed material, camera, seed, click centers and horizons. All seven algorithms were frozen before its labels were disclosed. The 14 requested horizons on the three assets are six distinct physical trajectories, all positive. Firewoods and Dead Tree Trunk development labels were known before the test. All 686 measured calls and 98 warmups returned the native Boolean, frame and a witness in the native first-ignition set. Ordinary unbranched continuations matched all 360 reference steps for every arm. The runs are same-state timing repeats. [Prospective recipe](../t101-playground-holdout/PROTOCOL.md)

## Click-to-answer latency

Milliseconds from the caller immediately before sending the real second click to receiving the result, including the new shell, fork, guard, computation and restoration. Values are medians of seven rotated observations after a separate warmup. “Ordinary” uses T102's optimized complete-material active recipients with a reusable immutable pre-click anchor. “Restart” tries the same certified prefix, discards it at its first expiry and replays ordinary simulation. “Repair” logs if an expiry can occur and only recomputes omitted material if needed. All three share T102 full material when applicable. Four additional comparison arms, individual trials, phase times and cold starts are in the linked evidence.

| Asset | Click | H | First event after click | Ordinary | Restart | Repair |
|---|---|---:|---:|---:|---:|---:|
| Firewoods | A→B | 60 | 36 | 162.9 | 264.5 | 164.1 |
| Firewoods | A→B | 180 | 36 | 167.8 | 256.3 | 163.6 |
| Firewoods | B→A | 60 | 50 | 271.3 | 212.1 | 212.1 |
| Firewoods | B→A | 180 | 50 | 272.1 | 213.2 | 214.2 |
| Dead Tree Trunk | A→B | 60 | 50 | 312.7 | 143.9 | 145.2 |
| Dead Tree Trunk | A→B | 180 | 50 | 316.4 | 145.2 | 146.3 |
| Dead Tree Trunk | B→A | 60 | 51 | 342.9 | 197.5 | 198.6 |
| Dead Tree Trunk | B→A | 180 | 51 | 331.4 | 195.4 | 197.9 |
| Playground | A→B | 30 | 24 | 147.8 | 105.7 | 105.4 |
| Playground | A→B | 60 | 24 | 147.9 | 107.8 | 106.9 |
| Playground | A→B | 180 | 24 | 147.6 | 102.5 | 103.1 |
| Playground | B→A | 30 | 15 | 75.2 | 44.4 | 45.4 |
| Playground | B→A | 60 | 15 | 76.7 | 45.7 | 45.7 |
| Playground | B→A | 180 | 15 | 74.3 | 44.3 | 45.5 |

On Firewoods A→B, 30 sliced frames from 180 gave 1,740 hot samples. The next two sliced frames added 224. Independent ordinary branches recovered identical physical state at frames 210 and 212, and after one additional native step from each. A zero guard at 212 required one ordinary step. The event occurred on frame 216. Reconstructing 32 material steps cost 39.2–40.2 ms with the active backend. The largest simultaneously retained deposition arrays used 153,600 bytes, plus the saved material state, per-frame objects and other query state. Restart evaluated 66 steps versus 36 with repair. Firewoods B→A and all Dead Tree/Playground cuts returned during their first prefix; the prospective asset provides no evidence for the cost of repairing an expired interval. Some H=180 previews incurred up to 261,120 allocated log bytes even though the event prevented reconstruction. Full gas still advances throughout the prefix.

The ordinary active anchor requires initialization and a reusable pre-click state. Its cold build took 9.7–23.4 ms across the six edit arms and retained 179,143–407,035 typed-array bytes, excluding JS containers. Build time is included in the first call that needs it. Query validation and any branch-local copies are included in measured delivery. Repeated calls use that warm anchor. The fresh ordinary control rebuilds its own index without a persistent anchor. Loading and first-brush setup are reported separately. No human-preview deadline or benefit in an actual artist session was measured.

## Reproduction and raw evidence

Build the pinned plugins in T93, T94, T95, T97 and T102 according to their task READMEs, then run `node tracks/tog/tasks/t100-material-repair/build.mjs` followed by `node tracks/tog/tasks/t100-material-repair/active.mjs`. The reproducible browser environment and third-party asset preparation are documented in T90, T92 and T101. Use the same registered runtime, pins and unmodified native operator. Browser clocks here are specific to the recorded Edge/Node host. The scorer needs only Python's standard library and the published receipts. The simulator and assets are unnecessary to verify the tables and native reference matches.

```powershell
$t = 'tracks/tog/tasks'
$joint = @('--methods','asset-cache,active-fresh,active-anchor,restart-cache,repair-cache,restart-active,repair-active',
  '--active-plugin',"$t/t102-active-recipients/local/plugin.js",
  '--active-audit',"$t/t102-active-recipients/audit.js",'--repeats','7')
node "$t/t100-material-repair/run.mjs" @joint --check
node "$t/t100-material-repair/run.mjs" @joint --out ./local-t100-fresh/firewoods
$dt = "$t/t92-transfer-workload"
node "$t/t100-material-repair/run.mjs" @joint --recipe "$dt/recipe.json" --asset "$dt/local/scene.ply" --reference "$dt/evidence/capture-report.json" --traces "$dt/evidence" --out ./local-t100-fresh/dead-tree
$pg = "$t/t101-playground-holdout"
node "$t/t100-material-repair/run.mjs" @joint --asset-name playground --external-targets "$pg/REFERENCE.json" --recipe "$pg/recipe.json" --asset "$pg/local/scene.ply" --reference "$pg/evidence/capture-report.json" --traces "$pg/evidence" --out ./local-t100-fresh/playground

python "$t/t100-material-repair/score.py" firewoods
python "$t/t100-material-repair/score.py" dead-tree
python "$t/t100-material-repair/score.py" playground --targets "$pg/REFERENCE.json" --native-dir "$pg/evidence"
```

The scorer audits the published directories by default. Add `--capture-dir ./local-t100-fresh/firewoods` (or the corresponding asset directory) to verify and summarize a new run. The native runner requires a new output directory. The raw receipts list input and staged-source identities, full per-trial assumptions and costs, cache counters, material repair logs, warmups and isolated whole-state audit counts. [Firewoods](evidence/firewoods/CAPTURE.json) · [Dead Tree Trunk](evidence/dead-tree/CAPTURE.json) · [Playground](evidence/playground/CAPTURE.json) · [Scorer](score.py)
