# Exact terminal scan from a subset of vortex-field evaluations

A regional material query needs the correct native heating sample after particles have moved and some have died. Picking every seventh input particle gives the wrong law. The solver first sorts by Morton code, moves every particle, culls by temperature, density and domain, then samples every seventh **survivor** before testing whether it is hot. There is a shared cap over all layers.

The terminal operator retains the native tree and director preparation. In Morton order it determines post-update temperature and density exactly; an outward velocity bound gives definite survival or death at the spatial boundary. Ambiguous boundary cases get their native per-particle field evaluated, even if the particle can never heat the requested region. This preserves the running survivor rank. For selected hot carriers, a padded reach test can discard those that cannot affect any eligible recipient. Only the remaining carriers need their exact binary32 velocity and position. Contributions are applied to the native heat array in the original order. The first native threshold crossing is returned. The terminal state is disposable, and ordinary native steps advance the earlier frames. The rank-only ablation shares the survival rule and omits spatial rejection. The all-carriers ablation evaluates every carrier's field.

## Measured effect

Median of paired ratios of caller-visible times per window, after measuring each query in seven balanced repeat positions. Each row counts overlapping queries. The comparison includes branch creation, restoration and result dispatch. [Full public T90 captures](../t90-callable-regional-query/README.md) · [Per-query figures](SCORE.json)

| Asset | Queries | Against regional native | Against rank-only | Queries that reached the requested final scan | Against native when reached |
| --- | ---: | ---: | ---: | ---: | ---: |
| Firewoods | 18 | 0.918 | 1.001 | 11 | 0.621 |
| Dead Tree Trunk | 18 | 0.947 | 0.970 | 10 | 0.458 |

For H=1 the delivered ratios to native were 0.424 and 0.348. At H=8 they were 1.009 and 0.981, respectively. An earlier event stops the ordinary path before this terminal routine can run. On Firewoods the rank-only version accounted for almost all delivered benefit; on the trunk, spatial filtering had a clearer benefit when the terminal scan was actually used (0.732 relative to rank-only for those ten windows). The sums of field calls over reached terminal queries were 867 out of 39,383 total carriers on Firewoods and 378 out of 31,185 on the trunk. These counts concern the terminal update only. Sorting, field preparation, earlier frames, query dispatch and preserving the editor state cost time. The held-out mesh changes geometry and seed but uses the same particle operator and researcher-defined editing question.

## Correctness and reproduction

The native field body is extracted from a SHA-pinned demo by [the builder](build.mjs). The code reuses the native tree, thermal field, world transform and float stores. The guaranteed motion allowance is 4.000002 coordinate units per second plus a binary64 margin on these bounded coordinates. Velocity must be computed whenever membership in the post-step stream is ambiguous. The proof covers the fixed-layer, unit-scale and zero-rotation controls enforced by the runner and operator. Ordinary timestep, fuel, thresholds and RNG stay shared. Input geometry is finite on the published assets. [Frozen protocol](PROTOCOL.md)

From the repository root run `node tracks/tog/tasks/t93-exact-terminal-gas/build.mjs` to generate the native closure plug-in. [T90](../t90-callable-regional-query/README.md) records the complete performance invocation. Run `python tracks/tog/tasks/t93-exact-terminal-gas/score.py` for all per-window ratios and `node tracks/tog/tasks/t93-exact-terminal-gas/check_operator.mjs` for synthetic operator tests. On 120 deterministic fixtures with an externally supplied bounded velocity field, all three operators match a dense advance on every eligible site's stored heat and the chosen witness, including 32 positive, 88 negative and 10 empty windows, 1,876 ambiguous-boundary checks and cap saturation. The native scene replay supplies a separate end-to-end correctness check.

The measured one-step improvement motivates testing whether the first safe answer can be read at intermediate frames and whether the coupled material update itself can be restricted over multiple steps. The limited comparison supplies no claim that sparse evaluation of a tree field is a new technique. [Nearest prior art](../t96-prior-art-review/README.md)
