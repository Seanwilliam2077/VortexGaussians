# Independent integration review

27 October 2026. Scope: repository organization, historical evidence migration, CPU CLI inspection, and the art page shell. **No GPU, solver rollout, optimizer, new scientific experiment, or timing benchmark was run by this review.** The reviewed entries are usable within the tested scope; neither research contribution is established.

## Evidence and separation

The two tracks have different implementations and questions. `tog/` contains the unchanged R20 passive-smoke core plus a declared scene fork and a single-control inspection CLI. `art/` wraps the existing browser demo's public API. It does not use the TOG core. Neither line can use the other's functionality, images, or audits as proof of its own physical correctness, artistic value, or cost benefit.

The catalog identifies the R19–R22 reports and manifests by exact hashes. All copied PNGs and extracted result sources matched their sealed manifest entries. The ten included summaries/plots passed byte-count and SHA checks. Original report and archive paths are external-archive identifiers, not broken clone links. The full historical arrays and audits were not re-run during this migration. Original protocols under `tog/fixtures/` are historical documents; their old archive references do not become executable dependencies of the portable CLI.

R20's derivative failures and separate supplement, R21's inactive protection penalties, and R22's failed upper-region **rightward** displacement gate remain explicit. Internal audit counts are not counted as research contributions. Current repository functionality does not retroactively change the historical R22 pause or turn a failed task into a qualified one.

## What actually ran

| Check | Observed result | Boundary |
|---|---|---|
| Default TOG CLI | Validated the draft, zero rollouts, no numerical runtime imported | No target is attached; no feasibility or artist-need validation |
| `approve` without `--execute` | Planned only; output directory was not created | Did not generate an approved trajectory |
| `validate --require-target` | Rejected the incomplete draft with exit 2 | Expected rejection, not a test failure |
| `history --execute` | Recomputed the saved R22 image gate: 0 qualifying frames, maximum rightward shift 1.4065755548435703 pixels; historical task remains false | No forward simulation or new qualification |
| Existing CPU interface check | All 17 interface cases passed, including no Torch import and unchanged initial-state AST | Implementation checks, not scientific validation |
| Art page in headless Edge 149 | Blank iframe and disabled simulation controls initially; author note saved as literal text, survived reload, and appeared in downloaded JSON; incomplete audience note rejected | GPU and software rasterizer disabled; only HTML/CSS/JS requested, no demo or PLY |
| Current track prose links | 30 repository-relative links resolved; no failed linked file in this scan | Excludes immutable historical fixture prose and external websites |

Details: [CLI record](checks/cli.json), [HTML record](checks/html.json), [link record](checks/links.json). The [HTML smoke script](checks/html-smoke.cjs) starts and closes its own local server and a fresh browser context, and refuses to overwrite a prior result. It requires an existing Playwright installation and Edge, or explicit `PLAYWRIGHT_MODULE` / `BROWSER_EXECUTABLE` overrides; it installs nothing.

The first CLI harness attempt assumed UTF-8 while the Windows child emitted its native encoding. Only the harness was corrected with `python -X utf8`; application source and parameters were unchanged. This harness failure is retained in the CLI record.

## One concrete integration repair

Source review found that the new art slider initially wrote radians to `P.yaw`, while the existing demo computes azimuth as `P.yaw * Math.PI`. The art author corrected the adapter to `degrees / 180` and synchronized the slider with the actual initial scene angle. No original demo source was changed. The corrected source was used by the shell test; this review did not independently render a 60° scene to measure camera geometry.

Tested TOG source-manifest SHA256:
`3f6ade3b1fe2bbdd7b4fd65425a688b172d2ff4c54fdab826f37ca66f3ad99f7`.
Tested art JavaScript SHA256:
`8d404b2304d2ed0545da6eeecacb91fbb2020cc038da83168b9bbb7fa0987d8a`.
Both were unchanged across their tests; the HTML record also pins its HTML and CSS.

## Unimplemented or untested scope

The TOG CLI is an input/approval/control inspection interface, **not an inverse solver**. It does not find controls, run the historical low-rank experiment, or implement cache-assisted editing. The supplied brief is an unvalidated researcher draft with no authored target. An `approve` command generates a zero-control reference; it cannot itself establish human approval. A declared holdout role is not proof that the data were unseen. These limitations are correctly stated in the track documentation.

The art shell exposes a rehearsal and journal, not a finished artwork or audience study. Its reset is reinitialization; exported notes are not a resumable physical checkpoint. The built-in campfire is synthetic; a local PLY chooser does not establish the scene's provenance or artistic significance. The full demo load/ignite/advance/pause/reset and custom-asset paths, actual WebGL visuals, mobile layout, and cross-browser behavior were **not tested here**. They need their own UI record and must not be inferred from the shell check. Venue facts and publication readiness were not independently re-evaluated in this software review.

No known blocking issue remains for the tested portable entry points. Remaining scientific work is a qualified task and a real ordinary-method bottleneck; remaining art work is a concrete space, authorial choices, a complete experience, and actual observations. More interface checks cannot substitute for either.
