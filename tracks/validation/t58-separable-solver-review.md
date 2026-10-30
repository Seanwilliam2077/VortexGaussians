# T58 mathematical and saved-data review

**Verdict: no unresolved blocker.** The one fixed invocation qualifies only the declared same-discrete-operator fixtures: 18 saved T56 states and one manufactured system. All six frozen categories pass. No new fluid trajectory, Green matrix, CG solve or Gaussian candidate was run. T56's failed physical qualification and T57's timeout remain unchanged; T58 does not establish a short/full-time physical reference, matched speedup, new research mechanism or TOG contribution.

## Review provenance

I participated in pre-run design/code readback and retain the earlier T48–T57 collaboration context; this is not a blind review. Before freeze I read actual FORMULATION, PROTOCOL, solver.py, evaluate.py, supervisor, OS probe and ignored freezer, checked the half-cell transform and original operator by hand, and requested that the u/J gates explicitly mean two combined field norms rather than five separately normalized Jacobian gates. I inspected the corrected text before reporting no blocker. The eigen-identity denominator was explicitly defined before measurement as operator-normalized, while also reporting eigenvalue-relative diagnostics; the full Poisson RHS-relative gate was never changed.

After completion I independently checked final bytes, machine receipts and local records, then used bundled NumPy only to load/reduce existing arrays, reconstruct derivatives and apply the original assembled stencil. I did not import or execute solver.py, evaluate.py, T55/T56 modules, FFT/DST, Thomas, CG, source quadrature or a fluid trajectory; no new solve or fixture was generated. Verifying that stored known_phi matches its frozen formula and applying the old stencil to stored fields are readback checks, not independent method replication. Transform tests were audited from frozen source and saved records, not rerun. No external sources were accessed.

The one saved-array readback took .1663152000401169 s after its identity setup; its process clock before printing, including imports, hashing and reductions, was .4073576000519097 s. These are reviewer postprocessing costs, separately recorded, not part of the scientific child or a performance benchmark. Additional plain-text/JSON identity checks used standard-library bookkeeping. Only this review is written; root owns drafts, publication and subsequent experiments.

## Algebra and implementation

The checked original FV stencil has radial coefficients L_i=r_i^3/(W_i*h), U_i=r_(i+1)^3/(W_i*h), W_i=(r_(i+1)^4-r_i^4)/4. Its axis face has L_0=0; the outer radial diagonal has the extra U_last. Axial endpoint diagonals are 3/h^2, interior diagonals 2/h^2 and neighbors -1/h^2. The candidate RHS includes 2*U_last*gR and 2*gminus/h^2, 2*gplus/h^2. Corners affect unchanged reconstruction but not the five-point solve.

The evaluator's independent radial-flux/ghost application equals the original assembled matrix algebraically. It does not use new factors or transforms to test its residual or manufacture b. The W-weighted RHS-relative residual is a distinct required check from comparison to the old CG answer. Floating-point application order can change tiny residual values; both forms are disclosed below.

The half-cell sine modes, positive eigenvalues and exceptional last-mode norm are consistent with the boundary rows. For odd extension (x,-reverse(x)), phase-corrected rFFT returns unnormalized sine coefficients. The inverse explicitly places the real Nyquist coefficient 2*S_n; irFFT supplies the distinct last-mode normalization. Pure-mode forward tests prevent mutually compensating forward/inverse errors from passing round trips alone. Thomas uses lower multiplier -L_i/pivot_(i-1), subtracts its product with the previous -U, then performs the correctly signed back substitution. Positive eigenvalues give strictly diagonally dominant weighted-SPD radial systems; every actual pivot and output is checked finite/positive as applicable. Factors are rebuilt per fixture and charged.

The schedule is exactly five fixed transform lengths, 18 ordered original state systems and one 256/512 manufactured system. Importing T55 exposes only its reconstruction/error routines; the inspected evaluator never calls its Poisson, oracle, quadrature or main. Saved u is checked bit-for-bit at all 18 states and J0 at six initial states; later old J is reconstructed from unchanged saved phi/boundaries. The fixture equations and physical norms are not refitted or aligned.

## Independent saved-array reduction

All selected old and new arrays were finite, had the required shapes and matched their recorded identities. Every new stored u/J matched a direct readback reconstruction of its saved new phi/boundary exactly; every old reconstructed u matched saved old u exactly, and all six reconstructed initial old Jacobians matched J0 exactly. Whole-box weighted phi errors and the two-component u/five-component J fixed-core norms matched reported values to rounding. The fixed-core weight is 2*pi*r*h^2; the solution norm uses W_i over the whole box.

Using a separately written assembled application of the old five-point matrix, rather than the evaluator's flux order, gives maximum new saved-state RHS-relative residual **1.1624278431001151e-14**. The evaluator reported maximum **1.0767234826632053e-14**. Both pass the unchanged 1e-10 gate; no residual was substituted after seeing output. Maximum independently reduced phi/u/J errors are respectively **3.25769400659253e-10**, **2.2089481688394202e-10**, **9.738389553867647e-10**, below 1e-8/1e-7/1e-7. The old-CG assembled diagnostic maximum is 9.937151747628645e-11, versus its flux diagnostic 9.937153528542003e-11. Old uncertainty remains visible and historical verdicts are not rewritten.

The stored manufactured known_phi is bit-identical to its prescribed nonconstant radial factor and axial modes 1,7,n. Applying the assembled old operator to that known array differs from saved flux-constructed b by relative **1.1839262101995246e-15**. For the saved new solution, the assembled residual is **2.1019381518200188e-15** (reported flux residual 1.8623116251166877e-15) and known-phi error is **1.710080546054833e-13**. These pass both frozen gates. This signed algebraic fixture does not certify real dynamic-boundary work.

Saved transform records contain exactly 20 round trips, 15 pure-mode forward checks and 15 eigen identities at n=64,128,192,256,512, explicitly including k=n. Their maxima are 3.2229148165710374e-16, 1.0056081173056278e-15 and 4.515502408099259e-16 for round trip, forward coefficients and operator-normalized eigen residual. The eigenvalue-relative diagnostic maximum is 8.401481768320384e-12. I recomputed the predicates from these records without rerunning transforms; denominators were not interchanged. All six final check categories are consistent with the inspected source, saved reductions and result status.

## Runtime, outputs and costs

The exclusive marker records zero scientific children before the single Popen; execution.json records one afterward, with all other original marker fields matching. The supervisor contains no retry/fallback and validates preservation before granting qualification. It requires 18 fixture records, two supplemental records, 19 raw files, correct order/counts/runtime, zero physical work, successful return and all fixed time/memory conditions. The stdout contains 18 matching fixture messages followed by the matching final status; stderr is empty. Every fixture JSON equals its result entry, as do transform/manufactured records.

The child returned 0, supervised in **.768266599974595 s** within 180 s. Its internal before-result-write time is .5143095999956131 s and supervisor before-receipt time is .8934892000397667 s. Summed solver calls are .028695999877527356 s, including fresh factors and both transforms. Summed fixture timers are .30533359991386533 s; those source timers stop before writing each JSON record, so the whole child remains the complete cost authority. All file output and final record work are charged there. Phase attribution is nested, not a set of disjoint totals. The published per-case maxima, solver/fixture sums and phase totals match independent JSON reductions.

The prior T56+T57 supervised cost 1316.7941713000182 s is retained, giving **1317.5624378999928 s** through T58. This three-task sum excludes older project history, whose receipts remain intact. Different sets of work cannot be compared as a matched speedup. The 19 new NPZs total **18101784 bytes** and remain ignored.

Preflight/launch available physical memory is 27193638912/27049332736 B, above 3 GiB. All four memory observations are valid, time ordered and lifetime-peak nondecreasing. Maximum observed working-set peak is **60043264 B**, below 2 GiB; maximum sampled private usage is 798400512 B and peak pagefile is 819228672 B. Private/commit fields are not separate stop gates. The last successful sample at .7666306999744847 s retains the lifetime peak; no query error is recorded. Held-handle peak observations are not a hard allocator cap, reserved host capacity or an independently proven bound over every possible observation/exit tail.

The scientific executable, all 43 frozen input bytes, linked log/raw/record identities, freeze receipt and result identity were independently rehashed and matched. Python 3.12.14/NumPy 2.3.5 are present in the completed result and were asserted by the child. No claim rests solely on a prior tiny-runtime probe.

## Final documents and next-task boundary

Final README/RESULTS preserve the fixture-only qualification and costs. Before sealing, the next decision was corrected to retain **full-box circulation-weighted absolute axial centroid and covariance** diagnostics; the common core restricts field errors, not moments. The new port comparison is explicitly q-represented physical vorticity with 2*pi*r^3 weight and velocity with 2*pi*r, with old-field denominators, not the q-squared invariant. Euler/reconstruction finiteness and original face bounds remain explicit. I read back these corrections and the reviewer timer's before-printing limitation. No scientific input changed.

T59 is prepared as six new same-solver trajectories with all historical gates, an additional old/new S64/S128 port regression, independently checked original residual per solve, fresh factor costs, immediate real-field checkpoints and explicit kernel lifetime accounting. Its one 600 s child requires a separate freeze; no T59 implementation/run is claimed here. Complete source/transport/Green costs and all six cases must pass; a checkpoint or one case cannot qualify the task. Later t=1 work and an ordinary complete-tangent Gaussian comparison remain separate. Retaining c=beta_star*a_z avoids dropping amplitude from that future translation baseline. T58 supplies an ordinary implementation component, not a core paper contribution.

## Final reviewed task identities

These 14 direct task-file identities were generated from actual final bytes after all prose corrections. Publication helpers and a later audit-manifest are parent-owned and are not included in the claimed review set. This report's own hash is reported separately, not recursively embedded.

| File | Bytes | SHA256 |
|---|---:|---|
| `.gitignore` | 7 | `a7d8bdcefba82a95ebc021d87c629fdea21f13af953bf01e28b7cf8b0eeceb41` |
| `FORMULATION.md` | 5399 | `d70c1a2105a3beb2506001335a1dbb581bd768f1ce3e1ef584ba3f50608dcfa3` |
| `PROTOCOL.md` | 6877 | `d51ae3b26279af8f3eda3eb6bb7903f95be9653093fb11ea62da8a810c667d1e` |
| `solver.py` | 2790 | `c643626adb909d79cb352a5d08d9355e1ecf749c6f39cc266bf98a52edbe3e16` |
| `evaluate.py` | 8878 | `09c632b35abf5aa625bb417aa818fb755a281af6211d430d82c46797534f3baa` |
| `run_once.py` | 8248 | `bb352b7cb41ef30348df828c5f642baa01a327a62ed53de4caf9bbce4c51ef8a` |
| `resource_preflight.py` | 1589 | `8ac1acd72335f11015ea5f8218ce24563a3407d9ec254a5032072ab51830bedf` |
| `resource-preflight.json` | 906 | `39f57e566cc3908fb8f81d7fbe18b78be0e865104dba76159caea21fb5446cf3` |
| `input-manifest.json` | 9574 | `7d5ebdfaef27de08d97c9f6635b3a984a4d88d5a01b5fc3cefc38b4b5850675f` |
| `execution.json` | 8875 | `8fd003d7f2775c32744177b0808a3f4779711046c119c50f948994022ad2087f` |
| `result.json` | 37501 | `34e8a1da37322456cccb8df9d1d6c0a0c4f9a0991048d20b056b012a4dc874b9` |
| `RESULTS.md` | 6821 | `6f15eb197db37a4bdf8e9a39f562909ccd1dff4d8ac035f533f36c6113378f7b` |
| `DECISION.md` | 7594 | `116bf655a4c48cf4917b27053794e843fa234ae8966000a32f460f212685aed6` |
| `README.md` | 1694 | `f7689e69e39501bab83f1c3b06c83627ab88f4113e1686986deb2064504a4b61` |

## All 43 frozen inputs matched

The following identities were regenerated from actual file bytes; old arrays were additionally read only for the explicitly authorized saved-field checks above.

| File | Bytes | SHA256 |
|---|---:|---|
| `tracks/tog/tasks/t58-separable-solver-qualification/.gitignore` | 7 | `a7d8bdcefba82a95ebc021d87c629fdea21f13af953bf01e28b7cf8b0eeceb41` |
| `tracks/tog/tasks/t58-separable-solver-qualification/FORMULATION.md` | 5399 | `d70c1a2105a3beb2506001335a1dbb581bd768f1ce3e1ef584ba3f50608dcfa3` |
| `tracks/tog/tasks/t58-separable-solver-qualification/PROTOCOL.md` | 6877 | `d51ae3b26279af8f3eda3eb6bb7903f95be9653093fb11ea62da8a810c667d1e` |
| `tracks/tog/tasks/t58-separable-solver-qualification/solver.py` | 2790 | `c643626adb909d79cb352a5d08d9355e1ecf749c6f39cc266bf98a52edbe3e16` |
| `tracks/tog/tasks/t58-separable-solver-qualification/evaluate.py` | 8878 | `09c632b35abf5aa625bb417aa818fb755a281af6211d430d82c46797534f3baa` |
| `tracks/tog/tasks/t58-separable-solver-qualification/run_once.py` | 8248 | `bb352b7cb41ef30348df828c5f642baa01a327a62ed53de4caf9bbce4c51ef8a` |
| `tracks/tog/tasks/t58-separable-solver-qualification/resource_preflight.py` | 1589 | `8ac1acd72335f11015ea5f8218ce24563a3407d9ec254a5032072ab51830bedf` |
| `tracks/tog/tasks/t58-separable-solver-qualification/resource-preflight.json` | 906 | `39f57e566cc3908fb8f81d7fbe18b78be0e865104dba76159caea21fb5446cf3` |
| `tracks/tog/tasks/t55-axisymmetric-reference/reference.py` | 10613 | `499bab137463df4435230e3cbf4d16b0723feed5ad5d06087a0bafd911204908` |
| `tracks/tog/tasks/t55-axisymmetric-reference/FORMULATION.md` | 4604 | `7d463593ec8f021ab814d0213bcf5f9b74b1c79ae9496b6d4cab2452f6440709` |
| `tracks/tog/tasks/t56-coupled-reference/reference.py` | 17488 | `51499f5c50b8f7f25ebb8df2569bc7eff085938cbd9d88f36b8604f9aaa4e01f` |
| `tracks/tog/tasks/t56-coupled-reference/FORMULATION.md` | 5434 | `0500b1fad0d187f7815f5751f33ec78835d60ea9b047b21ed08e74c28d39f029` |
| `tracks/tog/tasks/t56-coupled-reference/PROTOCOL.md` | 7332 | `1b7defa36dbe33df2ff6d01ca52aa62117ea7aeaea8a1121d4deba66406ae537` |
| `tracks/tog/tasks/t56-coupled-reference/result.json` | 31700 | `95e616130f169cf325f79f3e27f79ac5879a029fef922291e92d4b11842ee099` |
| `tracks/tog/tasks/t56-coupled-reference/execution.json` | 4937 | `6a2b25ae1b11c47921f535589637a7412b9d9c94110b617e285bc7b38d02b746` |
| `tracks/tog/tasks/t56-coupled-reference/input-manifest.json` | 2723 | `cd353bc8eec8eb4616be9f44922fcafcad67e953a85545db1f5c6286d9548967` |
| `tracks/tog/tasks/t56-coupled-reference/audit-manifest.json` | 9396 | `601bc9d1b431d7fa1ed8703d007dc118297c90ffdce00150fb83083d79643622` |
| `tracks/tog/tasks/t56-coupled-reference/local/S32.npz` | 698212 | `36c793aa2c96cc8da2c7ed84560ffdd96ff43ee5c127c1db347dbce1a661b8ce` |
| `tracks/tog/tasks/t56-coupled-reference/local/S32.json` | 3699 | `47bb8bad500fd15e70d86d76632ebffc04423793e1333627e5c4cf07020f6370` |
| `tracks/tog/tasks/t56-coupled-reference/local/S32-steps.jsonl` | 141097 | `58d0a29de3441f50b1ff629b9de3940169e539635e5ae12b8eef5bf091c27bb5` |
| `tracks/tog/tasks/t56-coupled-reference/local/S64.npz` | 2768740 | `1100e33caf1fd28d250ecda7b251aa4fbe0bba03501e1b5d9d3f5d7c5d396493` |
| `tracks/tog/tasks/t56-coupled-reference/local/S64.json` | 3700 | `c0a4563c85eba9652f33e53d3f1ea3b6a9fb7052300969ed4130af9b3c7199e3` |
| `tracks/tog/tasks/t56-coupled-reference/local/S64-steps.jsonl` | 140400 | `8eb50ac12fac021cbbb2e1fde2e3398d08c7450f344e0eb5b0d6e3b9c715ffd6` |
| `tracks/tog/tasks/t56-coupled-reference/local/S128.npz` | 11038564 | `346d78f7f0ebba17c15fd1b5285c3472c1b4ac9d43cebf20eca9fe7532112bb2` |
| `tracks/tog/tasks/t56-coupled-reference/local/S128.json` | 3703 | `a17c2e94ece6f699581943986d779eaba63c6e3bc509040387cce0736259e075` |
| `tracks/tog/tasks/t56-coupled-reference/local/S128-steps.jsonl` | 139459 | `3b922240d528a54dc5fda341b64be16a17b538e5dab3e3810c5cc5977be55c76` |
| `tracks/tog/tasks/t56-coupled-reference/local/T64.npz` | 2768740 | `cb41eaae4a32ebcd3691ccc7a6a730a9f1f46992b201919106b99d1d56af680d` |
| `tracks/tog/tasks/t56-coupled-reference/local/T64.json` | 3708 | `2e4ee45283a0904f1c3ca48485e4210071e98310dc7cbf8d1bb9704f24af7609` |
| `tracks/tog/tasks/t56-coupled-reference/local/T64-steps.jsonl` | 279795 | `ef68e23ccda4e58057b774459e57b4ddbebb630886027a910b0f73a93b04d36c` |
| `tracks/tog/tasks/t56-coupled-reference/local/D96.npz` | 6215524 | `4220ea98751e0c8c2480fcefee8d920f03488a70af733e412f3ecfc8cf265dac` |
| `tracks/tog/tasks/t56-coupled-reference/local/D96.json` | 3706 | `1a775fd305fab3a90662561f75a216b64155918c45e73fa974f380698d22cd2c` |
| `tracks/tog/tasks/t56-coupled-reference/local/D96-steps.jsonl` | 140043 | `f906104dbb9aeba58119ac6e2cb7de9ec7b05d4abfaa8cf7affb3c86c8dda544` |
| `tracks/tog/tasks/t56-coupled-reference/local/Q64.npz` | 2768740 | `1dcb9f32f3c170f6af5d7badda8bdf6590de3c546b1dc2505dfca7ab7add6e8b` |
| `tracks/tog/tasks/t56-coupled-reference/local/Q64.json` | 3698 | `b7eacf6e375017f3a37f96d6602ca01fdc701c54f6a6fb253a805b05a0ed4f6b` |
| `tracks/tog/tasks/t56-coupled-reference/local/Q64-steps.jsonl` | 140363 | `fedf2b852ee10cf44b720d20ac1aad777163690aa769fc9edf72ad7a41244f98` |
| `tracks/tog/tasks/t57-finer-short-reference/DECISION.md` | 9091 | `2ff004ffa50276bdbf425d80df06be29b1017abbc60180fe04050221c900f328` |
| `tracks/tog/tasks/t57-finer-short-reference/PROTOCOL.md` | 6948 | `02cab7e2195ab268dd3d00c98ab741825a44f9d80176e64115faa600ef30404d` |
| `tracks/tog/tasks/t57-finer-short-reference/execution.json` | 2793 | `0fba254f5b3b485eca041fd93a3dd1cd0bb1ddb780b94e28faf0d190bd6f4672` |
| `tracks/tog/tasks/t57-finer-short-reference/input-manifest.json` | 6538 | `6dc00fa6ed67bcd689e95b5c31457818e359d8142921e0b3da6a10c60430e91f` |
| `tracks/tog/tasks/t57-finer-short-reference/audit-manifest.json` | 13819 | `4fe8d7f41632910d26d6e3eadb66d9879715d3ba5a3232aa9ba107ad14db3aa8` |
| `tracks/tog/tasks/t57-finer-short-reference/memory.py` | 2231 | `4b83a89eff664dc0d86fb0c71b39c99d71720c1d18c5f93557e279d0ca3745fd` |
| `tracks/validation/t56-coupled-review.md` | 17447 | `ec44008a21429649bca6c2d77ff2b242003124e602510cf02d8e531ec8a62a4a` |
| `tracks/validation/t57-finer-short-review.md` | 21442 | `217b5d2acd9b8e1409258ec6ca3cfd17293fa36466bbfb82ddb6cb9d39129a29` |

## Key local receipt and diagnostic identities

All 18 fixture JSONs, 19 raw NPZs and their identities were checked against execution.json/result.json. Their complete per-file identity list is anchored by the reviewed execution/result hashes above rather than duplicated here. Additional inspected local records are:

| File | Bytes | SHA256 |
|---|---:|---|
| `local/freeze.py` | 3528 | `45d0bb72c78ec3a1e6040064d4bf4c6401efc96e57da187eb136aace889e34f7` |
| `local/freeze-receipt.json` | 288 | `ba2271aa19db3b383b4978b28fe95aba96845e4386ad231803a49fbbb9f873b4` |
| `local/execution-started.json` | 1518 | `159402d14d71cffbe67336cf873f862da46a223cca60d3900180a8bce13fb6ad` |
| `local/transform-checks.json` | 3939 | `e26e81271aec0a113e471abd188ae2a272aef22768da07ee7472e0c430cca927` |
| `local/manufactured.json` | 1007 | `ac62453b971fd1dbd37c90c9dba2c1e2badae7b58342006be1fade9f78ffc608` |
| `local/stdout.txt` | 904 | `9fba73b72c4fb3e77c4b4ac23eaa798bec9a37302e7bfb71e0b867fb224e8ccd` |
| `local/stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `local/memory.jsonl` | 711 | `405d24cc1dd8186b15d500234eaaeddb73a960dbac3d1f826cb4a49c1b259374` |

Scientific executable matched to manifest and receipt:

| File | Bytes | SHA256 |
|---|---:|---|
| `C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe` | 107312 | `5640e9be2fd33d05a1a9ae1228e2354609a69ab831605995ec4e2bd6da8fff5e` |

No scientific solver was executed by the reviewer. Passing this review and these linear-system fixtures does not change the unresolved physical-reference, finite-time candidate or TOG-contribution requirements.
