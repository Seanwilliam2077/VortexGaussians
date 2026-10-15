# P3g: one-step raw-field residual reuse

P3g tests whether retaining one step of information from an existing direct
correction improves accumulated tracer transport at the same tree-query budget.
The experiment is exploratory: one previously observed and one previously unrun
seed pair in the same stationary source condition. See the frozen
[P3G_PROTOCOL.md](P3G_PROTOCOL.md) for the full contract.

## Commands

Use the portable Node/Playwright setup in [README.md](README.md).
`PLAYWRIGHT_MODULE` can select an existing Playwright installation;
`BROWSER_EXECUTABLE` or `--browser-executable` selects Chromium/Edge. No local host
paths are hardcoded. Run browser measurements without competing browser workloads.

```text
node --test research/tests/*.test.mjs
node research/p3g-smoke.mjs --out research/runs/p3g-smoke-final
node research/p3g-run.mjs --suite quick --out research/runs/p3g-quick
node research/p3g-run.mjs --suite all --out research/runs/p3g-full --baseline research/runs/p3f-full --baseline-archive ../../outputs/p3f/VortexGaussians-P3f.zip
```

Existing manifests are never overwritten. Quick runs 15 steps per case and cannot
trigger timing. There is no timing-only bypass.

## Algorithm and comparison

Six complete quality trajectories are DD, curvature and memory at physics/render
pairs `(11,101)` and `(83,521)`. DD and curvature at the old pair also perform exact
immutable P3f replay. The checksum list pins the archived manifest and both raw
records to the frozen ZIP; before/after provenance checks cover these records and
every source file. Old binary files can be omitted in portable reproduction only
when their absence is explicit; their reference checksums remain authenticated by
the pinned records.

All physical, source, render and optical settings remain fixed: physical cap 600,
render cap 9600, source 180/s, `dt=1/60`, 180 steps. Curvature selection retains the
P3f fraction 0.1, grouping, seven-query models, score and salt. The memory branch
uses the same actual direct-query budget. A selected particle's direct raw field
minus its current **unclipped** affine field creates four residual components
`[ux,uy,uz,Tb]`, keyed by stable birth ID and creation frame. If unselected on the
immediately following step, that particle adds the stored residual to its new
unclipped affine field, then clips Tb to `[0,1.6]`, applies forcing and the usual
speed clamp. Reuse does not renew the entry. A current direct correction takes
priority and creates a new entry. Direct native Float32 temperature is not
additionally clipped.

Each step replaces the entire cache with current selected entries, including
entries whose particle retires during that step. Missing entries are explicitly
counted on the next step. Formal equal-budget interpretation requires no retirement
or missing particle IDs; these events cause a scientific quality failure rather
than silently reducing the comparison population. Extra affine evaluations for
cache creation, lookup and maintenance count as work even though they add no tree
queries.

## Raw evidence and audit scope

Each trajectory saves 181 physical/birth traces and separate tracer hashes,
13 Float64 particle arrays, six linear RGBA32F buffers and PNG previews: 78
particle arrays and 36 images in total. Twelve DD foreground/hole ROI records
contain 24 mask files. Four corrected trajectories save 12 full selection records
each, giving 48 selection JSON files.

The two memory trajectories additionally save every step as a separate JSON file:
360 records containing complete cache-before/cache-after, all created and used
events, actual input IDs, overlap/expiry identities and a deduplicated dictionary
of the models involved in those events. No extra direct truth queries are made.
Each event model retains its seven raw samples and derivatives. Its raw affine
value, residual origin, TTL, direct priority, nonrenewal and cache lineage can be
recomputed independently on every step. The full spatial partition is independently
checked only at the 12 full-input checkpoints; off-checkpoint event records alone
do not establish how every group centroid was constructed. Actual particle
velocity and Euler transport are cross-checked at the saved particle checkpoints.

`result.memoryEvents` contains file references and independently recomputed
summaries; the original production summary is retained under `events.summary` in
each raw file. `result.memoryTrace` retains the per-step cache hash and production
summary. `manifest.quality.memoryDetails` aggregates all 360 references; `exposure`
reports total reuse divided separately by previous live cache members, all current
inputs and current unselected inputs. Residual statistics keep velocity and Tb
components separate. There is no mixed-unit residual norm.

The snapshot cache hash uses FNV-1a of canonical ID/frame JSON containing four
Float64 little-endian hex strings per entry. Only its wire representation
canonicalizes negative zero to positive zero, preserving exact JSON round-trip
verification; residual arithmetic is unchanged. Hash format:
`fnv1a32-json-id-frame-residualF64LE-zero-canonical-v1`.

## Decision and timing

All six trajectories finish before the gate. On each seed separately, memory must
pass the original absolute image/path thresholds and strictly improve both worst
sampled position RMSE and worst sampled p99 over curvature. Query budgets must
match on every step, identities must remain complete, and actual reuse must be
nonzero. Exposure is reported continuously; there is no tuned exposure cutoff and
no cross-seed averaging to rescue a failed case.

A complete finite negative result retains `status: passed`,
`stageStatus: stopped_after_quality`, `protocolComplete: true` and an explicit
`timingSkipped` reason. `accuracyPassed` describes the absolute thresholds;
`memoryGatePassed` additionally requires improvement, exposure and budget checks.
Nonfinite state, invalid provenance or incomplete evidence is an execution failure.

Only a passed gate permits ten old-pair DD/memory timing runs, five alternating
orders AB/BA/AB/BA/AB. Each has 20 warmup frames, reset and 41 completed-frame
measurements at frames 60–180 every third frame. `gl.finish` drains prior work and
synchronizes completion. Grouping, model queries, selection, extra model
evaluations, cache management, advection and drawing all count. No event observer,
dense particle transfer or full-cache hash is inside the timed frame. Quality and
timing endpoint cache hashes and production summaries must match. Central cost is
the median of five run medians; tail is the median of five run p95 values, not
pooled-frame p95. Engineering continuation requires at least 1.5× speedup over DD
and no worse tail, after quality passes. The 256×192 images and single condition
remain diagnostics, not a general physical, visual-quality or performance claim.
