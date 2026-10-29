# T50 — bounded visual equation check

Root inspected PDF pages **3, 4, 5, 6, 10, 11**, once each, after rendering each once at 140 dpi with the existing Poppler `pdftoppm`. These are the complete six permitted page inspections; no crops or repeat views followed. All six commands returned zero. Poppler nevertheless warned that display fonts for Symbol and ArialUnicode were unavailable. The selected equations were legible in these rendered pages, but that observation is not a font-completeness or whole-document structural validation.

The source identity is in [ACQUISITION.md](ACQUISITION.md). This visual check does not reopen or repair T49's failed access attempt. Paper images remain ignored. Pages 7–9 were not visually inspected; their evaluation summary remains the bounded textual reading described in [EVALUATION.md](EVALUATION.md).

## Findings against the extraction alerts

- **Page 3, equation (5):** the second boundary row is labelled solid and the third free surface, while the following prose describes them in the opposite order. That inconsistency is visible in the acquired version; it is not merely an extraction artifact. Do not silently correct the source.
- **Page 5, equations (15)–(16):** (15) has no explicit transpose on its displayed gradient, while (16) explicitly uses a transpose inside the inverse. The prose below also describes an inverse transpose. Thus the local matrix update is readable, but the printed notation is not fully consistent. Our comparison uses the explicit matrix in (16) and states our own Jacobian convention, rather than inferring a convention that resolves every printed equation.
- **Page 5, equation (11):** an extra trailing D is visible after the boundary label. It is not evidence for an additional boundary operator.
- **Page 6:** equation (18) and Algorithm 2 display the usual backward-Euler diffusion system/inverse. Algorithm 1's viscosity row visibly has an extra inverse attached to the discrete Laplacian inside the outer inverse. The inconsistency persists in the page image. The audit uses the section's explicit equation (18) for the stated intended diffusion operation; it does not certify executable pseudocode or infer what unavailable code actually runs.
- **Pages 4 and 6:** the liquid formulation has a separate harmonic boundary-gauge solve as well as incompressibility projection; sharing a matrix is not zero cost. The latter projection retains the impulse field and updates velocity.
- **Pages 10–11:** the damping parameter is displayed inside the stretching matrix. The instability/interpolation explanation is tentative in the source. The discussed future particle/surface representation is an author proposal, not evidence that a current gap or novel solution has been established.

These checks resolve whether the flagged symbols occur in the acquired printed version. They do not validate the paper's implementation, accuracy, stability or reported timings. The paper is retained as an ordinary algorithmic comparator with these source ambiguities disclosed.
