# How stable are the complete editorial-action timings across browser launches?

On the Firewoods case that tries two candidate strokes, dense repair finished sooner than ordinary replay in all four fresh processes for both the primary view and the joint two-view operation. Its median paired delivery ratio was 0.856 and 0.826, respectively. On the Playground case that accepts the light stroke immediately, repair edged ahead in three primary-view blocks (median ratio 0.960), but ordinary won three joint-view blocks (median repair/ordinary ratio 1.048). The primary and joint Playground intervals both cross parity. This experiment reproduces conditions from T111/T113 and measures execution repeatability on a pinned host. It does not add a new edit, seed or scene. [Frozen process schedule](PROTOCOL.md) · [Independent scoring and raw warm samples](SCORE.json)

| Scene and action | Block 1 | Block 2 | Block 3 | Block 4 | Median ratio | Range | Repair faster |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Firewoods, camera 0 | 0.894 | 0.739 | 0.857 | 0.856 | 0.856 | 0.739–0.894 | 4/4 |
| Firewoods, both views | 0.816 | 0.839 | 0.776 | 0.837 | 0.826 | 0.776–0.839 | 4/4 |
| Playground, camera 0 | 0.932 | 1.001 | 0.975 | 0.945 | 0.960 | 0.932–1.001 | 3/4 |
| Playground, both views | 1.072 | 0.991 | 1.121 | 1.023 | 1.048 | 0.991–1.121 | 1/4 |

A table entry is the median of two warm repair calls divided by the median of two warm ordinary calls in **one process and operation**. The four ratios come from four fresh browser launches per scene. Each process also provides two related outputs from the same parent; the two scopes and calls inside one process are correlated. At two even observations the median is their midpoint. Absolute delivery varied substantially. Raw milliseconds below give ordinary / repair per process, in the actual interleaved scene order.

| Process block | Camera 0, full / repair (ms) | Both views, full / repair (ms) |
| --- | ---: | ---: |
| Firewoods 1 | 937.8 / 838.2 | 1,358.7 / 1,108.3 |
| Playground 1 | 476.5 / 443.9 | 626.0 / 671.2 |
| Playground 2 | 417.8 / 418.3 | 691.7 / 685.8 |
| Firewoods 2 | 889.7 / 657.6 | 1,129.2 / 947.9 |
| Firewoods 3 | 867.1 / 743.1 | 1,325.2 / 1,028.2 |
| Playground 3 | 370.4 / 361.2 | 575.4 / 645.3 |
| Playground 4 | 371.1 / 350.8 | 553.0 / 565.8 |
| Firewoods 4 | 696.5 / 596.1 | 995.8 / 833.0 |

Within a block, each method/operation first receives a separately cold index warmup; the warm measurements rotate invocation order twice. Across blocks the initial primary treatment follows ordinary, repair, repair, ordinary and the joint operation offsets that ordering. Each fresh Node worker (24.16.0) launched a separate Chromium-based Edge 149.0.4022.52 instance through Playwright 1.62.1. Browser launch took 0.44–1.88 s for Firewoods and 0.48–1.63 s for Playground. Cold anchor construction ranged from 5.3–12.9 ms and 12.6–26.1 ms, respectively, consuming 179,155 and 405,715 typed bytes. The eight worker times including setup, native continuation and validation sum to 215.68 s. The archived receipts separate these clocks from one complete host-delivered action. [Eight raw capture archives](evidence/)

All 96 calls (64 measured, 32 warmups) matched the original outcome, stroke choices, earliest frame, complete crossing count and mass, and a contributing stable site on each positive crossing frame. Both full native trajectories and the exact common parent marker were verified in every process. Firewoods primary selected F and the secondary camera in its joint operation had no qualifying stroke. Both Playground decisions selected L. A relative improvement on Firewoods reproduces across these launches; that sign does not extend uniformly to the single-attempt Playground action. Four distinct process blocks per scene on one host are the units of this timing result. These observations give no independent samples of artist preferences, edits, machines or production scenes. [Firewoods whole-action reference](../t113-firewoods-editorial-action/README.md) · [Playground whole-action reference](../t111-playground-shot-choice/TIMING_RESULTS.md)

To verify the published set without a browser, use `python score.py` from this directory. The scorer reconstructs all decision witnesses from the native onset traces and view weights and checks every retained call, trial order and source SHA. `node run.mjs --check` tests code composition for both datasets. A fresh `node run.mjs` starts eight serial child workers in a new copy without an existing evidence directory. Each run writes a fresh capture once and stops on any error. All simulation code, geometry setup and view caches use the original T111/T113 preparation.
