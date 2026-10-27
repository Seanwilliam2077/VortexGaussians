# T12 pre-run source review

27 October 2026. Root and an independent reviewer read the new T12 runner, config, protocol and common solver before freezing/execution. No blocking mismatch was found. The interrupted parent turn had not frozen or run T12; the continuation checked processes and the idle GPU before starting the one `runs/run-01` execution.

- Runner SHA256: `258da8e8c9f16be33c84edddc5601427d7a33aa388e10ca9b5cceeae7f1d1ca4`.
- Config SHA256: `8fb935bfee4590358d12fc0fb7645bacdb337164ed7c4e67a26e72288936c3d8`.
- Protocol SHA256: `a5d7f180402dd2aecefbf63ef2b293f7b555573c1aa72049f0da376d585c3380`.

The reviewed path uses the public coarse-MAC seed and known nonsymmetric density, correctly samples the vector potential on z edges, shares the 20-step prefix and computes both 20-step suffixes. Old-velocity transport means the first future density/image cannot yet respond to the wind acceleration. The response uses only the final image ROI with the fixed reference denominator.

The observed code intervals and the extra floating tolerance are distinct from byte-identical requantization. PHR retains all 163,842 inequalities and uses their sum. Both searches independently start from the same reference, reset curvature at AL changes, count every real evaluation and pay for final verification. An evaluated feasible line-search point may be the best witness; this is disclosed and never relabeled as an optimizer-returned point.

G0 checks both the response derivative and the full AL scalar, with two Euclidean-unit directions, nine full evaluations and two reverse calls. Its trajectory validity and memory gates apply before optimization. Qualification failure stops this frozen configuration without a step-size sweep or relaxed gate.

Interpretation boundary: projection preserves DC components of the parameterized velocity. Adding a fixed `(0, .12, 0)` base does **not** fix every candidate's mean flow. The declared initial-velocity maximum/RMS prior applies after projection and base addition. These are source checks, not experimental results or evidence of a new method.
