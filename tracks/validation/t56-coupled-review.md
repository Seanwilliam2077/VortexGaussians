# T56 — coupled-reference mathematical and saved-data review

## Verdict and provenance

No unresolved implementation, evidence-integrity or final-claims blocker remains. **The scientific qualification fails.** All six trajectories completed, but S32/S64 reconstructed vorticity discrepancies exceed the fixed 1% requirement at every saved time, including t=0. The other nine predicate categories pass. The frozen all-required contract therefore remains failed; a finer-pair pass or successful execution cannot override it.

Reviewer: continuing second agent `t48_review`, with inherited T48–T55 collaboration history. I advised before code on physical metric/control choices, including the conservative reconstruction comparison that avoids discarding fine structure by coarse restriction. I then read the actual T56 FORMULATION, PROTOCOL, implementation, runner and freeze helper before launch. This was not blind protocol design or an independently implemented numerical replication. I requested a pre-freeze wording correction because the implementation reports a boundary-shell circulation fraction, not actual later omitted exterior tails; the corrected frozen protocol explicitly leaves later exterior mass unmeasured/unbounded. No numerical code change was requested by this reviewer.

After the single root execution I read the saved result, receipt, manifest, corrected protocol and final README/RESULTS/DECISION. Authorized saved-output postprocessing loaded the six existing NPZs and logs, reconstructed only their already saved polynomials and evaluated the frozen metric/moment integrals. I used explicit standard three-point/two-point Gauss nodes and weights for this data reduction; I did not import or execute reference.py, build a new Green matrix, evaluate a new initial oracle, run Poisson/transport or generate any trajectory. Numerical saved-array postprocessing did occur and is not being described as text-only review. No new sources were accessed. This review is the only file I wrote; task drafts, gates and shared state were not edited.

## Pre-run mathematical/code findings

The stored q is an annular-volume average under r dr dz. Its radial reconstruction center rc=(2/3)(r_+^3-r_-^3)/(r_+^2-r_-^2), rather than the arithmetic midpoint, makes the radial linear deviation have zero annular mean; the axial midpoint does the same in z. The separated exponential-difference and erf/erfc initialization integrates the given Gaussian over each annular cell. Reflection/erfc branches preserve positive tails, and the implementation does not initialize with midpoint q or clip stored cells.

Minmod slopes use adjacent radial centroids. The common slope multiplier based on the maximum radial and axial deviation bounds the entire reconstructed linear cell polynomial between zero and 2qbar in exact arithmetic while preserving its mean. The 64-epsilon margin is present. Face checks enforce finite/nonnegative values and the declared upper donor tolerance. The axis q ghost is even; exterior ghost averages implement the stated zero-inflow assumption. These are ordinary numerical reconstruction choices, not a new method.

The elliptic source is explicitly a piecewise-constant approximation of the transported cell averages, with exact radial r^3 cell mass times h and a midpoint source kernel. The field used for comparisons is the declared limited piecewise-linear reconstruction; this difference is disclosed. The dense geometric boundary matrix is multiplied by current q at every SSPRK2 stage and saved snapshot. Neither analytic initial q nor periodic boundary values are substituted later. The reused T55 elliptic solver/formulation retain their previously reviewed sign, axis, weighted symmetry, half-cell boundaries, diagonal CG and true-residual check. Their identity is included in the freeze.

Nodal psi is shared by both face directions. F_r=-difference_z(psi), F_z=difference_r(psi) make cell volume-flux divergence cancel algebraically, and the axis radial flux is exactly zero. The upwind q flux is shared by neighbors with opposite signs. The outer lower/upper/radial signs correctly select zero incoming q and reconstructed interior outflow. Annular cell volumes divide the conservative update; no elliptic r^3 weight is substituted into transport.

The sufficient forward-Euler positivity argument is consistent: each outgoing donor value is at most 2qbar and outgoing volume CFL is at most 1/2, so outgoing removal cannot exceed the stored average in exact arithmetic, with nonnegative inflow. Code checks q1, the second Euler update and the final SSPRK2 combination without clipping or dt reduction. The two boundary q fluxes enter the circulation ledger with dt/2. Current-source solves are performed twice per step, plus three saved endpoint solves, all counted.

The metric implementation retains both polynomials on their common finer partition. It does not restrict fine q to coarse means or align fields. Vorticity squared uses 2pi*r^3, velocity uses 2pi*r, and circulation/moments use r. Linear q differences squared times r^3 have maximum radial degree five and axial degree two, so the declared 3x2 rule integrates these represented polynomials exactly in real arithmetic; this is not an exact norm/certificate for the unknown fluid solution. Signed axis velocity ghosts and centered velocity reconstruction match the stated convention. The control/finer member supplies the norm denominator.

Full-box centroid/covariance and diagnostics use the same reconstructed q. The fixed analytic initial covariance diag((4-pi)/2,1) supplies a common normalization. The implementation distinguishes 2pi integral r*q^2, axial impulse pi integral r^3*q and physical vorticity squared integral 2pi integral r^3*q^2. The latter may change by stretching. The 2% q-squared and 1% impulse gates are numerical-drift screens on this truncated box, not a physical-enstrophy conservation assumption or tail certificate.

S32/S64/S128 share dt and output times; T64 changes only dt; D96 preserves h, dt, angular order and source-cell rule while extending the box; Q64 changes only angular quadrature. Radial/axial source quadrature remains coupled to spatial resolution. The initial analytic u/J checks are rerun because the discrete source differs from T55. The error-ratio waiver applies only when both spatial-pair values are below the frozen floor. No metric, case, norm, threshold or waiver was changed after output.

The runner/freeze contract is consistent with one 600-second child and six cases. It uses an exclusive started marker, no retry/fallback, pre/post frozen input/executable identity checks, and retains step logs/raw files and case records even for failure. Complete-output validation checks expected names, steps, 2*steps+3 solves, 2*steps stages, inherited source identity preservation, expected exit/status and raw/log identities. A valid failed-check result remains failed.

## Saved-output checks

All ten frozen inputs and executable match their actual bytes. Manifest, new/reference source, runner, result, started marker, stdout/stderr, six case JSONs, six NPZs and six step logs agree with their recorded identities. Every case JSON matches its result entry. All NPZ arrays are finite and have the declared shapes, spacing, nonnegative q and three saved times. I recomputed initial u/J errors from saved numerical and saved analytic arrays; I did not call the oracle.

The logs have the complete ordered snapshot/stage/step sequence for each case. Counts reproduce 700 steps, 1400 transport stages, 1418 solves and 515506 CG iterations. Logged CFL/divergence/residual extrema, iteration totals/restarts, Euler-stage/face positivity and circulation-ledger values reproduce the case summaries. The actual per-stage Poisson residual was not independently recomputed by another operator/solve; its saved true-residual calculation is supported by the inspected unchanged solver.

Saved reconstruction reductions reproduce all fifteen vorticity/velocity comparison norms and all eighteen full-box sets of circulation, centroid, covariance, q-squared, impulse and vorticity-squared diagnostics to floating-point reduction rounding. Using explicit Gauss weights rather than the evaluator's returned floating-point weights slightly changes some near-zero moments, without any changed predicate. All ten categories reproduce with only vorticity_disagreements false.

The spatial comparisons are:

| Pair | Time | Vorticity discrepancy | Velocity discrepancy | Axial centroid discrepancy | Covariance discrepancy |
|---|---:|---:|---:|---:|---:|
| S32/S64 | 0.0 | 0.01627836698386338 | 0.011875066938728385 | 1.5859583193943893e-19 | 0.001445486840891359 |
| S32/S64 | 0.125 | 0.016319024627933772 | 0.011869652937758577 | 0.00011052123958558979 | 0.0021234572391593946 |
| S32/S64 | 0.25 | 0.016624221509034684 | 0.01188508424006332 | 0.00021786663395730044 | 0.002859621197586255 |
| S64/S128 | 0.0 | 0.004177862997975246 | 0.002939615377446075 | 4.94170194520388e-18 | 0.00018632532873673056 |
| S64/S128 | 0.125 | 0.004216435278366882 | 0.0029369796534097835 | 2.9127226352794466e-05 | 0.000352638573118463 |
| S64/S128 | 0.25 | 0.004347559713233459 | 0.0029406268922233334 | 5.8246374647547006e-05 | 0.0005320250110924427 |

Thus the S32/S64 failure is already present before time advancement. This identifies an initial coarse-reconstruction resolution limitation within the frozen representation/norm. It does not prove all later discrepancy has the same cause, independently isolate source/advection/elliptic errors, or demonstrate failure of the Gaussian carrier. The S64/S128 agreement and nonzero-time reductions 3.870336801245646 and 3.8238052161612672 are retained as partial evidence, not substituted for the failed coarse requirement.

The independent controls all satisfy their frozen thresholds. Their largest stored vorticity disagreement is 2.2012475279658403e-7 and velocity disagreement 8.142783947363318e-6. The tiny angular differences do not establish equally tiny true integration error. No refinement disagreement is promoted to a rigorous continuum error bound. Positivity, small invariant drift and near-exact mass bookkeeping also do not prove field accuracy, as the failed field gate itself illustrates.

The finest saved centroid/cross-covariance observation in RESULTS matches the saved numerical moments. It is explicitly an unqualified-reference observation. There is no Gaussian comparator trajectory, fit or t=1 meaningful-motion result, and no accepted reference accuracy is inferred from those descriptive numbers.

## Accounting and final decision

The receipt returns 2 and completed_failed_checks after 116.53663460002281 supervised child seconds, within the 600-second cap. The child timer before result writing is 116.29796609992627 seconds and the supervisor timer before receipt writing is 116.61247589997947 seconds. The .06366179999895394-second final comparison work is inside the child. Case/phase timers have nested scopes and cannot be added as extra invocations. Source preparation, pre/post review and publication are separate work, not hidden inside a solve-only performance number.

Saved metadata sums to 1045692416 geometric kernel target/source/angular pairs, 26258520 NPZ bytes and 981157 per-step-log bytes. The largest kernel alone is 134742016 bytes; this is not total process peak memory. The actual 1418 solves and 515506 iterations, zero restarts, all failed/coarse/control work and full one-child cost remain charged. Stdout is 2264 bytes and stderr is empty. Earlier T52–T55 outcomes/costs remain historical evidence and are not overwritten.

The final README/RESULTS/DECISION preserve the failed T56 qualification and its scope. The proposed T57 is a new finer-resolution question, reusing exact S64/S128 evidence openly while adding S256 and controls at S128. It retains algorithm, reconstruction, norm, quality gates and failed T56 costs; old evidence is not called a new measurement. It specifies a separate freeze, four new trajectories in one 1200-second child, output isolation, prior-data identities, explicit host/process-memory preflight and no fallback/escalation after a failed attempt. The large matrix estimate and need to account for temporaries are correctly distinguished from measured peak usage. I have not reviewed a future T57 wrapper or approved a particular allocation/monitor implementation. No T57 execution occurs in this T56 result.

A later success would not relabel T56, certify full t=1 behavior, validate a creator brief or establish a useful new method. The present result is a completed and informative reference-qualification failure. The full SIGGRAPH/TOG goal remains active and unachieved.

## Sealed identities

The following eleven final task-file identities were generated programmatically from actual bytes after final claims were ready. This review and later publication/audit files are outside this set.

| File | Bytes | SHA256 |
|---|---:|---|
| `.gitignore` | 7 | `a7d8bdcefba82a95ebc021d87c629fdea21f13af953bf01e28b7cf8b0eeceb41` |
| `FORMULATION.md` | 5434 | `0500b1fad0d187f7815f5751f33ec78835d60ea9b047b21ed08e74c28d39f029` |
| `PROTOCOL.md` | 7332 | `1b7defa36dbe33df2ff6d01ca52aa62117ea7aeaea8a1121d4deba66406ae537` |
| `reference.py` | 17488 | `51499f5c50b8f7f25ebb8df2569bc7eff085938cbd9d88f36b8604f9aaa4e01f` |
| `run_once.py` | 5666 | `8bc3082b5f1449998f2f27008cdb7b7616552afa9955898fd05aabece47c9ffc` |
| `input-manifest.json` | 2723 | `cd353bc8eec8eb4616be9f44922fcafcad67e953a85545db1f5c6286d9548967` |
| `execution.json` | 4937 | `6a2b25ae1b11c47921f535589637a7412b9d9c94110b617e285bc7b38d02b746` |
| `result.json` | 31700 | `95e616130f169cf325f79f3e27f79ac5879a029fef922291e92d4b11842ee099` |
| `RESULTS.md` | 8205 | `ea69873ac27a500eb438e34e4e0b3098e1903fc36f22a0c0978b6524241a2692` |
| `DECISION.md` | 5561 | `82aa1e72b36e2712b0a076ad000f3ad6221ea60f8380d8fbc5d9f424e2625c95` |
| `README.md` | 1534 | `66f61f93fcdf84997783af6dd7fd562a2502b48ff1a53fb559ab02829c1fabda` |

Historical frozen dependencies:

| File | Bytes | SHA256 |
|---|---:|---|
| `tracks/tog/tasks/t55-axisymmetric-reference/reference.py` | 10613 | `499bab137463df4435230e3cbf4d16b0723feed5ad5d06087a0bafd911204908` |
| `tracks/tog/tasks/t55-axisymmetric-reference/FORMULATION.md` | 4604 | `7d463593ec8f021ab814d0213bcf5f9b74b1c79ae9496b6d4cab2452f6440709` |
| `tracks/tog/tasks/t55-axisymmetric-reference/TASK.md` | 4132 | `b470e55c6449348136673764e7d7b975cd3bad479ddefa0d881d827eba84e89e` |
| `tracks/tog/tasks/t55-axisymmetric-reference/DECISION.md` | 6454 | `ed1d20b4b603ecb4afd49e06f4a33aba6b86ecbabd6bb1f87c4cbc445c1d420f` |
| `tracks/tog/tasks/t55-axisymmetric-reference/audit-manifest.json` | 9225 | `5bc23f9b3e2deb550365d4ac2a1a94db4f8ed59064bd15aab5b85a8f45ec7d76` |

Ignored local helper, started marker, logs, case records and raw evidence identities:

| File | Bytes | SHA256 |
|---|---:|---|
| `local/freeze.py` | 1797 | `53634118a22ee3df268b1fe07755943a4afc73ff8a62bd55aefaaca32b8079df` |
| `local/execution-started.json` | 1257 | `e56d47b78beb082aca49ff926c66a781ab35812cda86617ad103cfec91e83f6e` |
| `local/stdout.txt` | 2264 | `f2376100a2e7faa0e8b5335679adcf42dd7d848ec50a2356529610418bf5710d` |
| `local/stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `local/S32.json` | 3699 | `47bb8bad500fd15e70d86d76632ebffc04423793e1333627e5c4cf07020f6370` |
| `local/S32-steps.jsonl` | 141097 | `58d0a29de3441f50b1ff629b9de3940169e539635e5ae12b8eef5bf091c27bb5` |
| `local/S32.npz` | 698212 | `36c793aa2c96cc8da2c7ed84560ffdd96ff43ee5c127c1db347dbce1a661b8ce` |
| `local/S64.json` | 3700 | `c0a4563c85eba9652f33e53d3f1ea3b6a9fb7052300969ed4130af9b3c7199e3` |
| `local/S64-steps.jsonl` | 140400 | `8eb50ac12fac021cbbb2e1fde2e3398d08c7450f344e0eb5b0d6e3b9c715ffd6` |
| `local/S64.npz` | 2768740 | `1100e33caf1fd28d250ecda7b251aa4fbe0bba03501e1b5d9d3f5d7c5d396493` |
| `local/S128.json` | 3703 | `a17c2e94ece6f699581943986d779eaba63c6e3bc509040387cce0736259e075` |
| `local/S128-steps.jsonl` | 139459 | `3b922240d528a54dc5fda341b64be16a17b538e5dab3e3810c5cc5977be55c76` |
| `local/S128.npz` | 11038564 | `346d78f7f0ebba17c15fd1b5285c3472c1b4ac9d43cebf20eca9fe7532112bb2` |
| `local/T64.json` | 3708 | `2e4ee45283a0904f1c3ca48485e4210071e98310dc7cbf8d1bb9704f24af7609` |
| `local/T64-steps.jsonl` | 279795 | `ef68e23ccda4e58057b774459e57b4ddbebb630886027a910b0f73a93b04d36c` |
| `local/T64.npz` | 2768740 | `cb41eaae4a32ebcd3691ccc7a6a730a9f1f46992b201919106b99d1d56af680d` |
| `local/D96.json` | 3706 | `1a775fd305fab3a90662561f75a216b64155918c45e73fa974f380698d22cd2c` |
| `local/D96-steps.jsonl` | 140043 | `f906104dbb9aeba58119ac6e2cb7de9ec7b05d4abfaa8cf7affb3c86c8dda544` |
| `local/D96.npz` | 6215524 | `4220ea98751e0c8c2480fcefee8d920f03488a70af733e412f3ecfc8cf265dac` |
| `local/Q64.json` | 3698 | `b7eacf6e375017f3a37f96d6602ca01fdc701c54f6a6fb253a805b05a0ed4f6b` |
| `local/Q64-steps.jsonl` | 140363 | `fedf2b852ee10cf44b720d20ac1aad777163690aa769fc9edf72ad7a41244f98` |
| `local/Q64.npz` | 2768740 | `1dcb9f32f3c170f6af5d7badda8bdf6590de3c546b1dc2505dfca7ab7add6e8b` |

Executable: `C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`, 107312 bytes, SHA256 `5640e9be2fd33d05a1a9ae1228e2354609a69ab831605995ec4e2bd6da8fff5e`. This identifies python.exe, not every dependent runtime library.
