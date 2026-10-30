# T67 — fixed future ordinary two-Gaussian capacity measurement

This is the prospective numerical contract accompanying [the analytic derivation](DERIVATION.md), under [T66's decision](../t66-saved-product-diagnostic/DECISION.md). **No numerical work is performed in T67.** A later T68 implementation must be statically reviewed and frozen before its single permitted scientific invocation. This is an ordinary endpoint comparator, not a new dynamics method. The search is finite and explicitly restricted; a miss cannot establish Gaussian-family impossibility.

## 1. Common problem, inputs and hard resource limits

Keep the existing t=1 S256/S128 reconstructed q fields on D8, the 2πr³ physical-vorticity inner product, original full-space Gaussian moments and original gates: field error <=.10, absolute axial-centroid error <=.10, covariance Frobenius error / **1.0882203729522952** <=.10. Reference qualification uses the same metadata and tolerances as T63/T66. No radial-centroid or conservation gate is added. Two strictly positive components have nonnegative weights, including zero-weight boundaries; Γ is a fitted positive scale, not forced to the reference circulation.

Only two numerical input files are decoded: the existing T60 S256/S128 endpoint snapshots, with q,qr,qz,r,rc,z from each, exactly **twelve arrays**. Do not read T65's decomposition or T66's recovered factors. Freeze the old contracts/results/qualification receipts, endpoint metadata and raw identities, current worker/supervisor/protocol/preflight, executable and memory observer. Hash inputs before and after; saved arrays use allow_pickle=False, exact expected float64 shapes, finite coordinates and original annular-center reconstruction. Check all original reference corners and polynomial statistics before selection. T61 qualification and T60's failed receipt retain their historical meanings.

One later child has **120 seconds**, including imports, input qualification, every basis/geometry/root/weight operation, direct integrals, artifacts and input checks. Observed peak working set is limited to **512 MiB**, with .25-second OS samples and >=1 GiB available physical memory at OS-only preflight and launch. Use the existing bundled Python 3.12.14/NumPy 2.3.5 and one OMP/OpenBLAS/MKL/NumExpr thread. No installation, pilot, retry, alternative precision rescue, new trajectory or automatic search extension. An exclusive invocation marker prevents repetition. Hard time/resource exhaustion retains partial records and the full cost, with **no qualified witness** from an unfinished invocation. Finding an early promising candidate does not skip the prescribed remaining search/confirmation.

Add the later complete child cost to the tracked T56–T66 reference/endpoint series **1980.2512354997452 seconds**. Earlier scientific phases and T53/T61 diagnostic/qualification costs stay separate. T67 adds zero scientific time.

## 2. One consistent primary inner product and direct qualification

Construct exactly six positive Gauss–Legendre rules of orders **3,2,8,6,16,12**, **47 unique one-dimensional nodes**. Rules are constructed once, with finite, ordered nodes inside (-1,1), positive weights, symmetry and weight sum 2 checked to 1e-13 absolute. Any rule-generation eigensolver work must be logged; it is included in the child rather than treated as free setup. No new rule order or adaptive integration is allowed.

The 3x2 polynomial route qualifies the two references, **983040 node-cell reconstructions**, against original saved circulation, centroid, covariance, q-squared, impulse and physical-vorticity norms using rtol=3e-11, atol=3e-14. Original corner positivity uses **655360 corner-cell evaluations**. Compute C independently and positively; do not infer it from a fitted residual.

Use **8x6** as the primary discrete Gaussian inner product. For each uncached S256 component, store its radial values at 8×256 nodes and axial values at 6×512 nodes, and the centered one-dimensional contractions needed by the three-term original PL expression for b in DERIVATION §4. Evaluate r-r_c and z-z_c centered in the integrands; do not subtract two large primitive values to obtain a small cell-centered moment. The primary b, diagonal M and cross M all use this same tensor rule and normalization. Compute cross M as the product of one-dimensional pair dot products; never invert the 2x2 Gram matrix. All b_l, M_ll and M(η) must be finite and positive. Check pair Cauchy agreement M12² <= (1+1e-12)M11M22 as an empirical arithmetic check, without changing any entry. Identical components remain valid.

The primary optimization target is J=B²/M for this discrete inner product. Evaluate B and M with nonnegative barycentric weights when scoring, avoiding cancellation in their expanded polynomials. The stationary equation uses the expanded coefficients only to locate candidates. Report C-J without clipping; a nonfinite or negative projected numerator makes that numerical geometry unresolved, never an artificially perfect fit. These primary scores select candidates; they do not alone certify physical error or an unobserved optimum.

Before searching, evaluate the **unchanged selected T63 single-Gaussian tuple**, including its saved amplitude, on both references by direct **8x6 and 16x12** sums of nonnegative squared differences. Its mixture representation is η=0 with Γ=A s_r² sqrt(2π)s_z. Do not project/refit this control. Compare its direct field scores and analytic moments to the frozen T63 selected-candidate records: field discrepancy <=1e-9; moments rtol=3e-11, atol=3e-14. Two primary contraction checks at the fixed amplitude must agree with corresponding direct 8x6 scores within 1e-9. Require the control's primary/confirmation discrepancy <=1e-9. This 1e-9 cross-rule tolerance is a new prospective numerical qualification, stricter than T63's 1e-6; no historical result or physical acceptance gate is changed. Any control disagreement fails the invocation before search.

After the full bounded search, freeze exactly one selected mixture's six geometry values, η and Γ. Evaluate that identical tuple against S256 and S128, each by direct 8x6 and 16x12 integrals. At every direct node, reconstruct the original reference and accumulate (q_ref-q_model)² with positive weight; do not reconstruct the numerator from C-2ΓB+Γ²M. Primary/confirmation field-score difference must be <=1e-9. Selected S256 primary contraction/direct difference must also be <=1e-9. Both field-score estimates must satisfy the unchanged .10 gate for a positive witness. Any confirmation disagreement is a numerical qualification failure, with no refitting or replacement candidate.

For every direct rule integral, compare its independently accumulated reference denominator with the polynomial C using rtol=3e-11, atol=3e-14. Full-space control and selected-candidate moments use the analytic mixture formulas. Cross-check the between-component covariance formula against raw second moments minus μμᵀ with the same tolerances; a witness requires the original moment gates under both numerically agreeing routes. This adds at most four fixed model-moment route evaluations (two models × two routes), and eight model/reference/route moment-gate comparisons, outside the search's moment-check budget. Separately report full-space circulation/impulse and finite-D8 mass/impulse accumulated during both existing direct rules, including primary/confirmation agreement at the same tolerances. These diagnostics add no new nodes; report their reductions separately. Finite-D8 diagnostics do not replace the full-space acceptance moments or assert zero exterior tails. S128 supplies no selection information.

## 3. Fixed outer domain, initial bank and bounded refinement

Restrict each component to **s_r,s_z in [.5,1.5] and z in [-.5,1.5]**. These ranges are a declared search restriction around the existing unit-width, displaced task, not a consequence of the moment gates for all mixtures. No geometry outside them is evaluated or clipped into them. No minimum nonzero weight is imposed. Record zero-weight and identical-component cases explicitly.

The initial bank contains **45** components from the Cartesian product

    s_r in [.75, 1., 1.25], s_z in [.75, 1., 1.25],
    z in [-.5, 0., .5, 1., 1.5],

plus the **one frozen T63 selected geometry**, for **46** components. Enumerate s_r outermost, s_z next, z innermost; append the T63 geometry last. Its primary projected amplitude is allowed within the search, but it is a different operation from the fixed-amplitude control. Enumerate all unordered bank pairs including equal indices in increasing (i,j), i<=j: **1081 initial geometry proposals**. Do not omit identical components or individual single-Gaussian boundary cases.

For computation, canonicalize each pair by lexicographic (z,s_r,s_z) component order. When reusing an already weighted tuple after a swap, also transform η to 1-η. Cached geometry/basis keys use exact stored floating-point tuples, not a tolerance that merges distinct proposals. Log proposed order, canonical order, duplicates and bound rejections.

After all bank pairs, choose up to **four distinct canonical pairs** with qualified feasible candidates, ranked by descending J; break equal-J ties by the explicit lexicographic key ((z1,s_r1,s_z1),(z2,s_r2,s_z2)), then smaller η. If fewer exist, use exactly those available; if none exists, perform no local refinement and retain an inconclusive search. Do not invent another start. Different pairs may represent the same zero-weight field; that does not justify deleting their distinct dormant geometry.

Each start is refined independently through three fixed levels. Width step sizes are **.10, .05, .025** and corresponding axial-center steps **.20, .10, .05**. Each level has at most **eight complete polls**. A poll holds its center fixed while proposing negative then positive perturbation of each of the six coordinates in order (s_r1,s_z1,z1,s_r2,s_z2,z2), exactly twelve attempted neighbors. Reject outside-box neighbors without clipping; reject or reuse duplicate geometries as recorded, while still charging the proposal. After all twelve attempts, choose the neighbor with greatest primary J using the same geometry/η tie key, and make at most one move. Move only for strictly larger primary J than the current center; equal J preserves the current center. If no strict improvement exists, advance immediately to the next fixed level, without extra directions. After eight polls, advance regardless of progress. Each start retains its best qualified candidate found.

This gives at most **4×3×8×12=1152 neighbor proposals**, and **2233 total geometry proposals** including the bank. Each neighbor changes only one component, so exact-key component caching permits at most **1198 distinct S256 component bases** (46+1152). If implementation would exceed either cap, stop as a budget failure rather than silently dropping accounting or changing the search. Select the best qualified feasible candidate found across the bank and all refinements, using the same ranking. Never call it the global or continuous-geometry optimum.

## 4. Fixed-geometry weight feasibility: exact arithmetic on rounded coefficients

For each evaluated geometry, construct the axial interval and the degree-at-most-four covariance polynomial from the original full-space formulas and S256 reference. Generate binary64 H entries and coefficients in the fixed order given in DERIVATION §2, using math.fsum for Frobenius sums. Convert these generated finite binary64 values exactly to standard-library Fraction rationals. Axial linear constraints similarly use exact rational representations of the stored values, including μ_z, z_l and .10; divide without a second floating-point rounding. **Exactness here concerns these rounded-coefficient polynomials only**, not π, square roots, reference errors or the original real-arithmetic physical gates.

Trim exactly zero leading coefficients; do not use an epsilon to change the degree. Treat zero, constant, linear and lower-degree cases explicitly. Intersect the axial interval with [0,1], retaining singleton intervals. Separate exact endpoint roots before counting interior roots. Compute gcd(P,P') and the square-free polynomial with exact rational long division; retain multiplicities and the original P's signs. Use its Sturm chain to isolate all distinct interior real roots, including repeated/tangent roots. Count roots on subintervals, bisect left before right, and retain exact rational roots encountered. Use the original polynomial's signs on each complementary interval, not merely sign changes across roots, to identify feasible intervals and isolated feasible roots.

Per geometry hard limits are: degree **<=4**, at most **24 exact polynomial long divisions** covering all degree reduction/GCD/square-free/Sturm work, at most **five polynomials in a Sturm chain**, maximum **8192 bits** for any retained rational numerator/denominator, at most **512 isolation tree nodes**, and maximum depth **64**. Every retained non-exact root bracket must have one distinct root and width **<=2^-40** before it can generate a boundary candidate. Count rational arithmetic/long divisions, chain lengths, maximum bit sizes, root counts, nodes and depths. These caps do not promise every ill-conditioned polynomial is resolvable in time.

Hitting a per-geometry cap, inconsistent root count, undefined division, unresolved multiplicity/sign or an unrepresentable isolated feasible point records **inner feasibility unresolved**, with its reason and partial work. It must not be relabeled infeasible. Remaining originally scheduled geometries may proceed, but there is no precision escalation, new solver, extra start or component. Global time/memory limits still end the entire invocation without a qualified result.

Construct the stationary numerator A0+A1η from exact rational representations of the stored primary b1,b2,M11,M12,M22, using the algebra in DERIVATION §3. If A1!=0, retain its exact rational root; if A1=0 and A0!=0, record monotonicity; if both vanish, record the constant-objective degeneracy. Do not infer degeneracy from a small coefficient. There is at most one stationary root. Its exactness is again for the rounded discrete coefficients, not the continuous objective.

## 5. Representable weight candidates and unresolved boundaries

Mathematical interval/root completeness does not guarantee that an isolated feasible root is representable as a binary64 η. Use this predetermined candidate construction, then sort increasing η and deduplicate exact floating values:

- For each of at most four non-exact polynomial root brackets, propose float(left), float(midpoint), float(right). For an exact rational polynomial root, propose its nearest binary64 value and the two adjacent binary64 values instead. Maximum **12** attempts.
- For the two axial/[0,1] interval endpoints, propose the nearest binary64 value and its two adjacent values. Maximum **6** attempts, including a duplicated singleton endpoint if present in the attempt log.
- For the at most one stationary root lying within the axial interval, propose its nearest binary64 value and its two adjacent values. Maximum **3** attempts.
- For each of at most five feasible open intervals, propose the binary64 midpoint of the certified root-free interior remaining between neighboring root brackets/endpoints. Maximum **5** attempts. If no such interior is isolated, retain the unresolved case rather than fabricating a midpoint.

Thus at most **26 weight attempts per evaluated geometry**, **58058** overall. Count attempts before deduplication and record outside-[0,1] rejections. Evaluate the original, unexpanded full-space moment formulas at every retained in-range value with the original unrelaxed gates; record the rounded-polynomial classification separately. If a root-boundary classification and original moment test disagree, retain that disagreement and mark the geometry's inner search incomplete. No tolerance turns an original gate failure into a pass. A representable candidate that passes the original formulas may still be retained as a valid candidate, but it is not described as the certified optimizer of the original continuous feasible set.

An isolated feasible point without a qualifying representable candidate remains explicitly unresolved. For a mathematically feasible boundary/open interval with no surviving candidate, do not silently claim exhaustive optimization. Score only candidates with positive finite B,M,Γ=B/M and passing original moment gates; retain all failed/undefined attempts and the reason. Candidate ranks use the primary J, with the stated ties. If a geometry has no feasible set for its exactly rounded polynomial, record that restricted fact, not a physical-family impossibility.

Report `root_isolation_complete_for_rounded_polynomial` and `representable_candidate_construction_complete` separately from witness status, per geometry and as all-searched-geometry conjunctions. The first concerns classification/isolation of the exactly rounded polynomial; the second is false for unresolved candidate coverage or a polynomial/direct-moment discrepancy. Both are procedural flags. Even when both are true, finite root brackets and representable boundary approximations do not establish exact maximization of the continuous rounded-coefficient problem, global geometry coverage, or a formal continuum result. A positive endpoint witness may survive unresolved unselected geometries only after complete direct qualification of the selected tuple. A miss with any unresolved geometry is explicitly inconclusive.

## 6. Full work caps, records and verdicts

Count actual work and all rejected/duplicate attempts; do not substitute caps for measurements. Fixed qualification/confirmation work includes:

| Work | Fixed value or maximum |
|---|---:|
| Input files / decoded arrays | exactly 2 / 12 |
| Rules / unique 1D nodes | exactly 6 / 47 |
| Reference polynomial node-cell samples | exactly 983040 |
| Reference corner-cell samples | exactly 655360 |
| Fixed-amplitude control primary contractions | exactly 2 |
| Additional control axis-node exponential evaluations | <=7680 |
| Additional control diagonal Gram axis products | <=7680 |
| Additional control three-term contraction cell visits | <=491520 |
| Initial geometry proposals | exactly 1081 |
| Neighbor proposals | <=1152 |
| Total geometry proposals | <=2233 |
| Distinct S256 component bases | <=1198 |
| S256 component axis-node exponential evaluations | <=6133760 |
| Three-term reference contraction cell visits | <=471072768 |
| Cached diagonal Gram axis products | <=6133760 |
| Cross-Gram axis products, one pair per evaluated geometry | <=11432960 |
| Rational polynomial long divisions | <=53592 |
| Root-isolation nodes | <=1143296 |
| Weight attempts / original moment checks | <=58058 each |
| Fixed control/selected full-space moment route evaluations | <=4 |
| Fixed model/reference/route moment-gate comparisons | <=8 |
| Direct control integrals, two references × two rules | exactly 4 |
| Direct selected-mixture integrals, if one selected candidate exists | exactly 4 |
| All direct reference/model node-cell samples | <=78643200 |
| Direct component point evaluations | <=117964800 |

The contraction cell cap is 1198×3×256×512. Axis caps use 8×256+6×512=5120 points. Diagonal and cross Gram products are counted separately from exponentials. Control contraction work uses its unchanged geometry on both references; its two reference contractions, axis exponentials/products and cell visits are **additional** to the S256 search caps. Their maxima are 5120+2560=7680 axis points and 3×(256×512+128×256)=491520 cell visits. Report control/search attribution separately and count actual cached reuse only once. The four control direct integrals consume 39321600 node-cell samples; four mixture direct integrals consume another 39321600. Each selected-mixture sample evaluates at most two components; an exactly zero-weight or identical-component simplification may reduce actual component work but never removes original node-cell accounting. No new full numerical-array artifact is required: retain the selected parameters and all b/M/η/Γ/score summaries in scalar records.

At most 1198 S256 bases require 6133760 cached axis values (about 49 MB of float64 payload), plus centered contractions and bookkeeping. This is a storage estimate, not a substitute for observed peak memory or a speed claim. Exact-rational arithmetic, reference contractions and direct confirmation are fully inside 120 seconds; the stated worst-case operation caps do not guarantee that wall-time ceiling will suffice. Timeout remains a preserved failure, not a reason to enlarge the budget or end early with an unconfirmed candidate.

Save a per-phase journal, all proposal decisions, roots/brackets/multiplicities and unresolved reasons, candidate counts, the selected tuple, qualification comparisons and complete resource/execution receipts. Scientific counts include library work used for rules and all rational operations; historical/reference setup costs stay in the tracked series. Do not discard failed geometry records to make only successful work visible.

Possible outcomes are: a numerically qualified **ordinary two-Gaussian endpoint witness** passing both direct field estimates and original analytic moments on both references, with held-candidate field-score difference <=.001; **qualified bounded-search inconclusive** when no such stable witness is found; **reference-sensitive inconclusive** when the fixed candidate's reference comparison exceeds .001; or a preserved **numerical/identity/resource failure**. Per-geometry unresolved work is disclosed independently. No outcome is family exclusion, a causal/conservation-preserving solver or a new contribution. A qualified ordinary compact witness closes this specific endpoint-capacity motivation; any further method task needs a separately evidenced causal, control, conservation or complete-cost question. There is no automatic third component or retry.
