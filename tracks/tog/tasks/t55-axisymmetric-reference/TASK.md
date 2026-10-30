# T55 — a physical task before method development

This is a researcher-defined development task for the same single curl-Gaussian, not a creator-validated brief or a held-out benchmark. It screens whether a compact vortical primitive can predict coherent self-induced transport and shape. It does not assume that one primitive is adequate or that a new algorithm is needed.

Use free-space incompressible Euler, density one, no viscosity, forcing, walls or swirl. Set the initial Gaussian width sigma=1 and center axial speed u_z(0)=1, hence t_c=1. The impulse direction is +z. In meridional coordinates r>=0,z in R,

    q(r,z,0) = omega_theta/r = (3/2) exp(-(r*r+z*z)/2),
    omega_theta(r,z,0) = r q(r,z,0).

This is T49–T54's same normalized carrier, with a=(3/2)(2*pi)^(3/2) e_z and s=1. It is a broad-core Gaussian vortex ring, not a thin filament. The flow is axisymmetric; this does not support general 3D speed claims.

## Future trajectory screening choices, fixed before trajectories

Window t in [0,1], saved times 0,1/4,1/2,3/4,1. This is the initial center-speed one-width timescale; it does not promise the ring centroid moves one width. Require the reference's axial circulation-centroid displacement at t=1 to be at least .25 initial widths for a meaningful-motion screen. If not, record insufficient motion for this task rather than failure of a method.

Primary sampled physical requirement: at every saved time, world-coordinate relative L2 vorticity error <=10%, with three-dimensional volume measure 2*pi*r dr dz. No translation, rotation or scale alignment is allowed in that norm. The same initial field and ordinary full-parameter differential fit are available to every comparator; the verified optimal coefficient is not withheld. Center update is diagnostic only, and any reference-snapshot fit must be labelled an oracle, not an equally informed deployable baseline.

Secondary motion/shape requirements: axial circulation-centroid error <=.1 initial widths, and circulation-weighted meridional covariance Frobenius error <=.1 times its initial reference Frobenius norm. Use omega_theta dr dz for these quantities, explicitly distinct from the 3D primary norm. Center the shape statistic only; do not use that centering to hide primary displacement error. Record Gamma=integral omega_theta dr dz and negative-vorticity mass without clipping. These statistics require positive vorticity with nonzero Gamma; a violated positivity assumption must be reported.

Future empirical reference-qualification targets are 1% for sampled 3D field disagreements, .01 width for centroid disagreements and .01 initial covariance norm for shape disagreements when spatial, time and domain controls are varied independently. Convergence disagreements are evidence, not rigorous true-error bounds. Conservation and tail/support diagnostics must be retained. No continuous-time supremum claim follows from five samples. These thresholds are researcher screening choices, chosen independently of T54's .355 instantaneous residual; they are not creator, production or venue acceptance criteria.

## This task only qualifies an initial spatial reconstruction

T55 implements one ordinary r^3-weighted finite-volume Poisson reconstruction with free-space Green boundary values. It compares initial velocity and the full Cartesian velocity Jacobian against the known analytic field under a separately frozen numerical protocol. It evolves no q, advances no time and scores no candidate trajectory. A pass is only a necessary spatial prerequisite. Advection, dynamic boundary/source truncation and time convergence still need their own protocol and evidence.

If the spatial reference fails its fixed checks or execution budget, retain the failure and stop this numerical task. That is an evaluation gap, not a rejection of the carrier. If it passes, consider the remaining reference/time-evolution requirements before any finite-time method decision. Count all reconstruction, Green-boundary work, fitting and failed/preparatory executions in later comparisons. No candidate repair or new representation is selected here.
