# T13 saved-evidence CPU review

2026-10-27. The independent review **passed** on its first execution. This is an audit of saved arrays and records, not a successful feasibility search. The producer completed with `NO_NONSEED_FEASIBLE_POINT_FOUND_WITHIN_FIXED_SEARCH`.

The auditor imports NumPy only when `--execute` is supplied. It did not import the producer, Torch, run AD, render, advance a state, or measure new solver performance. [Script](t13-array-review.py), [machine-readable result](t13-array-review.json), [pre-run review](t13-pre-run-review.md).

## Verified evidence

- All **14 NPZ / 91 arrays** match their file SHA, byte size, raw SHA, dtype and shape; all stored numeric arrays are finite. All frozen source/input pins match the recorded before/after sources and the current files. The 12 portable input arrays also match their original T12 source arrays byte for byte.
- T13's saved analytic `theta`, 20 observation images, initial velocity, step-20 velocity/density, first 20 state-metric rows and constraints are **byte-identical** to the corresponding T12 G0 prefix; maximum difference is zero in all seven comparisons. This supports the saved observation-prefix identity, not an independently recomputed trajectory.
- Recomputed 163842-constraint PHR sums and gradient–L2-unit-direction products pass the original two-direction/two-step FD gate. Maximum independent relative FD error is **3.5390713521e−8**, below `1e−4`. All 163842 analytic PHR branches are active, minimum absolute branch margin **0.5114435288**. Saved numerical diagnostics and recorded allocator peaks pass G0. CPU summation produces tiny FD differences from the producer's GPU reductions; no gate was changed.

## Search result

The saved G0 point is the search initial state. Its raw images give **1965** interval violations and maximum alpha violation **0.00191590773011**. With the search's reset lambda=0 and penalty=1, its recomputed PHR loss is **13.4601722139**.

The saved least-violating point is evaluation **68**, independently recovered as the earliest strict lexicographic minimum of `(maximum positive constraint, sum of squared positive constraints)` over the complete valid-call ledger. Its arrays give:

| Quantity | Recomputed value |
|---|---:|
| Maximum alpha interval violation | 4.6896847252703155e−5 |
| Violating pixels | 170, spread across all 20 frames |
| Maximum positive scaled constraint | 0.011958696049439305 |
| Sum of squared positive constraints | 0.0031184919405752515 |
| Initial velocity maximum / component RMS | 0.1406874541354641 / 0.07104650647319333 |
| Velocity difference from seed, maximum / relative L2 | 0.0032560496472345338 / 0.012108841948520183 |
| PHR loss under the applicable saved AL multipliers | 0.002105900069192055 |

Both saved outer multiplier updates reproduce the declared rule; penalty remains 1. All **78** search evaluations are recorded as numerically valid, within the initial-velocity priors, and nonseed; **zero** satisfy the observation-interval gate. Only the saved initial/least images and fields are independently recomputed here. Other trial eligibility and least-selection order are verified from their scalar ledger; their unsaved images are not independently reconstructed. Thus this is not a claim that every trial was independently re-rendered.

The search ended at **36 returned steps**, its fixed 3×12 return budget, with 36 acceptance-cache hits and zero misses. It did not exhaust the 80-call cap or stop on timeout. No candidate, paid full verification, future trajectory or response score exists; the least point is explicitly not a witness.

## Cost and interpretation

New G0: 9 observation evaluations / 1 reverse / **2.7304203 s**. Search: 78 observation evaluations / 77 reverse / **36.8805885 s**, including its IO. Total: **87 observation evaluations, 1740 simulated steps, 78 reverse calls, 0 full evaluations**. Recorded worker wall is **55.6126804 s**. The individual search-call timer sum is 35.2484123 s and is contained within search wall; it is not added again. These are producer measurements, not independent timing repetitions.

The finite ordinary recovery run reduced the recorded violation but did not produce an eligible alternative state. This does **not** establish uniqueness, infeasibility, safety, absence of an alternative response, or superiority of a new method. It also does not show collapse back to the seed: every recorded search point remains nonseed under the declared threshold. No response conclusion is available without a feasible state and its paid continuation.

Reproduce from repository root (safe CPU NumPy runtime; a fresh output path is required):

```text
python -I -B tracks/validation/t13-array-review.py
python -I -B tracks/validation/t13-array-review.py --execute --out NEW-AUDIT.json
```

The ignored local `runs/run-01/worker` and original T12 raw archives are required for this full audit; they are not implied to ship in a repository clone.

Audit script SHA256: `6602dd6cc01451b0b25f9b738f9d60905b40edccb9b74d21b6c574baef6af0ce`.
Audit JSON SHA256: `f6a6895f2064f8ee0c7d7708b8ad135a823ed628e99ddb88511ddb2206ae9aa9`.
Producer runner SHA256: `0c35cd801bb4930679044b9b8490336b2de05978459b0e51d83b53fb390dcdbe`.
Producer freeze SHA256: `7615e63bf6e4868566290423f7925d192a035ae5bc32f4157daea726f9a70b12`.

Review stopped after this bounded saved-evidence audit. No producer evidence or protocol was modified.
