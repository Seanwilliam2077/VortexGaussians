# T30 — independent saved-arithmetic review

29 October 2026. Reviewer: pressure_screen. **All saved arithmetic and classification checks pass.** The result supports `close_whole_interval_two_event_certificate_on_fixed_scope`. This review inspected frozen sources and independently checked saved data; it did not import/call the screen, evaluate a candidate output or pair moment, integrate, evaluate exp/CDF, obtain sources or create inputs.

## Arithmetic and proof boundary

The reviewer rebuilt exact rational `tau` from T18's stored clipped masses and channel ranges from the original T17 colors, preserving their binary64 values exactly. Independently computed `S12` and `S13` by direct sums `sum((-t)^k/factorial(k))`, rather than the worker's term recurrence. All **578 packed rationals**, including the two epsilon values, match their stored canonical numerator, denominator and decimal approximation exactly. This covers tau, three ranges, maximum range, t, both polynomials, tail endpoints and floor endpoints for all 48 cases. No epsilon was replaced by the nearby decimal rational 1/1000 or 1/100.

The enclosure argument is sound on this stored-mass model. On `[0,1]`, decreasing alternating terms give `S13<=exp(-t)<=S12`; positive multiplication by `1+t+t²/2` and subtraction yield the stated tail bounds. Since `p3'(tau)=exp(-tau)*tau²/2>=0`, substituting `t=1` for larger tau preserves a **lower** bound. The worker correctly uses upper bound 1 in that branch, not the upper bound at t=1. Clamping the lower tail to zero and the upper tail to one preserves validity. Multiplication by nonnegative half-range is valid. Empty-input extrema and all zero cases are handled explicitly. There are 34 cases with tau>1.

This is exact arithmetic for **stored rounded masses/colors**, not a formal enclosure of the underlying Gaussian CDFs or a certificate for an unevaluated RGB implementation. The tail floor constrains the declared radius; it is not a lower bound on actual approximation error. Survival of this filter, including a floor upper endpoint below epsilon, does not establish the complete radius or output accuracy.

## Identity, populations and result

All eight frozen artifacts match current bytes/hashes and both saved identity maps. Freeze and worker hashes match the execution receipt; stdout/stderr lengths and hashes match. All 48 journal records equal the result cases in order. Original fixtures, 399 labels, T18/T21 mass/RGB/G equality, source qualifications and stable input orders agree. Independent reconstruction of common exact/G/2 paths and T21 bounds recovers the same 28-ray population and acceptance IDs at both epsilons.

Every exact lower/upper comparison and all saved per-case flags match. Exclusion uses **strict `lower>epsilon`**, without a numerical allowance. Aggregate lists, counts, zero survivor union and decision flags agree:

| Epsilon | Common-unsolved population | T21 accepted, each cap | Tail-floor excluded in population | Primary unresolved survivors |
| --- | ---: | ---: | ---: | ---: |
| .001 | 28 | 1 | 28 | 0 |
| .01 | 28 | 4 | 28 | 0 |

The smallest eligible lower floor is **0.010747264457053604**, on `generic-10-n4`; its exact rational comparison is still strictly above .01. The largest eligible lower floor is approximately 0.040150698348398. These are lower endpoints, not evaluated true tail probabilities or output errors.

Across **all 48 cases**, .001 excludes 35 and retains 13; .01 excludes 34 and retains 14. At .01, `generic-05-n2` has a floor interval straddling epsilon and is correctly retained by the necessary filter. It is outside the declared N>=4 population. Thirteen cases have an upper endpoint at most epsilon at either tolerance; no lower endpoint equals epsilon exactly. These observations do not add accepted candidate outputs or justify changing the population.

## Work accounting and decision

Static loop inspection and saved case fields match **48 cases, 399 labels, 624 fixed term updates and 96 exact epsilon classifications**. Thirteen recurrence updates were performed per case, including trivial cases. Candidate outputs and pair moments are zero; the script contains no exp/CDF/integration call. These counters describe the declared screen work, not all rational-integer operations or future delivery cost.

The sole invocation completed without failure/timeout/retry. Worker time before final serialization is **0.06335179996676743 s**; the supervisor's child-launch-through-exit interval is **0.2219267999753356 s**, below its 30-second cap. The latter includes child startup/imports and final serialization, but excludes the supervisor's preceding freeze check and later receipt write. These nested intervals are not added, and their difference is not a serialization-only measurement. Reading already prepared masses avoids their acquisition cost; no complete-method timing follows.

The independent saved-data audit completed without a mismatch or audit repair. No original script or result was changed.

Because every eligible ray is already excluded by this certificate's floor, closing this whole-interval two-event/certificate route on the fixed development scope follows the predeclared rule. Computing pair corrections or running a cost study is unwarranted under this protocol. This does not establish that the proposed output is inaccurate, that other tail treatments fail, that the broader integration problem is solved, or that a TOG contribution exists. T29/T28 closures and all historical gates remain unchanged; no successor experiment is authorized by this arithmetic pass.

## Reviewed identities

Task-local paths below are relative to `tracks/tog/tasks/t30-two-event-output-screen/`.

| Artifact | SHA256 |
| --- | --- |
| T17 `inputs.json` | `5cccf0238c679e14bc50e67d2d24726a58295b484b1d3464bf77d4eca0491cb7` |
| T18 `run-01/results.json` | `fa4fb6887c6b38e800f18e919634821b3ee51c2fb0122cd0dbb4047eead7873d` |
| T21 `run-01/results.json` | `94d3ad607ba70ee6d7192643e6ad39ec3802f2a269b12df8cbfe87e59917bf83` |
| `PROTOCOL.md` | `d1786206c2d4ce1273d167fc7a8d08bfc4850c1ee778dd99b998e70bd31361bf` |
| `DERIVATION.md` | `950cafccafbe9ef88b87795f6f2d9a18889926b3489499649e8a01c13a5451a5` |
| `screen.py` | `fc1b65f3e3e5fb00f30740d4ef612256875350d0d29eeb31072d9e06f457b5e9` |
| `supervise.py` | `b565083a838b1745f93d057a18d8471af50b29f2a5fbb8212dba39b5c7ae9cc6` |
| `tracks/validation/t30-pre-execution-review.md` | `7b3b01345becd05064a27c2e88ca758a9da2c04ed9bcc122e1658b7a03de7624` |
| `freeze.json` | `3e17dac02400b0994e80d24547f84ce8640411c358524f33121895d1d51080db` |
| `run-01/results.json` (171,103 bytes) | `b0d3a60086c9fc036cf25917fadc80cf6add8e2cc0134765834c295fcbf5d35b` |
| `run-01/journal.jsonl` (117,170 bytes) | `0990492d36229e981cc6c59ce766fabd3c50916539d9169f961248f8e863b24c` |
| `run-01/execution.json` | `f1ffcdaa6b35243011c1dfec7537084f56c21ab98ac4d7b07a538c9384cbd115` |
| `run-01/stdout.txt` | `e4252e068280217b05a18ea0b2b569ffbc7ae10d5e63cc223c3ae2a7d6a2e69e` |
| `run-01/stderr.txt` (empty) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
