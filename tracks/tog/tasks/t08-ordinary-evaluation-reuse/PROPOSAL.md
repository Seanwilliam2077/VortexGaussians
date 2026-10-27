# T08 proposal — ordinary reuse of an identical returned evaluation

This is a single implementation check on the already solved T07 task. Keep the same T06 target, original v0/rho0, T05 final-x initialization, complete76-constraint Objective/acceptance/force mathematics, lambda0/rho1, fresh L-BFGS history, numerical settings and all task gates. T07 is sealed. No new target, solver tuning, protected-response cache or method claim is introduced.

## Sole change

After a successful closure forward and finite backward, retain **only the latest** closure's `x.detach().clone()`, `frames.detach().clone()`, final velocity/density detached clones and a fixed model/input identity. Do not retain the autograd graph, loss, gradient, old PHR terms or previous closure history. Identity covers the pinned core/model/config, initial fields, target, active model/input objects and tensor mutation-version counters (including static model tensors). The core and initial fields remain unmodified within this worker; an identity/version mismatch disables reuse.

After `optimizer.step` returns, compare returned x with this stored x using dtype/shape checks and `torch.equal` on contiguous uint8 views (byte matching, including signed zero), and compare the identity. Only a match permits using these stored numerical fields. Otherwise perform the original real forward. In both cases freshly evaluate the unchanged acceptance and expanded-force gates at the returned x, and recompute PHR records under the current multipliers/rho. A trial is never accepted merely because its objective was low. Clear the closure cache on rollback and AL/history changes; input/source authentication failures remain failures, not valid cache entries.

The initial warm-control validation is a real forward. At termination, pay for an additional real forward of the final accepted x, apply all original gates and compare frames/velocity/density against the accepted cached arrays. Save both results and exact comparison records. Any disagreement is preserved as a reuse-validation failure, even if image tolerances pass; no retry. Success requires both exact final agreement and all original task gates; final verification cannot silently replace a failed accepted result with a different answer.

## Budget and qualification

The budget is120 **real** solve forwards including initial validation, all closure/line-search calls, acceptance misses and final verification. A conservative closure reservation leaves two slots: one possible acceptance miss and one mandatory final forward. If that reservation prevents a further closure, restore the last accepted x/state; never retain the rejected trial as final. Hits consume no forward budget but their checks/force calculations/IO remain measured. The whole fresh worker stays≤600 seconds. No new initialization or extra iteration schedule is added.

The T07 scalar mathematics and target are unchanged. Authenticate its source/core/config/input identities, fresh G0 records and compact original raw qualification arrays on CPU before GPU work; require objective/acceptance/force AST equality. Reuse the qualification, with no new G0 GPU forward/backward. State the partial raw scope if full G0 images are omitted; saved q/constraints/gradient/directions suffice to recompose the scalar FD test but not to independently redo image loss or AD.

## Required records and interpretation

Record actual closure count, acceptance hit/miss count and time, initial-forward cost, mandatory final-forward/validation cost, true-forward total, detached cache payload, solve wall and total worker wall. Closure time includes writing its detached cache; hit/miss time includes identity/x checking and original acceptance/force checks. Keep nested costs separate to avoid counting the same forward twice.

Preserve every accepted x/q/frames, final fields, qualification provenance, trial/rollback events and source hashes. The independent post-audit compares the complete accepted x/q/frames sequence with T07 and explains every miss or trajectory difference. Bitwise equality is the observed equivalence check, not presumed from source similarity. The reservation policy could affect a budget-bound run; T07 completed within budget, but that fact does not waive the check.

One fixed execution can establish actual call savings and whether this ordinary evaluation reuse preserves the accepted trajectory on this development input. It is not a new algorithm, statistical speedup, a general determinism guarantee, or evidence for protected-response caching. T07 was already successful; T08 is not an attempt to rescue a failed task. Freeze/run only after root accepts the implementation review and grants the GPU window.
