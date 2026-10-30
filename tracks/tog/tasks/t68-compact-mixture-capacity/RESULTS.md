# T68 results — ordinary two-Gaussian endpoint capacity

## Accepted outcome

The sole child returns zero and the frozen supervisor accepts **`completed_ordinary_two_gaussian_endpoint_witness`**. All seven numerical categories pass: frozen inputs/prior qualification, rules/reference statistics, unchanged T63 control, prescribed search, fixed selected confirmation, work counts and final identities. Physical success is checked separately against the original three .10 gates. This is empirical numerical qualification, not a formal floating-point enclosure.

Use the T67 normalized component g(sr,sz,z) with integral r g dr dz = 1, and q = Gamma [(1-eta) g1 + eta g2]. The complete selected tuple is:

| Parameter | Component 1 | Component 2 |
|---|---:|---:|
| sr | 1.0733495975649336 | 0.8500000000000001 |
| sz | 0.9822094448500068 | 0.65 |
| axial center | 0.03382405243470804 | 1.0 |

**eta = 0.32141700957001723**, **Gamma = 3.8064553493987305**. Both weights are positive and components differ. The model is smooth and positive over the complete meridional domain; its moments retain Gaussian tails. It does not inherit T66's zero exterior or piecewise factor representation. Eight stored parameters specify this candidate; no claim of uniform identifiability at coincident/zero-weight configurations follows.

| Fixed candidate / reference | Primary field error | Confirmation field error | Axial-centroid error | Covariance error / D0 |
|---|---:|---:|---:|---:|
| Selected / S256 | .04751348970275233 | .04751348970275233 | .008399928715086102 | .04898612819299672 |
| Selected / S128 | .047613562825337206 | .04761356282533721 | .008460595644590008 | .049277058619881395 |
| Unchanged T63 / S256 | .11603541704243382 | .11603541704243382 | .0810546875 | .0969848111128256 |
| Unchanged T63 / S128 | .11599556505187959 | .11599556505187959 | .0809940205704961 | .09712945843613188 |

The covariance denominator is the original S256 initial norm **D0 = 1.0882203729522952** in every comparison. The table's selected moments use the between-component formula; the raw-second-moment route also passes, with covariance errors .04898612819299689 / .04927705861988157. Maximum selected field-rule disagreement is **6.938893903907228e-18**, within 1e-9. The S256 contraction score differs from direct squared integration by **1.40304434737004e-14**. Nonnegative direct sums, rather than the subtraction C-J alone, qualify the field result.

The reference sensitivity difference is **.00010007312258487888**, below .001. All eight parameters, including fitted scale, stay fixed on S128. These two references concern the same development endpoint. This is neither a held-out scene nor evidence that the mixture can reach this state from the prescribed initial field without seeing the endpoint.

## Moments, positivity and conservation diagnostics

The selected full-space circulation centroid is **[1.255270858755723, .34436943621962196]**. Its covariance is

    [[ .4523055627204682,  -.05898928877696925],
     [-.05898928877696925, .9940547599241708 ]].

Full-space circulation is **3.8064553493987305** and axial impulse is **24.25162308589101**. Their differences from the stored original S256 reference are **+.0465129374522828** and **+.6261741577004862**; the S128 impulse difference is **+.6227388218942913**. These diagnostics show that this unconstrained endpoint fit is not an exact conservation result. They are not retroactive failure gates. The primary D8 integrals give circulation **3.8064553493964977** and axial impulse **24.251623085425535**; confirmation-rule diagnostics agree under the frozen tolerance. Finite D8 values and analytic full-space values remain distinct.

The sign of the cross covariance can be represented by ordinary mixtures with different radial widths and axial centers. This constructive witness removes the need to infer a compact-family deficiency from the earlier local single-Gaussian miss. It is not an optimality theorem or a new mixture algorithm.

## Search coverage and actual work

All 1081 unordered pairs from the 46-component bank are proposed, including identical pairs. The four fixed best distinct starts are evaluation indices 678, 794, 799 and 177. Their three-level refinement performs **56 complete twelve-neighbor polls**, hence **672 neighbor proposals**. Levels stop only at the predeclared no-improvement condition or eight-poll cap. There is no early-success shortcut. Evaluation 1629 is selected after the complete schedule, with 575 evaluated geometries supplying eligible candidates.

The **1753 proposals** partition into **1646 evaluations**, **75 geometry-cache hits** and **32 out-of-box rejections**. There are **304 distinct S256 component bases**, including the reused control basis, and 2989 component-cache hits. Width/position bounds and all original caps remain unchanged; no third component or expanded search occurs.

| Recorded work | Actual count |
|---|---:|
| Decoded NPZ files / arrays | 2 / 12 |
| Jacobi-rule eigendecompositions / shared rule nodes | 6 / 47 |
| Reference polynomial node-cells / corners | 983040 / 655360 |
| Control axis exponentials / diagonal Gram axis products | 7680 / 7680 |
| Control three-term reference cell visits | 491520 |
| Search axis exponentials / diagonal Gram axis products | 1551360 / 1551360 |
| Search three-term reference cell visits | 119144448 |
| Search cross-Gram axis products | 8427520 |
| Exact polynomial long divisions / isolation nodes | 10940 / 34348 |
| Counted rational operations | 3364183 |
| Attempted weights / original moment checks | 6879 / 6809 |
| Fixed control and selected moment routes / reference gate comparisons | 4 / 8 |
| Direct control / selected integrals | 4 / 4 |
| Direct reference-model node-cells / component point evaluations | 78643200 / 117964800 |
| Direct circulation/impulse diagnostic reductions | 1920 |

Maximum root depth is 39, retained rational size 4362 bits, Sturm chain length 5. All evaluated rounded polynomials complete root isolation; **1071** have an empty rounded feasible set. **155 geometries** retain incomplete representable-candidate construction because rounded feasibility and original floating moment tests disagree. None is relabeled globally infeasible. There are zero root-budget-unresolved or numerical-unresolved geometries. The selected candidate has both procedural flags true and passes direct original physical tests independently. These facts suffice for its positive witness; they do not certify continuous inner optimality or global geometry optimality.

Two input identity passes each hash **20652568 bytes**, including 50 repository/local input identities, the executable and manifest. All remain unchanged. No T65/T66 numerical array is an input, and no new array, trajectory, installation, pilot or retry occurs. The work journal retains detailed rational/root/candidate/proposal records locally instead of placing its 13.98 MB contents in Git.

## Complete cost and evidence limits

| Recorded phase | Seconds |
|---|---:|
| Imports and initial hashes | .2071884999750182 |
| Rules and reference qualification | .049385700025595725 |
| Fixed T63 control | 1.0306274000322446 |
| Fixed geometry and weight search | 7.07582679996267 |
| Fixed selected confirmation | 1.5219856998883188 |
| Counts, verdict and final hashes | .04060329997446388 |

Internal time before result writing is **9.929170899908058 seconds**; complete supervised child time is **10.119494400103576 seconds**; supervisor time before receipt writing is **10.540019800071605 seconds**. Phase times exclude uninstrumented instructions/output costs and are not independent runtime benchmarks. The complete child includes all control, setup, rule construction, fitting, roots, direct confirmation, hashing and output work. It is not an interactive simulation speed claim.

The inherited **1980.2512354997452-second** T56/T57/T58/T59/T60/T63/T65/T66 scientific-child subtotal plus T68 equals **1990.3707298998488 seconds**. This includes recorded failures in that series, not all project computation. T52, T54 and T55's separate scientific children, T53 diagnostics and T61's .9663960000034422-second qualification remain separately reported in their original receipts. Preparation, static review and publication are not scientific-child time.

OS-only preflight costs **.007756399922072887 seconds** before writing. Available physical memory is **30486089728 / 27687215104 bytes** at preflight/launch. Forty-one observations, including the final query, record lifetime peak working set **91754496 bytes**, maximum private usage **110243840**, peak pagefile usage **111366144** and last sample time **10.119146700017154 seconds**. The 120-second and observed 512 MiB limits pass; these are process observations, not whole-machine memory accounting.

The [independent review](../../../validation/t68-compact-mixture-review.md) records its source/saved-scalar/journal checks and prior advisory participation. It does not repeat scientific quadrature, root isolation or the fit. Numerical agreement, a successful ordinary comparator and review completion do not establish a TOG contribution.

The endpoint-capacity branch is now closed as a reason to invent a representation. The outstanding question is causal evolution from the same initial condition with a fair information and cost budget. T63 remains inconclusive, T60 remains failed, T61 remains separate; no historical result changes.
