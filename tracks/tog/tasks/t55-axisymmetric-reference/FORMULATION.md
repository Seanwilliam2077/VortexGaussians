# T55 — same-field axisymmetric reference

The convention is omega_theta = partial_z u_r - partial_r u_z. With q=omega_theta/r and streamfunction psi=r^2 phi,

    u_r = -r phi_z,       u_z = 2 phi + r phi_r,
    -(phi_rr + 3 phi_r/r + phi_zz) = q,
    q_t + u_r q_r + u_z q_z = 0.

Here viscosity nu=0. This follows directly by differentiating the streamfunction and the axisymmetric no-swirl vorticity equation. The ordinary free-space streamfunction/Biot–Savart ancestry and a sign discrepancy in one inspected source are recorded in [SOURCES.md](SOURCES.md); the implementation uses the explicitly stated curl convention throughout.

The fixed initial normalization is sigma=1, q=1.5*exp(-(r^2+z^2)/2) and u_z(0)=1. Equivalently the localized magnetization is m=1.5*exp(-|x|^2/2)*e_z; its normalized-Gaussian coefficient is a=1.5*(2*pi)^(3/2)*e_z, not a unit coefficient. This is the same physical curl-Gaussian carrier as the preceding tangent analysis in the units specified in [TASK.md](TASK.md).

At the axis phi_r=q_r=0, u_r=0 and u_z=2phi. The radial operator's limit is 4phi_rr, not the 2D radial Laplacian. Treat phi as a radial function in four coordinates plus z: -Delta_5 phi=q. This elliptic device does not make the transport velocity incompressible in five dimensions.

The 5D Green function is 1/(8*pi^2*distance^3). Integrating its three-sphere angular measure gives boundary values

    phi(r,z) = 1/(2*pi) integral r'^3 q(r',z')
               [integral_0^pi sin(theta)^2 /
                (r*r+r'*r'-2*r*r'*cos(theta)+(z-z')^2)^(3/2) dtheta] dr'dz'.

T55 uses this only at faces bounding the finite source box, with interior Gauss nodes. No target is a source node. The same-ring point kernel has a logarithmic singularity; this construction does not evaluate or replace its diagonal with zero. Continuous source points can still approach a boundary target, so avoiding a sampled singularity does not make the closed-domain integrand smooth or certify quadrature error. The refinement comparisons below provide empirical evidence only. Extending direct point quadrature to interior/self interactions would require a separate treatment.

## Discrete elliptic solve

Use cell centers on [0,R]x[-Z,Z], uniform h in both directions. Let W_i=integral_(r_-)^(r_+) r^3 dr. Radial face coefficients are r_face^3/(W_i*h). Interior off-diagonal coefficients use this expression; outer Dirichlet face flux uses twice that coefficient because its face is half a cell away. Axial interior coefficients are 1/h^2; axial Dirichlet faces similarly use 2/h^2. The inner radial face has zero flux. Boundary data enter the right-hand side. This operator is positive and self-adjoint in the W_i-weighted inner product, so diagonally preconditioned weighted conjugate gradients apply. A weighted relative residual is a linear-solve check, not a physical error certificate.

Recover first and second derivatives using centered differences with reflected axis values and Dirichlet ghost extrapolation. With mixed derivative phi_rz, the nonzero cylindrical-to-Cartesian Jacobian entries at y=0 are

    J_xx = -phi_z-r phi_rz,   J_xz = -r phi_zz,
    J_yy = -phi_z,           J_zx = 3phi_r+r phi_rr,
    J_zz = 2phi_z+r phi_rz.

The extra J_yy term is essential. The numerical ghost extrapolation is not a high-order boundary stencil; qualification metrics use the fixed interior core and also report larger-domain errors separately.

## Analytic initial oracle

Let d=sqrt(r^2+z^2), A(d)=integral_0^d t^2 exp(-t^2/2)dt and f(d)=1.5*A(d)/d^3, with f(0)=.5. Define D=f'/d and E=D'/d. Then

    u_r=-r*z*D,                   u_z=2*f+r*r*D,
    J_xx=-z*D-r*r*z*E,            J_xz=-r*D-r*z*z*E,
    J_yy=-z*D,                    J_zx=4*r*D+r*r*r*E,
    J_zz=2*z*D+r*r*z*E.

For d>1/2 use the erf form for A, D=(1.5*exp(-d*d/2)-3*f)/(d*d), and E=(-1.5*exp(-d*d/2)-5*D)/(d*d). Near zero, 16-term power series from Gaussian integration avoid cancellation: f=1.5 sum (-d^2/2)^n/[n!(2n+3)], D=-1.5 sum (-d^2/2)^n/[n!(2n+5)], E=1.5 sum (-d^2/2)^n/[n!(2n+7)]. This initial oracle is available ordinary information, not a new method. No formal floating-point bound is claimed.

Physical velocity/Jacobian error uses the 3D weight 2*pi*r dr dz, never the Poisson solver's r^3 algebraic weight. Vorticity L2 for q instead uses 2*pi*r^3 q^2 dr dz. Source truncation in the Green integral is separate from boundary quadrature and the FD solve. The reported Gaussian 5D source-tail fraction is not a velocity-error bound; actual initial comparisons with the full free-space oracle include the combined observed error.
