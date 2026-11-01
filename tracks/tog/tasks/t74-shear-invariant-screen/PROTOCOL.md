# T74 independent numerical confirmation

Fixed before the sole scientific invocation,2026-11-01. The analytic outcome is already predicted; this is a confirmation, not a blinded discovery experiment or a performance benchmark.

Use A=3/2, q0=A exp[-(r²+z²)/2], x=r²/2 and physical H measure2πr³ dr dz. At this state F=2zφ0q0. Evaluate φ0 independently from its radial erf expression, with a20-term local series below radius.5. Use NumPy only for arrays and fixed Gaussian quadrature; no install, optimization, search or historical trajectory import.

## Fixed calculations

1. Direct tensor Legendre integrals on r∈[0,10],z∈[-10,10] with orders96 and192 in each coordinate. Evaluate Gram/cross/norm integrals for e0=zq0, e1=z(x−1)q0 and n=(z³−3z/2)q0. Compare with analytic ||e1||²/||e0||²=1/2, ||n||²/||e0||²=3/2, orthogonality, <F,e1>/<F,e0>=−4/21 and <F,n>/<F,e0>=−2/7. Closed rates are b0=16A√(2/3)/45, b1=−8b0/21 and bn=−4b0/21. Compute actual nonnegative squared residuals directly for translation alone and translation plus shear, not by subtraction of large norms.
2. Compare derivative-relative residuals with the T52 closed moments J0=15√π/16, J1=√(2π/3)/3 and J2=√π[2atan(1/(2√2))−5/(6√2)]. Translation residual²=1−J1²/(J0J2); adding shear multiplies the captured part by1+32/441. Report the fraction of the remaining translation residual removed, explicitly distinct from32/441. Report the omitted n-direction energy8/147 of the translation energy and its3/4 ratio to the shear gain. This is not comparison to an optimized ordinary two-Gaussian or flow-map solver.
3. At fixed x=0,.5,1,2 of this same initial state, compute the conditional third-central-moment derivative with both2E[(Z⁴−3Z²)φ] and2E[Z³φ_z], using the same96/192 axial rules and N(0,1) weights. Preserve normalization/centering. Both expressions must agree and be strictly negative at these sampled x. The analytic proof, rather than these samples, covers all finite x.
4. For linear shear amplitudes a=0,.001,.25,.5,1,2, evaluate the dimensionless kinetic-energy ratio

   E(a)/E(0)=3∫₀¹s²∫₀∞ w exp(−w)/√[1+a²s²(1−s²)w] dw ds.

   Use Legendre96/Laguerre64, then Legendre192/Laguerre128. Report E0=A²π^(3/2)/3, ratios and deficits. Require ratio1 at a=0, a strict decrease for the positive sampled amplitudes, and the small-a coefficient(1−ratio)/a² near6/35 at a=.001 (absolute tolerance1e−5). These finite checks illustrate the independently proven general-shift inequality; they do not prove it or measure a simulated trajectory's energy drift.

For direct/closed coefficients, relative residuals and Gram identities use absolute error<=1e−9 after the normalizations stated above; adjacent rules use max-absolute normalized disagreement<=1e−9. Conditional derivative agreement and rule disagreement use absolute1e−9. Energy ratios use adjacent-rule absolute1e−9. Report actual differences; no clipping, hidden acceptance of negative residuals or post-run tolerance changes. The finite domains and binary64 comparisons provide empirical confirmation, not interval-certified tails.

## Execution and cost

One scientific subprocess, wall limit30seconds and observed working-set cap256MiB, with no automatic retry. Record all startup/import, node construction, integrals, result IO and process-exit time in the complete child interval. A short supervisor polls OS memory, retains stdout/stderr and records its own overhead separately. Refuse an existing invocation marker. A resource or numerical failure is retained and ends this task; it is not evidence against the analytic family until diagnosed.

Freeze source/input identities before invocation; preserve originals. Full code/script setup and research time are not made free by reporting only child seconds. Update the explicitly tracked scientific-child subtotal2017.6732525997795seconds by this child interval only, without adding overlapping supervisor time. No real-time, GPU, multi-scene, full-window or TOG claim follows. All files stay small and no new raw arrays, assets or media are produced.
