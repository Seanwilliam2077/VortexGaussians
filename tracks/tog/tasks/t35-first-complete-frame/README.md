# T35 — complete computation, failed persisted RGB evidence

Completed30 October2026. **T35 fails delivery of a qualified complete RGB frame.** Its single process exits0 and reports49,152 in-memory accepted pixels, but independent saved-data review finds that every saved blue value was overwritten by the ray's far clip. The frozen result and incorrect RGB PNG are preserved as failure evidence, not displayed as a successful rendering. No repair-and-rerun occurred.

## Concrete failure

The `<31d10I` schema uses `b` twice: once for blue, once for ray endpoint b. The worker constructs RGB and then assigns `b=ref_ray['b']`, overwriting blue before serialization. Both binary slots therefore contain the far clip. Converting records back to a dictionary and forming the PNG preserves that error. The range50.00028–62.53017 is a distance, not radiance. The genuine ordinary blue samples were not saved elsewhere for the full frame; reference interval midpoints cannot be relabeled as those samples.

[Independent audit](../../../validation/t35-saved-result-audit.json) performs1,227,213 saved-data checks and records98,304 failures: RGB range and endpoint checks fail for each of49,152 pixels. [Review](../../../validation/t35-saved-result-review.md) separates the process's reported success from failed persisted output. The pre-execution reviews missed this alias; their historical reports remain unchanged. The worker's numerical gates precede the faulty dictionary update, explaining the apparent contradiction. Neither process exit0 nor its full-valid mask proves delivery correctness.

The [independent auditor source](audit/audit_saved.py) is a byte-identical copy of the script used once after the process finished(SHA25629248b5948512ccac1d639cd509f23fb838645f3e07e72fba19745b62af13f3e). It reads saved evidence only. From the repository root, `python tracks/tog/tasks/t35-first-complete-frame/audit/audit_saved.py --execute --out NEW_REPORT.json` reproduces the failing audit with a new report path and expected exit2; it does not run the renderer or overwrite the original audit.

## What remains supported

The saved reference endpoints, all190,102 accepted leaf records, alpha, red/green, geometry/omission aggregates and counters were not overwritten. The independent audit verifies leaf ownership, domain, adjacency, absorption, ranges and endpoint reconstruction. It does not independently regenerate per-source projections, omission components or mixed-color operands that were intentionally not saved. Binary64 bounds are not formal directed-rounding certificates.

| Preserved quantity | Value |
|---|---:|
| Pixel records / frame |49,152 / original90-front,256x192 |
| Full-alpha>=0.001 pixels |986 /49,152 =2.0060% |
| Worker-classified mixed pixels |956 |
| Nontrivial bounding box, inclusive |x120–135,y70–144 |
| Maximum full alpha |0.5487233025 |
| Maximum ordinary/full-alpha distance |0.00001341486 |
| Created reference cells / accepted leaves |195,926 /190,102 |
| Maximum created cells in one pixel |850 |
| Ordinary zero / color-box / GL paths |47,782 /375 /995 |

The original-size [alpha image](run-01/alpha.png), inspected by root, shows a narrow vertical plume against otherwise empty background; the nontrivial bounding box is16x75 pixels. [Retention](run-01/retention.png) is similarly concentrated. This supplies actual full-image support evidence and a small development workload, but no complex scene, validated creative task or demonstrated need for a new renderer. The incorrect [RGB image](run-01/rgb.png) is retained only to diagnose the failure and must not support visual-quality claims.

## Paid cost and immutable artifacts

The sole invocation takes568.3149 supervisor seconds, including566.0320 computation seconds and1.9109 packaging seconds. Ordinary preparation is4.1231s and solving119.3417s; independent projection99.5116s and reference333.1790s. Other measured stages include qualification4.1943s, stream writes3.2830s, source checks, import/decode, tree/camera and remaining loop overhead. Timers include small progress writes. These are scalar Python costs with instrumented verification, not FPS or a strong optimized baseline. Both the600-second compute cap and200,000-cell cap were approached but not crossed; no budget changed.

[Execution](run-01/execution.json) and [raw worker report](run-01/result.json) remain intact, including the misleading worker success status and corrupted RGB summary. Raw numeric evidence is27,851,948bytes. Lossless [pixel records](run-01/pixels.bin.gz) and [leaf records](run-01/leaves.bin.gz) preserve the original bytes; all14 frozen identities match. No timeout, surviving child, retry, new input, simulation, GPU run or source acquisition occurred.

[Next entry](NEXT_ENTRY.md) requires a distinct-field storage repair with non-scientific round-trip checks, then at most one separately frozen ordinary-only full-frame replay against the intact saved reference. That would qualify a new delivered image, never recover or retroactively pass T35. Both ordinary invocations and the first reference's cost must remain counted. T32/T33 remain failed, T34 remains a fixed-subset pass, art/main remain unchanged, and the TOG core contribution remains unestablished.
