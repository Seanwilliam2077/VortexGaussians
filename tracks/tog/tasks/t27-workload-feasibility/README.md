# T27 — learned-workload feasibility decision

29 October 2026. **NO_GO_AS_IS: the inspected local setup is not ready for the fixed official training recipe, and observation-data conditions remain unresolved.** This is a concrete preparation result, not a finding that this GPU cannot train a useful representation. No execution protocol or numerical job is prepared.

## What changed

The [frozen protocol](PROTOCOL.md) asked whether one transparently researcher-trained Vol3DGS representation could provide a practical next input after T26 closed its bounded ready-checkpoint route. Five fixed recipe/dependency files were acquired successfully: 166 lines and 11,103 bytes, all matching saved Git-tree identities. The [recipe analysis](RECIPE_CONTRACT.md) resolves the environment, installer and scene flags without executing them.

One bounded [environment probe](probe_environment.py) completed in 26.157 seconds. The [sanitized receipt](environment-summary.json) identifies a Windows 11 machine with an RTX 5070 Laptop GPU, about 8GB VRAM, and an installed PyTorch 2.11.0+cu128 that discovers the device. Compiler entry points were not found in the queried locations; SlangTorch and several required distributions are absent from this selected environment's metadata. The recipe instead prescribes Python 3.9, torch 2.0.1, CUDA 11.7 and SlangTorch 1.3.7 with Bash/Unix setup. Device discovery is not extension compatibility, memory-fit or throughput evidence. Details and unresolved costs are in [ENVIRONMENT_AND_COST.md](ENVIRONMENT_AND_COST.md).

The [official observation-source audit](DATA_SOURCE.md) identifies an author-linked Mip-NeRF360 archive advertising 12,535,427,936 compressed bytes. No archive-body bytes were read. The inspected page supplies no explicit data-use terms found by this audit; members, selected-scene extent and extracted storage remain unverified. This limited gap is not a claim that research use is prohibited.

The initial web extraction hid the literal archive href. A [post-initial-access transport clarification](METADATA_CLARIFICATION.md) used the optional description-page slot to read the same page's HTML, followed by one HEAD request to its observed first archive URL. The original protocol/freeze remain unchanged. This is disclosed as an adjustment after initial access, not retroactive preregistration. All three metadata calls were consumed; no extra source family or retry was added.

## Accounting and qualification

| Work | Actual | What it establishes |
|---|---:|---|
| Fixed recipe/dependency source | 5 files / 166 lines / 11,103 bytes | Published setup and flags; not an executable lock |
| Data metadata | 3 calls; zero archive-body bytes | Observed source and advertised compressed size |
| Saved content / metadata receipts | 26,755 bytes | Local representations, not network-traffic measurement |
| Saved response wrappers | 28,889 bytes | Separate acquisition records |
| Local probe | 1 invocation / 26.157 seconds | Current resource and discovery snapshot |
| Installed-torch query | 1 / 25.813 seconds | Version and CUDA-device discovery only |
| External executable probes actually launched | 2 | nvidia-smi and wsl; missing commands not retried |
| Installations, tensors/models, builds, training, numerical comparisons | 0 | No execution qualification or performance result |

CUDA discovery can initialize driver/runtime state; the probe does not claim zero GPU-state effect. Host-specific raw output and acquired third-party sources remain ignored. [Acquisition records](acquisition-requests.json), [source inventory](source-inventory.json) and the [publication manifest](audit-manifest.json) bind the evidence. [Independent review](../../../validation/t27-feasibility-review.md) verifies the saved identities, budget, disclosure and decision without another acquisition or probe.

## Decision and next useful question

There is no justified install/download/training plan yet. One separately bounded combined decision should resolve whether a specific isolated setup for this actual GPU and platform, plus explicit observation-use and selected-member conditions, can fit a practical acquisition/setup/training cap. It must distinguish documented compatibility from a successful build and keep dependency changes explicit. The discriminating criterion is a disposable single-scene qualification with bounded data acquisition, build, storage and training, requiring no open-ended renderer/ABI port. It need not guarantee that8GB will fit; it must allow inexpensive failure. If obtaining that plan still requires searching dependency combinations, switching scenes or expanding debugging budgets, close this researcher-training acquisition route rather than adding another preparatory audit. Reopen only on concrete new carrier/environment evidence. Repeating ready-asset lookup or silently upgrading until something runs would not answer the question.

Even a successful one-scene training run would only supply a learned input for a falsifiable applicability study: do prefix-specific gains survive learned overlap/color/density distributions and repay all failed-shortcut costs against an accurate ordinary reference? It would not establish creator demand, improved reconstruction quality, novelty, broad speedups or TOG readiness. The same-input reference, ordinary shortcuts, complete cost and negative outcomes must remain visible. T22's 1.37% median batch reduction with overlapping ranges gives no basis for a new architecture or large training campaign.

All historical gates and results stay unchanged, including T19's incomplete comparison and T20's unresolved source mapping. The research goal remains active; art is inactive, the old hourly automation remains deleted, and main is untouched.
