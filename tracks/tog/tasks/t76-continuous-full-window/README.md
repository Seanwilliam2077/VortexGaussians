# T76 — ordinary continuous projection passes the original full-window task

**Publication addendum, 2 November 2026:** research is paused. The [handoff archive](../../../evidence/handoff-2026-11-02/README.md) now publishes all ten original T76 reference NPZ inputs, twelve companion metadata JSONs and the complete journal as 23 lossless gzip files with original byte identities. Older references below to local-only arrays and an ignored journal describe their location at execution time. Their original paths remain ignored; the archived copies are tracked separately. No experiment was repeated. The original one-shot guard, runtime limits, numerical verdict and reproduction caveats remain unchanged.

Completed 2 November 2026, Asia/Shanghai. Exactly one scientific invocation completes the original two causal paths, all nine numerical qualification categories, both references and the original physical/time/reference-sensitivity gates. **This establishes a stronger ordinary baseline on one development case, not a new method or TOG contribution.** Art remains paused.

## What changed and what was measured

T75 identified geometry directions omitted by the old search. T76 retains the same two-Gaussian representation, exact initial state, Euler targets, original causal search, geometry bounds, physical model and scorer. At each step a bounded conventional nonlinear least-squares polish improves that freshly generated seed. Both paths start independently from q0 and finish at t=1, with h=1/16 and h=1/32. No saved trajectory is spliced in. Predictions are sealed before reference-array access. The [pre-run protocol](PROTOCOL.md) fixes every numerical choice and budget.

The following endpoint scores use the original primary reference S256. Covariance is the original Frobenius error divided by D0=1.0882203729522952; centroid error has the original coordinate units. Each physical threshold remains 0.10.

| Run and h | Relative vorticity L2 | Axial centroid error | Normalized covariance error |
| --- | ---: | ---: | ---: |
| T71, 1/16 | 0.08026183 | 0.01436328 | 0.05693569 |
| T76, 1/16 | 0.04865304 | 0.00438745 | 0.08096747 |
| T71, 1/32 | 0.09475414 | 0.00207040 | 0.10944815 |
| T76, 1/32 | 0.04753653 | 0.00367755 | 0.07636064 |

Both T76 paths pass at all five original checkpoints against **both** S256 and S128. Across those 20 score records, maximum field, centroid and normalized covariance errors are 0.04881907, 0.00917882 and 0.08129685. This is not pointwise dominance over T71: the coarse-path covariance and fine-path endpoint centroid errors increase while remaining within the original gates.

At all 17 common times, the two T76 paths pass the original 0.01 sensitivity gates. Their maximum differences are field **0.00465464**, centroid **0.00070990**, and normalized covariance **0.00493634**. T71's endpoint field/covariance differences were 0.03238761/0.07744833. Reference-score differences are at most 0.00086941/0.00006067/0.00032938 respectively. Two-step consistency is not a time-convergence theorem, and two reference resolutions are not two scenes.

The result removes the direct motivation for a richer representation or special birth mechanism **on this particular task**. T71 remains the historical time-sensitive result. It has not been relabeled; T76 is a separately frozen stronger ordinary solver.

## Remaining limitations

Relative to their own initial moments, endpoint circulation increases 0.6498%/0.6565% and axial impulse increases 3.4259%/3.4344% for coarse/fine paths. These are reported observations, not newly introduced acceptance gates. This baseline is not conservative; smaller step size alone did not eliminate this drift in the measured pair. There is no demonstrated practical failure attributable to it yet.

All 48 polishing attempts improve their seeds and pass three independently evaluated gain routes. All stop at `no_accepted_line`, not the gradient tolerance. No stationarity, KKT or global optimality claim follows. Finite quadrature/domain controls are empirical binary64 checks, not rigorous error certificates. The case is axisymmetric, no-swirl, free-space Euler; it does not validate three-dimensional fire, combustion, interacting scenes or production use.

## Actual work and runtime

The full scientific child takes **31.5586529000 seconds**, including import/setup, prediction, search, failed trials, confirmation, sealing, reference scoring, hashes, journal/result I/O and exit. Observed peak working set is **73,129,984 bytes** over 127 observations. Supervisor time through receipt construction is 31.8247381001 seconds, with 0.2660852000 seconds nonoverlapping overhead; the final receipt write is not timed.

- 48 original searches: 73,914 proposals, 11,720 component bases, 199,497 weight/control attempts.
- 48 polishes: 292 linearizations/SVDs, 630 trials, 244 accepted steps, 386 objective rejections, 726 model evaluations. No invalid trials, truncated singular values, active-bound exclusions or seed fallbacks occurred.
- 224 field evaluations, 2,736,128 spatial visits, 1,107,296,256 field heat-integrand visits; 12,104 cross evaluations and 6,126,592 cross heat-integrand visits.
- 96 candidate confirmations, 98 moment evaluations; original checkpoint/reference/time-comparison controls retained. Full counters are in [result.json](result.json).

All frozen caps are respected. The cumulative **selected scientific-child subtotal** is 2049.958372399793 seconds; this excludes much research/engineering work and is not project cost. T76 has a larger predeclared allowance than T71 and a disclosed executable-identity change. Neither strict speed comparison nor interactive frame latency is claimed.

## Evidence and reproduction boundary

Protocol commit `ec9479f`; implementation `d7bdc5e`; explicit preparation/runtime disclosure `d579202`; sealed manifest `6a387e7`. The first metadata-only preparation failed on an executable SHA change before any scientific invocation. [PREPARATION_RECORD.md](PREPARATION_RECORD.md) and [RUNTIME.json](RUNTIME.json) preserve old/current identities and the unknown cause. Same version strings do not establish identical dependency binaries. The subsequent scientific invocation uses the explicitly frozen current executable, and all 52 frozen identities remain unchanged.

[execution.json](execution.json), [source_manifest.json](source_manifest.json), [input-manifest.json](input-manifest.json), [predictions.json](predictions.json) and [result.json](result.json) retain the complete scalar evidence. The ignored 178,721,100-byte journal has identity in the receipt; raw reference assets remain local. This is not yet a self-contained public reproduction package: the frozen original reference files and runtime are needed to rerun the scientific worker. Its one-shot invocation guard is intentionally spent; do not rerun or remove that marker in this evidence directory.

For a portable **saved-scalar readback only**, run `python tracks/tog/tasks/t76-continuous-full-window/summarize.py`; `--write` verifies or creates [SUMMARY.json](SUMMARY.json). This post-run standard-library reader validates result/prediction hashes and derives tables without importing scientific code, reading reference arrays or generating trajectories. It is not another scientific invocation.

[REVIEW.md](REVIEW.md) discloses the two reviewers' implementation/protocol participation. No fresh formal TOG score is assigned; historical 2/6 remains a historical snapshot. [DECISION.md](DECISION.md) records the next research boundary.
