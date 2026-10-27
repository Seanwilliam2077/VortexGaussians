# Next finite task: T13 ordinary feasibility recovery

Decision after T12, 27 October 2026. This is a preparation decision, not a completed experiment or a frozen executable. Continuing technical exploration is authorized. No new user input is needed to prepare and run this bounded probe after source review.

T12's 152 non-seed trial records failed only the original pixel-interval gate. This leaves two explanations unresolved: the ordinary response objective/penalty coupling may impede restoration, or this configuration may also resist ordinary feasibility recovery from a separate perturbation. A specialized method is not the next justified action.

## Fixed question and input

Starting from exactly the original T12 G0 perturbation `seed + .01 * Rademacher(2026102712)`, can an ordinary feasibility-only solve find another observation-compatible initial velocity under the **unchanged** T12 data, parameterization, camera, velocity prior and per-pixel interval gate? That starting point has 1,965 interval violations. Do not select another perturbation, loosen a gate, use the seed as fallback, or search along the seed-to-trial segment.

The objective is the same PHR sum with the response term removed. Keep lambda=0, mu=1, three outer rounds of at most12 L-BFGS returns and the same AL update rule. No new regularizer, nullspace basis or target is added. The new runner should be a narrow documented fork of T12; the frozen T12 code and results remain untouched.

## Budget and verification

- Search evaluations need only the complete 20-step observation prefix. Extract that prefix without changing its operations; a full evaluator then adds the original two future branches for final verification only.
- Qualify the newly extracted PHR-only observation path with nine fixed 20-step evaluations and one reverse call: original G0 point, two Euclidean-unit directions, h=1e-5/1e-6, lambda=2/mu=1, original 1e-4 relative derivative gate, numerical validity and 6/7 GiB allocator limits. No automatic step-size sweep or fallback.
- At most80 actual search/final evaluations, reserving one for a full 60-step verification; 300 seconds of search and a separate bounded whole-worker supervisor fixed in the executable protocol before running. Count 20-step and 60-step work separately, including all qualification, rejected trials, acceptance misses and final checks. This is not an equal-cost speed comparison with T12.
- Stop at the first actually evaluated observation-feasible point whose **projected fine-grid initial velocity** differs from the reference by maximum absolute value greater than1e-10. This threshold only excludes numerical identity; report relative L2 distance as well and never call an arbitrarily small difference substantial ambiguity. A line-search candidate may qualify, with its origin disclosed.
- Perform one paid complete-history plus two-future verification of that candidate, using the original wind, horizon, ROI and denominator. Do not select candidates by their response. If final verification fails, preserve the failure without searching for a replacement in this task.
- If no non-seed feasible point is found, retain the least-violating evaluated point as a failed diagnostic, not a witness. No seed fallback and no fabricated response range.

## Decision after the probe

A qualified alternate state establishes only ordinary feasibility from this fixed perturbation; inspect its actual state distance and unchanged wind response. It does not by itself explain T12 causally or establish a useful ambiguity. If feasibility again fails, stop further method development on this input contract. Neither outcome licenses a dedicated nullspace implementation, an uncertainty guarantee, or a claim that the flow is uniquely identified. Any subsequent method needs a separate concrete capability and task argument.
