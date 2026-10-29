# T36 independent saved-output review

**Pass for the new ordinary-only output on the fixed first frame.** One authorized saved-byte audit completed with 884,904 checks and zero failures. It preserves `qualified_ordinary_replay_only`; it does not change T35's failed RGB delivery or recover its overwritten blue samples.

The auditor imported only the standard library and evaluated no scene, projection, Gaussian CDF, density bound or integral. It independently unpacked new `<13d6I` and old `<31d10I` positional records, checked saved arithmetic and PNG encoding, and verified source/data identities before and after. The prior 190,102-leaf mathematical audit was not repeated; its fixed reference identity and the corresponding per-pixel endpoints were reused.

## Saved result

- All 49,152 pixels are committed and independently qualified, with zero invalid, failed or unfinished records. The unique schema retains new blue separately from near/far clipping distances.
- Maximum distance to both reference endpoints per channel is R **0.000640610025266608**, G **0.0009801999849409215**, B **0.000994845783965248**. Maximum alpha discrepancy is **0.000013414859907250228**. All satisfy the unchanged `0.001+1e-10` gate; all RGB/alpha, omission, path and reproduction gates pass.
- New red, green, ordinary alpha, retained count, ordinary path/order, mass charge and pruning delta exactly reproduce their intact T35 fields. Maximum normalized clip discrepancy is 0.000486344628045187 against the limit 1. The complete ordinary operation-counter dictionary equals T35's non-reference counters. This is reproduction evidence, not a speedup result.
- Saved RGB ranges from `[0,0,0]` to `[1.2060765392564263,1.0699881013288852,0.8202146199785505]`; maximum full alpha is 0.5487233024981905. Inherited coverage remains 986 nontrivial pixels (2.0060% of the image), 956 mixed pixels, bounding box `[120,70,135,144]`. These coverage values do not establish a demanding creative workload or an independent new scene.
- Ordinary paths remain 47,782 zero-mass, 375 color-box and 995 GL. Every saved record's actual RGB/alpha values were checked, independently of committed flags and worker success.

PNG signatures, dimensions, CRCs and scanlines were decoded independently. For every pixel, displayed RGB bytes exactly match the fixed exposure-one `L/(1+L)` then sRGB mapping of the **new saved HDR RGB**; alpha, retention and validity-mask bytes also match their specified mappings. The corrected `rgb.png` SHA256 is `f8d2e7aee145b2f9d7c987c8527fcb48932bb5d4589cbd28768e3be1251cad84`. This verifies encoding fidelity, not artistic quality. No crop, rescale, exposure fit or image editing was performed by the audit.

## Identity, budget and cost

All 20 frozen artifacts passed before/after identity checks; freeze SHA256 is `2956bd2b75aac195caaa036a6990a5d21c4f57d6931d65638f02f72110c8e0da`. New compressed/raw pixel identities, all published images, prior comparison files and execution logs also matched. New numeric evidence totals 6,298,888 bytes, below 32 MiB.

The scientific invocation returned exit 0 with no timeout, errors or live child. Computation was **125.5684367 s**, including preparation 2.6980736 s, ordinary solve 118.6531910 s, saved-evidence comparison 1.2727273 s and stream write/readback 2.1179807 s. Saved validation/encoding took 1.1715231 s; supervisor process/cleanup time was 126.8568328 s. These fit the 300/330/10-second limits.

T35's **566.0320006 s** of computation remains paid and recorded, including independent projection 99.5116054 s and reference enclosure 333.1790178 s. T35 plus T36 computation totals **691.6004373 s**, before their separately recorded publication/supervisor overhead. T36 is a second ordinary scientific invocation reusing an expensive existing reference, not a fresh renderer-plus-reference timing, FPS measurement or strong-baseline benchmark.

## Limits and artifacts

The reference interval is applicable because its bounding construction does not depend on the ordinary answer; the old answer only selected the stopping time. Reuse remains conditioned on the fixed authored field, camera, source/runtime identity and exact reproduction checks. The old per-source projection and omitted-mass checks were not independently regenerated. This is binary64 qualification, not a formal floating-point certificate, original P3-image preservation, physical validation or a TOG contribution. T32/T33 failures, T34's subset-only qualification and T35's failed persistence outcome remain unchanged.

- Audit: `validation/t36-saved-output-audit.json`, SHA256 `1d4266adde6dd9886e0cd67309314f510074237616b59e217865256f5d8ede5`.
- Auditor stdout: `t36-ordinary-output-replay/audit/saved-audit-stdout.txt`, SHA256 `ac6f01daa69e4dc71f7842153a539a616a237733494037082d748671fa8257cb`.
- Auditor stderr is empty, SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

No scientific retry, reference refinement, source modification or next experiment was performed in this review. The corrected full image is now available for workload assessment; successful delivery alone does not justify another method or automatic scene batch.
