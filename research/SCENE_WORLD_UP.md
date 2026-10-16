# Scene rotation and upward graph propagation

2026-10-16. The preview's directional graph-heating heuristic previously used
source-space Y as up even after scene pitch changed the displayed orientation.
For source-Z-up reconstructed assets, rotating the scene upright therefore
left the thermal preference pointing sideways.

For the existing scene transform `Q = Ry(yaw) Rx(pitch)`, the source-space image
of world up is `(0, cos(pitch), -sin(pitch))`. The graph now projects the neighbor
offset onto this vector. The zero-pitch branch retains the old arithmetic.
Positive scene scale cancels against the source-space neighborhood radius when
the existing `1e-4` denominator floor is inactive; that floor remains unchanged.
This repairs a coordinate bug in the existing heuristic, not a new transport law.

The frozen comparison encodes the same seven world points in four source
frames, including both quarter-turn pitches and an oblique scaled placement.
After one graph-only step, all four candidate cases match an independent
world-coordinate kernel. The three rotated reference cases reproduce the
directional error. Identity-case initial/final public snapshots are exact
between reference and candidate. Independent verification passed 176 checks;
it retains the three expected reference failures.

Run the live regression from the repository root with Playwright installed:

```powershell
node research/scene-up-regression.mjs --out research/runs/world-up-new
```

Use a new output directory; existing results are not overwritten. Set
`PLAYWRIGHT_MODULE` and optionally `BROWSER_EXECUTABLE` for an external runtime.
The test evaluates expected heat from observed world positions and also checks
the prescribed positions. It does not run rendering or validate real combustion.

The local `outputs/scene-world-up/` evidence package preserves the old reference,
candidate, all eight case records, fixtures, protocol, independent checker and
the live regression result. The separate `outputs/real-asset-static/` checkpoint
verifies actual Firewoods loading and source-camera coordinates. Its strict GPU
half audit remains 102/103 because one subnormal coefficient differs from the
independent nearest-rounding expectation; that discrepancy was not hidden or
repaired. The static camera adapter is not part of this runtime change.
