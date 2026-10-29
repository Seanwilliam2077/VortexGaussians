# T47 — affine vorticity transport and projection

**Completed analytical screen; ordinary repair identified, no new method selected.** The target is the raw vector-Gaussian carrier underlying the original vortex direction, rather than T46's unmatched mechanical mass/velocity merge. This is still T15-A representation-transfer exploration.

[The derivation](ANALYSIS.md) proves that Euclidean solenoidal projection P and common volume-preserving affine transport T_F generally do not commute. The difference is a transverse rank-one Fourier multiplier: both results can be divergence-free yet represent different vorticity. They agree for already-solenoidal inputs, and for all inputs only when F is a rotation. A continuous derivative-Gaussian gauge example illustrates the distinction without pretending it is a finite-particle run.

The exact correction is ordinary conjugated projection Q_F = T_F P T_F^(-1), equivalently a constant-coefficient weighted Helmholtz solve. A compact multiplier or a single deformation matrix does not eliminate representation, elliptic inversion or velocity-reconstruction costs. This is a state/operation boundary, not a new fluid algorithm.

The [four-file static audit](LOCAL_MODEL.md) finds that P5c already documents non-solenoidal raw sources, while its stretching update retains scalar kernel widths. The demo combines source and target widths and separates its display covariance from these dynamic kernels. Neither inspected path implements the persistent anisotropic source transfer tested by the mathematics. This therefore does not establish a present simulator bug.

[Two pinned primary documents](SOURCES.md) cover existing divergence-free velocity bases and flow-map vorticity transport/reconstruction. No search query, third source family, numerical evaluation, scientific-array reduction, simulation, renderer, installation, asset or method implementation occurred. The [scope](SCOPE.md) discloses when the finite question was fixed. [Mathematical review](../../../validation/t47-mathematical-review.md) and the [manifest](audit-manifest.json) record verification and preserved history.

The full research goal remains active and unachieved. No numerical or implementation task is selected. A subsequent decision needs a meaningful operation on the actual state and a mechanism beyond ordinary transported projection, with full-cost strong baselines. Noncommutation alone supplies neither practical advantage nor a TOG core contribution. Historical outcomes, art inactivity, main and the deleted automation remain unchanged.
