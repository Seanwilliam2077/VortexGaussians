# T46 mathematical and model-contract review

30 October 2026. **CLEAR after two pre-seal clarifications.** This is collaborative mathematical/adversarial checking, not blind replication or empirical validation. The reviewer had participated in preceding transfer/moment analyses, read the five T46 drafts, and checked selected passages in only the four model files named by LOCAL_MODEL. No scientific method, numerical example, simulation, renderer, new model variant or external acquisition was executed.

The first draft's joint-Gaussian construction specified independent noise with mean zero and covariance R but did not explicitly require Gaussian noise. The final ANALYSIS now states `eta~N(0,R)`, allowing a degenerate Gaussian. The final LOCAL_MODEL also replaces ambiguous “removed resolved kinetic energy” wording with the declared mass-weighted joint-state interpretation, expressly excluding an automatic macroscopic single-velocity energy interpretation. Neither clarification changes the displayed second-moment identities.

## Mathematical findings

The regression residual has zero mean and is uncorrelated with position. Its covariance is the stated Schur complement `R=V-B S^-1 B^T`, hence positive semidefinite. For positive component weights and SPD component covariances, its nonnegative component decomposition proves the exact common-affine-velocity equality condition. The singular-covariance caveat is appropriate. Momentum preservation follows from the retained velocity-position cross moment; neither R nor its trace is automatically a combustion or thermal variable.

The label-based kinetic second-moment loss is `M tr(R)/2`. The law of total conditional covariance gives the displayed separation into multistream dispersion and the macroscopic field's departure from its best affine fit. These terms cannot be silently identified with each other. The opposite-velocity, identical-position-distribution example correctly has zero initial macroscopic velocity and positive label-based kinetic second moment.

For trajectory-constant free streaming, the exact updates are `S(t)=S+t(B+B^T)+t^2 V`, `B(t)=B+tV` and constant V. Propagating the deterministic affine merge under that same dynamics therefore produces differences `t^2 R`, `t R` and R. This is not integration of a frozen Eulerian affine velocity field. Matching means and mass makes the projected full-line optical-depth second-moment difference `kappa M t^2 P R P^T`; it does not certify the full density, RGB or perceptual error. Possible degenerate spatial measures are disclosed.

For the explicitly Gaussian joint state, differentiation preserves matrix order and gives `Cdot=R S^-1-C^2` and `Rdot=-CR-RC^T`. The Gaussian kinetic-stress acceleration `R S^-1(x-mu)` agrees with the conditional mean's material acceleration while individual free-streaming velocities remain constant. This is distinct from incompressible pressure projection. The broader affine phase-space covariance congruence is a standard exact second-moment update, not nonlinear closure or recovery of the original mixture.

## Local applicability and cost limits

Selected direct checks were confined to `demo/index.html` lines 1589–1617, 2093–2117, 3650–3717 and 3877–3904; `research/P2_README.md` lines 1–25; `research/physical_reference/README.md` lines 1–34; and `research/shared_state_screen/PROTOCOL.md` lines 7–42. Their whole-file hashes match LOCAL_MODEL. These passages support the crucial distinctions: visual covariance, field-derived velocity, transient affine approximation groups retaining tracers, authored thermal measure, and prescribed trajectories do not instantiate the proposed persistent mechanical merge. Other cited 3D/render passages remain the scoped model auditor's findings; this review does not claim complete source inspection or repository-wide absence.

The six extra symmetric scalars and O(k) preparation/O(1) fixed-group propagation are appropriate exact-real operation counts. Group construction, force/model semantics, conditioning/PSD checks, rendering, invalidation and child retention remain separate costs. An equally informed ordinary joint-moment representation obtains the same identities. No practical advantage or new method follows.

SOURCES reports two queries and four primary attempts, with two usable records and two access failures. This review checked that attribution and limitation record without independently reacquiring the literature or treating inaccessible snippets as evidence. No remaining blocker was found. The justified result is a specific state-loss identity, ordinary repair and scoped local model mismatch; no implementation or numerical queue is selected.

Reviewed SHA256 identities:

```text
SCOPE.md
d5b7b10f3c40ff47d5b9afde857b12002d5a7770526b7068b52c6ad71134a1f2
ANALYSIS.md
64a8a9211d62901cfa65b5821043a2fb7d6255b2edf686588c7807380c8dbe8c
SOURCES.md
b057c7293abbbf9bd52db18b32d5d293452d033fe8c7b485651ab1d4d4ac77c5
README.md
ffe267f36ad880ea32c56fdd39da94d367f261752b12a7181edc01f7f483cf81
LOCAL_MODEL.md
268b52da2395bef26e6b9b7db2b34c8486f0f35e6120803141f7b80f62c9944e
```
