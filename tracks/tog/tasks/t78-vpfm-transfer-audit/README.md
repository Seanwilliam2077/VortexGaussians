# T78 — the transfer hotspot does not yet justify a new compression method

2 November 2026. The fixed audit acquires four official code/configuration files at VPFM commit `6acf81ae63df994a0826a90450a0a34c1a28ff5f`, verifies their Git blob and SHA256 identities, and derives the actual operator. It finds two decisive constraints: the main per-particle transport contractions are already outside the stencil, and the scalar numerator transfer can have full rank 27 on one interior branch. Neither ordinary contraction hoisting nor a presumed generic exact low rank supplies a new method. **No benchmark or solver implementation follows this candidate.** This does not close all possible P2G acceleration research.

## Published workload and what the source actually establishes

VPFM Table 6 reports the following with-Hessian values on the authors' RTX4090 system. The default acquired source instead selects the moving plesiosaur; exact paper-to-commit/configuration correspondence is unverified. These are published numbers, not our measurements. [VPFM v1, section 9.6 and Table 6](https://arxiv.org/html/2505.21946v1).

| Published 3D case | Total time (s) | P2G (s) | P2G fraction, arithmetic only |
| --- | ---: | ---: | ---: |
| Hopf link | 0.25 | 0.10 | 40.0% |
| Leapfrog | 0.43 | 0.21 | 48.8% |
| Trefoil | 0.26 | 0.10 | 38.5% |

The authors attribute the transfer cost to atomics and suggest GPU-MPM techniques. Its cited paper was not acquired: the inspected bibliography contains no external full-text link, and the fixed scope does not permit another discovery query. This leaves a full primary comparison to that implementation open. The cost fractions only motivate inspecting an operation. If one were exactly 50% and everything else stayed fixed, eliminating it would imply a conditional 2x total upper bound; no realized speedup follows.

## New evidence

[OPERATOR.md](OPERATOR.md) records the complete source-level contract: three staggered edge grids; quadratic B-spline weights; active/domain/solid masks; 192 candidate visits per active particle; separate numerator/denominator accumulation; and division only when D>1e-5. Below that threshold the source retains the numerator. The main Jacobian/Hessian contractions are already per-particle work; the final gradient-matrix addition is written inside the neighbor loop and compiler hoisting is unknown.

[ANALYSIS.md](ANALYSIS.md) supplies an exact algebraic screen. On a common polynomial branch, a straightforward moment factorization needs 351 scalar statistics, direct grouped outputs at most 162, and an ordinary mixed construction 108. These are sufficient representations, not memory minima or speed estimates. More decisively, a tensor-Vandermonde argument constructs rank27 for one component's numerator and rank81 for independent three-component values. This restricts exact linear intermediate dimension for arbitrary inputs; it is not a runtime bound or an impossibility of structured acceleration. Default initial sampling places one particle per half-cell before masking, so high group occupancy is not assured.

The ordinary baseline must allow invariant hoisting, separable weight evaluation, skipping zero terms where semantics permit, binning/sorting, local reductions and blocked scatter/gather. Their complete costs include rebuilds, temporary state, synchronization, grid fills and normalization. There is no new Gaussian requirement or measured advantage from the proposed moments.

## Evidence limits and cost

[SOURCE_MANIFEST.json](SOURCE_MANIFEST.json) records four files/224,093 bytes, one search, four web open/click attempts and ten repository attempts including metadata, one rejected schema call and the author-link verification. The protocol allowed six files, eight web opens and twelve repository calls; unused capacity was not filled. Third-party sources stay ignored. No install, scientific import, compilation, profiler, mesh asset or simulation occurred. One local archive transfer was rejected because the shell command exceeded Windows length limits; the retained tool text was then written through apply_patch and its exact blob hashes verified.

[REVIEW.md](REVIEW.md) contains the participating analyst and separate static review. Neither is an independent run or external peer review. Selected scientific-child subtotal stays2049.958372399793seconds, not project cost; no fresh TOG score. T76's ordinary success remains, art stays paused, and the full SIGGRAPH goal is active and unmet. [DECISION.md](DECISION.md) closes this narrow candidate and identifies the next evidence boundary.
