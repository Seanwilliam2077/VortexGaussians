# T47 mathematical and model-contract review

30 October 2026. **CLEAR within the declared continuous analytical scope; no new method or numerical task is selected.** The reviewer did not participate in T47's initial operator derivation, but participated in preceding T43–T46 analyses/reviews and read the completed T47 drafts. This is collaborative adversarial readback, not blind empirical replication. No external source was reacquired, scientific code executed, numerical example evaluated or model variant developed.

## Operator algebra

The whole-space curl/Biot–Savart convention gives `curl curl (-Delta)^(-1)=P` with the stated transverse Fourier projector. For the volume-preserving constant F, the Fourier argument is `q=F^T k` and the multiplier is F. Subtracting the two compositions gives exactly

```text
P(k)F-FP(q) = [M k/(k^T M k)-k/|k|^2] q^T,
M=F F^T.
```

The bracket is perpendicular to k. At nonzero k it vanishes precisely in an eigendirection of M; otherwise an input mode commutes precisely when its longitudinal scalar `q^T eta_hat(q)` vanishes. Thus already-solenoidal inputs commute for every allowed F. Universal operator commutation requires `M=aI`, and `det F=1` forces a=1 and a proper rotation. Constant-F transport preserves divergence, so the two outputs can both be solenoidal without agreeing. An arbitrary prescribed F need not be the flow map of the reconstructed velocity.

For `eta=grad phi`, the chain rule gives `T_F grad phi=M grad phi_F`. The displayed diagonal deformation and frequency produce the stated nonzero coefficient proportional to `kappa(s^2-s^-2)/2`. Gaussian Fourier transforms are nonzero there, and continuity extends the difference to a frequency neighborhood. The draft correctly confines this example to a derivative-Gaussian continuous source. It does not assert an exact gauge freedom in a finite constant-vector Gaussian dictionary or establish a current-code failure.

## Conjugated projection and cost

The conjugated symbol is `Q_F=I-M k k^T/(k^T M k)`. Its idempotence, transverse range and kernel span(Mk) follow directly. `M^-1 Q_F` is symmetric, establishing the stated weighted orthogonality rather than Euclidean orthogonality. Fourier transformation of `div(M grad psi)=div b` confirms the sign and denominator in `b-M grad psi`. The transported gradient gauge is annihilated.

This is an ordinary transported/weighted Helmholtz projection. The raw Gaussian parameter transformation is exact under the declared determinant-one map, but the projected field generally leaves the finite original Gaussian family and has nonlocal tails. Constant arithmetic per already available Fourier mode does not remove particle-to-field conversion, elliptic inversion, domain/boundary handling or velocity reconstruction. No practical accuracy or timing comparison follows from these identities.

## Local and literature scope

Selected checks were limited to the four recorded model files: `physical_reference/core.py` lines 1–10, 47–86, 141–156 and 219–253; its `PROTOCOL.md` lines 1–30, 80–84 and 120–124; `demo/index.html` lines 2311–2326, 2351–2369 and 2388–2401; and `research/EVIDENCE_STATUS.md` lines 20–22 and 94–111. Their whole-file byte/hash identities match LOCAL_MODEL. These checks support the preexisting raw-source warning, source-only scalar widths retained through P5c stretching, and the browser's target-dependent scalar interaction widths and additional forcing/caps. Other display/layered passages remain the model auditor's scoped findings; no exhaustive repository absence is claimed.

SOURCES reports two pinned primary HTML documents from the two named families, no search query and no failed document route. This review assessed the record and attribution limits without independently reacquiring the papers or auditing their tool-request history. Their stated divergence-free basis and transport/reconstruction capabilities are not claimed to implement the exact conjugated symbol or validate this repository.

No blocker was found. The result concerns a precisely proposed carrier/operation and an ordinary correction, not a newly discovered non-solenoidality defect, physical creation of vorticity, floating-point certificate, novelty finding or TOG contribution.

## Reviewed draft identities

Before sealing, the publication identity check caught a missing-character transcription error in the LOCAL_MODEL hash below. All five draft identities were independently recomputed and the review table corrected; no draft or scientific content changed.

| File | Bytes | SHA256 |
|---|---:|---|
| SCOPE.md | 2418 | `4ef28b0c3ae66fd184d7976cac83be1f90c80a54034837928369484887034420` |
| ANALYSIS.md | 7626 | `11a0b15031185146b7c9aef8e009fdcd482c6ff60d0783542e19dcc23f9ef9f2` |
| LOCAL_MODEL.md | 10190 | `aa6afbfdfd5dc8a3d238a84f9ee3bfe73ab07edb30afc36fde5ff4e4284d667a` |
| SOURCES.md | 2874 | `76f9457ddf0eb0a587530022ba20148be2d0b4a2789137e27cf310fad1051909` |
| README.md | 2580 | `a0ba0f3df3eaaad4855a9630175318e2019858818d94e437c67099dd6efe2a94` |
