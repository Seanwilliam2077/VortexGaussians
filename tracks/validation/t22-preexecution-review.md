# T22 independent preexecution review

29 October 2026. Reviewer: `volume_screen`. **Static review clear: no blocking discrepancy found.** This review reads source and hashes only; it does not import modules, execute an integrator, sample an integrand, run a numerical probe, or establish successful qualification.

## Reviewed identities

Paths below are relative to `tracks/tog/tasks/t22-prefix-complete-cost/`.

| File | SHA256 |
| --- | --- |
| `PROTOCOL.md` | `fd37b7375bbd876be8d749cda74e9c2cd2ca6fdd67760ceb2f9f62dc3859d2b8` |
| `methods.py` | `17bf8a0e3991de4bb62d542caa633343ad55e5f422529d123224b3660e50dac8` |
| `integrators.py` | `94c6ab6748c42c40c8446ec5af01adf3b7b4ff66a6a45f7f9aba26bc651113af` |
| `benchmark.py` | `02cacdcb353ab6713efd32a79f5ba5ccac30bd117414218a53aeca56a0fecafb` |
| `supervise.py` | `68ddd6038ca16f58dad82311add4a95ca58eddf48762a160cd22dd04d074c930` |

The integrator matches the pinned T19 source. The governing T21 contract and T19 source were also read. Input/reference hashes are checked against fixed literals in the worker; the forthcoming freeze and its before/after checks must cover all stipulated artifacts.

## Mathematical and cost-path checks

- The original continuous color model, clipped optical masses, background attenuation, stable mean order, full-line inversion CDF and inherited simple/Jensen caps are preserved. Signed differences are `c_j - c_i`, with separate nonnegative U/V accumulation and channelwise `min(G, max(U,V))` admission.
- Prefix arms use the mass of all preceding sorted primitives, indexed back to the original component. Signed-only arms do not construct those prefixes. Partial sums only reject; acceptance requires the complete relevant pair traversal and final six `fsum` reductions. Zero-alpha/zero-contrast skips occur consistently before unnecessary CDF work.
- Shared exact and G/2-center branches precede every arm. Direct GL does not pay sorting or pair-alpha work. Rejected tail/pair work remains inside its delivery before full-model GL fallback. Tail acceptance returns its retained color with the original deletion bound.
- The accepted prefix output reuses its already computed Pi array. This avoids duplicate exponentials without introducing a cross-call cache or saved output. Signed-only and tail composition remain unchanged. The declared exp-of-prefix-sum versus transmission-product roundoff distinction is accurate; the common external error gate still applies.
- Unit-rule creation and checks are inside the requesting arm's timed integration. The byte-identical GL ladder retains its original Simpson fallback and diagnostics. Counters distinguish actual pair, CDF, method exponential, integration, rule and fallback work; inherited integrator exponential work can be derived from its recorded PDF-component and integrand evaluations.

## Schedule, isolation, timing and decision checks

- `benchmark.py` gives delivery only seven immutable raw-parameter fields plus epsilon, its own cache and deadline. Fixture IDs and saved T18 GL64 RGB remain in scheduling/validation. Working numeric-array conversion remains inside delivery.
- Stage A has 48 × 2 epsilons × 2 baseline arms = 192 scheduled calls, rotating the first baseline by fixture index. Stage B is reachable only after all 192 pass, then allocates independent fresh per-arm caches. Its 6 passes × 2 epsilons × 48 fixtures × 6 arms = 3456 calls use the frozen rotation. The first Stage B pass is correctly described as initial rule use after qualification, not a cold process.
- All arms share the same delivery timer. Validation, file/hash work, raw snapshot preparation and publication have separate accounting. Enclosing stage/worker windows are explicitly identified as nested totals rather than additive overhead.
- Each returned RGB is checked against the same saved reference with `epsilon + 5e-10`; nonfinite results, invalid metadata, method errors, deadline failures and inaccurate outputs stop scheduling. Each completed attempt is appended and flushed to the journal before proceeding. Successful scientific comparison additionally requires complete A/B counts, no failed/fatal records and unchanged identities.
- Stable joint wins use all six actual shortcut acceptances plus the slowest of five subsequent candidate times against the fastest comparator time. Prefix-increment wins additionally require neither signed-only shortcut ever to accept and stable superiority to both signed-only arms. Controls, N<4 and common paths are excluded. Jensen remains primary; the three-ray .01 cohort only enters reporting/decision. Secondary results cannot alter the primary decision.
- `supervise.py` launches one child through one `subprocess.run`, with the remaining external 300-second budget after initial identity checks. Worker imports, both stages and result serialization lie inside this cap; post-exit log publication and final supervisor accounting are separately disclosed. Both entry points default to plan-only, and no retry is implemented.

## Limits of this clearance

This permits the already authorized single frozen invocation to test the fixed workload. It does not predict that empirical GL/Simpson qualification will pass, certify binary64 error bounds, establish speed or novelty, or revise any sealed T19 failure. A timeout or incomplete/failed stage remains inadmissible for comparative performance conclusions. Post-run review must verify the saved schedule, raw errors, identity checks, paid work and fixed decisions without executing a solver again.
