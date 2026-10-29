# A finite, uniform pointwise bound with a fixed-size record

This is exact-real mathematics for the model and single construction fixed in [T44 NEXT_EVIDENCE](../t44-view-change-merge-screen/NEXT_EVIDENCE.md). No numerical evaluation was performed. A valid formula is not a novelty, floating-point or practical-performance certificate.

## Model and projected parameter segment

Let positive weights sum to one. In a stored orthonormal frame `(P0,n0)`, component means and SPD covariances have the common initial footprint

```text
mu_i=(a0,z_i),    Sigma_i=[[S0,b_i],[b_i^T,d_i]],
```

where d_i is a variance. The ordinary moment Gaussian has mean `(a0,z_bar)` and covariance `[[S0,b_bar],[b_bar^T,d_bar+v_z]]`, with `v_z=E_w (z_i-z_bar)^2`. All symbols below refer to this original reference frame; a common invertible affine map F and an orthographic camera P enter through `Q=P F`. Common translation cancels the density difference. Put

```text
A=Q P0^T,  h=Q n0,  H=||h||_2,  a=||A||_op,
xi_i=h(z_i-z_bar),
Delta_i=A(b_i-b_bar)h^T+h(b_i-b_bar)^T A^T
        +(d_i-d_bar-v_z)hh^T.
```

The projected component is `phi_i(y)=phi_2(y;a_g+xi_i,S_g+Delta_i)`, and the projected moment merge is `g(y)=phi_2(y;a_g,S_g)`. Direct averaging gives

```text
E_w xi_i=0,       E_w(Delta_i+xi_i xi_i^T)=0.
```

Define `m=min_i lambda_min(Sigma_i)>0` and `lambda=m lambda_min(Q Q^T)>0`. Every `S_i=Q Sigma_i Q^T` is at least `lambda I`. The merged 3D covariance is at least m I because it is the average component covariance plus a positive-semidefinite between-mean term; hence S_g has the same floor. The entire straight parameter segment

```text
psi_i(t,y)=phi_2(y;a_g+t xi_i,S_g+t Delta_i),    0<=t<=1,
```

therefore has covariance at least `lambda I`. The segment need not describe the physical motion: it interpolates two distributions at the current query. The bound does not require a small angle or a bound on motion derivatives. A whole time interval still requires controlling the bound over that interval, not sampling one time.

## Uniform Gaussian derivative constants

For any 2D Gaussian with covariance S at least `lambda I`, Fourier inversion gives

```text
phi_2(y;mu,S)=(2pi)^(-2) integral exp(i omega.(y-mu))
                                     exp(-omega^T S omega/2) d omega.
C_n(lambda)=(2pi)^(-2) integral ||omega||^n exp(-lambda||omega||^2/2) d omega
           =2^(n/2) Gamma((n+2)/2)/(2pi lambda^((n+2)/2)).
```

The radial integral is over the entire plane, including every Gaussian tail. If `L_x=-xi.grad` and `L_D=Delta:grad^2`, then for nonnegative integers r,j,

```text
sup_y |L_x^r L_D^j phi_2(y;mu,S)|
  <= ||xi||^r ||Delta||_op^j C_(r+2j)(lambda).
```

This follows directly from `|omega.xi|<=||omega|| ||xi||` and `|omega^T Delta omega|<=||Delta||_op ||omega||^2`; no nuclear-norm or component-count factor is needed. In particular,

```text
C3=3/(2 sqrt(2pi) lambda^(5/2)),    C4=4/(pi lambda^3),
C5=15/(2 sqrt(2pi) lambda^(7/2)),   C6=24/(pi lambda^4).
```

These constants are sufficient uniform envelopes, not claimed optimal constants.

## Exact cancellation and finite remainder

Parameter differentiation along the segment is the constant spatial operator

```text
D_i=-xi_i.grad+(1/2)Delta_i:grad^2,
partial_t^j psi_i=D_i^j psi_i.
```

Taylor's integral formula at t=0, evaluated at t=1, is exactly

```text
phi_i = g+D_i g+(1/2)D_i^2 g
          +(1/2) integral_0^1 (1-t)^2 D_i^3 psi_i(t) dt.
```

In the weighted sum, the first derivative's covariance term is `-(1/2)E_w(xi_i xi_i^T):grad^2 g`. It cancels the mean-mean term from the second derivative. The mean first derivative is zero. Consequently, for `f=E_w phi_i`,

```text
f-g = -(1/2) E_w(xi_i tensor Delta_i):grad^3 g
       +(1/8) E_w(Delta_i tensor Delta_i):grad^4 g+R,
R=(1/2) E_w integral_0^1 (1-t)^2 D_i^3 psi_i(t) dt.
```

All tensor products are fully contracted with the symmetric derivative tensor. Let `r_i=||xi_i||` and `delta_i=||Delta_i||_op`. Since the integral of `(1-t)^2/2` is 1/6, the Fourier envelopes imply

```text
sup_y |f(y)-g(y)| <=
 (C3/2) E_w(r_i delta_i)+(C4/8) E_w(delta_i^2)
 +(1/6) sum_(j=0)^3 binom(3,j) C_(3+j)/2^j
                              E_w(r_i^(3-j) delta_i^j).
```

This is a finite-step inequality, not the T44 local asymptotic expansion. It holds for each finite Q with positive lambda, for every image-plane position.

## Fifteen retained moments suffice

Define nonnegative reference-frame scalars

```text
Z_i=|z_i-z_bar|,
B_i=||b_i-b_bar||_2,
J_i=|d_i-d_bar-v_z|,
M_pqr=E_w Z_i^p B_i^q J_i^r.
```

Here J is a scalar magnitude, not an operator. Set `beta=2 a H` and `gamma=H^2`. The elementary matrix norm inequality gives

```text
r_i=H Z_i,       delta_i<=beta B_i+gamma J_i.
```

Only these fifteen moments occur:

```text
degree 2: M110, M101, M020, M011, M002;
degree 3: M300, M210, M201, M120, M111, M102,
          M030, M021, M012, M003.
```

With C_n evaluated at lambda, define the directly evaluable scalar

```text
E_T = (C3/2) H (beta M110+gamma M101)
      +(C4/8)(beta^2 M020+2 beta gamma M011+gamma^2 M002)
      +(1/6) sum_(j=0)^3 [binom(3,j) C_(3+j)/2^j H^(3-j)
          * sum_(l=0)^j binom(j,l) beta^l gamma^(j-l) M_(3-j,l,j-l)].
```

The finite double sum has ten terms. Substitution into the previous inequality proves `sup_y|f-g|<=E_T` with no component access at query time. Powers with exponent zero mean one, including at H=0. Every term has a positive total power of H, so E_T=0 there; the shared-footprint exactness is recovered. For H near zero with bounded A and a covariance floor bounded away from zero, E_T is O(H^2). If all B_i are zero it is O(H^3) in general. Absolute moments lose signed cancellations: a symmetric mean pair's actual fourth-order error is not automatically retained by this bound.

Nonnegative normalized f and g each have peak at most `1/(2pi lambda)`. Their difference is bounded by that same peak, not twice it. Thus a further valid density bound is

```text
E=min(E_T,1/(2pi lambda)).
```

The fifteen moments plus m are sixteen extra real scalars, in addition to the initial frame and ordinary merged state. This is a sufficient record, not a minimality theorem. Raw component values are used only during preparation. The three degree-one moments needed by a lower-order ordinary comparison are optional extra metadata, not secretly used in E_T.

## Optical meaning and limits

For fixed group mass M and extinction per mass kappa, complete orthographic ray integration gives `tau_f=kappa M f` and `tau_g=kappa M g`. Therefore pointwise optical-depth error is at most `kappa M E`. Since exp(-x) is 1-Lipschitz on nonnegative x,

```text
sup_y |exp(-tau_f)-exp(-tau_g)| <= min(1,kappa M E).
```

The same bound applies to finite-pixel averages and the constant-white-source/black-background output `1-exp(-tau)`. It does not certify arbitrary differently colored emission, perspective, truncated rays or a learned opacity-to-mass conversion. For independent groups, optical-depth errors can be summed conservatively before the transmittance Lipschitz bound; this does not prove any scene-level acceptance rate or reduction in drawing cost.

Common nonlinear/component-specific motion, changes to mass/weights/extinction, or edits to component parameters invalidate the unchanged record. Re-forming it costs work. Near singularity the formula remains finite for fixed positive lambda but may be uselessly large. Floating-point certification would require directed rounding or verified envelopes for eigenvalues, moments, powers and sums; none is implemented here. Shared exact real identities do not establish GPU stability or speed.
