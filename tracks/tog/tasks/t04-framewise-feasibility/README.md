# T04 — 同一任务的事后普通求解器修订

The one fixed run found a solution passing **all original T02 gates**: 25/25 edit frames and 50/50 protected ROI/frames. This is an ordinary constrained solver result on a researcher-authored development target. It is not a new task or method, an independent preregistered replication, artist validation, or a speedup result. T03's earlier budget failure remains unchanged.

T03 optimized mean edit error but accepted only when every frame passed. Its final mean normalized edit MSE was .568734, while frames39/40 still failed. T04 added those 25 per-frame requirements to the 50 protection and one RMS constraints. The original mean objective and regularizer stayed unchanged. It paid for the prior accepted x as a warm start; every new trajectory began at original v0/rho0, with fresh lambda=0, rho=1 and no old L-BFGS history. See [PROPOSAL.md](PROPOSAL.md), [PROTOCOL.md](PROTOCOL.md), [config.json](config.json) and [freeze.json](freeze.json).

## One-run outcome

| Recorded item | Result |
|---|---:|
| New76-constraint derivative qualification | Passed; largest relative discrepancy 9.547e−7, gate1e−4 |
| New optimization rollouts | 67: 46 closure calls +21 accepted-state validations |
| Returned L-BFGS steps / AL outer updates | 20 /0 |
| Worst edit relative / absolute RMS | 4.4738% / .00803456 |
| Worst protection relative / absolute RMS | 1.9673% / .00405436 |
| Coefficient max / RMS | .4098504 / .0369414 |
| Actual expanded force max-component | .3904334 |
| New solve wall, including acceptance and evidence IO | 62.5723s |
| New worker / supervisor wall | 85.5517s /86.5951s |

All final finite, nonnegative density, alpha range, control and force gates passed. Thirty-two of46 closures had an active protected PHR branch;24 had an active edit branch. The source/input hashes were unchanged. The peak Torch allocation was2,181,807,104 bytes, cumulative over this worker's qualification/solve; it is not complete process/device peak memory.

## Cost and interpretation

The warm-start dependency was **T03 joint:119 rollouts /86.6583s**, followed by **T04:9 qualification +67 solve rollouts /85.5517s whole worker**. This partial dependency total is195 rollouts /172.2100s; it excludes T03's shared qualification, setup and edit-only arm. The complete chronological T03+T04 record is **263 rollouts /243.3248s of worker wall**. These are sequential observed costs, not cold-start performance or an isolated comparison of formulations.

This establishes a joint answer found by this paid ordinary path. Added budget, warm start and explicit edit inequalities all changed; this single result does not identify which change caused success or prove the mean objective was T03's sole problem. No additional search, threshold change or rerun followed. No response cache or claimed new optimizer was tested.

## Retained evidence and reproduction

Clone-contained: [result-summary.json](result-summary.json), [framewise_joint-final.npz](framewise_joint-final.npz) (x/q/fullframes/final velocity/density/accepted q history), [publication-manifest.json](publication-manifest.json) and source/contract. The final NPZ is a byte-exact copy of the worker output, SHA256 `39ea370477f0e42b2f5d4afc5b15798f0853f940c98bcac93e2ee3b7126a1904`. The compact package is about3.16MB.

The full local `runs/run-01` is31,279,744 bytes and preserves all derivative probes, every accepted image/control/AL record, logs and complete worker summary. It is Git-ignored and **not supplied by a repository clone**. [raw-run-manifest.json](raw-run-manifest.json) supplies its file/array hashes, not the absent arrays. Independent saved-array review is maintained separately under `tracks/validation/`; it does not rerun the model or optimizer.

```powershell
python -I -B runner.py  # plan only, no Torch import
python -I -B runner.py --execute --out runs/reproduction-01
```

Execution requires the declared Python3.12/Torch2.11 CUDA runtime and fixed GPU UUID. Another device is a separately declared reproduction, not an overwrite. The standalone supervisor enforces600 seconds including the new gradient qualification and solve. Existing paths are rejected. All relative dependencies are in this repository, including the paid T03 final x; no historical absolute paths or witness controls are needed. The original T01 single-rollout entry point was not changed.
