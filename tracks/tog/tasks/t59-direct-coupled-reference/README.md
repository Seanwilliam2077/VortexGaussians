# T59 — short coupled reference and direct-solver port qualify

**Completed 30 October 2026:** `qualified_short_reference_only`. Six new trajectories finish [0,.25], all eleven frozen categories pass, and 18 completed field checkpoints are retained. One supervised child takes 242.856030800 s, within the 600 s cap.

The two spatial vorticity-disagreement maxima are .0043475597 and .0011194295, below .01, with nonzero-time error reductions 3.9193 and 3.8837. Time/domain/angular controls pass. New S64/S128 vs old CG-run fields differ by at most 3.4959035e-12 in physical vorticity and 2.2131697e-10 in velocity. No candidate method was tested.

- [Protocol](PROTOCOL.md), [formulation](FORMULATION.md), [40 frozen inputs](input-manifest.json).
- [Results and full costs](RESULTS.md), [machine result](result.json), [execution receipt](execution.json).
- [Source and saved-array review](../../../validation/t59-direct-coupled-review.md), with pre-run participation disclosed and no scientific-method rerun.
- [Next decision](DECISION.md): prepare the original full t=1 physical task and the ordinary complete-tangent Gaussian comparison under a separate freeze.
- [Publication identity chain](audit-manifest.json). The 217,263,132 bytes of raw arrays remain ignored locally.

The reference is qualified empirically only for this short window, tested controls and measurement region. This is ordinary numerical infrastructure, not a new TOG contribution, unrestricted whole-space guarantee or full t=1 result. T56 remains failed, T57 remains timed out; full goal active, art inactive, main unchanged and automation deleted.
