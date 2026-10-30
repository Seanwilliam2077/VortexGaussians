# T69 decision — qualify the current-state projector before a rollout

## Selected ordinary comparator

Select [finite-step Euler-target projection](COMPARATOR.md), with exact initial q0 and a current-state-only velocity/contraction evaluator. It avoids installing an approximate initial split and avoids a singular coincident parameter Gram solve. The current-state finite bank/refinement supplies a concrete bounded implementation, rather than an uncharged global optimization oracle.

The zero-weight birth alternative is analytically valid and remains available evidence against broad impossibility claims. It is not selected because it additionally requires a qualified constrained tangent continuation/rank treatment. This is an implementation choice, not evidence that birth performs worse. Only these two formulations were considered; no third family, extra endpoint fit or external source batch was added.

T69 derives an ordinary heat-potential contraction that removes the need for a grid solve in the mathematical predictor. It does not measure that evaluator or establish an advantage over grid methods. Numerical integration, full target norm, direct confirmation and all search costs remain unpaid until a later recorded child. No new method or TOG claim follows.

## Next finite task T70

Prepare, independently review and freeze **one current-state evaluator and two fixed first-step projections**, then invoke at most one scientific child if the complete qualification contract is implementable. One child has at most **120 seconds**, observed **512 MiB** working set and >=1 GiB available physical memory before launch; use the existing bundled Python/NumPy, one thread per numerical library, no installation or scientific pilot. A timeout/failure retains costs and gets no retry under T70.

The allowed numerical inputs are authored scalar states, not future reference arrays:

1. The exact original q0, Gamma0=(3/2)sqrt(2pi), both component geometries (1,1,0), with eta=0. The same density represented with identical components and eta=1/3 is a degeneracy check, not another physical initial condition.
2. One fixed scalar evaluator fixture: Gamma=Gamma0, eta=1/3, component (sr,sz,z) tuples (0.9,1.05,-0.2) and (1.1,0.85,0.4). This researcher-authored state exercises anisotropy and self/cross interactions. It is not a new scene, real demand, held-out task or a reference trajectory. It is used only for evaluator consistency, not fitted or advanced.
3. Two first-step fits from the same exact q0, at **h=1/16 and h=1/32**, using the selected finite algorithm. Neither result initializes the other. No multi-step rollout, endpoint snapshot, T68 tuple or future-reference moment is available to the predictor. The prescribed proposal caps apply independently and all work is paid.

Before any scientific invocation, write the executable numerical contract: fixed heat rules and improper-integral mapping; spatial direct rules/tail controls; initial analytic velocity/derivative and T54 coefficient calibration; full self/cross-term checks; unchanged-state and identical-component controls; signed-target/zero-scale handling; contraction-versus-direct agreement; retained root/weight degeneracies; full target-norm cost; selected-tuple confirmation without refitting; and exact operation/resource counts. Numerical thresholds must be justified against this evaluator's intended downstream accuracy and fixed before data. A pair of agreeing rules alone is not a rigorous tail/error certificate.

Implementation and standard-library/static inspection are permitted before freezing; numerical imports/probes, quadratures, test fits or parameter searches outside the single paid child are not. Do not import historical scientific modules merely to run extra unrecorded controls. No new dataset, scene, library installation or external source batch is needed. If the complete evaluator/qualification cannot be specified within this scope, record the concrete gap and stop that finite task before launching; do not silently omit cross terms, norm costs or controls.

## Interpret the next result correctly

- Qualified contractions and valid first steps would demonstrate a numerically usable ordinary startup, not the original t=1 physical task. A later trajectory requires its own frozen integration, time-sensitivity and original five-time scoring contract.
- A positive projection improvement does not establish the correct true Euler error or that noncoincident components are necessary. Retain the unchanged-state and ordinary tangent information fairly.
- A no-split/stalled result is a result of the bounded algorithm and step sizes, not exclusion of ordinary causal mixtures. Diagnose the actual score/coverage before selecting another action; no automatic search/component escalation.
- Numerical or resource failure leaves the ordinary comparator unqualified, not a new method superior. Preserve all partial work and prior outcomes.

The full research goal remains active and unachieved. T68's endpoint witness stays accepted; T63 stays inconclusive, T60 stays failed and T61 remains separate. Art, main and the deleted automation remain unchanged. Submission still needs a useful mechanism beyond ordinary baselines, temporal/multiscene evidence and complete reproducibility.
