# A: conserved transfer does not imply optical preservation

**Decision: do not select this card for implementation.** The physical input can be authored and its output assessed, but the card does not yet supply a mechanism that distinguishes it from conservative remapping plus affine transfer and ordinary optical error control. This is a decision about the present proposal, not a claim that every Gaussian transfer problem is solved.

## What the inspected sources establish

[APIC, TOG 2015](https://math.ucdavis.edu/~jteran/papers/JSSTS15.pdf), sections 5.1–6, gives mass-weighted deposition, an affine particle state and collocated transfer formulas (8)–(11). Its tensor `D = sum_i w_i (x_i-x_p)(x_i-x_p)^T` comes from the interpolation stencil. Quadratic/cubic spline cases simplify `D`; trilinear interpolation can make it singular, with a special gradient identity used instead. The paper also gives a MAC variant. **Do not assign collocated angular-momentum guarantees to that original MAC variant.** Section 9 acknowledges filtering and remaining energy loss.

[MAC APIC, JCP 2020; inspected author preprint dated 14 August 2019](https://www.cs.ucr.edu/~shinar/papers/2019-mac-apic.pdf), sections 2.2, 2.4–2.5 and 7.1, supplies MAC transfers with per-axis affine state and stencil tensors. Its weights reproduce constants and linear coordinates. The appendix proves transfer conservation of linear/angular momentum, affine preservation at `dt = 0`, and the single-particle stability property. This addresses angular-momentum conservation missing from the original MAC variant. Sections 6–6.1 explicitly distinguish conservative transfers from their **nonconservative complete algorithm**, which uses constant-density pressure projection. These are conditional transfer properties, not an arbitrary changing-resolution, splitting/merging, physical-Gaussian or optical guarantee.

Reading scope and access failures are recorded in [a-sources.json](a-sources.json). Neither work's executable implementation was inspected. No general novelty survey was completed.

## Two distinctions that prevent an invalid baseline claim

The following are algebraic deductions for this card, not new results attributed to either paper.

1. For a normalized physical Gaussian `phi_p`, cell masses `w_i = integral_cell_i phi_p(x) dx` sum to one if the cells cover the whole support. Replacing each cell distribution by its fixed node/center need not preserve `sum_i w_i x_i = x_p`. Consequently these cell-integral weights cannot simply replace a linearly reproducing APIC stencil while inheriting its proof. Truncated Gaussian support additionally needs an explicit tail account. A conservative remap may retain cell first moments or apply a consistency correction; calling that correction Gaussian-specific is not itself a contribution.
2. A Gaussian's physical covariance `Sigma_p` and the stencil tensor `D_p` are different objects. For physical affine flow `u(x) = v_p + C_p(x-x_p)`, its internal angular momentum is determined by `C_p Sigma_p`. The collocated APIC affine state is `B_p = C_p D_p`. Matching the APIC conserved quantity therefore does not automatically preserve the angular momentum of the originally declared continuous Gaussian. A proposed transfer must state which quantity it preserves and compare with an ordinary remap allowed the same moments.

## Cheapest rejection: a symbolic merge counterexample

Let `phi_S(x)` be a unit-mass, centered, three-dimensional Gaussian with covariance `S`, with `s > 0`, `a > 0`, and fixed extinction per unit mass. Compare

```text
rho_mix(x) = [phi_(s² I)(x-a e_x) + phi_(s² I)(x+a e_x)] / 2
rho_one(x) = phi_(s² I + a² e_x e_x^T)(x).
```

Both have mass one, mean zero and covariance `s² I + a² e_x e_x^T`. Under the same globally affine flow `u(x) = A x + b`, their total linear momentum is `b`; their total angular momentum is the same because `integral rho(x) x cross (A x + b) dx` depends only on the first two moments. Choose `trace(A) = 0` if an incompressible instantaneous velocity is wanted. This is an instantaneous remapping calculation, not a simulated continuation.

For the complete central line `(0,0,z)`, and extinction per unit mass equal to one,

```text
tau_mix = exp[-a²/(2s²)] / (2 pi s²)
tau_one = 1 / [2 pi s sqrt(s²+a²)]
tau_mix / tau_one = sqrt(1+a²/s²) exp[-a²/(2s²)] < 1.
```

The strict inequality follows from `log(1+t) < t` for `t = a²/s² > 0`. Thus a two-to-one merge can preserve all these mechanical moments while changing optical depth and hence transmittance. This rejects **an implication from moment preservation to optical preservation**. It does not reject approximate optical control, prove that no useful compressor exists, or show a production bottleneck. No numerical test was run.

## Remaining question, cost and stopping rule

An assessable input route exists: the fully specified Gaussian pair, physical extinction and affine field above. A future approximate transfer would need to state its ray domain, error tolerance, admissible particle/grid degrees of freedom, positivity conditions and support/tail treatment **before** running it. The ordinary comparison must receive the same moments, quadrature, split/merge budget and resolution. Cost must include support integration, consistency correction, constraint solution, reconstruction, optical verification and any continuation check; neither a smaller image error at extra particle count nor transfer-only timing establishes an advantage.

The card's finite source-level question was whether Gaussian integrals plus low-order moments alone introduce a different capability. They do not specify one: mass integration is a direct integral identity, affine preservation has an existing transfer construction, and optical preservation does not follow from the moments. Adding a generic constrained optical fit only restates the desired output. **No bounded distinct mechanism remains to authorize now.** A future proposal would need an explicit tighter error bound or cheaper admissible reconstruction than that ordinary comparison; its absence here is a missing method, not evidence that such a method is impossible.

Uninspected areas include general conservative remapping, Gaussian-mixture compression, adaptive particle resampling and application-specific rendering transfer. Their omission prevents a broad novelty claim. It is not grounds for expanding this task's search budget or launching a toy solver.
