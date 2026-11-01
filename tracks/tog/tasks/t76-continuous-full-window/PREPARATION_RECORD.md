# T76 preparation/runtime identity record

2026-11-02, Asia/Shanghai. The first standard-library-only `prepare.py freeze` attempt at source commit d7bdc5e stopped with `ValueError: bundled executable changed`. All inherited nonarray evidence hashes and ten raw file lengths had been checked, but no T76 input manifest or invocation marker existed. No scientific worker, numerical import, raw-array body read/hash, trial, fit or integration occurred. This is a retained preparation failure, not a failed scientific invocation hidden by a retry.

The executable has the same path and107,312-byte length as T71, but a different SHA256:

- T71 identity, retained unchanged: `5640e9be2fd33d05a1a9ae1228e2354609a69ab831605995ec4e2bd6da8fff5e`.
- Current identity: `f8b45d63047da9d9adf09892e4cc4317b859e86a93a478cc9616bc69d3b176e5`.

Standard-library inspection reports the same Python3.12.14 build string and NumPy distribution metadata2.3.5. NumPy itself was not imported during this inspection. The reason or date of the binary change is unknown; it is not attributed to an installer or automatic update without evidence. Byte-identical runtime replay of T71 is not claimed.

Before the first scientific invocation, explicitly freeze the current runtime in RUNTIME.json and make preparation use that disclosed identity, while still validating the unchanged protocol versions. The worker will independently verify Python/NumPy versions during its charged run. No installation, numerical policy, optimizer constant, physical gate, resource allowance or historical source/result is changed. RUNTIME.json and this record join the frozen input list. The scientific one-invocation limit remains unspent.
