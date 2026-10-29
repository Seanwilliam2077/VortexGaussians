# T49 — separate projection metric and Gaussian envelope

This is an ordinary Fourier-characteristics calculation for a prescribed common affine velocity. It repairs the specific affine/heat closure boundary recorded in T48 by retaining independent projection and envelope matrices. It is not a new evaluator algorithm, a novelty result, a numerical qualification, or an existing-code defect. Only T48 CARRIER and DECISION were read for this derivation; no external sources, scientific execution or implementation were used.

## State and prescribed equation

Let M and C be symmetric positive-definite matrices, c a vector coefficient and mu a center. Define, for k != 0,

```text
Q_M(k) = I - M k k^T/(k^T M k),
omega_hat(k) = Q_M(k)c exp(-k^T C k/2) exp(-i k^T mu).
```

The field is solenoidal because k^T Q_M=0. Setting M=C=Sigma recovers exactly T48's field; positive rescaling of M has no effect. This is the same-field relationship, not replacement by the simpler raw-source Biot–Savart model.

Assume a prescribed v(x,t)=A(t)x+b(t), trace A(t)=0, on R³, and constant viscosity nu>=0. The equation considered is

```text
partial_t omega + (v dot grad)omega = A(t)omega + nu Delta omega.
```

It is a linear transport/stretching/diffusion equation once v is prescribed. Sufficient regularity of A,b on the finite interval is assumed so that the fundamental matrix exists. No boundary is present. Exact state equations are

```text
Mdot  = A M + M A^T,
Cdot  = A C + C A^T + 2 nu I,
cdot  = A c,
mudot = A mu + b.
```

In particular, pure heat changes C only; pure affine transport applies the same congruence to both matrices. The equations describe their simultaneous action, not an assumption that affine transport and isotropic heat commute.

## Characteristics and joint exact solution

Let Fdot=A(t)F, F(0)=I, and Phi(t,s)=F(t)F(s)^(-1). Trace A=0 gives det F=1. With the Fourier convention grad -> i k, the PDE becomes

```text
partial_t omega_hat - (A^T k) dot grad_k omega_hat
  = A omega_hat - [nu |k|² + i b dot k] omega_hat.
```

Along kdot=-A^T k, the quantity q=F(t)^T k(t) is constant. The vector stretch is F(t), the scalar attenuation is exp[-nu integral_0^t |k(s)|² ds], and translation contributes its usual phase. The identity

```text
F Q_(M0)(F^T k) = Q_(F M0 F^T)(k) F
```

therefore preserves the stated form. Explicitly,

```text
M(t)  = F(t) M0 F(t)^T,
C(t)  = F(t) C0 F(t)^T
        + 2 nu integral_0^t Phi(t,s) Phi(t,s)^T ds,
c(t)  = F(t)c0,
mu(t) = F(t)mu0 + integral_0^t Phi(t,s)b(s) ds.
```

The quadratic form of the added covariance is exactly the heat attenuation along the Fourier characteristic. Differentiating these expressions gives all four ODEs above. M remains positive definite; C is a positive-definite congruence plus a positive-semidefinite term. No commutation of A at different times is required: F is the actual fundamental matrix, not exp(integral A) unless the needed commutation holds.

This proves finite-state closure for the joint prescribed equation. Exact affine and heat substeps also remain in the family, but a chosen finite operator splitting need not equal the joint solution. The covariance integral, or its equivalent ODE, is what captures their simultaneous action.

## Redundancy and normalization

Q_(a M)=Q_M for every scalar a>0. The symmetric records therefore contain eighteen stored scalars (6+6+3+3) but seventeen effective generic parameters absent other restrictions. One may fix det M=1; the representative ODE already preserves det M because trace A=0. A time-dependent positive rescaling is another equivalent gauge, with an added scalar multiple of M in its ODE. The displayed Mdot selects a convenient representative, not a unique matrix history for the field.

The Gaussian factor is normalized. No amplitude/Jacobian term is missing from cdot because the prescribed transport preserves volume. The coefficient c remains a raw-source parameter, not an ordinary total-vorticity integral. The zero field has further trivial parameter degeneracies. Ordinary M-scale redundancy does not authorize dropping M's anisotropic shape or setting M=C after heat diffusion.

## Real-space meaning and tails

Let h_(M,C) solve

```text
-div(M grad h_(M,C)) = G_C,
omega = c G_C + M [Hess h_(M,C)] c.
```

Equivalently h_hat=exp(-k^T C k/2)/(k^T M k). Its ordinary heat representation uses G_(C+2rM) integrated over r>=0. For independent matrices it is not automatically T48's radial erf potential in one whitened coordinate.

Writing z=x-mu and rho²=z^T M^(-1)z, the leading far field is

```text
[3 z (z^T M^(-1)c)/rho^5 - c/rho^3]
/ [4 pi sqrt(det M)].
```

It follows from the unit-mass Gaussian convolved with the anisotropic elliptic Green function. The envelope affects smoothing and, generically, subleading algebraic terms; T48's exponentially small radial correction must not be imported without its matched-matrix condition. A nonzero carrier still has an O(|z|^(-3)) tail, is not absolutely L1-integrable, and has no ordinary absolutely convergent total-vorticity integral. Its smooth vorticity and Euclidean Biot–Savart velocity remain L2. Gaussian-distance culling, compact support, and a physical zero-mode convention remain unqualified.

## Ordinary velocity integral structures

The Euclidean Biot–Savart velocity has the exact symbol

```text
u_hat(k) = i [ (k cross c)/|k|²
              - (k cross M k)(k dot c)/(|k|² k^T M k) ]
           exp(-k^T C k/2) exp(-i k^T mu).
```

Keeping both terms is necessary for this same field. The first denominator has the usual one-parameter Laplace/heat representation. The product denominator in the second term has the ordinary representation

```text
1/[|k|²(k^T M k)]
  = integral_0^infinity integral_0^infinity
      exp[-a |k|² - r k^T M k] da dr.
```

After multiplication by the Gaussian, its covariance is C+2aI+2rM. Thus a direct available heat representation has one integration parameter for the first term and two for the correction; velocity and its spatial Jacobian use derivatives of these kernels. Derivatives must be taken before treating the double-potential integral as a finite object: the undifferentiated double inverse is not itself a convergent scalar potential integral in three dimensions, whereas the required derivatives admit convergent integrals.

T48's one-dimensional reduction used its matched envelope/metric structure. Independent C removes that immediate proportional structure. This establishes the dimension of the representation just displayed, not a lower bound on all possible formulas or proof that a one-dimensional reduction is impossible. No new quadrature, coordinate optimization, numerical order, cost measurement or evaluator implementation is proposed here. Ordinary reductions and exact special cases remain available to every comparator.

## Physical and research scope

The prescribed velocity is not required to equal the Biot–Savart reconstruction of this field; the derivation does not impose that equality or omega=curl v. Hence it is not a self-consistent Euler or Navier–Stokes solution. A generic finite carrier field does not reproduce a globally affine velocity. Obtaining the advecting velocity, deformation, boundaries and interactions remains a separate problem.

A sum of carriers under the same A,b,nu obeys the same linear equation exactly. Assigning separate local A_i or flow maps keeps the separately represented terms solenoidal but does not establish one common fluid motion on their overlapping tails. Non-affine transport introduces additional dependence not covered by these finite ODEs.

The result repairs T48's specific state coupling by ordinary second-matrix bookkeeping and Fourier characteristics. It does not identify a defect in an existing scalar-core implementation, establish equivalence to another representation family, or distinguish a new method from the same-state ordinary reference. Full reconstruction cost, useful task evidence, non-affine evolution accuracy and any practical advantage remain unmeasured. No numerical task follows automatically.
