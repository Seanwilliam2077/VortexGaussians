# Sharing gas after a surface edit has already changed the material

In Blackbody's released Curtain catching scene a thin static box hangs above a lighter. Two ordinary simulations changed one parameter, how long sustained heat must accumulate before the box burns. At the original 0.35 s setting the first lit texels appear in frame 10. Doubling it to 0.70 s delays visible-in-state ignition until frame 18. By frame 36 the arms have 416 and 122 lit texels, respectively. These counts measure the simulated surface. The original camera is evaluated separately.

## When the two gas solves can be shared

The dry, unlit material can accumulate different amounts of heat without supplying any fuel, heat or smoke to the coarse or fine gas. The lighter supplies a common, evolving heat source. While no texel can reach ignition, the bound fixed in the protocol admits the same gas advance in both alternatives. The source has a common static collider, no spotting, no wetting or smoulder, and no flexible cloth. A changing feedback path or an already-lit initial state would require a separate argument.

| Measured event | Native boundary |
| --- | --- |
| First unequal object atlas | Update 2, frame 2 |
| Last update admitted in advance | Update 12, end of frame 8 |
| Updates beginning with different material inside the bound | 10, or 9 after discounting an additional one-step lag |
| Last observed matching gas before native emission | Update 16 |
| First different pressure, velocity, coarse and fine scalar fields | Update 17, frame 10, substep 2, with 13 versus 0 lit texels |
| First differing adaptive update input, zero-based | 54 |
| End of frame 36 | 112 versus 109 native updates |

The full current gas checkpoint matched at each admitted boundary and ember summaries matched at each admitted completed frame. The saved substep observations through frame 12 precede the post-step ember pass and frame-end measurement. Subsequent comparisons use complete-frame endpoints at the same time. Object heat and the ordered radiant feedback used by the next frame are outside the T151 gas checkpoint. The independent continuation experiment expands the recorded state to include them.

Each fresh ordinary process used the original 152 by 176 by 80 coarse grid and 3-fold fine resolution on the same RTX 5070 Laptop GPU. The two instrumented runs took 203.89 and 201.66 seconds including cold preparation. Those costs include independent checkpoint reads and compression. An ordinary implementation can share gas while advancing both atlases, test actual emission, or exploit the ratio between the two catch times. This study measures a dependency window. It does not time these alternatives.

## Verify the record

Run `python -B tracks/tog/tasks/t151-surface-preignition/verify.py` with NumPy to reconstitute the complete material atlases from their XOR deltas, verify hashes and event counts, compare both scene descriptions, replay the guard, and recompute the score. The JSONL records contain native step inputs and field digests. The compressed streams contain the measured material state at every recorded boundary.

[Prospective protocol](PROTOCOL.md) · [Score](evidence/SCORE.json) · [Pinned source hashes](SOURCES.json) · [One-trajectory comparator](../t153-catch-state-transfer/) · [Native fork](../t154-native-surface-fork/)
