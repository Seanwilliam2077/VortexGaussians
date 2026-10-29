# T50 — evaluation evidence from the allocated excerpt

This audit received only `local/eval-read.txt`, PDF pages 7–10, in one delivery: **2,503 words including page markers; 22,805 bytes; SHA256 `c2037cea3ed5d7cfa110d8ef01b8536259f8c3334c133a61d3477fa2e0a460f3`**. Hashing and decoding used the same byte buffer. The receipt is `local/eval-reading-receipt.json`. No PDF, other excerpt, page image, linked source or supplemental material was read here. Consequently, the visual statements below report the authors' text/captions, not an independent inspection of rendered figures.

## Paper-derived evidence

Pages 7–10 of *Impulse Fluid Simulation* (DOI 10.1109/TVCG.2022.3149466) report:

- **Validation (p7):** Taylor vortices with kinetic-energy comparison against Eulerian semi-Lagrangian advection; a Karman street with reported Strouhal number 0.161 versus a cited 0.16–0.18 range; and qualitative ink spreading.
- **Smoke (pp7–9):** plume, colliding jets, and sphere/octopus interactions. Plume comparators are semi-Lagrangian plus vorticity confinement, McCormack plus confinement, and IVOCK. Figure 7 specifies IVOCK at `384×192×192`, while the proposed plume uses `256×128×128`; the separate timing paragraph states matching resolution.
- **Reported cost (p8):** over the first ten plume frames, the proposed method reports advection/reinitialization, stretching, viscosity and projection at 617/702/625/1983 ms. IVOCK reports advection, stretching and projection at 1330/397/8719 ms. The proposed solver uses double precision and GPU Poisson; IVOCK uses float and CPU Poisson. These are paper measurements, with implementation/hardware confounds, not local timings or isolated representation costs.
- **Liquids (p9):** tank impact and obstacle streams use PIC/FLIP, level-set surfaces and surface tension. One stream case reports 23% overhead over PIC/FLIP. Hardware attribution is internally unclear: this paragraph names Xeon/V100/256GB, then says the setup matches smoke; p8 names Ryzen/RTX2070/64GB.
- **Control and limits (p10):** large CFL can destabilize stretching. Damped stretching is demonstrated for artistic vortex-scale control; the authors describe its proposed causal explanation as a hypothesis. The discussion identifies Eulerian and hybrid implementations. These pages provide no human trial or creator-study evidence; qualitative flow-detail claims should remain author assessments.

## Implications for the local contract

The relevant comparison target is an entire delivery task with matched output, boundary conditions, error criteria and complete cost accounting. A state-closure proof alone cannot inherit the quoted solver outcomes. A fair future comparison would need to distinguish representation work from advection, diffusion, boundary treatment and velocity reconstruction, while controlling numerical precision and implementation resources.

For T49, the general operation has related evaluation precedent; equivalence of the finite Gaussian state, equal approximation quality, practical cost advantage and usefulness for the user's intended workflow remain **unverified**. Changing a stretching coefficient must be declared as changing the operation rather than presented as evidence of accuracy for the unchanged equation. These are interpretation limits, not permission for a new experiment or a proposed benchmark queue.
