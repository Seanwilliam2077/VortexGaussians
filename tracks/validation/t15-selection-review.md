# T15 selection review

28 October 2026. Read-only review of the four files below; no new source search, source-code execution, simulation, solver implementation, asset preparation or GPU run. The reviewer authored candidate B, so this is a cross-candidate logic review, not an independent replication of B's source inspection. A and C's literature statements were assessed as written; the underlying papers were not independently reread in this review.

## Files actually checked

| File | SHA256 |
|---|---|
| `tracks/tog/tasks/t15-core-hypothesis-selection/PROTOCOL.md` | `9ab3df7de74e9b5bdb5adb3ee4869f1b7b31b94bba23d5ba0e903ae2d3acef53` |
| `tracks/tog/tasks/t15-core-hypothesis-selection/A_TRANSFER.md` | `f470f356918b70ef2f025cc515a1dbf1860992bd7ba09235fbd189a578527daf` |
| `tracks/tog/tasks/t15-core-hypothesis-selection/B_PRESSURE.md` | `e8df5bf42b3c07f97489659cc6f43089a3ee91fa7bced4cef6107f7cec0cccc4` |
| `tracks/tog/tasks/t15-core-hypothesis-selection/C_VOLUME.md` | `e89c9c0a6c480e391cb316750e9fb58bbdbcd32630c796786e276a07891e4578` |

## Mathematical and decision assessment

No blocking algebraic error was found in the stated reductions.

- **A:** Integrating the displaced isotropic Gaussians over the complete central line gives the stated exponential factor. Integrating the moment-matched anisotropic Gaussian gives the stated reciprocal square-root factor. `log(1+t) < t` establishes the strict ratio inequality. Matching the first two density moments also matches the integral of `x cross (A x + b)`. Thus the example invalidates an implication from mechanical moment preservation to exact optical preservation. It does not show that an approximate optical-conservative transfer is useless or impossible. The distinction between a physical covariance and an interpolation-stencil tensor is necessary. The memo preserves these limits.
- **B:** For the specified positive-conductance graph operator, component constants, componentwise compatibility and anchored components are correctly distinguished. Near-disconnection can affect small positive eigenvalues without changing exact nullity. The low-rank edge-update observation is limited to fixed unknowns; changing cut-cell unknowns is explicitly excluded from that shortcut. The missing incremental-update mechanism is not proof that current valid solvers have no setup or convergence bottleneck.
- **C:** The weighted color enclosure follows from the positive measure `-dT`. The two-Gaussian log-ratio is quadratic, making its endpoint/stationary-point range calculation valid under the stated positive Gaussian and constant-color assumptions. Independent emission is correctly excluded from the bounded `j/sigma` argument. Real-arithmetic enclosures do not establish a floating-point certificate, which the memo states. The analysis shows that the currently proposed primitive is an ordinary integration enclosure; it does not establish the fastest practical implementation, useful tolerance/cost ranges, or absence of a bottleneck.

All three no-go decisions are consistent with the **predeclared selection rule**: no present card specifies the required distinct mechanism. No card is selected for method implementation or numerical qualification by T15. This is a selection result, not an experimental result showing that ordinary methods meet every useful budget.

Two framing restrictions matter for the consolidated decision:

1. “No distinguishing method yet” must not become “ordinary-method performance measurement cannot be informative.” The selection rule asks for a mechanism before selecting method development; it cannot establish that a measured bottleneck does not exist. Neither two-source omission nor symbolic reduction can make that performance claim.
2. Fair baselines receive the same input information, physical model and readily available analytical primitives. This does not require handing a future genuinely new algorithm to the baseline and then declaring the algorithm non-novel. The elementary range formula in C is not a distinct method here, but that rationale must not become a blanket dismissal of every future tighter bound.

The three-card selection batch is complete and should stop. Continuing authorization is still effective: failing these cards does not logically require permanent termination of the whole research program, an unsolicited pause, or a new permission request. It also does not authorize inventing a fourth card, reopening closed numerical routes, or beginning implementations just to keep the queue occupied.

## One concrete remaining evidence gap

Within **the already defined C operation**, the actual ordinary integration contract and complete cost are unestablished. The memo explicitly says that the implementation bodies of the already identified author repository were not obtained. Consequently, it cannot yet say which emission model, overlap handling, sampling/termination rule and error guarantee the accessible implementation actually executes. This is a specific source-inspection gap, not missing user assets or proof of an unmet need.

A bounded ordinary-baseline task is justified **first as contract preparation**, not as an automatic timing run. Its value is to determine whether an executable, comparable ordinary reference exists and whether a later measurement would answer a question not already settled by the published two-Gaussian mismatch.

### Proposed entry, budget and termination gates

This is a recommendation for a separately recorded next task; nothing below was executed in T15.

- **Scope and entry:** stay with C's declared positive Gaussian extinction, constant per-component bounded color, opaque endpoint, and emission–absorption integral. Use the already named official `facebookresearch/volumetric_primitives` repository. Pin an accessible revision before reading implementation. Inspect its relevant integrator entry points and directly required helpers; cap the pass at six code files plus build metadata/README, one repository and one bounded reading session. No new literature-search batch, dependency installation, modified renderer, benchmark scene production or GPU run is required for this gate.
- **Source deliverable:** a code-linked input/output contract and operation-cost ledger: active Gaussian traversal, analytic transmittance evaluations, color/emission sampling, termination/error rule, opaque-depth handling, dependencies, and which setup/update work must be counted. Explicitly mark unknowns. If the source executes different optical semantics, document that mismatch instead of treating its image or time as a same-problem baseline.
- **Proceed-to-measurement gate:** only prepare a later fixed-budget ordinary measurement if an executable matching reference or a justified standard-reference route is identified, the exact observable is specified, and there is an assessable accuracy/cost question. Declare the physical input, overlap/conditioning range, error metric, reference accuracy check, first-use and repeated-use costs, and resource cap before any run. Certification and empirical accuracy must remain separate. “Reproduce overlap error in two nearby Gaussians” fails this gate because it repeats known evidence.
- **Stop gate:** stop after the source pass if implementation access remains unresolved, semantics cannot be aligned, required dependencies make this finite task impractical, or no specific measurement question survives. Record the reason; do not substitute a weaker renderer, silently implement a new method, or expand to another repository/candidate to force a result. The same applies if an eventual ordinary measurement already meets its declared quality/cost target.
- **Interpretation gate:** an expensive ordinary computation would establish a measured cost under that contract only. It would not establish creator value, a new mechanism, an algorithmic advantage or TOG readiness. A repeatable bottleneck could motivate a later mechanism proposal; it cannot automatically promote the rejected card to a contribution.

This action is feasible for the researcher without asking the user to invent a task or supply a personal scene. Its expected information gain is modest but concrete: replacing an uninspected implementation assumption with a comparable contract, or closing that access route cheaply. Do not represent it as likely to produce a paper core, and do not run it merely because continued automation is available.
