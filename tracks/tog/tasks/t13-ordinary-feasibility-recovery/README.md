# T13: ordinary feasibility recovery did not find an alternate

27 October 2026. One fixed ordinary Phase-I run is complete. **No non-seed observation-feasible state was found**, so no future branches or final response evaluation were run. This ends method development on this particular T12/T13 input contract under the [decision made before T13](../t12-ordinary-wind-response-extrema/NEXT_PHASE_I.md). It is neither proof of a unique reconstruction nor evidence that a specialized solver is needed.

T12 attempted to vary a local-wind response while fitting its original observation intervals. T13 instead asks whether the same ordinary optimizer can recover feasibility from the existing fixed G0 perturbation. It removes the response term and retains the data, velocity parameterization, physics, camera, 163842 inequalities and original acceptance gates. The changed starting point means this is not a controlled causal explanation of T12's failure or an equal-cost speed comparison.

## Result and cost

| Item | Actual result |
|---|---|
| New PHR-only derivative qualification | Passed; 9 observation evaluations, 1 reverse call, 2.730 seconds |
| Search | 78 observation evaluations, 77 reverse calls, 36 returned steps, 36 exact-input cache hits and 0 acceptance misses |
| Termination | All 3 outer rounds of 12 returned steps completed; no additional search after the fixed budget |
| Least-violating evaluated point | Evaluation 68, recorded as `line_search_or_closure`; a failed diagnostic, not a feasible witness |
| Original observation gate | 170 of 81920 pixels exceed the unchanged 1e-10 alpha allowance; maximum excess 4.6896847252703155e-5 |
| Diagnostic velocity distance from reference | Maximum component difference 0.0032560496472345338; relative L2 distance 0.012108841948520185 |
| Search time including evidence IO | 36.881 seconds |
| Complete 60-step future evaluations | 0; no candidate met the gate |
| Whole new numerical work | 87 observation evaluations, 1740 physical steps, 78 reverse calls; 55.613 worker seconds |
| Qualification allocator peaks | 1,189,322,752 allocated / 1,210,056,704 reserved bytes; not a whole-process GPU-memory measurement |

The diagnostic's observed prefix passes numerical validity and the original initial-velocity priors. Its 170 quantized-code differences are each one code value. The fixed starting point had 1965 interval violations. Improvement in these measures does not turn the remaining violation into acceptance. The unchanged wind response `d` is **not evaluated for the failed point**, and no response range or zero-valued future is supplied. The nonidentity threshold only excludes numerical identity; its distance is not evidence of useful ambiguity.

The whole worker includes initialization and input loading beyond the separately recorded qualification/search times; its enclosing supervisor took 56.454 seconds. Input-pack preparation copied existing arrays once on CPU in 0.099 seconds with zero simulation. T12's prior discovery and reference-generation work remain prior costs; T13 is not a cold reconstruction from unseen observations.

## Reviewable artifacts

- [Protocol](PROTOCOL.md), [config](config.json), [frozen source/input identities](freeze.json), and [portable input manifest](inputs-manifest.json).
- [Independent pre-run review](../../../validation/t13-pre-run-review.md) verifies the original array bytes and operation-identical observation/future loops. Default plan imports no Torch and runs no simulation.
- [Independent saved-array review](../../../validation/t13-array-review.md) and [publication](publish-01/README.md) provide arithmetic checks, full-frame observation diagnostics and compact evidence. These are CPU-only postprocessing, not extra fits.
- [Root publication review](../../../validation/t13-publication-review.md) checks the actual figure and all 13 output file hashes.
- [Next decision](NEXT_DECISION.md) closes this numerical input contract and sets the next bounded research question.

Raw `runs/run-01/` contains the supervisor, summary, logs, qualification arrays, least-violating observation and two multiplier-update records, and is ignored by Git. Full unrecorded trial trajectories cannot be independently re-rendered from the scalar call log. The compact publication authenticates its selected original arrays; it does not claim to preserve every trial parameter.

The runner SHA256 is `0c35cd801bb4930679044b9b8490336b2de05978459b0e51d83b53fb390dcdbe`; the freeze SHA256 is `7615e63bf6e4868566290423f7925d192a035ae5bc32f4157daea726f9a70b12`. Runtime input tensors and frozen sources remained unchanged. T12 and earlier sources, failures and acceptance criteria are preserved.

## Commands

From the repository root, a standard-library-only plan is:

```sh
python -I -B tracks/tog/tasks/t13-ordinary-feasibility-recovery/runner.py
```

The existing 1.13 MB input pack is sufficient for the numerical runner; it does not require old ignored raw files. `prepare_inputs.py` documents the already-completed, byte-preserving extraction and refuses to overwrite the pack. Explicit replay uses the pinned CUDA runtime and a fresh output name:

```sh
python -I -B tracks/tog/tasks/t13-ordinary-feasibility-recovery/runner.py --execute --out runs/replay-explicit
```

Replay is not queued. This run does not establish a creator requirement, broad inverse-problem difficulty, or a TOG contribution, and does not reopen the completed protection-cache route.
