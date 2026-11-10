# T81 public numerical evidence

Sixteen gzip files,7,523,115 compressed bytes, archived from the sole T81 run. [MANIFEST](MANIFEST.json) records compressed/decoded identities and binds the passing SUMMARY to its exact original result report. No browser or solver is needed to inspect these files.

- Four `*-steps.jsonl.gz` files are byte-identical copies of all360 original per-frame records for each arm. They include the ten-column offer arrays defined by `adapter.js`, source IDs, outcomes, occupancy, counters, RNG draw counts, native attrition and instrumented timings.
- Twelve `*.dynamic.json.gz` files cover prefix, zero-time intervention and endpoint for all four arms. Each includes all34,687 material rows (`id,fuelInitial,fuel,heat,char,glow,state`), frontier/cursor/counters, full project-generated gas fields and emission-source observation labels. Geometry and appearance from the external reconstruction, images and camera are not republished.
- Native auxiliary continuation state (`vpmTick`, source, pointer and other values) is omitted. Native selected-field hashes and recorded RNG counts are not complete-state certificates. These projections cannot restart the original dynamics. Emission-source labels do not establish unique combustion ancestry.

From the repository root, verify the archive with standard Python:

    python tracks/tog/tasks/t81-firewoods-capacity-causality/verify_public.py

The successful local audit in `audit_saved.py` additionally used original captures, the external asset and frozen runtime files; it is not a portable new simulation command. Do not delete `invocation.json` or rerun the consumed experiment on a fresh clone. Reproduction on another runtime requires a new explicitly scoped protocol and must preserve this historical result.
