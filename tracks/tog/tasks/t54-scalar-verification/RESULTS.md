# T54 — constant consistency passes; ordinary baseline quantified

One scientific child exited 0 with [result status consistent](result.json). The unchanged T52 evaluator completed all 128/256/512-node rules (896 shared nodes). All nine moment-to-closed and six adjacent-rule relative checks are below the original 1e-9 threshold; the largest saved difference is 8.659435934191642e-15. Positive finite moments and the required variance/residual assertions passed. This is floating-point numerical consistency of the derived constants, not a formal certificate of all rounding or quadrature error.

## Saved scientific values

The closed moments are J0=1.661675485223921, J1=0.4824008363721784 and J2=0.1602620299206584. The complete three-order table and differences are retained in result.json; no new evaluator was used to obtain this report.

| Quantity | Closed expression evaluated by frozen code | 512-node result |
|---|---:|---:|
| beta_best/g0 | 0.29030989544096925 | 0.290309895440969 |
| beta_center/g0 | 0.6666666666666666 | 0.6666666666666666 |
| E_best | 0.3551693233816372 | 0.3551693233816361 |
| E_center | 1.2628476537634736 | 1.2628476537634752 |
| E_zero derivative reference | 1 | 1 |
| E_best/E_center | 0.2812447901559462 | 0.281244790155945 |
| Fractional residual reduction vs center | 0.7187552098440537 | 0.718755209844055 |
| kappa_N | 0.329396116405985 | 0.3293961164059837 |
| kappa_best | 0.11699139578845269 | 0.11699139578845187 |
| kappa_center | 0.4159771127620982 | 0.4159771127620971 |

E measures the L2 norm of the **initial physical vorticity-derivative residual divided by the exact derivative norm**, for one initially isotropic curl-Gaussian. The ordinary full-parameter fit reduces that residual by approximately 71.9% relative to the center update; its remaining E_best is approximately 0.3552. Neither number is a relative flow-state error. The zero update is only a metric anchor. All 12 existing tangent parameters were allowed in the analytical minimization; the isolated symmetry reduces its physical optimizer to one translation coefficient.

The kappas multiply initial derivative rates by t_c, the initial center-speed traversal time of one Gaussian width. They do not give the error after evolving for t_c. No time integration or visual-quality test took place. The reported negligible real-arithmetic tail/series bounds do not bound library floating-point error; the observed agreement and analytic derivation remain separate evidence.

## Execution and cumulative costs

| Execution | Outcome | Supervised child seconds | Supervisor seconds before receipt writing |
|---|---|---:|---:|
| T52 first scientific attempt | failed, no result | 4.807828599936329 | 4.814353100024164 |
| T53 diagnostic A | failed in four-node call/check interval | 5.221102399984375 | 5.236473200027831 |
| T53 diagnostic C | small checks passed | 0.3228970000054687 | 0.3276987000135705 |
| T54 second scientific attempt | consistent | 0.5475459999870509 | 0.553717799950391 |

T53 B was ineligible and never ran. The scientific attempt count is two across T52/T54, with one failed and one successful; diagnostics are two separately counted executions. T54 introduced no warmup, extra evaluator, fallback or new diagnostic. These execution costs exclude human/model reasoning, preparation bookkeeping, supervisor interpreter startup and final receipt writing; they are not a complete project-cost estimate or fluid-method performance result.

The new child reports Python 3.12.14, NumPy 2.3.5 and Windows 11. Per-order node-generation/integration seconds are respectively: 128 nodes, .005903699900954962/.00012430001515895128; 256, .008937699953094125/.000152900000102818; 512, .03961219999473542/.00031649996526539326. Its own pre-result-write elapsed time is .4566193000646308 seconds; the supervisor covers the larger complete child lifetime. These are one-shot instrumentation values, not a speed benchmark.

All seven frozen input identities and the executable identity are unchanged. The result records the exact 5,071-byte original scientific script. Stdout is 616 bytes; stderr is empty. [execution.json](execution.json) preserves the command, full observed cost, output/log identities and qualification checks. Its scientific pass does not change T52's failed receipt or create T52 result.json. The inherited `t52-...` result schema is intentional byte-identical evaluator provenance.

The [second-agent review](../../../validation/t54-scalar-review.md) reads saved values/gates/identities and limits without another scientific evaluation. No fluid trajectory, candidate method, new source or asset, installation, rendering or persistent runtime repair occurred. Full goal active; art inactive, main unchanged and automation deleted.
