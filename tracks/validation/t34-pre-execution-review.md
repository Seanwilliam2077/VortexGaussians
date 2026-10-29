# T34 independent pre-execution review

30 October 2026. **No unresolved static blocker was found.** This review supports freezing the specified single qualification, not a successful result or a prediction that its budgets suffice. T32 and T33 remain failed. An incomplete T34 closes the stated density-box reference route on these fields and budgets.

## Scope

Read all four new files in `tracks/tog/tasks/t34-box-reference-qualification`: PROTOCOL.md, reference.py, run.py and supervise.py (56,909 bytes / 860 lines). Read the three corresponding T33 Python files for text/AST comparison (42,218 bytes), and reused the already reviewed T33 density-box proof and next-task contract. An initial read used a nonexistent task-directory spelling and returned no source; a filename listing located the correct directory. No other source or asset was acquired.

Inspection used only file reads, hashes, text differences and standard-library AST parsing. No T34/T33 module was imported or executed; no numerical example, pilot, projection, CDF/exp, integration or sampling was evaluated. Only this review was written.

| Reviewed file | SHA256 |
|---|---|
| PROTOCOL.md | `6784f24d9404415b4ec868d94cb54fddc9b56e86257677405233e89980edcc0c` |
| reference.py | `25beec8688039830ca4a2609066b29dc82025929951c1f1e9e57fa7ee384d045` |
| run.py | `f4871cd6ebcf52d2515d097c8c91894a2b0d144d0556ae7bb1e1db12afe6f088` |
| supervise.py | `26b2eef2fcb3413514410d25e6a04e7a36fe5d894517c99143683590a81e9b63` |

The future freeze must include these identities, the review, reused implementation/input identities and governing documents before the sole invocation.

## Bound correctness and numerical implementation

The implementation matches the real-arithmetic threshold proof. Each channel is sorted once by `(color, source_id)`. For split m, the maximum candidate uses prefix lower densities plus suffix upper densities; the minimum reverses that assignment. The weighted sums use the same assignment. Both endpoint splits are included, giving N+1 corners for each extremum. Taking the maximum/minimum over these corners is the exact optimum over the box when its summed lower density is positive. Independent extrema for different channels remain valid channelwise bounds.

Subtracting the retained channel minimum yields nonnegative residual colors; adding it back after the ratio preserves the full linear-fractional optimum in exact arithmetic. This is not the earlier independent residual-numerator relaxation. The original full-field `cmax` still controls tiny-component omission uncertainty, computed before this centering; neither the residual maximum nor retained color range replaces it. Optical absorption weights and retained alpha remain unchanged.

When the summed lower density is zero, the implementation returns the smallest/largest colors on positive-upper support. All-zero upper density fails at the existing density-scale check (and is guarded in the helper); it is not declared vacuum. A positive-lower branch rejects nonpositive corner denominators rather than adding epsilon. Existing empty/equal-color analytic paths remain before sorting. Ties, zero-upper components and a single positive component are consistent with the proof.

Forward and reverse scans use the Neumaier update with nonnegative inputs. Prefix index m sums entries below m; suffix index m sums entries at or above m, with explicit zero endpoints. No total-minus-prefix cancellation or repeated full-prefix summation occurs. Eight scans per channel construct weighted/unweighted lower/upper sums in linear work. Each update performs the counted five floating additions/subtractions, including its corrected stored value. Products, corner combinations and divisions are separately counted. Scans, ratios and final endpoints reject nonfinite/invalid values; clipping to the original retained color range does not create a directed-rounding guarantee.

Sort calls/items, scan calls/items, residual/product arithmetic, two candidate corners per split and both ratio evaluations are charged, including failed work. These named counters plus stage time are not a total-FLOP measurement. Three sorts cost O(N log N) per non-analytic ray; cell scans use O(N) work/storage per channel. No new Gaussian/CDF/exp work is added by the extrema calculation itself.

## Independence and unchanged contract

AST comparison confirms all old top-level reference functions/classes except `enclose` are unchanged, as are its nested diagnostics, output stopping, allocation, global reduction and finish functions. The reviewed cell change replaces only the color-mixture quotient with the new helper; projection, density extrema, optical weights, initialization and subdivision logic retain their original forms.

Ordinary RGB is fixed before reference computation. The new sorting, residuals, scans and extrema never read it. The reference still uses output only for the endpoint accept/disjoint/inconclusive decision and reporting. Tighter intervals can change heap priority values and hence selected leaves, as the protocol explicitly permits; the largest-uncertainty selection rule is unchanged and independent of the desired output.

Worker/supervisor differences from T33 are identity/schema/namespace and cumulative-third-attempt reporting, with T33 failure preservation added. Geometry, pruning, leaf-ledger, alpha, range, endpoint and coverage gates are unchanged, as are the ordinary implementation and all sample rules. Source checks before/after failures, exclusive reservation, failed-stage timing, journals, publication failure handling and supervisor cleanup remain.

The limits remain 180-second computation / 210-second wait plus 10-second termination, 8,192 created cells per ray / 200,000 total, at most 336 rays and 32 MiB raw output. No pilot, retry, replacement sample, cap increase, fourth qualification or automatic alternate reference is authorized. Failure-state limitations remain disclosed: unwrapped/deadline errors may lack a complete local reference ledger.

## Limits of this approval

Exact box extrema are exact only for the real-arithmetic relaxation, not necessarily jointly realizable Gaussian densities along the ray. Binary64 density bounds, residual arithmetic, compensation and clipping are not a formal floating-point enclosure. Static review does not establish numerical error, useful coverage, resource sufficiency or performance. The cumulative history and one-attempt closure remain part of the decision; neither a pass nor a failure establishes a rendering bottleneck, a new method or a TOG contribution.
