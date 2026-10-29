# T50 — Impulse Fluid Simulation contract audit

30 October 2026. **Completed single-source audit; no new solver, simulation or established TOG contribution.**

The acquired author version of *Impulse Fluid Simulation* directly supplies the ordinary impulse-field algorithm relevant to T49: grid/particle-grid evolution, gauge management, projection and boundary operations. Its reinitialization exposes a specific mismatch with retaining a single localized Gaussian potential. That mismatch and the existing prescribed-flow closure leave nonlinear, self-consistent evolution unproved; neither is evidence of practical advantage.

- [Scope and predeclared budget](SCOPE.md)
- [Source identity, acquisition and reader limitations](ACQUISITION.md)
- [State, gauge and algorithm mapping](METHODS.md)
- [Paper-reported evaluation and confounds](EVALUATION.md)
- [Six-page visual equation check](VISUAL_CHECK.md)
- [Shared reading ledger](reading-ledger.json)
- [Decision and complete comparison contract](DECISION.md)
- [Prepared next analytic consistency question](NEXT_EVIDENCE.md)
- [Independent review](../../../validation/t50-contract-review.md)
- [Publication manifest](audit-manifest.json)

One new acquisition: 24,089,500 bytes, HTTP 200, zero redirects, 4.109 seconds, no retry. T49's prior oversized-response failure remains unchanged. The source is an IEEE TVCG accepted author manuscript (DOI 10.1109/TVCG.2022.3149466), not a verified latest/final typeset version. Source PDF, extracted text, page images and temporary tooling remain ignored locally.

All paper outcomes remain attributed reports. Actual acquisition and reading costs are recorded separately from absent scientific execution. Published timing confounds and printed equation inconsistencies are retained. The next task is prepared only; no new source batch or numerical run is selected. Full research goal active, art inactive, automation deleted, main unchanged.
