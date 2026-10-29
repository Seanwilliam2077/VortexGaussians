# T21 independent bound and saved-data review

29 October 2026. Reviewer: pressure_screen. **Mathematical, protocol, runner and saved-result review complete. The one authorized saved-data screen qualifies and meets its preparation-only admission gate.** The reviewer has not imported or executed `reduce.py`, called an integrator, generated samples, evaluated new exponentials, or accessed new sources. Pre-execution clearance preceded root's invocation; subsequent checks used only saved values and independent arithmetic.

## Mathematical and protocol findings

No blocking issue found in the frozen real-arithmetic derivation. For stable sorted ranks i<j, the event that every label k<i is empty is independent of the two-label event F_j<F_i<=b. The actual winner event W_ij is a subset of their intersection; therefore w_ij<=P_i D_ij<=P_i B_ij. The exact winner integral correctly retains survival of the other labels k>i. There is no valid additional whole-interval emptiness factor for labels between i and j, and the document does not add one.

The disjoint winner events give Delta=L_exact-L_sorted=sum(c_j-c_i)w_ij. Separately bounding positive and negative coefficients gives -V<=Delta<=U. Intersecting with the original symmetric global interval [-G,G] yields the frozen lower/upper endpoints and E=min(G,max(U,V)). The half-width of that asymmetric interval would not be the error bound of the unchanged sorted output; the implementation uses its larger endpoint magnitude instead. It does not assume cancellation of unknown terms or introduce the unselected shifted color-hull bound.

The real inequalities E_combined<=E_signed_only<=E_old are justified by termwise nonnegativity, and Jensen remains no larger than simple when the inherited pair caps have that ordering. These inequalities need not be strict. The first sorted row receives no prefix improvement; the two-label bound is unchanged. Stored pair caps and binary64 exponentials do not supply outward-rounded certificates, including in possible underflow cases. The existing empirical allowance is not a proof of numerical enclosure for arbitrary inputs.

The protocol fixes the same 48 development rays, both historical epsilons, both inherited caps, the unchanged output, and one signed-only attribution diagnostic before computing candidate values. Jensen alone governs admission. The 28-ray historical denominator and the separately declared common-unsolved population avoid counting shared analytical shortcuts as new work. The saved-reference opportunity count is only a posthoc observation about this set, not a formal attainable limit or a method input. Zero added rays closes this particular refinement on its fixed scope; added rays permit preparation of a later cost contract, not execution or a contribution claim. Neither result establishes a general ordinary-method limitation or changes T19's unevaluated stable-win status.

## Static runner findings

`ROOT=HERE.parents[3]` resolves the repository. Required input/result/protocol/proof/runner hashes, the freeze hash, original fixture equality, stable ordering, complete unique pair identities, label/pair totals and inherited qualification are checked. The formula receives colors, order, masses, pair caps and G; it receives no fixture ID, reference RGB or opportunity classification. Reference comparisons and population flags occur after formula evaluation.

Masses remain indexed by original input position. Prefix accumulation indexes them through the stable order; prefix lookup for a pair uses its earlier original input index. Separate nonnegative lists correctly retain channel signs, including harmless zero contributions. Old absolute sums are reconstructed, and both signed-only and combined estimates are checked against all three saved references and available analytical RGB with the frozen allowances. The distinct admission count unions rays across epsilons rather than counting ray/epsilon pairs.

The operation ledger is consistent with the code: for each ray the two caps require 2*(3+6+6)=30 channel `fsum` calls, with separate prefix additions/exponentials, pair traversals, prefix-cap products, and color products. Validation and reduction scans are separately counted. All-case reporting after a comparison failure cannot admit the candidate: aggregate admission requires global qualification. Exceptions also yield an unqualified record; no repair/retry path is present.

The actual script retains per-pair signs and term lists, so its working storage is O(N^2), in addition to the loaded results. The derivation's possible streaming O(N) additional storage must not be attributed to this audit implementation. Offline time excludes producing the loaded pair caps, sorting, mass preparation and fallback, and is not a delivery benchmark. Root has committed to an external 60-second subprocess supervisor that also covers launch and final serialization; the runner's internal deadline alone would not cover its final output write.

## Checked pre-execution identities

All paths below are relative to the repository and were read directly. No task artifact was edited by this reviewer.

| Artifact | SHA256 |
| --- | --- |
| `tracks/tog/tasks/t21-winner-prefix-bound/PROTOCOL.md` | `42795e131f9a6b0186de7169c8f2a574cd3c04d9a815f8e286e41d735fc85cd1` |
| `tracks/tog/tasks/t21-winner-prefix-bound/DERIVATION.md` | `af8956a46fc60e5ef0fa671388b485820c5d2a2b81e1eab285dd3a1e64866ddc` |
| `tracks/tog/tasks/t21-winner-prefix-bound/reduce.py` | `8c03c0a00057f881754fa50cc2ce3938a12db283ec7989147198c1cf539566fe` |

## Independent saved-data audit

The sole `run-01` exits 0, with 48/48 cases qualified and no recorded failure. The freeze was created before the recorded start. All six frozen artifacts, their byte lengths and before/after hash maps match current files. Every T21 case maps in order to the original T17 fixture and T18 record; all 399 labels and 3272 unique pair records are accounted for. Stable order, inherited masses, sorted RGB, G, references, analytical RGB and all pair signs agree with their sources. No historical reference or input was changed.

Independent standard-library arithmetic checked every saved positive/negative sum, interval endpoint, absolute bound, old reconstruction, per-case flag, summary population and admission decision. The reviewer used the stored prefix factors, rather than reevaluating exponentials. Their sequential optical-mass sums agree exactly with the saved sums; a separate product recurrence using the saved per-label survival factors `1-alpha` differs from the stored prefixes by at most **2.220446049250313e-16**. This is an empirical arithmetic consistency check, not a new enclosure certificate. An exact-rational cross-check of the color differences, pair caps and stored-prefix products differs from the saved nonnegative sums by at most **4.440892098500626e-16**.

The 48 cases contain 144 saved numerical RGB vectors and 8 analytical RGB controls. All **1824** channel/reference/cap/variant combinations were checked against both their signed interval and absolute bound. Maximum reference-enclosure excess is **5.440092820663267e-15**, below the frozen 1e-9 allowance. Maximum old-bound/sum reconstruction difference is **8.881784197001252e-16**, below 1e-12; maximum combined/diagnostic/old dominance excess is **0**. Finiteness, nonnegativity and cross-cap dominance under the same arithmetic allowance also hold.

One reviewer-only audit initially asserted inherited `B_Jensen<=B_simple` bitwise and stopped. Two already saved T18 pairs exceed that real-arithmetic ordering by floating-point rounding, with maximum excess **3.76158192263132e-37**. Continuing the audit with the existing 1e-12 consistency allowance required no artifact edit, candidate invocation, new exponential or numerical solve. This is a correction to an overly exact audit assertion, not a repaired scientific result or a change to the frozen gates.

Both historical and declared common-unsolved denominators are **28** at each epsilon. Old counts reproduce before the new counts are compared. Simple and Jensen have the same acceptance counts:

| Epsilon | Old accepted | New accepted | Added | Added by signed-only diagnostic | Further addition requiring the prefix |
| --- | ---: | ---: | ---: | ---: | ---: |
| .001 | 1/28 | 1/28 | 0 | 0 | 0 |
| .01 | 1/28 | 4/28 | 3 | 2 | 1 |

The existing accepted ray is `structured-04-n4-span3`. The three distinct additions are below; all entries are maximum-channel Jensen bounds, with the saved GL64 error shown only as an observation.

| Ray | Old | Signed-only | Prefix + signed | Saved sorted error |
| --- | ---: | ---: | ---: | ---: |
| `generic-11-n8` | .013883356920583585 | .009364390463573067 | .008029167396330883 | .004952786226347317 |
| `generic-14-n4` | .010169901232627307 | .005093255818616234 | .005076645414011072 | .001976787054986273 |
| `structured-08-n8-span3` | .023174623480314908 | .011601639766995159 | .009079286420270808 | .0035467535747147894 |

Only the third ray demonstrates a threshold crossing attributable to the prefix beyond signed grouping. Simple also accepts each, with maximum bounds .008493713378563339, .005700712819343058 and .009291979768190704. The posthoc saved-reference opportunity counts are 1 at .001 and 9 at .01; they did not enter the formula. All IDs, not just counts, match the independently reconstructed populations.

## Actual cost and decision boundary

There was one candidate invocation, no timeout and no retry. The worker records **0.06185069994535297 s before serialization**; the external supervisor records **0.18771000008564442 s**, covering the subprocess and its output serialization. These intervals are nested and must not be summed. Both fall below the external 60-second cap. Six progress records report 8, 16, 24, 32, 40 and 48 completed cases, followed by the qualified final record; stderr is empty. These times describe offline reduction, not production delivery or speedup.

The independently reconstructed ledger contains **352 prefix additions and 352 exponentials**, **3272 structural plus 3272 reduction pair traversals**, **6544 prefix-cap products**, **39264 color-cap products**, **9816 color differences**, and **1440 nonnegative channel sums**. There are zero new Gaussian CDF or reference/integrand evaluations. Loaded caps, sorting, masses, original bound construction, fallback and delivery preparation remain outside this timing. The audit's own saved-data arithmetic is not another candidate experiment.

The frozen gate is satisfied by three distinct newly accepted Jensen rays. Retain exactly an **acceptance-region observation on inspected development data** and allow preparation of one later finite complete-cost contract. No execution is authorized by this gate itself. The result does not establish speed, a useful scene-scale regime, a Gaussian-specific mechanism, literature priority, practical demand or a TOG contribution. T19 stable wins remain **NOT EVALUATED**; its failed delivery and T20's source-access gap remain unchanged.

## Saved-result identities

All paths in this table are relative to `tracks/tog/tasks/t21-winner-prefix-bound/`.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `freeze.json` | 1394 | `1bd509e0536bff1390f207a6d693ef20991b68b31da5db9a277d37b048e4ce32` |
| `run-01/results.json` | 976592 | `94d3ad607ba70ee6d7192643e6ad39ec3802f2a269b12df8cbfe87e59917bf83` |
| `run-01/execution.json` | 957 | `5cdf5220945dd7241c8994b8c6290eabb4cb7270d048ea26b12acc29bce0b9fa` |
| `run-01/stdout.log` | 482 | `63b6a636d8060a99c587a1cc627f998c9c7231bb336bacccf39834dd2f8374f6` |
| `run-01/stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The inherited input/result identities are respectively `5cccf0238c679e14bc50e67d2d24726a58295b484b1d3464bf77d4eca0491cb7` and `fa4fb6887c6b38e800f18e919634821b3ee51c2fb0122cd0dbb4047eead7873d`. The frozen ordinary shortcut source remains `2369efea4f60d4cf546f926b9b6322bfa12a4109fa1332b92f2b22f94779ecb2`; it was not imported during this review.
