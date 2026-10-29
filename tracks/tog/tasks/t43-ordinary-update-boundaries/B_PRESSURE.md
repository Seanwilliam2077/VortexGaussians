# B — exact port deletion and an ordinary feasible-cycle bound

This is one edge-deletion construction within T15-B. It resolves T39's single-bridge task trap without assuming that pressure conditioning measures flow-output difficulty. It is algebra on a fixed weighted graph, not a solver benchmark, new geometry model or novel-method claim.

## Fixed projection and edge closure

Let B be an oriented vertex-edge incidence matrix of a connected graph, W a diagonal matrix of positive conductances, R=W^(-1), and L=BWB^T. The graph has no external sources/sinks or moving boundaries. The prescribed predicted flux u is fixed. Use the compatible zero-mean inverse L^+ and define

```text
J(q) = (1/2) (q-u)^T R (q-u),       Bq=0,
P_W = I - W B^T L^+ B,
q0 = P_W u.
```

P_W is the orthogonal projection onto the cycle space ker B in the R inner product. Closing edge e means adding the exact constraint q_e=0, leaving all other unknowns, conductances and predicted fluxes unchanged. Work in the old edge coordinates with the closed edge constrained to zero. This is not a moving-wall remap or an approximation that merely assigns a very small conductance.

Write b_e=B e_e and

```text
g = P_W W e_e = w_e P_W e_e,
k = e_e^T g = w_e (1 - w_e b_e^T L^+ b_e).
```

For any z in ker B, R-orthogonality gives <g,z>_R=z_e. Taking z=g yields k=||g||_R^2>=0. If k>0, the unique closed-edge projection is

```text
q* = q0 - (q0_e/k) g,
||q*-q0||_R = |q0_e| / sqrt(k).
```

Indeed g_e=k makes q*_e=0 and Bg=0 preserves divergence. For any competing feasible adjustment delta, delta+(q0_e/k)g has zero e coordinate and is orthogonal to g. Pythagoras therefore makes the displayed adjustment the minimum R-norm one. Because q0 was already the unconstrained projection, this also minimizes J after closure.

For a bridge, every circulation has zero flux on that edge; k=0 and q0_e=0. Deletion leaves q0 feasible and optimal. This statement does not apply to a bridge carrying prescribed net boundary flux: closing that edge could make the boundary data incompatible. Do not divide 0 by 0 or silently subtract a component mean to hide incompatibility.

## Projection objective is not flow energy

With the complete old edge objective retained,

```text
J(q*) - J(q0) = q0_e^2 / (2k).
```

If the new objective omits the deleted edge term entirely, its value at the same optimizer is smaller by u_e^2/(2w_e). Thus the difference from old J(q0) is q0_e^2/(2k)-u_e^2/(2w_e). This is an objective bookkeeping constant, not a different remaining flow.

The projected flow's own squared R norm moves in the opposite direction:

```text
(1/2)||q*||_R^2 = (1/2)||q0||_R^2 - q0_e^2/(2k).
```

Neither expression is called a physical energy law without the corresponding discretization/units. The appropriate output-change measure here is the declared weighted flux norm, not gauge-dependent pressure values or an unspecified visual error.

## Two ports make a nontrivial flow change

Consider two connected chambers A/B with two ports, both oriented A to B. Let their fluxes be (f,-f), their positive resistances be r1/r2, and each chamber's compatible unit source/sink vector d_i cancel the divergence caused by those port fluxes. Define

```text
h_i = W_i B_i^T L_i^+ d_i,        B_i h_i=d_i,
q_i^0 = P_(W_i) u_i,
v = (h_A, h_B, 1, -1),
H = ||v||_R^2 = r1+r2+sum_i d_i^T L_i^+ d_i.
```

The h_i are minimum-norm unit transport flows and are R-orthogonal to each chamber's internal circulations. Consequently the old projected flow is the independent chamber projections plus f v, with

```text
f = [sum_i h_i^T R_i u_i + r1*u1 - r2*u2] / H.
```

Closing port 1 makes port 2 the sole bridge, so the new exchange flux is zero while the chamber circulation projections stay q_i^0. For deletion of port 1,

```text
g=v/H,       k=1/H,
q*-q0=-f v,  ||q*-q0||_R=|f| sqrt(H).
```

For port 2 the corresponding g has the opposite sign. Unlike T39's lone bridge, a two-port circulation can carry nonzero projected exchange. Its deletion changes a global flow component. But the output change depends on both f and H; poor pressure conditioning alone supplies neither that change nor evidence that an ordinary update is expensive.

## A cheap ordinary competitor must also be allowed

An exact new g generally costs one old-system solve L^+b_e and a full gradient application; a two-chamber construction can instead precompute one compatible response per chamber. It would be incorrect to infer that every useful error bound requires those solves.

Take any known cycle z with Bz=0 and z_e=1. For two ports, one path through each chamber and the two ports supplies such a vector. Put E_z=z^T Rz and form

```text
q_hat = q0 - q0_e z.
```

This is already divergence-free and has zero flux on the closed edge. Since g/k is the minimum-norm unit cycle through e, it is orthogonal to z-g/k and

```text
||q_hat-q*||_R^2 = q0_e^2 (E_z - 1/k).
```

For the two-port graph 1/k=H>=r1+r2. Hence an explicit sufficient bound needing no new pressure solve is

```text
||q_hat-q*||_R <= |q0_e| sqrt(E_z-r1-r2).
```

The right side uses the known cycle and the two port resistances. A looser general bound is |q0_e| sqrt(E_z). The two-port radicand is nonnegative over reals because E_z contains both positive port terms and nonnegative chamber terms. This bound may be very loose; no useful tolerance has been demonstrated here. It is nevertheless a valid ordinary alternative, unlike merely zeroing the edge and leaving other flows unchanged, which generally violates divergence.

The identity and bound follow from feasible circulation and variational projection. They do not supply a distinct representation or new solver. A fair ordinary comparator can use the same cycle, information and norm tolerance, falling back to exact projection when necessary.

## Full cost, stability and decision

Exact response setup includes the solve, gauge/compatibility treatment, residual control and gradient computation. Storing and explicitly applying a dense edge response is O(|E|), even if its scalar coefficient is cheap. A fixed set of linear output measurements can cache their responses, but that does not deliver a full field for free. Repeated closure/reopening of the same fixed port can reuse responses; ordinary Schur or rank-one matrix updates receive the same reuse. New predicted velocities generally still require their ordinary projection, and changed chamber geometry can invalidate the cached responses.

A cycle approximation pays path acquisition (worst-case O(|E|) graph traversal), resistance accumulation and norm-bound evaluation; a cached path update touches only its path edges. It does not certify pointwise velocity, visible smoke motion or a moving obstacle. No complexity claim hides topology/remapping/setup costs of a different task.

The expression 1-w_e b_e^T L^+b_e can suffer cancellation for a near-bridge edge. A small rounded value cannot be reclassified as an exact topological bridge. Approximate inverse errors, stable solve formulations and a conservative bound would need explicit control in an implementation. Every displayed identity here is over exact reals, not a floating-point certificate.

The two-port case makes the flow task nonempty and gives an exact output-sensitive quantity plus a cheaper ordinary sufficient bound. All are obtained from the same constrained quadratic projection. No distinct method or equal-total-cost advantage remains established, so no implementation or numerical queue is selected. This rejects the current mechanism claim, not every future method for topology edits.
