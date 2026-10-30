# T57 — preserve the resource failure; qualify a same-operator solver next

The terminal status is `timeout_no_retry`: zero complete new trajectories in 1200.257536700 seconds. The measured totals and limitations are in [RESULTS](RESULTS.md) and [execution.json](execution.json). The resource-failure branch below is selected. No new solver, fluid run, source batch or larger budget was introduced inside this invocation.

## Selected next question after the retained resource failure

The 1200-second cap prevented completion; preserve that failure. Do not call the reference qualified, score a Gaussian method against an unqualified prefix, rerun this task, lower resolution, shorten its window or raise its budget. A completed logged stage is not a saved field checkpoint: the unchanged T56 solve_case writes its NPZ and case summary only after a whole case finishes. The killed partial S256 trajectory therefore cannot be silently resumed from logs.

The terminal records identify a specific ordinary implementation issue: every stage starts the weighted CG solve from zero, and the completed logged Poisson solves account for 88.302% of the full failed invocation. This observation alone neither proves CG is inherently inadequate nor establishes a research contribution. It motivates **T58: separately freeze one same-discrete-operator ordinary direct-solver qualification using existing saved states**, with no new fluid trajectory or Green matrix. Do not substitute a different physical equation, boundary condition or weaker residual.

The current rectangular FV operator is separable in the uniform axial coordinate. Its axial matrix has diagonal 2/h^2, endpoint diagonals 3/h^2 and off-diagonals -1/h^2. With n axial cells, modes

    s_k(j) = sin(pi*k*(j+1/2)/n), k=1,...,n, j=0,...,n-1
    lambda_k = 4*sin(pi*k/(2*n))^2/h^2

diagonalize that matrix, including the half-cell Dirichlet ghost rule. Their squared norms are n/2 except the last mode k=n, whose norm is n. There is no zero mode. Consequently an ordinary sine transform followed by one radial tridiagonal solve per mode solves the same linear system. The transformed RHS must include the existing nonhomogeneous radial and axial boundary additions before transforming.

Use exactly the old radial coefficients left_i/right_i, diagonal left_i+right_i+lambda_k with an extra right_last in the final row, and off-diagonals -left_i/-right_i. Positive lambda makes these matrices strictly diagonally dominant with nonpositive off-diagonals; their exact-real Thomas pivots are positive. The original r^3 cell weights also make them self-adjoint positive definite. These algebraic facts do not replace finite/positive pivot checks or the unchanged true weighted residual <=1e-10 evaluated with the original operator.

A NumPy-only FFT implementation can use the odd extension v=(x_0,...,x_(n-1),-x_(n-1),...,-x_0) of length 2n. If V=FFT(v), the unnormalized sine coefficients are

    S_k = -0.5*Im[exp(-i*pi*k/(2*n))*V_k].
    x_j = (2/n)*sum_{k=1}^{n-1} S_k*s_k(j) + (1/n)*S_n*(-1)^j.

The half-cell phase and exceptional last-mode normalization must be checked independently; applying an unnormalized forward transform twice is not the inverse. This is an ordinary separation-of-variables/Thomas baseline improvement, not a proposed TOG method. The derivation was checked conceptually by a second agent without source access or numerical execution.

## Bounded T58 preparation now selected

Before running, freeze a standalone implementation, derivation, exact fixture identities and supervisor protocol. Allow one child, at most 180 seconds including imports, all transform/factor setup, fixture loads, solves, comparisons, residuals and output; zero retries, pilots, installs, new sources or fluid trajectories. Reuse the byte-valued memory observation method with >=3 GiB available host preflight and a 2 GiB observed peak-working-set stop. No scientific invocation is authorized by this document before that separate freeze.

Use all 18 saved T56 states (six cases at 0,.125,.25), including the historically failed coarse case as a **linear algebra fixture**, not a retrospectively qualified physical reference. Saved q, dynamic boundary vectors and phi permit same-system checks without rerunning CG or building K. Require original true weighted residual <=1e-10; weighted phi difference from saved CG <=1e-8; reconstructed u and J differences <=1e-7 under the original fixed-core, 3D-volume-weighted norm. Reconstruct the old J from the saved old phi/boundaries for later times; this is an algebraic readback, not a new elliptic solve. Keep old solver uncertainty visible and validate initial saved u/J identities where available.

Freeze transform round-trip and eigenmode checks before execution for n=64,128,192,256,512, including k=n explicitly. Require relative round-trip <=1e-12 and independently formed axial-operator eigen residual <=1e-11. Add exactly one manufactured linear-system check at nr/nz=256/512, R=8, with zero boundary data and a prespecified known phi containing axial modes 1,7,n and a nonconstant radial factor. Construct b with the original discrete stencil and recover phi; require relative phi error <=1e-8 and true weighted residual <=1e-10. This signed algebraic fixture is not a positive physical vortex, additional application task or new candidate mechanism. Its purpose is testing the largest operator and the exceptional mode; it does not measure S256's real dynamic-boundary cost.

Report complete cost per fixture and whole child, including factor/transform setup, reconstruction, comparisons and memory. Any test/resource failure closes this qualification without fallback or automatic repair. Passing would support only the same-operator replacement on these fixtures; a later separately frozen coupled reference must still requalify spatial/time/domain/angular agreement, positivity, CFL, drift and full costs. Dense current-q Green work remains in every later budget. No automatic restart of T57 or t=1 rollout follows a linear-solver pass.

If a direct/old-CG difference exceeds its frozen gate, qualification fails, but the cause may include old CG uncertainty. The manufactured known solution, original-operator residual and old-solution discrepancy are different evidence; none silently overrides another required check or by itself proves a physical carrier failure.

## Deferred full-task route, requiring a later qualified reference

The next preparation should directly address the existing [T55 full t=1 task](../t55-axisymmetric-reference/TASK.md) and the ordinary complete-tangent Gaussian comparator, with a new budget informed by actual costs. A short-time snapshot-oracle fit is optional later for diagnosing a demonstrated prediction error; inserting one now would not resolve the full task's motion and finite-time requirements.

For the isolated free-space isotropic Gaussian, explain why translation equivariance carries the verified full-space optimal tangent to every translated state. Only then use its constant-speed analytic translation as the ordinary projection trajectory; do not merely freeze an initial best derivative without that argument. The coefficient must remain the verified one, never refitted to reference snapshots or the restricted measurement core. Analytic translation removes ODE time-discretization error, not field sampling, reference or floating-point errors. Neither the initial residual rate times the elapsed interval nor a short-time fit predicts guaranteed success/failure at t=1.

The argument is available without another numerical fit. Let T_mu denote axial translation and F the free-space Euler vorticity vector field. Free-space velocity reconstruction and spatial differentiation commute with T_mu, so F(T_mu omega)=T_mu F(omega). The full-space L2 inner product is translation invariant, and the complete Gaussian tangent space at the translated state is the translate of the original tangent space. Thus its orthogonal field projection commutes with T_mu. In T52/T54's coefficient convention the velocity vector is beta_star*a; denote its actual axial speed by c=beta_star*a_z, not by beta_star alone. The verified initial projected field derivative is c times the axial-translation tangent; at every translated state the projected derivative is the same translated tangent with the same c. Consequently center_mu(t)=center_mu(0)+c*t with unchanged amplitude/covariance is a valid trajectory of that ordinary projected field dynamics. This statement concerns the full-space projection, not a reoptimization over the finite measurement core or a claim that exact Euler evolution is a translation. It supplies an inexpensive fair comparator once a physical reference is qualified, not a repair or new method.

T56 and all earlier failures remain immutable in either branch. The full goal remains active and unachieved: an ordinary reference qualification or its implementation improvement does not establish a distinct useful TOG contribution. Art stays inactive; main and the deleted automation remain unchanged.
