# T47 local model applicability audit

This report records a completed static inspection of four existing files. It asks whether any inspected path implements a persistent anisotropic Gaussian kernel whose covariance and vector strength undergo the proposed common-affine transfer. It does not execute a method, establish an empirical error, or assess external novelty. No additional source reading or acquisition was performed to write this report.

## Source identities and scope

| Repository-relative file | Bytes | SHA256 |
|---|---:|---|
| `research/physical_reference/core.py` | 12528 | `5b1fbe376d03ff1e3a55baf7fe8be760a5e60f89d6ef4b34c2c46619d982e926` |
| `research/physical_reference/PROTOCOL.md` | 16128 | `047614a73c73ba0abfcdc8b1032cabd026ac9731e868ba06b2455f0b621ba455` |
| `demo/index.html` | 314044 | `e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0` |
| `research/EVIDENCE_STATUS.md` | 9044 | `0eef78dee6c04239e36e0209e51d777281541569455aef66a0f0b1c311677b4a` |

These are whole-file byte identities captured during the audit; the content review used targeted matches and bounded windows. The physical-reference filenames were located with `rg --files research/physical_reference`; filename discovery did not inspect the other files' contents. Searches within the four selected files included `sigma`, `isotropic`, `anisotrop`, `stretch`, `solenoidal`, `diverg`, `helmholtz`, `covarian`, `DDFK`, `VPFM`, `P5c`, `Gaussian`, `kernel`, `transport`, and demo identifiers such as `evolveF`, `sxx`, `VREF3`, `sg`, `SG`, `stepSimVPM3`, `vpmSigma0` and `s2`. The line spans below identify the supporting evidence, not an exhaustive whole-repository inspection. No fifth file's content, linked paper, or linked implementation was opened.

## P5c already distinguishes raw source vorticity from its reconstruction

`research/physical_reference/core.py:1–6` explicitly describes a small direct-sum reference rather than a complete flow solver. It defines `Gamma = volume * vorticity`, states that the vector Gaussian representation need not itself be divergence-free, and distinguishes the Biot–Savart velocity reconstruction from an exact Navier–Stokes solution. This limitation is already acknowledged; T47 must not present it as a newly discovered defect.

`research/physical_reference/PROTOCOL.md:3,7–10` limits the experiment to isolated operators and specified ODEs. Each source has an independently supplied, positive scalar `sigma`, interpreted as the standard deviation on each coordinate axis. The protocol explicitly excludes a target width, visual gain, reference-grid volume, lookup tables and tree aggregation. It also prohibits inferring source volume from opacity, density or kernel width. The raw source kernel at `16–20` is

`W_j(r) = (2*pi*sigma_j^2)^(-3/2) * exp(-|r|^2/(2*sigma_j^2))`.

The velocity and its full Jacobian are specified at `23–30`. The single-source qualification explicitly warns again that vector Gaussian vorticity is generally not divergence-free and that the test validates an operator, not a complete physical vortex ring (`80–84`).

In the implementation, `core.py:47–86` stores `x`, vector `Gamma`, scalar `V/T/cV/sigma`, and IDs. It contains no kernel covariance matrix in this source-record schema. `97–133` evaluates radial Gaussian factors from Euclidean radius and scalar width. `141–156` passes only `p["sigma"]` to those factors, then sums the source cross-product velocity and its Jacobian. Thus the source-only isotropic semantics are visible in both the declared contract and these implementation paths.

The scoped distinction is between raw source vorticity, a velocity reconstructed from it, and transport of an entire reconstructed solenoidal field. These are not interchangeable qualifications. In particular, the documented distinction does not establish the proposed common-affine transfer or any commutation property for it.

## Stretching updates leave the P5c kernel width unchanged

`core.py:219–228` implements the strength RHS as `J_u * Gamma + V * curl(force)`. `232–241` copies source records and changes only position and vector strength. The copied `sigma` is unchanged by this step. The prescribed-strain path at `245–253` adds an external linear velocity/Jacobian and invokes that same update.

The matching protocol at `120–124` qualifies the prescribed ODEs for `x` and `Gamma` using a fixed scalar width. It does not evolve a full kernel covariance by `F Sigma F^T`, transport the complete spatial reconstructed field, or assert that these operations commute with Helmholtz projection. Its broader limitation at `170` excludes long-time vortex-dynamics convergence and other complete-solver claims. Consequently, a passed strength-stretching ODE cannot be reused as evidence that a persistent anisotropic-kernel transfer is already implemented or correct.

## The browser kernel has different width semantics

The layered browser comments at `demo/index.html:1781–1795` describe isotropic Lamb–Oseen sources, a tree approximation and lookup tables. The actual leaf interactions at `1910–1918` and direct path at `1930–1943` use the sum `tS2 + SG[j]^2`, where `tS2` comes from the target particle (`2093–2095`). The equal-width fast path is set at `2077–2078`. Therefore the browser leaf interaction is not the P5c source-only operator when source and target widths differ.

The 3D leaf path is equally explicit: `2311–2326` uses `s2 = 0.5 * (tS2 + sj*sj)` and evaluates its radial factors using that scalar effective width. `2367–2369` supplies the target's squared width. The tree-accepted paths use a scalar aggregate width (`1898–1908` for layered VPM; `2296–2309` for 3D), with lookup-table or far-field branches. These are current implementation semantics, not an independently validated replacement for the P5c operator.

In layered VPM, `2049–2078` initializes scalar `sg`, optionally increases its squared value by a viscosity term and caps it, then packs that scalar into `SG`. This is scalar core spreading, not anisotropic affine covariance transfer. In 3D, `2351–2362` initializes a missing scalar width and packs it alongside position, vector strength and temperature; the inspected 3D integration step does not evolve a covariance matrix or apply a deformation to `sg`.

The 3D field calculation returns the local directional-derivative contribution at `2306–2309,2323–2326`. The stepping code stores it (`2374–2375`) and applies it to strength (`2388–2390`), followed by damping and a strength cap (`2391–2393`). Velocity then includes direct buoyancy, optional turbulence and wind, and a speed cap before advection (`2394–2401`). The layered path likewise updates strength, derived velocity and position with its existing forcing and guards (`2093–2117`). These steps are not an implementation of exact full-field common-affine transport. The P5c source-only operator's properties cannot be assigned without qualification to the complete browser path, including target-dependent widths, approximations and additional velocity modifications.

## Display covariance remains separate from the dynamics kernel

`demo/index.html:1589–1604` directly evolves the three 2D entries `sxx/sxy/syy`, then applies relaxation toward identity, determinant normalization and anisotropy limits. The comment explicitly distinguishes this covariance evolution from storing a deformation gradient; the function name `evolveF` does not override the implementation.

Layered particles are initialized with both these display-shape entries and the separate scalar `sg` (`1613–1617`). Kernel packing at `2073–2074` uses position, circulation, dynamics temperature and `sg`, not the display covariance. The display code explicitly labels cooling expansion as rendering-only (`2715–2716`) and reads `sxx/sxy/syy` to obtain drawn ellipse axes (`2722–2728`). The 3D display path uses camera-facing billboards or shapes stretched along trajectories (`2686–2698`), which likewise do not establish an anisotropic dynamical source kernel.

The comment that solver degrees of freedom equal rendering primitives (`1785`) describes shared particle indexing at that level. It does not establish equality of the displayed covariance and the kernel covariance. Similarly, the presence of analytic stretching and a routine named `evolveF` cannot support a claim that the proposed persistent anisotropic transfer already exists.

## Prior-work warnings and decision boundary

`research/EVIDENCE_STATUS.md:20–22` distinguishes the actual browser VPM path and static/reference ODE evidence from validated complete flow. Its contribution section already records DDFKs' divergence-free kernels and vorticity updates, Vortex Particle Flow Maps' flow-map derivative transport, and the warning that Gaussian deformation and Cauchy stretching alone do not identify a new solver (`94–103`). It also records divergence-free transport of Gaussian appearance and identifiability limitations (`108–111`). These are preexisting repository source records, not newly acquired or independently reread external papers. The same page rejects general novelty or system-advantage inference from the current candidates (`113–120`).

Within the inspected paths, there is no implemented persistent anisotropic dynamical kernel undergoing the proposed common-affine covariance/strength transfer. P5c has independent isotropic source widths retained through its strength update; the browser has scalar effective widths and a separate visual shape. This is a scoped implementation finding, not proof that no other repository file or external method provides such a transfer.

If a T47 commutator derivation succeeds, its immediate relevance is a model-consistency limit for the explicitly proposed transfer rule. It cannot be reported as a newly observed bug in an existing anisotropic-transfer implementation, as a new discovery of raw-source non-solenoidality, or as evidence of novelty, useful error magnitude, performance benefit or paper readiness. No numerical method, simulator, benchmark or external source was executed or acquired in this audit.
