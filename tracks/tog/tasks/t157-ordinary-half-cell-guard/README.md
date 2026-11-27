# A stronger ordinary baseline for the two catch times

Under round-to-nearest-even binary16 storage, the fast catch word alone determines the directly rounded half whenever its magnitude word is at least `0x0800` or is even. Each other finite magnitude has two possible slower words. This classifies 61,440 of the 63,488 finite signed words as unambiguous, including both signed zeros. The other 2,048 finite words each admit a pair of binary32 inputs that map to different slower words. The 2,048 infinity and NaN encodings fall outside the stated contract. [Exhaustive result and endpoint witnesses](SCORE.json) · [Protocol written after observing the curtain exception](PROTOCOL.md)

For each fast storage word, the verifier computes the smallest and largest binary32 inputs that round to it. An even fast word includes both halfway ties. For an odd fast word the extremal binary32 values are the next values inward. The zero cell on each side ends at half the minimum subnormal. For the maximum finite word the outward tie rounds to infinity. Monotonic rounding places every possible slower word between the rounded halves of the two endpoints. The tested singletons all equal half of the fast stored value exactly, preserving the relation required for the next update. The verifier checks both signs, all 63,488 outward midpoint ties and all 126,976 extremal input evaluations. [Executable check](check.py)

| Fast magnitude | Possible slower magnitude(s) | Significance |
| --- | --- | --- |
| `0x0000` | `0x0000` | A nonnegative input that stores to positive zero still stores to positive zero after halving. |
| `0x0001` | `0x0000`, `0x0001` | In units of the smallest subnormal, both 0.75 and 1.25 store to fast word 1. Halving them directly yields different slow words. |
| `0x02fe` | `0x017f` | The fast word at the known curtain exception has only one slower result. |
| `0x03ff` | `0x01ff`, `0x0200` | The largest fast subnormal is ambiguous. |
| `0x0400` | `0x0200` | The first fast normal is unambiguous. The next fast normal is ambiguous. |
| `0x07ff` | `0x03ff`, `0x0400` | This is the last ambiguous positive fast word. |
| `0x0800` and `0x0801` | `0x0400` and `0x0401`, respectively | Both parities have a unique half above the low interval. |

For the known curtain replay, the sharper check admits every successive history through step 12. Independent native confirmation of all four material channels succeeded at the 13 boundaries including initialization. At step 8 exactly one even low nonzero texel extended the original range. The extension was designed after seeing that texel. It has no independent holdout here. T153's original registered history still ends at step 7. [Original score](../t153-catch-state-transfer/SCORE.json) · [Native replay classification](SCORE.json)

An implementation could advance the fast material with the shared gas while testing for any ambiguous texel and reconstruct the slower material at the fork. It must establish the dry, unlit, unsaturated dynamics, matching branch decisions, exact factor-of-two pre-store relation, subnormal handling and backend rounding. A fallback must retain the last good state and common inputs to advance the first ambiguous step on both native materials. Costs include the ambiguity detection and synchronization, retaining enough inputs for fallback, reconstruction or replay, and the two complete futures after the gas diverges. Synchronously advancing two native materials beside the common gas remains an ordinary comparator. T154's retained-packet work can demonstrate actual restart fidelity; its implementation does not by itself outperform this conditional single-material baseline. No execution of either the device-side rounding guard or its fallback was timed here. Other catch ratios, materials and renderers require their own validity checks.

Verify with Python and NumPy from the repository root.

```sh
python -B tracks/tog/tasks/t157-ordinary-half-cell-guard/check.py
```
