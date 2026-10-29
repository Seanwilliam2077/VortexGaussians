# T26 — actual SH color and tile ordering

29 October 2026. Static inspection by pressure_screen of exactly three acquired files, **335 unique lines**. Dependency: `chinmay0301ucsd/slang-gaussian-rasterization`, commit **`5eca1185550c35e3236c511c311aee3eb9129169`**, as pinned in T25. Paths below are relative to `slang_gaussian_rasterization/`. No network, import, compilation, numerical evaluation or asset inspection; previous evidence is unchanged.

## Color source facts

Both color functions use `normalize(g_xyz_ws-cam_pos)`: the world-space direction **from camera to Gaussian center**, with no local zero-length guard ([spherical_harmonics.slang, 96–102 and 140–146](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/spherical_harmonics.slang#L96)). This closes the previously unread direction convention. T25's vertex stage evaluates this once per primitive/view, not at each ray sample.

The coefficient reader loads RGB vectors indexed 0–15, with nested `active_sh>0`, `>1`, `>2` tests ([62–90](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/spherical_harmonics.slang#L62)). The evaluator supports the displayed real SH polynomial through degree three; values above three do not introduce additional bands here. Constants C0, C1, C2 and C3 are explicit at lines 15–32. With direction `(x,y,z)`, the basis factors in coefficient order are:

| Indices | Factors before the corresponding stored constants |
| --- | --- |
| 0 | 1, multiplied by C0 |
| 1–3 | -y, z, -x, multiplied by C1 |
| 4–8 | xy, yz, 2z²-x²-y², xz, x²-y², multiplied by C2[0–4] |
| 9–15 | y(3x²-y²), xyz, y(4z²-x²-y²), z(2z²-3x²-3y²), x(4z²-x²-y²), z(x²-y²), x(x²-3y²), multiplied by C3[0–6] |

The signs in C2/C3 are part of the convention, not extra positive normalizers. Both branches evaluate the same polynomial and add **0.5**. The ordinary branch returns `max(rgb,0)` ([100–130](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/spherical_harmonics.slang#L100)); the softplus branch returns `log(1+exp(10*rgb))/10` ([134–175](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/spherical_harmonics.slang#L134)). Neither clamps to one. Over finite real inputs these give nonnegative colors (strictly positive for softplus), with no coefficient-independent upper bound. The displayed softplus has no stable large-argument branch; overflow/underflow behavior is a numerical risk, not an observed failure. These files apply no color-space transfer function and do not establish whether training targets represent linear radiance.

## Keys and sort call

For each primitive/tile overlap, [tile_shader.slang, 19–63](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/tile_shader.slang#L19) writes

```
key = uint64(tile_y*grid_width+tile_x) << 32
key |= reinterpret<int32_t>(xyz_vs.z)
value = original Gaussian index
```

Despite the local variable name `ndc_xyz`, T25 traced this z to **center view-space depth**. It is not the Gaussian's projected maximum-density parameter along a pixel ray. Each overlap of one primitive receives the same depth bits. Buffer locations use the preceding primitive's cumulative offset, but original index is only the paired value, not a secondary key. Tile-range extraction subsequently reads the upper 32 bits and records boundaries ([67–101](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/slang/tile_shader.slang#L67)).

The [CUDA wrapper, 15–48](https://github.com/chinmay0301ucsd/slang-gaussian-rasterization/blob/5eca1185550c35e3236c511c311aee3eb9129169/slang_gaussian_rasterization/internal/sort_by_keys/sort_by_keys.cu#L15) requires CUDA int64 keys and int32 values, calls `cub::DeviceRadixSort::SortPairs` once for temporary-storage sizing, and again for execution with bit arguments `0,32+highest_tile_id_msb`. It does not locally compare depths or break equal-key ties. External CUB implementation/version and its stability guarantee were not inspected; the call name and input placement alone do not prove stable ties or cross-device reproducibility.

**Conditional interpretation:** ordinary ascending radix behavior, enough selected tile bits, valid tile IDs and positive finite IEEE float depths produce tile grouping and increasing center depth within each tile. Positive finite float bit patterns are monotone with depth; T25's center cutoff removes depths <=0.2 on the ordinary valid-input path. This is not a validity proof for NaNs, negative/overflowed tile IDs, arbitrary signed 64-bit keys or incorrectly supplied bit counts. The wrapper does not independently establish those conditions. Equal depth keys contain no explicit deterministic index tiebreaker.

## Relation to the existing bound

The [T21 coupling](../t21-winner-prefix-bound/DERIVATION.md) can be relabeled by **any fixed total permutation**: its winner identity and prefix inequality do not require ascending ray means. Applying it to an observed depth/tie order would require consistent pair orientation and prefixes. This mathematical observation does not alter T21/T22's frozen stable-mean implementation, inputs or measured results. Unknown ties matter for reproducibility and for which permutation's bound is evaluated, not for validity after a permutation is specified.

Likewise, finite colors above one do not invalidate the real proof when actual color differences and extrema are used. They do prevent silently substituting the historical [0,1] fixture range or importing its empirical thresholds as demonstrated workload behavior. Floating finiteness and accuracy still need qualification.

Color/order closure does not remove [T25's approximation chain](../t25-volume-kernel-contract/KERNEL_MODEL.md): full-line masses versus finite domains, guards, alpha caps, culling and blend termination remain distinct from T21's same-mass exact-overlap versus whole-primitive comparison. Its bound is not a total certificate for the released renderer. No trained carrier, performance bottleneck or novelty is established here.

## Raw identities

| Local acquired file | Inspected lines | Bytes | SHA256 |
| --- | ---: | ---: | --- |
| `code/5-spherical_harmonics.slang` | 1–175 | 6973 | `c06f4909bcd728181c66234eca328ee4fb46227532cf6d3ddf1a43a785f480f4` |
| `code/6-tile_shader.slang` | 1–101 | 3417 | `f9ca5b69d4c3cea6dfd5a048c7f96a6dba3f9fa3a5adc986d1fa045d49f172ed` |
| `code/8-sort_by_keys.cu` | 1–59 | 1962 | `0433a3871af7a9729793df44c6b935a5d1e22d7fbc2673877e2b09d9dcde0a6c` |

The first two source headers state Google 2024 and Apache-2.0; the inspected CUDA file has no license header. These are source observations, not asset permissions or repository-wide legal conclusions.
