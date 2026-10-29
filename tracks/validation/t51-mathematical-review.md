# T51 mathematical readback

30 October 2026. Reviewer: collaboration agent `t48_review`.

**Verdict: no mathematical blocker found.** For each positive initial isotropic covariance scale and nonzero covector, the exact self-induced inviscid vorticity derivative lies outside the complete tangent of the existing single curl-Gaussian family. The argument establishes exact nonclosure only; it does not establish practical error, instability, a useful repair, novelty or a TOG contribution.

## Provenance and scope

The reviewer previously read back T48, T49 and T50 and inherited their collaboration context, including the prepared T50 membership protocol. The five T51 task files were then read directly. The reviewer checked the completed argument by hand, independently of its document hashes, and reported no blocker before the parent confirmed the files frozen.

No parent paper, raw source excerpt, image, new external source or linked material was read. The allowed T49/T50 parent documents did not require reopening. No numerical evaluation, symbolic-software evaluation, scientific-array reduction, simulation, implementation, rendering, additional family, counterexample batch or next-task argument was executed. Tooling was limited to document reading and byte/hash bookkeeping. The reviewer wrote only this review and did not edit task drafts, shared states or historical records. This is a separate adversarial algebra readback with inherited context disclosed, not blind discovery or experimental reproduction.

## Full tangent and parity

At the initial state C=sI, the derivative of the normalized Gaussian is correctly

    Gdot/G = (x dot v)/s - tr(D)/(2s) + (x^T D x)/(2s^2).

The first term comes from the moving center, the second from normalization, and the third from the inverse covariance. Differentiating G[a cross C^(-1)(x-mu)] also gives b cross x/s, -a cross v/s and -a cross D x/s^2. These are all terms in the displayed tangent; no normalization, inverse-matrix or center term is missing.

Every symmetric D is admissible instantaneously at sI because positive definiteness is open. Neither constant determinant nor isotropic covariance evolution is imposed. The proof therefore includes all three center, three covector and six symmetric-covariance derivatives. Possible redundancy in their tangent images does not weaken the parity argument.

Under x -> -x, the center terms are even, while every covector and covariance term is odd. Consequently an even physical target cannot obtain an even contribution from b or D, even if some odd terms cancel one another. The proof does not need to assume b=D=0, and does not make that unsupported assumption.

## Radial reconstruction and physical nonlinear derivative

The reconstruction u=aG+Hess(H)a is the complete existing same-field reference. For the regular decaying solution of -Delta H=g(r), radial integration gives H'=-r^(-2) integral_0^r q^2 g(q)dq. The 4 pi normalization is accounted for through 4 pi integral_0^infinity q^2 g(q)dq=1; no extra 4 pi factor belongs in the displayed finite-radius equation.

With B=H'/r, h=B'/r, f=g+B, tau=a dot x, W=a cross x and k=g/s, the formulas u=f a+h tau x and omega=k W follow from the radial Hessian. In the material-advection derivative, differentiating the radial k contributes tau(k'/r)(f+h r^2)W, while differentiating W contributes kh tau W. In the stretching derivative, W dot x=W dot a=0 removes the radial and tau derivatives, leaving exactly kh tau W. The latter terms cancel with opposite signs in the physical Euler right-hand side.

Since k'=-r k/s and B+rB'=H'', the remaining factor is f+h r^2=g+H''. The radial Poisson equation then gives g+H''=-2H'/r=L. Thus the displayed exact expression

    N = (G/s^2) L(r) (a dot x)(a cross x)

has the correct sign, radial dependence and powers of s. It is a physical vorticity derivative, not a potential residual. The center limits are smooth; L(0)=(2/3)g(0) and N(0)=0 are consistent with the complete reconstructed velocity.

Differentiating L=2r^(-3) integral_0^r q^2 g(q)dq yields L'=(2g-3L)/r. Strict decrease of the Gaussian gives 3 integral_0^r q^2 g(q)dq>r^3 g(r) for every r>0, hence L'<0 there. Positivity and the far-field coefficient L~1/(2 pi r^3) are also correctly normalized. These analytic statements are not sampled numerical evidence or a finite-cutoff bound.

## All-tangent contradiction

N is even. If it equaled the full tangent, taking parity components would force equality with only the center contribution. Evaluating that equality at zero forces a cross v=0, hence v=beta a for a spatially constant scalar beta because a is nonzero.

For each radius r>0 there are directions neither parallel nor perpendicular to a. In those directions both a dot x and a cross x are nonzero. Equality at every point would therefore require beta=L(r) for every positive radius, contradicting strict monotonicity. This is an all-tangent contradiction, not a failure manufactured by fixing the center velocity, suppressing covariance freedom or testing a small collection of points.

The resulting implication is appropriately stated: no differentiable parameter path inside this family can solve the exact self-consistent Euler vorticity equation through the declared state. The argument needs only the necessary tangent condition for such an exact path. It does not claim that an approximate particle method needs exact tangent membership or that no useful approximation can converge.

## Explicit center-affine residual and limits

T49's reconstructed center value is u(0)=L(0)a, and even velocity parity gives grad u(0)=0. The ordinary inviscid center-affine update therefore supplies v=L(0)a, b=0 and D=0. Substitution into the complete tangent gives the stated residual

    R = (G/s^2)[L(r)-L(0)](a dot x)(a cross x).

For every positive radius the scalar bracket is strictly negative. Thus R vanishes on the axis and equatorial plane (including the center), and is nonzero elsewhere. This correctly exposes why center-only or symmetry-set checks would miss the mismatch. The residual is not asserted to be a best-fit tangent residual or assigned an unevaluated norm.

Adding a gradient to the impulse potential cannot change this physical vorticity residual. This is distinct from T50's potential-class nonclosure under gauge blending, and from ordinary time-discretization error. It does not invalidate T49's exact prescribed-affine/heat closure in its own scope. It also does not attribute an error to current code that implements a different source model.

The decision preserves all material limitations: no finite-time error, best approximation, error tolerance, runtime, instability, practical bottleneck, repair or new mechanism has been established. No automatic enrichment, refitting, extra family, numerical experiment or implementation is selected by the negative result. No broader exact-closure theorem for other initial states or families is inferred. The full research objective remains active and unachieved.

## Frozen task identities

The following table was generated directly from actual file bytes after the freeze. Digests were not manually transcribed. The table specifies the reviewed record; it is not a substitute for the algebraic assessment above.

| File | Bytes | SHA-256 |
|---|---:|---|
| .gitignore | 7 | `a7d8bdcefba82a95ebc021d87c629fdea21f13af953bf01e28b7cf8b0eeceb41` |
| SCOPE.md | 2149 | `f7b27162656edd875f619806e32970dbdb9ef9f6dd22e2d45ce7d35ca5436772` |
| TANGENT.md | 6553 | `651d7b0daa128edefcd65d4f187229762363d6d627d6575d5ea1836ca7c8a66f` |
| DECISION.md | 3005 | `72d19b4f7d4d89233ba280fa6d16e72a48f0cc64030ee4991f45a35dec138e7a` |
| README.md | 1264 | `2e8057e1341b32b3eb1f0ad083ed50255e5069a41973e352eb5b4a4d5e7e9447` |

There is no unresolved blocker within this mathematical readback. Publication bookkeeping and historical preservation remain the root agent's separate responsibility; passing those checks cannot turn the exact nonclosure result into submission readiness.
