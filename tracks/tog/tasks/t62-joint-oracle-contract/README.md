# T62 — a concrete joint-capacity test for one Gaussian

The [derivation](DERIVATION.md) reduces the original joint endpoint requirements to a compact three-parameter geometry problem with amplitude eliminated analytically. The unavoidable covariance error from the saved cross term is **0.0949379333**, below the original .10 gate. Covariance alone therefore does not exclude this Gaussian family.

Moment-matched geometry provides the first ordinary candidate: sr=0.9963219264, sz=1.017825967 and z0=0.3527693649. It meets the two moment requirements in exact arithmetic; its field score and optimal amplitude have **not been evaluated**. The admissible marginal intervals are sr in [0.9555161401,1.035520965], sz in [1.000892212,1.034482565] and z0 in [0.2527693649,0.4527693649]. The widths remain coupled by the covariance disk, so these intervals are not an independent box-feasibility claim.

The [fixed measurement protocol](PROTOCOL.md) first checks that candidate. If it already passes, ordinary search is skipped. Otherwise the limit is 606 S256 geometry evaluations, with the original joint gates, fixed 8x6 scoring and 16x12 confirmation. All parameters stay fixed for S128 sensitivity. One later scientific child is capped at 120 seconds and 512 MiB observed peak working set; no invocation occurred in T62.

The objective uses ordinary separability of the same Gaussian quadrature, with a direct nonnegative residual calculation for confirmation. This is a baseline capacity test, not a new numerical method. A verified witness could establish sampled representability; an unsuccessful local search would remain inconclusive. Offline reference access does not provide causal dynamics.

- [Saved scalar evidence and bounds](evidence.json).
- [Decision and next finite action](DECISION.md).
- [Independent mathematical/protocol readback](../../../validation/t62-joint-oracle-review.md).
- [Publication and preservation inventory](audit-manifest.json).

T62 adds no fit, integral, field evaluation, trajectory or scientific invocation. One standard-library preparation copied existing metadata and evaluated the displayed scalar formulas. T61's qualified failure of the existing projected trajectory and T60's original failed acceptance receipt remain unchanged. TOG contribution, useful causal correction and multi-scene evidence are still outstanding.
