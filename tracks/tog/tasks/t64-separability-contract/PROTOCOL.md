# Next experiment T65 — one fixed separability diagnostic

## Contract and budget before any numerical result

This is a prospective protocol justified by the [derivation](DERIVATION.md). T64 does not implement or execute it. T65 may implement and statically review sources, then freeze this protocol, sources, supervisor, runtime and relevant metadata/inputs before **one** scientific child. There is no pilot, import probe, retry, extra precision, adaptive integration or fifth SVD after an unfavorable result.

Use the existing bundled Python 3.12.14/NumPy 2.3.5, with OMP/OpenBLAS/MKL/NumExpr thread limits one. Complete child budget is **120 seconds**, including import, input hashing/decoding, all checks, four decompositions, outputs and final preservation checks. Observed lifetime peak working set must stay within **512 MiB**, sampled every .25 seconds; require at least **1 GiB** available physical memory at OS-only preflight and launch. Preserve any partial logs on timeout, memory, numerical or acceptance failure. An exclusive invocation marker prevents rerunning. Add the complete child cost to the unchanged prior 1978.636870399816 seconds, including failures; T61's .9663960000034422-second evidence qualification remains separate.

## Inputs and admissible work

Use only T60's saved S256 and S128 snapshot-4 NPZ files and metadata, whose identities are inherited in [evidence](evidence.json), together with T61's qualification and T63's scalar/reference readback. The future child hashes and decodes the two files, loading only q,qr,qz,r,rc,z with allow_pickle=False. Require float64 finite arrays, shapes n×2n / n / 2n, time=1, domain D8, exact saved coordinate definitions and unchanged identities. No historic scientific module is imported. Keep the original piecewise-linear reconstruction; no slope refit or interpolation filter.

Process S256 then S128 with identical procedures. This spectral diagnostic depends on each reference, so each receives its own matrix decomposition; it is not a held-parameter Gaussian sensitivity test, an independent scene or a new flow. No Gaussian fitting or evaluation is included. Exactly two one-dimensional rules, orders 3 and 2 (five nodes), may be constructed. Two reference polynomial integrations (one per reference) and direct Y assembly share the same six node-pair reconstruction loops, totaling **983040** node-cell samples. Four corner checks per cell total **655360** points. Reuse the polynomial statistics formulas from frozen source by explicit reviewed implementation, not execution of the old worker.

Assemble scaled-basis C, exact-formula Gram blocks and 2×2 Cholesky factors, then F=Lr^T C Lz. Independently assemble Y from the original q+qr(r-rc)+qz(z-zc) formula at the six node pairs, with physical square-root weights. Require every Gram block finite positive definite and each Cholesky reconstruction relatively consistent within 1e-12. Check each radial/axial quadrature Gram block against its analytic counterpart within relative Frobenius error 1e-12. No singular-value computation is allowed for these checks.

Call `numpy.linalg.svd(X, full_matrices=False)` exactly once for each of the following matrices, retaining U,s,Vh:

| Case | Basis F | Independent quadrature Y |
|---|---|---|
| S256 | 512×1024 | 768×1024 |
| S128 | 256×512 | 384×512 |

Exactly four SVD invocations are permitted. Neither a second solver nor tuning the decomposition is selected. A failed SVD makes the measurement unqualified; do not switch algorithms. Keep finite, nonnegative, descending singular values; evaluate the tail-energy separability error from each spectrum.

## Fixed qualification checks

All requirements apply to both references and both constructions where relevant. These are empirical consistency checks, not a formal error certificate.

1. Recomputed circulation, centroid, covariance, q-squared, axial impulse and physical-vorticity-squared statistics agree with their original saved metadata with relative tolerance 3e-11 and absolute tolerance 3e-14, as in T63. Cell-corner and node positivity checks pass unchanged.
2. `||F||_F²`, `||Y||_F²` and each spectral sum of squares agree with the independently accumulated polynomial physical-vorticity norm to relative tolerance 1e-10. Report all differences, rather than replacing the reference norm with a fitted denominator.
3. For each decomposition, relative Frobenius residual `||X-U diag(s) Vh||_F / ||X||_F <= 1e-10`. Both `||U^T U-I||_F` and `||Vh Vh^T-I||_F <= 1e-10`. These products are included in cost. Do not use another SVD or an eigensolver to measure norms.
4. Compare the two complete spectra after padding F's with n zeros: Euclidean spectral difference divided by the saved norm's square root <=1e-10. Their separability errors differ by <=1e-10. Y's last n singular values have Euclidean norm divided by the saved norm's square root <=1e-10. Report the residual-based upper expression from the derivation as a computed diagnostic only, not a certified enclosure.
5. Preserve all frozen identities, exact four-decomposition/two-reference/rule/sample counts, output shapes and finite scalar records. Any missing category, output, count or failed numerical/resource check makes the entire result unqualified. Resource failure is not evidence for or against separability.

S256 is primary. Report S128 and absolute error difference; declare sensitivity agreement only when `abs(E256-E128)<=.001`. This tolerance concerns the new diagnostic's numerical-reference sensitivity; it does not change any historical physical gate.

## Decision fixed before measurement

The physical field gate remains **0.10**. With all qualification checks passed, classify:

- `qualified_numerical_barrier_evidence` only when both references' two estimates exceed .10 by more than **1e-8** and the sensitivity condition passes. The 1e-8 margin is a decision separation buffer, not a certified rounding bound. The conclusion is stable numerical evidence consistent with a separability barrier for these saved reconstructions. `formal_exclusion=false` remains mandatory.
- `qualified_no_separability_exclusion` otherwise. Record every value and whether it is below, near, or sensitivity-discordant with the gate. This result does not establish Gaussian feasibility; marginal shape, moment constraints and local-search coverage remain unresolved.
- `unqualified` on any qualification/resource/acceptance failure, retaining cause, partial output and full cost.

No outcome automatically enlarges T63's search, adds mixture components, starts a causal model or qualifies a TOG contribution. Stronger formal exclusion would need an explicit verified error enclosure; it is not obtained by changing this status label.

## Outputs and cost visibility

Save one result JSON, phase/work journal, stdout/stderr and supervisor resource/execution receipt. Save exactly two ignored NPZ audit bundles, one per reference, containing F,Y and their two U/s/Vh factor groups plus scaled Gram blocks/coefficients/coordinates; record array shapes, bytes and file identities. There are two decompositions per reference, with one U/s/Vh triple each. All arrays are outputs of the paid child; review outside it may hash files and inspect metadata/scalars, but numerical recomputation is separate paid work and must not be disguised as free review. No large arrays enter Git.

Log each matrix assembly/decomposition/check and artifact-write interval. Report matrix dimensions, reconstruction points, Gram counts, four SVDs, residual/orthogonality products, output bytes, imports/hash costs and complete child wall time. No GPU or runtime purchase/install is needed. The timing includes diagnostic qualification work and is not a simulation speedup comparison.
