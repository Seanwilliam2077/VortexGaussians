# B: edited fluid connectivity and pressure projection

28 October 2026. Source-level and analytic screening only; no solver, fixture, timing, GPU work, or creator-demand evidence was produced. The operation remains the one fixed in `CANDIDATES_BEFORE_SEARCH.md`.

**Decision: no-go for implementation from this candidate.** The operation is assessable and admits synthetic inputs, but the proposed component/near-component update does not yet specify a capability or complete-cost difference beyond a valid robust pressure solver. This rejects the current mechanism claim, not all research on changing fluid domains.

## What the two inspected works establish

1. Azevedo, Batty, and Oliveira (2016), *Preserving Geometry and Topology for Fluid Flows with Thin Obstacles and Narrow Gaps*: Section 4 gives a graph-based cut-cell projection retaining distinct sub-cell fluid regions. Algorithm 1 updates the mesh during simulation; Section 7 includes moving solids. Table 2 separates meshing from its reported total. This is direct prior coverage for topology-respecting projection, not evidence of an optimal incremental multigrid hierarchy. [Author manuscript, Sections 4 and 7, Table 2](https://uwspace.uwaterloo.ca/bitstreams/9459a480-4969-40c2-9ef2-11a7244ee7e6/download).
2. Wang, Sun, and Zhu (2026), *Matrix-Free Multigrid with Algebraically Consistent Coarsening on Adaptive Octrees*, arXiv v1: Sections 2–3 develop consistent coarse operators/corrections; Section 4.6 evaluates pressure solves around moving obstacles. Section 2.2 describes a global zero-mean residual adjustment for the all-Neumann case. These passages do not establish componentwise treatment of disconnected chambers or incremental hierarchy-update cost. The arXiv record says submitted to JCP; acceptance is not established here. [Versioned primary text](https://arxiv.org/html/2604.18886v1), [submission record](https://arxiv.org/abs/2604.18886v1).

The reading budget ends here. Neither the absence of an incremental-update experiment in these passages nor lack of an inspected implementation establishes a literature gap. No cited third paper was followed. No code or asset availability claim is made from a paper's references.

## Analytic check of the proposed distinction

The following is our own algebraic assessment, not an experimental result or an additional literature claim.

For a fixed finite-volume graph with row-volume scaling absorbed into the right-hand side, the Neumann pressure operator has the form `A = B W B^T`, with cell–face incidence `B` and positive open-face conductances `W`. Each unanchored connected component contributes one constant null vector. Its scaled right-hand side must sum to zero on that component. A pressure Dirichlet condition removes this freedom only in components connected to that condition. Pinning a gauge cannot repair physically incompatible prescribed boundary fluxes.

A narrow but open channel has small positive conductance. It can introduce a difficult low-energy mode without introducing another exact constant null vector. Merely labeling exact connected components does not address this difficulty. Conversely, thresholding a small positive conductance to zero changes the pressure problem; it is not a free preconditioning improvement unless the original operator and error contract remain intact.

On a fixed set of unknowns, editing a few face weights is a sum of rank-one edge updates. Reusing a valid hierarchy or applying a generic matrix update is not by itself a new mechanism. Real cut-cell edits may also create/remove unknowns, so the fixed-graph low-rank observation must not be promoted to a general geometry-update guarantee. A local coefficient change can alter global low-frequency pressure response; “unaffected geometric region” does not imply “unchanged relevant coarse space.”

The card supplies no update rule, locality/error bound, or amortized-cost condition that resolves this distinction. A proposed experiment comparing a repaired candidate to a baseline retaining an invalid old preconditioner would therefore test an implementation defect. It would not test the current research claim.

## Fair ordinary workflow and complete cost

An admissible baseline uses the same fluid graph, face fractions, boundary conditions, topology information, initial velocity, and acceptance tolerances. It can rebuild robust geometric/algebraic multigrid, use appropriate component gauges and compatible residual projection, and reuse the previous pressure/hierarchy where valid. It must be allowed to update or discard obsolete coarse information. A weak geometric coarsening already known to lose boundary consistency is not the only comparator.

Comparison would cover geometry processing and fluid-state remapping, component/near-mode detection, hierarchy setup/update, all preconditioner applications and linear iterations, failed reuse attempts/rebuilds, memory, and final divergence/boundary-flux validation. Count both the first edit and the complete edit sequence. Pressure values are gauge dependent, so a small change in pressure alone is not a physical acceptance measure. No cost advantage, convergence rate, or production latency requirement has been measured here.

The present periodic FFT core explicitly lacks solid boundaries. It is not a meaningful baseline for this operation without a separately specified boundary discretization. Reusing its name or adding a mask would not supply the missing physics contract.

## Input route, rejection, and what could change the decision

Researcher-authored stationary chambers with an opening/closing zero-thickness passage can define a projection-algebra qualification, with each edited domain's prescribed fluxes explicitly compatible. A moving barrier additionally needs consistent boundary velocity and newly exposed fluid-state semantics. A sealed shrinking volume is not made admissible by subtracting an incompatible mean right-hand side. Such synthetic inputs would still establish neither a creator need nor production benefit.

The cheapest rejection has already occurred: the candidate's stated improvement is standard correctness/reuse intent without a concrete distinguishing mechanism. Do not construct a solver or artificially difficult baseline to rescue it.

Reconsideration would require a specified update operator and an assessable reason it preserves a needed coarse-space property at lower total cost than equally informed robust reuse/rebuild, on an identified admissible edit family. That reason could initially be an analytic bound or a reproducible ordinary-solver bottleneck with full cost accounting. Neither is present. The two-source screen leaves the wider dynamic-topology literature unresolved; it does not justify a novelty claim, another search batch, or automatic solver development.
