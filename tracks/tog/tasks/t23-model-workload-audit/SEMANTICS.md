# T23 — conditional ray mapping and unresolved release contract

29 October 2026. This is a paper-level semantic check and elementary algebra, not an implemented adapter, numerical result, or new method. The source-specific observations and inspected locations are in [VOL3DGS_PAPER.md](VOL3DGS_PAPER.md). The [repository ledger](repository-access.json) records the failed fixed-revision request. No pinned implementation or asset metadata was acquired.

## Conditional mapping, derived here

Suppose a released field really stores an unnormalized nonnegative extinction component

```text
sigma_i(x) = kappa_i * exp(-0.5 * (x-m_i)^T Q_i (x-m_i)),
Q_i = Sigma_i^-1, Sigma_i positive definite, kappa_i >= 0.
```

This is an explicit condition on a potential release, not an inference that a stored opacity field equals kappa. On a world-space ray x(t)=o+t*d with unit d, set

```text
v_i = o-m_i
q_i = d^T Q_i d > 0
r_i = d^T Q_i v_i
h_i = v_i^T Q_i v_i - r_i^2/q_i >= 0
mu_i = -r_i/q_i
sd_i = 1/sqrt(q_i)
w_i = kappa_i * exp(-h_i/2) * sqrt(2*pi/q_i).
```

Completing the square gives exactly sigma_i(o+t*d)=w_i*NormalPDF(t;mu_i,sd_i). Its mass on [a,b] is w_i times the normal-CDF difference. This is the input form used in T17–T22. If d is not unit and t is a camera parameter, optical depth uses ||d||*sigma_i(o+t*d)dt; the w above therefore also needs ||d||. Failing to distinguish camera-depth and world-distance conventions changes the target. The nonnegative h statement is exact arithmetic, not a guarantee for a cancellation-prone implementation.

With per-component color c_i constant along the chosen ray, a field whose source is j=sum_i sigma_i*c_i has the same overlapping-emission structure as T21. A position-dependent color, independent emission term, scattering albedo, or discrete alpha operator needs a different mapping. SH coefficients alone do not establish which direction/position the implementation evaluates or its output color units.

These statements provide a possible mathematical route from a genuine density representation. They neither convert peak alpha to density nor certify the unavailable checkpoint. They do not require physical calibration of learned density.

## What prevents a qualified workload now

| Requirement | Evidence and present decision |
|---|---|
| Density and source operator | Paper-level relation is supported by the source note; released field names, activation, normalization and scene units remain unverified without pinned code. The formula above is conditional. |
| Complete domain and support | The source note records a full-line/finite-domain difference. Whole-line Gaussian algebra is not the same target as our fixed clipped deliveries. A future task must declare its domain and charge any excluded optical mass; neither a rasterizer tile list nor a finite segment silently proves complete support. |
| Color range, constancy and background | T22 developed on [0,1] component RGB and fixed backgrounds. The source note does not establish that release contract. T21's convex-mixture/sign argument extends algebraically to any finite component colors with their actual channel extrema, but that observation is not a tested loader, equivalent tolerance scale, or permission to clip colors. Background and any postprocessing must also be explicit. |
| Camera/covariance mapping | The elementary ray restriction above is possible for a positive-definite covariance in known world coordinates. Stored covariance factorization, transforms, ray units, near/far semantics and camera carrier were not inspected. |
| Prior-method coverage | The successful paper read is limited to named sections; Hybrid yielded no new text. No exact coverage or novelty clearance for the winner-event bound follows. Prefix attenuation in a renderer is not by itself this bound, and unfamiliar terminology is not evidence of absence. |
| Existing official input and permissions | No pinned tree, checkpoint metadata, camera files, asset sizes or asset-use statement was acquired. This is an unverified carrier, not proof that one does not exist. Paper access alone cannot qualify it. |

## Consequences for the local cost result

These are hypotheses to measure later, not measurements: optical masses affect every prefix; camera units and truncation can change them; actual color ranges change pair contributions and the meaning of a fixed absolute RGB tolerance. Which primitives enter each ray controls both acceptance and worst-case pair work. None of these distributions is known for an official asset. Therefore T22's one incremental case and small full-batch difference cannot be extrapolated using a paper's model name.

Decision: retain the paper-level mathematical route and the exact missing release fields. The fixed T23 condition for preparing an asset applicability experiment is not met. No numerical protocol, data acquisition, renderer, new bound variant or additional source batch is queued. This closes this finite audit, not the broader research objective and not the possibility of a useful Gaussian-volume method.
