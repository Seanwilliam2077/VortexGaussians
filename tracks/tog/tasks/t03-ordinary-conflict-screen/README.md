# T03: ordinary conflict screen

This task uses the fixed [T02 authored target](../t02-authored-upper-bend/README.md) with the unchanged portable smoke model. It compares two ordinary full-control PHR/L-BFGS solves: edit-only and joint editing/protection. Each independently starts from zero and has 120 full rollouts. Target reachability is unknown. This is a development screen, not a new method or a speedup claim.

The numerical contract is in [PROTOCOL.md](PROTOCOL.md); exact settings are in [config.json](config.json). `freeze.json` authenticates source/input files relative to this task. No historical absolute paths, witness controls or hidden target states are runtime inputs. The prepared R22 driver is the documented fork source; the underlying objective and solver settings are R21's ordinary baseline.

```powershell
# Plan only: no Torch import or GPU computation.
python -I -B runner.py
# Explicit fresh run; supervisor enforces 600 seconds including qualification.
python -I -B runner.py --execute --out runs/reproduction-01
```

Use the existing Python 3.12 / Torch 2.11 CUDA environment. The fixed run authenticates the declared GPU UUID in `config.json`; another device requires a separately declared reproduction freeze, not overwriting this experiment. Both mask objectives must first pass the new-target derivative qualification. Failure stops without retry or altered finite-difference steps.

The complete local run directory contains stdout/stderr, supervisor outcome, worker summary, derivative probes, every accepted x/q/image/AL state and each arm's final velocity/density. `runs/` is Git-ignored. Compact results and final arrays may be published here after the run; absence of complete local trajectories from a clone is explicit. They are not deleted when creating a compact publication.

## Recorded outcome

The one frozen run completed with exit 0. Both objective-gradient qualifications passed (largest relative discrepancy 5.506e−7, fixed gate 1e−4). Sources and inputs were unchanged. The 600-second supervisor observed 158.746 seconds; the worker reported 157.773 seconds including imports, qualification and output. Peak Torch allocated memory was 2,181,761,024 bytes, cumulative over qualification and both arms, not total process/device memory.

| Arm | Full rollouts / returned steps | Worst edit relative RMS | Worst protection relative RMS | Passing edit / protection frames | Outcome |
|---|---:|---:|---:|---:|---|
| edit-only | 59 / 19 | 4.9603% | 5.4101% | 25/25, 17/50 | Its own edit/control gates passed; protection failed |
| joint | 119 / 34 | 6.1154% | 2.0250% | 23/25, 49/50 | Budget interrupted line search; restored last accepted state |

Joint failed edit frames 39–40 and the upper protected ROI at frame 40. It used the predeclared reserve-one-validation policy: at 119 calls the next trial was forbidden and rolled back, rather than spending the last slot on an unvalidated trial. No additional step or retry followed. Each arm's coefficient, actual force and finite/nonnegative-state checks passed.

Protection was active in this ordinary solve: the joint arm had 41/84 closures with at least one positive effective protected PHR branch, and one multiplier/rho update. The compact summary's `withEffectiveProtectionPenalty` counts only **positive summed PHR values** (35/84), not all active branches; a PHR value can be negative while its derivative is active. Edit-only had zero effective protection branches by definition. Its 35/39 closures with protection violations are reported, not penalized.

This exposes protection violations along one successful editing solution. It does **not** demonstrate a jointly feasible solution or prove target infeasibility. The joint solver reduced protection error but did not pass the original gates. Different stop criteria and one sample do not support a solver-speedup comparison (recorded arm walls: 42.023 and 86.658 seconds). No response-cache method or artist validation was tested.

Clone-contained records are [result-summary.json](result-summary.json), [publication-manifest.json](publication-manifest.json), and the byte-exact final bundles [edit_only-final.npz](edit_only-final.npz) / [joint-final.npz](joint-final.npz), including q, full frames, final velocity/density and accepted q history. The published bundle is about 6.9 MB. The preserved complete local run is 67,201,191 bytes; it is Git-ignored and not part of a clone. [raw-run-manifest.json](raw-run-manifest.json) supplies its hashes, not the missing arrays themselves. Independent saved-array review is recorded separately under `tracks/validation/`; no GPU re-execution is implied by that audit.
