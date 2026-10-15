# P7 reproduction

Use the Node.js and Python/NumPy runtimes recorded in the evidence. From the
extracted source directory, inspect `PROTOCOL.md`, then run:

```sh
node --test test.mjs
python audit.py ../formal --source-dir . --freeze ../freeze.json --out ../new-audit.json
node --expose-gc run.mjs --formal --freeze ../freeze.json --out ../new-formal-run
```

Use fresh output paths; never overwrite the archived run. A completed producer still requires
the independent audit. A valid negative decision must not be converted into
a passing result by modifying the frozen thresholds or scene.
