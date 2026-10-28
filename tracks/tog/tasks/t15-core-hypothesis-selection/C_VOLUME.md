# C — overlapping Gaussian emission with a pixel-error bound

28 October 2026. **Do not select the current mechanism for implementation.** The operation and researcher-authored inputs are well defined, but analytic optical depth plus a source-color interval is a standard weighted integration enclosure. This screen has not identified an additional Gaussian-specific tightening or amortization mechanism that a fair ordinary integrator cannot also use. This is a rejection of the present card, not a theorem that useful rendering research is impossible.

## Inspected primary evidence

The screen inspected exactly two source families selected by root; it issued no search queries. URLs and access limitations are in [c-sources.json](c-sources.json).

1. **Condor et al., Don't Splat your Gaussians**, DOI 10.1145/3711853. The [main paper](https://arcanous98.github.io/assets/data/papers/Gaussian_tracing_meta_TOG-compressed.pdf), sections 4–6, defines extinction as a sum of kernel contributions, obtains segment transmittance from summed analytic optical depths, and handles overlapping supports. Section 6.1, equation 22, explicitly approximates radiance-field emission using optical-depth-weighted color. Its [supplement](https://arcanous98.github.io/assets/data/papers/Gaussian_tracing_meta_TOG_supplemental-compressed.pdf), S.1.4, equation S.12 and the following paragraph, distinguishes single-primitive closed-form emission from general overlapping emission requiring numerical integration. Thus analytic transmittance is not exact arbitrary colored-overlap emission. The [author repository](https://github.com/facebookresearch/volumetric_primitives) exposes scattering, radiance-field and absorption-only integrators; its README requires a modified Mitsuba branch. Implementation bodies were not obtained in this screen. No claim about their complete error-control behavior follows from that access limit.

2. **Talegaonkar et al., Volumetrically Consistent 3D Gaussian Rasterization**, [arXiv 2412.03378v3](https://arxiv.org/html/2412.03378v3), sections 3–4 and 7, integrates individual Gaussian transmittance analytically while retaining sorting and nonoverlap assumptions. Appendix A, equation 22 and Figure 7, compares the same mixture-density, density-weighted-color field against ray marching and already demonstrates overlap mismatch, including two nearby primitives. Consequently, reproducing that discrepancy would not qualify a new mechanism. Its [official repository](https://github.com/chinmay0301ucsd/Vol3DGS) is publicly linked; no build or runtime was attempted. Rasterization under different overlap assumptions cannot be the sole correctness or timing baseline for this card.

The inspected material establishes these particular formulations and approximations. It does **not** establish that deterministic certification is absent from all prior work. No third source family was inspected, and no novelty conclusion is inferred from the two papers' omissions.

## Independent analytic reduction of the proposed bound

The following is our source-level mathematical check, not an experimental result or a claimed new theorem. Fix one ray, a finite near-to-opaque interval `[0,z]`, scalar nonnegative extinction contributions `s_i(t)`, and per-ray constant RGB colors `c_i` in `[0,1]^3`. Define

```text
sigma(t) = sum_i s_i(t)
j(t)     = sum_i s_i(t) c_i
c(t)     = j(t) / sigma(t)                 where sigma(t) > 0
A(t)     = integral_0^t sigma(u) du
T(t)     = exp(-A(t))
L        = integral_0^z T(t) j(t) dt + T(z) L_background.
```

This is the declared emission–absorption model; it is not screen-space alpha compositing or a physical calibration of the original demo. If arbitrary independent emission is allowed, a bound on `j` alone does not imply a bounded `j/sigma`; that variant needs its own ordinary integrand enclosure. We do not silently apply the color argument to that broader model.

For any subinterval `[a,b]`, suppose componentwise `m <= c(t) <= M`. Since `-T'(t) = T(t) sigma(t)` and the integration measure is nonnegative,

```text
W[a,b] = T(a) - T(b)
W m <= integral_a^b T(t) sigma(t) c(t) dt <= W M.
```

The midpoint of this enclosure has componentwise error at most `W (M-m) / 2`; summing interval widths gives a global integration bound. Equal color has zero width and gives `c * (1-T(z))` exactly in real arithmetic. In the coordinate `s = 1-T(t)`, the same integral is simply `integral c(t(s)) ds`; the enclosure is the usual lower/upper Darboux bound. This argument holds for **any** nonnegative extinction with a computable cumulative integral. Gaussian optical-depth formulas make `W` accessible, but those formulas are already available in the inspected prior work. Recursive subdivision based on this width is ordinary validated/interval quadrature in an optical-depth measure.

Even a favorable two-Gaussian tightening does not yet distinguish this candidate. If `s_1,s_2` are positive Gaussian restrictions to a ray, `log(s_1/s_2)` is quadratic in `t`. Therefore the mixture weight `s_1/(s_1+s_2)` is a logistic transform of a quadratic, whose extrema on a closed interval are attained at endpoints or an interior stationary point of that quadratic. This supplies an exact real-arithmetic color range for two constant-colored components. It is an elementary range evaluation of the known integrand and must also be available to the ordinary interval baseline. Giving only the candidate this information would manufacture an advantage. With more components, separately bounding each ratio can be loose or require additional work; the card presently supplies no proved tightening or cost reduction for that case.

Certification also requires accounting for finite-precision evaluation of exponential/error functions, covariance conditioning, support truncation or culled tails, and any ray-tile bound. An adaptive rule's empirical error estimate is not itself a rigorous enclosure. A high-accuracy ray-marching image is a useful reference, but does not prove a bound either. None of these engineering obligations provides the missing research mechanism by itself.

## Input, output, comparison and stopping decision

- **Available input route:** two explicitly authored positive-definite Gaussian volumes, bounded per-component colors, a ray, and an opaque depth require no unreleased asset or opacity-to-density conversion. Monochrome, proportional-density and separated-support limits can be checked analytically. These inputs establish mathematical qualification only; no production demand has been demonstrated.
- **Assessable output:** the declared RGB integral, a componentwise absolute-error enclosure and a breakdown of integration, truncation and floating-point error. Camera motion changes the ray; continuity and support validity cannot be assumed from one ray's bound.
- **Strong ordinary comparison:** adaptive quadrature of the **same** `T(t) j(t)` with the same analytic cumulative optical depth; if certification is requested, also compare validated interval quadrature with the same available Gaussian and ratio ranges. The existing approximate colored rasterization is a contextual quality/speed comparison, not a replacement for this baseline.
- **Complete cost:** ray-to-Gaussian reduction, acceleration-structure construction/update, candidate/support traversal, all cumulative-depth and color-range evaluations, any discarded-tail accounting, subdivisions, final accumulation and conservative floating-point arithmetic. Count tile-bound setup and recomputation under motion if introduced. No speed measurement has been made.
- **Cheapest disqualification:** the weighted enclosure above already reduces the conjectured method to ordinary integration with known primitives. We have no separate proposed bound to prove tighter at equal available information and cost. A second search round is unnecessary for this rejection; stronger novelty evidence could not substitute for a missing mechanism.

**Decision:** C satisfies a concrete operation and an accessible analytic input route, but fails T15's mechanism-difference condition. Do not run a two-Gaussian overlap demo or begin a renderer merely to accumulate another known effect. Reconsider only after specifying a nontrivial, provable bound or reuse construction, its complete cost, and a reason the equally informed ordinary integrator does not already obtain it. This is a missing research idea, not a request that the user supply assets or authorize more compute. There is no selected numerical qualification in this memo.
