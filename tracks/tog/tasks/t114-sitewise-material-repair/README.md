# Exact sitewise temporal reconstruction of a material block

While the existing gas-emission certificate holds, the material recipients have independent trajectories conditional on the logged gas deposits and fixed ordered graph donors. Preserving native binary32 rounding at every deposit and decay allows a block to be evaluated site by site. The merged ignition times rebuild the complete ordered frontier and coupled state. This algorithm worked on the registered Firewoods and Playground edits. It did **not** make the hard Firewoods B→A query faster than optimized ordinary replay. [Exactness argument](EXACTNESS.md) · [Frozen test](PROTOCOL.md) · [Kernel](repair.js)

| Scene / operation | Ordinary full | Chronological dense repair | Chronological sparse repair | Sitewise repair |
|---|---:|---:|---:|---:|
| Firewoods A→B | 270.6 | 250.9 | 225.0 | 228.7 |
| Firewoods B→A | **600.8** | 661.9 | 677.2 | 666.1 |
| Playground camera 0 | 426.1 | 379.5 | 389.8 | 378.9 |
| Playground camera 153 | 777.6 | 766.4 | 778.7 | 740.0 |
| Playground joint choice | 713.1 | 687.3 | 677.5 | 668.9 |

Milliseconds are median host-delivered latencies over four balanced measured waves following one warmup. Measurements share the original assets, camera/matte tasks and native reference branches. Firewoods uses single-stroke previews, and Playground uses an actual light-first editor action that may need the full sibling as well. All 40 Firewoods and all 60 Playground calls, including warmups, returned the native result. In each Playground operation sitewise narrowly beat the lower of the two chronological medians, but its advantage changed sign across waves. The original T111 ordering of ordinary and dense repair also changed in this session. These are repeated measurements of fixed edits and machine state. [Firewoods raw calls](evidence/firewoods/CAPTURE.json) · [Playground results](playground/SCORE.json)

## Why the expensive repair persists

Firewoods B→A spends 146.2 ms on the sitewise reconstruction phase versus 150.8 ms on dense chronology and 150.9 ms on sparse chronology. The end-to-end sitewise range was 652.4–693.8 ms, entirely above ordinary full at 584.3–606.1 ms. Of 34,687 sites, 7,048 had positive heat at the block start. The 72 logged frames contained 6,829 sampled hot carriers. Their native-radius lookups produced **2,824,238 in-support receiver callbacks** and 367,383 actual heat writes to still-cold sites. The fixed donor graph had just 89 active recipient edges, causing 5,664 graph writes across the block. The sitewise kernel performed 547,861 positive heat decays, updated 5,355 burner clocks, and recovered 956 new ignition IDs. Reordering the graph and clocks affected a small part of the already expensive full flame/material contact computation.

The corresponding A→B repairs lasted 30 and 2 frames. They had 1,740 and 224 samples, 621,918 and 52,662 geometric callbacks, and only 9 and 8 initial donor edges. The sitewise reconstruction phase was 40.0 ms (dense 47.1, sparse 46.0). Its delivered time remained slightly above sparse on that edit. The BA sitewise kernel used at least 416,960 typed scratch bytes for the CSR transpose and per-site frame and onset tracking, in addition to retained gas logs, transient JS buckets/maps, the physical fork and the common immutable T102 anchor. Instrumentation for counting stores was used in a separate 180-frame audit; its inner-loop timings do not enter the delivery comparisons. The T106 sparse baseline builds a positive-heat bitmap at each recovered block; BA has one 72-frame reconstruction. [Per-method phases and active work](evidence/firewoods/SCORE.json)

## Verification and reproduction

Separate full-deadline trajectories agreed on every camera milestone increment and on the complete-state fingerprints at every repaired boundary and a fresh native successor. An additional untimed Firewoods audit checks complete arrays directly: each of six A→B and seven B→A blocks is independently reconstructed with chronological full material and a fresh active-recipient index. Every material byte, ordered frontier entry, cursor, RNG and particle property matches sitewise evaluation at the boundary and after its next native step. Each check starts from the same independently forked state and the original logged gas deposits. This supplements the ordinary uninstructed native trajectories and preserves the timed comparison. [Direct full states](evidence/firewoods-direct/SCORE.json) · [Comparison implementation](direct-audit.js)

Build the plugins used by [T108](../t108-visible-progression/README.md), then run `node tracks/tog/tasks/t106-sparse-heat-scan/build.mjs` to produce its sparse control. Use the same pinned browser/runtime and externally acquired Firewoods PLY. From the repository root:

```powershell
$t = 'tracks/tog/tasks/t114-sitewise-material-repair'
node "$t/run.mjs" --check
node "$t/run.mjs" --out ./local-t114-fw
python "$t/score.py" --capture-dir ./local-t114-fw
node "$t/direct.mjs" --out ./local-t114-fw-direct
python "$t/score.py" --capture-dir ./local-t114-fw-direct --direct
```

The Playground integration, separate true-action timing and complete reproducer are in [its subdirectory](playground/). No additional renderer or GPU transfer was introduced. The technical contribution here is the tested factorization and measured limit of its benefit, rather than an overall speed claim.
