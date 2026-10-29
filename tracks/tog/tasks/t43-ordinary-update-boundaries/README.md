# T43 — useful exact cases, but the updates are already ordinary

**Decision: do not select either construction for implementation.** Within the existing A/B operations, this finite algebraic task identifies a whole-view exact Gaussian merge and an output-sensitive closed-port correction with a cheap sufficient error bound. Each is obtained directly by ordinary moment matching or constrained projection. These results strengthen the fair comparison and remove specific premises for a new method; they do not establish novelty, measured performance or a TOG contribution.

This follows T42's completed but visually unqualified Firewoods run. It neither modifies that workflow nor treats its admission saturation as the cause of the image ambiguity. [Scope](SCOPE.md) was recorded after preliminary reasoning, not presented as an empirical preregistration. No new numerical run, raw-array reduction, scene, external source acquisition or installation occurred. The previous goal turn was progress; the current turn adds mathematical evidence rather than another functionality test.

## A: when the current view really can be preserved

[The derivation](A_TRANSFER.md) considers positive physical masses, common extinction per mass and complete parallel rays of a fixed orthographic camera. If all merged Gaussians have identical projected means and projected covariances, ordinary three-dimensional moment matching preserves the entire optical-depth image exactly. Depth distributions and image-plane/depth correlations can differ; this is a nonempty class, not only identical Gaussians.

More generally, degree-zero/one/two moments of the projected optical-depth image are just projections of the retained spatial moments. Adding these constraints to a merge already matching those spatial moments adds no independent information. A velocity-position cross moment gives the usual affine closure preserving total linear and angular momentum, without guaranteeing energy, local velocity or subsequent simulation accuracy.

This is a positive exactness boundary beyond T15's counterexample and T39's all-rays uniqueness argument. Its limits matter: it does not give perspective/clipped-ray accuracy, arbitrary colored emission accuracy, approximate-footprint guarantees or a new transfer operator. The ordinary method uses the very same O(k) moment aggregation and fixed-size solve. Keeping separate physical/render states remains a fair alternative.

## B: measure flow change, and allow a cheap feasible correction

[The port-deletion derivation](B_PRESSURE.md) fixes a compatible closed weighted fluid graph and predicted edge fluxes. For its old projection q0, let g be the Riesz response of the deleted edge's flux coordinate in the weighted cycle space, with k=||g||². When k>0, the exact update is

```text
q* = q0 - (q0_e/k) g,
||q*-q0||_R = |q0_e|/sqrt(k).
```

A single bridge has k=0 and already carries zero circulation. Two chamber ports allow a nonzero exchange flow f. Closing one removes that mode, with exact weighted change |f| sqrt(H), where H includes both port resistances and both chamber effective resistances. This makes the operation nontrivial, but pressure conditioning alone still does not determine output difficulty.

Crucially, an ordinary comparator need not always compute the exact global response. Any known unit cycle z through the edge yields a feasible closed, divergence-free flow q_hat=q0-q0_e z. In the two-port case it has the real-arithmetic sufficient bound

```text
||q_hat-q*||_R <= |q0_e| sqrt(z^T R z - r1 - r2).
```

This pays path acquisition/update and bound evaluation, without a new pressure solve. It may be too loose for a useful tolerance; no measured advantage is asserted. Exact response setup instead pays old-operator solves and full-field response work, which ordinary Schur/rank-one methods can also cache. These are concrete ordinary options that a future comparison must not disable. The derivation distinguishes projection-objective increase from the decrease in the flow's own squared norm, and identifies near-bridge cancellation as a numerical concern, not a new topology rule.

## Duplicate check and review

The contemplated low-count Poisson correction under C was already derived, compared with a cheaper ordinary alternative and screened in [T30](../t30-two-event-output-screen/README.md). This turn found that record before generating another derivation or experiment. Its original outcome remains closed; the duplicate is not counted as a new mechanism or numerical evidence. T37/T40 and all earlier outcomes are also unchanged.

[Adversarial mathematical review](../../../validation/t43-mathematical-review.md) checks the normalizations, optical scope, projection geometry, objective constants, cheap-cycle bound and ordinary comparison. Review is not an independent experiment, literature-priority search or floating-point certification. The [manifest](audit-manifest.json) binds the resulting documents and preserved history. Research reasoning and review time were not measured; zero scientific execution is not a runtime advantage.

## Consequence for the research goal

A method claim based only on extra view moments or the cost of recomputing pressure after port closure would now ignore explicit ordinary capabilities. Those premises are rejected for development here. This is not a proof that approximate compression or topology editing has no remaining bottleneck, nor that the derived bound is tight on practical inputs.

No next numerical task is selected. A useful next proposal needs a specific additional representation/update, its complete-cost comparison against these ordinary options, and evidence capable of changing a decision on an assessable operation. Merely choosing a case where a sufficient bound is loose, a pressure matrix is ill-conditioned, or a demo is unclear does not supply that proposal. The full submission objective remains active and unachieved: core method, strong-baseline advantage, distinct useful tasks, multi-scene evidence and a portable public reproduction are still missing. Art/main remain unchanged and the deleted automation is not recreated.
