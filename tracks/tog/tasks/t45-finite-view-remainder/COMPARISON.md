# Same-contract ordinary alternatives, costs and a tightness limitation

The [finite Taylor bound](PROOF.md) is valid, but it must be compared with ordinary methods using the same covariance information, setup opportunity and pointwise contract. These comparisons are algebraic deductions, not new source acquisitions or numerical results. T44's inspected references remain the limited source record for ordinary KL/overlap ancestry; this task makes no new literature-priority claim.

## Ordinary KL can also yield a fixed-cost pointwise bound

Let `r=f-g`, and let every projected covariance and the merge have floor lambda as in the proof. For one normalized 2D Gaussian,

```text
sup_y ||grad phi_2(y;mu,S)|| <= 1/(2pi sqrt(e) lambda^(3/2)).
```

Indeed, with `z=S^(-1/2)(y-mu)`, use `||S^(-1/2)||<=lambda^(-1/2)`, `sqrt(det S)>=lambda` and `sup_(t>=0) t exp(-t^2/2)=exp(-1/2)`. Hence r is globally L-Lipschitz for

```text
L=1/(pi sqrt(e) lambda^(3/2)).
```

If `q=||r||_infinity`, the cone of radius q/L around an absolute maximum gives

```text
||r||_1 >= integral_0^(q/L) 2pi s(q-Ls) ds = pi q^3/(3L^2).
```

Finite Gaussian mixtures are continuous and vanish at infinity, so a nonzero absolute maximum is attained; the zero case is immediate. T44's stored U3 gives `||r||_1<=b1=min(2,sqrt(2 U3))`. Thus the ordinary pointwise bound is

```text
E_K=min(1/(2pi lambda),(3 L^2 b1/pi)^(1/3)).
```

The same physical and transmittance conversion as PROOF.md applies. Preparation needs U3 and m, both O(k); a current query needs only constant-dimensional matrix work and two retained scalars. This bound is generally coarse and does not itself vanish with H, although the exact H=0 check can return zero. It still refutes the claim that ordinary KL metadata can only ever serve an integrated contract once the same quantitative covariance floor is supplied. Replacing U3 with a reevaluated U2 gives another valid bound at O(k) query cost. Neither KL quantity is exact mixture KL.

The cone conversion is not the strongest ordinary smoothness bound. For one Gaussian, `||Hessian phi||_op<=1/(2pi lambda^2)`: in whitened coordinates the factor is bounded by `max(1,|t^2-1|) exp(-t^2/2)<=1`. Thus `||Hessian r||_op<=K2=1/(pi lambda^2)`. At an absolute maximum the gradient is zero. Integrating the positive paraboloid `q-K2 ||y-y0||^2/2` gives `||r||_1>=pi q^2/K2`. Another same-cost ordinary bound is therefore

```text
E_K2=min(1/(2pi lambda),sqrt(b1)/(pi lambda)).
```

All valid ordinary bounds may be combined by taking their minimum. No claim of optimality is made for this finite comparison.

## Ordinary overlap admits a pointwise certificate too

An unmodified L2 density metric is not a pointwise metric. A valid conversion is available using the same floor. Let `K=(lambda/2) I2`; subtract K from every projected component covariance and from S_g to define normalized `f_tilde,g_tilde`. The covariances remain positive definite and the moment relation remains valid. Gaussian convolution gives

```text
r=phi_K*(f_tilde-g_tilde),
||r||_infinity <= ||phi_K||_2 ||f_tilde-g_tilde||_2
               = sqrt(ISE_tilde/(2pi lambda)).
```

Here ISE_tilde is the exact squared L2 Gaussian-overlap expression from T44, evaluated on these reduced covariances; `||phi_K||_2^2=1/(4pi sqrt(det K))=1/(2pi lambda)`. This ordinary bound is O(k^2) in general, O(1) for binary groups, and exactly zero at an initial common footprint. It requires component access and may suffer cancellation in floating-point overlap evaluation. This is not a claim about a measured practical implementation.

## Generic derivative bounds already share the reuse mechanism

The ordinary first-order parameter integral, without moment cancellation, yields

```text
E_1=C1 H M100+(C2/2)(beta M010+gamma M001).
```

Three additional first absolute moments suffice, and preparation/query costs are O(k)/O(1). It vanishes at H=0, but generally only as O(H). T45 obtains a higher-order envelope by applying ordinary second-order Taylor expansion and using the moment identities. An equally informed generic Taylor/interval method can use precisely that expansion and the fifteen statistics. It must not be forced to use E_1 or an integrated metric while the proposal receives the cancellations. No different update, representation or complexity class has been established by renaming this derivation as a new guard.

Binary groups can directly project their two children and apply ordinary formulas at fixed cost. The O(k)-to-O(1) query statement is relevant only to variable-size groups with amortized preparation, and is shared by generic retained-statistic bounds. It is not a whole-scene speedup.

## The prescribed covariance floor can hide useful view information

Use the already analyzed symmetric subfamily of T44, not a new scene or run:

```text
Sigma_i=diag(s^2,s^2,epsilon^2),
z_i=+/-a with equal weights,  a=sqrt(V-epsilon^2),
0<epsilon<min(s,sqrt(V)),  F=I,
P_theta=[[cos theta,0,sin theta],[0,1,0]].
```

The prescribed floor is `lambda=epsilon^2`, whereas the actual component projected covariance is

```text
diag(s^2 cos^2 theta+epsilon^2 sin^2 theta,s^2).
```

For any fixed `0<|theta|<pi/2`, it stays bounded away from zero as epsilon tends to zero. Here `B_i=0`, `Z_i=a`, `J_i=a^2`. The positive E_T formula contains

```text
(2/3) C3(epsilon^2) a^3 |sin theta|^3.
```

It therefore diverges as epsilon tends to zero. The additional peak cap also diverges. For fixed positive kappa M the transmittance certificate becomes the trivial bound one, although the actual projected distributions remain well conditioned. To check the actual small-angle order without numerical evaluation, let `u=a sin(theta)e_x` and let S be the displayed component covariance. Symmetric mean expansion through order three gives `f=phi_S+(u.grad)^2 phi_S/2+R_f` with `|R_f|<=C4(ell)||u||^4/24`. A first-order covariance expansion of `g=phi_(S+u u^T)` gives the same two terms and `|R_g|<=C4(ell)||u||^4/8`. Both paths have the actual lower floor `ell=s^2 cos^2(theta)`. Hence

```text
||f-g||_infinity <= C4(ell) a^4 sin^4(theta)/6.
```

For a fixed cone `|theta|<=theta0<pi/2`, ell is uniformly positive and `a<=sqrt(V)`. The actual error therefore tends uniformly to zero as theta tends to zero, uniformly in small epsilon. The ordinary binary comparison has no growing-k query penalty in this inherited family.

This diagnoses a tightness problem of the chosen floor and absolute-moment construction. It is not a no-go theorem for every retained record: tighter directional matrix bounds or direct component checks may avoid it. This task does not silently replace its floor, add a second candidate variant or initiate a tuned benchmark. The failure of a sufficient certificate is not a failure of the rendered approximation.

## Complete cost and applicability ledger

| Item | Required accounting |
|---|---|
| Find groups | Not provided by this theorem. Exact common projected means/covariances must be established. Checking a known group is O(k); discovering many useful groups has separate cost. Near equality needs an additional residual contract. |
| Prepare a known group | A first pass obtains weighted means, variance, merged covariance and m; a second pass obtains the fifteen centered absolute moments. Fixed dimension and degree make total work O(k). Stable accumulation is not implemented. |
| Retain metadata | Sixteen extra real scalars plus the reference frame and ordinary merged Gaussian/mass. The frame may be shared across groups. With a chosen 64-bit scalar encoding the sixteen scalars alone would use 128 bytes, excluding alignment, hierarchy, renderer and rounding metadata; no actual memory saving is measured. |
| Current query | Fixed-size Q/A/h operations, a 2x2 minimum eigenvalue, norm and powers, and fifteen-term statistics. O(1) per known group in exact-real operation counting; accepted groups still need rendering. |
| Repeated motion | Only common invertible affine pushforward with fixed weights/mass/extinction. Component-specific/nonlinear changes need recomputation or invalidation. A single-time evaluation is not a continuous-motion certificate. |
| Refinement/unmerging | Rejected destructive merges cannot recover children. A hierarchy retaining children still pays their parameter and metadata storage; rejecting groups pays traversal, child evaluation and possible projection/rendering. No fine-memory removal is established. |
| Ordinary methods | U3+floor pointwise bound: O(k) setup/O(1) query; U2: O(k) query; smoothed overlap: O(k^2) general/O(1) binary query; generic Taylor can reuse the same record and formula. Include all setup, invalidations and rejected checks for every method. |
| Scene/accuracy | Arbitrary RGB, perspective, clipping, approximate initial footprints and real creator requirements remain unqualified. Summing group error bounds can become too conservative; no accepted-group rate, visual quality or speed was measured. |

The exact construction therefore passes the finite-mathematics question but does not establish a distinct useful cost/accuracy opportunity. Its record, useful regimes and ordinary alternatives have to be assessed together. No implementation or numerical queue is selected from this task.
