# Post-confirmation analytic lead: one generator couples both omitted shapes

The mechanism analyst supplied this observation after the sole T74 confirmation, and Root checked the symbolic differentiation. It is kept outside the frozen derivation/worker inputs. No additional numerical measurement or solver is implied.

In physical-volume coordinates, use the Hamiltonian convention

\[
\dot x=-\Psi_z,\qquad \dot z=\Psi_x,
\qquad \dot q=\Psi_zq_x-\Psi_xq_z.
\]

For the original q0, a radial generator \(\Psi=x k(2x+z^2)\) gives

\[
\dot q=z\,k(2x+z^2)q_0,
\]

because the two terms containing k' cancel. In particular, \(\Psi=x(2x+z^2)\) gives \(z(2x+z^2)q_0\). Removing its H-orthogonal translation part leaves

\[
z(2x+z^2-7/2)q_0=2e_1+n.
\]

The optimal projection coefficients already derived satisfy \(b_1=2b_n\). Thus one ordinary Hamiltonian direction can couple the shear and the conditional cubic deformation in precisely this initial projection ratio. The captured squared norm is \(G_1+G_n=(8/63)G_0\); this follows algebraically from the existing orthogonality identities, not from a new fit or measured trajectory.

This is a constructive direction for reasoning about radial redistribution. It does not supply a new method. The polynomial generator is unbounded and does not itself define an admissible complete free-space evolution solver. A globally regular map, induced-velocity cost, energy behavior and comparative benefit remain unresolved. Choosing k=2φ0 recovers the ordinary exact initial Euler generator, making clear that writing this structure down does not bypass the self-consistent velocity solve at later states.

This lead should be compared with ordinary material/flow-map and mixture alternatives before implementation. It does not automatically replace the bounded baseline diagnostic in DECISION.md or authorize an additional run.
