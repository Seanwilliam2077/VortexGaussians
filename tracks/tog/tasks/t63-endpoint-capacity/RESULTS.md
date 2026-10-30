# T63 results — endpoint field error remains above the gate

## Accepted outcome

One scientific invocation returned zero and passed all six frozen qualification categories: input identities before, reference readback, ordinary-score calibration, selected-score qualification, fixed-work accounting and input identities after. Its accepted status is **`completed_search_inconclusive`**, with `capacity_witness=false`. No scientific retry or new flow trajectory occurred.

The scoped family is q=A exp(-r²/(2 sr²)) exp(-(z-z0)²/(2 sz²)), with positive amplitude and widths. It is tested against the same qualified t=1 reference, using the original physical-vorticity measure 2πr³ dr dz on D8. Amplitude is eliminated for the primary 8x6 quadrature objective. This is an offline capacity search, not an executable dynamics rule.

## Search and physical evidence

The moment-matched first candidate records field error **0.12884619751363202** and fails the shortcut. The prescribed 65 grid coordinates then supply three local starts; 39 grid coordinates survive the original moment tests. Those starts complete 18, 20 and 20 six-neighbor cycles, ending at step 2^-10. Across center, grid and polls, 414 attempted coordinates yield **372 objective evaluations and 42 rejections**. No boundary gate is relaxed for rounding.

The minimum recorded eligible objective is index 139, originating at `poll/0/16/2/-1`. Selected parameters are A=1.4960975737243711, sr=0.9983495975649336, sz=1.0072094448500069 and z0=0.43382405243470806. Selection considers the prescribed records; it supplies no global-optimality guarantee.

| Endpoint / candidate | Relative vorticity L2 | Absolute axial-centroid error | Normalized covariance error | Joint result |
|---|---:|---:|---:|---|
| Original ordinary model, S256 (T60/T61) | 0.11619327199178484 | 0.08269547822674578 | 0.10056910228577531 | Field and covariance fail |
| Selected candidate, S256 | 0.11603541704243381 | 0.0810546875 | 0.0969848111128256 | Field fails |
| Same complete parameters, S128 | 0.1159955650518796 | 0.0809940205704961 | 0.09712945843613188 | Field fails |
| Unchanged gates | ≤0.10 | ≤0.10 | ≤0.10 | All required |

Thus ordinary parameter adjustment repairs the recorded covariance miss, but this search barely changes the field mismatch. The evidence does not isolate its structural cause or exclude an unvisited feasible Gaussian. S128 is sensitivity of the identical selected tuple, not a second fit, independent scene or held-out task.

All eight direct rule scores complete: calibration and selected candidate on each reference, each under 8x6 and 16x12. Calibration reproduces the saved ordinary scores. For the selected S256 candidate, the direct squared numerator/denominator are 0.1702014743623162 / 12.641021874312637; S128 gives 0.17004123437668497 / 12.63780003427593. Selected contraction versus direct score differs by 2.1094237467877974e-15. The maximum stored direct-rule difference across calibration and confirmation is 1.3877787807814457e-17. These checks support this evaluator; they are not formal continuous-integral or continuum-flow certificates.

The candidate's analytic full-space circulation is 3.764739553063935 and axial impulse 23.576541601661578. Relative to S256 they differ by +0.001275854944545296 and -0.002070112050678863, respectively. Against S128 the impulse difference is -0.0022151982188550745. These are disclosed diagnostics, not newly imposed gates; D8-integrated quantities remain distinct from full-space formulas. Positivity and moment/field requirements do not by themselves enforce conservation-respecting dynamics.

## Full recorded work and resources

The child decodes two existing NPZ files and loads twelve arrays. It constructs six one-dimensional rules with 47 nodes; performs two polynomial reference integrations totaling 983,040 node-cell points and 655,360 corner evaluations; and executes 374 contractions (372 search plus two calibration). Contractions account for 1,912,320 axis exponential evaluations and 146,767,872 coefficient-cell visits. Eight direct Gaussian rule integrations account for 78,643,200 node-cell points, each with reference reconstruction and Gaussian evaluation.

Both identity passes hash **20,262,257 bytes**: 20,146,578 repository-input bytes, 107,312 runtime bytes and 8,367 manifest bytes. There are 36 frozen repository inputs. The manifest's first read is explicitly charged; identical before/after byte counts are expected. All identities remain unchanged.

| Child phase | Seconds |
|---|---:|
| Imports and initial hashes | 0.185760900 |
| Rules and reference qualification | 0.048388300 |
| Calibration | 0.716808800 |
| Selection | 0.058099400 |
| Selected direct confirmation | 0.720700300 |
| Final input hashes | 0.028766000 |

These phase times are not exhaustive wall time and are not comparable algorithm benchmarks. The child records 1.7623158999485895 seconds before result writing; the supervisor records **1.957236499991268 seconds for the complete child** and 2.049519899999723 seconds before receipt writing. Prior scientific-child history is 1976.6796338998247 seconds, so cumulative cost is **1978.636870399816 seconds**. T61's standard-library evidence qualification remains separately 0.9663960000034422 seconds. OS preflight takes 0.009635900030843914 seconds before its receipt; postrun review's successful metadata/scalar audit takes 0.03869780001696199 seconds. Human/agent analysis and publication bookkeeping are not represented as scientific run time.

The sole child uses Python 3.12.14/NumPy 2.3.5 with per-child single-thread limits. Available physical memory is 30,700,634,112 bytes at preflight and 31,041,073,152 at launch. Nine observations report lifetime peak working set **48,762,880 bytes** (about 46.5 MiB), maximum private bytes 66,170,880 and peak pagefile bytes 67,297,280; final sample time is 1.9569236000534147 seconds. These observed counters stay below the frozen 512 MiB ceiling and 120-second child limit. They do not measure whole-machine resource use.

## Review, provenance and limits

The [sealed review](../../../validation/t63-endpoint-capacity-review.md) checks all frozen identities, 491 journal records, coordinate decisions, work counters, saved numerator/denominator arithmetic, moments, conservation diagnostics and receipts. It decodes no arrays and repeats no field evaluation or integral; its pre-run involvement is disclosed. It corroborates the accepted evidence without claiming independent numerical replication.

The [result](result.json) retains exact scalars; [execution](execution.json) anchors raw journal/resource identities. No failed history is relabeled. The researcher-defined single-ring task remains distinct from a validated creator need. Neither the local negative search nor numerical qualification establishes family impossibility, a new mechanism, useful causal dynamics, generalization, visual benefit or TOG contribution.
