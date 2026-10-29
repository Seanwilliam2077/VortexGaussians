# T48 — closure is available; a method advantage is not established

The [carrier calculation](CARRIER.md) answers the first question positively: the affine orbit of a projected isotropic Gaussian is represented exactly by a center, a vector coefficient and one symmetric positive-definite matrix. Repeated prescribed volume-preserving affine maps need no growing transformation history. This is twelve scalar parameters in the mathematical record, excluding all thermal, material, rendering, boundary and implementation data. The invariants and transport law are exact identities, not energy-conservation or self-consistent-simulation claims.

The [velocity derivation](VELOCITY.md) resolves a second concrete uncertainty left by T47: this field does not intrinsically require a grid solve. Its velocity and spatial Jacobian admit an ordinary one-dimensional integral, obtained by differentiating convergent heat-kernel integrals before eliminating one integration parameter. This is a same-field reference construction; it is not a measured fast implementation. A Fourier formula alone had not supplied this cost contract.

## What must not be silently dropped

The carrier's real-space vorticity has an algebraic tail even though its underlying Gaussian parameters are finite. Gaussian-tail neighbor culling is therefore not a valid inherited acceleration. The vector coefficient is a raw-source parameter, not an absolutely convergent total physical vorticity integral. These properties already occur for the projected isotropic ancestor; they are not newly observed defects in the demo.

The same matrix determines both the Gaussian envelope and the transported projection metric. A simple isotropic core-spreading update changes both, whereas true heat diffusion changes only the Gaussian factor. Thus exact affine closure does not make this one-matrix representation a closed viscous solver. This round records that boundary without introducing a second state family or an experiment designed to favor it.

Independent affine maps keep a sum of these primitives divergence-free. They do not establish a common physical flow map on their overlapping tails. Obtaining a deformation from a reconstructed velocity, controlling a local affine approximation, and satisfying boundaries are additional operations, not free consequences of the kernel identity.

## Fair ordinary comparison

A comparison of methods delivering this vorticity's velocity must use the full two-term integrand in VELOCITY. Dropping the correction yields the velocity of a different raw-source model. That cheaper term is useful for explaining the formula, but cannot be substituted as an inaccurate or deliberately mismatched baseline.

The ordinary one-dimensional formula itself is available to every comparator. So are matrix eigensystems, shared quadrature nodes, isotropic exact cases, differentiation of the same integrand, batching and any separately qualified far-field acceleration. All source preparation, accuracy-controlled integration, failed shortcuts, gradient evaluation, updates and reconstruction work must count. No fixed quadrature order, useful accuracy/cost region, numerical stability envelope or timing advantage has been measured. This record supplies no basis for charging the ordinary method a mandatory global solve.

The [bounded source screen](SOURCES.md) also finds existing deforming Gaussian vortex representations and anisotropic velocity-evaluation work. It does not match the exact present projector from the inspected material, and that non-match is not novelty evidence. Its two access failures and abstract-only results remain limitations.

## Outcome and next decision

**Retain the derived carrier and evaluator as analytical reference material; do not select them as a new core method.** The finite task has changed the available evidence: exact compact affine closure and an ordinary low-dimensional reconstruction are now explicit, while locality and diffusion limitations are identified precisely.

Before a numerical method task, the research must select a useful operation and a mechanism with a reason to improve on this ordinary reference. If viscosity is part of that operation, it must explicitly address the envelope/metric distinction; if local affine evolution is used, it must address consistency on the full field. A parameter-count argument, nonzero projection commutator, unavailable article, or hypothetical slow quadrature is insufficient. No numerical run, implementation, new source batch or favorable workload is automatically queued by this result.

The full SIGGRAPH/TOG objective remains active and unachieved: a distinct method, practical task evidence, accurate strong-baseline advantage, multi-scene validation and portable reproduction are still missing. Historical failures and their original criteria remain unchanged. This is analytical progress toward selecting the right representation and comparison, not a submission-readiness claim.
