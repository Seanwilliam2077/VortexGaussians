# Exact grouping is possible, but does not create generic low rank

This is post-source algebra for the operator in OPERATOR.md. No numerical rank computation, approximation, benchmark or new solver is performed. The claims concern arbitrary admissible algebraic transfer inputs; they do not assert that every such input is reached by a physical VPFM trajectory.

## A sufficient exact moment factorization

Partition active particle positions into common half-cell regions, and retain their literal source stencil/branch classification. For interior groups this fixes the nonzero destinations and the polynomial branch of each quadratic B factor for every component. If a boundary/cast tie requires another class, retain that class rather than changing the source rule. Local coordinates xi within a group avoid unnecessarily large world-coordinate monomials.

On one such region, each weight is a tensor-product polynomial of degree at most two in each coordinate:

\[
w^c_j(\xi)=\sum_{\alpha\in\{0,1,2\}^3} L^c_{j\alpha}\xi^\alpha.
\]

Write the affine particle value as a_pc+sum_d b_pcd y^c_jd in matching local coordinates. Here a and b retain the complete transported gradient and physical dx factors; this is a change of algebraic coordinates, not a new physical fit. For every alpha form

\[
M_\alpha=\sum_p\xi_p^\alpha,\quad
A^c_\alpha=\sum_pa_{pc}\xi_p^\alpha,\quad
B^{cd}_\alpha=\sum_pb_{pcd}\xi_p^\alpha.
\]

Then D and N are recovered by applying L to M and to A+sum_d y_jd B^d. Current destination masks multiply the recovered group contributions, which are added to the global N/D arrays before the original normalization branch. All memberships, coefficient evaluations and reductions cost work. This gives a sufficient ordinary exact factorization, not a unique or optimal one.

There are 27 shared position moments and 27*(1+3) coefficient moments for each of three components: **351 scalars**. By contrast, the three component stencils have at most 27 nonzero entries each, with one numerator and denominator each: **162 direct group-output scalars**. An ordinary hybrid needs **108 scalars**: 81 direct node numerators plus 27 shared position moments to reconstruct all component denominators. These are explicit sufficient constructions. They do not prove that 351 scalars are necessary, that 162 or 108 is a lower bound, or that any construction is faster. Since the default initial sampling has one particle per half-cell before masking, there is no source-level guarantee of aggregation amortization.

## Generic numerator rank already fills the stencil

Restrict to an interior group, one component, zero gradient and variable particle scalar values. The transfer matrix is W_jp=w_j(xp). In one dimension, within a fixed quadratic branch around the nearest grid point, the three weights are

\[
b_-(r)=\tfrac12(\tfrac12-r)^2,\quad
b_0(r)=\tfrac34-r^2,\quad
b_+(r)=\tfrac12(\tfrac12+r)^2.
\]

They span all quadratic polynomials: their sum is 1, b_+-b_-=r, and b_++b_-=1/4+r². Evaluation at any three distinct positions in an open subinterval has rank three, since it is an invertible basis change of the quadratic Vandermonde matrix. Take a tensor product of three such positions in each dimension, entirely within one common branch group. The resulting 27-by-27 three-dimensional weight matrix has rank 27. This proves existence; generic sufficiently populated groups also have full row rank, without needing an empirical SVD.

Consequently a linear factorization W=CR that is exact for arbitrary scalar values on those fixed positions must have intermediate dimension at least 27. Independent values of three components give a block-diagonal numerator map of rank 81; the staggered bases each remain invertible on the common region. The denominator is fixed when positions and active membership are fixed, so it is **not** counted as another independent 81-dimensional lower bound.

This is not a runtime or total-storage lower bound, and full-rank structured transforms may still be fast. It does not rule out acceleration by scheduling, lower occupancy, reusable positions, a restricted physical input set, or a deliberately approximate transfer with a downstream error contract. It rules out inferring exact generic low rank just from having many particles in a stencil. Preserving a few integral moments also does not preserve every discrete numerator, denominator or later velocity solve.

## Research consequence

The source already performs the obvious per-particle transport contraction. Polynomial moment aggregation and direct local output reduction are ordinary algebraic organizations of the same operator. The rank result and initial occupancy give no present reason to prefer a Gaussian or compressed state. A new approximation would need a justified workload/error contract, including the D>1e-5 branch and downstream reconstruction, and a benefit over optimized ordinary transfer including grouping costs. No such advantage is measured or selected here.
