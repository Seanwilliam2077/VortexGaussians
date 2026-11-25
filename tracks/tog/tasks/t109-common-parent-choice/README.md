# Choosing between two second strokes on one simulated shot

The registered brief preferred the smaller intervention if it ignited at least a quarter of the visible shell opacity within 1.5 seconds. **The full brush was required in the decision view.** From the same seed-53 parent, the light stroke reached 11.69% at the deadline. The full stroke crossed 25% after 44 steps (0.733 s) and reached 34.83% by the deadline. The second calibrated camera saw less than 0.08% from either physical alternative throughout the same 90 steps. This is a consequence of this investigator-defined, camera-specific brief. No artist made or endorsed the selection. [Measured trajectories in both views](brush-choice.pdf)

| View | Second brush radius | Native sites painted | Shell sites ignited by step 90 | Visible shell opacity ignited by step 90 | First step reaching 25% |
|---|---:|---:|---:|---:|---|
| Camera 0, decision | 0.06 | 74 | 190 | 11.692% | No by 90 |
| Camera 0, decision | 0.12 | 288 | 493 | 34.831% | +44 |
| Camera 124, sensitivity | 0.06 | 74 | 190 | 0.011% | No by 90 |
| Camera 124, sensitivity | 0.12 | 288 | 493 | 0.073% | No by 90 |

At the decision-view crossing there were 359 ignited shell sites. Their integer opacity mass was 72,163,970 against a target of 70,706,438. The larger 493 is the count at the common 90-step comparison time. Whole-frame floating-weight reference and integer query gave the same crossing classification and frame. The two cameras share each trace. This experiment contains two physical edits of one fitted asset, one seed and one common original shot.

## Delivered query costs

The editor actually branches from and restores the same live frame-180 pre-click state for both brush sizes and both views. The methods are the frozen [T108 visible-progression operators](../t108-visible-progression/). Medians include the true click, shell registration, fresh eligible mass, active-cache validation, physical work, branch restoration and host delivery. Each row uses three balanced measured waves and one warmup per method. These are disposable preview queries. T103 measured keeping and continuing a first-event branch separately.

| View and brush | Ordinary full replay (ms) | Restart after a guard expires (ms) | Repair material only (ms) | Repair / ordinary |
|---|---:|---:|---:|---:|
| 0, light | 513.4 | 600.4 | 414.8 | 0.808 |
| 0, full | 225.9 | 321.7 | 201.4 | 0.891 |
| 124, light | 495.9 | 577.1 | 398.1 | 0.803 |
| 124, full | 526.5 | 618.2 | 431.6 | 0.820 |

A sequential chooser tests light first and only pays for full if light misses the deadline. Light missed in both views. Thus the chooser and a UI displaying both proposals require both calls here. **Additive warm-cache estimates**, obtained by summing the two per-query medians, are 739.2 / 922.1 / 616.1 ms for ordinary / restart / repair in the decision view. For camera 124 they are 1,022.4 / 1,195.4 / 829.6 ms. A paired two-proposal UI delivery was not measured. This one-computer result offers no general speed guarantee, and three method trials per case do not establish population timing uncertainty. [Raw calls and full audit curves](evidence/timing/CAPTURE.json)

The original T107 fixed-camera raster and validation workload took 0.785 and 0.803 seconds for cameras 0 and 124. T109 verified and reused those geometry weights. Installing an archived table into this browser took a further 67.1 / 58.3 ms per view, with a 277,496-byte lookup buffer for all 34,687 sites. The first ordinary light warm-up in camera 0 incurred the only pre-click active-edge anchor build (11.0 ms; 179,155 bytes of typed storage). All sibling requests revalidated that anchor. Independent shell construction and click were charged on every preview. Cold view/view-change and base preparation costs are separate from the warm conditional comparison; JavaScript object and transport storage were not measured.

## Verification and reproduction

The original PLY gives 2,371 material centers in the static 0.12–0.26 exterior shell and no intersection with either candidate click. Both frozen camera files cover all 2,371 IDs, even though they were emitted for older eligible sets. Eligibility from the *new* parent retained all 2,371. The independent native references have identical deterministic rows and pre-click marker through all 180 common frames, including RNG draws, particle count, onset IDs and active count. The frame-180 marker is 9ec29346. Both edited native continuations matched all 360 frames and endpoints in the profiled browser. Each of the 48 measured/warmup deliveries matched the native first crossing and exact eligible denominator, mass and count. Each method also matched every step of all four 90-step curves, for 12 complete-curve audits. Repaired physical state matched full replay at frames 206 and 207 (light) and 210 and 212 (full). The second camera changes the readout only. The opacity matte measures static projected contribution of ignited substrate; moving flame, changing visibility and audiences' perception of fire are beyond its definition.

Run from the T109 directory in the pinned T86/T108 environment. The reference capture requires an unused output folder. The default paths below regenerate everything on a clean checkout with the original Firewoods PLY available; the Git copy already carries its native ledgers and scores. T93/T94/T95/T97/T100/T102/T108 plugins must be built as in T108. The timing runner takes an optional fresh `--out` folder. Set `T86_PLY` to the original externally obtained foreground PLY if its default location is unavailable.

```text
python prepare.py
node capture.mjs evidence/native
python reference.py
node run.mjs --check
node run.mjs
python score.py
python figure.py
```

[Prospective brief and execution rules](PROTOCOL.md) · [Sibling clicks and frozen state](STATIC.json) · [Native onset data](evidence/native/) · [Decision and latency tables](SCORE.json)
