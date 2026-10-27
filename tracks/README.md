# Two research tracks, one VortexGaussians repository

Started 27 October 2026. VortexGaussians remains the shared project. Its original browser artwork/tool is retained while two distinct research questions develop alongside it.

| Track | Question | Entry | Current claim |
|---|---|---|---|
| TOG technical research | Can an artist revise selected smoke motion while retaining approved imagery, with a useful capability or cost advantage over strong ordinary control? | [TOG workspace](tog/README.md) | Core contribution unestablished; task and bottleneck qualification |
| Art research | How can burning and resetting a captured space become a medium for exploring digital memory? | [Art workspace](art/README.md) · [rehearsal interface](art/index.html) | “Combustible Digital Memory” is a provisional artistic proposition; no audience study or accepted paper |

[Current tasks](STATUS.md) · [Exploration rules](EXPLORATION.md) · [Historical evidence](evidence/README.md) · [Original browser demo](../demo/index.html)

The technical track targets a substantive TOG contribution. The art track develops an independent artwork and practice-based argument suitable for consideration as an Art Paper. An art publication would be a separate outcome, not fulfillment of the TOG objective. A visible effect, passing test suite, or count of research rounds establishes neither contribution.

## Shared assets and independent evidence

The existing `demo/`, `static/`, and `research/` directories retain their roles and histories. The art interface uses the public demo API instead of maintaining a second simulation engine. The TOG miniature uses a separately documented periodic MAC passive-smoke model; it is not the original fire solver or a newly validated Gaussian fluid simulation.

Experiments identify the exact engine, initial state, camera, target provenance, constraints, and measured scope. Historical negative results remain negative. Small readable summaries and figures live in Git; large raw arrays, third-party assets, and personal rehearsal notes stay outside tracked source unless their inclusion is intentional and documented.

Neither line supplies invented evidence for the other: an artist's reaction is not a numerical speedup, and a constraint residual is not an artistic contribution. Reusing code or assets is useful; any papers must explain their distinct questions, evidence, and relationship.

## Run locally

From the repository root:

```sh
python -m http.server 8137
```

Open `http://localhost:8137/tracks/art/` for the art rehearsal, or `http://localhost:8137/demo/` for the original interface. The rehearsal loads its simulation only on request. The bundled campfire PLY is synthetic; importing it is not a real captured-space case study.

The TOG workspace documents its portable Python commands. Planning and task validation should work without initializing a GPU; simulation requires an explicit execution option and the declared runtime dependencies.

## Continuous exploration

The author authorized both tracks to continue on 27 October 2026, with the provisional art theme above. Work proceeds in bounded, reviewable tasks and records what changes the next decision. Initial effort is weighted toward the TOG question while preserving a useful art iteration in each cycle. Resource exhaustion or an explicit pause stops execution; it does not convert incomplete work into a successful result.

The research branch carries the new work without automatically replacing the public historical project page. See the task log for actual commits, validations, remaining gaps, and publication status.
