# T60 — full-window Gaussian screen, failed final readback

The sole scientific child completed six fresh trajectories through t=1 in 416.261165200 seconds. All 36 NPZ files and 30 checkpoints survive. The frozen supervisor nevertheless closes this task as **`failed_result_validation_no_retry`**, with the official ordinary-model verdict **unqualified**. No rerun or historical-file repair occurred.

The cause is a Windows path-string mismatch in final result validation, independently located by read-only replay. Saved numerical output reports all twelve reference checks passing, and a t=1 ordinary projected-Gaussian vorticity error of 0.116193272 against the original .10 gate. Those values are corroborated saved observations, **not an accepted T60 model verdict**. See [results and failure](RESULTS.md), [independent review](../../../validation/t60-full-window-review.md), and [next bounded saved-evidence qualification](DECISION.md).

The original [formulation](FORMULATION.md), [protocol](PROTOCOL.md), [49-input freeze](input-manifest.json), [numerical output](result.json), [failed execution receipt](execution.json), and [publication inventory](audit-manifest.json) preserve exactly what happened. `reference.py`, `measurement.py` and `run_once.py` are the frozen historical programs, including the diagnosed acceptance defect; this directory is not a repaired launcher. Large arrays/logs and diagnostic support remain under ignored `local/`, with identities in the receipts/review.

No new method, fit, source acquisition or TOG contribution is established. Art remains inactive; main and the deleted automation are unchanged. The full research goal remains active.
