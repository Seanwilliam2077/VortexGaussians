# Exact regional material updates across coupled steps

On a disposable simulation branch, off-region material can be omitted through several frames if the original burning sites that supply graph heat and new gas particles remain predictable. The guard qualified 10 of 12 multi-frame queries on Firewoods and 12 of 12 on Dead Tree Trunk. The two Firewoods fallbacks were the frame-210 A→B cut at four and eight frames, where the cyclic emitter cursor could reach an unknown new burner. All 36 regional query results and first ignition frames matched the full solver. The measurements reuse the original T90/T92 windows on two assets. [Pre-execution protocol](PROTOCOL.md) · [Matched joint experiment](../t94-resumable-gas-query/README.md)

## What can be left out

At the input state there are already at least as many original active burners as the graph service cap and the feed quota. Compute the minimum fuel over that ordered frontier. Repeated native binary32 subtraction at the minimum guarantees that every original burner survives H−1 advances. If the feed cursor cannot wrap past the existing tail in those H−1 rounds, new off-region ignitions cannot change the ordered emission offers. Every graph update continues to use the same prefix of 1,400 old donors. Appended sites are outside both dependency sets over this interval. These are sufficient conditions for this solver.

Compute complete gas dynamics each intermediate frame, including native admission, particle births and random draws. Only the fixed shell needs material flame heating and the following threshold scan. Until the first regional ignition, its eligible recipients remain fixed. Lazily build just the graph edges from the original donor prefix to these recipients after the first negative scan. Subsequent graph applications visit those edges in native donor order, preserving each binary32 write. Return immediately on the first regional ignition. When the guard fails, the implementation pays for the check and runs full ordinary prefixes. A caller that needs to continue displaying the complete branch cannot use this regional state after the query.

## Cost against the matching terminal solver

Each ratio is the median across windows of candidate/control delivered time, using the median of nine interleaved measured calls per method and window. Both sides use the same branch setup, witness target and terminal scan. Shared spatial shell membership and constructing the original live cut precede these calls. The two measured arms overlap in time windows and share the geometry.

| Asset and query set | Number of windows | Sliced prefix / same rank-only terminal | Sliced prefix / same ordinary regional terminal |
| --- | ---: | ---: | ---: |
| Firewoods, all | 18 | 0.973 | 0.952 |
| Firewoods, qualified multi-frame | 10 | 0.922 | 0.819 |
| Dead Tree Trunk, all | 18 | 0.811 | 0.824 |
| Dead Tree Trunk, qualified multi-frame | 12 | 0.389 | 0.459 |

With the rank-only terminal the median delivered times on Firewoods were 19.32 ms with the slice and 19.58 ms for its control. On Dead Tree Trunk they were 18.63 and 23.00 ms. One-frame calls contain no sliced prefixes. Early events can also leave very little intermediate work to omit. On Firewoods the 10 positive windows had a median ratio of 0.996, while its eight negative windows had 0.725. On Dead Tree Trunk the corresponding ratios were 0.811 and 0.215. These gains must also be compared to ordinary cached whole-graph execution; this paired test alone cannot establish novelty or production value. [All timing groups and raw input links](SCORE.json)

## Intermediate agreement and reproduction

Before timing each cut, the audit ran a full native branch and a sliced branch at the longest qualified horizon. On each completed, event-free intermediate step it compared every ordered gas particle's enumerable fields, layer clocks, current RNG draw count, ordered emitter IDs and cursor, plus each initially eligible material site's exact heat, fuel and state. On the first positive step it checked that the returned ID was among the native regional ignitions. Firewoods matched 647,066 particle fields, 30,128 site states and 672 ordered offers over 14 continued steps. Dead Tree Trunk matched 603,806 particle fields, 99,834 site states and 768 offers over 16 steps. A true event ends the partial branch before the native post-scan work, so the audit compares an event there instead of a post-emission state.

[Build script](build.mjs) injects the unchanged native gas and the pinned global admission/offer code into the [regional material operator](slice.js). Run `node build.mjs` in this directory, then use the [joint profiler](../t94-resumable-gas-query/run.mjs) with its T93/T94 plugins, the generated T95 plugin and [the untimed verifier](audit.js). `python score.py` independently checks both saved joint captures and rebuilds the reported counts/ratios. All timing scopes refer to the local browser profile. The transfer geometry is mesh-derived and the editing task is researcher-defined.
