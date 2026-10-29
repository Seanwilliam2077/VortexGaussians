# Velocity regression residual: exact state loss, ordinary moment repair

This is an exact-real calculation for a declared joint distribution of position and velocity. It is not a measurement of the current VPM demo, a statement that its rendering covariance represents physical mass, or a new closure claim. The [local model check](LOCAL_MODEL.md) and [source screen](SOURCES.md) keep those distinctions explicit.

## Joint state and the ordinary affine merge

Let `(X,U)` be random position/velocity with finite second moments, normalized positive mass weights and total mass M. Define

```text
mu=E X,  v=E U,
S=Cov(X)>0,   B=Cov(U,X),   V=Cov(U),
C=B S^(-1),   E_res=U-v-C(X-mu).
```

The inverse denotes a linear solve. Direct calculation gives `E E_res=0`, `Cov(E_res,X)=B-CS=0` and

```text
R=E[E_res E_res^T]=V-B S^(-1) B^T >= 0.
```

This is the linear-regression residual covariance or the Schur complement of S in the joint covariance. The identity needs no Gaussian assumption. For a general joint law, R is not necessarily the conditional covariance at a particular x; it becomes the constant conditional covariance for a joint Gaussian. Calling it a local physical pressure tensor before specifying that model would be premature.

Under T43's component model,

```text
X|i ~ N(mu_i,Sigma_i),
U|X,i = v_i+C_i(X-mu_i),
```

the previously retained S/B and the missing V are

```text
S=E_w[ Sigma_i+(mu_i-mu)(mu_i-mu)^T ],
B=E_w[ C_i Sigma_i+(v_i-v)(mu_i-mu)^T ],
V=E_w[ C_i Sigma_i C_i^T+(v_i-v)(v_i-v)^T ].
```

Writing `e_i=v_i-v-C(mu_i-mu)` yields a nonnegative decomposition

```text
R=E_w[ (C_i-C)Sigma_i(C_i-C)^T+e_i e_i^T ].
```

With positive weights and each Sigma_i positive definite, R=0 if and only if every `C_i=C` and `v_i=v+C(mu_i-mu)`. Thus all components must share one global affine velocity almost everywhere. For singular input covariances only the occupied subspaces are constrained; the stronger equality assertion must not be imported unchanged.

The ordinary merged Gaussian `X_g~N(mu,S)` with deterministic velocity `U_g=v+C(X_g-mu)` preserves mass, spatial mean/covariance and B. As T43 shows, these preserve total linear and angular momentum about the same origin. They do not preserve all of V.

## Kinetic energy needs a declared interpretation

For the component-label joint law, the original and merged kinetic energies satisfy

```text
K_joint=(M/2)(||v||^2+tr V),
K_affine=(M/2)(||v||^2+tr(B S^(-1) B^T)),
K_joint-K_affine=(M/2)tr R >= 0.
```

For the stated SPD component model, equality holds precisely under the common affine-velocity condition above. This is a well-defined loss of phase-space kinetic second moment, compatible with retained total momenta. It does not establish actual numerical dissipation in a solver that never performs this merge.

If overlapping components instead represent one macroscopic velocity `u_bar(x)=E[U|X=x]`, its kinetic energy is

```text
K_macro=(M/2)E ||u_bar(X)||^2,
K_joint-K_macro=(M/2)E tr Cov(U|X).
```

The regression residual decomposes as

```text
R=E Cov(U|X)
  +E[(u_bar(X)-v-C(X-mu))(u_bar(X)-v-C(X-mu))^T].
```

The first term is conditional multistream dispersion; the second is the single-velocity field's departure from its best affine fit. They have different meanings. R is not automatically heat, combustion energy, turbulence or pressure in the demo. In particular, the label-based energy loss can be positive when the macroscopic velocity field has zero kinetic energy.

## Free streaming exposes the missing spatial evolution exactly

Specify the dynamics before comparing representations:

```text
X(t)=X+t U,   U(t)=U.
```

This means velocity is constant along each trajectory. It is not repeatedly evaluating a frozen Eulerian affine field; that different ODE would involve a matrix exponential. Under the stated free streaming,

```text
mu(t)=mu+t v,
S(t)=S+t(B+B^T)+t^2 V,
B(t)=B+t V,     V(t)=V.
```

For the deterministic affine merge propagated with its own constant trajectory velocities,

```text
S_g(t)=(I+tC)S(I+tC)^T
      =S+t(B+B^T)+t^2(V-R).
```

Therefore

```text
S(t)-S_g(t)=t^2 R,
B(t)-B_g(t)=t R,
V(t)-V_g(t)=R.
```

These are finite-time identities, not truncated expansions. At nonzero t, full spatial covariances agree exactly if R=0; an individual orthographic projection only tests `P R P^T`. Under the normalized-density/full-line optical model, the projected optical-depth second-moment difference is `kappa M t^2 P R P^T` because means and total mass match. This does not quantify RGB or perceptual error.

Covariance identities remain meaningful if `I+tC` is singular, but then the merged spatial Gaussian can become a degenerate measure. They do not promise a positive-definite render primitive at every time.

## Retaining six scalars restores ordinary second moments

Store symmetric V, or equivalently R in addition to S and B. The ordinary update

```text
dot S=B+B^T,   dot B=V,   dot V=0
```

reproduces all of the displayed free-streaming moments. An equivalent joint-Gaussian representation is

```text
X_g~N(mu,S),
U_g=v+C(X_g-mu)+eta,
eta~N(0,R), independent of X_g (a degenerate Gaussian is allowed).
```

This is an analytic distribution description; no sampling is required. If R is singular, it is a possibly degenerate Gaussian measure in phase space rather than a nonsingular six-dimensional density. Its joint covariance is

```text
Gamma=[[S,B^T],[B,V]].
```

A common linear phase-space flow propagates this covariance by ordinary matrix congruence. For `dot Z=L(t)Z+d(t)`, the mean and covariance obey `dot mean=L mean+d` and `dot Gamma=L Gamma+Gamma L^T`; the equations are exact second-moment equations for any initial law with finite moments when all components share that affine force model. They do not make a non-Gaussian mixture Gaussian or supply nonlinear forces/collisions.

For a single joint Gaussian under free streaming, while S(t) stays invertible, its conditional velocity is affine with `C(t)=B(t)S(t)^(-1)` and conditional covariance `R(t)=V-B(t)S(t)^(-1)B(t)^T`. Differentiating gives

```text
dot C=R S^(-1)-C^2,
dot R=-C R-R C^T.
```

These relations are consistent with the kinetic stress `rho R`: its mean-field acceleration is `-rho^(-1) div(rho R)=R S^(-1)(x-mu)` for a spatial Gaussian and spatially constant R. This explains why the conditional mean accelerates even though individual free-streaming velocities do not. It is not an incompressible pressure projection, and does not validate adding R to the existing smoke dynamics.

The retained global joint-Gaussian state and a local ten-moment gas closure are not the same discretization. The latter evolves local density, mean velocity and symmetric pressure tensor fields; the former stores position/velocity means and all their joint second moments per group. Both already use second-order velocity information. The [limited sources](SOURCES.md) establish that such information is standard, not that a particular modern graphics implementation has this exact record.

## A symbolic semantic check, not a new workload

Take two equal-weight components with the same `N(0,S)` spatial density and opposite constant velocities `+u` and `-u`, with nonzero u. Then `v=0`, `B=0`, `C=0`, `V=R=u u^T`. Initial spatial density and the macroscopic velocity field are identical to a stationary single Gaussian. Their macroscopic kinetic energy is zero, while the label-based joint kinetic energy is `(M/2)||u||^2`.

Under declared collisionless free streaming the fine density becomes two Gaussians centered at `+t u` and `-t u`; the affine merge remains stationary. Retaining R produces a Gaussian with covariance `S+t^2 u u^T`, matching second moments but generally not the two-lobe density. In a view with `P u=0` that distinction is hidden; a transverse view need not agree. This is a state-interpretation and higher-information limit, not an authored benchmark, fluid reference, perceptual finding or proof of a novel bottleneck. No numerical instance was evaluated.

## Full cost and research decision

For an already specified k-component group, forming V/R adds O(k) fixed-dimensional arithmetic and a 3x3 solve already needed for C. The extra symmetric record contains six real scalars; conditioning, accumulation and PSD validation in finite precision remain work. Query-time propagation of a single fixed-size joint covariance is O(1). Group discovery, spatial/optical approximation error, force evaluation, invalidation, rendering and retention of children for unmerging remain separate costs.

Ordinary methods may retain exactly S/B/V or a joint Gaussian, use richer transfer bases where applicable, or keep fine physical state independently of coarse optical state. They obtain the same free-streaming moments with the same information. No timing, storage win or accuracy advantage was measured. The existing repository's visual covariance, derived VPM velocities and temporary affine field groups do not instantiate this mechanical merge, as the four-file audit documents.

The screen therefore identifies a genuine loss within a specified model and an ordinary fix, but no distinct mechanism or matched practical task. No implementation or numerical queue is selected. This does not deny possible nonlinear/physical representation-transfer problems; it prevents this ordinary regression/second-moment identity from being relabeled as the missing TOG contribution.
