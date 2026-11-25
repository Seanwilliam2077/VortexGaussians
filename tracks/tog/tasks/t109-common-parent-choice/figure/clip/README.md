# Two brush sizes in two calibrated views

[Supplementary video · H.264](brush-choice.mp4) · [Per-frame measurements](frames.csv) · [Validation and source hashes](receipt.json)

**Caption.** Two second strokes of radius 0.06 and 0.12 start from the same frame-180 woodpile. Orange shows the projected contribution of initially eligible shell sites that have ignited since the edit. Teal shows the rest of the eligible shell. In camera 0, the larger brush crosses the 25% target on step +44, at native frame 224. By +90 the smaller and larger brushes reach 11.692% and 34.831%. From camera 124 their contributions reach only 0.011% and 0.073%. The camera changes the projected opacity of a site while the underlying simulated ignition history for each brush stays fixed.

The 12.5-second silent clip plays each of the 90 successive native steps at 12 steps per second. The solver advances at 60 steps per simulated second. Three labeled still holds provide time to read the comparison.

| Encoded picture numbers, starting at zero | Native frames | Display |
|---|---|---|
| 0–23 | 180 | Second stroke, held 2 s |
| 24–67 | 181–224 | Steps +1 to +44 |
| 68–79 | 224 | First target crossing, held 1 s |
| 80–125 | 225–270 | Steps +45 to +90 |
| 126–149 | 270 | Deadline, held 2 s |

## Measurement and provenance

Each camera gives every eligible site a fixed opacity weight from its depth-ordered Gaussian projection, including attenuation by the entire foreground. Images show unrounded pixel contributions to that initial matte. The target bars cover 0–100%, with a mark at 25%. Readouts divide ignited by eligible opacity after each per-site weight has been rounded to integer millionths of a pixel. The denominator sums all 2,371 eligible sites and is fixed at 282,825,750 micro-pixels in camera 0 and 829,199,132 in camera 124. Fewer than one pixel of unit opacity in camera 124 accounts for the faint local change at the deadline. These are investigator-defined criteria for a static view of material transitions. The geometry has artificial neutral lighting. Gas appearance and human judgments are outside this measurement.

The generator rebuilds the four curves from the two native onset ledgers and recomputes the fixed denominator in each camera. For all 360 brush/view/step pairs it checks the site count and integer numerator against the independent native reference and verifies both the full-image and displayed-crop integral of the colored matte against the archived unrounded site weights. It checks the final pixel arrays against the earlier technical figure. Four additional rows in the CSV give the post-click starting state. AL and AF denote the light and full second strokes. [Registered trajectories and reference](../../REFERENCE.json) · [Projection definition](../../../t107-visible-burn-progression/PROTOCOL.md)

The gray substrate is the same original binned-density drawing used in the companion figure, derived from spatial measurements on Qianfan Shen et al.'s FieryGS Firewoods dataset. The movie uses the source camera calibration and geometric-opacity measurements. Source photographs, fitted appearance channels, and raw foreground geometry are omitted. [Figure construction and dataset provenance](../README.md) · [FieryGS project](https://pku-vcl-geometry.github.io/FieryGS/)

## Reproduction

With the pinned Firewoods foreground and camera file, run the following command from this directory. Python requires NumPy, Pillow, and ReportLab. FFmpeg with libx264 and FFprobe must be on PATH.

```text
python make_clip.py --source PATH_TO_FIREWOODS
```

The command produces the MP4, CSV, and JSON receipt and performs a complete decode to validate the codec, dimensions, frame count and duration. Input identities and the output hash are in the receipt. The MP4 size and hash can vary with the H.264 encoder build.
