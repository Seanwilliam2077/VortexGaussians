# T23 — Vol3DGS paper audit

29 October 2026. [v3 HTML](https://arxiv.org/html/2412.03378v3) acquired; no PDF, code, assets, or numerical execution.

| Topic | Classification and inspected extractor lines |
| --- | --- |
| Extinction | Confirmed: weighted unnormalized Gaussian density (§§3.1–3.2, L103–117). |
| Activation | Confirmed: density reparameterization, equation 20 (§5, L185–193). |
| Emission | Confirmed: density-weighted colored overlap reference; sorted approximation assumes separation (§4.1, L134–152; Appendix A, L333–343). |
| Domain | Mismatched: full-line transmission versus our finite clipping (§4.2, L155–166). Ray restriction: Appendix B, L344–379. |
| Color | Unresolved: SH softplus described; [0,1], linear-space and checkpoint guarantees unestablished (Appendix D, L384–390). |
| Errors | Sorting/overlap limitations acknowledged (§7, L245–253). Inspected sections do not establish T21's signed winner-prefix bound or accuracy-controlled fallback. |
| Assets | Official repository link observed, L65–66; checkpoint fields, cameras, background, finite boundaries, complete supports and permissions unqualified here. |
| Culling | Tile heuristics acknowledged (§8, L254–261); omitted-tail validity unresolved. |

**Own assessment:** Mathematical compatibility does not qualify implementation/assets. T21/T22 establish neither workload frequency nor novelty. Paper licensing does not establish asset permission. Domain differences and unresolved color/support semantics prevent transferring T22's timings.

Provenance and retained-response hashes: [ledger](vol3dgs-paper-access.json).
