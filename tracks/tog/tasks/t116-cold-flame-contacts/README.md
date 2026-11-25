# An evolving cold receiver grid helps full replay too

The long Firewoods camera-matte query became faster when flame deposition looked up only currently cold material. This improvement applied to the ordinary full solver as well as to deferred repair. On B→A, sitewise repair delivered in 473.7 ms and chronological repair in 482.1 ms versus **493.9 ms for the equally indexed ordinary solver**. Neither deferred method passed its registered requirement of at least 10% lower median and at least five wins in six paired waves. The development route stops here. [Preregistered gate](PROTOCOL.md) · [Operator and assumptions](OPERATOR.md)

| Camera-0 query | Ordinary full | Chronological repair | Sitewise repair | Ordinary cold grid | Chronological cold grid | Sitewise cold grid |
|---|---:|---:|---:|---:|---:|---:|
| Firewoods A→B, +44 frames | 246.6 | 226.7 | 229.1 | 202.5 | 206.2 | 193.3 |
| Firewoods B→A, +86 frames | 611.5 | 677.6 | 765.1 | 493.9 | 482.1 | 473.7 |

Values are median host-delivered milliseconds from the actual second click to the result, six balanced repetitions per method after a separate warmup. The ordinary solver had the same active recipient graph and the same evolving cold-site spatial data structure for the physical gas-to-material update. On B→A, chronological-cold/ordinary-cold was 0.976, with five of six favorable waves. Sitewise-cold/ordinary-cold was 0.959, with four of six favorable waves. Their paired-ratio ranges were 0.876–1.288 and 0.847–1.190. The shorter A→B check produced ratios of 1.018 (three of six) and 0.954 (four of six). Repeated timings share one host and two known development edits. No protected or additional transfer cases were run. [All paired waves](evidence/firewoods/SCORE.json)

## What accounted for the improvement?

The registered 72-frame B→A reconstruction processed the same 6,829 ordered hot samples in both sitewise variants. The original hash delivered 2,824,238 callbacks inside the physical support radius. The cold grid delivered 368,276 (87.0% fewer), preserving exactly 367,383 real heat additions, 5,664 graph additions and 547,861 positive-heat decay stores. A cold candidate in the sitewise index can catch up and become burning on the callback; this explains why its callback and write counts differ. The sitewise reconstruction phase fell from 167.1 to 57.5 ms and chronological repair fell from 157.2 to 60.2 ms. Ordinary *complete* query delivery fell from 611.5 to 493.9 ms. Crediting only the candidate with cold receiver indexing would substantially overstate the scheduling benefit.

On the B→A warm query, ordinary built one mutable grid (median 0.4 ms, 280,576 typed bytes). The two deferred modes each built three grids (median 0.65–0.70 ms), with global and projected grids together requiring up to 561,152 live typed bytes. Static material-to-cell mapping occupied 138,748 typed bytes and took 3.9–4.2 ms on first use on each independent edit page. JS object overhead is separate. The full-deadline audits also recorded all broad and in-support tests, removals and registration sizes. The instrumented timing of those audit passes is excluded from the delivered medians. [Raw registrations, first-use costs and complete curves](evidence/firewoods/CAPTURE.json)

All 84 calls (72 measured, 12 warmup) matched the registered Boolean/defined state, eligible denominator, quarter-matte count and mass, and true first crossing frame. Every method also reproduced each of the two native 180-step readout curves. The per-arm uncensored native continuations verified all 360 steps. At six A→B and seven B→A completed repair boundaries, both cold repair backends directly matched the full physical material bytes, ordered frontier, gas/RNG values and a further native step against independent full chronological reconstruction. Separately, ordinary cold replay matched complete physical state for eight steps on each edit against the native unoptimized solver.

## Reproduction

Prepare the T108/T114 native runtime and Firewoods asset as in [T114](../t114-sitewise-material-repair/README.md). The T114 preflight emits its pinned adapter. Then run from the repository root:

```powershell
$t = 'tracks/tog/tasks/t116-cold-flame-contacts'
node tracks/tog/tasks/t114-sitewise-material-repair/run.mjs --check
node "$t/build.mjs"
node "$t/check-grid.mjs"
node "$t/run.mjs" --check
node "$t/run.mjs" --out ./local-t116-fresh
python "$t/score.py" --capture-dir ./local-t116-fresh
```

To verify the committed receipts with Python's standard library and no simulation dependencies, run `python tracks/tog/tasks/t116-cold-flame-contacts/score.py`. The independent geometry check is also standalone Node. [Source](control.js) · [Scorer](score.py)
