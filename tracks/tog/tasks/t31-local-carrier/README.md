# T31 — an existing local simulation becomes a reusable authored input

The sole acquisition completed under the [pre-fixed protocol](PROTOCOL.md): one browser, one reset,180 steps and both original P3 capture times. It exported all270 particles at step90 and all540 at step180, with complete raw particle inputs and an explicitly defined continuous isotropic Gaussian field. This supplies a local input for future same-model ordinary-reference work. It establishes no renderer bottleneck, new method, accuracy/speed improvement or TOG core contribution.

## What was actually obtained

| Existing capture | Time | Particles | Sum of full-line peak strengths k | Largest RGB component |
| --- | ---: | ---: | ---: | ---: |
| shared-s11, step90 | 1.4999999999999996 | 270 | 40.073155027702256 | 2.3239372513395082 |
| shared-s11, step180 | 2.9999999999999942 | 540 | 65.71101349664323 | 2.3430615086998454 |

The sum of k is not a particular ray's optical depth or physical mass. All particles are retained, including particles that may be outside a future view. The fixed specification has256x192 pixel centers and all three existing views; no rays or images were evaluated. These are two times and three views of ONE author-generated simulation, not multiple independent scenes, learned scan data, a creator-validated brief or held-out evaluation.

[states.json.gz](run-01/states.json.gz) contains619,128 raw JSON bytes in224,545 lossless gzip bytes. It retains both full physics/render particle arrays, parameters, configuration, counters and step receipts. [carrier.json.gz](run-01/carrier.json.gz) contains167,310 raw JSON bytes in58,581 gzip bytes, with all810 mapped Gaussians and camera/view metadata. Raw/compressed identities are in [result.json](run-01/result.json). This is a complete input for the declared field, not a demonstrated resumable simulator checkpoint.

## Model boundary

[MODEL.md](MODEL.md) defines h=R/sqrt(6), nonnegative extinction strength from the existing optical parameter, the unchanged P3 temperature color formula evaluated in binary64, true unit-ray finite segments and linear HDR with black background. It removes the old billboard's truncation/pedestal and changes perspective footprints and overlap integration. The new output is therefore **not an image-preserving conversion** of the original renderer. A future difference from the original splat image is expected model difference, not evidence of improvement.

The observed color maximum2.3430615 makes it especially important not to reuse the old [0,1]-color fixture's error guarantees unchanged. Future pruning must account for omitted extinction's effect on downstream radiance and retain the shared full field as its target. Original shader float32 results and displayed/bloomed screenshots are not this binary64 field's references.

## Execution and qualification

[execution.json](run-01/execution.json) records one successful invocation in4.388339700060897 supervisor seconds; worker elapsed time was3.8656127 seconds. These cover acquisition/setup/serialization/cleanup, not rendering throughput or GPU speed. Node24.16.0, Playwright1.62.1 and Edge149.0.4022.52 ran the existing demo; WebGL reported AMD Radeon890M through ANGLE/D3D11. No NVIDIA-renderer claim follows from the separate machine CUDA capability. Zero browser page errors, blocked external page requests, retries, installations, ray integrations or image outputs were recorded. Frozen sources matched before and after, and no worker was left running.

The [static review](../../../validation/t31-pre-execution-review.md) caused timeout, partial-output, final-cleanup and supervisor-receipt defects to be fixed BEFORE the source freeze and sole execution. Original demo, recipe and runtime files were not edited. The [independent saved-carrier review](../../../validation/t31-saved-carrier-review.md) checks all810 mapped rows: source index, position, h, k and RGB recompute with maximum binary64 discrepancy0. Sequential aggregates match exactly; independently summed aggregates differ by at most3.410605131648481e-13, within the fixed tolerance. All4,970 review checks pass, including the eight frozen source identities and four compressed/raw artifacts. No simulation or integration was repeated.

Historical P3 aggregates lacked particle arrays. Their original demo hash differs from the current source, and the current particle hashes differ as well; this acquisition is not asserted to reproduce those historical states. No second current-version replay was performed, so general replay determinism remains unverified. The frozen new arrays are authoritative for subsequent comparisons.

Before the protocol, one delegated exploratory source inspection read706 unique demo lines against a600-line budget. That106-line overrun is disclosed in PROTOCOL.md; it is not called compliant. No scientific execution preceded the freeze. Root exploratory reading had no frozen total-line cap. These facts do not change the capture budget or erase the exploration deviation.

## Decision

Keep this carrier for a separately bounded ordinary-reference entry task described in [NEXT_ENTRY.md](NEXT_ENTRY.md). Do not retune its density, choose another seed/time, multiply particles, or revive T29/T30 merely because new data now exists. T28's trained-carrier route remains closed. A strong ordinary method may already meet the useful accuracy/cost target; if so, record that outcome rather than manufacture a harder workload. Art, original core and main remain unchanged.
