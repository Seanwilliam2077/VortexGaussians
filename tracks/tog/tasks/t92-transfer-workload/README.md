# Transferring the exterior-brush query to a fallen trunk

On a second geometry the two brush orders produced **11 positive and seven negative regional queries**. All 18 windows had cold, fuel-positive sites. Reversing the strokes changed both the endpoint and the time at which the second brush's neighbors ignited. These labels give the proposed predictors a new task with an observable yes/no ground truth. The 18 observations share one geometry, one seed and many frames.

## Geometry and fixed choices

[Dead Tree Trunk](https://polyhaven.com/a/dead_tree_trunk) is a 3.05 m weathered log model credited to Rob Tuytel and released under [Poly Haven's CC0 asset license](https://polyhaven.com/license). Only the 2,812-byte glTF descriptor and the 2,293,788-byte geometry buffer are needed. Source URLs and byte identities appear in [prepare.py](prepare.py). No textures, third-party model files or appearance reconstruction are shipped. The acquisition technique for this model has not been verified.

We retained the exact 50,900 distinct positions among 52,593 mesh vertices, in source order, and assigned identical native splat appearance parameters. Vertex sites reflect the input mesh's tessellation. No area reweighting, photometric fitting or choice of a desired response was involved. The operation tests the native heat/graph operator on a mesh-derived splat geometry. It supplies no evidence about photo-realistic rendering or transfer across trained 3D Gaussian scenes.

The [registered protocol](PROTOCOL.md) and [recipe](recipe.json) were committed at `666dc8c` before either trajectory ran. The fixed upper-bark picks at quarter and three-quarter log length use the ordinary Euclidean brush of radius 0.12 at both locations. The task measures the shell one flame interaction radius outside the second brush. The spherical contacts contained 1,532 and 1,273 sites and both were fully available when applied as the second stroke at frame 180. The initial shells around A and B contained 6,979 and 5,697 sites. The numerical controls carry over from Firewoods, including world-fixed gas layers, native world-scale transforms and the admission switch. A new seed, 23, was fixed with the geometry. A graphics researcher defined the edit. This was not observed artist behavior.

| Stroke order | Cut frame | Eligible shell sites | First ignition within 1 / 4 / 8 frames |
| --- | ---: | ---: | --- |
| A → B | 210 | 5,697 | none / none / none |
| A → B | 240 | 5,551 | none / 243 / 243 |
| A → B | 300 | 5,012 | 301 / 301 / 301 |
| B → A | 210 | 6,979 | none / none / none |
| B → A | 240 | 6,592 | 241 / 241 / 241 |
| B → A | 300 | 5,412 | 301 / 301 / 301 |

The two takes ended at frame 360 with 15,939 and 14,500 burning sites. The public [event answer table](evidence/regional-truth.json) provides all observed regional ignition IDs per frame for each window, including the smallest stable ID on the first positive frame. At frame 240 of A→B the first witness is material 1604 at frame 243. A query comparing a proposed positive witness should accept any eligible stable ID that ignited at its promised time. A query promising the first event must return the correct frame.

The native staged HTML is byte-identical to the T86 reference. We checked every point's cumulative ignition membership against each of the six native cut states, active and retired counts through all 720 frames, zero-time stroke IDs and the final native markers. Full capture took 47.95 s including setup, observation and exporting checkpoints. Native stepping took 22.04 s and 13.80 s for A→B and B→A respectively. Those are trajectory component timings; comparative authoring-query measurements belong to T90. T91 and T93 application code were frozen before these reference outcomes were released. They can compare against ordinary first-event replay without designing the scene in response to their own errors. [Capture receipt](evidence/capture-report.json)

## Reproduce

From this directory, with Python 3, verify the complete registered labels, file hashes and cut/event correspondence offline:

```shell
python score.py
```

To reproduce geometry and both native takes, use Node, Playwright and a compatible browser. The geometry converter uses only the Python standard library. For a different machine, set `PLAYWRIGHT_MODULE` to the absolute path of the local Playwright package and `BROWSER_EXECUTABLE` to the browser executable. When omitted, the capture uses the previous frozen machine's runtime locations.

```shell
python prepare.py --download
node capture.mjs local/reproduced
python score.py --reference local/reproduced
```

The two upstream source files and material PLY remain in the ignored `local/` directory. `recipe.json` and `shell-ids.json.gz` are checked against freshly regenerated geometry. The six public checkpoint files reproduce the T86 cut schema. Their gas state and stable material IDs can be evaluated without starting another simulator unless the comparison requires actual native query timings. [Native checkpoints](evidence/checkpoints/) · [Reference implementation](capture.mjs)
