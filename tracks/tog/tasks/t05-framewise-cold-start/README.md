# T05 — ordinary zero-control baseline

One fixed cold-start solve found a joint solution for the same authored T02 development target. The unchanged 76-constraint PHR/L-BFGS formulation started at x=0, lambda=0, rho=1 with fresh optimizer history. No former optimizer controls or states were loaded. This avoids treating the earlier T03/T04 discovery path as a necessary ordinary-baseline cost.

| Recorded outcome | Value |
|---|---:|
| Edit frames passing both original gates | 25/25 |
| Protection ROI/frames passing both original gates | 50/50 |
| Maximum edit relative / absolute RMS | 4.95528% / 0.00889926 |
| Maximum protection relative / absolute RMS | 1.82871% / 0.00412773 |
| Solve forward calls | 84 = 57 closures + 27 validations |
| Returned L-BFGS steps | 26 |
| Solve wall, including validation/evidence IO | 60.4013 s |
| Complete worker / supervisor wall | 76.3454 / 77.2603 s |
| Reused G0 authentication within startup | 0.04925 s |
| New G0 forward/backward calls | 0 / 0 |
| Peak Torch allocated / reserved bytes | 2,181,708,800 / 2,189,426,688 |

All finite/state/control gates passed. The first jointly passing accepted point was step26. There was one outer multiplier update; rho remained1. Protection violations occurred in37 of57 closure trials, so this solve did encounter protection constraints. These trial facts do not certify optimality. Source/input hashes remained unchanged; no retry or parameter adjustment occurred.

The inherited G0 cost was9 forward calls,1 backward and5.71314 s in T04, reported separately as an existing development prerequisite. It is not new online work. The89,109-byte [G0 proof](g0-proof.npz) contains25 non-frame qualification arrays authenticated before Torch import. Scalar PHR/FD arithmetic is recomputed from those records; full image loss and AD are not recomputed. Nine original image arrays are deliberately omitted, with their hashes retained in [proof metadata](g0-proof.json).

## Evidence and scope

- [Protocol](PROTOCOL.md), [configuration](config.json), [source/input freeze](freeze.json), [runner](runner.py).
- [Compact result](result-summary.json) and [final arrays](framewise_joint-final.npz): x, q,25 full frames,76 constraints, accepted q history, final multipliers, velocity and density. The final NPZ is a byte-exact copy of the completed worker output.
- [Publication hashes](publication-manifest.json) and [complete raw-file manifest](raw-run-manifest.json).
- [Independent review/audit location](../../../validation/t05-review.md), maintained separately by the reviewer.

Complete accepted arrays and stdout/stderr remain locally in Git-ignored `runs/run-01` (29,314,927 bytes); they are not supplied by a clone. No raw history was deleted for publication. The compact manifest covers3,580,428 bytes, including the final arrays and G0 proof.

This is one development target and one execution. It establishes feasibility and observed ordinary-baseline cost for this input. It is not a holdout, repeated timing result, statistical speedup, new algorithm, physical validation or artistic-usefulness result. T03 remains a failed fixed solve; T04 remains a successful paid-warm follow-up. Their outcomes are not rewritten.

From this task directory, `python -I -B runner.py` prints the plan without Torch/GPU execution. Reproduction of the already completed run requires the declared compatible Torch/CUDA runtime and a fresh output path; it must not overwrite `runs/run-01`. The recorded command used the existing Python3.12/Torch2.11 CUDA environment with child-only DLL/MKL settings, four CPU threads and the pinned RTX5070 Laptop UUID.
