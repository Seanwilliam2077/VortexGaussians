# T20: concrete ordinary accuracy contract, unresolved source mapping

29 October 2026. **The local ordinary integration contract is now explicit; the bounded primary-source acquisition failed.** This task ran no numerical method and prepares no new numerical protocol. T19 remains an incomplete accuracy-failed comparison, without a speed conclusion or retry. The research goal remains active and no TOG contribution is established.

## What this audit adds

[MATHEMATICAL_CONTRACT.md](MATHEMATICAL_CONTRACT.md) fills in the range-construction and work details behind T15's ordinary optical-depth enclosure. For each Gaussian on a finite cell, endpoint densities supply its minimum and endpoints/contained peak supply its maximum. Nonnegative color-weighted density sums divided by positive density bounds give a whole-cell mixture-color interval. Multiplying it by the exact optical mass `T(left)-T(right)` and accumulating all cell intervals yields a sufficient **real-arithmetic** channelwise enclosure. The enclosure center may be accepted when every channel's half-width meets epsilon.

This is an ordinary mathematical operator, not an acquired implementation from the unavailable paper or a new contribution. It supplies a specific alternative to relying only on a quadrature-rule difference. The prior T19 conservation check remains a necessary rejection test; a small conservation residual can hide opposing channel errors.

The contract counts the work of an explicit adaptive implementation. With N positive-weight components and S bisections from one root cell, there are `S+2` distinct endpoints and `2*S+1` cell constructions. Under the specified endpoint-reuse contract, both scalar CDF and density-exponential evaluations number `N*(S+2)`; range arithmetic costs `O(N*(S+1))`, plus queue operations. Stable tail-CDF evaluation, conservative arithmetic, repeated work, failures and lower-memory recomputation may add costs and must be counted when implemented. These are symbolic counts, not measurements or a promise about the input-dependent S.

Three claims remain distinct: a sufficient formula over real numbers, empirical accuracy of an actual binary64 implementation, and a formal floating-point certificate. The last requires bounded special functions, accumulation, subdivision and returned-color rounding. It is not silently imposed as a universal prerequisite for every future empirical study; equally, binary64 code must not be advertised as certified merely because the real-arithmetic formula is valid. No implementation or empirical qualification was performed here.

## Source acquisition and its limit

The [binding budget](../t19-complete-cost/NEXT_EVIDENCE.md) permits only the previously identified Novins/Arvo/Salesin (1992) family. [PROTOCOL.md](PROTOCOL.md) was recorded before access. [SOURCE_LEDGER.json](SOURCE_LEDGER.json) preserves every explicit attempt and separates them from T17's historical failures.

| T20 access | Outcome |
|---|---|
| One [Cornell institutional-record](https://ecommons.cornell.edu/entities/publication/456a7f76-1dd0-4f9f-97eb-4242c19b8606) access | Web transport reported400/timeout; no metadata content or link list acquired. This is not verified origin HTTP400. |
| First full-text attempt at the [previous official download endpoint](https://ecommons.cornell.edu/bitstreams/27eeb67c-3304-4960-9887-808760b46a97/download), web client | Reported429 Too Many Requests; no full text. |
| Second full-text attempt, one standard-library urllib call to the same endpoint | HTTP429; [machine record](source-attempt-02.json), 1.0539355 seconds; no full text. |

The precise download endpoint was recovered from the independent reviewer's retained T17 tool history: it had been clicked from that institutional record. The historical durable T17 note recorded two failed PDF accesses but omitted this exact URL. This recovery did not add a source family or guess a URL. It does not authenticate paper content that was never acquired.

The budget is exhausted: one metadata access, two new full-text attempts, zero search queries, zero extra families, zero acquired PDF bytes and **zero inspected pages**. T17's two earlier429 attempts remain separate historical attempts; the cumulative full-text count is four. No document rendering, installation, third-party source publication, numerical-method execution, integrand sampling, GPU work or new scene occurred.

Because no pages were obtained, this audit makes **no new assertion about that paper's equations, assumptions, algorithms or relationship to the pair bound**. The local mathematical contract is independently derived from the allowed ancestry. Access failure is neither absence-of-prior-art evidence nor proof that an ordinary baseline is unavailable.

## Decision and remaining work

The mathematical part identifies a sufficient ordinary operator and countable work. The required primary-source mapping remains unresolved. Under the pre-result rule, **T20 closes without preparing or executing another numerical protocol**. Do not append a third download attempt, silently change the source budget, rerun T19 under a new label, or infer an architecture/scene queue from this audit.

This result narrows the scientific question: an ordinary real-arithmetic accuracy construction exists; its actual complete cost and the candidate's advantage over accurate ordinary delivery are still unmeasured. The candidate also lacks practical workload and novelty evidence. Those gaps remain part of the active research objective, rather than being replaced by this completed prerequisite. A future step needs its own substantive rationale and finite contract; T20 does not supply a numerical queue.

[Independent review](../../../validation/t20-accuracy-contract-review.md) checks the local proof, cost counts, source ledger and bounded decision without executing methods. [audit-manifest.json](audit-manifest.json) authenticates these artifacts and the unchanged T17–T19 evidence/core/art state. The research branch alone is updated; historical failures, main deployment and the inactive art track are preserved.
