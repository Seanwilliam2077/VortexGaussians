# T55 — initial axisymmetric reference review

## Verdict and review provenance

No unresolved mathematical, execution-contract, saved-data or interpretation blocker remains. The single T55 scientific child completed all five preselected initial reconstructions and passed all eight frozen predicates. The supported conclusion is `qualified_initial_only`: an ordinary initial spatial reconstruction for this field and these fixed comparisons. There is no fluid trajectory, physical-task pass, candidate-method result, independent domain-error certificate or TOG contribution.

Reviewer: the continuing `t48_review` agent. I inherited the collaboration history and participated in earlier T48–T54 mathematical/code reviews. I also advised on T55's physical metric contract and read its actual TASK, FORMULATION, PROTOCOL, reference implementation, runner and freeze helper before launch. This is not a blind design review or independent scientific execution. I reported one interpretive correction before freeze: D96 changes both domain and boundary quadrature, so its difference must be labelled a combined sensitivity control. The final frozen protocol explicitly makes that correction. I read back the final viscosity/normalization and boundary-singularity clarifications as well.

After the root's single execution, I read the saved manifest/receipt/result, clarified documents and final README/RESULTS/DECISION. With explicit saved-data-review authorization I imported the existing NumPy only to load the five existing NPZs with allow_pickle=False and reduce their saved fields. I used a weighted flattened Euclidean norm to reproduce all core/full-box errors and paired comparisons. I did not execute, import or compile reference.py; generate a new quadrature rule; evaluate the analytic oracle again; apply a new Poisson solve; advance transport; or access any external source. Numerical saved-array postprocessing did occur, and is not being concealed as purely textual review. It is not a second reference invocation or independent replication.

The source record's byte identity and frozen preservation were checked, but I did not independently inspect its external documents or verify its source-search accounting. Its ancestry/source claims remain attributed to the root's bounded audit and other consultant. My mathematical assessment below is the hand readback of the explicit formulation and implementation. Only this validation file was written by me; task drafts and shared state were not modified.

## Hand mathematical and implementation checks

With omega_theta=partial_z u_r-partial_r u_z and psi=r^2 phi, differentiation gives u_r=-r phi_z, u_z=2phi+r phi_r and omega_theta=-r(phi_rr+3phi_r/r+phi_zz). Thus the stated elliptic equation has the correct sign and source q=omega_theta/r. For inviscid no-swirl axisymmetric flow q is advected. The normalization m=1.5 exp(-|x|^2/2)e_z gives the specified q, a=1.5(2pi)^(3/2)e_z, width one and u_z(0)=1; it is not a unit normalized-Gaussian coefficient.

At the axis, even radial regularity gives phi_r=0 and the limit phi_rr+3phi_r/r=4phi_rr. The four-radial-coordinate plus axial elliptic interpretation is consistent. The 5D fundamental solution is 1/(8pi^2 d^3). Integrating its angular measure 4pi sin(theta)^2 dtheta gives the implemented 1/(2pi) factor. Interior Gauss source nodes avoid an exactly coincident sampled boundary target, but the continuous boundary integrand can still approach its endpoint singularity. The frozen formulation now states this limitation. No singular self term was silently set to zero, and no conclusion is extended to direct interior point evaluation.

For the radial finite-volume operator, W_i is the exact integral of r^3 over a radial cell and face coefficients are r_face^3/(W_i h). The axis face coefficient vanishes. At the first cell the radial coefficient is 4/h^2, giving the correct four-dimensional radial limit on a quadratic. The outer half-cell Dirichlet contribution is twice the ordinary face coefficient; the extra diagonal and right-hand-side terms in code match this. Axial boundary coefficients similarly double 1/h^2. Neighbor face fluxes agree after multiplication by W_i, which establishes weighted symmetry; Dirichlet boundaries and positive flux coefficients give positivity. Diagonal preconditioning in that weighted inner product is consistent with the inspected CG recurrence.

The solver starts from zero, caps each solve at 2000 iterations, and checks the true weighted residual when the recurrence reaches its tolerance. A failed true check restarts the direction within the same iteration budget. It does not launch a new scientific child. Saved residuals and iteration counts were checked against the contract; the post-run review did not reapply the operator or rerun CG to independently reproduce those residuals.

The centered derivatives, reflected axis ghost values and ordinary Dirichlet extrapolation generate the five nonzero Cartesian Jacobian entries at y=0: J_xx=-phi_z-r phi_rz, J_xz=-r phi_zz, J_yy=-phi_z, J_zx=3phi_r+r phi_rr and J_zz=2phi_z+r phi_rz. The essential J_yy entry is retained, and the Frobenius norm counts every nonzero component. The grids are cell-centered and do not sample the axis itself; axis treatment is imposed and checked algebraically. Boundary ghosts are not presented as a high-order boundary formula, and their full-box consequences remain visible.

For the analytic initial oracle, f=1.5 A(d)/d^3 with A=integral_0^d t^2 exp(-t^2/2)dt yields f(0)=.5. D=f'/d=(1.5 exp(-d^2/2)-3f)/d^2 and E=D'/d=(-1.5 exp(-d^2/2)-5D)/d^2 give the stated velocity/Jacobian. Differentiating the integrated Gaussian series gives the implemented denominators 2n+3, 2n+5 and 2n+7 with coefficients +1.5,-1.5,+1.5. Sixteen terms below d=.5 and the erf expression above it match the declared code. No formal floating-point remainder certificate is claimed or independently numerically evaluated here.

The source-tail expression is also correct: the normalized radial r^3 exp(-r^2/2) tail is (1+R^2/2)exp(-R^2/2), the axial Gaussian tail is erfc(R/sqrt(2)), and the outside-box union is their sum minus their product. The initial physical vorticity squared norm instead has r^3 exp(-(r^2+z^2)) measure, producing radial (1+16)exp(-16) and axial erfc(4) tails for the fixed core. Neither omitted-mass fraction is a velocity/Jacobian-error bound or a statement about later support.

## Saved-data verification

All ten frozen input byte identities and the bundled executable match the manifest. The manifest, code, runner, result, logs and per-case JSON identities match the receipt. The exclusive started marker agrees with the receipt prefix. Each NPZ hash matches its case record. All saved arrays are finite, u and J have the prescribed 2- and 5-component shapes, q/phi shapes and grid spacing match the case, and each per-case JSON is identical to its result entry. The six stdout JSON lines match the five case metrics/solver records and final status/checks; stderr is empty.

From the saved fields I reproduced all twenty core/full-box relative errors to floating-point reduction rounding. The review weights are 2pi*r*h^2, not the elliptic r^3 weights. The same fixed core mask r<=4, |z|<=4 is used without alignment. These are discrete physical-weight quadrature norms, not rigorously exact continuous-space integrals. The saved values are:

| Case | Core u relative error | Core J relative error | Box u relative error | Box J relative error | CG iterations | True weighted residual |
|---|---:|---:|---:|---:|---:|---:|
| S32 | 0.01480333804862586 | 0.007889622530816702 | 0.01491742433832684 | 0.00801374123745079 | 138 | 9.448402671864405e-11 |
| S64 | 0.0036849143556747974 | 0.0019734732003031824 | 0.003713613160999885 | 0.002004511695400218 | 273 | 9.387893660303047e-11 |
| S128 | 0.0009202425493332519 | 0.0004934573730947934 | 0.0009274278641937993 | 0.0005013080699934691 | 538 | 9.71143661936379e-11 |
| Q64 | 0.0036849143556749553 | 0.0019734732003032617 | 0.0037136131610000615 | 0.002004511695400345 | 273 | 9.387895719647135e-11 |
| D96 | 0.0036860813466678263 | 0.0019723751459892257 | 0.0036964858015597537 | 0.0020016179424957956 | 416 | 9.657413456216354e-11 |

The recorded refinement factors are 4.01728143988709 and 4.004285998669207 for u, and 3.9978361649930836 and 3.9992779678743946 for J, all exceeding 1.5. The finest core errors both satisfy .005. Their roughly fourfold reduction is observed behavior of these grids, not a convergence theorem.

Q64 and D96 core coordinates and physical weights equal S64's exactly. The independently reduced saved-array differences reproduce Q64/S64 u=8.362970310756439e-15 and J=1.7873746984816567e-13, below 1e-4, and D96/S64 u=6.522378115760852e-5 and J=4.502255222099013e-6, below 1e-3. No interpolation or alignment was applied. All eight qualification predicates reproduce from saved metrics/residual metadata and saved-array comparisons.

Q64 isolates the changed boundary quadrature orders at R=8; its tiny disagreement does not imply equal true quadrature accuracy, particularly for a future evolved source. D96 changes both the source/solve box and quadrature orders, including angular order, so it is a combined sensitivity check. It cannot isolate domain truncation. The final protocol, results and README accurately preserve this limitation. Direct analytic free-space comparisons still measure each initial case's combined observed error within the core/full box.

## Budget and claims

The actual recorded work is one scientific child, five elliptic solves and zero trajectories. The exclusive started marker and no-retry supervisor enforce the single permitted invocation path. The child returned zero in 3.918251399998553 supervised seconds within the 180-second cap. Its internal timer before result writing is 3.7610482999589294 seconds; the supervisor timer before receipt writing is 3.942284299992025 seconds. These quantities have different endpoints and are not interchangeable. Saved per-case phase and total timers retain boundary integration, solve, reconstruction, analytic-oracle and output overhead, rather than presenting solve time alone as full cost.

Summing saved metadata gives 69,632 grid cells, 279,756,800 scalar boundary target/source/angular evaluations and 8,972,626 raw NPZ bytes. These counts are loop/accounting quantities, not independent samples or equivalent-accuracy work. Stdout is 2,028 bytes and stderr is empty. The five solver iteration counts are 138,273,538,273,416 with no direction restarts; their saved true residuals meet 1e-10. Timings are one-shot qualification observations, not a method speed comparison. Preparation, source audit, later review and publication are not claimed to be included in the child time. The review's permitted saved-array reductions are separate postprocessing; they did not add a reference solve.

TASK fixes the future t=1 field/centroid/shape screen as a researcher choice. Primary vorticity error uses the unaligned world-coordinate 3D norm; circulation centroid/covariance use omega_theta dr dz. Their weights are not interchangeable. The center update stays diagnostic and the complete ordinary tangent fit receives the verified coefficient. Reference-snapshot fitting must remain an oracle. The .25-width future motion screen, 10%/1% physical/reference field thresholds and secondary thresholds are not inferred from the earlier .355 derivative residual or claimed to express creator/venue requirements. No finite-time values or positivity/conservation results are reported in T55.

The final DECISION correctly identifies a remaining dynamic-reference gap: boundary values must depend on current discrete q at every stage rather than the analytic initial source. Its w=rq conservative equation follows from partial_r(r u_r)+partial_z(r u_z)=0; annular-volume fluxes from a common streamfunction can enforce the corresponding discrete cancellation. Positivity and circulation conservation alone cannot certify shape accuracy. The decision prepares a separately frozen short [0,1/4] coupled qualification with at most six trajectories in one 600-second child, independent control comparisons, complete costs and stop rules. No T56 algorithm has been fully reviewed here and no T56 invocation is authorized or claimed by this T55 evidence. The original t=1 task remains unchanged, and a reference failure remains an evaluation gap rather than carrier failure.

The full research goal remains active. The measured result is a useful initial reference prerequisite, not a useful new mechanism or a completed SIGGRAPH/TOG contribution.

## Sealed actual identities

These thirteen task identities were generated directly from the final bytes after root declared the claims ready. SOURCES.md is included for identity/preservation only, not as an independently re-audited external-source claim. Publication/audit files created later and this review itself are outside this set.

| File | Bytes | SHA256 |
|---|---:|---|
| `.gitignore` | 7 | `a7d8bdcefba82a95ebc021d87c629fdea21f13af953bf01e28b7cf8b0eeceb41` |
| `TASK.md` | 4132 | `b470e55c6449348136673764e7d7b975cd3bad479ddefa0d881d827eba84e89e` |
| `FORMULATION.md` | 4604 | `7d463593ec8f021ab814d0213bcf5f9b74b1c79ae9496b6d4cab2452f6440709` |
| `PROTOCOL.md` | 4087 | `878d7ef55fbbbe6927233b1defcad425d33c4c49ff221515fa5fabf2c833e465` |
| `SOURCES.md` | 5590 | `6a543063d8c079ff654b9a5c1f3cb32b574efbca2e2a9c7d93525af5134d7c10` |
| `reference.py` | 10613 | `499bab137463df4435230e3cbf4d16b0723feed5ad5d06087a0bafd911204908` |
| `run_once.py` | 4932 | `37d8eefdbd6e7af26602568aa3447c3ad6c19a6453a0a4f54281b81a94970ffd` |
| `input-manifest.json` | 2726 | `f0e9d24ab7e084a893e355490988f69bc99563a2eb444b2d0baa37e6b9b00e05` |
| `execution.json` | 2868 | `87bc69a913b50d77b061186788da98b4e5382b44deab29fe0ba9477c9aeab476` |
| `result.json` | 7436 | `93ade10e42154fdc46c90aaaed3839c1362f3f05ff1b1b9b3bb971816bc41cae` |
| `RESULTS.md` | 6587 | `508e34cb0d1d0422841b77b486692a06117dbb3a355694803c74fd7a349d3848` |
| `DECISION.md` | 6454 | `ed1d20b4b603ecb4afd49e06f4a33aba6b86ecbabd6bb1f87c4cbc445c1d420f` |
| `README.md` | 1645 | `21a92427c2a2f5e825be5f23994746e9dcaa93ef95f14f44330786f2bdceb434` |

Historical frozen inputs were checked directly against the manifest:

| File | Bytes | SHA256 |
|---|---:|---|
| `tracks/tog/tasks/t49-affine-diffusive-state/CURL_CARRIER.md` | 10494 | `3ea80f3adb73eacf0318e9a362121926c3a7d229d453c408d7d9728edda71717` |
| `tracks/tog/tasks/t51-self-induced-tangent/TANGENT.md` | 6553 | `651d7b0daa128edefcd65d4f187229762363d6d627d6575d5ea1836ca7c8a66f` |
| `tracks/tog/tasks/t54-scalar-verification/DECISION.md` | 4285 | `52c7e6e29275e3cbe46663b43cb9117d2390bb335fef657d6ff4bb727d91a92b` |

The ignored helper/marker/log/case/raw identities below document the saved evidence; they are not claimed to be committed assets:

| File | Bytes | SHA256 |
|---|---:|---|
| `local/freeze.py` | 1794 | `cebc66e7e620efe5c74124531be1923da038d8cf3e67db4bb35171f9050f3e85` |
| `local/execution-started.json` | 1260 | `32d567d9368bedf0e8c08ace5efa112ceb5ec35916469bfb3947fb29af1b5ec5` |
| `local/stdout.txt` | 2028 | `03c8cbaf4ad8ec7efc7a0441f82528156a26d8bf08cc549d30fc6ce737d411a8` |
| `local/stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `local/S32.json` | 1103 | `dbdc91f10d9b72680ee2ba235eedc93579699701540ec201556c82139537e339` |
| `local/S64.json` | 1111 | `2398142ac08358271c868cee836a4504b8e32767346b3ed214fe216ff0afbe2c` |
| `local/S128.json` | 1112 | `9e6013678ded661383c4b4b4fc3377c0aa704f43c6b2c9b4b5e961fa9858d51e` |
| `local/Q64.json` | 1111 | `83329562432d2e4897fa8a37ad69e6012ef95b4370695b812b178c5e4d018ac4` |
| `local/D96.json` | 1109 | `9e302360551e64e9ff92728b16fa41c19bff7cecc5a53c343ba297d5ce26ecd0` |
| `local/S32.npz` | 268714 | `0e76c02ce71442ba06e3908f35966202006627f93912237a7c911f84ad621353` |
| `local/S64.npz` | 1058986 | `f77043afc620bc0b283890aa8e956664906a4dc86ade67e9f924f9b2927670d7` |
| `local/S128.npz` | 4212394 | `0c3bfb38217bdf5e3343208a05a929a9bf9df92eed75ca652be8601114eda302` |
| `local/Q64.npz` | 1058986 | `368191ffd1e4fbdd848be24d9bab602781299b92b1416f01fcef4f04464831cf` |
| `local/D96.npz` | 2373546 | `9b814f68afbb7e297311dc682f9984d186c8d89c846ba4763f630feb35b1c4dc` |

Executable: `C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`, 107312 bytes, SHA256 `5640e9be2fd33d05a1a9ae1228e2354609a69ab831605995ec4e2bd6da8fff5e`. This identifies python.exe; it does not hash or freeze every dependent runtime library.
