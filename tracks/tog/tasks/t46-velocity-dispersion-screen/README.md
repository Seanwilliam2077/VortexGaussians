# T46 — velocity dispersion is lost by an affine merge, but the fix is ordinary

**Result: the declared affine merge loses a positive-semidefinite velocity residual, and retaining it restores ordinary second-moment motion. No new method or matching demo task is selected.** This is a different state-evolution question within T15-A; it does not reopen T45's error-bound implementation.

The [analysis](ANALYSIS.md) proves

```text
R=Cov(U)-Cov(U,X)Cov(X)^(-1)Cov(X,U) >= 0,
kinetic second-moment loss = (M/2) tr R,
free-streaming spatial covariance difference = t^2 R.
```

These identities expose exactly what T43's mass/momentum/affine-state preservation does not retain. Six additional symmetric velocity-moment scalars recover that particular evolution, but this is ordinary joint-moment propagation. It generally does not recover the original density or optical image. Label-based kinetic energy, macroscopic single-velocity energy and thermal energy must remain distinct.

The [four-file local audit](LOCAL_MODEL.md) rules out a tempting false validation: the demo's `affine` path creates temporary field approximation groups while retaining its tracers, and its VPM velocities are derived from a field. Its visual covariance and thermal measure tests are not evidence of this mechanical merge or kinetic loss. This is a scoped model mismatch, not a claim that no related code exists anywhere.

The [source screen](SOURCES.md) used two queries and four attempted primary items: two accessible model/abstract records and two access failures. Existing Gaussian velocity-moment modelling is confirmed; no complete graphics novelty survey or new APIC/PolyPIC theorem was obtained. [Mathematical review](../../../validation/t46-mathematical-review.md) checks the derivation, semantics and cost, with collaborative provenance disclosed.

The [fixed scope](SCOPE.md) is complete. No numerical example, scientific-array reduction, simulation, implementation, new asset or installation occurred. No further source batch or workload is automatically queued to make this ordinary state enrichment appear novel. A later representation-transfer proposal needs a distinct mechanism and a matching force/state/task contract, rather than merely additional second moments. This does not prove ordinary methods solve every such task.

The complete SIGGRAPH/TOG objective remains active and unachieved: a distinct core method, useful task evidence, complete-cost strong-baseline advantage, multiple scenes and portable reproduction are still missing. Historical outcomes remain sealed; art/main and deleted automation remain unchanged. The [manifest](audit-manifest.json) records identities and preservation, not scientific qualification.
