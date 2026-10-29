# T48 mathematical review

30 October 2026. Reviewer: separate collaboration agent `t48_review`.

**Verdict: no mathematical blocker found in the six frozen drafts identified below.** This is analytical readback of a prescribed free-space carrier and its reconstruction formula. It does not validate a numerical implementation, physical time evolution, performance advantage, literature novelty or submission readiness.

## Independence and exact scope

The reviewer inherited the parent conversation summary and collaboration context, received a targeted mathematical checklist, and then read all six draft files directly. The parent subsequently identified an ambiguity in the description of the raw-Gaussian comparator; the author corrected that paragraph and integral punctuation. The reviewer read back the final VELOCITY file before sealing this review. This is a separate adversarial readback with disclosed collaboration, not blind discovery or independent experimental reproduction.

Only SCOPE, CARRIER, VELOCITY, SOURCES, DECISION and README were read for this review. T47 ANALYSIS was permitted but was not needed or opened. No external source was acquired, no source search was extended, and no simulation, numerical evaluation, symbolic-software evaluation, scientific-array reduction, benchmark or implementation was run. Tool use was restricted to document reads and generating/verifying document byte counts, SHA-256 identities and this review. No draft, state or historical file was edited by the reviewer.

The six-file identity table was generated programmatically from actual file bytes, without manual digest transcription:

| Draft | Bytes | SHA-256 |
|---|---:|---|
| SCOPE.md | 3005 | `f1fbca4d45a504263daa18b41967d32d7f564d4f1071857d44f98aef89586ea2` |
| CARRIER.md | 7186 | `1e328b7e8fae6c1eeb1cfaea95445f17642e71d25ad7c90698d3674a90885013` |
| VELOCITY.md | 10579 | `1136803b737a53fedca7ebfdeb12d2e1dd2519b6251d9291e8764afbe78b2a36` |
| SOURCES.md | 6606 | `d929a44f994b4246c3e313603eebd27e7b9d8f036777d864e5241df271d74bb8` |
| DECISION.md | 4990 | `7972df60decebfc4adcc5b5f4daa0aef86ad2ceaf9ddcdeea0dcee2b2377f90b` |
| README.md | 2133 | `0bb96683dc7fc12975aae85d530ee15da5d3d716d5b28d73569285448b71ac94` |

These identities specify the reviewed content, not its scientific truth. The reasoning below supplies the mathematical assessment.

## Carrier, normalization and limitations

1. **Projection and affine closure.** For nonzero k, Q_Sigma=I-Sigma k k^T/(k^T Sigma k) has range k-perpendicular and nullspace span(Sigma k). It is idempotent, and Sigma^(-1)Q_Sigma is symmetric, giving the claimed metric orthogonality. Substituting q=H^T k directly yields H Q_Sigma(q)=Q_(H Sigma H^T)(k) H. The Fourier phase and Gaussian exponent give the stated center and covariance updates. Under det H=1 there is no missing volume factor. The determinant and c^T Sigma^(-1)c invariants follow by congruence. Twelve stored scalars is a parameter-record count, not a claim of twelve unconstrained degrees of freedom along one fixed ancestor's orbit.

2. **Real-space potential and Hessian.** Whitening z by Sigma^(-1/2) turns -div(Sigma grad) into the negative Laplacian. Consequently the factor (det Sigma)^(-1/2) and erf(r/sqrt(2))/(4 pi r) are the correct normalized Gaussian potential. Fourier transformation of c G_Sigma+Sigma Hess(h_Sigma)c produces exactly the declared Q_Sigma multiplier, with the correct sign. The radial Hessian formula and its congruence back to z are correct. Its central value is Hess_z(h_Sigma)(0)=-(1/3)G_Sigma(0)Sigma^(-1), hence omega(mu)=(2/3)G_Sigma(0)c. This also checks the normalization independently of the far-field expression.

3. **Tail, integrability and coefficient meaning.** Differentiating the leading elliptic Newtonian potential yields exactly [3 z(z^T Sigma^(-1)c)/r^5-c/r^3]/[4 pi sqrt(det Sigma)]. For fixed SPD Sigma and nonzero c this nonzero angular coefficient gives an algebraic tail and prevents absolute L1 integrability; it does not prevent L2 integrability. Bounded angular behavior of omega_hat near k=0 gives a velocity multiplier no worse than order 1/|k|, which is square integrable near the origin in three dimensions. High-frequency Gaussian decay controls the other end. The draft correctly avoids assigning the raw-source coefficient an absolutely convergent total-vorticity meaning, Gaussian tail culling, or a physically validated circulation/energy interpretation.

4. **Gauge and diffusion.** Q_Sigma annihilates Sigma grad psi, and its congruence update transports that gauge as stated. A nonzero constant-vector Gaussian carrier is not itself a pure gauge: choose a nonzero k perpendicular to c. Heat diffusion changes the Gaussian envelope to Sigma+2 nu s I while leaving the original Q_Sigma unchanged. Updating the single stored Sigma would generally change the projector as well, so the claimed generic failure of single-matrix diffusion closure is correct. The isotropic, zero-diffusion and zero-field exceptions are appropriately separated.

5. **Physical boundary.** Common prescribed affine pushforward is an exact kinematic identity. Independent maps on overlapping carriers do not thereby define a single physical flow map or a self-consistent Euler evolution. The drafts retain this distinction and do not infer locality from the finite parameter record. No current-code defect is established by these calculations.

## Reconstruction derivation and directional Jacobian

6. **Fourier signs and differentiated heat integrals.** The correction symbol is -i(k cross Sigma k)(k dot c)exp(-r/2)/(p r), with p=|k|^2 and r=k^T Sigma k. Applying curl Sigma grad(c dot grad) to a Gaussian has exactly that sign and cubic Fourier factor. The raw term grad(Phi) cross c has the declared sign. The covariances Sigma+2tI and (1+2s)Sigma+2tI follow directly from the two Laplace representations.

7. **Infrared issue and absolute convergence.** The undifferentiated double integral is not a finite scalar potential in three dimensions: its low-frequency scalar symbol behaves as |k|^(-4). For fixed SPD Sigma, let R=1+s+t. On bounded query sets the double-integral covariance has eigenvalues comparable to R. Third and fourth spatial Gaussian derivatives are bounded at infinity by constants times R^(-7/2); integrating over the two-parameter region is then finite. The undifferentiated Gaussian instead scales as R^(-3/2) and diverges after two-parameter integration. Subtraction Phi_C(z)-Phi_C(0) improves that decay to R^(-5/2), makes the subtraction convergent and leaves the relevant spatial derivatives unchanged. This justifies the differentiated representation and its local differentiation/interchange without asserting a finite bare potential.

8. **Change of variables and moments.** With a=1+2s and b=2t/a, the Jacobian is a/4, the covariance is a(Sigma+bI), and the integration domain is the stated rectangle. The third Gaussian derivative has a negative cubic-v term divided by a^3 and three positive K-v terms divided by a^2. Combining these with Gaussian normalization a^(-3/2) and the Jacobian a/4 gives J_(7/2) and J_(5/2), respectively. The substitution y=1/a, incomplete-gamma form, recurrence, derivative identity and series of J_p all check. The stated central fractions are the corresponding 1/(p-1) limits. The small-q stability caveat is necessary and retained.

9. **Cross-product contraction and velocity.** One K-v permutation cancels because Sigma K is symmetric. The other two give E=(Kc) cross Sigma v+v cross Sigma Kc, while the cubic contribution is -D(c dot v), with D=v cross Sigma v. Since Sigma K=I-bK, these simplify to the stated E and D. The raw term contributes -(1/2)N exp(-q)(v cross c) after b=2t, yielding the full factor 1/4 and -2 coefficient in the boxed one-dimensional formula. No factor or sign discrepancy was found.

10. **Full directional derivative.** At fixed carrier state, dq[h]=v dot h, dv[h]=Kh, dD[h]=(Kh) cross z+v cross h, and dE[h]=(Kc) cross h+(Kh) cross c. Applying J'_p=-J_(p+1) yields every displayed directional-Jacobian term, including the positive final ell D s_c J_(9/2) term. Taking three coordinate directions gives the full spatial Jacobian with the stated column convention. This is not a material derivative through evolving parameters.

11. **Center, isotropic limit and improper endpoint.** SPD Sigma removes the b=0 singularity. At z=0 the odd velocity vanishes and its Jacobian is finite. For Sigma=lambda I, D, E and their directional derivatives vanish identically, so the correction disappears and the raw isotropic Gaussian Biot-Savart limit is recovered. For large b, K=b^(-1)I-b^(-2)Sigma+O(b^(-3)); leading terms in D and E cancel, giving D=O(b^(-2)) and E=O(b^(-2)). With N=O(b^(-3/2)), this gives correction decay at least b^(-7/2), including the directional Jacobian, versus b^(-5/2) for the raw terms. These fixed-parameter asymptotics do not establish uniform quadrature complexity or a finite-cutoff error certificate.

## Comparison, provenance and decision

The corrected final VELOCITY paragraph and DECISION agree: the **complete two-term formula** is the same-field reconstruction reference. The raw anisotropic Gaussian term alone describes a different source field and is only a structural/cost comparison. Its cheaper structure must not be presented as a failed same-field baseline. The full one-dimensional formula is available to ordinary competitors; the derivation does not entitle a proposed method to exclusive use of standard matrix preparation, quadrature, differentiation or isotropic cases.

The drafts include source preparation, query work, quadrature accuracy/refinement, Jacobian evaluation, accumulation, updates and boundary/evolution requirements. No fixed node count, speedup, numerical conditioning envelope or new core method follows from this readback. CARRIER's fixed-dimensional pointwise vorticity expression is correctly separated from accuracy-controlled velocity reconstruction.

SOURCES internally reports a bounded two-query/four-item screen with two successful opens and two failed opens, and identifies abstract-only versus inspected-manuscript evidence. This reviewer did not replay those acquisitions or verify the primary papers; that provenance remains the source analyst's record. Its stated non-match does not support novelty, and the drafts do not use it that way. The ordinary-method and literature limitations are consistent with retaining the construction as analytical reference material only.

The parent-requested comparator clarification was resolved before this seal. No unresolved mathematical blocker remains in the reviewed record. This acceptance is restricted to the displayed continuous-field identities and their stated scope; it does not establish implementation correctness, practical usefulness, a strong-baseline advantage, multi-scene evidence, or a SIGGRAPH/TOG core contribution.
