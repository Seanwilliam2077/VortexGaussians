# Research evidence status

Updated 2026-10-16. The released browser prototype, the archived paper, and the
research experiments have different scopes. This page records the current
evidence without treating implementation checks as a new method or acceptance
criterion.

## What the recent experiments establish

| Experiment | Finding | Scope and limitation |
| --- | --- | --- |
| [P4a](P4A_README.md) | Pairwise finite-capacity heat exchange conserves the declared sensible energy. | Authored areas, volumes and capacities; a standard exchange model, not combustion validation. |
| [P4b](P4B_README.md) | The exchange interface drives the actual 3D VPM path with fixed particles; feedback changes the trajectory. | Does not establish Navier–Stokes accuracy, reaction chemistry or particle lifecycle accounting. |
| P5/P5b | Velocity-tree acceptance could omit thermal support. An independent thermal traversal repairs the identified omission. | Differences from the old trajectory measure repair sensitivity, not error against physical truth. |
| [P5c](physical_reference/README.md) | A Float64 direct reference specifies integrated vorticity, source-only Gaussian velocity and its full Jacobian, volume-weighted temperature, and its own gradient. | Static fields and specified ODEs; not a validated coupled flow or combustion solver. |
| [P6](exact_neighbor_reference/README.md) | Exact spatial hashing reproduces the direct exchange graph and update in nine cases. | A standard CPU neighbor baseline; no GPU or full-frame acceleration claim. |
| [P7](shared_state_screen/README.md) | A 512-state material proxy fails the fixed 2% display-temperature tolerance; an 8192-state shared representation passes. | No timing was run because the quality gate failed. This does not establish superiority over stronger proxies. |
| [P7b](proxy32_followup/README.md) | One disclosed follow-up with 2048 material states passes the same quality gates and both cost and storage gates against the shared representation. | A post-result development experiment on two stationary panels with prescribed gas-particle paths; not a held-out result, renderer test or new method. |

P7b reuses the authenticated P7 reference and shared quality trajectory. Its
proxy errors are 0.575% for panel response, 0.881% for regional response and
1.262% for the display-temperature field, each below the fixed 2% tolerance.
Both timing arms were run afresh: six paired blocks with alternating arm order,
each containing one full 120-step trajectory per arm (12 measured trajectories
total). The median of the paired proxy/shared time ratios
is 0.273028 (all six below one), corresponding to 72.7% less time for this CPU
pipeline to the display-temperature buffer. It excludes rendering, GPU work,
file output and the independent audit. It is not a full-system speedup.

The proxy owns 166,912 persistent typed-array bytes and 266,804 bytes at its
largest algorithm phase. The shared representation owns 395,520 and 792,076
bytes; even after an optimistic 196,608-byte deduction for reusing renderer
positions, its corresponding counts are 198,912 and 595,468 bytes. These count
unique ArrayBuffer payloads; unmeasured JavaScript/Map heap is not assumed zero.
They are not process RSS or measured integrated-renderer memory.

The architectural inference is limited: this controlled material-exchange task
does not require one thermal state per visual sample. It does not establish that
separating every vortex and render primitive is always preferable.

## Existing-system engineering update

The existing layered preview now skips already-ineligible graph neighbors
before distance evaluation. A fixed six-run comparison on the synthetic
campfire preserved all saved public states and PNGs, while completed-frame
medians changed from 40.8–42.2 ms to 24.2–24.5 ms on one AMD890M machine.
This standard three-line optimization is not a new method or a modern-method
comparison. See [the engineering record](FRONTIER_EARLY_REJECTION.md) for the
measurement scope, separate evidence archive and old reference source.

## Real-asset coordinate preparation

The Firewoods foreground (34,687 Gaussians) has been loaded without subsampling
and statically rendered through an isolated source-camera adapter. Full source
and world instance arrays, sorting and camera projection were independently
checked. The strict audit is 102/103: one GPU half coefficient differs by one
minimum subnormal step from NumPy nearest rounding. The failure and all raw
results are retained; no full-scene quality or FieryGS reproduction is claimed.

That preparation exposed a separate runtime error: the graph's upward preference
used unrotated source Y. [The coordinate fix](SCENE_WORLD_UP.md) now respects
scene pitch and passes four world-coordinate regression cases. Real-asset
dynamic behavior and strong-baseline advantage remain separate open questions.

## Reproducibility and provenance

P7b source was frozen before its formal run. The producer's five unit tests and
the auditor's twelve metadata/negative checks passed. Independent audit covers
all 121 new states and 251,680 temperature components; independent all-pairs
physical replay covers five fixed steps, not the entire trajectory. The parent
P7 evidence was actually re-audited. Extracting both sealed packages into a new
directory reproduces both complete audit reports exactly.

The source is in this repository. The large evidence archives are separate local
deliverables; they are not silently assumed to be available from GitHub.

| Required archive | Bytes | SHA-256 |
| --- | ---: | --- |
| `VortexGaussians-P7-shared-state-screen.zip` | 254696730 | `e09b48282f81034a724db19dfb29f4b6bd7eacdde92b3f963e90f66ae746b32d` |
| `VortexGaussians-P7b-proxy32-followup.zip` | 4363125 | `3f1e0db992d013571f743c755f679f0121361f2299c00eb261784aa4f1688b52` |

Use the [P7b reproduction instructions](proxy32_followup/README.md) with both
archives. Do not overwrite old runs or edit the byte-pinned sources to reuse an
existing evidence record. Experimental thresholds are project decisions, not
SIGGRAPH requirements.

## Contribution and remaining gaps

No new core method or compelling system-level advantage has yet been
established. Existing work already covers several tempting broad claims:

- [DDFKs](https://arxiv.org/html/2601.17693v1) provides forward fluid simulation
  with divergence-free kernels and vorticity-based updates;
  [Vortex Particle Flow Maps](https://arxiv.org/html/2505.21946v1) transports
  vorticity with flow-map derivatives. Gaussian deformation and Cauchy stretching
  alone do not identify a new solver.
- [GI 2022 surfel/VPM boundaries](https://graphicsinterface.org/wp-content/uploads/gi2022-10.pdf)
  and [VEMPIC](https://www.dgp.toronto.edu/projects/vempic/) are relevant strong
  alternatives for boundary handling. A point-based representation does not by
  itself resolve missing geometry or make a physical boundary uniquely known.
- [HyFluid](https://github.com/y-zheng18/HyFluid) already optimizes vortex
  particles from video; [LagrangianSplats](https://arxiv.org/html/2605.09299v1)
  uses divergence-free transport of Gaussian appearance. High-frame-rate RGB
  alone does not generally identify physical temperature or a unique velocity.

These comparisons reject the currently specified candidates, not every possible
research direction. A system contribution need not invent every component, but
must demonstrate a substantive new capability or quality–cost advantage under
fair comparison. Current evidence does not establish that either.

The next implementation must be motivated by a concrete technical hypothesis
and a baseline capable of using the same information. Do not extend the proxy
resolution sweep, rename standard moment/remapping methods, or start expensive
inverse training merely to produce another phase. Full reaction/lifecycle
accounting, physical boundaries, real asset replay and matched-quality
whole-system evaluation remain missing from the research path. Adding these
features would improve engineering completeness; it would not automatically
establish a research contribution.

Historical media and hardware timings remain author-reported records. The
archived PDF predates these checks and should not be read as the current
validated claim set.
