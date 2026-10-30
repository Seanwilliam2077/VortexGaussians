# T64 — the same field metric admits an ordinary separability diagnostic

## Question and scope

T63 found no joint endpoint witness in a fixed local Gaussian search. Its best field error .1160354170 exceeds the original .10 gate while both moment tests pass. A larger search is not selected. Instead ask whether **any product field** u(r)v(z) can approximate the same saved piecewise-linear endpoint in the physical-vorticity norm. Every scoped axisymmetric Gaussian is such a product. This is an ordinary representation diagnostic, not a new dynamics method, a fitted correction or a TOG contribution.

Everything below concerns the exact real-valued function defined by the saved binary64 coefficients on D8=[0,8]×[-8,8]. It does not certify the unknown continuum Euler solution or address an unrestricted three-dimensional carrier. No array, integral or singular value is evaluated in T64.

## Preserve the reconstruction and measure

The saved reference in cell I_i×J_j is

    q_R(r,z) = q_ij + qr_ij (r-rc_i) + qz_ij (z-zc_j).

The stored radial center rc_i is the binary64 evaluation of the annular-volume formula 2(r_+³-r_-³)/(3(r_+²-r_-²)). The derivation treats that saved value as a fixed real coefficient; it does not replace it by an unrounded formula. The axial center zc_j is its midpoint. There is no local bilinear term. Values on the finitely many cell boundaries are immaterial in L2. For axisymmetric physical vorticity omega_theta=r q,

    ||omega_R-omega||² = ∫_D8 2π r³ (q_R-q)² dr dz = ||q_R-q||²_W.

Thus H=L2([0,8],2πr³dr) tensor L2([-8,8],dz). This is a product measure. It is not the r dr measure used for circulation or reference centroids.

Take radial local functions 1_I and (r-rc_i)1_I, and axial functions 1_J and (z-zc_j)1_J. Interleave local index 0/1 within each cell. The global coefficient matrix A has 2×2 blocks

    A_ij = [[q_ij, qz_ij], [qr_ij, 0]].

Let D_k=(r_+^k-r_-^k)/k. Exact real-arithmetic radial Gram blocks are

    Gri = 2π [[D4, D5-rc D4],
              [D5-rc D4, D6-2rc D5+rc²D4]],

and axial blocks are diag(h_z,h_z³/12). Gram matrices are block diagonal because cells have disjoint interiors. Their blocks are positive definite: a nonzero linear polynomial has positive square integral under the positive almost-everywhere weight. The radial off-diagonal is generally nonzero. Annular centering does not orthogonalize an r³-weighted basis.

## Scale the basis without altering the field

For numerical assembly, use xi=(r-m_i)/h_r and eta=(z-zc_j)/h_z with midpoint m_i. Both range over [-1/2,1/2]. This reduces the disparity between constant and slope basis scales and avoids subtracting nearby powers in the Gram formulas. The exact coefficient blocks become

    C_ij = [[q_ij + qr_ij(m_i-rc_i), h_z qz_ij],
            [h_r qr_ij,                    0]].

The annular-center correction must remain. This is a basis change, not interpolation at a new center. The radial Gram block in this basis is

    Gr = 2π h_r [[m³ + m h_r²/4,       m² h_r/4 + h_r³/80],
                 [m² h_r/4 + h_r³/80, m³/12 + 3m h_r²/80]],

and Gz=h_z diag(1,1/12). These expressions follow by expanding (m+h_r xi)³ and using the exact moments of xi on [-1/2,1/2]. They remain valid for the first radial cell touching the axis. No numerical polynomial integral is needed to derive them.

Let Gr=Lr Lr^T and Gz=Lz Lz^T be lower Cholesky factors, block diagonal over cells. The matrix in orthonormal coordinates is

    F = Lr^T C Lz,                 ||q_R||²_W = ||F||²_F.

The transposes matter. The corresponding orthonormal basis column is Lr^-1 phi; substituting phi=Lr times that column gives the displayed orientation. Never replace this with an unweighted SVD of the cell-average array.

## Why the finite matrix solves the unrestricted product relaxation

Let U and V denote the radial and axial piecewise-linear spaces. They contain q_R through U tensor V. If g(r,z)=u(r)v(z) is any square-integrable product, its orthogonal projection is

    P_(U tensor V) g = (P_U u)(P_V v).

The projection is still a product (possibly zero). Since q_R lies in the tensor space, Pythagoras gives

    ||q_R-g||²_W = ||q_R-Pg||²_W + ||g-Pg||²_W >= ||q_R-Pg||²_W.

Consequently a product outside the finite space cannot outperform its projected product. Smooth Gaussians need not themselves belong to U or V. The finite rank-at-most-one problem therefore attains the same infimum as the unrestricted separable problem.

For fixed unit factors a,b, optimizing the scalar coefficient in t a b^T gives t=a^T F b and squared residual ||F||²_F-(a^T F b)². Maximizing the absolute bilinear form gives the largest singular value sigma_1. Hence

    E_sep² = 1 - sigma_1² / ||F||²_F
           = (sum_(k>=2) sigma_k²) / (sum_(k>=1) sigma_k²).

For numerical reporting use the nonnegative tail sum, avoiding cancellation in 1 minus a near-one ratio. Positivity, Gaussian marginal shape, centroid and covariance constraints are absent from this relaxation. Thus E_sep lower-bounds the Gaussian field error; E_sep<=.10 does not prove a jointly feasible Gaussian. Conversely, an established E_sep>.10 would exclude every separable field for this exact reconstruction, independent of parameter-search coverage.

## Independent metric-preserving construction

A second construction checks both weighting and reconstruction. Use three-point Gauss-Legendre integration on each radial cell and two-point on each axial cell. Construct Br with local rows sqrt(2π w_r r_node³)[1,xi] and Bz with sqrt(w_z)[1,eta], using cell-scaled weights. Radial Gram integrands have degree at most five and axial ones degree at most two, so in real arithmetic

    Br^T Br = Gr,                 Bz^T Bz = Gz.

Directly evaluate the original q_R expression at these node pairs, without C or F, and form Y_(node_r,node_z)=sqrt(2π w_r r_node³) q_R sqrt(w_z). Then

    Y = Br C Bz^T = Pr F Pz^T,
    Pr = Br Lr^-T,                Pz = Bz Lz^-T,
    Pr^T Pr = I,                  Pz^T Pz = I.

Left/right isometric embeddings preserve all nonzero singular values and the Frobenius norm. This establishes that the quadrature matrix answers the *same continuous reconstructed-field product problem*, not a separate sampled-point fitting problem. With Nr=n,Nz=2n, F is 2n×4n and Y is 3n×4n. The additional n singular values of Y vanish in exact arithmetic. The derivation supplies a specific independent numerical check of assembly, rather than just a second call on the same matrix.

## Floating-point evidence and the boundary of exclusion

Suppose an exact matrix X is represented approximately as U S V^T. If d=||X-U S V^T||_F, eU=||U^T U-I||_F and eV=||V^T V-I||_F, then

    ||X||_2 <= s1 sqrt(1+eU) sqrt(1+eV) + d.

This follows from the triangle inequality, operator norm <= Frobenius norm, and ||U||_2²<=1+eU. With **rigorous upper enclosures** for these quantities, an assembly-error upper bound and a reference-norm lower bound, the expression could yield a certified lower bound on E_sep. Raw computed residuals, two agreeing SVDs or a safety margin alone are not those enclosures.

The selected next experiment is therefore explicitly an **empirically qualified separability estimate**, with numerical-above-gate versus inconclusive outcomes. It will check two independent constructions, all singular values, norms, decomposition residuals and orthogonality, and retain a fixed numerical separation margin. It will not claim a formal floating-point certificate or unconditional family impossibility. This distinction accounts for unresolved assembly/linear-algebra rounding instead of silently treating a computed singular value as an exact upper bound.

Reference discretization is a second, separate issue. S128 and S256 have qualified convergence evidence but no rigorous continuum-error bound. A stable numerical-above-gate result could motivate ordinary representations with radial/axial dependence. Neither formal exclusion for a saved reconstruction nor empirical spectral evidence alone establishes which causal evolution law should produce that dependence, conserved dynamics, visual benefit, generalization or novelty.
