# P4a: standard thermal-exchange substrate

This is a numerical foundation for a later gas–surface combustion study. It is isolated from the browser demo and all frozen P3 experiments. It does not render fire or claim a new simulation algorithm.

The full scientific contract is in `P4A_PROTOCOL.md`. Commands and file names below have been checked against the implementation; formal results remain pending until root freezes the sources and runs the complete matrix and independent audit.

## What the test computes

Surface nodes carry explicit area and heat capacity per area. Gas nodes carry explicit volume and heat capacity per volume. A compact distance kernel defines their pair conductance. Every substep moves exactly the same signed heat quantity out of one reservoir and into the other. Temperatures update simultaneously. A capacity-based CFL rule selects substeps to preserve the initial temperature range without clipping.

The 21 cases cover an analytic pair, reversed heat flow, a disconnected pair, stiff substepping, coincident measure splitting, order changes, rigid transformation, temporal refinement, spatial refinement, and an intentionally one-sided negative control.

## Evidence to preserve

Each case must retain its complete input scene, configuration, initial state, all outer-step temperature vectors and transfer ledgers, final state, source fingerprint, and checks. The formal manifest lists all cases and comparison results. The independent audit reconstructs the exchange operator from input geometry; it separately checks actual Euler substeps and the matrix-exponential solution of the finite spatial graph.

The primary hard checks are relative energy/ledger residual `1e-12`, temperature bounds and independent Euler agreement `1e-9 K`, common-anchor invariance `1e-9 K`, and decreasing temporal-reference RMSE for the specified pair/corner timestep series. Spatial-refinement values are descriptive. The one-sided control intentionally violates energy conservation and is not a fair physical baseline.

## Reading a result

- A runner completing all cases means the evidence was generated; it does not by itself mean every numerical contract passed.
- An independent audit passing means the saved data and reported checks agree within the declared tolerances.
- Exact pair/finite-graph agreement is about this mathematical model. It is not a validation against a real fire or a continuum flow solver.
- Split invariance assumes physical measure is supplied and split correctly. It does not recover missing material mass from a PLY file.
- A later live VPM connection must account for birth, death, changing capacities, advective transport and sources/sinks explicitly. P4a does not exercise these operations.

Do not import P3 position-error thresholds or performance claims into this phase. There is no browser timing benchmark here, and passing these standard correctness tests is not a claim of publication readiness.

## Commands

From the repository root, with Node.js available:

```sh
node --test research/tests/p4-thermal.test.mjs
node research/p4a-run.mjs --help
node research/p4a-run.mjs --suite quick --out research/runs/p4a-quick
node research/p4a-run.mjs --suite all --out research/runs/p4a-full
```

Output directories must be empty; the runner refuses to overwrite prior evidence. The quick suite contains four shortened exploratory cases and is not the full scientific protocol. It must not be presented as complete temporal/reference validation.

`p4a-design.mjs` defines the immutable matrix and authored geometry/material inputs. `lib/p4-thermal.mjs` implements the conservative exchange. `p4a-run.mjs` writes `manifest.json` and one JSON record per case. The manifest checks hashes before/after execution and reports `referenceStatus: pending-independent-audit`: a passed runner deliberately does not claim the separate matrix-exponential and independent-substep audit has already passed.

The independent Python audit is a separate delivered script outside this numerical module. Its exact invocation belongs to the final artifact's recovery instructions; it must read these saved inputs and raw states and rebuild the operator independently. Do not substitute the runner's own exported edges or its two-reservoir summary for that audit.
