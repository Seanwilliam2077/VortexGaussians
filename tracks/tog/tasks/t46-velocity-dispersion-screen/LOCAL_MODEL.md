# T46 local model applicability audit

Parent commit supplied for this task: `6a8a24316f9cf7072ca63cfe8fb6802f4556e5da`.

This is a targeted, static audit of four existing model files. It asks whether the proposed loss of velocity dispersion under an affine-momentum Gaussian merge describes an operation already implemented or qualified locally. It does not execute a simulator, test a scene, establish a measured defect, or assess external novelty.

## Scope and identities

Filename discovery used `rg -l -i --glob '*.md' --glob '*.mjs' --glob '*.py' --glob '*.html' 'kinetic|APIC|affine momentum|affine state|merge|split' research demo/index.html`. Discovery returned filenames; subsequent content inspection was limited to the four files below, using keyword matches and bounded relevant windows. The line spans cited below are the evidence windows for the conclusions, not a claim that all surrounding code was reviewed. No fifth model file, external source, or numerical execution was added when writing this report.

Whole-file SHA256 and byte counts identify the current source bytes whose selected lines were reviewed. The supplied parent commit is context; this report does not substitute these hashes for a separate Git ancestry check.

| Repository-relative file | Bytes | SHA256 |
|---|---:|---|
| `demo/index.html` | 314044 | `e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0` |
| `research/P2_README.md` | 3670 | `060225da8f8eab9fe6e67718dd376eb6b6a97c99e6713ff7b95765e83888da80` |
| `research/physical_reference/README.md` | 1628 | `c5a13bf21d03b7489b62bb06f0bd0b1d1f82fd36666279866576b5369dd1af9b` |
| `research/shared_state_screen/PROTOCOL.md` | 25977 | `ba4afa4b0d72dac0ec38190a11b75b3c4ab18e07b92999c161a7896a2eb99211` |

The initial T46 protocol/mathematical-context reads by the parent and other agent are separate from this four-file targeted model audit. This report neither counts their context reads as additional model files nor claims to have independently inspected them. Search matches and a limited selection cannot establish repository-wide absence of a feature.

## What the inspected demo actually stores and updates

**Layered visual covariance is not an affine momentum state.** `demo/index.html:203–204` labels a covariance/strain control, but the implementation at `1589–1604` updates the three entries `sxx/sxy/syy`, relaxes toward identity, normalizes the determinant and limits anisotropy. The name `evolveF` alone does not establish a stored deformation gradient or APIC momentum tensor. Emitted layered particles at `1613–1617` contain position, circulation `G`, temperatures, density, velocity, visual covariance and scalar kernel width `sg`; the comment distinguishes rendering temperature from dynamics temperature. The VPM packing at `2073–2075` uses position, `G`, dynamics temperature and `sg`, rather than those visual covariance entries.

**Particle velocity is evaluated from the current field.** In `2093–2117`, `stepSimVPM` obtains the VPM field, adds the existing buoyancy/director/turbulence/wind terms, applies its speed cap, assigns particle `vx/vy`, evolves circulation and visual shape, then advects the particles. Cooling, density decay and retirement follow at `2118–2120`. Thus a saved `vx/vy` is not, by itself, an independently conserved mechanical momentum parcel.

The 3D variant is described at `2125–2130` as a vector-circulation Gaussian-regularized Biot–Savart control. Its step at `2336–2417` uses a fixed reference volume (`2353–2354`), packs position/circulation/temperature/kernel width (`2359–2362`), evaluates field and stretching (`2367–2375`), updates circulation and reassigns velocity from the field plus forcing before advection (`2388–2401`). The closed branch retains thermal parcels (`2403–2410`). These passages do not implement the proposed replacement of a joint position–velocity distribution by one persistent affine-momentum Gaussian.

**Rendered splats do not automatically supply mechanical mass.** P3 display particles use a fixed camera billboard/radius and optical weight (`2676–2682`). The 3D display path produces camera billboards or trajectory filaments with size depending on density/speed (`2686–2708`). Layered cooling expansion is explicitly rendering-only, and the display axes use `sxx/sxy/syy` (`2715–2725`). Inferring physical mass or kinetic energy directly from these display covariances would add a model assumption absent from these passages.

**P3 affine groups are transient field approximators.** The comment at `3650–3652` explicitly states that groups are rebuilt each step from old positions, are not persistent particles/carriers, and do not reorder the live tracer array. The split at `3655–3674` partitions a group by spatial extent; it is not a mechanical particle split. `p3AffineModels` uses a center and six offset stencil points to estimate a velocity Jacobian and temperature gradient (`3677–3698`). It reconstructs a local field at each original tracer (`3701–3713`); the subsequent score is explicitly heuristic (`3715–3717`). The stepping path rebuilds these groups/models, reconstructs the field, and advances retained tracer particles (`3877–3904`). This is prior local overlap with affine field approximation, but not evidence of a persistent Gaussian merge that discards the residual covariance in T46.

## Existing measure, split and energy qualifications

`research/P2_README.md:3–9` separates duplicate splitting from grid refinement, requires explicit positive area weights for area mode, and describes area-weighted source injection with intensive recipient material state. It explicitly declines physical energy conservation: heating is not debited from a solver energy, and the kernel is heuristic. The documented suite (`23`) concerns authored-area duplicates/order/refinement/closed-loop checks. The remaining real-scene requirements at `25` include a surface/material model, overlap handling and physical scale/parameters. These are relevant prior warnings against confusing Gaussian count with measure; they do not qualify a kinetic-energy-preserving mechanical merge.

`research/physical_reference/README.md:3–7` describes an isolated ordinary reference with explicit `Gamma = volume * vorticity`, a source-only Gaussian Biot–Savart field, its Jacobian and volume-weighted thermal interpolation. Its stated checks and exclusions (`30–34`) include measure/split consistency and small ODE checks, but exclude coupled Navier–Stokes, walls, combustion, long-time dynamics, rendering, speed and novelty. These are documentation claims about that reference; its Python implementation was not opened or executed in this audit. The README does not establish an affine-momentum merge or kinetic-energy transfer rule.

`research/shared_state_screen/PROTOCOL.md:7–11` compares shared thermal state with an ordinary proxy while explicitly omitting VPM, a velocity solver, buoyancy, pressure, mechanical wall interaction and rendering. Area/capacity is authored rather than inferred from opacity, covariance or count (`24`); gas capacity and the thermal-energy ledger are explicit and omit birth/removal/split/clamp (`34`). Its affine velocity field and trajectories are prescribed (`36–42`). A prescribed affine trajectory is not an evolved mechanical affine-momentum state, and this thermal ledger is not a kinetic-energy merge test.

## Applicability judgment

For an explicitly declared positive physical mass measure, let normalized mass-weighted moments be `Cxx = Cov(x)`, `Cvx = Cov(v,x)` and `Cvv = Cov(v)`, with invertible `Cxx`. Replacing the original velocities by the least-squares affine field with `A = Cvx Cxx^-1` gives residual covariance

`R = Cvv - Cvx Cxx^-1 Cvx^T`,

which is positive semidefinite. With total mass `M`, the removed kinetic second moment under this declared mass-weighted joint-state interpretation is `M trace(R) / 2`. This is a mathematical consequence of that declared regression/merge model, not an empirical result from the four inspected files; it is not automatically the macroscopic single-velocity energy loss.

Applied merely to the demo's sampled, derived VPM velocities, the same expression is initially a weighted field-regression residual. Calling it lost physical kinetic energy additionally requires a justified mass measure, mechanical state semantics and an actual merge operator. None is supplied by the cited display covariance, temporary P3 groups, authored-area thermal checks or prescribed-flow thermal protocol.

The proposed screen therefore remains within operation A, but is not yet directly instantiated by the inspected simulator paths. A subsequent decision must first state the mechanical carrier and transfer it intends to study, with the ordinary separate fine render state and ordinary affine/regression remedies treated fairly. This audit neither identifies a measured existing defect nor rules out a useful mechanical extension; it supplies no performance, visual-quality or contribution evidence.
