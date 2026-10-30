# T66 results — joint feasibility of the saved leading product

## Accepted outcome and fixed candidate

One frozen scientific child returned zero and was accepted as **`completed_broader_separable_endpoint_witness`**. All eight numerical categories pass: frozen inputs before, input shapes/coordinates, triangular recovery, reference readback, polynomial/quadrature agreement, saved field-score agreement, fixed work accounting and frozen inputs after. Physical conditions are separately checked; numerical completion is not substituted for them.

The candidate uses only T65's saved S256 leading singular pair, recovered by 768 two-component back substitutions. The radial integral before sign orientation is -1.055438935660223. Multiplying both factors by -1 leaves their product and amplitude unchanged. Recovery residuals measured before that sign change are 1.6616919780842952e-17 radially and 6.403241222231151e-17 axially. No new decomposition, optimization, conservation rescaling or clipping occurs.

| Same S256 candidate | Field error | Absolute axial-centroid error | Normalized covariance error | Original joint gates |
|---|---:|---:|---:|---|
| Against S256 | 0.09016269504854826 | 0.013722547497353466 | 0.09536735231131477 | all pass |
| Against S128 | 0.09018322260501836 | 0.01378321442685726 | 0.0954720855302773 | all pass |

Each gate remains .10, and both covariance comparisons use the original S256 initial norm **1.0882203729522952**. S256's score agrees with T65's relaxed score within **1.3877787807814457e-17**. The held-candidate reference difference is **2.0527556470098518e-05**, below the fixed .001 sensitivity tolerance. S128 receives the same factors, amplitude, support and evaluation partition, rather than its own fit. This remains resolution sensitivity on one endpoint, not a second scene or temporal generalization.

## Positivity, moments and domain semantics

Minimum radial/axial factor endpoints are **1.2290799672965663e-14 / 1.6096382503772358e-14**. All 1536 checked endpoints are positive without clipping. Quadrature reports circulation **3.7500837415807635**, centroid **[1.253169501860887, 0.3390468174373546]** and covariance diagonal **[0.42180821295787996, 1.0270947772640708]**. Its cross covariance is 1.1102230246251565e-16; the independent separable formula gives exactly zero. Raw moments and normalized statistics agree under the frozen 3e-11 relative/3e-14 absolute checks.

The same candidate's q-squared integral is **12.363213419611576**, axial impulse **23.471072397833836**, and physical-vorticity norm squared **12.538259068826777**. These use their distinct original weights: circulation uses r, q-squared uses 2πr, impulse uses πr³q, and physical-vorticity squared uses 2πr³q².

Circulation differs from either reference by **-0.009858670365684219**; axial-impulse differences are **-0.1543765303566822 / -0.15781186616287712**. They are reported diagnostics. No new conservation gate is added, and no exact conservation claim follows from passing the three original endpoint gates.

The candidate is defined on r in [0,8], z in [-8,8], with **explicit zero extension outside**. Its reported finite-D8 moments become full-space moments only under that declared extension. Boundary product suprema at r=8, z=-8 and z=8 are **1.7306437099427377e-14**, **1.644673525173657e-14** and **1.9122939512692585e-14**. They are small but nonzero, so the extension is discontinuous. The radial/axial factors also have 255/511 nonzero internal jumps, with maximum magnitudes **0.00039755499675120376 / 0.0007841483614035027**. These facts remain part of the result; it is not promoted to a smooth fluid model.

The representation stores 512 radial and 1024 axial coefficients, plus coordinate arrays. This is a broad piecewise-linear product with **1536 stored factor coefficients**, not evidence that a similarly accurate low-parameter model already exists. The scalar-factor rescaling redundancy also means this storage count is not an independent-dimension claim.

## Fixed work and complete resource cost

The child decodes exactly three NPZ files/nineteen arrays. Work includes 768 triangular recovery blocks, nine independent polynomial factor integrals covering 3328 cell moments, 1536 factor endpoints, 766 adjacent-piece jumps and three boundary-product checks. Both original references contribute 655360 corner checks. Closed-form orders 3 and 2 construct five rule nodes without an eigensolver; shared quadrature evaluates 786432 candidate samples and 1572864 reference samples. Two reference integrals and one candidate integral complete. SVD/eigensolver calls, Gaussian evaluations/fits and new trajectories are all zero.

Input hashing covers **52331299 bytes** before and again after computation, including 47 repository inputs, the executable and manifest. One ignored bundle contains four arrays a[256,2], b[512,2], r[256], z[512], all float64: **18432 array bytes**, **19390 file bytes**, SHA256 `02fda1bd7d9a079b424337aeff7b08fe29596fd6718abfa3d985cde0ec616f5d`.

| Recorded phase | Seconds |
|---|---:|
| Imports and initial hashes | 0.220101500 |
| Input arrays and recovery | 0.030344600 |
| Independent polynomial moments and sign | 0.003225100 |
| Recovered-factor artifact | 0.002161600 |
| Fixed quadrature | 0.093598200 |
| Scores and verdict | 0.000038800 |
| Final input hashes | 0.092669900 |

The seven recorded phases do not include every uninstrumented instruction or result-writing cost. Internal time before result writing is **0.44871629995759577 seconds**, complete supervised child time **0.653795599937439 seconds**, and supervisor time before receipt writing **0.8076659999787807 seconds**. The inherited reference/endpoint series subtotal **1979.5974398998078** plus this child gives **1980.2512354997452 seconds**. This receipt field tracks scientific invocations T56/T57/T58/T59/T60/T63/T65/T66, including failures; it is not the total of all research computation. Earlier [T52](../t52-best-tangent-enstrophy/execution.json), [T54](../t54-scalar-verification/execution.json) and [T55](../t55-axisymmetric-reference/execution.json) record their separate 4.807828599936329 / .5475459999870509 / 3.918251399998553-second children. T61's .9663960000034422-second evidence qualification and T53 runtime diagnostics also remain separate. No historical receipt or subtotal is rewritten. OS-only preflight takes .015331199974752963 seconds before writing. Static review, preparation and publication are not represented as scientific-child time.

Preflight/launch available physical memory is **28637425664 / 28460531712 bytes**. Four samples, including a successful final query, record lifetime peak working set **48238592 bytes**, maximum private usage 24436736 and peak pagefile usage 33591296. Last sample time is .653252899996005 seconds. The observed 512 MiB/60-second limits pass; these are per-process observations, not whole-machine costs or simulation speedup evidence.

The execution receipt anchors 19 work-journal records: seven phase pairs, three decoded-input metadata records, one factor save and one terminal outcome. The independent standard-library audit takes **0.08084399998188019 seconds**, excluding final prose and overall review time. It checks source/receipt identities, declared layouts, saved scalar arithmetic and completion counts without array decoding or numerical replication, with prior static participation disclosed.

## What changes, and what remains unresolved

Unlike T65's field-only relaxation, this result supplies an actual positive candidate satisfying all original joint endpoint gates under the stated extension convention. The original requirements are therefore jointly attainable in this broader family. T63 remains an inconclusive local single-Gaussian search; neither Gaussian impossibility nor optimal search coverage has been proved.

No new method, compact model, causal evolution, exact conservation, multiscene evidence, creator validation or TOG contribution follows. T60's failed receipt, T61's separate qualification and every earlier outcome remain unchanged. The next finite decision must address compact ordinary alternatives and their complete costs before attributing a gap to a new mechanism.
