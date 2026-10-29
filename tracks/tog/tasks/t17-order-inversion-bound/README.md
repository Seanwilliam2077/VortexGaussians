# T17: an order-inversion bound, with incomplete numerical qualification

29 October 2026. **The real-arithmetic construction has a checked derivation, but the full 48-ray qualification did not pass.** Attempt 1 failed during quadrature-node initialization; the one allowed repaired attempt processed all 48 rays, with 41 passing and seven reference failures. T17 is closed at its execution budget. No third run, changed threshold or relabeled failure is part of this task.

This is progress toward assessing a possible rendering mechanism, not an established TOG contribution. It stays within the continuous Gaussian emission–absorption operation considered in T15-C. T15's rejected generic interval mechanism and T16's source mismatch remain unchanged. The research goal remains active; the deleted hourly automation has not been recreated. Art files are unchanged.

## What is different

Instead of a generic color enclosure, the [derivation](DERIVATION.md) bounds whole-primitive compositing error through **pairwise reversed optical mass weighted by color contrast**. A first-arrival coupling handles any finite number of components. A Jensen saturation tightens the simple pair bound in real arithmetic. The Gaussian full-line ordering probability is analytic; finite clipping requires keeping full-line weights in that probability term, alongside a clipped-mass upper bound.

The target is a continuous, colored self-emission integral with prescribed extinction densities. Learned peak opacity, scattering transport and the original demo's rendering are not identified with that model. The proof assumes exact arithmetic; this implementation is not a floating-point certificate. Computing all pairs costs O(N²), before any fallback integration or scene-level preprocessing.

The [bounded source screen](RELATED_WORK.md) inspected three identified families after two disclosed exploratory queries. Ordinary controlled-precision integration and hybrid transparency are established prior work. Two primary full texts were inaccessible. No priority claim follows from this screen.

## Frozen inputs and actual execution

[PROTOCOL.md](PROTOCOL.md) was fixed before input generation and numerical execution, including the disclosed switch from unavailable SciPy to adaptive Simpson. [inputs.json](inputs.json) contains eight analytical controls, 16 seeded generic cases, 16 structured cases and eight clipping cases. These are researcher-defined ray qualifications, not production scenes or user-demand evidence.

The original script and all failure/diagnostic records remain under [run-01](run-01/execution.json). [REPAIR.md](REPAIR.md) documents the runtime fault and single repair: replace the failing NumPy `leggauss` initialization with standard scalar Legendre/Newton construction of the same GL32/64 rules, and capture worker logs. The input and protocol hashes remained unchanged. The repaired [qualification.py](qualification.py) retains all integration formulas, orders, breakpoints and scientific gates.

| Recorded work | Actual amount |
|---|---:|
| Attempt 1 supervisor wall time; no completed ray | 6.061169 s |
| Four isolated runtime diagnostics; no fixture integration | 8.350454 s total |
| Attempt 2 worker / supervisor wall time | 2.843803 / 3.852255 s |
| Sum of two attempt supervisor times | 9.913424 s |
| Adaptive Simpson / GL32 / GL64 evaluations | 79,369 / 31,616 / 63,232 |
| Pair terms recorded | 3,272 |
| GPU work, installation, renderer or asset download | None |

Supervisor time includes worker execution and output handling; worker time begins after its NumPy import and ends before the final JSON write. Diagnostic and input-generation/inspection work are separate from those attempt totals. Reference timings are qualification costs, not a fair performance comparison or a speedup. Both attempts stayed below the 300-second cap.

## Results, including all failures

[run-02/results.json](run-02/results.json) contains every input, pair term, reference output, analytical comparison and decision. [Execution](run-02/execution.json), [progress](run-02/progress.jsonl) and [rule diagnostics](run-02/quadrature-rules.json) accompany it. The 48 per-case checkpoint files duplicate the corresponding JSON records exactly; those local duplicates are ignored rather than published a second time.

**41/48 cases qualify; 7/48 do not.** Every failed case reports `Adaptive Simpson endpoint resolution exhausted`:

- `control-05-equal-color`
- `structured-03-n4-span1.2`
- `structured-07-n8-span1.2`
- `structured-11-n16-span1.2`
- `structured-12-n16-span3`
- `structured-15-n32-span1.2`
- `clipping-06`

Saved breakpoints expose near-coincident segments as short as 2.775558e-17, for which the recursive quarter points cannot be represented. GL32 and GL64 returned values for all 48, but they do not replace the missing second reference or turn these failures into passes. The seven failures indicate a reference implementation limitation, not a demonstrated failure or success of the proposed bound.

Across comparisons that actually returned values, the largest reference disagreement is 7.671641e-14, largest analytical-control discrepancy is 2.553513e-14, and largest observed Jensen-bound excess is 4.662937e-15. These are below the fixed tolerances; the missing reference results still make the aggregate gate false.

There are 28 non-control cases with N≥4, of which 23 are numerically qualified. At **both** fixed thresholds .001 and .01, exactly **one** qualified case has Jensen bound below the threshold while the global color-range bound exceeds it. The simple pair bound accepts that same one case; Jensen adds no accepted case at either threshold.

| Case | max global bound | max simple bound | max Jensen bound | max observed sorted error, GL64 |
|---|---:|---:|---:|---:|
| Four components, span 3 (`structured-04`) | .632121 | .000446824 | .000444566 | .0000994594 |
| 32 components, span 3 (`structured-16`) | .724947 | .0498518 | .0493778 | .000139032 |
| Thick coincident control (`control-07`) | .999999 | .999999 | .999999 | .636091 |

The first case is a sparse, heavily clipped configuration. It is a limited informational witness, not a demonstrated hard rendering task. The dense example shows substantial conservatism despite a small actual error; the opaque coincident control offers no improvement over the global bound. Do not select only the sparse case for subsequent cost reporting.

## Decision and reproducibility

The numerical qualification remains **incomplete**, so no performance comparison is admitted by these results. The next finite task is specified in [NEXT_EVIDENCE.md](NEXT_EVIDENCE.md): address the identified reference defect under a new explicit budget, retaining T17 as failed/incomplete, before considering any full-cost comparison. No hierarchy, split strategy, tile reuse or new scene is introduced to rescue the bound.

[Independent review](../../../validation/t17-array-review.md) checks saved inputs/results and scope without rerunning quadrature. `audit-manifest.json` records publication identities. Reproduction commands below are documentation, not authority for a third attempt in this task; use fresh output names and retain original evidence:

```sh
python -I -B -X utf8 tracks/tog/tasks/t17-order-inversion-bound/qualification.py
python -I -B -X utf8 tracks/tog/tasks/t17-order-inversion-bound/qualification.py generate --out NEW_INPUT.json
python -I -B -X utf8 tracks/tog/tasks/t17-order-inversion-bound/qualification.py run --input tracks/tog/tasks/t17-order-inversion-bound/inputs.json --out NEW_DIRECTORY
```

The default command only reports a plan. Numerical execution requires the explicit subcommand and an existing NumPy environment. The committed input retains the original generator's SHA; later executions legitimately record the repaired script's separate SHA. Neither engineering validation, the proof, nor this limited witness establishes novelty, useful end-to-end cost, scene-level generalization or submission readiness.
