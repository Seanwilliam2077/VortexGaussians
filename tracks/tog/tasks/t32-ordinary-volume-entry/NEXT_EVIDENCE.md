# Next finite task — answer the output-accuracy question directly

Prepared after the failed T32 invocation; this is a new, explicitly result-informed development task. It must preserve T32's failed status, original reference half-width gate, cell budget and raw evidence. It is not held-out confirmation and does not reopen T28/T29/T30.

## Evidence motivating it

T32 stopped at frame 90 / front / (132, 73): reference red half-width 0.000331721 exceeded its auxiliary 0.0001 requirement, although the ordinary output's greatest distance to either saved endpoint was about 0.000334382, below the actual 0.001 output tolerance. Thus the failure does not demonstrate inaccurate GL output. A separate 0.0001 midpoint target may demand work that cannot change the requested accuracy decision.

For a valid independent interval L <= C <= U, an already computed ordinary answer A satisfies |A-C| <= epsilon if max(|A-L|, |A-U|) <= epsilon. This is a sufficient endpoint test, independent of the interval's midpoint precision. Conversely, an interval disjoint from [A-epsilon, A+epsilon] can demonstrate failure; overlap without containment is inconclusive. These are elementary interval facts, not a novel rendering contribution. Mathematical containment and the existing binary64 implementation's qualification are separate obligations.

## Analysis already completed

[STOPPING_CONTRACT](STOPPING_CONTRACT.md) derives these rules, independence conditions and limitations in this task. Two implementation reviewers independently recommended this elementary rule over a more complex envelope. Do not repeat that analysis as another claimed research result.

## Bounded next action

Prepare and independently review **one separately named output-accuracy qualification**, then freeze before its one permitted invocation. Use only the immutable T31 model/carrier and T32 sources/outputs. No new source search, capture, simulation, packages, browser/GPU execution, field/opacity modification, new seed/frame/view or sample selection is permitted. Keep the exact two fields, three cameras and geometry rule, including all dark samples. No new density/color bounding implementation is part of the next task.

The protocol must state changed versus unchanged requirements:

1. Replace the separate 0.0001 reference midpoint requirement with the sufficient endpoint-distance stopping rule at the unchanged 0.001 RGB tolerance and disclosed numerical allowance. Preserve all alpha, geometry, pruning, range, ledger and coverage gates. Save actual interval widths and stopping reasons. Count T32 among cumulative ordinary-entry qualification attempts; it stays failed.
2. Fix the ordinary answer before reference evaluation. It may enter only the stopping decision, never reference construction, retention or split priority. Preserve the reference algorithm and count its full work, including failed paths. Binary64 qualification remains distinct from formal numerical certification.
3. Retain at most 180 seconds of computation / 210 seconds outer wait with the existing 10-second termination allowance, 8,192 created cells per ray, 200,000 overall, at most 336 rays and 32 MiB raw output. One exclusive attempt reservation, no retry or post-failure repair-and-run. Save complete completed records and available failure diagnostics. No automatic cost study follows a failure.
4. Stop on the first failed gate, demonstrated accuracy failure, unresolved cell/time cap or coverage failure. Do not replace cases, increase a cap, tighten old gates, invent a new envelope or silently add another invocation. A pass qualifies only this fixed authored subset, not full images, a trained scene, a real creator brief, a rendering bottleneck or novelty.

The next task is justified by a specific mismatch between an auxiliary verification target and the requested output tolerance, not by a desire to obtain a pass. If direct stopping cannot meet the model/numerical obligations, record that specific gap. A future successfully qualified ordinary entry would permit considering a useful complete-frame cost question, not claim a contribution. If ordinary rendering already suffices, record that and reconsider the research question instead of tuning workloads to force a failure.
