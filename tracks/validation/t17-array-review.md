# T17 independent saved-data review

29 October 2026. **T17 did not pass its all-48 qualification.** Attempt 1 failed during numerical-rule initialization; the single repaired attempt completed all 48 records but qualified only 41. Seven adaptive Simpson references failed. The saved evidence is internally consistent, and available comparisons reveal no bound violation above the original allowance. Neither statement converts the seven failures into passes.

This reviewer read the protocol, derivation, original and repaired code, failure/diagnostic records and saved inputs/results. Checks used Python standard-library parsing, hashing, arithmetic and closed-form expressions only. No qualification module was imported, no ray integrand or quadrature was rerun, no random inputs were regenerated, and no new fixture, web request, dependency or GPU work occurred. Two preliminary metadata-query mistakes (Windows path separators and a nonexistent `records` key) were corrected in local review commands before the complete review; they changed no task data and were not qualification retries.

## Fixed evidence identities

The following paths are relative to `tracks/tog/tasks/t17-order-inversion-bound/`.

| File | SHA256 |
|---|---|
| `inputs.json` | `5cccf0238c679e14bc50e67d2d24726a58295b484b1d3464bf77d4eca0491cb7` |
| `PROTOCOL.md` | `4c631c90d08d1e5b9ac19ebc6e52cbd2c902c267af105ccbedeb1cccc292586c` |
| `DERIVATION.md` | `0bbbf3cac5e470fdfee175d835dd838370a0e134448caf61ec0e937ff1b3f27c` |
| `qualification.py` | `d648567e27b030c454ba37fdbee11b0df1b7de6b9e2a78c10a66cc0031557831` |
| `REPAIR.md` | `6318e4442e238106a5b9727a2124707a0ff8451178f5628b369798f4dc253f13` |
| `run-01/source-qualification.py` | `8d0e4221ba82708e14f2db9764d35f4ed48cf1ae3dc82f857cdb7823f0e14953` |
| `run-01/attempt.json` | `7562a9b11bf525ccaf515c1075e3cc83676e9b3cf9b7852f1a34cb7ffa20a977` |
| `run-01/execution.json` | `f894bf22f2bc1d09f23407584fe8067d6c4bfebe0d6a406dea7e9c47b6709bf8` |
| `run-01/runtime-diagnostics.json` | `2e595b522907f07c2d45b44cc386ad29e3c343c316aae8b8599ff3846e0c0df8` |
| `run-01/runtime-inherited-diagnostics.json` | `183c7dadbb6050bf0d6c768ee7b94a5478c999d434c9871c93eb54562b061775` |
| `run-01/runtime-leggauss-diagnostics.json` | `a8c75df36df42520bb2dcdf80de8249dd1b22af92996c6cdcc3f7a01f222fc38` |
| `run-02/attempt.json` | `961614550ddb50d6971bd011e81021ac598434e47779d5bb80357267793f77c5` |
| `run-02/execution.json` | `9c3cc1395b91da0ed52be18229f2c6d85b26cf6c2f961ed0abb168b93a2f88e0` |
| `run-02/results.json` | `63203cad05febfad1adf5c1a56a3341a61dbd7489110f46e0fc7b012ba5d95d2` |
| `run-02/quadrature-rules.json` | `886349f4d1ed63221a3afd317bbe5e4ab13532054f293207281135d5b1669375` |

Both attempts' before/after source, input and protocol identities match their manifests. The input retains the original generator hash; the repaired script is separately identified. All 48 per-case JSON objects equal their corresponding objects in `run-02/results.json` after parsing. A byte-identity manifest over those files has SHA256 `093b7b726975cbe5b6e217c6a6440c28174777adeede58994c4bc502ff5c317d`: sort filenames, concatenate `filename + TAB + lowercase file SHA256 + LF`, then hash that UTF-8 text. The complete result preserves every case even if these duplicate per-case files are not published separately.

## Input construction and repair scope

The saved input contains 48 unique IDs: eight controls, sixteen generic cases, sixteen structured cases and eight clipping cases. There are 399 primitive entries and 3,272 unordered pairs. The saved shapes, finite values, nonnegative weights, positive widths, RGB ranges, background and intervals satisfy the protocol. Control parameters/colors, the structured Cartesian-product order and alternating widths/cycling colors, and both clipping parameter families with their four intervals were checked directly against the written construction.

The generic size sequence is `(2,4,8,16)` repeated four times; all parameters fall in the declared ranges. Static generator inspection confirms `default_rng(20261028)` and consecutive draws for mean, log-width, log-weight and RGB. This review did not regenerate the random draw sequence; the immutable input hash and preserved generator identity are the recorded provenance.

AST comparison finds only `worker` and `run_supervised` changed among pre-existing functions, with `legendre_value_and_derivative` and `gauss_legendre_rule` added. The input generator, integrand, breakpoint construction, analytic controls, pair formulas, reference integrators, gates and summary functions are unchanged. The changes replace node construction and capture failure output; they do not change the scientific fixtures or tolerances.

The saved GL32/GL64 node/weight lists are ordered, symmetric, finite and positive where required. Recomputing their recorded moment sums for powers 0–12 gives maximum error `8.881784197001252e-16`, below the implementation check `5e-13`. The reported root residuals and iteration counts meet the saved rule checks, and rule data in the standalone JSON equals its results copy. This is a saved-rule arithmetic check, not a new quadrature execution or a proof of floating-point integration accuracy.

## Recomputed formulas and gates

Closed-form mass calculations from the saved input agree with the clipped masses. Stable mean ordering, exact full-line weights in the inversion expression, clipped-product cap, simple/Jensen pair values, color contrasts, aggregate sums, global cap and ordered RGB were independently recomputed. The maximum pair-field difference from operation ordering is `2.220446049250313e-16`. All recorded pair counts and breakpoint lists match their saved-input construction. No review consistency issue was found.

Using saved reference RGB values, the original comparison arithmetic and gates reproduce **41/48**, distributed as follows:

| Group | Completed | Qualified |
|---|---:|---:|
| Controls | 8 | 7 |
| Generic | 16 | 16 |
| Structured | 16 | 11 |
| Clipping | 8 | 7 |

The maxima over **available** reference outputs are:

| Quantity | Recomputed maximum | Original allowance |
|---|---:|---:|
| Any available reference pair difference | `7.671641100159832e-14` | `5e-10` |
| GL32 versus GL64 | `6.661338147750939e-16` | `5e-10` |
| Available reference versus applicable analytic control | `2.55351295663786e-14` | `5e-10` |
| Observed ordered error minus any saved bound | `4.6629367034256575e-15` | `1e-9` |

Vacuum, zero mass, the two single-profile controls, thin/thick coincident profiles and the red/blue identity retain all three numerical references. The red/blue absolute ordered error agrees with `alpha^2/2` in its two active channels. The equal-color control has only the two GL references: their analytic agreement does not restore its missing Simpson reference. All saved numeric values are finite, including outputs that belong to otherwise failed cases; finite records are not equivalent to completed references.

## Seven retained reference failures

Each row below records `Adaptive Simpson endpoint resolution exhausted`; none records a bound violation. The saved breakpoints contain initial segments that already trigger the code's midpoint/quarter-point resolution guard. This identifies a concrete implementation limitation without running a replacement integrator or changing the original breakpoint rule.

| Case | Simpson evaluations before failure | Guard-triggering initial segment widths |
|---|---:|---|
| `control-05-equal-color` | 258 | two at `2.220446049250313e-16` |
| `structured-03-n4-span1.2` | 1957 | `2.220446049250313e-16` |
| `structured-07-n8-span1.2` | 1858 | `2.220446049250313e-16` |
| `structured-11-n16-span1.2` | 1533 | `2.220446049250313e-16` |
| `structured-12-n16-span3` | 391 | two at `2.220446049250313e-16` |
| `structured-15-n32-span1.2` | 1212 | `2.220446049250313e-16` |
| `clipping-06` | 128 | `5.551115123125783e-17` and `2.7755575615628914e-17` |

They are failures under the predeclared gates, even though GL32/GL64 values are present and agree. No interpolation, merged breakpoint, substituted reference or third attempt was used in this audit. A future separately declared engineering correction cannot retroactively change T17's outcome.

## Informative-case counts and limits

Excluding controls and `N<4` gives 28 eligible inputs; 23 qualify numerically. At **both** `0.001` and `0.01`, the sole qualified case satisfying `max(E_jensen)<=threshold<max(G)` is `structured-04-n4-span3`. The simple bound also satisfies both thresholds for exactly that case. Thus Jensen adds **zero** threshold-passing cases in this saved set.

For that one case, `max(G)=0.6321205586470791`, `max(E_simple)=0.0004468241865962383`, `max(E_jensen)=0.00044456571657989856`, and the maximum GL64-referenced compositing error is `0.00009945938030458956`. These values provide a limited instance where pair information is useful relative to the global cap. They do not establish efficiency, a broad application regime or Jensen-specific practical benefit. The five failed eligible cases remain unknown to the complete qualification, rather than being silently dropped from its denominator.

The dense/thick cases are retained. For example, `control-07-coincident-thick` has maximum observed GL64-referenced error `0.6360905244548692`, while global, simple and Jensen bounds all saturate at `0.9999991584213054`. Passing validity does not imply an informative bound. Clipping cases retain the full-weight inversion formula and clipped-mass cap; one clipping reference failure remains unresolved.

## Failure and full recorded time accounting

Attempt 1 exits with native status `3228369023` (`0xc06d007f`) after `6.061168999993242` supervisor seconds. Its `cases` directory is empty. The original source creates that directory after import/input validation and before node generation. Independent retained diagnostics show three successful NumPy import probes and the same native exit during `leggauss(32)` after its pre-call marker. This supports the node-initialization failure window, not a proven DLL/BLAS root cause. No ray integration completed in that attempt.

Attempt 2 returns exit code **2**, completes all 48 records and preserves the seven failures. Its worker takes `2.843802500050515` seconds and supervisor takes `3.85225450003054` seconds. Neither attempt reaches its 300-second cap. The sole allowed repaired attempt has been consumed; this review authorizes no further run.

| Recorded work | Count / time |
|---|---|
| Adaptive Simpson integrand evaluations, including partial failures | `79,369`; `1.2780739995650947 s` summed reference time |
| GL32 evaluations | `31,616`; `0.4773100995225832 s` |
| GL64 evaluations | `63,232`; `0.943436799920164 s` |
| All reference evaluations | `174,217` |
| Sum of 48 case times | `2.7198729002848268 s` |
| Both supervised attempts | `9.913423500023782 s` |
| Four retained initialization diagnostics | `8.350453799939714 s` |
| Supervised attempts plus those diagnostics | `18.263877299963497 s` |

Reference and case times are nested inside worker/supervisor time and must not be added again to that total. Failed initialization and diagnostics are not discarded as warm-up. Input generation, prior dependency probes, implementation/review effort and complete research wall time were not fully timed; `18.2638773 s` is the sum of the identified recorded execution intervals, not end-to-end research cost or a renderer benchmark. The direct pair-bound calculation was not separately benchmarked against an equally informed ordinary method.

The defensible result is partial empirical qualification plus a preserved implementation failure, alongside the real-arithmetic derivation. T17 has neither a complete all-48 pass nor a numerical counterexample above the fixed bound tolerance. No formal floating-point certificate, literature priority, performance advantage, creator need or TOG contribution follows from this audit.
