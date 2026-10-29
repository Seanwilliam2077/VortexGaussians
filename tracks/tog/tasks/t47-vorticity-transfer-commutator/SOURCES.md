# T47 — two named primary documents

Read 30 October 2026 under the [scope](SCOPE.md): no search queries, two unique primary HTML documents, no failed document route. Repeated find/open paging remained within these same documents, including reinspection after context compaction; this is a document count, not a count of tool requests. The cap was four documents including failures. No citation following, third family, repository/code acquisition, asset, PDF, installation or locally archived paper. Links pin the inspected arXiv v1 rather than implying a current-version survey.

## DDFKs

[Xing et al., DDFKs: Fluid Simulation with Dynamic Divergence-Free Kernels, arXiv:2601.17693v1](https://arxiv.org/html/2601.17693v1), sections 4–5. Section 4 represents velocity using matrix-valued radial kernels, with particle position, scalar radius and vector weight. Algorithm 1 uses position advection as an initial guess, then physics-based optimization, with periodic reinitialization. Section 5.1 fits initial velocity and gradients through sampled objectives.

This supplies an existing divergence-free velocity representation and an evolution strategy. It does not by itself supply an exact constant-vector Gaussian Cauchy-transfer contract, or verify the local implementation. No reported speed or accuracy is imported as our measurement; no failure of DDFKs follows from T47's different raw-source operation.

## Vortex Particle Flow Maps

[Wang et al., Fluid Simulation on Vortex Particle Flow Maps, arXiv:2505.21946v1](https://arxiv.org/html/2505.21946v1), sections 3.2, 4.2, 4.4 and 5.2–5.3. Equation 12 transports vorticity by the forward flow-map Jacobian; equation 13 includes derivatives of that Jacobian when transporting vorticity gradients. The discrete method carries vorticity, its gradient and flow-map derivatives on particles, transfers quantities to a grid, and reconstructs velocity through vector-potential Poisson solves with additional boundary treatment.

This is an existing coupled transport/reconstruction alternative. Its bounded discrete hybrid solver is not identical to T47's whole-space multiplier model. We neither infer its error from the commutator nor claim it implements the exact proposed Q_F formula. Published performance is not a local comparison.

## Scope of inference

The repository already named both families; this round examines their relevant representation/evolution contracts rather than claiming newly discovered prior work. Together they prevent treating “divergence-free kernels” or “Cauchy transport with flow-map derivatives” as sufficient novelty. The ordinary weighted projection in [ANALYSIS.md](ANALYSIS.md) is derived there algebraically. These two documents do not constitute an exhaustive novelty search or establish any comparative advantage. No source absence is interpreted as a contribution.
