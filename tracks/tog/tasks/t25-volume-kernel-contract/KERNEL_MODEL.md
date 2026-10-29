# T25 — actual volume primitive and vertex contract

29 October 2026. Static inspection by pressure_screen; no source import, compilation, numerical evaluation or network request. Inspected all 713 lines of `internal/slang/utils.slang` and all 139 lines of `internal/slang/vertex_shader.slang` in `chinmay0301ucsd/slang-gaussian-rasterization` at **`5eca1185550c35e3236c511c311aee3eb9129169`**, the dependency pin resolved by root from the main repository at `dd175d52938264770a783cbb7929e20572675544`. Source paths below are relative to `slang_gaussian_rasterization/`. This note covers the primitive evaluator and vertex stage; root separately audits their Python callers and compositing loop.

## Actual primitive expression

In [utils, lines 574–617](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/utils.slang#L574), let `mu` be the camera-space center, `Q` the supplied inverse covariance, `d` the supplied direction and `kappa=opacity_volr`. With `e=1e-7` (line 17), the code computes

```
qbar = max(e, d^T Q d)
n = mu^T Q d
t = n / qbar
if n <= 0: return zero RGBA
p = exp(-0.5 * (t*d-mu)^T Q (t*d-mu))
sigma = sqrt(1 / (qbar+e))
alpha = min(0.99, 1-exp(-2.506*kappa*sigma*p))
return (rgb*alpha, alpha)
```

The separate ordinary `opacity` is loaded at line 584 but unused in this expression. The function does not normalize `d`, apply a physical-length Jacobian, or use its H/W/focal-length arguments. Unit direction must therefore be established at the caller, not inferred from this signature. It neither evaluates endpoint CDFs nor takes a near/far interval. The numerator guard and final cap are active; the commented alternative normalizations are not.

**Independent algebraic interpretation:** for positive-definite Q, unit d, removed guards/regularization, and 2.506 replaced by sqrt(2*pi), the optical mass is the full-line integral of the unnormalized Gaussian `kappa*exp(-0.5*(t*d-mu)^T Q*(t*d-mu))`. This is a conditional ideal model, not an exact description of the guarded floating implementation. A physical line parameterized by nonunit d requires the additional length factor `norm(d)` in its integration measure. The n-positive branch still includes the Gaussian's negative-t tail; the n-nonpositive branch discards a Gaussian whose forward tail can be nonzero. Thus the numerator test is not a half-line or finite-interval integral. The extra e in sigma also changes the width even when the q floor is inactive.

The [T24 density contract](../t24-official-release-contract/DENSITY_STORAGE.md) records that the main `ours` getter returns `kappa=-log(1-0.99*a)*mean(1/s)/2.506`. Substitution cancels that divisor against the evaluator's 2.506 in real arithmetic, yielding pre-cap mass `-log(1-0.99*a)*mean(1/s)*sigma*p`. This supplies the previously missing normalization convention; it does not establish that the paper's coefficient, finite-domain reference or continuous overlapping-emission output equals the released approximation. The `ever` and string `None` branches retain their own getter definitions. No reverse-helper or rendered-image failure was executed here.

## Geometry, color and support

The [covariance builders, utils 658–713](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/utils.slang#L658) form `Sigma=R*diag(s*s)*R^T` and `Q=R*diag(1/(s*s))*R^T`. They assume a scalar-first quaternion, do not normalize it, and use unguarded reciprocal scales. Q is Sigma's inverse when R is orthogonal and scales are nonzero; the main caller's normalized rotation and positive activated scales therefore matter. The [camera transform, utils 264–269](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/utils.slang#L264) applies `R_camera * matrix * R_camera^T` to both covariance and inverse covariance. Treating both that way presumes an orthonormal camera rotation, not an arbitrary affine camera matrix.

In [utils 434–446](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/utils.slang#L434), `softplus_rgb` selects one of two imported SH color functions. Arguments include the Gaussian's world center and camera position. The [vertex stage, 79 and 136–138](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/vertex_shader.slang#L79) evaluates and stores one RGB per primitive per view; the volume evaluator uses that stored RGB, without a sample-position color call. The imported `spherical_harmonics` body was not acquired. Actual direction sign/normalization, basis convention, bias, clamping, softplus definition, output range and color space remain unresolved by these files. Function names do not establish a [0,1] bound or linear radiance.

The [vertex stage, 71–108](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/vertex_shader.slang#L71) rejects nonpositive `scale3d_factor`, center depth <=0.2, exactly zero projected determinant and zero touched tiles. It multiplies scales by that factor for projection, then divides it out before building the physical 3D covariance. Its density argument is not used directly; the origin of the supplied factor belongs to the caller audit. Projection uses a clamped Jacobian and adds 0.3 to each 2D covariance diagonal ([utils 229–261](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/utils.slang#L229)).

The active radius is `ceil(3*sqrt(max(eig1,eig2)))`, with a 0.1 floor inside its discriminant ([utils 303–310](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/utils.slang#L303)). It defines a screen-clipped tile rectangle ([vertex 11–31](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/vertex_shader.slang#L11)). Alternative `splat_radius2`, `compute_maxpdf_ray`, ordinary 2D opacity evaluation and tomography routines in utils are not substitutes for these active calls. Finite tile support and center rejection omit portions of an infinite-support Gaussian without a per-channel error certificate in these files. Sorting keys, blend termination and background are outside this two-file audit; no claim about their complete implementation follows from their absence here.

## Mapping boundary and identities

The sources establish the guarded single-primitive volume expression and its coupling to stored activated density, covariance and per-view RGB. A conditional ideal Gaussian ray mapping is possible. They do not alone qualify an identical T21/T22 operation: finite ray-domain handling, sorting/compositing, all omitted-support errors, color bounds and actual carrier/configuration validity must also be specified. No trained asset was inspected, no throughput was measured, and no novelty claim follows.

`utils.slang` lines 1–13 contain a Google 2024 Apache-2.0 header; this records that source header only, not an asset license or a repository-wide legal conclusion.

| Acquired local source | Inspected lines | Bytes | SHA256 |
| --- | ---: | ---: | --- |
| `acquired/code/13-utils.slang` | 1–713 | 25165 | `c34f1dd627dc642e026d2ac1d561f27486bfe309e6ad3b4028087674e718acab` |
| `acquired/code/14-vertex_shader.slang` | 1–139 | 6317 | `9a63d77e8e0755ac99985be5322ca98867eaf1ca45e8dbc514091d9dc6e37743` |

This reviewer inspected **852 unique code lines**. A text-only count of the nine acquired code files in `requests-transfer.json` independently confirms **2123 total lines** (91+128+94+88+205+258+407+713+139), below the global 4500-line cap; line counting did not extend this review's semantic inspection to other source files.
