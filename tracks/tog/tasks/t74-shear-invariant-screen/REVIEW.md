# T74 source and saved-record review

Root records the technical analyst's post-run report, 2026-11-01. The analyst previously independently checked and wrote the mechanism derivation, and therefore discloses participation. This is not a blind external review, a numerical rerun, a formal TOG score or a second independent experimental replication.

Read-only scope: DERIVATION.md, verify.py, run_once.py, result.json, execution.json and source_manifest.json. No file changes or scientific invocation during this review. A separate analyst implemented the worker; Root read the complete worker and derivation before the sole execution.

The analyst reports no blocking discrepancy:

- The worker uses the physical 2πr³ weight and directly sums nonnegative residual squares. High-rule relative residual squares are 0.12614524827136933 and 0.06273628669468864. The 50.266627% improvement refers to the old residual square, whereas 32/441 uses already captured translation energy as denominator.
- Conditional normalization and central-moment differentiation are explicitly checked. All 33 saved checks agree with the scalar results. The maximum adjacent-rule energy-ratio discrepancy is 2.7933e-13.
- The full child interval is 0.2694689999 seconds. The extra supervisor interval is 0.0909399000 seconds and is not added a second time to the scientific-child subtotal. The worker's smaller internal interval is not substituted for full cost. Observed peak working set is 39,514,112 bytes.

Root independently read the saved JSON, source and mathematical derivation. Seven source/input hashes were unchanged after execution according to the supervisor. The numerical check supports the constants and illustrative energy deficits; it is not the proof of the general-shift inequality. Finite-domain quadrature consistency supplies no formal tail certificate, trajectory qualification or method advantage. Earlier research outcomes and the historical2/6 assessment are unchanged.
