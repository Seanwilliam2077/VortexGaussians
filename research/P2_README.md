# P2 explicit area-measure diagnostics

P2 asks whether changing a scene's sampling changes combustion and feedback when the represented surface area is held fixed. Read [P2_PROTOCOL.md](P2_PROTOCOL.md) before interpreting the results. Successful duplicate splitting is a representation check; actual grid refinement is a separate convergence experiment.

The default `spreadMeasureMode: 'legacy'` preserves the original per-node coupling. The opt-in `area` mode requires `spreadClockMode: 'elapsed'` and a finite positive `areaWeight` for every point passed to `__demo.research.setScene`. Missing area is rejected. The `analysisWeight` used by the harness to calculate summary metrics is a separate field and is never silently used as simulator input. Ordinary PLY scenes do not provide the required measure.

In area mode, a burning source's graph contribution is multiplied by its area divided by `spreadReferenceArea` (default 0.0016 in squared scene-coordinate units). Recipient heat, fuel fraction, and char fraction remain intensive. Scene feedback schedules `spreadAreaFeedRate` (default 30) particle events per second per reference area. Sources are selected by area after canonical ordering and coalescing of exactly coincident live source positions. The new schedule does not retain the legacy extra 0.5 admission coin: 30 already includes that factor at the original 60 Hz step rate.

Only fractional event credit carries between steps. Integer work beyond the scene-feed cap is explicitly dropped, capacity rejection consumes an event, and remaining fractional credit is cancelled when no live source remains. Thus finite work caps and finite particle capacity still matter. These policies do not establish physical energy conservation: heating does not deduct solver energy, the kernel is heuristic, and P1 cold-particle recycling still discards state.

Use Node.js 20+ and the same Playwright/Chromium or Edge setup as [P0](README.md). From the repository root:

```sh
node --test research/tests/*.test.mjs
node research/p2-smoke.mjs --out research/runs/my-p2-smoke
node research/p2-run.mjs --suite all --out research/runs/my-p2-full
```

Set `PLAYWRIGHT_MODULE` and `BROWSER_EXECUTABLE` to existing local installations if needed. Use a fresh output directory for each run. The manifest saves the protocol, source hashes, environment, seeds, configuration, and case outcomes; raw JSON retains all sampled point states. Software execution status and the scientific invariance result are distinct: a completed experiment can demonstrate a failed hypothesis.

For custom experiments, always use `setScene → reset → ignite → step`. The event ledger is bounded by `reset`: replacing a scene clears its fractional credit but does not reconcile counters from a previous run. Changing a scene midway without resetting is outside this protocol.

The main matrix has 56 cases: 24 graph-only duplicate/order comparisons, 8 graph-only uniform/adaptive refinement comparisons, and 24 closed-loop duplicate comparisons over three seeds. Refinement uses cell-centred partitions of a fixed rectangle, with an exactly aligned initial source patch and retained coarse anchors. Duplicate variants include spatially variable multiplicity, so equal total point counts are not used as a proxy for equal represented area.

The synthetic area values are known by construction. Applying this approach to reconstructed Gaussian scenes still requires an explicit surface/material model, handling of overlapping splats, validation of physical scale and material parameters, and real-scene quality and performance comparisons. Quadrature weighting alone is not a novelty claim.
