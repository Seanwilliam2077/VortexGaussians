# Matched recovery kernels on the prospective Playground action

All four numerical variants returned the same accepted light brush in both cameras, with the same crossing frames, masses and contributing site IDs. They each evolved only one physical sibling in the joint view. Sitewise repair had the smallest of the four medians in this session; its differences from the stronger chronological method were 0.2%, 3.4% and 1.3%. Every matched four-wave comparison changed direction, including the primary and joint operations.

| One complete action | Ordinary full | Chronological dense | Chronological sparse | Sitewise | Sitewise / faster chronological median |
| --- | ---: | ---: | ---: | ---: | ---: |
| Camera 0 | 426.1 | 379.5 | 389.8 | 378.9 | 0.998 |
| Camera 153 | 777.6 | 766.4 | 778.7 | 740.0 | 0.966 |
| Both cameras | 713.1 | 687.3 | 677.5 | 668.9 | 0.987 |

Cells are medians of four balanced, warm, full host-delivered calls in milliseconds. A cold warmup was run for each method and operation. Sitewise time relative to the faster chronological time **within each wave** was 0.948/1.319/1.005/1.044 for camera 0, 1.057/0.949/1.133/0.939 for camera 153, and 1.008/1.193/0.909/1.035 jointly. The per-wave comparator can switch between dense and sparse. The complete 60-call worker took 78.38 s. Ordinary and dense already changed ordering between the earlier T111 session and this session. A consistent end-to-end improvement over strong chronological recovery has yet to be demonstrated. [Work and raw ranges](SCORE.json) · [All calls and execution costs](evidence/CAPTURE.json)

All four methods' 90-frame mass and ignition count trajectories agreed for both cameras and both the chosen and untried brush. The retained full-horizon audits compared native state fingerprints and the very next full step across all methods. A separate sitewise-only diagnostic then compared every material array, frontier, ordered particle and clock entry against isolated chronological replay at the boundary and after one following native step. Direct equality passed at frames 212/235/257 for the light stroke and 239/261 for the full stroke. Across the five boundary states there were 15,995 particles and 6,801,955 bytes of material payload, followed by a separate next-step comparison each time. The 24.31-s direct worker supplies correctness evidence; it contributes no latency measurement. [Direct comparison receipts](direct-evidence/CAPTURE.json) · [Diagnostic driver](direct.mjs)

The original asset, brushes, camera tuples, seed, weighting and native results are the frozen T111 inputs. `node run.mjs --check` checks the generated source and the pinned runtime. For another paired session run `node run.mjs --out FRESH`, then `python score.py --capture-dir FRESH`; `python score.py` verifies the public timing archive. Run `node direct.mjs --out FRESH-DIRECT` for independent byte comparisons. Raw native source trajectories reside in T111.
