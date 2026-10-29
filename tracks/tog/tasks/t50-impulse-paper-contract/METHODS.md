# T50 bounded methods mapping

## Reading record

Only `local/methods-read.txt` was read, exactly once, using one byte read. It contains the assigned PDF pages 3–6, including page markers: **3178 whitespace-delimited words; 31583 bytes; SHA256 `ba243e5ee49fdf4f3d74d092237fca3cb5fa5259a8797d877603ec6dfe40e7a1`**. The same in-memory bytes supplied the displayed text, word count and hash. The output was not truncated. The bookkeeping receipt is `local/methods-reading-receipt.json`.

The excerpt identifies an IEEE author version, DOI `10.1109/TVCG.2022.3149466`. This audit did not open the PDF, another excerpt, an image or an external link, and did not execute a scientific method. The excerpt hash is not an independently verified PDF identity.

## Paper-derived mapping: concise paraphrase

- **State/gauge:** Page 3, Section 3.2.1, equations (4)–(5), relates impulse field m to velocity through a gradient gauge and a Poisson projection. Page 4, Section 3.3, equation (9), combines the evolution and gauge constraints.
- **Evolution:** Equations (6), (9) and (12) include transport, stretching, gauge forcing, viscosity and optionally buoyancy. Section 3.2.2 uses a harmonic boundary gauge for liquids and sets that gauge to zero for smoke.
- **Representation:** Page 5, Section 4, stores velocity/impulse on MAC faces and gauges/scalars on cells. Section 4.2 uses semi-Lagrangian smoke advection; liquid PIC/FLIP transfers through particles and returns quantities to the grid.
- **Reinitialization:** Section 4.1 blends m with its projected velocity each step, normally using r=.97, to control impulse growth. Section 4.6 says projection updates velocity while retaining impulse.
- **Numerics:** Section 4.3, equation (16), uses an implicit local transpose-gradient solve with cell/face interpolation. Page 6, Section 4.4, equation (18), uses backward-Euler viscosity. Section 4.6 uses GPU multigrid-preconditioned conjugate gradients for projection.
- **Boundaries:** Equations (3), (5), (8), (10)–(11) and Section 4.5 describe solid nonpenetration and free-surface conditions; the boundary-gauge and projection solves reuse a matrix.

**Extraction uncertainties:** Page 3's prose assigns boundary-row names inconsistently with equation (5)'s labels. Equations (15)–(16) differ in explicit transpose notation. Equation (11) and Algorithm 1's viscosity line contain malformed text; the latter differs from equation (18). These were sent to the parent for visual checking within the same four-page budget, not silently corrected here.

## Own comparison with the already derived T49 model

**Same mathematical structure:** T49's m=aG_C and u=P m instantiate an impulse/vector-potential field followed by projection. Its covector update adot=-A^T a is consistent with the transpose stretching structure displayed in equation (16), subject to confirming the paper's gradient convention. These similarities exclude treating impulse state, covector stretching or velocity reconstruction by projection alone as a new mechanism.

**Different contracts:** The paper's state is a spatial field supported by a grid/particle-grid algorithm. T49 retains one Gaussian's center, covariance and covector, and proves closure only for a prescribed traceless affine velocity plus constant-viscosity heat diffusion in free space. Its parameter a is also the normalized carrier's integrated hydrodynamic impulse; it is not interchangeable with the paper's entire field m. The paper's coupled numerical flow and bounded-domain projection do not follow from T49's finite prescribed-flow closure, and T49's analytic closure is not evidence of equal discretization error or cost against that solver.

**Reinitialization does not stay in the T49 parameter class:** In the T49 free-space continuum contract, for m_r=r m+(1-r)P m, linear projection gives P m_r=P m and curl m_r=curl m. However, for nonzero a and r<1, the projected velocity has an algebraic tail, so m_r is generally no longer a single constant covector times a Gaussian. Maintaining T49's localized gauge without this blending is a different algorithmic choice; the identity neither establishes stability nor reproduces the paper's discrete reinitialization. Conversely, representation nonclosure under that particular blending does not prove T49 unusable.

**Unverified:** These four pages do not establish whether the paper or wider literature already contains T49's exact Gaussian parameter closure or one-dimensional reconstruction formulas. Their absence from this bounded methods description would not establish novelty. The malformed equations require the parent's visual check; no numerical stability, runtime, convergence or boundary implementation was independently assessed.

**Decision limit:** The reading supplies a concrete ordinary impulse formulation and exposes a gauge/representation compatibility question. It does not yet justify implementation, an equal-source-count comparison, removal of projection cost, or a TOG contribution. Any future comparison must freeze the same physical field, domain, forcing, gauge/reinitialization behavior and accuracy requirement; source-count equality alone is insufficient.
