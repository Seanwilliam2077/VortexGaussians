# T78: audit one published particle-to-grid bottleneck

2 November 2026. T76/T77 changed the authoritative state and next decision; the preceding goal turn was substantive progress. The worktree is clean at 68f06c9 and no relevant numerical job is running. Art remains paused. This task does not reopen T77's exhausted broad screen or start another synthetic flow.

## Concrete operation and question

The already identified Vortex Particle Flow Maps paper reports particle-to-grid (P2G) transfer as roughly half of its measured runtime and explicitly points to atomic operations. This is evidence about a published implementation, not a local measurement or an unavoidable lower bound. Audit its actual transfer operator and cost context before selecting any system/method hypothesis.

Determine whether a useful remaining problem lies in the transfer's numerical information requirements, or in ordinary implementation organization. Specifically, can grouping particles with a common transfer stencil preserve the exact discrete numerator and normalization from a fixed number of polynomial moments? If so, identify whether that is merely ordinary local reduction, whether deformation/Hessian terms really prevent it, and which costs it changes. Do not assume Gaussian primitives, particle compression, new approximation or new physics are necessary. A standard optimized scatter/gather/grouping implementation must be an allowed baseline.

## Fixed read-only budget

- One exact web search: `Fluid Simulation on Vortex Particle Flow Maps official code github`, only to locate its author-linked project/repository. No replacement search or other method discovery query.
- At most two primary texts: the fixed VPFM arXiv v1 and its already cited GPU-MPM work if an official link is available. At most eight web open/click retrieval attempts, including failed access; on-page finds are permitted. No other paper family or citation chase.
- Inspect exactly one official VPFM repository at one recorded commit. At most six distinct relevant code/configuration files, plus README/LICENSE and bounded repository/commit/tree metadata. At most twelve repository retrieval attempts including failures; no fallback to a different implementation. Prefer the GitHub connector; record any capability/access failure before a direct public read fallback.
- Source files may be retained in ignored local storage with byte/hash/source identity. Do not vendor third-party code or assets into the research branch. No clone, install, compile, GPU/CPU scientific run, reference generation, profiler run, scenes or data acquisition.

## Required result and stop

Write the actual transfer equation, stencil/boundary/normalization semantics, how transported derivatives enter, and a symbolic full-work ledger including grouping, storage and rebuilds. Relate it to the paper's specific workload/cost report without claiming identical source-to-paper reproduction. Identify the strongest ordinary transformation that leaves the discrete field unchanged.

End with either one concrete falsifiable operation-level hypothesis that survives the ordinary-alternative check, or no selected method. Algebraic equality alone is not a new algorithm; fewer atomic updates alone are not a measured speedup. If access or semantic dependencies exceed the fixed budget, retain the exact gap. Do not add a new benchmark or solver automatically. Historical gates, results and ratings remain unchanged; the full research objective stays active and unmet.
