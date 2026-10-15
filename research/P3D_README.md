# P3d: specialize the DG field queries

P3c found low error for direct induced velocity with interpolated temperature. P3d removes redundant queries from that already tested model: cache nodes evaluate only temperature, while tracers query only induced velocity. It compares DD, DG-original, and DG-specialized at fixed spacing 0.035. This is an engineering experiment on previously observed conditions, not a new heldout test or a new numerical-method claim. See [P3D_PROTOCOL.md](P3D_PROTOCOL.md) for the frozen contract.

The quality matrix has 27 trajectories: three forcing conditions, three paired seeds, and three methods. Every trajectory records 181 physical/birth trace rows plus a separate 181-entry tracer hash trace, 13 double-precision particle checkpoints, and six linear RGBA32F images. DG-specialized must reproduce DG-original exactly at every tracer-hash step and every particle/image checkpoint. DD and DG-original must also reproduce the corresponding immutable P3c traces, old snapshot fields, and recorded binary hashes.

The timing matrix has 45 independent runs. Each run warms up for 20 frames, resets, and samples every third frame from frame 60 through 180 (41 samples). GPU work completes with `gl.finish` before and after measured frames. This measures synchronized wall-clock frame latency, not pure GPU time. The 1–3 second measurement window contains a growing particle population; it is not steady state. Tracer cache construction, query, interpolation, advection, sort/upload, draw submission, and completion are included. Tracer substages are parts of `tracerMs` and must not be added to the frame total again.

Timing uses the lightweight physical/birth trace, with no dense per-frame tracer hash or snapshot collection. Quality hash collection runs separately. Five repeat orders are fixed in `p3d-design.mjs`; three Latin rotations and two reversed orders provide partial, not perfect, position balance.

Run from the repository root:

```text
node --test research/tests/*.test.mjs
node research/p3d-smoke.mjs --out research/runs/p3d-smoke-final
node research/p3d-run.mjs --suite quick --out research/runs/p3d-quick --baseline research/runs/p3c-full
node research/p3d-run.mjs --suite all --out research/runs/p3d-full --baseline research/runs/p3c-full --baseline-archive PATH_TO_IMMUTABLE_P3C_ZIP
```

The existing `research/package.json` supplies Playwright. Alternatively set `PLAYWRIGHT_MODULE`. Select an installed browser with `BROWSER_EXECUTABLE` or `--browser-executable`; no host-specific path is embedded. Supported suites are `all`, `quality`, `timing`, and `quick`. Only `all` sets `protocolComplete:true`. All suites retain `exploratory:true`. `quick` is three 15-step trajectories, with partial baseline checks explicitly labelled. It cannot satisfy the full engineering decision. Output manifests are never overwritten.

`lib/p3d-baseline.json` pins SHA256 hashes of the P3c manifest and 18 DD/DG raw JSON records, read directly from the archived delivery with SHA256 `204ebcebc2586a290a9f6eeca527766cdfb5f95d49d2c54bfcbbb9563e3eaee3`. The runner verifies every pinned JSON before and after its run. If `--baseline-archive` is supplied, that ZIP must have this exact SHA. The manifest records its path/hash, the pin-list hash, and the old source fingerprints. Portable reproduction may use the authenticated 19 JSON files in `baseline/p3c-full` without duplicating the large archive. Reference binary hashes then come from those authenticated records; any reference binary files present are additionally rehashed. All newly generated binary files are always rehashed. Missing old binaries are counted explicitly and do not become fabricated equality tests.

Full output includes 351 Float64 particle files, 162 RGBA32F files, 162 preview PNGs, 108 byte masks, and 1,845 synchronized frame samples. Binary metadata includes dimensions/layout/orientation and SHA256. The raw quality JSON holds `trace`, `tracerTrace`, `snapshots`, `checkpoints`, and `captures`; raw timing JSON holds `initial`, `final`, `trace`, `timings`, and distributions. Readback and preview capture occur outside timed frames.

`manifest.quality` contains 18 comparisons against DD, fixed DD reference masks, nine exact specialized/original equivalence records, 18 old-path regression records, and visible failures. `manifest.timing` contains nine method/condition summaries. Central cost is the median of five run medians. Tail cost is the median of five run p95 values, not pooled-frame p95; all run and raw-frame records remain available.

`manifest.decision` separates `evidenceComplete` from `accuracyPassed`. A measured accuracy or cost failure is a valid negative result. `engineeringGo` requires complete valid evidence, the unchanged accuracy checks, and—in every condition—DG-specialized central speedup of at least 1.5 over DD with median-of-run-p95 no worse than DD. No seed, scale, threshold, or condition is reselected after seeing the measurements. Any provenance failure also prevents an engineering-go result.

New query counters distinguish full, velocity-only, and temperature-only queries. Thermal-support rates use only queries that actually requested temperature. In specialized DG, `componentDirectNoThermalSupportQueries=0` because those direct queries did not request temperature; it does not demonstrate thermal support at every tracer. The dedicated sampler smoke checks exact component equality on real points and synthetic leaf, accepted-cluster overlap, unsupported, and empty cases, together with absence of work for an unrequested component.
