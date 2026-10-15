# P6 reproduction

Verified runtimes are recorded in formal/manifest.json and the audit output.
Use Node.js with --expose-gc and Python with NumPy. From the extracted `source`
directory, run:

```sh
node --test test.mjs
python audit.py ../formal --source-dir . --freeze ../freeze.json --out ../new-audit.json
node --expose-gc run.mjs --formal --freeze ../freeze.json --out ../new-formal-run
```

Choose new output paths. Original evidence is never overwritten. The producer
reports completion pending independent audit; execute the auditor on a new run
before interpreting any measurements. The archived P4 reference is an unchanged
test fixture, not a timed competitor. All timings cover only this synthetic
finite-capacity heat-exchange component, not a complete frame or fluid solver.
