# T32 independent pre-execution static review

29 October 2026. **No unresolved blocking finding in the named static scope.** This permits the frozen single qualification attempt; it is not an execution result, accuracy certificate or promise that the reference fits its budget.

The reviewer inspected only the six T32 files below and T31 MODEL.md. Their final versions total **68,328 bytes / 1,088 lines / seven files**; earlier drafts and final changed sections were also read, so this total describes final unique file contents, not cumulative I/O. An initial metadata request used a nonexistent T31 directory and read no content there; the correct path was taken from run.py. No carrier data, prior demo, old integrator body, external source, imported module, numerical evaluation or test was read/run. Only this review file was written.

## Findings resolved before execution

1. The first run.py draft checked final source identities only after success. Its final version verifies sources in `finally`, records `final_source_check`, preserves the original failure, and changes success to failure if the final check fails.
2. The initial protocol promised every special-function call despite uncounted elementary camera/alpha operations. It now accurately names the implemented work-counter categories and distinguishes these from exhaustive math-call/FLOP profiling. Initial/final source checks, imports and serialization have explicit timing fields.

The final harness also checks ordered leaf-domain coverage, adjacency, summed absorption against retained alpha, each leaf's finite/color range, and reconstruction of reference bounds including omission uncertainty. Final reference failure diagnostics preserve available current bounds and leaves as `partial_unqualified`; packaging does not evaluate the integrand or alter a failed result.

Before freeze and before any ray evaluation, the final protocol and run.py changed reference half-width from the preparatory `.00001` to `.0001`. The reviewer checked this declared adjustment: the output gate remains worst distance to **both** reference endpoints `<=.001+1e-10`, so it supplies no additional output-error allowance; widening a fixed reference interval cannot make that endpoint test easier. This avoids requiring a reference 100 times finer than the delivery tolerance. No pilot or candidate values informed the choice. The other five reviewed files remain unchanged; static readiness is retained for this final configuration.

## Mathematical and implementation checks

- Both ray constructions match T31's top-down pixel centers, yaw-in-pi camera convention, unit direction and projection-plane clips converted into ray distance. Ordinary projection uses cross-product distance; the reference independently uses trigonometric basis vectors and residual-vector distance. Both implement full-line mass `q=k*exp(-perpendicular^2/(2*h^2))` for the same authored field. No billboard output is treated as truth.
- A node's center sphere supplies a lower bound on every perpendicular distance; largest h and summed nonnegative k give the stated full-line omission bound. Traversal prunes disjoint nodes and checks the resulting partition. HDR pruning uses original-field channel maxima, including retained downstream emission, so it does not omit the extinction effect on retained colors. Black background and nonnegative colors are required and checked.
- The reference receives all original projections, independently charges its tiny omissions, and does not import ordinary/BVH/GL code. Gaussian density endpoint/peak extrema bound nonnegative source and extinction; their ratio bounds the mixture color. Exact-real analytic cell absorption weights then bound cell radiance. Log scaling avoids declaring a density underflow region physically empty. Empty/equal-color branches retain omission accounting.
- The ordinary wrapper explicitly prohibits the inherited Simpson fallback. GL-order agreement remains an empirical stopping criterion; independent endpoint-distance and alpha gates decide qualification. The imported T22 kernel body was outside this review's allowed files, so its prior implementation audit remains inherited evidence rather than a newly repeated review.
- Selection uses fixed grid/source indices and geometry only. All six groups must retain nontrivial coverage, with at least one mixed-color ray; no replacement pixels or threshold changes follow a failure. Per-ray/global cell caps and deadlines fail rather than relaxing accuracy. The exclusive attempt reservation, worker start and result creation prevent overwrite/retry; the supervisor retains exit/timeout evidence if worker finalization is unavailable. Partial records remain failures, not full-subset results.

## Limits of approval

The real-arithmetic envelopes are sound under the stated model assumptions; binary64 CDFs, exponentials, geometry and interval arithmetic are not directed-rounding proofs. Explicit allowances and independent agreement do not establish universal certification. A reference-cap, deadline, geometry, coverage or publication failure is a meaningful unqualified outcome with no automatic fallback or second invocation. Passing this subset would establish neither full-frame cost nor production demand, novelty, a new scene, or TOG readiness. T28/T29/T30 stay closed.

## Final reviewed identities

Paths are repository-relative. Hashes are SHA256.

| File | Bytes | Lines | SHA256 |
|---|---:|---:|---|
| `tracks/tog/tasks/t32-ordinary-volume-entry/PROTOCOL.md` | 9684 | 47 | `40fbcca08d40f3e2732d61afac8ecb87760a1952d3e99f5fc7a71b04f754119c` |
| `tracks/tog/tasks/t32-ordinary-volume-entry/adapter.py` | 11851 | 271 | `e6da5219af1b8b1b7abf6f6b9555783fb846ebf740c0d1ed33f8dee4a8a9405c` |
| `tracks/tog/tasks/t32-ordinary-volume-entry/ordinary.py` | 3786 | 75 | `7ca2fb5f67cfaa3ea2c33c7818956d31073ab36b57e4195ed70ed2efd09e2966` |
| `tracks/tog/tasks/t32-ordinary-volume-entry/reference.py` | 21520 | 422 | `fb46af610a0b5936a892d3cc07f2784690a14509b043910ff7ef21cf3a11369b` |
| `tracks/tog/tasks/t32-ordinary-volume-entry/run.py` | 14943 | 207 | `0656cd7db7d9c753bdfce696a7aa6bbb3820a1484f43d295ca01a1dc6f3055e6` |
| `tracks/tog/tasks/t32-ordinary-volume-entry/supervise.py` | 2892 | 49 | `66a1637c28cb77dc2ba77016752a743ce881149a1cd36c882322bceda67baf59` |
| `tracks/tog/tasks/t31-local-carrier/MODEL.md` | 3652 | 17 | `2fb5315f175f058509080fb4ba09b0e77ecac75206b7325662766adf88f66814` |
