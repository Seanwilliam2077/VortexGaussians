# Post-result stopping-contract analysis

Prepared 30 October 2026 from the T32 saved failure and local frozen model. This is elementary verification reasoning, informed by a development result; no new numerical reference or ordinary output has been evaluated. T32 remains failed.

## Sufficient decision

Let an independently constructed interval satisfy L_k <= C_k <= U_k for the true continuous-field color C. Fix the ordinary result g before constructing the reference. For each channel define

    E_k = max(abs(g_k - L_k), abs(g_k - U_k)).

Absolute distance to a fixed scalar attains its maximum over a closed interval at an endpoint. Therefore |g_k-C_k| <= E_k. Accepting all E_k <= epsilon is a sufficient output-accuracy condition. No separate bound on the reference midpoint error is mathematically necessary. The reference interval must be wholly contained in [g_k-epsilon, g_k+epsilon]; intersection or midpoint agreement is insufficient.

If any interval is strictly outside the permitted output interval, the enclosure proves that component wrong: U_k < g_k-epsilon or L_k > g_k+epsilon. If the reference overlaps but is not wholly contained, the current enclosure is inconclusive. It can be refined within its existing budget or stopped as inconclusive. A future implementation must separately identify this outcome from invalid geometry, arithmetic, a failed source check or actual demonstrated inaccuracy.

The real-arithmetic proof assumes true enclosure. The existing reference uses ordinary binary64 erf/exp and floating-point bounds without directed rounding. A future empirical qualification retains the disclosed 1e-10 comparison allowance and cannot promote this proof to a formal floating-point certificate. Repeated comparisons do not constitute independent statistical tests or increase a confidence level.

## Independence and other gates

The ordinary g is computed once before reference work. Projection, all-source optical masses, omission thresholds/charges, density and color bounds, initial breakpoints, heap priority and bisection order must not depend on g. Only the accept/reject decision reads g and a complete, freshly reduced interval. This lets verification stop after sufficient evidence without making the underlying enclosure depend on the desired answer. No calibration of field, tolerance, omission or candidate output is allowed.

All geometry, pruning mass/radiance, alpha, range, leaf-partition and source-identity checks still apply before any ray is qualified. All fixed-subset nontrivial/mixed-color coverage requirements remain. The reference interval's actual width must be saved and must not be called a 0.0001-accurate truth when it is wider. Count setup, failed paths, complete reference work and rule creation, while keeping verification cost distinct from delivered rendering latency.

## What T32's saved ray does and does not show

For frame 90 / front / (132, 73), arithmetic on the saved g, L and U gives endpoint distances approximately [0.000334382, 0.000076616, 0.000010813]. Each is below 0.001, although the red interval's half-width 0.000331721 exceeds T32's separate 0.0001 requirement. This demonstrates why the auxiliary precision requirement could block an already decisive output interval. It does not execute the remaining T32 qualification gates, qualify the rest of the subset, establish error on a new field or retroactively change T32.

Both the adapter author and reference author independently considered this stopping rule after the failed run and recommended it before implementing a more complex envelope. The independent saved-result reviewer checks the saved arithmetic separately. No additional projection, CDF/exp, subdivision or quadrature is used in this analysis.

## Decision and alternatives

Prepare a separately frozen, single ordinary qualification invocation using this direct stopping rule and the identical field, geometric selection and numerical budgets. Keep cumulative attempt history explicit. Change only the auxiliary stopping requirement and the associated reporting/control flow; freeze and review the implementation before any execution. Details and stop rules are in [NEXT_EVIDENCE](NEXT_EVIDENCE.md).

Do not first implement a new density/color envelope. The old quotient bounds ignore shared density between numerator and denominator and can be tightened by an ordinary nonnegative residual or box linear-fractional optimization. Those are mathematical alternatives, not evidence of a new rendering method, and the saved failure does not require their implementation. Failure of the next finite task would require reassessing its specific cause; it would not automatically authorize them, greater budgets or different samples.
