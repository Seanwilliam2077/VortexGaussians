# T61 — saved evidence qualified; ordinary trajectory fails

The sole read-only qualification accepts T60's saved full-window reference under the [frozen protocol](PROTOCOL.md). All twelve original reference categories, integration checks and meaningful-motion requirement pass. The existing ordinary projected Gaussian trajectory fails the original joint task: at t=1 its relative physical-vorticity error is 0.1161933 and covariance error is 0.1005691, both above 0.10; axial-centroid error 0.0826955 passes.

This is an acceptance of existing observations, not a new simulation or integration. The [original T60 receipt](../t60-full-window-gaussian-screen/execution.json) remains `failed_result_validation_no_retry`. T61 changes only the interpretation of three relative artifact paths, accepting Windows or POSIX separators after containment and identity checks. No old source, output, gate or failure is rewritten.

- [Results and limits](RESULTS.md), [next decision](DECISION.md).
- [Machine-readable qualification](result.json), [supervised receipt](execution.json), [frozen inputs](input-manifest.json).
- [Validator](validate.py), [single-use supervisor](run_once.py), [path contract](path_contract.py), [literal path checks](path-checks.json).
- [Saved-evidence review](../../../validation/t61-saved-output-review.md), [publication inventory](audit-manifest.json).

One standard-library child took 0.966396 seconds; zero scientific invocations or trajectories were added. All 151 repository inputs, historical scientific executable and current bookkeeping executable retained their identities. Arrays were hashed without decoding. The earlier T60 saved-array review remains supporting evidence with its original limitations.

The next question concerns representation capacity versus evolution closure. A failed ordinary trajectory does not establish that every single-Gaussian trajectory must fail, and no new method or TOG contribution follows yet. The task is researcher-defined, with no creator validation or held-out application evidence.
