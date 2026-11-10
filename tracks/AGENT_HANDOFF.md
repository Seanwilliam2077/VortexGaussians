# VortexGaussians — agent handoff, 2 November2026

**Current override, 10 November 2026:** the user has resumed technical research and requested an update of current related papers. Art remains paused. Read the newest [STATUS](STATUS.md), [T82](tog/tasks/t82-current-literature-resumption/BRIEF.md) and T81 record before acting. The pause and next-step descriptions below preserve the original 2 November handoff; they are superseded by the current technical authorization. Remote main has independently advanced to `a7dfa98`; do not merge its revised demo into T81's frozen source.

## Current authority and immediate action

**Research is PAUSED by the user.** The latest request authorizes publishing existing research and a substantial handoff/data package only. Do not launch T81 or resume art/technical iteration until the user resumes research.

Repository: https://github.com/Seanwilliam2077/VortexGaussians (verified public).
Research branch: research/dual-track-exploration. Main remains the historical deployed project; do not merge/deploy it automatically. All prior art and technical work is preserved in this branch's history. The older research/p0-coupling-validation branch is an ancestor.

For a fresh machine, check out the research branch explicitly:

```sh
git clone --branch research/dual-track-exploration https://github.com/Seanwilliam2077/VortexGaussians.git
cd VortexGaussians
```

No Git LFS download is needed for the new handoff archives. Verification uses Python's standard library; historical experiments have separately recorded runtime and asset requirements.

Read this document, [STATUS](STATUS.md), [EXPLORATION](EXPLORATION.md), [TOG entry](tog/README.md), then [T81 resume record](tog/tasks/t81-firewoods-capacity-causality/README.md). The beginning of STATUS/EXPLORATION supersedes their historical entries. Their many older “next tasks,” active statuses and artistic viewing requests are historical, not a new queue.

## Actual objective and publication state

The user requires a credible TOG/SIGGRAPH technical contribution, permits abandoning original implementation preferences, and allows a limited system contribution. Success needs a worthwhile graphics problem, an identifiable new technical mechanism, strong ordinary alternatives, relevant evidence and reproducibility. Engineering checks, many iterations, a single passing development task, or agent approval do not establish that contribution.

**No TOG core contribution is established.** The historical technical rating2/6 is an internal author-side diagnosis, not a current regrade or external peer review. Art was separately paused before the whole research pause. Keep its files and historical reviews; do not start art production/writing/scoring or manufacture human feedback. Its historical A57 scores are both4/6; the requested5/6 was not reached. No actual user reaction is needed to run a future independently justified technical diagnostic.

## Research map and decision-changing evidence

| Area | Where to read | What to retain |
| --- | --- | --- |
| Original visual system | [root README](../README.md), [demo](../demo/index.html), [evidence status](../research/EVIDENCE_STATUS.md) | Layered heuristic fire/smoke rendered as splats; simulation kernels and visual covariance are distinct. Historical timings do not establish current physical accuracy or new contribution. |
| Coupling/shared-state studies | [research](../research/README.md), [P1](../research/P1_README.md), [evidence status](../research/EVIDENCE_STATUS.md) | Independent thermal state is a strong ordinary alternative; cold recycling deletes state and scans a layer. Do not insist on shared simulation/render storage. |
| Smoke editing/control | [TOG interface](tog/README.md), tasksT02–T15 | Ordinary methods solved two development edits. No established repeated-edit protection-cache bottleneck; do not invent a third analogous toy or require a cache. |
| Volume/output studies | tasksT16–T40 and their READMEs/decisions | Different volume, output and carrier contracts were investigated. Read individual records before reusing a model or conclusion; they are not all the same physics/rendering model. |
| Existing real-asset workflow | [T41](tog/tasks/t41-firewoods-workflow-entry/README.md), [T42](tog/tasks/t42-firewoods-sequential-workflow/README.md) | Original A→B Firewoods ignition preserves material state but is visually ambiguous. No A-only counterfactual or per-source emission attribution was recorded. This motivates T81. |
| Carrier/compact dynamics | tasksT43–T74, [T73 assessment](tog/tasks/t73-contribution-assessment/README.md) | Known heat-kernel contractions, generic birth logic and pure shear do not yet establish a new method. Preserve narrow failures; do not turn them into all-family impossibility. |
| Strong ordinary dynamics | [T75](tog/tasks/t75-saved-tangent-diagnostic/README.md), [T76](tog/tasks/t76-continuous-full-window/README.md) | Geometry directions plus ordinary nonlinear polishing resolve the original full-window case. Two reference resolutions are not two scenes. |
| Recent prior-art/operator audits | [T77](tog/tasks/t77-deformation-evaluation-screen/README.md), [T78](tog/tasks/t78-vpfm-transfer-audit/README.md), [T79](tog/tasks/t79-moving-domain-circulation/README.md), [T80](tog/tasks/t80-anisotropic-evaluator-contract/README.md) | No new method selected. Exact P2G low-rank assumption is unsupported; moving solids do not automatically produce nonzero first homology; planar Gaussian fields have strong ordinary exact evaluators. |
| Next finite question | [T81](tog/tasks/t81-firewoods-capacity-causality/README.md) | Frozen plan only, no implementation/run. Test whether per-layer quotas reject useful emission while global capacity remains idle, retaining the original recipe. |

The machine-readable [catalog](evidence/handoff-2026-11-02/CATALOG.json) indexes tracked task/study documents, protocols and result artifacts. Titles/status excerpts there are historical; this document defines the current pause.

## Most relevant numerical facts

T76: ordinary two-Gaussian, axisymmetric no-swirl free-space Euler, t=0..1; independent h=1/16 and1/32 paths. Original physical and sensitivity gates all pass, nine numerical qualification categories. Fine final S256 relative field/covariance errors0.04753653/0.07636064; maximum inter-path field/covariance differences0.00465464/0.00493634. All48 polishes improve their seeds but stop at no_accepted_line; no stationarity/global-optimum certificate. Fine impulse drift about3.4344% is an observation, not a new failure gate. Full child31.5586529seconds. T71's earlier time sensitivity stays historical.

T42:9 layers×600 nominal slots, original block admission. After3seconds2394 gas particles; after6seconds2433. The second interval has8640 feed attempts,8553 capacity rejections,43 new emissions. The source checks the target layer's600 cap. Global occupancy below5400 does not prove free redistribution has equal computational cost. Source selection is already round-robin; graph service separately processes a fixed1400-source prefix. Do not confuse the two.

T81: all four runs would retain the original policy through frame180, then cross A-only/A→B with per-layer/global blocking. Same asset, camera, seed, targets, timing and total slots. No recycling or particle relocation. The first half must match across arms; native RNG differences after changed admission are part of the policy effect. Detailed causal qualifications and unconsumed budget are in its brief.

## What is now available from Git

The [handoff evidence package](evidence/handoff-2026-11-02/README.md) adds:

- T76's complete original scientific journal, losslessly compressed.
- All ten original S128/S256 reference NPZ files used by T76, plus twelve companion metadata files, losslessly compressed with original hashes.
- Six T42 complete per-material dynamic-state projections:208,122 rows, plus frontier, gas aggregate, RNG and native counter data; a scalar execution ledger. External scene geometry/appearance/images are excluded. Original T42 never exported full gas arrays, so these cannot be recovered or claimed present.
- File identities, decompressed hashes, archival scripts and a standard-library verification entry. Existing complete T76 result/prediction/scalar reports and all historical source/protocol files remain at their original tracked paths.

Verify the package without simulation:

    python tracks/evidence/handoff-2026-11-02/verify.py
    python tracks/tog/tasks/t76-continuous-full-window/summarize.py

Do not run a spent run_once.py or delete invocation.json to repeat an old experiment. If a future reproduction is approved, restore reference bytes to a separate checkout or inspect the archive in place, qualify its runtime, and create a new execution directory/identity. The archive improves data availability; it does not certify cross-platform bitwise replay or complete portability of every historical harness.

Still external: the Firewoods third-party PLY/source photo and license provenance; downloaded third-party papers/repositories; large unrelated historical raw output; private notes. Their exact identifiers are in the relevant manifests. No new asset download or publication is required merely to inspect the archived numerical evidence.

## Resume mechanics and constraints

Original local workspace was C:/Users/seanzjxiao/Documents/Codex/2026-10-13/https-github-com-jiarui-liu-ideascientist/work/VortexGaussians. That absolute path is not a portable assumption. The outer workspace contains work/real-asset-ingest and outputs/. On a new machine, first establish which required assets/runtime are available; never treat a missing ignored file as an experiment failure.

1. Confirm explicit resumption and current scope. Check worktree, branch and real process handles before doing work; do not infer a running job from a status file.
2. Re-read T81 sources and verify inputs. Its implementation task was interrupted before writing an adapter or runner. Finish/review them before freezing executable identities.
3. Preserve original demo/art/main bytes, historical gates, failures and scores. Stage temporary research copies only for the declared intervention.
4. Freeze one informative question, budget and interpretation before execution. Exploratory diagnostics need a falsifiable question and fair ordinary alternative; they do not need an already proven novel solution. A new method claim still needs actual evidence of improvement.
5. Record failed attempts and full costs, including unsuccessful candidates, setup/reference/IO and cleanup. Current selected scientific-child subtotal2049.958372399793seconds is not total project cost.
6. Update current state, evidence and resume instructions, commit and push the research branch. Do not restore recurring automation or merge/deploy main automatically.

All reviews by collaborating agents are internal diagnostics. Record participation and what was actually read/run. Never replace a disappointing reviewer solely to raise a score.
