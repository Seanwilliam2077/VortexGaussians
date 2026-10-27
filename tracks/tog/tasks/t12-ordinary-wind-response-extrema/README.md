# T12: ordinary wind-response search found no new qualified witness

The new complete-objective derivative qualification passed, but both finite searches retained the public seed. Every evaluated non-seed trial in the recorded search failed the fixed pixel-interval requirement. This is a negative finite-search result, not evidence of unique velocity, zero uncertainty, or a need for a specialized solver.

The [fixed protocol](PROTOCOL.md) defines a conditional problem: known synthetic initial density, one public fitted velocity seed, 20 quantized observation frames, a local wind pulse, and a final-image ROI response. Each evaluation recomputes the complete 20-step history and both 20-step continuations. The two searches independently start from the same seed.

| Result | min search | max search |
|---|---:|---:|
| Full 60-step evaluations | 79 | 79 |
| Reverse calls / returned optimizer steps | 77 / 35 | 77 / 35 |
| Time including final verification and IO | 126.148 s | 111.523 s |
| Final selected witness | original seed | original seed |
| Final response d | 0.010101999875 | 0.010101999875 |
| Non-seed trial records failing pixel intervals | 76 | 76 |
| Smallest recorded maximum alpha interval excess | 5.094567e-6 | 3.304346e-6 |

Those non-seed trial records passed the numerical and initial-velocity priors. They are **not** accepted retrospectively: the unchanged interval tolerance is 1e-10. Their full arrays were not retained; classification of these trials uses their recorded metrics and source-defined acceptance rule. Actual reference, G0 and final arrays were independently audited.

The complete execution used 168 full evaluations, 10,080 solver steps and 156 reverse calls; worker time was 274.901 s. This includes one reference evaluation, nine new G0 evaluations and both searches with paid final checks. The independent saved-array G0 calculation found maximum relative derivative discrepancy 6.5984e-8 against the fixed 1e-4 gate. The final selected states reproduce the seed exactly; their found response span is zero, which is not a global bound or a confidence interval.

Evidence: [independent CPU array/log audit](../../../validation/t12-array-review.md), [pre-run review](../../../validation/t12-pre-run-review.md), [actual figure and compact data](publish-01/README.md), and [root publication review](../../../validation/t12-publication-review.md). Full raw arrays remain under ignored `runs/run-01/`; compact publication is 5.79 MB, preserving the predeclared images without lowering precision to meet the suggested 5 MB target.

The [next finite decision](NEXT_PHASE_I.md) is one ordinary feasibility-only recovery from the already fixed G0 perturbation. No dedicated nullspace method is justified yet. The old two-edit protection-cache route, original thresholds, core and art files remain unchanged.
