# Does different cloth feedback necessarily change the next gas update?

The registered sufficient test returned **inconclusive** on the two native buffers. They came from frames 1 and 2 of one unheated cloth trajectory. The test asks what would happen if either buffer were used with the same incoming gas, step settings and enabled kernels. The gas and fabric at the two recorded times have their own states and clocks. [Protocol](PROTOCOL.md) · [Machine-readable result](RESULTS.json)

| Pending cloth feedback | Frame 1 | Frame 2 |
| --- | ---: | ---: |
| Nonzero projected Z-area words | 192 | 192 |
| Nonzero Y-momentum words | 132 | 0 |
| All other nonzero words | 0 | 0 |
| Full 13-channel grid, uncompressed / zlib level 6 bytes | 53,248 / 622 | 53,248 / 458 |
| Four history channels, uncompressed / zlib level 6 bytes | 16,384 / 201 | 16,384 / 39 |

Across the 8 × 16 × 8 coupling grid, 170 Z-area and 132 Y-momentum words differed. Every projected-area support remained identical. The registered sufficient criterion requires matching momentum words on all three axes, so the Y component prevented certification. The two compressed payload sizes exclude metadata, restore and transfer time. zlib version 1.3.2 was used.

For a source-level interpretation developed **after** seeing this channel pattern, read the [axis audit](../axis-audit/README.md). The prospective decision above stays inconclusive. Both observations concern a single neutral trajectory. Run `python measure.py` with NumPy to reproduce all counts from the [archived native arrays](../evidence/). The script validates the two buffer digests, shape, layout and enabled flags before counting.
