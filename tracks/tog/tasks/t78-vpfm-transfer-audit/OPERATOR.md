# Actual pinned P2G operator and full-work boundary

Source inspected at official VPFM commit `6acf81ae63df994a0826a90450a0a34c1a28ff5f`. These are static source facts, not observed runtime behavior or a reproduction of the paper's performance. Only four code/configuration files were needed. The code remains in ignored local storage, with identities in SOURCE_MANIFEST.json.

## Inputs, transported coefficients and outputs

[run_vpfm.py lines 1060–1158](https://github.com/pfm-gatech/VPFM/blob/6acf81ae63df994a0826a90450a0a34c1a28ff5f/run_vpfm.py#L1060) defines P2G_w. Use the matrices **as assembled by that code**, without silently changing rows to columns to match a theoretical convention. For an active particle p, let Fg, T, F0 and C be the matrices constructed by Matrix.rows from the corresponding stored vectors. Define

\[
v_p=(F_gF_0)\omega_{0p},\qquad
G_p=F_gC_pT+\sum_{j=0}^2 H_{jp}\,\omega^{mid}_{pj}.
\]

The Hessian sum is included when use_hessian is true. The gradient term in the deposited value is included when use_APIC is true; both are true in the inspected configuration. All three matrix products, the matrix-vector product and the Hessian contraction occur **before** the neighbor loops. The final addition of the two gradient matrices is literally written inside the loops; compiler hoisting is unverified. Hoisting that addition is an ordinary loop-invariant optimization. A proposed optimization that merely moves the main contractions outside the stencil is already present. This extraction does not revalidate the source's tensor conventions against the continuum equations.

For component c, grid index j denotes physical edge location

\[
x^c_j=\Delta x\,(j+o_c),\quad
o_x=(1/2,0,0),\quad o_y=(0,1/2,0),\quad o_z=(0,0,1/2).
\]

The scalar kernel B is the compact quadratic B-spline: 3/4-r² for |r|<1/2, (3/2-|r|)²/2 for 1/2<=|r|<3/2, and zero otherwise ([taichi_utils.py line 1956](https://github.com/pfm-gatech/VPFM/blob/6acf81ae63df994a0826a90450a0a34c1a28ff5f/taichi_utils.py#L1956)). The weights are the product of three B evaluations at component-staggered distances. Let A^c_{jp} additionally encode the literal loop reach, domain tests, particle-active test and edge mask. The accumulated arrays are

\[
D^c_j=\sum_p A^c_{jp}w^c_{jp},\qquad
N^c_j=\sum_p A^c_{jp}w^c_{jp}
\left[v_{pc}+G_{p,c:}(x^c_j-x_p)\right].
\]

The output is N/D **only if D>10^-5**; otherwise the initialized-and-accumulated N is retained. It is not unconditionally divided, discarded, or divided by max(D,epsilon). Any replacement must preserve this branch, both arrays and every active contribution. Algebraic equivalence over real numbers does not imply bitwise identical parallel floating-point sums or an unchanged near-threshold branch.

## Stencil and boundaries

Each component computes base=int(xp/dx-o_c), then visits offsets {-1,0,1,2}³: 64 entries per component, 192 per active particle. Preserve the source's integer conversion, particularly near domain edges; do not silently replace it with floor. For x edges, the x index permits the full allocated range, while y/z exclude their outermost indices; y/z components permute that rule. The destination's edge_boundary_mask must be <=0. These tests occur before kernel evaluation. Nonzero support contains at most 27 destinations per component, but the source does not explicitly skip a reached zero weight before the two shared-array additions. Generated GPU instructions were not inspected.

[mask_particles, line 1162](https://github.com/pfm-gatech/VPFM/blob/6acf81ae63df994a0826a90450a0a34c1a28ff5f/run_vpfm.py#L1162) disables positions outside the open simulation box and positions whose center-cell mask is solid. The transfer receives current masks as inputs; constructing their moving-mesh geometry is a separate cost, not replaced or validated by this audit. Arbitrary fixed destination masks can be applied after exact within-group summation, since the same mask applies to every contribution to that destination.

## Call path and actual inspected configuration

The main step advects particles and derivatives, calls mask_particles, then calls P2G_w once at line 1433; vector-potential reconstruction and boundary work follow. The optional midpoint stage has its own grid transport/reconstruction, not a second call to this particle scatter. Reinitialization and gradient reset occur before advection. This is the selected source path, not every possible configuration.

[hyperparameters.py](https://github.com/pfm-gatech/VPFM/blob/6acf81ae63df994a0826a90450a0a34c1a28ff5f/hyperparameters.py) selects the moving plesiosaur, resolution 127x63x127, eight particles per cell, midpoint/APIC/Hessian enabled, positional reinitialization every 20 steps and gradient reinitialization every step. The source allocates 8,129,016 particles. [init_conditions.py line 391](https://github.com/pfm-gatech/VPFM/blob/6acf81ae63df994a0826a90450a0a34c1a28ff5f/init_conditions.py#L391) initially places one at each half-cell center before solid masking. Therefore high occupancy in a common half-cell branch cannot be assumed. Occupancy after advection was not measured.

The checked configuration is **not** a fixed reproduction of Table 6's Hopf-link/leapfrog/trefoil timing cases. Initial conditions for that table, exact timing instrumentation and paper-to-code commit correspondence are unverified. The repository's default also requires an external moving-mesh sequence; none was acquired. No end-to-end speed comparison is available.

## Symbolic work ledger

Let P be active particles, G total allocated edge entries, and B_g occupied groups after any chosen partition. This is an accounting template, not a profiler result.

| Work | Original or ordinary baseline | Extra obligations of grouping/moments |
| --- | --- | --- |
| Transported coefficients | Main contractions already formed once per active particle; O(P) fixed-size work; final gradient addition remains written in the neighbor loop | Same work, unless a distinct approximation is justified; storing coefficients adds bytes |
| Destination traversal | 192 source-level visits per particle; domain/mask tests; at most 81 nonzero component destinations | Build keys, classify branches and count/scatter or sort particles; grouping must be rebuilt or maintained after motion |
| Contributions | Two shared-array additions per reached destination; at most 384 syntactic additions per interior particle including zero-weight cases | Ordinary local grid-array reduction is allowed; count every local reduction, synchronization and flush, not only final global atomics |
| Grid maintenance | Six component-array fills (N and D) and three normalization traversals, O(G) | Retain these or account for a demonstrably equivalent sparse scheme and its metadata |
| Temporary storage | Existing particle and grid fields | Keys/indices/counts/offsets, reordered state or indirect reads, per-group coefficients/output arrays and any overflow path |
| Pipeline | Advection, reinitialization, mesh masks, Poisson/boundary work, I/O | Unchanged work stays in the total; no savings charged against it without evidence |

For a half-cell branch group, straightforward shared polynomial moments use 351 scalar channels, while direct group outputs need at most 162 scalar entries. An ordinary hybrid uses 81 node numerators plus 27 shared position moments for denominators, or 108 scalars. These counts exclude bookkeeping and are not minimal-rank claims. Fusing evaluation can avoid global materialization, but must charge local storage, register/shared-memory pressure and reduction work. [ANALYSIS.md](ANALYSIS.md) derives these statements and the exact-rank limit. A faster kernel or a useful system contribution is not established by this ledger.
