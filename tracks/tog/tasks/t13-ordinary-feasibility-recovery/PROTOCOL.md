# T13: ordinary feasibility recovery

Prepared 27 October 2026; no result is implied by this protocol. This is the
single Phase-I probe specified by T12's committed `NEXT_PHASE_I.md`. T12 and all
earlier tasks remain unchanged. Default CLI behavior is a standard-library-only
plan; root must review, freeze, and explicitly execute this new task.

## Fixed input and model

Preparation copies selected arrays from the SHA-authenticated T12 `reference.npz`
and original G0 analytic theta into a portable compressed `inputs.npz`.
Reuse its known rho0, seed theta, projected seed velocity, observed uint8 codes,
lower/upper rounding intervals, response denominator and wind. Do not generate a
new reference. Verify every array against the original saved raw manifest; verify
the loaded starting theta equals seed + .01 Rademacher(2026102712). Reuse and
authenticate both original L2-unit directions (generator 2026102713). The explicit
CPU preparation saves original NPZ and selected-array hashes, verifies pack
readback byte for byte, and records its cost separately from simulation. The
runtime reads only this pack and manifest; it does not require old ignored runs,
does not use old gradients, and does not import or execute T12's runner.

The immutable core, n=32, float64, dt=.025, MAC interpolation/projection, camera,
20-step observation and both 20-step future branches are unchanged. The new
`observe` method contains the original observation operations; `complete` reruns
that prefix from the candidate initial state and appends the original futures.
Initial velocity is P(interpMAC(.2 tanh(theta))) + (0,.12,0). The prior is actual
initial max component <= .35 and RMS over all velocity components <= .18.
Interval tolerance remains 1e-10 alpha; byte-identical quantization is separate.
All computed states retain the original finite/density/alpha/divergence gates.

## New qualification

Before searching, run exactly nine observation evaluations and one reverse call:
the loaded G0 point, two original Euclidean-unit directions, central differences
at h=1e-5 and 1e-6. Test the PHR-only sum with lambda=2 and mu=1; derivative relative
error denominator max(abs(g dot direction),1e-8), gate 1e-4. Numerical validity
is required for all nine observations, but they need not satisfy the observation
interval/prior. Torch allocator peak limits remain 6 GiB allocated / 7 GiB
reserved; these are not full process peaks. Failure/OOM stops without adjustment.

## One ordinary Phase-I search

Start only at the loaded perturbation, lambda=0, mu=1. Minimize the original PHR
**sum** over 163842 inequalities (all lower/upper pixel constraints and two velocity
priors), with no response term or new regularizer. Keep original LBFGS settings,
3 outer rounds x at most 12 returned steps, multiplier updates, penalty growth
1 -> at most 100 when max positive violation fails to halve, and fresh history
per outer round. No seed fallback or seed-to-trial interpolation.

At most 80 search/final actual evaluations, including initial evaluation,
closures, acceptance cache misses, and one reserved complete final evaluation.
Search has a 300-second soft cap; whole child process has a 600-second hard cap.
An observation evaluation costs 20 steps; a complete final evaluation costs 60.
G0's 9 observations are separate. Max possible work is 1820 physical steps if a
candidate is found after 79 search observations. No final future is computed if
none is found. Runtime records starts, completions, steps, reverse calls, actual
origins, cache hits/misses and wall time; this is not equal-cost comparison with
T12's 60-step evaluations. Reserve two slots before gradient closures (possible
acceptance miss plus final), one before a non-gradient search evaluation.

Every complete actual evaluation is recorded and checked **before backward**.
The first observation-feasible point with max|v0-vseed| > 1e-10 is saved immediately
and interrupts the search, including an initial point or line-search trial. The
threshold only excludes numerical identity; also report relative L2 distance.
An evaluated line-search point is not described as optimizer-accepted. Its saved
theta/output cannot be replaced by a later candidate or a rollback.

One paid complete 60-step rerun verifies that candidate against all original
gates and the same nonidentity test; it reports the unchanged wind response at
future20, ROI [28,26,36,56], divided by reference obs20 whole-image alpha sum.
Report original prefix-vs-final repeat differences. No response magnitude gate,
selection by response, replacement after failed verification, or automatic retry.

If no candidate is found, save the numerically valid evaluated point with least
lexicographic (max positive original constraint, squared positive-constraint sum),
earliest on ties. It is only a failure diagnostic, not a witness; compute no
future and supply no fabricated d. If all trials are numerically invalid, report
that there is no valid least-violating diagnostic. Budget/invalid-gradient exits
restore the last returned state without accepting a trial or discarding a saved
first candidate. A zero optimizer gradient never substitutes for the gates.

## Evidence and interpretation

Save qualification raw arrays, first candidate or least-violating observation,
one final complete output when applicable, call/returned-state scalar ledger,
source/input hashes before and after, runtime tensor hashes and timings. Raw runs
are ignored by Git. Input authentication reads only existing evidence; no old
source or result is changed. Success demonstrates finite ordinary recovery from
this perturbation, not useful ambiguity or why T12 failed. Failure is not proof
of unique state or of a need for a specialized method. Stop at this fixed result.
