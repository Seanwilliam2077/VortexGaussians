# Why both Bonsai brushes missed the visible-gas target

Both edits produce strong visible gas in the frame. For the light brush, 6,809 native pixels change by at least 16 RGB levels. For the full brush, 6,651 do. **Zero of those pixels falls inside a positive-weight target cell.** A small number of target pixels still change, so a pre-edit test based on complete separation between projected gas and target would be incorrect. At the registered 2 × 2 sampling scale, the largest target differences are 1 and 1.5 levels. The criterion requires 16. This locates the negative image result at the registered deadline. It does not identify the physical cause of the spatial separation. [Rescored histogram summaries and bounds](evidence/SCORE.json) · [Native action and calibrated inputs](../t141-bonsai-action/README.md)

| Frame 270 on the full 1560 × 1040 viewport | Light | Full |
| --- | ---: | ---: |
| Native pixels with any RGB change | 10,286 | 9,992 |
| Native pixels changing by at least 16 | 6,809 | 6,651 |
| Target pixels changing, among 11,984 | 45 | 183 |
| Maximum target pixel change, RGB levels | 1 | 2 |
| 2 × 2 cells meeting the registered contrast threshold anywhere | 1,698 | 1,657 |
| Positive target cells with any change, among 2,996 | 24 | 95 |
| Largest target change in unrounded 2 × 2 channel means | 1.0 | 1.5 |
| Target mass with any change, out of 411.094150 | 0.002687 | 0.012570 |
| Target mass reaching threshold | 0 | 0 |

Every method reproduced the four original native full-image hashes, the material and ordered particle/frontier digests, both native successor states, and the scalar image result in the first fresh process. Image histograms use ordinary native replay with gas on and gas suppressed while the edited material stays fixed. They record integer per-native-pixel bins and exact quarter-level 2 × 2 bins over the full frame and over cells with any tagged weight. The raw receipt includes all target masses per bin. No fitted imagery is distributed. [Complete first-process capture and histograms](evidence/process-1/RUN.json.gz) · [Contrast implementation](contrast.mjs)

## Repeatability remains unresolved

The first process completed its two warm-ups and six balanced pairs in 45.19 seconds. The requested scalar calls always evaluated both candidate brushes. Both algorithms rendered the complete viewport four times, read back only the target crop and returned changed masses and a decision. The indexed ordinary median was 1,888.3 ms and the sibling median was 1,831.1 ms. Sibling won four of six pairs. The ratio of medians was 0.970, and the median of paired ratios was 0.975. Across the pairs the mean ordinary-minus-sibling differences were 45.1 ms in host delivery, 46.5 ms in physics and 2.4 ms in the image phase. The remaining measured and unclassified overhead accounts for −3.8 ms. These component differences are small relative to variation between individual calls. An exact cache for this already-issued deterministic request would serve either method. These timings cover recomputing the scalar with the full viewport renderer. [All 12 measured calls](evidence/SCORE.json) · [Registered order and cost contract](PROTOCOL.md)

| Wave | Order | Ordinary ms | Sibling ms |
| --- | --- | ---: | ---: |
| 1 | Ordinary first | 1,909.6 | 1,941.0 |
| 2 | Sibling first | 1,935.8 | 1,902.2 |
| 3 | Ordinary first | 1,942.2 | 1,814.4 |
| 4 | Sibling first | 1,867.0 | 1,783.5 |
| 5 | Ordinary first | 1,847.2 | 1,847.8 |
| 6 | Sibling first | 1,813.3 | 1,755.7 |

The second fresh process loaded the entire fit, repeated the calibrated pixel audit, reached the same frame-180 parent and recovered the same 1,041 eligible shell IDs. Windows then rejected the atomic receipt rename with `EPERM` while recording entry into native matte preparation. It stopped at 9.65 seconds with zero measured calls. The exact reason the file was busy was not observed. Both process exits and the failure are preserved. The registered two-process criterion cannot be assessed. [Second receipt with filesystem error](evidence/process-2/RUN.json.gz) · [Second process exit](evidence/process-2/EXIT.json)

Run `python verify.py` to recompute the two decisions from the archived contrast histograms, compare all first-process branch evidence with T141, reconstruct orders and paired costs, and verify the procedural stop. To repeat execution in a fresh experiment, use the T141 input staging and environment, then `node run.mjs --check-staging` and `python supervise.py --out FRESH_DIRECTORY`. The runner uses the Node 24 module hooks API to reuse the fixed T141 host. Preserve the output of each serial process and the two independent outcomes. The archived receipts contain all numeric worker fields and redact absolute workspace paths from the error stack. Their original byte identities are included beside them. [Offline verifier and packaging](verify.py) · [Serial schedule](schedule.mjs)
