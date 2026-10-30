# T63 decision — diagnose separability before more fitting

## Evidence that changes the next question

The finite ordinary endpoint fit passes its numerical qualification but finds no joint witness. Its best field error is 0.1160354170, close to the previous ordinary trajectory's 0.1161932720; covariance and axial-centroid requirements now pass. This narrows the observed failure to the field test for the selected tuple. It does not prove that geometry optimization is exhausted or that every single Gaussian fails.

Increasing the local-search budget would add attempts without explaining the mismatch. A useful next discriminator asks whether the reference itself requires radial/axial dependence that no separable field can express. The tested Gaussian family is separable on D8, and the physical error measure is a product weight. This suggests an ordinary weighted rank-one approximation diagnostic; it is not a proposed new algorithm or contribution.

## Next finite task: T64 analytic separability contract

Prepare **one analytic derivation and one independent readback**, using the frozen reconstruction, physical measure, domain and saved scalar evidence already available. No new source-search batch, array decode, singular-value computation, Gaussian fit, integral, flow trajectory, dependency or scientific child belongs to this preparation. No fourth physical candidate or changed quality gate is selected.

The derivation must establish, rather than assume:

- An exact finite tensor-basis representation of the saved cellwise linear field, including its annular radial center, zero local bilinear coefficient and correct 2πr³ weight. Sampling cell centers and taking an unweighted SVD would answer a different question.
- Correct Gram factors and matrix orientation; why projection into the reconstruction's finite tensor space cannot increase the error of an arbitrary product field. Smooth Gaussians need not themselves lie in that finite basis.
- The relationship between the largest singular value, the reference norm and the minimum arbitrary rank-one error. The relaxation drops Gaussian shape and all moment/positivity constraints; it must therefore give a lower bound for the scoped family, not a joint-feasibility witness.
- What a finite-precision evaluation could legitimately exclude. A numerical singular value alone is not a formal upper enclosure. Any future exclusion rule must account for reconstruction/linear-algebra error, unchanged reference sensitivity and the distinction between the saved discrete reference and the unknown continuum flow.

If these requirements hold and the diagnostic would distinguish an actual mechanism, freeze a separate small measurement budget covering all assembly, norm/Gram checks, spectral work, residual checks and sensitivity. Select only the two existing endpoint references; no larger Gaussian search, mixture or new dynamics method is authorized by this preparation. If the bound is structurally too weak or cannot be evaluated reliably within the proposed budget, record that limitation and choose no numerical run.

Interpretation must be fixed before measurement: a qualified bound above 0.10 would implicate nonseparability for the saved reference and motivate examining ordinary representations capable of such dependence. A bound at or below 0.10 would leave Gaussian shape, moment restrictions and optimizer coverage unresolved. Neither branch supplies a causal mechanism, a conservation-preserving evolution rule or a new TOG contribution. The diagnostic may only redirect those questions.

## Goal and preservation

Publish T63 before numerical follow-up. Preserve T60's failed execution receipt, T61's separate evidence acceptance, the original endpoint requirements and all paid failures. The full goal remains active: a credible submission still requires a useful new method against strong ordinary alternatives, multiple scenes/held-out cases and reproducible evidence. Art remains inactive, main unchanged and the deleted automation stays deleted.
