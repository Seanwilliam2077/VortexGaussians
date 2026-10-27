# T11: same observation history, different source response

One frozen analytic qualification passed: two opposite-shear histories produce the same observed density and alpha to floating-point precision, then transport an identical added tracer differently. The construction is deliberately symmetric and known in advance. It qualifies this implementation; it is not automatic discovery, a wind-edit result or a new TOG contribution.

See the [saved figure and compact data](publish-01/README.md), [fixed protocol](PROTOCOL.md), and [independent CPU array review](../../../validation/t11-array-review.md). The complete raw density trajectories remain in the ignored `runs/run-01/` directory, identified by the published summary; they are not required to inspect the compact image results.

| Quantity | One execution |
|---|---:|
| Actual core steps | 120 |
| Maximum paired observation density difference | 5.551115e-16 |
| Maximum paired observation alpha difference | 8.326673e-17 |
| Final right-half source response, positive shear | 0.88580559 |
| Final right-half source response, negative shear | 0.11419441 |
| Maximum final difference of alpha responses | 0.09025790 |
| Whole worker / supervisor seconds | 19.580589 / 20.323509 |

Each image response is its own edited continuation minus its own unedited continuation. The density ratio uses the original source total as denominator. There is no response-amplitude pass threshold, probability or coverage guarantee. The general semi-Lagrangian solver is not mass-conserving, even though this particular construction has negligible measured mass drift.

The next finite task is T12: ordinary constrained search from a public fitted seed on a nonsymmetric synthetic input, with a local wind pulse and a fixed final-image response. It has a separate protocol and derivative qualification. T11 does not establish that a specialized search method is necessary.

The runner defaults to a standard-library-only plan. Explicit execution creates a fresh bounded subprocess and refuses output reuse; the existing run must not be overwritten. Reproduction is a new run and a new cost, not an extension of the saved result.
