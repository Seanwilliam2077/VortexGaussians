# T43 independent mathematical review

30 October 2026. **CLEAR within the stated algebraic scope; no implementation or experiment is selected.** This review read only the three T43 documents listed below. It performed no numerical evaluation, solver call, source search, renderer run or scientific-file modification. The scope explicitly follows preliminary algebra; it is not represented as preregistration.

## A: normalized moments and their limits

The declared positive masses, normalized weights `w_i=m_i/M`, positive-definite covariances and common extinction per mass remove the earlier normalization and parameter-semantic ambiguities. Orthographic Gaussian marginalization proves the common-footprint equality: projected between-mean covariance vanishes, so the ordinary merged Gaussian has the same entire full-line optical-depth image. Without that equality of footprints, its degree-zero through degree-two optical-depth moments still follow directly from the spatial moments. These are not moments of transmittance or RGB.

The affine cross moment is normalized consistently. `C Sigma=B_vx` preserves the complete velocity-position cross moment, hence its antisymmetric angular-momentum contraction as well as linear momentum. This statement uses the declared continuous component momentum densities; it does not inherit a different particle/grid discretization's conservation theorem. Energy, pointwise velocity, local incompressibility, subsequent dynamics, clipped/perspective rays and arbitrary colored mixing remain outside the exact guarantee. The final mechanical paragraph correctly interprets the inverse notation as a solve and distinguishes positive definiteness from good conditioning. The document correctly gives the same formulas and information to the ordinary comparator and includes grouping and continuation costs.

## B: deletion and the feasible-cycle competitor

For `P_W` as the R-orthogonal projection, `g=P_W W e_e` is the Riesz representative of edge-coordinate evaluation on the cycle space: `<g,z>_R=z_e`. Thus `k=g_e=||g||_R^2`, and the stated constrained update, norm change and bridge exception follow. The objective increment concerns `J(q)=||q-u||_R^2/2`; the projected flow's own squared norm decreases. Omitting the removed edge's objective term changes the reported objective by the stated constant, not the optimizer.

The new cheap-cycle addition is also correct. For `k>0`, put `z*=g/k`. Any feasible unit cycle satisfies

```text
<z*,z-z*>_R = (z_e-z*_e)/k = 0,
||z-z*||_R^2 = E_z - 1/k.
```

Multiplying by `q0_e^2` gives the exact approximation-error identity. In the specified two-port graph, a circulation with first-port coordinate one necessarily has second-port coordinate minus one. Consequently `E_z` contains both port resistances, while `1/k=H>=r1+r2`. Replacing `H` by this lower bound gives the stated conservative upper bound. It does not require a new pressure solve once the old projected flux and a known feasible cycle are available. Path acquisition, accumulation and applying the correction still cost work. The bound can be loose and has no demonstrated useful tolerance here.

## Decision and qualification limits

No blocking issue was found. Both constructions are ordinary moment matching or constrained quadratic projection, including the cheaper feasible-cycle alternative. No timing, numerical accuracy, practical workflow benefit, novelty or TOG contribution follows from this review. The real-arithmetic statements do not certify floating-point implementations: near-bridge cancellation and approximate inverse errors need separate treatment, as the draft acknowledges. The fixed closed-network hypothesis excludes incompatible boundary flux and moving geometry. Historical failures and attempt budgets remain unchanged.

Reviewed SHA256 identities:

```text
SCOPE.md
b21ab9b47963b8587d4546263e2412f819858b7fb0863bd83f262828889c67fd
A_TRANSFER.md
703691c24970c5706bc4d1cd9e7c9a67ce2c2171a3e157136a20a9d163bdee2f
B_PRESSURE.md
be6ecdf1a7538321a3c8b7564b698f903fc08c649cb6d2c368164defc4b88ced
```
