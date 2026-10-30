# T65 results — the relaxed product error is below 10%

## Accepted scientific outcome

One frozen scientific child returned zero. The supervisor accepted **`completed_qualified_no_separability_exclusion`** after all eight exact qualification categories passed: inputs before, reference readback, Gram checks, matrix norms, decomposition checks, construction agreement, fixed work and inputs after. The four prescribed SVDs completed; no retry, extra decomposition, Gaussian evaluation/fit or flow trajectory occurred.

The diagnostic minimizes physical-vorticity relative L2 error over arbitrary products u(r)v(z) against each saved piecewise-linear endpoint. It relaxes Gaussian shape, positivity and moment restrictions. Its exact real-arithmetic interpretation is in [T64](../t64-separability-contract/DERIVATION.md); this measurement is empirically qualified and retains `formal_exclusion=false`.

| Reference | Weighted-basis error F | Independent quadrature error Y | Original field gate |
|---|---:|---:|---:|
| S256 | 0.09016269504854825 | 0.09016269504854829 | 0.10 |
| S128 | 0.09017538698272817 | 0.09017538698272813 | 0.10 |

The S256/S128 F difference is **1.2691934179923092e-05**, within the fixed .001 sensitivity condition. All four estimates are below the gate by more than the 1e-8 numerical separation buffer. Both references receive their own decomposition of the same prescribed diagnostic; this is reference sensitivity, not a held-parameter fit or independent scene.

The result does not support numerical separability exclusion. In particular, the preceding Gaussian search's .1160354170 error cannot be used to assert that coupling is necessary under this field criterion. A broader separable function can have a lower relaxed field score; its moments, positivity and exterior behavior have not been checked here. This does not prove Gaussian capacity, Gaussian incapacity, joint feasibility or a useful evolution law.

## Numerical qualification

| Quantity | S256 | S128 |
|---|---:|---:|
| Reference physical-vorticity norm squared | 12.641021874312637 | 12.63780003427593 |
| F spectral energy | 12.641021874312639 | 12.637800034275912 |
| F tail energy after leading singular value | 0.10276280548587871 | 0.10276554003480719 |
| F largest singular value | 3.540940421530241 | 3.5404850648239012 |
| Complete F/Y spectrum relative difference | 1.5591898480567412e-15 | 1.1073001438401264e-15 |
| F/Y error difference | 4.163336342344337e-17 | 4.163336342344337e-17 |
| Extra quadrature spectrum relative norm | 1.556554619880456e-15 | 1.0988790182781468e-15 |

All reference moments and polynomial statistics match their frozen metadata and T63 readback. Every analytic Gram block is positive definite. Maximum analytic/quadrature Gram discrepancy is 3.803556076633082e-16; maximum Cholesky reconstruction discrepancy is 2.212776091792001e-16. Maximum stored matrix/spectral norm discrepancy is 1.4432899320127035e-15. Maximum relative decomposition residual is 2.9508986401755895e-15 and maximum orthogonality residual is 5.240171226641496e-14, comfortably within the predeclared empirical checks.

These checks concern the saved finite-box reconstruction. Computed operator-norm upper expressions remain explicitly uncertified. Agreement of two constructions and two references is neither a rigorous rounding enclosure nor a continuum Euler-error bound. The negative exclusion result must not be relabeled as a representation impossibility.

## Work and full cost

The child decodes exactly two inputs/twelve arrays, constructs orders 3 and 2 (five nodes), and shares **983040** node-cell reconstructions between reference statistics and Y assembly. It checks **655360** corners; constructs and checks 1152 analytic Gram blocks, 1152 quadrature blocks and 1152 Cholesky blocks; and performs 2688 one-dimensional Gram-node evaluations. Two coefficient matrices, two F matrices and two Y matrices produce **four SVDs, four residual products and eight orthogonality products**.

Each before/after input pass hashes **20065261 bytes**, covering 32 frozen repository inputs, executable and manifest. Output hashing covers **40085944 bytes**. The two ignored bundles contain **40078336 array bytes** and 16 arrays each, including F/Y, both factor triples, coefficients, Gram factors and coordinates. No array is decoded outside the paid scientific child for review.

| Phase | Seconds |
|---|---:|
| Imports and initial input hashing | 0.237105200 |
| S256 F SVD | 0.089572000 |
| S256 Y SVD | 0.153964500 |
| S128 F SVD | 0.013234400 |
| S128 Y SVD | 0.019786600 |
| S256 audit write/hash | 0.043066600 |
| S128 audit write/hash | 0.012260900 |
| Final input hashing | 0.026148300 |

The table is a selected phase breakdown, not exhaustive wall time; [result.json](result.json) records all 23 phases. Internal time before result writing is **0.771980700083077 seconds**. The complete scientific child takes **0.9605694999918342 seconds**; supervisor time before receipt writing is **1.0986102999886498 seconds**. Prior scientific history 1978.636870399816 plus this child gives **1979.5974398998078 seconds**. T61 qualification remains separately .9663960000034422 seconds. OS-only preflight takes .008567100041545928 seconds before writing; the independent successful metadata/scalar audit takes .1533226000610739 seconds. Analysis, static review and publication work are not represented as scientific run time. None of these timings is a simulation speedup comparison.

Preflight/launch available physical memory are 28655902720 / 28752113664 bytes. Five samples, including a successful final query, report lifetime peak working set **102449152 bytes**, maximum private usage 109199360 and peak pagefile usage 125071360. Last sample time is .960165899945423 seconds. These observed counters stay within the fixed 512 MiB ceiling; complete child time stays within 120 seconds. They are not whole-machine resource accounting.

| Ignored output | File bytes | SHA256 |
|---|---:|---|
| S256-audit.npz | 32052956 | `d5a31f851f9fd3c0df86f29d5397f17861d1e3eb65168e51887d6519fa2a4de4` |
| S128-audit.npz | 8032988 | `aab0677987fcb99375817ab3e2b8dbbe7ddcc85206de671e3d38959c86d5fc30` |

The [execution receipt](execution.json) anchors the complete work journal and resource/stdout/stderr logs. The independent review checks 69 journal records, 23 phase pairs, all identities, declared array layouts and saved scalar arithmetic. It performs no matrix reconstruction, integration or SVD; prior static-review involvement is disclosed. Historical failures and gates remain intact. No creator validation, causal mechanism, generalization or TOG contribution follows from this single researcher-defined diagnostic.
