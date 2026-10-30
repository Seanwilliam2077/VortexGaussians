# T58 — ordinary solution of the existing separable FV system

This is an implementation qualification of an ordinary reference solver. It does not change the free-space axisymmetric model, the discrete source or boundary data, introduce a physical approximation, or propose a novel method. [T57's decision](../t57-finer-short-reference/DECISION.md) motivates the test after its budget failure. The fixture equations are those of the unchanged [T55 code](../t55-axisymmetric-reference/reference.py) and [T56 formulation](../t56-coupled-reference/FORMULATION.md).

## Original linear system

Let h be the uniform cell width, nr/nz the radial/axial counts, r_f=i*h the radial faces, W_i=(r_(i+1)^4-r_i^4)/4, L_i=r_i^3/(W_i*h) and U_i=r_(i+1)^3/(W_i*h). The radial operator has diagonal L_i+U_i, with an additional U_(nr-1) at the outer row, lower diagonal -L_i and upper diagonal -U_i. L_0=0 implements the axis. The axial operator has diagonal 2/h^2 except its two end entries 3/h^2, and off-diagonals -1/h^2. The endpoint additions encode half-cell Dirichlet faces through antisymmetric homogeneous ghosts.

The unchanged nonhomogeneous RHS is q with additions 2*U_last*gR at the outer radial row and 2*gminus/h^2, 2*gplus/h^2 at the first/last axial columns. The two outer corner values do not enter this five-point system; they are retained for the unchanged velocity/Jacobian reconstruction. No source or boundary matrix is recomputed from a different quadrature.

The evaluator independently applies this original operator using radial face flux differences and reflected/antisymmetric ghosts. It constructs the original RHS separately. It calls neither the candidate's transform nor its Thomas factors to evaluate the residual or manufacture the known RHS. The residual is the original RHS-relative weighted norm

    ||A*phi-b||_W / ||b||_W,
    ||v||_W^2 = sum_ij W_i*v_ij^2.

The common axial h factor cancels. This gate remains <=1e-10. It is not replaced by a recurrence, normwise backward error or agreement with an old answer.

## Sine modes and FFT convention

For n=nz, j=0,...,n-1, and k=1,...,n,

    s_k(j)=sin(pi*k*(j+1/2)/n),
    lambda_k=4*sin(pi*k/(2*n))^2/h^2.

Substitution into the interior and the two ghost rows gives the same eigenvalue. Orthogonality gives squared norm n/2 for k<n and n for k=n, whose entries are (-1)^j. All eigenvalues are positive. With unnormalized sine coefficients S_k=sum_j x_j*s_k(j), use the odd extension of length 2n, (x,-reverse(x)). Its forward Fourier coefficient satisfies F_k=-2i*exp(i*pi*k/(2n))*S_k. Hence

    S_k=-0.5*Im[exp(-i*pi*k/(2n))*F_k].

For inversion set the zero frequency to 0, F_k=-2i*exp(i*pi*k/(2n))*S_k for 1<=k<n, and the real Nyquist coefficient F_n=2*S_n. NumPy irfft with length 2n, restricted to its first n samples, gives the inverse. Conjugate frequency pairs and the unpaired Nyquist term implement the distinct 2/n versus 1/n sine normalization automatically. The last frequency is explicitly assigned real rather than relying on an approximately real exponential expression.

Transforming the RHS before solving yields one radial tridiagonal system per k, with diagonal L_i+U_i+lambda_k and the original outer U_last addition. These real matrices are strictly diagonally dominant with positive diagonal and nonpositive off-diagonals; the W_i weights symmetrize them. Their exact-real Thomas pivots are positive. The implementation checks finite positive pivots at every row and finite output. Each fixture rebuilds its factors/transforms; no hidden or uncharged cache is used. Reusing those factors in a later coupled implementation is a separate implementation choice that must be frozen and costed.

## Independent checks and limits

The fixed transform checks use n=64,128,192,256,512 and modes k=1,7,n. Their known sine coefficients test the phase and exceptional normalization separately from a round trip. A deterministic mixed vector extends the round-trip checks. For the axial eigen identity the normwise backward residual is

    eta_operator=||A_z*s-lambda*s||_2 / ((4/h^2)*||s||_2),

using the exact spectral norm 4/h^2. T57 specified an eigen-residual threshold but not its denominator; this definition is fixed here before any T58 measurement. The threshold is <=1e-11. Also report the eigenvalue-relative diagnostic eta_lambda=||A_z*s-lambda*s||/(|lambda|*||s||), without selecting between normalizations after output. Small eta_operator alone does not certify low-mode solution accuracy. Complete Poisson solves must still pass the original RHS-relative residual and independent solution-error gates; those gates are unchanged.

The manufactured fixture is exactly nr/nz=256/512, R=8, h=1/32, with known discrete array

    phi_ij = (1+(r_i/R)^2) * [sin(pi*(j+1/2)/nz)
             + .2*sin(7*pi*(j+1/2)/nz) + .03*(-1)^j].

Set all Dirichlet data to zero and b=A*phi using the independent original stencil. The resulting signed RHS is a linear algebra fixture, not a positive physical vortex or an additional application scene. Recovering this known array checks the largest declared operator and the last mode. It supplies no real dynamic-boundary cost, coupled trajectory or reference-accuracy result. Old-CG differences, residuals and manufactured-solution error are distinct required evidence; disagreement with an old CG answer cannot by itself identify which solution is responsible.
