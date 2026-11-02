# Research data and agent handoff — 2 November 2026

Start with [AGENT_HANDOFF](../../AGENT_HANDOFF.md). Research remains **paused**. This package publishes existing evidence; it contains no new scientific execution, score or contribution claim. The research branch is `research/dual-track-exploration`; the deployed `main` branch is unchanged.

## Included data

| Package | Contents | Gzip files | Compressed bytes | Decoded bytes |
| --- | --- | ---: | ---: | ---: |
| [T76](t76/manifest.json) | Ten original S128/S256 reference NPZ files, twelve original metadata JSON files, complete original scientific journal | 23 | 105,283,251 | 277,342,991 |
| [T42](t42/MANIFEST.json) | Six full per-material dynamic-state projections, plus a scalar execution ledger | 7 | 775,503 | 6,008,891 |
| Total | Existing project-generated evidence | 30 | 106,058,754 | 283,351,882 |

The compressed data total is **101.146 MiB**. The largest individual file is 18,515,614 bytes. The package uses ordinary Git blobs, so a normal checkout obtains these data without Git LFS or an external download. This is an intentional inclusion of substantial project-generated records, not publication of third-party assets or private notes.

T76 is a **lossless archive of original bytes**. Its manifest connects each archive to its original repository-relative path, byte count and SHA256, plus the frozen T76 input/execution receipts. The journal is the complete 178,721,100-byte record, not a selected success excerpt. NPZ files were treated as opaque bytes during archiving: no solver, NumPy computation or refitting was run. See [preparation history](t76/PREPARATION.md), including the initial archival size limit and its explicit revision. Existing [T76 result](../../tog/tasks/t76-continuous-full-window/result.json), [predictions](../../tog/tasks/t76-continuous-full-window/predictions.json), [scalar summary](../../tog/tasks/t76-continuous-full-window/SUMMARY.json), [protocol](../../tog/tasks/t76-continuous-full-window/PROTOCOL.md) and source code remain in their original tracked locations.

T42 is a **documented projection**, not a lossless archive of the whole external scene snapshot. Every checkpoint includes all 34,687 original material rows with `id, fuelInitial, fuel, heat, char, glow, state`: 208,122 rows across six checkpoints. It also retains recorded frontier, gas aggregates, RNG/native counters and original native hashes. `hash` and the narrower `particleStateHash` cover different selected native inputs, including particle fields omitted from this projection; neither is a complete-state or restoration certificate. The manifest records both original source identities and newly exported byte identities. Third-party positions, geometry, appearance, covariance, camera and rendered scene images are excluded. The original records never contained full gas-particle arrays, per-source emission outcomes or an A-only trajectory; this archive cannot supply them. The original visual task remains unqualified.

## Inspect and verify without simulation

From a checkout of the research branch:

```sh
python tracks/evidence/handoff-2026-11-02/verify.py
python tracks/tog/tasks/t76-continuous-full-window/summarize.py
```

Both commands read saved evidence. The first needs only Python's standard library and checks archive identities, decompressed identities and the T42 projection schema. The second recomputes a scalar readback of saved T76 results; it does not execute the solver. Verification success establishes archive integrity, not scientific validity, replay portability or paper readiness.

The saved [validation receipt](VALIDATION.json) records successful verification of all 30 archives, T42's 208,122 material rows and a real restoration of all 23 T76 originals into a new directory outside the repository. Each restored file was hashed again from disk. The same readback retained T76's original ordinary-baseline verdict; no new trajectory was run.

For offline inspection of original T76 files, optionally extract to a **new, nonexistent directory**, never the active checkout:

```sh
python tracks/evidence/handoff-2026-11-02/verify.py --restore-t76-to ../vortex-t76-restored
```

The verifier first validates the entire package, then preserves the original repository-relative directory tree beneath the new destination. It rejects an existing root and unsafe paths. Extraction does not install dependencies, run a simulation, recreate a complete checkout or reset any spent one-shot guard. The metadata is byte-preserved: absolute workstation paths inside it remain historical. The two aggregate T60 metadata files also reference final arrays and step logs outside the T76 input allowlist; these extra files are not included.

## Find the rest of the research

[CATALOG.json](CATALOG.json) inventories the repository's tracked research tasks, art studies and supporting files with canonical Git-blob byte counts, SHA256 and Git object identities. These identities are independent of checkout newline conversion. Its historical titles are navigation aids, not current authorization or fresh judgments. [build_catalog.py](build_catalog.py) generates the inventory after publication documents are staged, excluding this handoff package and the three changing status/handoff documents. It does not traverse ignored raw data or personal notes.

- [Current status](../../STATUS.md), [exploration record](../../EXPLORATION.md), [central handoff](../../AGENT_HANDOFF.md).
- [T80 completed ordinary-evaluator audit](../../tog/tasks/t80-anisotropic-evaluator-contract/README.md).
- [T81 paused implementation plan](../../tog/tasks/t81-firewoods-capacity-causality/README.md): the next finite question after explicit resumption; its four-arm budget is unconsumed.
- [Art workspace](../../art/README.md) and [A57 historical paper/reviews](../../art/studies/a57-room-argument-revision/README.md): preserved, still paused.

Not all historical external bytes are republished. Third-party Firewoods geometry/photo, downloaded papers/repositories, unrelated large historical output and private notes remain external. Read the relevant frozen manifests for their exact identities and provenance; check availability and redistribution terms before obtaining or using an asset. The next agent must distinguish an unavailable input from an experimental failure. Do not repeat an old run merely to fill an archive gap.
