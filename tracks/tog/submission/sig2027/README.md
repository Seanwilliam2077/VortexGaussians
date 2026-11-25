# SIGGRAPH 2027 Technical Papers working draft

[Read the three-page anonymous paper](paper.pdf) · [LaTeX source](paper.tex) · [Offline reviewer supplement](supplement.zip) · [Representative image draft](representative.png)

**Research decision, 25 November 2026. Hold the submission.** The experiment establishes a measurable gain in conservative material-site classification on two edits of one scene. Complete-domain and brush-region queries still invoke ordinary native fallback in every measured window. The project’s goal is the journal outcome in ACM Transactions on Graphics. The current evidence does not support presenting this as an accelerated editor.

## Evidence in the paper

| Experiment | Question | Result |
| --- | --- | --- |
| [T84](../../tasks/t84-ignition-edit-footprint/README.md) and [T85](../../tasks/t85-edit-prefix-certificate/README.md) | Does a second ignition do more than add a stroke? How long can the gas trajectory be shared? | 1,266 off-stroke gains and 12 losses under global admission. The same gas is guaranteed for 24 complete suffix steps on that arm. |
| [T86](../../tasks/t86-ignition-margin/README.md) | Can future heat certify individual unlit sites after the gas changes? | 373,913 / 535,437 repeated site queries certified, versus 328,626 for uniform hot-carrier weights, with zero observed false certificates. Full-domain fallback required in 18/18 windows. |
| [T87](../../tasks/t87-stroke-halo/README.md) | Does anything ignite just outside the second brush? | 10 yes and 8 no. Regional certificates gave 0/18 complete answers. Regional weighted computation with fallback cost 1.40× direct native first-event-or-end replay in paired median, with checkpoint loaded. |
| [T88](../../tasks/t88-positive-ignition-witness/README.md) | Can residual heat or guaranteed material graph heating prove a regional yes? | Neither proved any of the 10 positives. Graph donor service was guaranteed in all 12 multistep queries. Prior regional outcomes were known when the rules were designed. |
| [T89](../../tasks/t89-terminal-scan/README.md) | How soon is the requested answer available within native replay? | Regional native median was 11.85 ms through the last needed ignition scan versus 18.60 ms through the same step's end. All 720 frame event records agreed with the earlier run. |

**Internal reviewer recommendation: Reject, 2/6 on the project's scale.** The technical reader checked the source assumptions and participated in verification material preparation. This is an internal AI review. In its assessment, the 45,287 additional classifications, including 294 at or above half the ignition threshold, demonstrate selective prediction. They have yet to establish a useful latency improvement or transfer to another scene. T89 measures the time at which the label exists inside a running solver. Dispatch, extracting a region result and restoration have not been independently timed in an early-return implementation.

**Priority for the next technical decision.** Stop optimizing the current all-site heat bounds for a whole-brush yes/no answer on these takes. The unresolved recipients determine that answer. A plausible next mechanism would have to prove an ignition at one of those recipients using the hot carriers the native solver actually samples, or exclude every such recipient cheaply on a negative query. First compare against an actual callable first-event native query timed from the same loaded checkpoint through result delivery. Before a submission claim, fix an independently motivated new edit and another reconstruction, and test if the method still returns the requested answer sooner. The existing woodpile and reversed edit remain development evidence. A new run budget has not been spent on that proposal.

## Rebuild or verify

The public research branch includes full dynamic cut inputs, timings, per-frame events and numerical scorers. The external Firewoods PLY is required to regenerate bounds from native geometry. For a compact independent verification, unzip [supplement.zip](supplement.zip) in an empty directory and run `python verify.py`. The package recomputes all 72 full-domain masks from exported thermal enclosures, and runs all four offline score checks without network or third-party packages. Spatial construction is reproducible separately from the Git code with the pinned asset. The supplement is 9,395,255 bytes; SHA256 `fe97b057cc0fa06c706fbc6f216364f043d0a60aac8d82c004541119cee9ef74`. [Packager](pack_supplement.py)

The working PDF was compiled locally using acmart 2.21 (1 November 2026), ACM-Reference-Format, author-year citations, BibTeX and Tectonic 0.17.0. With that class available, `tectonic paper.tex` or `latexmk -pdf paper.tex` rebuilds it from this directory. [Figure and source](make_figure.py) use the recorded data. The anonymous reading copy suppresses publisher metadata. Defining the LaTeX macro `RealSubmissionID` to the actual assigned ID switches the source to the venue review settings and inserts the ID. No author or submission ID has been invented.

## If the research becomes ready

SIGGRAPH 2027 uses one Technical Papers submission and considers all submissions for the journal outcome. A version of at most nine pages excluding references is also eligible for a conference proceedings outcome. These outcomes carry different publication venues. Before uploading, the human authors need to finalize authorship, verify scientific claims and AI disclosures, review the existing public prepublication and historical manuscript for the submission form, and check the anonymity and permissions of the deliverables, including a representative image. The working files have been published to the research branch. No entry has been created in the submission system. [SIGGRAPH 2027 Technical Papers instructions](https://s2027.siggraph.org/program/technical-papers/)

| Milestone | UTC | Beijing / Shanghai |
| --- | --- | --- |
| Register title, abstract, topics and complete author list | 21 Jan 2027, 22:00 | 22 Jan, 06:00 |
| Deadline for final materials or their MD5 commitments | 28 Jan 2027, 22:00 | 29 Jan, 06:00 |
| Upload exact matching files where MD5 was used; each author completes conflicts, keywords and review commitment | 29 Jan 2027, 22:00 | 30 Jan, 06:00 |

Participation in an internal review and completion of a formatting pass do not constitute external peer review. The art track remains paused.
