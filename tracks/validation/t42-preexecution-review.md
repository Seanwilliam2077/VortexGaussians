# T42 independent pre-execution review

**No unresolved concrete blocker found in the final reviewed task files. No browser or scientific execution was performed by this review.** Read only the eight authorized new files: PROTOCOL.md, recipe.json, preparation-history.json, prepare.mjs, stage.mjs, adapter.js, capture.mjs and supervise.py. Rechecked the revised capture/supervisor/protocol sections after reporting findings. No original demo, runtime helper, historical adapter/driver, asset or additional source was opened; the original-source allowance was not expanded. The saved-state auditor was not part of this review.

## Fixed operation and preparation

The recipe and worker agree on seed 11, the existing layered world-coordinate VPM configuration, fixed A/B picks, and two intervals of 180 steps at 1/60 second. The worker has twelve explicit 30-step calls, two discrete ignition calls and six checkpoints: initial, immediately after A, before B, immediately after B, endpoint and reset. There is no step/reset between the two B checkpoints. RequestAnimationFrame is suppressed before page load; no additional dynamics invocation was found in the new task code. The final reset uses the same seed and controls. A second location already reached by propagation is retained as an outcome, not relocated.

The two offline preparation invocations are disclosed. The failed 3-pixel selector stays failed; the 10-pixel revision retains the photo targets and does not use a dynamic observation. This is exploratory input preparation, not a successful original selector or a second dynamic attempt. This review inspected that record and selector code, but did not rerun it or independently validate decoded asset values.

## Camera, hook and output scope

The adapter supplies the stated transformed source-camera basis and scaled intrinsics, dispatches camera updates, and adds inspection/export access. It does not contain a simulation or ignition call. The final worker sets the source camera after resetting placement/parameters, avoiding reliance on whether reset recomputes a camera previously built with loadPLY's automatic scale. World/layer mode, disabled default emitter, elapsed-clock policy and declared legacy material model remain fixed.

The staging code inserts the assembled adapter at a unique marker and checks that removing the exact insertion restores its original source string. It writes an exclusive staged file without overwriting the original demo. This is a reviewed construction, not an independently executed byte-reversal test: the actual original, adapter and staged HTML identities must be included in the pre-execution freeze. Existing-core guarantees about world-mode transport and researchSnapshot contents are inherited from the bounded source inspection, not re-established here by reading old files.

Each checkpoint requests detailed state and adds frontier, camera, buffer and GL metadata; it saves capped, losslessly compressed JSON and a full PNG under exclusive names. The final code records post-render GL/context status associated with that PNG, saves the image before failing a bad render, and retains progress/partial artifacts on failure. The status is capture completion pending saved-data and visual audit, not workflow success. Full per-point schema/order/identity, finite values, frame/time, B's instantaneous state transition, particle hash/aggregate continuity, reset and visible identifiability still require that later audit. No raw-particle or physical-accuracy guarantee follows from an aggregate/hash export.

## Findings resolved before execution

1. The original supervisor could wait 240 seconds and then spend another 30 seconds on termination. It now stops ordinary waiting by 210 seconds, allows at most 20 seconds for taskkill, and bounds the final wait by the remaining 240-second process budget.
2. Source-camera setup was moved after the initial reset, removing the stale-placement dependency.
3. GL status originally preceded rendering. The new post-render checks cover each exported frame, including the last reset image. Browser error collections are checked again after cleanup rather than only before it.
4. Timeout/termination failures and a still-live parent are explicitly recorded. The protocol now describes attempted tree termination and correctly avoids treating a terminal parent as proof that all descendants exited.
5. Time scopes are explicit: worker time ends after cleanup/error checks but before final receipts; supervisor process time ends at its parent-status check, with inventory hashing and pre-receipt elapsed time separately reported. Final supervisor receipt/stdout work is excluded. These fields must not be called complete end-to-end benchmark timings.

The worker's elapsed deadline is also checked after cleanup. The external supervisor consumes the attempt before launch and uses a fresh exclusive output directory; launch failure does not permit retry. Same-origin page request routing and error records are present, without claiming OS-wide network isolation. Runtime compatibility, successful cleanup and graphics behavior remain untested until the sole attempt. Any reported live process requires cleanup rather than another run or a successful-process claim.

## Decision boundary

The protocol tests existing sequential ignition on a real input, not a new method. The zero-time B check rejects unintended reinitialization while allowing all subsequent ordinary coupling; it adds no protected region. Success closes the authored brief as served by existing operations. A contract/resource failure or visually ambiguous/already-ignited B stays failed or unqualified and authorizes no tuning, extra location, larger run or renderer change. This pre-execution review supplies neither a scientific result nor a TOG-contribution judgment.
