# T57 source, runtime and preservation review

Verdict: **no unresolved blocker to publishing the retained `timeout_no_retry` outcome. T57 did not qualify a finer short reference.** Its single child exhausted the fixed time budget with zero completed new trajectories, no new NPZ, no completed case JSON and no result.json. Partial log checks do not provide a full-field comparison, saved checkpoint, initial-error/drift verdict, Gaussian-candidate result or TOG contribution. T56 remains `completed_failed_checks`.

## Provenance and scope

This reviewer participated before the run: I read the actual T57 protocol, wrapper, memory observer, supervisor and ignored freezer, considered saved-case reuse, unchanged T56/T55 numerics, metric predicates and resource accounting, and reported no unresolved pre-run blocker. I retain earlier T48–T56 collaboration/review context. This is therefore not a blind design review or an independent execution. During the live child I performed only a static review of the conditional next decision; I did not compete for numerical resources.

After the parent reported terminal completion I independently read back the final task sources/documents, manifest, execution/preflight/start/freeze receipts, stdout/stderr, all 222 partial step-log records and all 4790 memory records. A separate standard-library-only bookkeeping script hashed actual files and reduced these saved JSON/JSONL numbers; its results matched the parent's ignored evidence-summary.json exactly. It imported no scientific evaluator or NumPy, loaded no old or new arrays, ran no solver, quadrature, scientific compile/import, trajectory, symbolic evaluation, benchmark, extra OS probe or external source query. Old NPZs were read only as bytes for their prescribed identity checks. No new numerical fields exist to reproduce. Saved residual values were checked against gates, not independently recalculated from absent fields.

I requested two interpretation clarifications: direct-versus-old-CG differences do not by themselves identify which solve contributes the discrepancy, and the future Gaussian translation speed must retain amplitude a. The final DECISION now distinguishes original-operator residual, manufactured-solution error and old-CG disagreement, and writes velocity = beta_star*a, axial speed c=beta_star*a_z and center_mu(t)=center_mu(0)+c*t. I read back the corrected text before sealing. No frozen numerical input changed, and no task draft or shared status was edited by this reviewer. Only this report is written.

## Unchanged numerical contract and reuse

The T57 wrapper imports the frozen T56 module and changes only its output ROOT; it does not call the old main or replace a numerical function/global. The unchanged T56 module imports the frozen T55 spatial code. The actual source still uses the annular-volume-average q initialization, conservative nonnegative piecewise-linear reconstruction, current-q free-space boundary matrix, weighted FV/CG solve and SSPRK2 evolution reviewed in T56. The Poisson routine initializes x to zero on each invocation and requires a recomputed true weighted relative residual <=1e-10 within 2000 iterations. These are concrete implementation properties, not an assertion that all ordinary CG implementations are slow.

The two old S64/S128 cases are loaded from frozen JSON and NPZ, with their settings, saved times and raw/log identities checked. Reconstructed geometry vectors r/rc/z must equal saved vectors exactly; snapshots are copied with allow_pickle=False and saved moment records retain their old provenance. Reuse does not convert their earlier agreement into new T57 measurement. The wrapper explicitly requires Python 3.12.14 and NumPy 2.3.5 before loading cases; it does not fit against snapshots.

The four prescribed new cases are sequential S256, T128, D192, Q128. A complete invocation would perform 500 new steps, 1000 transport stages and 1012 elliptic solves. These are planned counts, not completed work. The six-case comparison set would combine two reused and four new cases; summing reused case counts would not represent new work. S256 alone began in this invocation. Its kernel and initial solve necessarily precede its saved stage prefix, but their unsaved end-of-case fields/timings are not recoverable.

The fixed comparison implementation retains the original physical-field definitions: reconstructed omega_theta=r*q, 2*pi*r^3 weighted q differences, 2*pi*r weighted velocity differences, common finer partition with 3x2 Gauss integration, full-box circulation-weighted moments, the original analytic shape normalization, no alignment or restricted-core refitting. The new spatial pair and three controls, nonzero-time reduction predicate and small-error waiver are indexed consistently. They were never reached because comparisons follow all four completed new cases. The absence of metric results is neither a pass nor a measured representation failure.

## Invocation and stopping behavior

The supervisor validates every frozen input and the scientific executable before launch, checks host availability, creates an exclusive start marker, and contains one Popen with no retry/fallback path. The marker intentionally records scientific_child_invocations=0 before launch; execution.json records 1 and the child PID after launch. All other marker fields match the final receipt. This difference is expected, not evidence of a second run.

The held process handle samples Windows OS lifetime PeakWorkingSetSize and companion byte-valued counters. Source inspection confirms the 80-byte x64 PROCESS_MEMORY_COUNTERS_EX layout, explicit ctypes signatures, live-observer failure handling, a 2 GiB observed peak stop and elapsed >=1200 s time stop. Either stop kills the supervisor's own live child and waits, then preserves logs. A complete output could not override a time/memory failure; input/executable changes would revoke qualification. No result or completed case was found, so the result-validation branch did not run.

The terminal status is timeout_no_retry, return code 1. Child supervised time is 1200.2575366999954 s; supervisor time before receipt write is 1200.3295421999646 s. The last observation is at 1200.0004046999384 s, consistent with the elapsed-time branch followed by termination latency. The full overrun is reported rather than hidden under the nominal 1200 s. This audit checks source and saved evidence; the parent's separate process-inventory confirmation is not represented as a second OS observation by this reviewer.

There are zero complete case records, zero new NPZs and no result.json. Only S256-steps.jsonl exists among the new step logs. The unchanged solve_case keeps snapshots/statistics in memory and writes its NPZ and case summary only after all steps finish. A snapshot solve log therefore is not a field checkpoint, including the recorded midpoint solve. No state can be resumed from these logs alone. T128, D192 and Q128 have no execution evidence and cannot be counted as started/completed trajectories.

## Independent reduction of the partial records

The JSONL sequence is exactly: snapshot 0; complete stage-0/stage-1/step records for steps 0 through 72, with snapshot 50 after completed step 50; then stage 0 of step 73. It contains 222 valid records, no malformed lines, 73 complete step records, 147 transport-stage records and 149 logged elliptic solves. The last complete step is 73, corresponding to t=.1825 for the unchanged dt=.0025. The extra stage does not constitute step 74. Snapshot solve steps are [0,50].

The 149 solve records total 180283 CG iterations, maximum 1226 and zero direction restarts. Maximum logged true weighted residual is 9.997855588309177e-11 and maximum logged volume divergence is 5.684341886080802e-15. All reported solve values are finite and within their frozen limits. Maximum logged outgoing CFL is .07997729211806799; minimum logged transport-face q is 2.598861814481879e-28. All 73 completed step records have nonnegative q/Euler-stage minima and circulation-ledger error <=1e-10, with maximum 2.3622128277234243e-16 and minimum Euler-stage q 3.0494762882192497e-28.

This validates only the checks represented by complete saved records. In particular the last stage-0 log precedes its ensuing Euler update check in the source, and a killed in-flight solve/update has no complete record. The absent fields prevent independent residual or reconstruction evaluation. Positivity/face upper-bound assertions in the inspected source are not substitutes for full trajectory accuracy or absent drift measurements.

Summing every recorded phase field independently gives: completed linear solves 1059.8456162002403 s; boundary matrix-vector products 10.845489900326356 s; reconstruction 2.8446474998490885 s; transport 3.9336301003349945 s. Completed Poisson work alone is 88.30151728221549% of the full failed child wall time, consistent with the published 88.302%. The remaining wall time includes setup, imports, old-field loading, unsaved phase work and overhead; this does not isolate a geometry-build timer or permit extrapolating a completed trajectory cost. Iterations/timers of any interrupted unlogged solve are excluded from these partial sums, while its elapsed cost remains charged in child time.

The prior complete failed T56 invocation is 116.53663460002281 s, independently confirmed against its frozen receipt. The arithmetic sum is 1316.7941713000182 s for T56+T57 supervised children. This retains all previous T56 failed/control work, rather than charging just the selected reused cases. T55 and the rest of the research history are not included in that two-task total and retain their separate receipts. No equal-work speedup or asymptotic claim follows from this failed invocation.

## Memory evidence and preservation

The OS-only preflight reported 26864070656 B available physical memory; immediately before launch the receipt reports 26696884224 B, both above the fixed 3221225472 B (3 GiB) requirement. These are observations, not reservations. All 4790 memory records are valid; elapsed times increase strictly, reported lifetime peak working set is nondecreasing, and each positive current working set is no larger than its reported peak.

Maximum observed lifetime peak working set is 2052538368 B, below the 2147483648 B (2 GiB) stop threshold. Maximum observed private usage is 1967009792 B and maximum peak pagefile usage is 2032242688 B. Private/commit values were reporting fields, not stop criteria. The successful last query precedes termination; final_memory_query_unavailable_after_exit is absent and interpreted as false. That false flag does not certify an observation after killing the child. Therefore the saved peak is not a formal bound over any unobserved exit/kill tail, and the monitor is not an allocator cap.

The source's S256 kernel shape implies 1026*131072*8 = 1075838976 matrix bytes; this is a source-level allocation count, not process peak memory. The process also carries temporary finite-check arrays, matrix construction temporaries, stage/snapshot arrays, retained old data and runtime allocations. Since no complete case summary exists, no missing geometry timing or numerical field is invented.

Every one of the 28 frozen input identities was independently regenerated from actual bytes and matched. The manifest, wrapper, supervisor, executable, freeze helper and all receipt-linked log identities also matched. The final scientific executable is unchanged. Versions were asserted at child entry and the preflight reports Python 3.12.14; no final result exists to serve as a completed child runtime report. The parent's evidence-summary.json exactly matches the independent reduction of the original saved records; it is corroborating bookkeeping, not a separate physical experiment.

## Next-decision check and limits

The selected T58 question is an ordinary same-discrete-operator linear-solver qualification, not a new carrier or an automatic T57 repair. Hand inspection of the displayed axial operator gives half-cell Dirichlet endpoint diagonals 3/h^2, interior 2/h^2, off-diagonal -1/h^2; the stated sin(pi*k*(j+1/2)/n) modes and positive eigenvalues match those rows, including k=n. The exceptional last-mode squared norm is n, versus n/2 for other modes. The odd-extension FFT phase and inverse normalization are consistent. Adding each positive eigenvalue to the original radial tridiagonal operator gives strict diagonal dominance, nonpositive off-diagonals and positive exact-real Thomas pivots; radial volume weights symmetrize it. These hand checks do not replace future finite-precision/residual tests or certify a yet-unwritten solver.

The preparation keeps the existing nonhomogeneous boundary RHS, old true weighted residual, all 18 T56 state fixtures and one explicitly signed manufactured largest-grid algebraic fixture. It does not reuse historically failed coarse states as qualified physical references. The transform, largest-mode, original-stencil residual, known-solution and old-CG comparison gates are distinct and all mandatory; old CG uncertainty remains a possible cause of disagreement. One separately frozen 180 s child with resource observation, no new Green matrices or fluid trajectories, and no retry/fallback is a coherent finite next scope. Passing would still require a later coupled-reference qualification with dense current-q boundary costs and all physical controls. No future numerical work was performed in this review.

The corrected future comparator argument uses free-space translation equivariance of the Euler field and the full-space L2 tangent projection. The projected translation velocity retains beta_star*a, so scalar axial speed is c=beta_star*a_z. It supports an ordinary constant-speed projected-family trajectory once a suitable physical reference exists; it does not assert exact Euler translation, finite-time error from initial residual times time, or permission to refit over a restricted core. No full t=1 candidate task, useful distinct mechanism or TOG contribution has yet been established by T57.

## Final reviewed T57 identities

The following 12 direct task-file identities were generated programmatically from the actual final bytes after the speed-notation clarification. A later audit-manifest.json or publication metadata is owned by the parent and is not claimed to have been reviewed here. This report does not include its own hash recursively.

| File | Bytes | SHA256 |
|---|---:|---|
| `.gitignore` | 7 | `a7d8bdcefba82a95ebc021d87c629fdea21f13af953bf01e28b7cf8b0eeceb41` |
| `PROTOCOL.md` | 6948 | `02cab7e2195ab268dd3d00c98ab741825a44f9d80176e64115faa600ef30404d` |
| `reference.py` | 5645 | `55baeed333df0ef4c825517225e8553e5a3af0991ef9fccd12eeeee95a492062` |
| `run_once.py` | 8515 | `23f26a6206c64fabdfa56ca1f32d89f7a29144c1d35ed7d6c2ae702a45c30101` |
| `memory.py` | 2231 | `4b83a89eff664dc0d86fb0c71b39c99d71720c1d18c5f93557e279d0ca3745fd` |
| `resource_preflight.py` | 1551 | `db7f49a3220f42ef00f905412ac5e1dbf0912d76ef90f1c1f847a08dd21da84f` |
| `resource-preflight.json` | 906 | `3232e5d00d1d4441dca33f2e4b941ca4e203d37694e7a3c8180a452b92f2f0e4` |
| `input-manifest.json` | 6538 | `6dc00fa6ed67bcd689e95b5c31457818e359d8142921e0b3da6a10c60430e91f` |
| `execution.json` | 2793 | `0fba254f5b3b485eca041fd93a3dd1cd0bb1ddb780b94e28faf0d190bd6f4672` |
| `RESULTS.md` | 5696 | `55fad26878e92bbea37cc1abf3de5b91b9b51e98d5909d2e23dd3a12b0f7895d` |
| `DECISION.md` | 9091 | `2ff004ffa50276bdbf425d80df06be29b1017abbc60180fe04050221c900f328` |
| `README.md` | 1242 | `a7c5c4a6ee841b440212b9e0873575d7a0d5f92b04bae60747571c70d6026baf` |

## All 28 frozen inputs, independently matched

Paths are repository-relative. These are the identities read back, not manually transcribed copies. Old NPZ access here was byte hashing only.

| File | Bytes | SHA256 |
|---|---:|---|
| `tracks/tog/tasks/t57-finer-short-reference/.gitignore` | 7 | `a7d8bdcefba82a95ebc021d87c629fdea21f13af953bf01e28b7cf8b0eeceb41` |
| `tracks/tog/tasks/t57-finer-short-reference/PROTOCOL.md` | 6948 | `02cab7e2195ab268dd3d00c98ab741825a44f9d80176e64115faa600ef30404d` |
| `tracks/tog/tasks/t57-finer-short-reference/reference.py` | 5645 | `55baeed333df0ef4c825517225e8553e5a3af0991ef9fccd12eeeee95a492062` |
| `tracks/tog/tasks/t57-finer-short-reference/run_once.py` | 8515 | `23f26a6206c64fabdfa56ca1f32d89f7a29144c1d35ed7d6c2ae702a45c30101` |
| `tracks/tog/tasks/t57-finer-short-reference/memory.py` | 2231 | `4b83a89eff664dc0d86fb0c71b39c99d71720c1d18c5f93557e279d0ca3745fd` |
| `tracks/tog/tasks/t57-finer-short-reference/resource_preflight.py` | 1551 | `db7f49a3220f42ef00f905412ac5e1dbf0912d76ef90f1c1f847a08dd21da84f` |
| `tracks/tog/tasks/t57-finer-short-reference/resource-preflight.json` | 906 | `3232e5d00d1d4441dca33f2e4b941ca4e203d37694e7a3c8180a452b92f2f0e4` |
| `tracks/tog/tasks/t56-coupled-reference/reference.py` | 17488 | `51499f5c50b8f7f25ebb8df2569bc7eff085938cbd9d88f36b8604f9aaa4e01f` |
| `tracks/tog/tasks/t56-coupled-reference/run_once.py` | 5666 | `8bc3082b5f1449998f2f27008cdb7b7616552afa9955898fd05aabece47c9ffc` |
| `tracks/tog/tasks/t56-coupled-reference/FORMULATION.md` | 5434 | `0500b1fad0d187f7815f5751f33ec78835d60ea9b047b21ed08e74c28d39f029` |
| `tracks/tog/tasks/t56-coupled-reference/PROTOCOL.md` | 7332 | `1b7defa36dbe33df2ff6d01ca52aa62117ea7aeaea8a1121d4deba66406ae537` |
| `tracks/tog/tasks/t56-coupled-reference/DECISION.md` | 5561 | `82aa1e72b36e2712b0a076ad000f3ad6221ea60f8380d8fbc5d9f424e2625c95` |
| `tracks/tog/tasks/t56-coupled-reference/input-manifest.json` | 2723 | `cd353bc8eec8eb4616be9f44922fcafcad67e953a85545db1f5c6286d9548967` |
| `tracks/tog/tasks/t56-coupled-reference/execution.json` | 4937 | `6a2b25ae1b11c47921f535589637a7412b9d9c94110b617e285bc7b38d02b746` |
| `tracks/tog/tasks/t56-coupled-reference/result.json` | 31700 | `95e616130f169cf325f79f3e27f79ac5879a029fef922291e92d4b11842ee099` |
| `tracks/tog/tasks/t56-coupled-reference/audit-manifest.json` | 9396 | `601bc9d1b431d7fa1ed8703d007dc118297c90ffdce00150fb83083d79643622` |
| `tracks/tog/tasks/t56-coupled-reference/local/S64.json` | 3700 | `c0a4563c85eba9652f33e53d3f1ea3b6a9fb7052300969ed4130af9b3c7199e3` |
| `tracks/tog/tasks/t56-coupled-reference/local/S64-steps.jsonl` | 140400 | `8eb50ac12fac021cbbb2e1fde2e3398d08c7450f344e0eb5b0d6e3b9c715ffd6` |
| `tracks/tog/tasks/t56-coupled-reference/local/S64.npz` | 2768740 | `1100e33caf1fd28d250ecda7b251aa4fbe0bba03501e1b5d9d3f5d7c5d396493` |
| `tracks/tog/tasks/t56-coupled-reference/local/S128.json` | 3703 | `a17c2e94ece6f699581943986d779eaba63c6e3bc509040387cce0736259e075` |
| `tracks/tog/tasks/t56-coupled-reference/local/S128-steps.jsonl` | 139459 | `3b922240d528a54dc5fda341b64be16a17b538e5dab3e3810c5cc5977be55c76` |
| `tracks/tog/tasks/t56-coupled-reference/local/S128.npz` | 11038564 | `346d78f7f0ebba17c15fd1b5285c3472c1b4ac9d43cebf20eca9fe7532112bb2` |
| `tracks/tog/tasks/t55-axisymmetric-reference/reference.py` | 10613 | `499bab137463df4435230e3cbf4d16b0723feed5ad5d06087a0bafd911204908` |
| `tracks/tog/tasks/t55-axisymmetric-reference/FORMULATION.md` | 4604 | `7d463593ec8f021ab814d0213bcf5f9b74b1c79ae9496b6d4cab2452f6440709` |
| `tracks/tog/tasks/t55-axisymmetric-reference/TASK.md` | 4132 | `b470e55c6449348136673764e7d7b975cd3bad479ddefa0d881d827eba84e89e` |
| `tracks/tog/tasks/t55-axisymmetric-reference/DECISION.md` | 6454 | `ed1d20b4b603ecb4afd49e06f4a33aba6b86ecbabd6bb1f87c4cbc445c1d420f` |
| `tracks/tog/tasks/t55-axisymmetric-reference/audit-manifest.json` | 9225 | `5bc23f9b3e2deb550365d4ac2a1a94db4f8ed59064bd15aab5b85a8f45ec7d76` |
| `tracks/validation/t56-coupled-review.md` | 17447 | `ec44008a21429649bca6c2d77ff2b242003124e602510cf02d8e531ec8a62a4a` |

## Read and checked local evidence identities

The local files are ignored evidence; recording their identity does not authorize committing private notes or large assets. The freeze helper was read only, and the evidence summary was independently reproduced from the original logs.

| File | Bytes | SHA256 |
|---|---:|---|
| `local/freeze.py` | 3220 | `9798595ce82687dae06c6963b28951c0908f5b2a26c2e27c08fed1bf455df34c` |
| `local/freeze-receipt.json` | 288 | `6e25c73932770fa5e4923973862a0f53c6813717095e67962b584668bb6f94ad` |
| `local/execution-started.json` | 1517 | `1e74f84842f09205e8e2150698d0d57547aa72b2c7501e19c54d44fc6958ced2` |
| `local/stdout.txt` | 110 | `c1e0dc93a05356413ada7c07e623efd375a5d15af8c84a98a0de33cd3e9abd33` |
| `local/stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `local/memory.jsonl` | 891361 | `1476d0996dce1706ea8cd47fbaeda65ef55b6758ab1a2204277fbe31d1a87dc1` |
| `local/S256-steps.jsonl` | 101523 | `f2be9f5e70eb9f6dc9ca8b4dbe17c4495f3bcd30b688138c64f7eb221279a266` |
| `local/evidence-summary.json` | 2611 | `af3c56240ca93293d100ebd9ed534eb4984ca98c7f505cd0c8a9f2be91e8f404` |

Scientific executable, independently matched to both manifest and receipt:

| File | Bytes | SHA256 |
|---|---:|---|
| `C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe` | 107312 | `5640e9be2fd33d05a1a9ae1228e2354609a69ab831605995ec4e2bd6da8fff5e` |

The report accepts the correctness of the documented failure boundary and preservation checks. It does not change that failure into scientific reference qualification, implementation novelty or publication readiness.
