# T60 — full-window ordinary reference and Gaussian screen

This is the separately frozen full t=1 measurement selected by [T59](../t59-direct-coupled-reference/DECISION.md), for the existing [T55 physical task](../t55-axisymmetric-reference/TASK.md). It introduces no new method, fit, scene or candidate representation. Six ordinary reference trajectories start freshly at q0=1.5*exp(-(r²+z²)/2), and the ordinary complete-tangent Gaussian uses the existing verified coefficient.

## Reference invariants and explicit changes

Reuse unchanged T56 geometry, cell averages, minmod joint positivity limiter, conservative upwind fluxes, SSPRK2, current-q dense Green boundaries, velocity/Jacobian reconstruction and core field comparisons. The ordinary T58 direct solver and independent original RHS/stencil residual adapter retain T59's equations. The horizon changes from .25 to 1; save 0,.25,.5,.75,1. There is no old-CG port regression or old checkpoint continuation.

The new wrapper retains the mathematical updates and changes output lifetimes explicitly: after initial oracle evaluation retain only the initial Jacobian needed in the final NPZ, releasing the initial flow's unused flux buffers; after each completed step's updates, ledger, logs and possible snapshot, release both stage flows, RHS and intermediate q buffers before the next stage. Saved snapshots retain independent q copies and required reconstructed fields. K is released after final dependent work before final stacking. These are pre-freeze lifetime changes, not adaptive numerical repairs.

The equation remains free-space inviscid axisymmetric no-swirl Euler, with q=omega_theta/r and -(phi_rr+3*phi_r/r+phi_zz)=q. Each elliptic call uses the unchanged half-cell FV boundary additions and freshly rebuilt sine/Thomas factors, then checks the independently assembled original W-weighted RHS-relative residual <=1e-10. The finite domain and Green source truncation are controlled empirically, not asserted exact.

## Two spatial measurement regions

Retain the historical core r<=4, |z|<=4. Add D8={0<=r<=8, |z|<=8} physical vorticity comparisons for all physical control pairs. Integrate differences of the original piecewise-linear q reconstructions with 2*pi*r³ weight on the common finer partition. A 3x2 Gauss rule integrates these polynomial expressions exactly in real arithmetic: radial degree at most five, axial degree at most two. Floating-point roundoff and underlying solution errors remain.

Full-box circulation moments use omega_theta dr dz = r*q dr dz, distinct from the primary 3D vorticity norm. Reference-refinement shape discrepancies retain the old analytic initial covariance denominator. The ordinary model's shape error instead uses the original task's actual initial S256 reference covariance norm. For D192 record Gamma and physical-vorticity-squared integral outside D8 within D12; cell boundaries align with D8. These and outer-shell values are diagnostics, not rigorous exterior error bounds.

## Ordinary projected Gaussian and its measurement

Read beta_best_over_g0 from the frozen T54 result and set c=1.5*beta_best_over_g0. The no-fit model is q_G=1.5*exp(-(r²+(z-c*t)²)/2), with actual speed c=beta_star*a_z. The translation-equivariance argument in [T57](../t57-finer-short-reference/DECISION.md) makes this a trajectory of the ordinary complete-tangent projected dynamics, not an extrapolation of initial residual or a center-only comparator.

Its analytic all-space Gamma=1.5*sqrt(2*pi), centroid=(sqrt(pi/2),c*t), covariance=diag((4-pi)/2,1) and squared physical-vorticity integral=(9/4)*pi^(3/2). The model remains positive and its negative-vorticity mass is zero. Reference positivity and nonzero circulation are checked rather than repaired.

At each saved time use S256 as primary reference and S128 as sensitivity. For each reference cell in D8, a fixed tensor 8x6 Gauss rule computes the physical vorticity error numerator, reference denominator and numerical Gaussian D8 mass diagnostics. A fixed 16x12 rule repeats these scalar integrations solely for prespecified confirmation. Require the two relative-error scores to differ by <=1e-6; never replace the primary rule based on output. Gaussian cross terms are not polynomials, so no polynomial-exactness claim applies. Store both rules' scalar integrals, costs and point counts; the D8 masses are numerical estimates, distinct from the analytic all-space moments.

Only a qualified reference, qualified score integration and meaningful reference motion allow a model pass/fail verdict. All claims remain limited to five times, D8 and measured controls; no continuous-time or unconditional all-space certificate follows.
