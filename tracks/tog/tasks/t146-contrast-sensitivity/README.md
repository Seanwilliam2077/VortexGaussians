# Does the same gas choice survive a change in RGB threshold?

The woodpile's primary camera chooses the lighter brush at every positive, representable threshold through **75 display levels**, including the registered 16. The full brush by itself still passes through 74.75. From 75.25 through 255 both miss. Changing only the contrast threshold never makes the heavier brush the preferred gas treatment in these images. The quarter of eligible opacity required for the choice was held fixed.

| View at the cut | Target opacity with any gas-induced display change, light | Full | Choice across the 1,020 positive cutoffs |
| --- | ---: | ---: | --- |
| Woodpile, primary (0) | 77.6911% | 80.1195% | Light through 75, then neither |
| Woodpile, secondary (124) | 0.03154% | 0.03147% | Neither throughout |
| Bonsai, primary (0) | 0.000654% | 0.003058% | Neither throughout |
| Bonsai, secondary (146) | Undefined | Undefined | Target outside camera |

The native displayed RGB is quantized to eight bits. For the difference of two unrounded 2 × 2 channel means, positive cutoffs are separated by one quarter of a display level. Each line above uses the same 1,020 possible cutoffs on the exact measured image pair; these are sensitivity calculations from reused images. No viewer supplied a perceptual cutoff. The native opacity and ordinary frame sources are [woodpile](../t140-native-shell-sensitivity/README.md) and [Bonsai](../t144-bonsai-repeated-cost/README.md). The latter's first process completed the diagnostic independently of its failed second timing process.

Run `python measure.py --check` for a standard-library reconstruction against the saved histograms, including the original registered values. To regenerate the [vector figure](../../submission/sig2027/contrast-sensitivity.pdf) from the same bins, run `python figure.py OUTPUT.pdf` with ReportLab. [Frozen retrospective analysis](PROTOCOL.md) · [All decision intervals and model inputs](SCORE.json)
