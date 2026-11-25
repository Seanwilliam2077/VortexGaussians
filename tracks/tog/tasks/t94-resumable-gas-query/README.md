# Exact regional tests at every native step

Firewoods and Dead Tree Trunk each have six edited checkpoints and 18 overlapping queries. After full gas-tree preparation, evaluate only the velocity/gradient rows needed to determine reachable sampled hot carriers and the regional ignition scan. Report an early witness immediately. On a negative intermediate scan, retain those field rows, fill the missing rows, execute the original native particle scatter, and complete the regular material and emission updates. Temporary recipient heat is separate. This pays for another round of heat queries on a miss but avoids duplicate writes to physical state and avoids evaluating the same velocity row twice.

The timed function begins with an in-memory cut and returns a Boolean, first frame and valid material ID to a Node host, including branch creation, rollback and result transfer. It uses T90's frozen interface. Full asset/scene preparation and shell construction are one-time costs. T94 returns its diagnostic counts in its result payload; ordinary methods return a smaller payload. Single-host nine-way rotated comparisons include one warm-up plus nine measured calls per query/method.

| Median paired delivered-time ratio to region-targeted ordinary replay | Firewoods | Dead tree |
| --- | ---: | ---: |
| Sweep, spatial culling, all 18 queries | 0.495 | 0.458 |
| Same, H=1 | 0.392 | 0.325 |
| Same, H=4 | 0.769 | 0.693 |
| Same, H=8 | 0.694 | 0.680 |
| Same, early positive multistep windows | 0.445 (7 windows) | 0.438 (8 windows) |
| Same, multistep no | 0.968 (5 windows) | 0.933 (4 windows) |
| Sweep, rank selection alone, all queries | 0.541 | 0.681 |
| T95 sliced material, rank terminal, all queries | 0.639 | 0.618 |

The spatial sweep's absolute median host time was 9.92 ms on Firewoods and 9.28 ms on Dead Tree Trunk. Relative to the earlier T93 spatial terminal-only implementation, its paired medians were 0.948 and 0.924. The ratio to ordinary native incorporates both last-step selection and the new intermediate sweep. These separately computed medians have different denominators. The spatial sweep beat region-targeted ordinary replay on 15/18 and 16/18 windows. Counterexamples include Firewoods B→A cut 210, H=8, a true no (1.137× ordinary), and dead-tree A→B cut 240, H=8 with an ignition at 243 (1.078×). T95 separately reduces material work on qualifying negative sequences. [T95 analysis](../t95-multistep-material-slice/PROTOCOL.md)

All 3,240 timed or warm-up responses agreed with the native reference. An untimed check continued each candidate past the first witness through all eight full steps, producing native frame, gas and material hashes for two selector modes × 12 cuts × 8 frames. The original cut survived each group of queries and every subsequent native reference frame and endpoint still matched. The additional T95 audit checked its eligible projections, offered IDs, RNG and gas fields where the guard applied. The complete profile wall times including these checks were 116.47 s and 202.94 s. These measurements reuse known development and earlier transfer queries at only one seed. The ordinary instrumented simulator still includes diagnostics; the [optimized native control](../t97-ordinary-cached-graph/PROTOCOL.md) addresses that comparison explicitly.

## Reproduce

`python score.py firewoods` and `python score.py dead-tree` need only the standard library, T90 receipts and public reference traces. [Raw Firewoods](evidence/firewoods/CAPTURE.json) · [Firewoods per-window results](evidence/firewoods/SCORE.json) · [Raw dead tree](evidence/dead-tree/CAPTURE.json) · [Dead-tree per-window results](evidence/dead-tree/SCORE.json)

Build T93 and T95 first using their build.mjs scripts, then build T94 with `node build.mjs` in this folder. The native re-run from the repository root uses the following command and a new output directory. The four optional transfer input paths are as documented in [T90](../t90-callable-regional-query/README.md).

```shell
node tracks/tog/tasks/t94-resumable-gas-query/run.mjs --out fresh-profile --methods full,trim,regional,rank-only,t93,sweep-rank,sweep-spatial,slice-rank,slice-regional --plugin tracks/tog/tasks/t93-exact-terminal-gas/local/plugin.js --plugin tracks/tog/tasks/t94-resumable-gas-query/local/plugin.js --plugin tracks/tog/tasks/t95-multistep-material-slice/local/plugin.js --plugin tracks/tog/tasks/t95-multistep-material-slice/audit.js --repeats 9
```

[Protocol](PROTOCOL.md) · [Nine-way comparison amendment](JOINT_PROTOCOL.md) · [Checked source adaptation](build.mjs) · [Dispatch and forced continuation](dispatch.js)
