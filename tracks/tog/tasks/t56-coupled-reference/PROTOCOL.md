# T56 — short coupled reference, before a method comparison

Previous goal turn: progress. T55 measured and qualified the initial ordinary free-space reconstruction. This task addresses its missing current-source boundary and transport evolution; it does not replace the full [T55 physical task](../t55-axisymmetric-reference/TASK.md) by a shorter, easier application. Same researcher-defined inviscid no-swirl curl-Gaussian ring, sigma=1 and initial center speed=1, no candidate or Gaussian fitting. The full t=1 task and future meaningful-displacement gate remain untested.

## Frozen budget and cases

One scientific child using the same existing bundled Python/NumPy as T55, at most 600 wall seconds including imports, all geometry/kernel preparation, stages, comparisons and output. Six preselected trajectories on [0,1/4], with snapshots at 0,1/8,1/4. No pilot, warmup, retry, fallback, adaptive step or post-result retuning. No new source search, asset, installation, scene or separate advection workload. Only saved-output postprocessing may follow the child. Mathematical/code readbacks and standard-library freeze preparation occur before execution.

| Case | R=Z | radial/axial cells | dt | steps | angular Green order |
|---|---:|---:|---:|---:|---:|
| S32 | 8 | 32/64 | .0025 | 100 | 32 |
| S64 | 8 | 64/128 | .0025 | 100 | 32 |
| S128 | 8 | 128/256 | .0025 | 100 | 32 |
| T64 | 8 | 64/128 | .00125 | 200 | 32 |
| D96 | 12 | 96/192 | .0025 | 100 | 32 |
| Q64 | 8 | 64/128 | .0025 | 100 | 64 |

The first three share the same time discretization. T64 changes only dt; D96 changes the domain while holding cell spacing, dt, angular rule and source-cell rule fixed; Q64 changes only angular quadrature. Radial/axial source quadrature error remains coupled to spatial refinement. No control supplies a rigorous true-error bound. All six cases run despite metric failures; a runtime, linear-solve, nonfinite, CFL, reconstruction or negative-cell failure ends the child with existing per-step/per-case evidence and no retry.

## Numerical contract

The implementation follows [FORMULATION.md](FORMULATION.md). Initialize true r-weighted cell averages of the same analytic Gaussian, not midpoint values. Use piecewise-constant current q for the r^3-weighted FV elliptic source and boundary source sum, with exact r^3 cell weights, midpoint kernel locations and fixed angular Gauss integration. Prepare a dense geometric boundary matrix for each case and apply it to current q at every SSPRK2 stage and saved endpoint. Its setup/storage/applications all count. There is no later substitution of analytic initial q or periodic/zero-Dirichlet boundary.

Use T55's unchanged weighted Poisson solve (zero initial guess, diagonal preconditioning, at most 2000 iterations, verified true weighted residual <=1e-10) and velocity/Jacobian reconstruction. Derive transport face volume fluxes from common nodal psi differences, with zero axis flux and divergence cancellation. Evolve annular q averages by a conservative MUSCL flux with minmod slopes centered at annular radial centroids; a multidimensional slope scaling keeps the reconstructed range inside [0,2qbar]. SSPRK2 uses two current-source solves per step. Outer inflow q is zero; outflow uses the interior reconstructed value. Report the outer two-cell circulation fraction and outgoing flux as source-support diagnostics. Actual omitted exterior mass at later times is not measured or bounded by this run; the initial Gaussian tail information in T55 does not supply such a later bound. The finite-source approximation is not silently called an exact free-space solution.

At every stage require finite values, all cell averages and reconstructed face values nonnegative without clipping, face donor bounds <=2qbar (roundoff tolerance 1e-12 relative plus 1e-300 absolute), maximum outgoing volume CFL <=.5, discrete volume divergence per cell <=1e-10, and the true Poisson residual. Retain both Euler-stage and final SSPRK2 positivity. Fixed-step violations stop rather than reduce dt. Record each step's two-stage boundary circulation flux and complete solver/timing data. Save the stage/step log locally as the run progresses, not only at case completion.

## Metrics and fixed predicates

Primary field comparisons use the same conservative limited piecewise-linear q reconstruction for both cases, on the fixed core 0<=r<=4, |z|<=4, in world coordinates. Integrate squared vorticity differences with weight 2*pi*r^3 using a fixed 3-point radial by 2-point axial Gauss rule on the common finer cell partition. These polynomial integrals are exact in real arithmetic for the declared reconstructions, not a certificate of the underlying fluid. Do not restrict away fine structure, align, clip or fit either field. Denominator is the finer/control member's norm. For velocity, reconstruct each saved component linearly from centered differences (axis radial velocity odd, axial even); use the same common partition and weight 2*pi*r. No claim of a continuum exact norm follows from floating-point evaluation.

Circulation/centroid/meridional covariance are full-box polynomial integrals of the same reconstructed q with measure r dr dz. Compare axial centroid and the complete 2x2 covariance; normalize covariance by the fixed analytic initial norm sqrt(1+((4-pi)/2)^2). Different domain moment integrals retain their tail discrepancy. Also report ring impulse pi*integral r^3 q, invariant-q squared norm 2*pi*integral r*q^2, physical vorticity squared norm 2*pi*integral r^3*q^2, extrema, circulation and outer two-cell source fraction. Physical vorticity squared norm can change through stretching; its change alone is not numerical diffusion.

All predicates are required; no failed coarse/control comparison is dropped:

- Initial core analytic u and full J relative errors <=.02 for S32, <=.01 for S64/T64/D96/Q64, and <=.005 for S128. This check is rerun inside this invocation because the source mapping changed from T55.
- At all three snapshots, both spatial pairs S32/S64 and S64/S128 and all controls S64/T64, S64/D96, S64/Q64: reconstructed vorticity disagreement <=.01, axial centroid disagreement <=.01 width, and covariance disagreement <=.01 initial norm.
- Spatial pair velocity disagreement <=.02; each time/domain/angular control velocity disagreement <=.01 at all snapshots.
- At the two nonzero times, spatial vorticity disagreements decrease by a factor >=1.5 from the coarse pair to the fine pair. Waive only when both errors <=1e-8; never waive a growing fine error because the coarse error alone is tiny.
- Every case's maximum relative circulation/SSPRK2 boundary-flux ledger discrepancy <=1e-10. At each snapshot, relative change from that case's initial reconstructed q-squared invariant <=.02 and axial impulse <=.01. These last two are bounded numerical-drift screens on this nearly isolated box, not an assumption that the physical vorticity norm is conserved.

Qualification means only that this short coupled reference meets these observed controls. There is no trusted full t=1 trajectory, candidate accuracy or new TOG mechanism. Failure is a reference gap, not carrier failure. Preserve all failures, costs and partial outputs. A later extension/repair requires a distinct justified task and freeze; no extra invocation is queued here.
