# P7b reproduction

This small archive requires the complete `VortexGaussians-P7-shared-state-screen.zip`
identified in `dependency.json`. Put it beside the extracted P7b directory.
Use Python with NumPy and Node.js; verified versions are recorded in the evidence.
From the extracted `source` directory, first verify the archived follow-up:

```sh
python audit_b.py ../formal --source-dir . --freeze ../freeze.json --parent-archive ../../VortexGaussians-P7-shared-state-screen.zip --parent-extract ../new-parent --parent-out ../verification/parent-re-audit.json --out ../verification/independent-audit.json
```

The auditor authenticates the entire parent ZIP before extracting it, executes
its frozen independent auditor, and checks all new proxy32 evidence. Both audit
outputs and the extraction directory must be fresh. This does not simulate a
new physical trajectory. To run a new follow-up using that verified extraction:

```sh
node --test test.mjs
node --expose-gc run.mjs --formal --freeze ../freeze.json --baseline-root ../new-parent --parent-archive ../../VortexGaussians-P7-shared-state-screen.zip --out ../new-formal
```

Audit that new run with `--baseline-root ../new-parent` and fresh audit output
paths. Do not substitute a different parent, alter a pin, or overwrite evidence.
The parent trajectory counts are inherited, and all follow-up timing must be new.
