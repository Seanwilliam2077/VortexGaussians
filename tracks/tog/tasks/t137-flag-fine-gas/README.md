# A stiffer flag closes the gas-sharing window during preroll

Doubling the released nylon flag's bending stiffness changed its evolving geometry after the first ordinary gas/cloth update. **The frozen test certified zero gas updates after that divergence.** Both branches kept the same upwind fire, wind, pole and mass. All 120 gas inputs aligned by time, frame, within-frame substep and external forcing. The final camera and an accelerated editing path were outside this physics test. [Protocol](PROTOCOL.md) · [Machine-readable paired result](evidence/SCORE.json) · [Ordinary flag scene](evidence/ordinary-scene.json) · [Stiffer flag scene](evidence/stiffer-scene.json)

| Native input boundary | Evolving flag | Pending cloth feedback | Observed gas before the update |
| --- | --- | --- | --- |
| 0, preroll frame −23 | Identical | Hook inactive | Identical |
| 1, frame −22 | Different positions and velocities | 8 Z-area, 2 X-impulse and 1 Y-impulse words differ; Z fails the axis test | Identical |
| 2, frame −21 | Different | Rule fails | Still identical, including fine scalars |
| 3, frame −20 | Different | Rule fails | Coarse velocity, pressure and measured maximum speed first differ |
| 4 and 6 | Different | Rule fails | First fine scalar difference at 4, first coarse scalar difference at 6 |

Each coupling grid contains 1,482,624 integer words. At boundary 1 the largest componentwise position difference is 6.79 µm. At boundary 3 the largest Z position difference is 8.38 mm and the largest native Z velocity discrepancy in the gas is 0.0000376. The native velocity check compares all three stored components, and the pressure and scalar checks cover their full grids. Exact field differences establish neither a perceptible image change nor any visible onset. [Early-state magnitudes](evidence/INITIAL_FIELDS.json) · [Native measurements](evidence/)

The sole admitted update was the initial inactive-feedback update, before the evolving cloth states separated. All 119 active comparisons failed. A retrospective comparison of complete **incoming and succeeding** ordinary gas checkpoints finds two equal updates from the start, one more than the guard certified. The additional update starts exactly at the first observed cloth difference and ends at boundary 2. The update from 2 to 3 ends with different gas. Even a method told those ordinary endpoints in advance therefore has **zero additional contiguous exact gas updates beyond the registered one-step lag** on this pair. The remaining 117 incoming gas states and the final state differ. That upper bound concerns this edit and this exact whole-gas criterion. [Frozen sharing and lag definition](../t133-flag-coupling/PROTOCOL.md) · [Axis predicate](../t130-independent-fx-choice/FEEDBACK_TEST.md)

## Scope and costs

One fresh process per arm ran a 1,148-vertex flag across 24 native preroll frames and 24 displayed frames. There were 42 gas substeps during preroll and 78 during the displayed second. Both used a 144 × 88 × 72 coarse grid with 432 × 264 × 216 fine gas. Their complete observer times were 130.63 s and 139.85 s, including 76.57 s and 85.42 s of device admission and preparation. The observer synchronizes before each gas update and hashes the 197,074,944-byte fine field at each boundary. These timings measure instrumented ordinary runs. There was no renderer, online sharing pipeline, paired ordinary-repeat estimate or creator task. Native or driver nondeterminism across independent runs was not separately measured. [First worker](evidence/ordinary.json) · [Second worker](evidence/stiffer.json) · [Full process clocks](evidence/workers.json)

**Subsequent independent control.** A third process with ordinary stiffness exactly reproduced all 169 recorded rows and all 121 pending coupling grids on this device. [T142 repeat and verifier](../t142-flag-replay-control/README.md)

## Reproduce and inspect

With Python and NumPy, run `python score.py` to reproduce the registered guard, the retrospective endpoint limit, worker checks and raw feedback identities. Run `python initial_fields.py` for componentwise magnitude statistics. The portable archive contains every pending grid in both trajectories (121 per arm, including the final frame), every native array hash, both scene descriptions, both completed-frame ledgers, and lossless early witnesses. For the first four inputs it saves complete cloth and scalar fields. For the two large velocity/pressure arrays it saves the exact indices and original/edited values of **every** changed word, with uniformly spaced background samples. Reading the sparse differences yields the same numeric differences as reading both full local arrays. The publication omits the common dense velocity and pressure background. Their complete native digests and post-prefix field digests are capture receipts. Full payload verification for those fields requires rerunning the observer. [Early archive index](evidence/early-index.json) · [Witness reader](pack_fields.py)

To reproduce the native observation use the [pinned Blackbody source and previously recorded runtime](../t126-external-curtain-runtime/README.md) on the admitted NVIDIA/D3D12 device. From this directory:

```sh
python flag.py --source BLACKBODY_CHECKOUT --out NEW_FOLDER
python pack_fields.py NEW_FOLDER
python score.py NEW_FOLDER
python initial_fields.py NEW_FOLDER
```

The first [T133 attempt](../t133-flag-coupling/README.md) stopped before simulation because its observer assumed one fine voxel per coarse voxel. T137 retained the released scene's automatically selected fine grid and compared that state. T130's author-intake and unopened artist alternatives remain separate.
