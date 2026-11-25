# An ordinary full replay with active recipients

The old donor graph caches geometry for every receiver in range. At the pre-click cut, most of those receivers have already burned. We built an ordinary competitor that skips that work while keeping complete material and gas trajectories. This lowers the comparison time on every asset. The slicing pipeline retains an advantage on some edits even against this stronger control.

| Asset | Query windows | Fresh active / geometric | Warm active / geometric | Repair / warm active (range) |
|---|---:|---:|---:|---:|
| Firewoods, development | 4 | 0.949 | 0.888 | 0.881 (0.782–1.007) |
| Dead Tree Trunk, development | 4 | 0.845 | 0.798 | 0.522 (0.462–0.597) |
| Playground, held out before labels | 6 | 0.822 | 0.717 | 0.656 (0.596–0.723) |

Ratios use median delivered edit-to-answer latency per query, then the median across the listed queries. All seven compared methods produced the native first frame and a valid witness or horizon answer on all 784 calls, including warmups (14 windows × 8 waves × 7 methods). Each asset contributes two actual edits. The horizons on the same edit often share an onset. Benchmarks include both fresh click and host delivery on a single native browser/CPU setup. Variance and all first-use and steady-state timings remain in the original measurements. The matched repair/restart comparisons and guards appear in [T100](../t100-material-repair/).

## Cache and validation cost

Cold sites have state zero. States advance monotonically through burning and charred on the tested forward branch. The fresh variant builds a grid of cold sites when a donor is first serviced. It accumulates the exact ordered, individually rounded native deposits, pruning any retired recipients before each donor is applied. The immutable pre-click variant keeps the cold membership at the common ancestor and indexes the first 1,400 current donors. Each sibling branch can only retire recipients or introduce a new donor. It uses a branch-local copy on prune. Reuse validates geometry identity, controls, prefix IDs and exact base cold membership. Fresh or rebuilt rows handle donors first serviced later. Restoring an earlier state discards branch-local rows.

| Asset and order | One-time build (ms) | Base cold sites | Retained donor edges | Typed allocation (bytes) |
|---|---:|---:|---:|---:|
| Firewoods AB / BA | 9.7 / 12.1 | 31,313 / 30,433 | 9 / 89 | 179,143 / 180,103 |
| Dead Tree Trunk AB / BA | 23.0 / 23.4 | 45,532 / 45,501 | 429 / 506 | 265,248 / 266,172 |
| Playground AB / BA | 15.3 / 20.1 | 75,281 / 75,511 | 0 / 110 | 405,715 / 407,035 |

Each cold build appears once per arm in a timed warm-up. All measured calls charge anchor validation. The typed count includes copied state, grid links, donor IDs, recipient IDs and binary64 increments. JavaScript map storage, object headers and temporaries are unmeasured. Per-call private bytes, new rows, copied rows and retired edges appear in the [per-asset summaries](evidence/). A zero-edge initial prefix on Playground AB still requires full ordinary gas, clock, scan, and future donor services.

An independent audit in each of the six arms repeated the actual click, restored it, and compared eight successive full native states with fresh, newly built anchor, and reused anchor. It checked all material values, ordered frontier, gas records and fields, layer clocks, emission cursor and RNG draw position. All comparisons agreed. Immutable anchor rows survived each sibling unchanged. The controls use static geometry, the frozen legacy deposition operator and monotone native material states.

## Reproduce

Build the T93, T94, T95 and T97 plugins as in T98, then run `node build.mjs` from this directory. It generates `local/plugin.js` (SHA-256 `3311852d29e7c1ee2b6f9b615235174ece6550c79b0c889e6e7b3b7f4c1e8474`). T100's joint runner also loads `audit.js`, then stores raw [native measurements](../t100-material-repair/evidence/) and machine receipts. Use `python score.py firewoods`, `python score.py dead-tree` and `python score.py playground` to check all first frames and full-state audit counts and reconstruct the local tables.
