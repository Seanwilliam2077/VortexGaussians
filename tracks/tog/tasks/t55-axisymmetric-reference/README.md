# T55 — qualify the initial free-space vortex-ring reference

The single fixed run passes all eight initial spatial checks. An ordinary axisymmetric finite-volume Poisson reconstruction with free-space Green boundary values gives core velocity/Jacobian relative errors of 0.000920243/0.000493457 on the finest grid, with approximately fourfold reductions under each spatial refinement. Five cases take 3.9182514 supervised child seconds. This qualifies only the initial reconstruction; no fluid trajectory or candidate method was run.

- [Physical task](TASK.md): researcher-defined coherent vortex-ring displacement and shape, with future physical and reference requirements fixed before trajectories.
- [Formulation](FORMULATION.md) and [bounded primary-source audit](SOURCES.md): physical convention, normalization, axis, free-space reconstruction and limitations.
- [Frozen protocol](PROTOCOL.md), [input manifest](input-manifest.json), [implementation](reference.py) and [single-invocation supervisor](run_once.py).
- [Results and costs](RESULTS.md), [machine result](result.json) and [execution receipt](execution.json).
- [Saved-data/math review](../../../validation/t55-reference-review.md) and [next evidence](DECISION.md).

The D96 control changes both domain and quadrature orders; it is a combined sensitivity check. No time-dependent boundary, advection, finite-time accuracy, full 3D workload, creator validation, formal error certificate or novel TOG contribution follows. Raw arrays remain ignored locally. Historical failures, art inactivity, main and deleted automation remain unchanged; the full research goal stays active.
