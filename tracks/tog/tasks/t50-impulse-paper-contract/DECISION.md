# T50 — decision after the identified solver audit

**Retain the ordinary impulse solver as directly relevant prior; do not implement a new solver or claim a core contribution.** The single-source audit succeeds in narrowing the problem. It supplies a concrete full algorithm and a representation/gauge compatibility issue, not measured evidence that our proposed carrier is preferable.

## Operation mapping to T49

| Operation | Relationship | Consequence |
|---|---|---|
| Impulse field followed by solenoidal velocity projection | Same general structure as T49's m=a G_C and u=P m | The formulation and projection are not our new mechanism. |
| Impulse stretching | Same covector structure in the paper's explicit local matrix, with printed-notation ambiguity disclosed | With our A_ij=partial_j u_i, the ordinary prescribed-flow update is adot=-A^T a. Exact local affine integration alone is not a new physical model. |
| Spatial state and coupled evolution | Different | The paper evolves a MAC field, with particle-grid transfers for liquids. T49 proves finite-parameter closure only under a prescribed common affine velocity and heat diffusion in free space. |
| Gauge reinitialization | Different representation requirement | The paper's blend m_r=r m+(1-r)P m preserves projected velocity in the ideal free-space continuum. For a nonzero localized Gaussian potential and r<1 it generally adds an algebraic tail, leaving that single-Gaussian potential class. |
| Reconstruction and boundaries | Different scope | T49's ordinary analytic free-space reference does not deliver the solid/free-surface conditions or the paper's additional boundary-gauge solve. |
| Accuracy, runtime and practical usefulness | Unverified locally | Paper timings and visual examples cannot be inherited as our measurements or used as an equal-error Gaussian comparison. |

The underlying source evidence is in [METHODS.md](METHODS.md), [EVALUATION.md](EVALUATION.md) and [VISUAL_CHECK.md](VISUAL_CHECK.md). The reinitialization nonclosure is our inference from T49's established free-space tail, not a claim made by the paper. For the exact linear projector, P m_r=P m and curl m_r=curl m. This establishes physical equivalence at that instant, not stability of a finite discretization or equivalence of future approximate updates.

## Complete cost contract before any future comparison

A candidate would have to deliver the same initial physical field, domain, forcing, diffusion and output accuracy. Account for fitting/initialization, field and Jacobian queries, advection, stretching, diffusion, gauge control or refitting, all velocity/boundary solves, source management, memory, output work and failures. Include setup and amortization explicitly. A free-space first question may exclude walls for both methods, but it cannot then claim to replace the paper's complete liquid/obstacle solver. Equal numbers of particles or stored parameters do not impose equal approximation errors.

Ordinary baselines retain the same analytic kernel/derivatives, exact local linear update and permissible gauge information. The grid reference's GPU/CPU and precision differences in reported timings prevent attributing its reported speed difference to impulse representation alone. This audit does not measure local performance or establish a universal source-count scaling law.

## What changes next

There are now two separate gaps: **self-consistent nonlinear evolution** and **stable finite representation/gauge management**. Merely reproducing this paper's local implicit update, choosing r=1, or removing interpolation does not close either gap. Source notation problems are not research contributions. The authors' future-work paragraph is not a novelty argument.

Before implementation, the useful finite question is whether even the current localized Gaussian carrier has a tangent consistent with its own induced velocity. This follows directly from T49's prescribed-flow limitation, sharpened by this paper's coupled solver. A [single analytic consistency task](NEXT_EVIDENCE.md) is prepared, not executed. It must allow the entire existing Gaussian tangent, not only the particular center-Jacobian update, so a failure cannot be manufactured by weakening the ordinary update. No external source batch, new family, parameter sweep, simulation or numerical queue follows this audit.

The full research goal remains active and unachieved. Historical outcomes, the original core, art inactivity, main and the deleted automation remain unchanged.
