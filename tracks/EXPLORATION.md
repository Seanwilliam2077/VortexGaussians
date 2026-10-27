# Exploration policy

This is the repository's working research policy, not a venue acceptance checklist. User steering takes precedence. Updated 27 October 2026.

## Decide before a run

For each finite task, record a question, the evidence that would change the next action, a preparation/compute budget, and a stopping condition. Distinguish exploratory development from held-out confirmation. Parameters may evolve between disclosed experiments, but saved failures and their original criteria are never relabeled.

The technical track first needs a recognizable artistic brief and a qualified task. The R22 two-pixel rule belongs to its frozen historical experiment; making a new example pass that number is not itself the research objective. Author-defined targets are allowed, with a recorded source and artifact identity. A target constructed by running known controls is labeled synthetic and must not leak its controls into optimization input.

At the next decision window, use one coherent brief and at most two fixed edits to determine feasibility and ordinary-method difficulty. Give the ordinary method the same information, control freedoms, starting-state options, quality requirements, and compute accounting as a candidate. Do not implement a dedicated response cache until there is an actual bottleneck and a plausible opportunity to recover setup and maintenance costs. If that opportunity is absent, close the mechanism and select a different hypothesis.

The art track develops a complete experience and records its creative choices. Its provisional theme is “Combustible Digital Memory.” Authored notes, agent-generated drafts, researcher observations, and actual participant responses must remain distinguishable. A local reset starts again; it is not reverse physical time or evidence that damage has been faithfully undone. Synthetic scenes are labeled synthetic.

## Record after a run

Update [STATUS.md](STATUS.md) with outputs, source identity, what actually ran, limitations, and the next finite action. Keep research costs separate from setup, qualification, and repeated diagnostic work. Report failures and trial runs. Keep large generated arrays in ignored run directories, with a compact inventory and hashes when they support a decision.

Use targeted checks for code changes. Re-run or broaden them only when a change or unresolved concern justifies it. Tests support implementation behavior, not the paper's novelty. Inspect the art interface visually and test its actual public-API behavior, including save/export and reset semantics.

## Continue without drifting

Read the latest status before choosing another task. Complete or safely conclude an existing run before starting a second run that writes the same outputs. Work on the TOG and art directories may proceed in parallel when file ownership is clear. Share a result across tracks only with its original scope attached.

If compute is unavailable, make progress on a portable specification, implementation, prior-art check, or analysis that answers an outstanding question; do not manufacture extra tests to consume quota. Do not purchase capacity or reset account limits as part of routine exploration. Stop when the author pauses, resources prevent progress, or the task requires information that cannot be inferred; record the concrete outstanding need.

The original archived research files remain immutable. New repo-native reproductions and adapters identify their ancestry and any changed semantics. Publication claims use the current evidence rather than the historical manuscript's wording. Art Papers and TOG retain separate contribution arguments even when they share this codebase.
