# T23 preparation — model, prior-method and official-workload compatibility

29 October 2026. **Prepared, not executed.** T22's sole invocation qualifies192 baseline and3456 comparison deliveries. It establishes one local prefix-increment win at .01, but the whole-batch median advantage is only1.37% versus direct GL and0.46% versus signed simple, with overlapping ranges and slightly worse .001 median. This warrants checking whether the construction has a relevant workload and a distinct role, not another timing run, favorable scene or renderer implementation.

## Fixed question and source families

Can an already identified Gaussian-volume method and its official asset format supply the same continuous colored-emission operation without an undocumented alpha-to-density conversion? What part of the current sorting/error-control construction is already covered by that method and the existing hybrid transparency family?

Use only these **two previously identified primary families**:

1. Talegaonkar et al., *Volumetrically Consistent 3D Gaussian Rasterization*, the fixed [arXiv2412.03378v3](https://arxiv.org/html/2412.03378v3) and its linked [official Vol3DGS repository](https://github.com/chinmay0301ucsd/Vol3DGS). The durable [T15-C note](../t15-core-hypothesis-selection/C_VOLUME.md) records a previous reading of sections3–4/7 and Appendix A, equation22/Figure7, about mixture density, density-weighted color and overlap discrepancy versus ray marching. That historical note is a reason to audit the source, not a replacement for new source verification or a claim that downloadable assets already qualify.
2. Hahlbohm et al., *Efficient Perspective-Correct 3D Gaussian Splatting Using Hybrid Transparency*, the [publisher article DOI10.1111/cgf.70014](https://onlinelibrary.wiley.com/doi/10.1111/cgf.70014). The [T17 source note](../t17-order-inversion-bound/RELATED_WORK.md) records the sorted-front/order-independent-tail construction and its volume-integration discussion. Inspect its actual semantics and scope; do not infer a same-model guarantee merely from similar names.

Do not repeat Cornell acquisition, add GFS because its full text was inaccessible, search a new paper family, or treat any unread source as evidence of novelty. Two sources cannot establish literature priority even if neither contains the exact current expression.

## Bounded acquisition and inspection

- Reuse existing local source material when available, preserving its recorded origin/version. For each named paper, at most one access to the named HTML endpoint and, only if needed, one linked official PDF/full-text fallback: at most four explicit document acquisition attempts total. No search-engine queries or alternative mirrors. Inspect only model definitions, compositing/integration, error/approximation treatment, limitations and data/implementation descriptions; at most32 PDF pages total, or explicitly named HTML sections with their retrieved lines recorded.
- For Vol3DGS code only, resolve and record one fixed repository commit before reading implementation. Allow at most four repository metadata files/requests in total for revision/tree/README/license; list acquired versus failed attempts. Then inspect at most **six relevant code files and1800 source lines in named ranges**, covering parameter activation/loading, covariance and color, camera/ray conventions, and the actual compositing/reference path. Select filenames from the observed pinned tree; do not guess nonexistent endpoints or silently follow a moving default branch. Record complete acquired byte counts/hashes and inspected ranges separately. If a file is acquired in full but only a range is read, do not claim the entire file audited.
- At most two asset-metadata pages/endpoints directly linked by that official repository/paper. Determine advertised checkpoint fields, scene/camera provenance, download extent and permission/license information where actually stated. Do not download checkpoints, images, archives or third-party datasets. An access/authentication failure is a recorded gap, not permission to bypass it or expand sources.
- No code execution/import, installation, numerical evaluation, new quadrature point, scene construction, GPU job, renderer or benchmark. No creator contact or invented usage testimony. This is a finite source/semantic audit, not workload measurement.

## Required evidence table

For each relevant source path, record exact inspected locations and classify the following as confirmed, mismatched, or unresolved:

1. Extinction definition and activation/units; relation between stored weights/densities and ray optical masses. Learned density is allowed without physical calibration. Learned peak alpha is not silently reinterpreted as density.
2. Full overlapping density and source term, including whether the target is density-weighted self-emission, discrete splat compositing, or illumination/scattering transport. Do not replace emission color with scattering albedo without a justified operator change.
3. RGB/SH evaluation, color space, boundedness and whether colors are constant along one ray; scene covariance/coordinate transforms, camera/ray parameterization, background and near/far or infinite-tail convention. Explicitly track spatial culling, support truncation and omitted tails. A rasterizer's culled list is not automatically the complete input to the continuous integral.
4. Existing sorted output, prefix attenuation, color-sign treatment, analytical/empirical error criterion, front/tail approximation and fallback. Distinguish the same construction from a different model, an empirical approximation or an unresolved passage. Mere use of prefix transmission in normal alpha compositing does not by itself prove use of T21's winner-event error bound; conversely the absence of that terminology does not establish novelty.
5. An actual existing official asset carrier with accessible metadata for density/covariance/color/camera/background/domain and use permissions, or the precise missing fields/access. A paper's synthetic illustration is not a public checkpoint; a download link is not proof of model compatibility. Its potential useful-ray frequency remains **unknown** until a separately authorized measurement.

Report how each confirmed difference could matter to the observed local-versus-batch gap. Do not manufacture an application brief from an asset's name or equate a familiar model with production demand.

## Decision and stop

- If a source covers the current proposed construction, narrow the contribution claim accordingly and retain the implementation as an ordinary comparator; do not optimize it into a purported new method.
- If model or official asset mapping cannot be made explicit within budget, end the audit with the concrete mismatch/missing fields. No extra source family, asset download, fabricated replacement scene or numerical task is queued automatically.
- If a relevant model and existing asset carrier are qualified, prepare **at most one** later finite contract to measure applicability on that asset: fix provenance, permitted acquisition size, cameras/ray sampling before inspecting success, complete versus culled support, accuracy semantics, ordinary comparators and full costs. This audit permits preparation only, not acquisition of large data or execution. Include rejected/dense rays and unchanged thresholds; do not choose views to amplify the lone T22 witness.

No T23 outcome by itself establishes novelty, widespread cost benefit, actual creator demand or a TOG core contribution. Keep T17–T22 evidence/gates sealed, art inactive and main untouched. The active research objective remains broader than this finite audit.
