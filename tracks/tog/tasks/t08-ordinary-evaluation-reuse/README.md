# T08 — ordinary evaluation reuse

The sole run completed on 2026-10-27. All25 edit-frame and50 protection-frame gates passed. The returned-state cache hit at all32 L-BFGS returned steps; there were no acceptance misses. The additional real final rollout reproduced saved frames, velocity, density and constraints byte-for-byte. Frozen source/input hashes were unchanged.

| Actual work/cost | T08 |
|---|---:|
| True solve forwards |70 =68 closures +1 initial +1 final verification|
| Backward calls |68|
| Returned steps / cache hits / misses |32 /32 /0|
| Solve wall, including evidence IO |59.8928993 s|
| Closure subtotal |55.9859960 s|
| Cache clone time, already inside closures |0.0164432 s|
| Acceptance subtotal, including initial forward and force checks |0.9577334 s|
| Final real verification, including gates |0.4191882 s|
| Maximum detached cache payload |1,916,928 bytes|
| Whole worker / supervisor |75.9206307 /76.8843871 s|

Maximum final edit relative/absolute RMS was .04994839075/.00929976552; maximum protection relative/absolute RMS was .01936767475/.00418664830. These satisfy the unchanged .05/.01 and .02/.005 gates. Control and finite-state gates also passed. No target or numerical parameter was revised.

T07 used101 solve forwards with68 backward calls. T08 removes32 repeated acceptance forwards and adds one final verification:31 fewer net forwards. This is ordinary reuse of an already computed evaluation. Whole-worker times are not comparable as a speedup test because T07 ran a new G0 and T08 authenticated the same existing G0. One sequential pair is not statistical performance evidence. The completed [independent post-audit](../../../validation/t08-post-audit.md) finds only the initial3 of99 accepted x/q/frames arrays byte-identical across T07/T08; the other96 differ by at most2.889e-11 in x,1.444e-11 in q and1.121e-11 in frames. The cause was not isolated. Within-run final equality does not establish cross-run bitwise equivalence. No protection-response cache, new optimizer or new research method is demonstrated.

See [protocol](PROTOCOL.md), [freeze](freeze.json), [summary](result-summary.json), [publication manifest](publication-manifest.json) and [final arrays](framewise_joint-final.npz). [The raw manifest](raw-run-manifest.json) identifies complete accepted trajectories and the independently recomputed final verification retained under local, Git-ignored `runs/run-01`. Those full local arrays are not supplied by a clone. Published final arrays contain x/q, all25 images, constraints, accepted q history, multipliers and final velocity/density; they support downstream CPU quality checks. The compact G0 proof contains25 qualification arrays and omits nine image arrays, as documented in [its manifest](g0-proof.json).

`python -I -B runner.py` prints the plan only. The completed run is not automatically repeated. No T09 or additional GPU experiment is part of this task. Independent validation is recorded separately under `tracks/validation/`; the execution-time pre-review is immutable because it is pinned by the freeze.
