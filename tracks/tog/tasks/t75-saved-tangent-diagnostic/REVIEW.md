# T75 participating analyst review

Root records the technical analyst's actual reports from2026-11-01. The analyst independently derived the tangent mathematics and participated in pre-execution static review. A separate analyst wrote the worker. This is disclosed collaboration, not a blind external review, numerical replication or a new TOG rating.

Before execution, the analyst checked the column convention/order, independent analytic Gram, nested SVD, saved-state extraction, exact coefficient secant and frozen work counts. Root and analyst both identified two missing explicit confirmations: direct additional-geometry norm/Pythagorean decomposition and direct residuals for main-route frozen coefficients on every route. The implementation added them before its5006af2 freeze, without changing physical routes or tolerances. The analyst subsequently read those additions and reported no remaining blocker. Root parsed syntax without imports or numerics and read the full source before the sole run.

After execution, the analyst read result.json, execution.json and source_manifest.json, without numerical execution. The saved results support:

- Weight residual square0.12425663055 versus full-tangent0.01468646941, normalized by the same F norm; geometry removes88.1805346% of the remaining weight residual square. Saved weights match their optimum to a relative field difference1.5932e-14.
- Full rank8 and normalized condition number105.0188, with independent Gram, held-main-coefficient and direct nested-decomposition controls. The observed gap is not produced by silently dropping poorly resolved columns.
- Nonzero projected circulation/impulse rates0.02220473/0.86658327 versus essentially zero direct Euler rates. This rules out describing the unconstrained projection as automatically conservative, but does not measure accumulated drift.
- Full child0.4569979000seconds, observed peak68,526,080bytes and tracked scientific-child subtotal2018.39971949975seconds, with overhead kept separate.

The analyst independently confirmed the post-run nonstationarity argument in ANALYSIS.md. It does not require the saved weights to exactly equal their optimum. The positive successor has the same tangent span, so the nonzero projected target residual supplies an admissible local descent direction. A useful finite step, finite optimized candidate, geometry-box interior claim and full trajectory remain separately unmeasured; the numerical gap has empirical quadrature qualification, not an interval certificate.

The analyst supports the proposed next ordinary-baseline validation provided it changes only continuous optimization of the same Euler target, regenerates each seed from each path's current state, preserves bounds/boundaries, freezes all budgets and stopping rules, retains seed fallback, charges rejected work, seals predictions before reference scoring and reports both time steps and conservation drift. No new score or acceptance claim follows.
