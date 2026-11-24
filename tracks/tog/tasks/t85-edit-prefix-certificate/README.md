# Exact reuse up to a change in gas emission

On the cached Firewoods take, the checker can answer material membership through frame 272 under per-layer admission and frame 205 under global admission. It starts just after the edit at frame 180 and reads no subsequent edited frame. The advantage over simply stopping at the first different source occurs on the per-layer take. On that same take, T84's ordinary stroke overlay already predicts the endpoint exactly. On the global take, where the edit spreads beyond the stroke, the two rules cover the same 24 complete steps. [Predictions](PREDICTIONS.json) · [Independent comparison](CHECK.json) · [Frozen question](PROTOCOL.md)

| Policy | Complete steps before a different offer source | Complete steps with equal effects on gas and random draws | Last exact material frame | First off-stroke material discrepancy, observed |
| --- | ---: | ---: | ---: | --- |
| Per-layer | 24 | 91 | 272 | None through frame 360 |
| Global | 24 | 24 | 205 | Frame 207 |

## What is reusable

The operation adds 288 direct burners to the end of the existing frontier. The analysis assumes access to the previous A take under the same policy, the ordered result of the zero-time B click, the asset, and the original controls. Source geometry, material IDs and the simulation timestep stay fixed. For every frame that qualifies, an editor can display the exact set of burning material IDs by including the directly lit sites in that frame’s cached A mask.

1. The initial gas, its ordering, the seeded random stream and the emission cursor coincide across the two branches. The instantaneous edit only appends material burners. Existing burners have sufficient binary32 fuel to survive the remaining 180 steps. Even the first 1,400 in the original frontier survive, so precisely those donors receive graph service throughout the suffix.
2. If the gas entering a frame is equal, the same solver advances it and the native flame sampler processes the same hot particles in the same order. At every off-stroke recipient the graph donors, their positions, and the update order also agree. The next material threshold scan thus adds exactly the unedited take’s new sites outside the direct edit. This argument handles only the supplied fixed native controls and material active-set target.
3. The edited frontier has its own order and round-robin cursor. The predictor computes each offered source and layer. From A’s end-of-frame layer counts minus its within-frame births we get the occupancies just before the first offer. A capacity block in both branches consumes zero draws. Admission to the coin flip in both branches uses the same draw. A rejected coin makes no particle. A successful birth from the same site consumes the same additional draws and creates the same native particle. The predictor stops on a change of fullness or an accepted different source. Gas identity is then known through the preceding complete frame, while the material scan in the stopping frame has already finished. Coincident but differently labelled birth sites would also make this conservative rule stop.

Independent checks recovered 117 active-set hashes and 5,590 ordered source/layer/outcome records without a discrepancy. At complete frames they checked layer counts, removal identities and random draw counts. They also verified the actual slot and reason for each stop. Full native gas arrays were exported at the boundaries. Their equality at intermediate frames follows from determinism and the operator argument above. In the global take the first changed source was proposed at frame 205 slot 40 (zero based). Two coin rejections kept the states equal. Slot 42 produced a different birth. Aggregate gas counts first differ at frame 295 and per-frame RNG consumption at frame 305. Using either as the break detector would miss the material difference beginning at frame 207.

## Costs and decision

The predictor took 0.633 s in one Python process for both policies including data reads, validation, calculations and output. Geometry plus manifest preparation took 0.011 s. Per-layer and global cache/instant-edit decoding took 0.275 and 0.301 s. Shadow computation and output-mask hashing took 0.032 and 0.012 s respectively. Python startup and acquiring the zero-time edit in a live editor add costs. T81 originally spent 16.18 and 16.33 s for the per-layer and global A arms, including the original capture and instrumentation. Actual fork state restoration and remaining suffix execution have yet to be integrated and timed.

The historical AB native step costs for the 91 per-layer steps and 24 global steps were 0.841 s and 0.253 s respectively with instrumentation. Including rendering and GPU completion gives 1.284 s and 0.375 s. A material-only query could omit interim renders. On global, just decoding the historical files already exceeded the 0.253 s step component. Subtracting these Python and browser figures cannot establish a live speedup. The first differing-source rule covers the same step cost on global. [Timing and checks](CHECK.json)

Our decision is to retain the certificate as an ordinary comparison for future edit previews. T84 supplies exact event-time labels which can test a sharper question after the gas diverges. Can bounds on a recipient’s accumulated heat still decide ignition early enough to beat ordinary progressive native replay? For a changed source, a certificate must bound error from pre-existing carriers as well as new births, because vortex velocities couple particles. It must permit all uncertain recipients to fall back. A full-cost experiment needs a material-only native reference, cache construction and incremental costs, and an independently motivated second edit. The present evidence favors studying that output-specific question over expanding the whole-gas prefix algorithm. The two measured policy variants share a single input and do not establish generalization or a TOG contribution.

Local editing of an existing fluid trajectory has published precedents. Chen, Levin and Langlois optimize control forces within local spacetime windows in particle-based liquids. Their abstract situates this editing workflow. It does not evaluate the discrete ignition-mask question measured here. [Authors’ paper, arXiv v2](https://arxiv.org/abs/2511.15189v2)

## Reproduce

From the repository root, the predictor accepts the original pinned PLY and uses NumPy. It reads only A traces beyond the edit time. One zero-time AB snapshot per policy supplies the ordered native click result and initial equality checks. The separate scorer uses only Python’s standard library, saved predictions and the public T81 archive.

```sh
python -B tracks/tog/tasks/t85-edit-prefix-certificate/predict.py --asset /path/to/foreground.ply
python -B tracks/tog/tasks/t85-edit-prefix-certificate/check_prediction.py
```

The T84 scoring and T85 predicate were developed on known historical takes. The rule was committed before the predictions and checked separately against the edited suffix. The source reviewer and the scorer author participated in T84. This is an internal review and a retrospective comparison.
