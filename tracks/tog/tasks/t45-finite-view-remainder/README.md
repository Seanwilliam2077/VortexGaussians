# T45 — a valid finite bound, without a distinct method advantage

**The specified finite pointwise remainder is proved in exact arithmetic. It is not selected for implementation.** Fifteen retained nonnegative moments and one covariance floor suffice for an O(1)-per-known-group query after O(k) preparation. The proof covers every image-plane position and recovers zero error at the common-footprint view, without dropping a Gaussian tail or a remainder term.

The [scope](SCOPE.md) follows T44's fixed analytical task. The [proof](PROOF.md) derives exact moment cancellation, the third parameter-order integral remainder, explicit spatial derivative envelopes through order six and the full retained-statistic formula. The [comparison](COMPARISON.md) supplies ordinary KL, smoothed Gaussian overlap and generic Taylor methods with the same pointwise contract and covariance information. [Mathematical review](../../../validation/t45-mathematical-review.md) checks these claims and their limits. No numerical evaluation, scientific-array reduction, simulation, rendering, new source, scene, asset or installation was performed.

## Evidence that changes the next action

- The finite remainder question has a positive mathematical answer. The extra record comprises sixteen real scalars plus the reference frame and ordinary merged state. It does not recover discarded children or make grouping, invalidation and rendering free.
- Ordinary U3 plus the same covariance floor already gives a constant-cost pointwise certificate through smoothness. Ordinary overlap can also certify pointwise error after a Gaussian convolution identity; binary groups are already constant cost. An equally informed generic Taylor method obtains the same retained-statistic construction. Comparing only with integrated KL or forced full component scans would overstate the result.
- On T44's existing symmetric thin-depth family, the prescribed global 3D floor tends to zero while the projected Gaussians remain well conditioned. The proposed bound becomes trivial even though an ordinary binary expansion proves small fourth-order error. This is a limitation of the chosen certificate, not an approximation failure or a universal obstruction to better metadata.

Thus T45 provides a checked mathematical tool and a concrete tightness diagnosis, but no distinct mechanism or demonstrated useful cost/accuracy opportunity. The intended practical input class—many useful common-footprint groups under shared affine motion—also remains unqualified. Do not start a benchmark simply to find an example on which this generic formula looks favorable.

## Research consequence

This finite remainder task is complete; no numerical task, floor variant, hierarchy implementation or source batch follows automatically. A further research step must supply a substantive different mechanism or task-supported use of representation transfer and survive the ordinary bounds above. A tighter sufficient bound alone is not evidence of a new graphics method; failure of a sufficient bound is not failure of the approximation. No claim is made that ordinary methods have no remaining bottleneck.

The full submission goal remains active and unachieved. Core-method distinctness, useful task/regime evidence, strong-baseline advantage, multiple scenes and portable reproduction remain outstanding. T42 and every historical result remain sealed. Art/main and the deleted automation remain unchanged. The [manifest](audit-manifest.json) records identities and preservation; bookkeeping checks are not scientific evidence, and unmeasured research time is not a performance result.
