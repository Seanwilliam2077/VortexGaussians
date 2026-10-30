# T57 — one finer short-reference qualification

This new task implements the fixed proposal in [T56 DECISION](../t56-coupled-reference/DECISION.md). T56 remains failed. Its S64/S128 raw arrays, case summaries and stage logs are reused as old evidence, never rerun. No candidate method is evaluated. The question is whether the unchanged ordinary reference qualifies over [0,.25] at a finer resolution range, at a measured complete cost.

## Frozen computation and interpretation

The wrapper imports unchanged [T56 reference.py](../t56-coupled-reference/reference.py), which imports unchanged [T55 reference.py](../t55-axisymmetric-reference/reference.py). Only the T56 module's output `ROOT` is redirected to this new task. The old main is never invoked. No numerical function, numerical global, initialization, limiter, source rule, elliptic solver, metric or time interval changes. [T56 FORMULATION](../t56-coupled-reference/FORMULATION.md) and [PROTOCOL](../t56-coupled-reference/PROTOCOL.md) specify the equations and limitations. In particular the field is the conservative annular piecewise-linear q reconstruction, with omega_theta=r*q; the Poisson source rule remains its ordinary cell-average approximation. Kernel storage does not imply exact source integration or a novel cached method.

| Case | Origin | R=Z | nr/nz | dt | angular order |
|---|---|---:|---:|---:|---:|
| S64 | saved T56 | 8 | 64/128 | .0025 | 32 |
| S128 | saved T56 | 8 | 128/256 | .0025 | 32 |
| S256 | new, first | 8 | 256/512 | .0025 | 32 |
| T128 | new, second | 8 | 128/256 | .00125 | 32 |
| D192 | new, third | 12 | 192/384 | .0025 | 32 |
| Q128 | new, fourth | 8 | 128/256 | .0025 | 64 |

All snapshots remain 0,.125,.25. Four new cases mean 500 steps, 1000 transport stages and 1012 elliptic solves if complete. Freeze source bytes, parent commit, recorded old runtime, current executable, old initial/saved arrays and associated case/log/manifest/receipt/result identities before launch. Only saved fields are used for the two old cases; geometry vectors are reconstructed by the unchanged function and checked exactly against saved r/rc/z. Saved moments are taken from the frozen old case records. New and reused evidence/cost must be labeled separately.

## Required predicates, all retained

- Initial core u/J errors: each <=.01 for saved S64; each <=.005 for saved S128 and all new cases.
- Space: S64/S128 and S128/S256 reconstructed full vorticity relative L2 <=.01 at all three times. Velocity <=.02. At each nonzero time coarse/fine vorticity error ratio >=1.5; waiver only if both <=1e-8.
- Controls: S128/T128, S128/D192 and S128/Q128 full vorticity <=.01, velocity <=.01, at all three times.
- All pairs retain absolute axial centroid discrepancy <=.01 initial width (width=1) and covariance Frobenius discrepancy <=.01 of the initial analytic norm. No spatial alignment, fitting, time shift, restricted means or changed denominator.
- Every Euler/reconstruction stage is finite/nonnegative without clipping; outgoing CFL <=.5; volume divergence <=1e-10; weighted true CG residual <=1e-10, max 2000 iterations per solve; same direction-restart behavior inside that budget. Every transport face retains the original upper bound.
- Every case: circulation/outflow ledger relative error <=1e-10, saved q-squared relative drift <=.02 and axial-impulse relative drift <=.01. Outer-shell diagnostics remain diagnostics, not bounds on exterior mass.

Metrics use the unchanged 3x2 Gauss integration on the common finer grid within fixed r in [0,4], z in [-4,4]. The S64/S128 discrepancy remains old evidence, even though read back during this invocation. All categories must pass; stage/numerical errors terminate the child immediately, while metric failures are assessed after all four frozen trajectories. Preserve partial logs and do not rerun.

## Resource contract and costs

One scientific child, at most 1200 s including imports, loading old arrays, all geometry construction, stages, comparisons and outputs. Zero pilots/warmups, retries, fallback solvers, installation, new sources, shorter windows, adaptive dt or substitute cases. The supervisor checks all input identities, reserves its one invocation with an exclusive file and writes stdout/stderr and a memory log as it runs. Qualification additionally requires the complete child receipt within the time cap; supervisor validation/hashing costs are recorded separately.

Before freeze a standard-library-only OS probe records available physical memory and validates the byte-valued Windows GetProcessMemoryInfo structure against the probe process; it performs no numerical imports or allocations. Require >=3 GiB available host physical memory both then and immediately before launch. Scientific child peak working set must stay <=2 GiB. The supervisor reads the OS lifetime PeakWorkingSetSize, WorkingSetSize, PrivateUsage and PeakPagefileUsage every .25 s with a held process handle, logs them, and stops on observed peak >2 GiB or elapsed >=1200 s. A live memory-observer error stops the child. A final query unavailable after confirmed process exit is disclosed; the final successful OS peak observation is then a lower bound for the unobserved exit tail. This is an observed stop rule with sampling/termination latency, not a hard allocator guarantee or an RSS-only estimate. Private/commit counters are reported, not additional stop gates.

S256's K is exactly 1026*131072*8 = 1,075,838,976 B. Its finite check temporarily creates ~134.48 MB of booleans; 8-row kernel temporaries, source arrays, retained old fields, stage arrays, snapshots, output stacks and Python/NumPy runtime add memory. Sequential cases release K when unchanged solve_case returns, since K is not returned or captured. Retaining field snapshots for comparisons is intentional. This allocation inventory suggests the 2 GiB observation cap is plausible, but only the measured run can establish whether this process meets it; no scientific pilot is allowed. Host availability is a momentary observation, not a reservation.

Record each new case's kernel build, all per-stage boundary/CG/reconstruction/transport times, complete child wall time, observed peak memory and saved-data size. Charge the full prior T56 child 116.53663460002281 s separately and report T56+T57 cumulative time; retain prior failed/control work. T55 and earlier preparation retain their separate receipts; no aggregate here claims to be the whole project cost. No speedup or new contribution follows from a baseline runtime alone.

Passing qualifies only this new finer ordinary reference on [0,.25], without rewriting T56, establishing t=1 accuracy, evaluating a Gaussian candidate, proving formal error or meeting TOG contribution requirements. Failure stops this invocation. No automatic S512 escalation, t=1 run, candidate run or literature batch is permitted. A separately documented next decision must use the actual outcome.
