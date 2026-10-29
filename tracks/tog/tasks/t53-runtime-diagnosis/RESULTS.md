# T53 — observed runtime evidence

Two diagnostic children ran under the frozen [scope](SCOPE.md), with no T52 measurement invocation, no T52 integrand or formula evaluation, and no package/environment installation or persistent change. Both input-identity checks passed. The probes did perform NumPy integer arithmetic and attempted four-node quadrature generation/checks; they are not zero numerical work.

| Slot | Existing runtime | Observed final stages | Terminal result | Supervised child seconds |
|---|---|---|---|---|
| A | research Python 3.12.13, NumPy 2.4.6 | NumPy import and integer array checks complete; `leggauss4_begin`, no `leggauss4_ok` | exit 3228369023; diagnostic failed | 5.221102399984375 |
| B | same runtime with conditional DLL registration | **Not invoked**: A had completed NumPy import, so the frozen import-failure condition was false | skipped, not failed/passed | no invocation |
| C | bundled Python 3.12.14, NumPy 2.3.5 | every stage through `leggauss4_ok` and `complete` | exit 0; small diagnostic passed | 0.3228970000054687 |

The supervisor times before receipt writing were 5.236473200027831 seconds for A and 0.3276987000135705 seconds for C. These include preparation/log handling within the supervisor but exclude its own interpreter startup and final receipt writing. They are diagnostic costs, not performance comparisons. Both stderr logs were empty. A stdout was 797 bytes; C stdout was 1,075 bytes. Exact identities, commands, observed Python/NumPy metadata and parsed stage records are in [A](diagnostic-A.json) and [C](diagnostic-C.json); raw logs stay in ignored `local/`.

## What the evidence resolves

A demonstrates that the original selected research runtime can import NumPy and do the stated small integer arithmetic now. Its failure is bounded by the begin/end markers around `leggauss(4)` **and the subsequent four-node assertions**. There is no finer stack trace; do not assert a particular internal LAPACK/BLAS/DLL failure. It has the same numeric exit code as T52, which is consistent with a related runtime problem but does not recover the original T52 phase or establish a common cause.

C provides an existing environment that completed those exact small checks without installation or repair. Interpreter and NumPy versions both differ, and other dependencies were not isolated. No attribution to either version follows. Two four-node generation/check sequences were attempted; one completed. A's actual generated-node count is unknown. Neither orders 128/256/512 nor scientific integrands, derived constants, accuracy gates, full runtime budget or fluid behavior were exercised.

## Preservation and review

The [pre-run identity manifest](input-manifest.json) records four frozen inputs and zero diagnostic children before freeze. Before freezing, a reviewer found that the original supervisor pass predicate ignored input-identity mismatch; root fixed it, the reviewer read back the fix, and no child ran before that correction. The final pass predicate requires unchanged inputs, and a mismatch in any prior receipt prevents further slots. This is a pre-run code correction, not post-result retuning.

The separate [review](../../../validation/t53-runtime-review.md) reads the code, receipts and saved logs without executing the probes again. The reviewer also advised the preparation scope and found the pre-run guard issue, so this is a second-agent readback rather than an independently designed replication. T52 retains its failed scientific invocation and no result; T53 neither replaces it nor supplies substitute decimals. Art remains inactive, main unchanged, automation deleted and the full goal active.
