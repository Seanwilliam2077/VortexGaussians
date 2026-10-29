# T44 — view drift, discarded information and an ordinary reusable bound

All new derivations here concern exact real arithmetic, positive normalized Gaussian-mixture weights and positive-definite covariances. Physical density is M times the probability density, with a common constant extinction per unit mass kappa. Optical depth uses complete orthographic rays. This is not a conversion of learned splat opacity into physical mass, or a claim about arbitrary colored emission.

## 1. Common-footprint cancellation is first-order, not generally fourth-order

Let Q(t)=P(t)F(t), where P has orthonormal image-plane rows and F is a common invertible affine linear part. Translation is common and immaterial to the difference. The fine projected mixture and the projection of its ordinary moment merge are

```text
f_t(y)=sum_i w_i phi_2(y; a_i(t),S_i(t)),
a_i=Q mu_i,                 S_i=Q Sigma_i Q^T,
a_bar=sum_i w_i a_i,
S_bar=sum_i w_i [S_i+(a_i-a_bar)(a_i-a_bar)^T],
g_t(y)=phi_2(y; a_bar,S_bar).
```

At t=0 assume a_i=a0 and S_i=S0 for all components; let phi be that common density. Moment matching commutes with the shared affine map. Write

```text
u_i = a_i'(0) - sum_j w_j a_j'(0),
V_i = S_i'(0) - sum_j w_j S_j'(0).
```

For smooth Q and a neighborhood with uniformly positive projected covariances, Gaussian parameter differentiation gives

```text
f_t-g_t = t^2 [
  -(1/2) sum_i w_i (u_i tensor V_i):grad^3
  +(1/8) sum_i w_i (V_i tensor V_i):grad^4
] phi + O(t^3).
```

Here the tensor contractions mean full contractions with the symmetric spatial derivative tensors. To see the cancellation, the first parameter derivative is `-a':grad+(1/2)S':grad²`. Its weighted first-order term matches the merged derivative. At second order the mean-mean term is canceled by the between-mean contribution to S_bar; the mean-covariance and covariance-covariance terms remain with the coefficients shown. Mean/covariance second derivatives otherwise average identically. Thus both the initial error and its first derivative vanish. This is a local expansion, not a finite-step bound.

A concrete positive-definite family has

```text
mu_i=z_i e_z,
Sigma_i=[[s²,0,b_i],[0,s²,0],[b_i,0,d_i²]],   b_i²<s² d_i²,
P_theta=[[cos(theta),0,sin(theta)],[0,1,0]].
```

All initial footprints are N(0,s² I_2). Projected x means are z_i sin(theta), and x variances are `s² cos²(theta)+2 b_i sin(theta)cos(theta)+d_i² sin²(theta)`. Therefore

```text
f_theta-g_theta = theta² [
  -Cov_w(z,b) partial_x³ +(1/2)Var_w(b) partial_x⁴
] phi + O(theta³).
```

In particular, equal weights with z=0, d²=s² and b_i=±b, 0<|b|<s², give `(b² theta²/2) partial_x⁴ phi+O(theta⁴)`. The merged 3D covariance is s² I, yet the error is already second order. If all component covariances instead equal s² I and only centered depths differ, the leading term is `-mu3 theta³ partial_x³ phi/6`, where mu3 is their third central moment. Symmetric equal-weight depths ±a remove that term and give `-a⁴ theta⁴ partial_x⁴ phi/12+O(theta⁶)`. That special fourth-order cancellation cannot be generalized to varying cross-covariance.

These are density-error orders, also orders of its L2 norm when the displayed coefficient is nonzero. Squared L2 errors have twice the order. Multiply density differences by kappa M for optical depth. No numerical example was evaluated.

There is a useful exact ordinary guard. If n0 is the initial ray direction and `Q(t)n0=0` throughout a reuse interval, then `Q(t)=A(t)P0`. Identical initial projected distributions remain identical, so the merge remains exact. Checking the current fixed-dimensional equality costs O(1); verifying it for an entire arbitrary motion path is not implied by one sampled check. Only `Q'(0)n0=0` does not establish an interval guarantee.

## 2. Mechanical moments do not identify later optical images

Fix M,s,V>0, choose 0<epsilon<sqrt(V), and put `a=sqrt(V-epsilon²)`, `S_epsilon=diag(s²,s²,epsilon²)`. Compare the probability densities

```text
p_A = (1/2) N(+a e_z,S_epsilon)+(1/2) N(-a e_z,S_epsilon),
p_B = (1/2) N(0,S_epsilon)
      +(1/4) N(+sqrt(2)a e_z,S_epsilon)
      +(1/4) N(-sqrt(2)a e_z,S_epsilon).
```

Both have mean zero and covariance `Sigma=diag(s²,s²,V)`, independent of epsilon. Assigning the same affine velocity b+Cx also makes their total momenta and velocity-position cross moments identical. Along z their complete optical-depth images are exactly the same `kappa M phi_s(x)phi_s(y)`, equal to the moment-merged Gaussian.

After a common 90-degree rotation about y, or a side-view camera change, their optical depths at the side-view origin differ by

```text
tau_B-tau_A = [kappa M/(4 pi s epsilon)]
             [1-exp(-(V-epsilon²)/(2 epsilon²))]² -> infinity.
```

Their retained mechanical state and initial full image stay fixed. Any deterministic reconstruction using only those retained quantities gives the same output for both and errs by at least half their difference on one. There is no finite uniform later-view optical-depth pointwise bound from that state alone without extra scale/shape restrictions. This is a symbolic information boundary, not an executed scene or a claim that every small view cone is unbounded.

In the narrower constant-white-source, black-background model `C=1-exp(-tau)`, side-view center values tend to 0 and 1 respectively. RGB is bounded; this is not unbounded RGB error, nor evidence about finite-pixel averages or perceptual image quality. Keeping fine optical state is an ordinary remedy, but the following scalar is another option for a different, integrated error metric.

## 3. A retained ordinary KL bound already survives common affine motion

For normalized p=sum_i w_i N(mu_i,Sigma_i) and its moment Gaussian g=N(mu,Sigma), convexity in the first KL argument gives

```text
D(p||g) <= sum_i w_i D(N_i||g)
         = U3 = (1/2)[log det Sigma - sum_i w_i log det Sigma_i].
```

The Gaussian KL trace and mean terms sum to the dimension because Sigma is the total second central moment; they cancel the dimension term. Logs are natural. The inexpensive moment-merge KL criterion is established prior work; see [the source record](SOURCES.md). The multi-component algebra and optical interpretation here are explicitly derived, not a priority claim.

Apply the same invertible affine map to both densities with mass-preserving pushforward: `rho_F(x)=rho(F^-1(x-b))/|det F|`. KL and U3 are invariant because each log determinant gains the same `2 log|det F|`. Projection cannot increase KL. Pinsker in L1 form and the probability-density bound L1<=2 then give, for any orthographic P,

```text
||p_projected-g_projected||_1 <= min(2,sqrt(2 U3)),
||tau_p-tau_g||_1            <= kappa M min(2,sqrt(2 U3)),
||exp(-tau_p)-exp(-tau_g)||_1 <= kappa M min(2,sqrt(2 U3)).
```

The last step uses the 1-Lipschitz property of exp(-x) on x>=0. These norms integrate over physical image-plane area. Thus U3 can be computed in O(k) fixed-dimensional work for an already known group and stored as one scalar. It needs no framewise update under the stated shared affine motion and view changes. Keeping Gaussian peak amplitude fixed while changing covariance is not this mass-preserving map. Component-dependent deformations, Gaussian closure under nonlinear flow, burning/source terms and changing kappa are not covered by this reuse argument.

If B denotes the displayed transmittance bound, a finite image region of area A has integrated error at most min(A,B) and mean absolute error at most min(1,B/A). A pixel area a_pix similarly gives only min(1,B/a_pix) for its average; this is not a pointwise guarantee. The metric can be too weak for a useful pixel tolerance. The full 3D L1 argument can also handle a common bounded clipping mask, but the full-line projected criterion below cannot be transferred to arbitrary clipping without analysis. No clipped-ray task is developed here.

At a specific view define S_i=P F Sigma_i F^T P^T and S_g=P F Sigma F^T P^T. The ordinary projected bound

```text
U2 = (1/2)[log det S_g - sum_i w_i log det S_i]
```

is the sum of projected component-to-merge KL values. Componentwise data processing gives U2<=U3; U2 is not exact mixture KL. Its full-line L1 bound can be tighter and is zero at a common-footprint view, but direct reevaluation accesses k projected components. In the indistinguishable family above U3=(1/2)log(V/epsilon²) for both inputs. That scalar cannot identify which later image is correct, yet conservatively exposes risk. It is extra information not recoverable from the fixed mechanical moments.

## 4. Exact ordinary overlap and the unresolved finite guard

For projected normalized Gaussians,

```text
<phi_i,phi_j> = phi_2(a_i; a_j,S_i+S_j),
||f-g||_2² = sum_ij w_i w_j <phi_i,phi_j>
             -2 sum_i w_i <phi_i,g> + <g,g>.
```

This exact real-arithmetic density metric needs O(k²) pair terms in general, plus projections/moments. A binary merge is already fixed cost; do not make its ordinary evaluation artificially quadratic in the full scene. L2 density error is not automatically pointwise transmittance or arbitrary RGB error. Near-cancellation of overlap terms, log determinants and nearly singular covariance matrices needs numerical treatment in implementations.

The local Taylor coefficients can be stored as drift indicators, but lack a finite-step remainder. A genuinely useful remaining question is whether moment cancellation yields a conservative pointwise bound from constant-size retained statistics over a finite view change, at a cost and tightness that matter against the ordinary U3/U2 and overlap alternatives. [The next finite analysis](NEXT_EVIDENCE.md) states that question precisely. It selects no numerical experiment or accepted method. Retaining a hierarchy for later unmerging also costs storage; a guard cannot reconstruct irreversibly discarded detail.
