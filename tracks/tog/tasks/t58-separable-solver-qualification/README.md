# T58 — ordinary same-operator solver qualification

**Completed, 30 October 2026:** `qualified_same_operator_fixtures_only`. All six frozen check categories pass in one 0.768266600-second supervised child: 18 saved T56 states and one manufactured largest-grid system. No new fluid trajectory, Green matrix, CG solve or candidate method was executed.

The ordinary FFT sine transform plus radial Thomas solver solves the identical half-cell Dirichlet FV system. Across saved states, maximum original weighted residual is 1.0767235e-14; phi, velocity and Jacobian differences from saved CG are respectively 3.2576940e-10, 2.2089482e-10 and 9.7383896e-10. These are linear-system evidence, not finite-time reference qualification or a novel method.

- [Formulation](FORMULATION.md) and [pre-run protocol](PROTOCOL.md) fix operator, transforms, exceptional mode, metrics and resources.
- [Results and complete costs](RESULTS.md), [machine-readable result](result.json), [execution receipt](execution.json) and [43-input freeze](input-manifest.json).
- [Source and saved-array review](../../../validation/t58-separable-solver-review.md), with pre-run participation disclosed and no solver rerun.
- [Next finite decision](DECISION.md): prepare six new short trajectories with this same ordinary solver, keeping all physical gates and adding solver-port regression.
- [Publication identity chain](audit-manifest.json). Large/raw arrays remain ignored locally with recorded hashes.

T56 remains failed; T57 remains timed out. No equal-work speedup, full t=1 success or TOG contribution follows. The full research goal remains active and unachieved; art inactive, main unchanged, automation deleted.
