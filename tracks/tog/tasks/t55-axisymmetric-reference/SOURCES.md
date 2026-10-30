# T55 — bounded source screen for an axisymmetric reference

This source-only screen identifies a mathematical free-space contract, not a qualified numerical solver. It performed no scientific computation, trajectory, installation, repository clone, source-file acquisition or asset download. The existing [T54 decision](../t54-scalar-verification/DECISION.md) supplied the task context. No new method is claimed.

## Acquisition accounting

Exactly two search queries, submitted together in one web call:

1. `axisymmetric no swirl Euler vortex ring free space Biot Savart elliptic integrals numerical scheme source code PyAxisymFlow`
2. `Gallay Sverak axisymmetric vorticity Biot Savart F(s) kernel stream function Euler no swirl`

Five web calls in total: that search call; one call opening S1/S2; one opening S3 and finding two locations in S1; one finding three locations in S3; one reopening S3 text near its introduction. Only the three primary documents below were opened. Other search-result snippets were not followed or used as technical evidence. No second query batch. The PDF skill was read locally; S3 was inspected only through web-extracted text, with no local PDF copy, page rendering or visual equation verification.

## S1 — inviscid transport and Biot–Savart form

[Deokwoo Lim and In-Jee Jeong, *On the Optimal Rate of Vortex Stretching for Axisymmetric Euler Flows Without Swirl* (2025)](https://link.springer.com/article/10.1007/s00205-025-02103-1), DOI `10.1007/s00205-025-02103-1`.

Inspected HTML: (1.1)–(1.5), lines 62–109, and §2.2, lines 293–320, plus tool-returned proof snippets; no full-paper review. Equations (1.4)–(1.5) give

\[
\partial_t\omega^\theta+u^r\partial_r\omega^\theta+u^z\partial_z\omega^\theta
=\frac{u^r}{r}\omega^\theta,
\qquad
\partial_t(\omega^\theta/r)+u\cdot\nabla(\omega^\theta/r)=0.
\]

Reconstruction is on \(\mathbb R^3\), with the reduced elliptic-integral kernel in §2.2. No numerical scheme was inspected. Its main growth theorem assumes compact support, unlike the Gaussian task.

**Unresolved text discrepancy:** HTML (1.3) prints \(\omega^\theta=-\partial_z u^r+\partial_r u^z\), opposite to S3, yet §2.2 prints the same kernel signs. No erratum, PDF image or alternative version was checked. Convention versus typo/transcription is unresolved; do not mix conventions.

## S2 — available code lead, not a matched solver

[bhosale2/PyAxisymFlow repository](https://github.com/bhosale2/PyAxisymFlow).

Only the landing README/listing was read, primarily lines 175–220. It describes axisymmetric elastohydrodynamic simulation of mixed soft/rigid bodies in **viscous** flows and advertises version 0.0.1, DOI `10.5281/zenodo.7658925`. The DOI, examples, kernels and tests were not opened; no commit was pinned.

The inspected material does not establish free-space boundaries, inviscid operation, discretization, time integration, Gaussian initialization or convergence qualification. These remain unverified, not necessarily absent. Availability alone does not qualify an Euler reference. No installation occurred.

## S3 — coherent streamfunction and axis contract

[Thierry Gallay and Vladimír Šverák, *Remarks on the Cauchy problem for the axisymmetric Navier–Stokes equations* (2015)](https://numdam.org/item/10.5802/cml.25.pdf), DOI `10.5802/cml.25`.

Reviewed web-extracted (1.4)–(1.8), (2.1)–(2.8), PDF zero-based pages 2/6 (printed 68/72); tool context also included pages 0–7/18. No full-document or visual check.

With standard \(e_\theta=(-\sin\theta,\cos\theta,0)\), S3 uses

\[
\omega_\theta=\partial_z u_r-\partial_r u_z,\quad
u_r=-r^{-1}\partial_z\psi,\quad u_z=r^{-1}\partial_r\psi,
\quad-(\partial_{rr}-r^{-1}\partial_r+\partial_{zz})\psi=r\omega_\theta.
\]

For decaying vorticity on \(\Omega=\{r>0,z\in\mathbb R\}\),

\[
\psi(r,z)=\frac1{2\pi}\int_\Omega\sqrt{r\bar r}\,F(s)\omega_\theta(\bar r,\bar z)\,d\bar r\,d\bar z,
\quad s=\frac{(r-\bar r)^2+(z-\bar z)^2}{r\bar r},
\]
\[
F(s)=\int_0^\pi\frac{\cos\phi}{\sqrt{2(1-\cos\phi)+s}}\,d\phi.
\]

Axis regularity gives \(\psi=O(r^2)\), \(\psi=\partial_r\psi=0\), and \(u_r=\partial_r u_z=0\) at \(r=0\). Near the diagonal, \(F(s)=\log(8/\sqrt{s})-2+O(s\log(1/s))\). The evolution theory fixes viscosity to one; this reconstruction supplies no inviscid numerical scheme.

## What this screen permits and leaves open

The source-supported mathematical route is transport of \(\omega_\theta/r\) coupled to the free-space axisymmetric reconstruction, using one coherent sign convention. The following are implementation inferences and unresolved qualifications, not source-certified results:

- A finite outer boundary needs a free-space boundary treatment or a quantified truncation approximation. Axis regularity does not justify setting the streamfunction to zero on an arbitrary finite outer box; a periodic inverse is also a different boundary problem.
- The diagonal singularity, axis limits, Gaussian tails, spatial discretization and time accuracy require explicit treatment. An analytic initial velocity/Jacobian check is necessary evidence, not a later-trajectory guarantee.
- No known numerical scheme with a complete inspected, pinned, reproducible implementation was established within this batch. S2 remains a lead with unresolved model compatibility. A newly written ordinary reference would need its own bounded qualification; it cannot inherit a numerical accuracy claim from S1/S3.

The three-document and two-query limits are closed. No further source acquisition or numerical task was executed by this screen.
