# T39 local checks of the previously identified A/B operations

These are finite mathematical arguments by the research agents, not a fourth operation, numerical experiment, new literature survey or domain-wide impossibility claim. They revisit the original T15 cards to determine whether there is a concrete alternative to implement. Neither is selected.

## A: conservative coarse state plus optical residual

For a fine density rho_f and moment-matched coarse density rho_c, write r=rho_f-rho_c. The residual has zero zeroth, first and second moments. Under the same invertible affine map x'=Fx+b, its push-forward keeps these zero moments. Rendering rho_c+r restores the original density exactly.

But retaining r exactly normally retains the fine components and a negative copy of the coarse component. The signed residual is not separately a nonnegative physical density; the identity supplies no memory or rendering saving. Truncating/compressing it returns to ordinary multiresolution representation and error-controlled mixture reduction. A fair baseline can also keep coarse physical and fine optical states, with the same budgets. Under affine motion, directly pushing forward the original Gaussians is already available.

A broader exactness boundary follows directly from line integrals. Equal transmittance along every complete ray implies equal line integrals for finite optical depths. Taking the two-dimensional Fourier transform over offsets of rays in a fixed direction gives the density's Fourier transform on the perpendicular plane. All directions cover Fourier space, so integrable densities with these identical projections are equal almost everywhere. Thus exact preservation of all optical projections requires preserving the density itself; mechanical moments alone cannot remove a real representation change. This is an elementary uniqueness argument, not a new theorem or a claim about finite-view approximate compression.

No distinct inexpensive residual representation or reconstruction rule emerged. The shared-state README read here supplies reproduction instructions, not a universal negative result about shared representations. T15's narrower rejection remains unchanged.

## B: topology edits and pressure projection

For a fixed connected fluid graph with incidence B and positive edge conductances W, let A_0=BWB^T on a fixed zero-mean/gauge subspace. Modifying r edge coefficients gives A_1=A_0+UDU^T. When both operators are invertible on that same subspace,

```text
A_0^(-1/2) A_1 A_0^(-1/2) = I + V D V^T,
V = A_0^(-1/2) U.
```

On a d-dimensional gauge subspace, the whitened relative operator above retains at least d-r eigenvalues equal to1 (the statement is vacuous for r>d). This does not say that only r eigenvalues of the original unpreconditioned pressure matrix move. Ordinary Woodbury/Schur-complement reuse already exploits this algebra, but building the interface matrix generally costs r old-operator inverse applications. Disconnection introduces new nullspaces and compatibility constraints; the invertible formula cannot simply be applied across that change. No new update rule or saving follows from the low rank alone.

There is also a task-value trap. In two sealed chambers connected by a single bridge edge, any divergence-free flux q satisfies 1_S^T Bq=q_bridge=0, up to the chosen sign convention. With fixed interior weights and predicted interior fluxes, the constrained weighted least-squares projection's internal minimizers are independent of the positive bridge conductance: its cost term is constant because q_bridge is fixed to zero. Closing that bridge gives the same internal projection. The pressure matrix can approach singularity without producing a difficult change in the projected velocity. Multiple openings or moving boundaries need their own analysis; this bridge argument does not cover them.

The missing ingredient remains a specific update rule with a full-cost advantage over robust ordinary reuse/rebuild on edits that actually change the flow. Neither poor pressure conditioning nor refusing the baseline valid component information provides it. No chambers were generated and no solver was run.

## Scope

Read-only agent inputs: T15 A_TRANSFER.md, B_PRESSURE.md and CANDIDATES_BEFORE_SEARCH.md; T38 NEXT_ENTRY.md; research/shared_state_screen/README.md. Root also reread existing research evidence summaries to avoid reviving previously rejected architecture claims. These checks make ordinary remedies and limiting cases explicit; they do not select a fresh experimental queue.
