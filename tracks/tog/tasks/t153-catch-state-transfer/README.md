# Reconstructing the slower curtain material

Across all 13 native boundaries admitted by T151, halving the fast catch-progress channel and copying the other three channels recovered the complete independent slow atlas byte for byte. Each boundary contains 260,064 binary16 words across 65,016 texels. This includes the initial state and 12 updates covering the first third of a simulated second. The edit changes the fixed curtain's catching time from 0.35 s to 0.70 s. The comparison uses two independent native runs and a researcher-defined edit. [Frozen protocol](PROTOCOL.md) · [Upstream native input](../t151-surface-preignition/evidence/) · [All boundaries, counts, hashes and witnesses](SCORE.json)

| Completed updates | Simulated seconds | Nonzero fast progress texels | Instantaneous range exceptions | Range admits entire history | Reconstructed words different |
| ---: | ---: | ---: | ---: | :--- | ---: |
| 0 | 0 | 0 | 0 | yes | 0 |
| 2 | 0.0833 | 20 | 0 | yes | 0 |
| 7 | 0.2292 | 46 | 0 | yes | 0 |
| 8 | 0.2500 | 58 | 1 | no | 0 |
| 12 | 0.3333 | 95 | 0 | no | 0 |

The original range check first abstained at step 8. Texel (z, y, x) = (5, 7, 44) had fast catch word `0x02fe`, below the registered positive minimum. Both the prediction and the slower native run stored `0x017f`. Steps 9–12 had no new range exceptions. The registered rule requires an unbroken history, so step 7 remains its last admitted boundary. Every registered prediction had zero changed words and zero maximum absolute error across fuel, catch progress, flags and smoulder. [Precision and prerequisites](PRECISION.md)

For this fixed pair, any cost comparison should include ordinary one-atlas reconstruction and synchronous advancement of two material atlases beside a common gas. Reconstruction must charge for checking the range, preserving a valid fallback on an ambiguous step and materializing the slower atlas at a fork. The readbacks here supply an offline check. Device execution, fallback, memory traffic, image changes and restart performance require separate measurements. The observed low word is even and suggests testing a sharper ordinary rounding criterion separately. That observation came after inspection of the outcomes.

Use Python with NumPy from the repository root to verify the saved score and the seven precision controls. Only the committed T151 evidence is needed.

```sh
python tracks/tog/tasks/t153-catch-state-transfer/compare.py
python tracks/tog/tasks/t153-catch-state-transfer/compare.py --controls
```
