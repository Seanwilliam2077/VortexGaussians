# T07 — ordinary solve for the second authored edit

The single fixed run found a joint solution for T06's delayed-bend target. It loaded only the previous qualified T05 x, reset lambda/rho/L-BFGS history, and recomputed every forward from original v0/rho0. The new target received a fresh scalar derivative qualification. No alternative start, target adjustment, extra budget or retry was used.

| Recorded outcome | Value |
|---|---:|
| New G0 | 9 forwards,1 backward; passed |
| Maximum new G0 relative FD discrepancy | 1.43495e−6 (gate1e−4) |
| Edit frames passing both original gates | 25/25 |
| Protection ROI/frames passing both original gates | 50/50 |
| Maximum edit relative / absolute RMS | 4.99484% /0.00929977 |
| Maximum protection relative / absolute RMS | 1.93677% /0.00418665 |
| Solve forwards | 101 =68 closures +33 validations |
| Returned L-BFGS steps | 32 |
| New G0 wall including evidence IO | 4.39107 s |
| Closure / acceptance synchronized wall | 55.0382 /13.6883 s |
| Solve wall including validation/evidence IO | 71.1901 s |
| Complete worker / supervisor wall | 91.5085 /92.4505 s |
| Peak Torch allocated / reserved bytes | 2,181,807,104 /2,189,426,688 |

The first jointly passing accepted point was step32. One outer multiplier update occurred; rho stayed1. Thirty-nine of68 closure trials had positive protection violations. The initial paid warm validation met all50 protection gates but only11/25 edit gates, so the timing revision was not already solved by the previous control. All finite/state/control gates passed at the final accepted state; source/input hashes remained unchanged.

The source solution cost is separate: T05 required84 solve calls,60.4013 s solve and76.3454 s whole worker. It is not added to the new edit's online latency. Historical T03/T04 optimization is not charged to this edit. Acceptance timing includes force checks; IO is included in wall timings and was not separately isolated. This implementation still performs a validation forward after returned optimizer steps. Ordinary reuse of an identical returned closure output could reduce redundant work; it was not implemented or measured. These timings therefore do not establish the strongest possible ordinary baseline or a cache advantage.

## Recomputable evidence

- [Protocol](PROTOCOL.md), [configuration](config.json), [frozen source/input hashes](freeze.json), [runner](runner.py).
- [Compact summary](result-summary.json), [final arrays](framewise_joint-final.npz), [publication hashes](publication-manifest.json).
- [Complete raw-file manifest](raw-run-manifest.json) and [independent review location](../../../validation/t07-review.md), maintained by the reviewer.

The final NPZ is a byte-exact worker copy containing x,q,25 full frames,76 constraints, accepted q history, final multipliers, velocity and density. Its SHA256 is `79e784b5c81cd75ff9af2d040b71164ebe56dd7fe3cb79e0b02b547b933a0830`.

The complete45 raw NPZ records, stdout/stderr and detailed summaries remain locally in ignored `runs/run-01` (43,401,095 bytes). They include all fresh G0 probes and33 accepted states; no history was deleted to make the compact publication. A clone supplies the compact final/summary package, not that local raw history. The publication manifest lists3,793,730 bytes.

This is one researcher-authored development revision with one measured execution. It shows that the ordinary solver found a qualifying answer under this fixed model and budget. It is not a held-out test, statistical performance result, external creative-demand validation, proof of physical realism, or evidence that a new method is necessary. There was no cold-start T06 comparison, so the result does not measure the advantage of warming from T05.

`python -I -B runner.py` only prints a plan. The recorded execution used the declared Python3.12/Torch2.11 CUDA runtime, four CPU threads, pinned RTX5070 Laptop UUID and child-only DLL/MKL settings. Existing outputs must never be overwritten. No further execution is part of this completed task.
