# Exact parity-dependent graph heat updates on native binary32 values

When the same ordered, nonnegative donor increments are applied to a cold material site, the full sequence of native binary32 stores can sometimes be replaced by a single integer shift of the input's binary32 word. The shift depends on the starting exponent and low-bit parity. [Derivation and domain](DERIVATION.md) · [Frozen protocol](PROTOCOL.md) · [Operator](operator.mjs)

The identity passed 45,162 deterministic synthetic cases across all normal binary32 exponents, including binade crossings, midpoint additions susceptible to double rounding, zero/subnormal inputs, overflow and random donor sequences. Of these, 25,910 used the fast lookup, 19,252 took the serial fallback, and 29,980 had distinct recorded shifts for opposite initial parities. A naive single final rounding disagreed with the serial result in 18,033 cases. These cases test arithmetic edge conditions rather than their frequency in the simulator.

## Archived native graph phases

We reconstructed the serviced prefix of 1,400 donors at each of the six T86 cuts and each of the six T92 cuts from the original geometry. There were no retirements on any selected frame. The post-step frontier order therefore retains the ordered donors from that frame’s graph phase. For each still-cold, fuel-positive recipient receiving at least two positive graph increments, we used monotonicity of serial native stores to find the complete interval of possible incoming binary32 values that produce its recorded post-graph heat. The serial inverse had an admissible preimage in every case. An interval can be wider than the set of states reachable through the preceding flame and decay phases.

| Across the six cuts on each asset | Firewoods | Dead Tree Trunk |
| --- | ---: | ---: |
| Cold, fuel-positive receiver–cut pairs | 178,479 | 249,858 |
| Receive zero / exactly one graph increment | 178,293 / 133 | 249,701 / 87 |
| Receive at least two positive increments | 53 | 70 |
| Unique native input among these | 53 | 68 |
| Exact lookup covers every admissible native input | 53 | 68 |
| Unique inputs where ordinary pre-sum changes the stored float | 8 | 16 |
| Potential ignition-threshold disagreements at graph output | 0 | 0 |
| Potential threshold disagreements after one more decay with zero flame heating | 0 | 0 |

The last two rows bound what single rounding alone could change in those specific tests. A native ignition scan can receive more gas heat before decaying; the experiment did not change a native ignition event or evaluate rendered fire. The two transfer cases with multiple admissible input words take the serial path under the conservative all-input criterion. In one of them scalar pre-summing necessarily matches the native result, in the other its effect depends on the unknown incoming word as bracketed by the inverse. See [all counts and frontier identities](RESULTS.json) for the precise per-cut classifications.

## Cost and research decision

Across the sampled inputs with at least two increments, ordinary serial application costs 115 rounded additions on Firewoods and 186 on Dead Tree. Building per-exponent parity descriptors costs 124 and 362 serial additions before any lookup overhead. On Dead Tree six additional serial additions remain in fallback. These counts allow reuse for the same donor sequence, recipient and exponent across cuts. For the two ambiguous transfer inputs this specific accounting uses the middle compatible word. The pre-summed scalar control pays 41 and 177 binary64 build additions plus one rounded output per application, with the value discrepancies above. None of these addition totals is an end-to-end latency measurement.

The static geometry contains 0.58–0.74 million positive edges per Firewoods donor prefix and 1.52–1.94 million per Dead Tree prefix, including edges to already-burning points. On the selected cuts, extremely few of these edges still deliver heat to a cold site. A more relevant ordinary optimization is to avoid maintaining or traversing edges to ineligible recipients, preserving the native order for remaining edges and updating it when the active set changes. The exact map is a verified numerical result. Actual use of this repeated-operator optimization at the tested scale does not establish a SIGGRAPH contribution. The fixed prefix and limited validation windows restrict interpretation.

## Reproduction

Run `node challenge.mjs` for [the stress tests](challenge.mjs). Run `node qualify.mjs` to recreate [the archived native qualification](RESULTS.json) from the T86 and T92 checkpoints, their original or reconstructed PLYs and per-frame ledgers. `T86_PLY` can point to the externally obtained Firewoods PLY. No additional native trajectories are required. [Qualification code](qualify.mjs)
