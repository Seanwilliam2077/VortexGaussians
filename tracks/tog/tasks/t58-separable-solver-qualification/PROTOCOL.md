# T58 — fixed same-operator direct-solver qualification

The finite question from [T57](../t57-finer-short-reference/DECISION.md) is whether an ordinary separable solve faithfully replaces the costly from-zero CG implementation for the same discrete operator. [FORMULATION](FORMULATION.md) fixes the equations, FFT convention, manufactured array and metric definitions. T56's spatial failure and T57's timeout remain immutable. A pass here does not qualify a fluid reference or establish a TOG contribution.

## Schedule and inputs

One scientific child, 180 seconds total including imports, loading/hashing old inputs, transform checks, factor setup, solves, reconstruction, validation and saving. Exactly 18 saved-state solves, ordered S32/S64/S128/T64/D96/Q64, each at snapshot indices 0,1,2 (times 0,.125,.25); then exactly one manufactured 256/512 linear system. Before them run the single fixed transform-check set at n=64,128,192,256,512. No pilot, warmup, retry, tuning, fallback, source search, install, new Green matrix, CG solve, fluid trajectory or candidate trajectory.

Freeze the parent commit, all new source/protocol/preflight files, the unchanged T55 reconstruction source, T56 source/protocol/receipt/result and every fixture's case/log/NPZ identities, T57 decision/failure records and unchanged memory observer, and the scientific executable. Read saved q, dynamic boundaries, phi and u directly from the original T56 NPZs with allow_pickle=False. Each state's complete original case provenance remains linked. No arrays are aligned, modified, retuned, substituted or copied into tracked storage. Historically failed coarse physical cases are legitimate algebraic fixtures but do not become qualified physical references.

Scientific runtime is the previously verified bundled Python 3.12.14 with NumPy 2.3.5, asserted at child entry. Import unchanged T55 solely for reconstruction and the fixed physical error reduction; do not call its Poisson, oracle, source quadrature or main. The supervisor uses a separate standard-library runtime and reuses unchanged T57 memory.py. Preflight is one OS-only probe, without numerical imports.

## Checks, all required

For each n, use the three explicit modes k=1,7,n and a fourth deterministic vector .3+cos(.37*(j+1))+sin(.13*(j+1)^2). Require relative round-trip L2 error <=1e-12 for every vector. Require forward coefficients of each pure mode to match the analytic single nonzero coefficient (n/2 or n for k=n), relative L2 <=1e-12. This prevents two mutually compensating transform mistakes from passing a round trip alone.

Independently apply the original axial ghost stencil at h=1 to each mode. Require its operator-normalized eigen residual <=1e-11, as explicitly defined before measurements in FORMULATION; report eigenvalue-relative residuals as diagnostics. T57 left this denominator undefined, and this document completes that definition rather than reclassifying any old measurement. Do not select a normalization after seeing output or weaken the complete-system residual.

For all 18 original saved-state systems require:

- Independent true weighted RHS-relative residual <=1e-10.
- Whole-box weighted phi relative difference from saved CG phi <=1e-8.
- Two separately scored errors, u and J, must each be <=1e-7 under the existing fixed-core r<=4, |z|<=4, 2*pi*r*h^2 weighted relative L2 metric. The u norm combines both velocity components; the J Frobenius norm combines all five nonzero Cartesian components, rather than separately normalizing each component. Denominators are the old saved/reconstructed fields, with no fitting/alignment.
- Reconstructing old phi with old boundary/corners must reproduce saved u bit-for-bit at all times, and saved J0 bit-for-bit initially. This is a data/reconstruction consistency check, not another physical test. Later-time old J is obtained with the unchanged reconstruction, without solving an elliptic system.

Report old CG residuals recomputed by the independent flux stencil as diagnostics. Floating-point ordering differs from its original assembled apply, so do not retroactively change T56's historical gate using this diagnostic. The direct solution must satisfy its newly frozen true-residual gate. Old-solution disagreement and true residual cannot waive each other's failure.

The one manufactured system must have known-phi weighted relative error <=1e-8 and original true weighted residual <=1e-10. Nonfinite values or nonpositive Thomas pivots stop the child; structural/reconstruction-identity errors also stop. Ordinary metric failures remain failures but the fixed schedule is completed where numerically safe, then all six result categories are required. No failed category is dropped or repaired in this invocation.

## Resources, outputs and decision

Require >=3 GiB available host physical memory at the one OS preflight and again before launch. The supervisor samples OS lifetime peak working set every .25 s with unchanged T57 GetProcessMemoryInfo code, writes a memory JSONL and stops on observed peak >2 GiB or elapsed >=180 s. A live observer error terminates the child. This is an observed limit, not a memory reservation or allocator cap; disclose any unavailable final query and unobserved exit/kill tail. Private and peak-pagefile counters are reported, not additional gates. An exclusive start file reserves the single invocation; any error closes it without retry.

Store each fixture's new phi/u/J, its metrics, source identities and complete elapsed time; also store the manufactured known phi/RHS/solution, transform diagnostics, stdout/stderr and memory log in ignored local. The result records all 18+1 solves and zero physical trajectories. Check original inputs and executable again after the child. Preparation, RHS assembly, both transforms, factorization, triangular solve, validation/reconstruction and output cost all count; no factor cache or prebuilt transform is excluded. Whole supervised child time is authoritative; per-phase timers are attribution only.

Retain the full prior T56+T57 child cost 1316.7941713000182 s, including the timeout, separately from this invocation and report their cumulative sum. Do not compare different solve sets as an equal-work speedup or present a manufactured-RHS timing as physical S256 trajectory performance. Earlier project costs retain their own receipts.

Passing supports only these same-operator fixtures. It permits preparing a separately frozen coupled-reference integration with current-q Green boundaries, all physical controls and complete costs; it does not automatically rerun T57 or start t=1. Failure preserves the specific residual/difference/resource evidence and stops this task. No new method, representation repair or submission-ready claim follows from either outcome. Art remains inactive, main unchanged and the deleted automation unchanged.
