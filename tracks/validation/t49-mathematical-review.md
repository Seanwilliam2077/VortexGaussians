# T49 mathematical and finite-scope review

30 October 2026. Reviewer: separate collaboration agent `t48_review`, returning for T49.

**Verdict: no unresolved mathematical blocker found in the seven final drafts identified below.** Both families have the stated exact closure under a prescribed incompressible affine advection/stretching/diffusion equation. Their fields and reconstruction contracts differ. This review does not establish self-consistent fluid evolution, implementation accuracy, performance, novelty or a TOG contribution.

## Participation, readback and identities

This reviewer previously reviewed T48 and inherited its collaboration history and the parent context. The T49 assignment identified the proposed checks. The reviewer then read all seven T49 drafts directly and checked their equations from the stated definitions. This is a separate adversarial readback with prior context disclosed, not blind discovery or independent numerical reproduction.

Two wording issues were reported before sealing: NEXT_EVIDENCE initially combined a six-page PDF-rendering allowance with an unqualified prohibition on a renderer, and DECISION referred ambiguously to a lower-count second column. The parent changed these to explicitly permit PDF-page reading while excluding fluid/scene rendering, and to name the curl-Gaussian column. Both final files were read back. The reviewer made no draft edits.

No external document was opened, no search was performed, and no numerical or symbolic-software evaluation, scientific-array reduction, simulation, implementation or benchmark was run. Tools only read the seven drafts and generated their byte/SHA-256 identities plus this review. Source acquisitions reported in SOURCES were not independently repeated. State files, historical records and other work were not edited.

The identity table below was generated directly from actual file bytes, without manual digest transcription:

| Draft | Bytes | SHA-256 |
|---|---:|---|
| SCOPE.md | 3233 | `bd5d424f0ac62c7a5e1c25adfee7f4b45a8d57fbf1bff8b4d83872cb477fead5` |
| METRIC_ENVELOPE.md | 8096 | `a317027b93765c641a13ec651c32102a936c92574cc72a7712d9e45ad3363516` |
| CURL_CARRIER.md | 10494 | `3ea80f3adb73eacf0318e9a362121926c3a7d229d453c408d7d9728edda71717` |
| SOURCES.md | 6286 | `cb71ef6835069dbc5b8af7731e465b64839330a4d998e586b2fe17fa0b85309c` |
| DECISION.md | 5187 | `8c1565700c7995df789f4a938f66ec6dbd905a9bf0c1a3f159758070665dde2a` |
| NEXT_EVIDENCE.md | 3777 | `d3befca58bd734d6cd6578fa2e8a1fcf43b827f21c95407d7496b74d30990bd4` |
| README.md | 2019 | `03ef8acbedd00b6b451af76456b274a60cc2952a833d1eb0e52686c9b16bcee5` |

These identities delimit the reviewed record; they do not substitute for the mathematical reasoning below.

## Independent metric and envelope

1. **Fourier equation and time ordering.** For trace A=0, Fourier transformation of (Ax) dot grad omega gives -(A^T k) dot grad_k omega_hat; the translation contributes i(b dot k)omega_hat. The displayed characteristic equation therefore has the correct stretch, diffusion and phase signs. With Fdot=AF, q=F(t)^T k(t) is constant along kdot=-A^T k. The derivation correctly uses the actual fundamental matrix. It does not replace it by exp(integral A) when matrices at different times fail to commute.

2. **Joint state equations and exact covariance.** The identity F Q_M(F^T k)=Q_(F M F^T)(k) F gives Mdot=AM+MA^T and cdot=Ac. Heat attenuation along the Fourier characteristic gives exactly the covariance increment 2 nu integral Phi(t,s)Phi(t,s)^T ds, so Cdot=AC+CA^T+2 nu I. The center obeys mudot=A mu+b. Differentiating the displayed integral solutions recovers all four equations. Positive definiteness and det F=1 follow under the stated assumptions. The text correctly distinguishes joint evolution from generally inexact finite affine/heat splitting, and does not omit the integration cost for arbitrary time-dependent A.

3. **Normalization and state count.** Q_(alpha M)=Q_M for alpha>0, and the normalized Gaussian requires no additional volume-amplitude factor because det F=1. Eighteen stored scalars and seventeen effective generic parameters are consistent. In particular, if two nonzero coefficients c and d gave the same angular field, choosing a nonzero k perpendicular to both would force c=d. For this fixed nonzero coefficient, equality on the open set k dot c != 0 then forces the two SPD matrices to be proportional. Thus no additional generic M/coefficient ambiguity invalidates the stated scale count. The zero field's extra degeneracies are acknowledged. The det M representative and optional time-dependent scale gauge are correctly described.

4. **Potential, tail and integrals.** The Fourier transform of c G_C+M Hess(h)c is exactly Q_M c times the Gaussian when -div(M grad h)=G_C. The heat-potential covariance C+2rM is correct. The unit-mass envelope yields the stated leading elliptic-Green-function Hessian tail. Changing C affects smoothing and generally algebraic subleading terms; the draft correctly avoids importing the matched-matrix exponential remainder from T48. The nonzero angular tail prevents absolute L1 integrability, while smoothness and order-zero Fourier behavior give L2 vorticity and L2 Biot-Savart velocity. The raw coefficient is consequently not assigned an ordinary absolutely convergent total-vorticity integral.

5. **Available reconstruction, without an impossibility claim.** The two Fourier velocity terms have the correct cross-product signs and denominators. Their Laplace parameters give covariance C+2aI+2rM. With fixed SPD C and M, the differentiated Gaussian kernels have absolutely convergent heat integrals; the bare scalar double inverse retains the three-dimensional infrared divergence. The record accurately describes an available one-plus-two-parameter representation, not a lower bound on all possible integral reductions. It does not declare independent C to make a one-dimensional evaluator impossible or claim an implementation advantage from the representation alone.

## Localized curl-Gaussian family

6. **Definition, normalization and impulse.** For m=aG_C, curl m=grad G_C cross a=G_C[a cross C^(-1)z], so vorticity is a localized odd Gaussian derivative and is solenoidal. Its integral is zero. The stated triple-product identity gives integral x cross omega=-a+3a=2a, hence unit-density hydrodynamic impulse I=a after the one-half factor. Integration by parts is valid because the Gaussian derivatives decay, and translation contributes nothing because integrated vorticity is zero. This is not the raw constant-vector Gaussian vorticity field.

7. **Covector law.** Under det F=1, both the gradient and a transform with F^(-T). The cross-product identity then gives omega'(Fx+b)=F omega(x). Transforming the impulse integral gives I'=F^(-T)I, consistent with a'=F^(-T)a. The coefficient must not use the contravariant update of the other family. There is no missing determinant factor under the declared incompressibility assumption.

8. **Exact prescribed PDE including viscosity.** The normalized Gaussian with the given center/covariance ODE solves scalar affine advection-diffusion. Commuting its gradient with material differentiation yields (D_t-nu Delta)grad G=-A^T grad G. Combining this with adot=-A^T a and the trace-zero cross-product identity yields A omega exactly. The covariance integral and a(t)=F(t)^(-T)a(0) are correct for noncommuting time-dependent A. Pure heat preserves a and adds 2 nu t I to C; simultaneous strain generally does not permit simply adding that matrix after the affine congruence. The drafts do not mistake the prescribed background U for the velocity reconstructed from the carrier.

9. **Velocity and one-dimensional heat formula.** Applying i k cross twice gives u_hat=P(k)a exp(-k^T Ck/2), with the correct positive projector sign. The finite Newton potential H_C=integral G_(C+2tI)dt satisfies -Delta H_C=G_C. Thus u=aG_C+Hess(H_C)a has zero divergence and curl equal to the declared omega. Setting s=2t produces the required one-half factor and Hessian integrand Phi[v(a dot v)-Ka]. Unlike the previous bare double potential, this single Newton potential is finite in three dimensions. Both the local Gaussian term and the integral are necessary parts of the same-field reference.

10. **Full directional Jacobian.** At fixed state, dv[h]=Kh, dPhi[h]=-Phi(v dot h), and the local term differentiates to -aG_C(v0 dot h). Product differentiation gives exactly w(a dot v)+v(a dot w)-(v dot h)[v(a dot v)-Ka] under the integral. Three coordinate directions produce the full spatial Jacobian with the stated convention. No derivative of changing carrier parameters is silently included.

11. **Positive self-center and parity.** At the center, the velocity matrix is the inverse-Fourier integral of P(k) times the positive Gaussian factor. For every nonzero h, the quadratic form integrates |h|^2-(k dot h)^2/|k|^2, positive on a set of positive measure. Therefore the matrix is strictly positive definite and the velocity is nonzero for every nonzero a. Isotropic symmetry gives (2/3)G_C(0)a. The reconstructed velocity is even, so its center Jacobian vanishes; vorticity is odd and vanishes there. This justifies the prospective nonzero-self contract without accusing a different existing source model of an error or claiming self-advection preserves the Gaussian family.

12. **Far field, convergence and cost limits.** The local Gaussian term decays rapidly, while the Newton-potential Hessian gives the displayed dipole velocity [3n(n dot a)-a]/(4 pi |z|^3) and an order |z|^(-4) gradient. For fixed C,z,a, the heat integrand has order s^(-5/2); its directional derivative has order s^(-7/2). SPD prevents a lower-end singularity. These justify the displayed improper integral and spatial differentiation, but do not furnish a finite-cutoff tolerance, uniform quadrature node count, stable floating-point evaluator or timing advantage. The draft includes all of those missing costs rather than treating finite state as constant-cost accurate reconstruction.

## Comparisons and the next finite source task

The two families share the prescribed operation and covariance ODE, not the represented field. Their low-frequency vorticity orders, spatial localization, coefficient semantics and center parity differ. The smaller curl-Gaussian record or integral count cannot establish superior equal-input accuracy or equal-particle efficiency. DECISION and the individual notes correctly require a common target and charged representation error before making such a comparison. Each same-field accuracy reference must retain its complete reconstruction, including the curl carrier's local and nonzero center terms.

The source record attributes the general magnetization/projection and covector-diffusion formulation to acquired ordinary literature, and reserves the exact Gaussian specialization as a local derivation rather than an established novelty. It separates successful access, partial reading, abstract-only evidence and the oversized-response failure. This reviewer checked those distinctions within the drafts but did not independently inspect the primary papers or replay the acquisition ledger. No performance or theorem from uninspected material was independently verified here.

NEXT_EVIDENCE is prepared, not executed. Its resolved scope is source-only: the one previously identified author-hosted PDF; one acquisition invocation; a 32 MiB response-body limit; a 60-second total limit; at most three HTTPS redirects; status/signature and source-identity recording; no retry, alternative host, new search or citation chase. It permits only existing dependencies, capped text inspection and six rendered PDF-page views, with repeats charged. The final wording explicitly permits those PDF views while prohibiting fluid/scene rendering. It requires stopping on access/reader/semantic insufficiency rather than substituting a favorable experiment. No code, assets, extra source or numerical task is authorized by that record.

The two reported wording ambiguities were resolved and read back before this seal. There is no remaining blocker to retaining these documents as analytical reference contracts and preparing the bounded source audit. This verdict does not establish a distinct method, useful scene-level task, numerical validation, strong-baseline advantage, multi-scene evidence or SIGGRAPH/TOG readiness. The full research goal remains active and unachieved.
