# T21 — three additional acceptance cases, not a speed result

29 October 2026. One fixed saved-data reduction completed and all 48 cases passed its empirical checks. At epsilon .01, the joint winner-prefix/signed bound accepts **4/28** eligible rays instead of 1/28. At .001 it still accepts 1/28. Both inherited simple and Jensen caps give these counts. Three distinct added rays meet the pre-result admission rule, so the elementary refinement is retained for a **prepared, not executed, complete-cost screen**. No TOG contribution or runtime advantage is established.

## What changed mathematically

[DERIVATION.md](DERIVATION.md) tightens T17's first-arrival coupling. If whole-primitive sorting chooses label i while exact continuous integration first encounters j, all labels preceding i in the sorted order must be empty. That event is independent of the i/j pair event. Its probability P_i=exp(-sum_{k<i} tau_k) therefore multiplies the existing pair cap B_ij.

For Delta=L_exact-L_sorted, accumulate positive channel contrasts into U and negative magnitudes into V using P_i B_ij. The fixed original sorted color has the real-arithmetic bound E=min(G,max(U,V)), componentwise. This does not assume unknown positive and negative errors cancel. The original G, colors, pair caps, inputs and numerical references remain unchanged; no new output midpoint or stronger shifted global interval is introduced.

The formula follows from elementary probability and signed interval arithmetic, works beyond Gaussian densities, and is not claimed novel. A finite empirical comparison is not a floating-point certificate. The rationale comes from T18's loose bounds, not T19's failed Simpson delivery or T20's source-access gap.

## Fixed screen and results

[PROTOCOL.md](PROTOCOL.md) was written before new bound values were evaluated. [freeze.json](freeze.json) authenticates it, the derivation, runner, original input, T18 result and T19 common-path source. [reduce.py](reduce.py) imports only the standard library; its formula receives no saved reference color or fixture identifier. Source hashes were unchanged before/after the sole execution.

The input contains the original 48 researcher-authored development rays, 399 labels and 3272 pairs. The historical denominator is 28 non-control N>=4 rays. The separately evaluated common-unsolved population also has 28 at each epsilon: none of these 28 receives T19's declared vacuum/zero-mass/equal-color/identical-profile exact solution or G/2 global-center shortcut. This excludes those named shortcuts, not all ordinary solutions. The old informative counts are reproduced under their original definition.

| Fixed epsilon | Old simple / Jensen acceptance | New simple / Jensen acceptance | Added by signed-only diagnostic | Additional cases from prefix |
|---|---:|---:|---:|---:|
| .001 | 1/28 for each | 1/28 for each | 0 | 0 |
| .01 | 1/28 for each | 4/28 for each | 2 for each | 1 for each |

The original accepted ray remains `structured-04-n4-span3`. The three additions at .01 are below. Values are maximum channel bounds/errors, using the inherited Jensen pair cap; the simple cap accepts the same rays.

| Added ray | Old bound | Signed-only diagnostic | Prefix + signed | Saved GL64 actual error |
|---|---:|---:|---:|---:|
| generic-11-n8 | .013883357 | .009364390 | .008029167 | .004952786 |
| generic-14-n4 | .010169901 | .005093256 | .005076645 | .001976787 |
| structured-08-n8-span3 | .023174623 | .011601640 | .009079286 | .003546754 |

Two additions already follow from retaining error signs. Only the structured eight-label case crosses .01 because of the prefix beyond that diagnostic. Jensen still adds **zero accepted rays over simple** at either threshold. The result does not support attributing all three additions to the prefix or to Jensen saturation.

The dense `structured-16-n32-span3` remains a limitation: Jensen falls from .049377786 to .015255493, while the saved actual error is .000139032. It still fails both acceptance thresholds. The saved-reference opportunity count among previously rejected common-unsolved rays is one at .001 and nine at .01; the combined bound captures none and three respectively. Those are posthoc development-data counts, not certified general reachability limits or inputs to formula selection.

## Verification and actual work

[Full saved results](run-01/results.json) retain all 48 per-case prefixes, pair signs, intervals, bounds, reference comparisons and population flags. All saved adaptive/GL32/GL64 colors and available analytical controls satisfy the new signed intervals under the unchanged 1e-9 empirical allowance. Maximum observed enclosure excess is5.440092820663267e-15. Maximum reconstruction/dominance discrepancy is8.881784197001252e-16 against the separately fixed1e-12 arithmetic consistency allowance. Both allowances were fixed before execution; neither changes the .001/.01 acceptance thresholds.

[Independent review](../../../validation/t21-bound-review.md) covers the proof and protocol before execution, static runner review, and a post-run audit of saved data without rerunning the candidate or numerical references. Root also parsed the runner statically and checked the complete source/result identities. One schema-inspection KeyError and one later report-format SyntaxError were read-only tooling mistakes; neither invoked the candidate, produced a new reference, changed a result or used a retry. The sole candidate invocation returned0, with empty stderr and no timeout.

| Recorded analysis work | Count |
|---|---:|
| Prefix additions / scalar exponentials | 352 / 352 |
| Structural / formula pair scans | 3272 / 3272 |
| Prefix-cap products, both caps | 6544 |
| Color-cap products, both formulas/caps | 39264 |
| Channel nonnegative fsums | 1440 |
| New Gaussian CDF / integrand / quadrature evaluations | 0 / 0 / 0 |

Worker time before result serialization is .061850700s; the external supervisor, including process startup and result writing, records .187710000s under the fixed60-second cap. These are offline analysis costs, **not delivery timings or a speedup**. Actual execution stores pair terms/signs and therefore uses O(N^2) memory; the derivation's possible streaming O(N)-extra-storage reduction is not the implemented memory profile.

Deployment would still pay parameter preparation, clipped masses, sort, alpha work, pair CDF/cap construction, RGB delivery, rejected shortcut work and fallback. Loading saved B hides none of this in the conclusions: it simply means this task does not measure that cost. No new numerical solve, scene, sample, source query, installation, renderer, GPU work or art production occurred.

## Decision and next evidence

The frozen rule is met: all checks pass and three distinct previously rejected rays outside the declared common shortcuts are newly accepted by Jensen. This is a limited acceptance-region observation on already inspected development data. It supports only preparing the [next finite complete-cost contract](NEXT_EVIDENCE.md), not executing it here or expanding scenes/architecture.

T19 remains232/2880 deliveries with **stable wins NOT EVALUATED**; its failure and timings are not relabeled or pooled with this task. T20's ordinary real-arithmetic enclosure remains valid as a local contract, with unresolved primary-source mapping and no implementation. A formal floating-point certificate is neither supplied nor silently required for every future empirical comparison. The current research still lacks complete-cost benefit, practical workload evidence and novelty clearance.

The research branch is updated; main, art and all historical gates remain unchanged. The active research goal continues independently of the deleted heartbeat. [audit-manifest.json](audit-manifest.json) records the publication and preserved evidence.

```sh
# Default is plan-only (statically reviewed):
python -I -B -X utf8 tracks/tog/tasks/t21-winner-prefix-bound/reduce.py

# Reproduction syntax only; this completed task permits no second invocation.
python -I -B -u -X utf8 tracks/tog/tasks/t21-winner-prefix-bound/reduce.py run --out NEW_DIRECTORY
```

The frozen sibling inputs/results, exact source identities and freeze.json are required. No automatic retry or input-generation command exists.
