# T20: local ordinary accuracy contract

29 October 2026. **Local mathematical derivation; no numerical execution and no novelty claim.** The governing boundary is [T19 NEXT_EVIDENCE](../t19-complete-cost/NEXT_EVIDENCE.md). This document makes the ordinary optical-depth enclosure already identified in [T15-C](../t15-core-hypothesis-selection/C_VOLUME.md) concrete. It does not repair T19 or supply a completed timing comparison. Root's bounded Cornell acquisition has now closed: the one metadata access returned a timeout/HTTP400, both allowed full-text attempts returned HTTP429, and zero pages/PDF bytes were acquired. The formulas below are not quotations or attributed implementations from that unread paper; its theorem-level mapping remains incomplete.

The fixed model is the continuous self-emission model in [T17 DERIVATION](../t17-order-inversion-bound/DERIVATION.md). [T18](../t18-reference-robustness/PROTOCOL.md) bounded one selected omission but retained empirical quadrature elsewhere. [T19's failure](../t19-complete-cost/README.md) demonstrates why an empirical stopping indicator is not a sufficient accuracy contract. Its already reported numerical residual is not recalculated here.

## Contract at a glance

| Item | Concrete ordinary contract | Guarantee or limitation |
|---|---|---|
| Input and target | Exact real interpretation of the stored finite interval `[a,b]`, Gaussian weights `w_i>=0`, widths `d_i>0`, means `mu_i`, constant linear RGB `c_i in [0,1]^3`, and background `g in [0,1]^3`. Compute `L=integral_a^b T(t) sum_i s_i(t)c_i dt + T(b)g`. | These are extinction densities, not learned peak opacities; no scattering, additional independent source term, or 3D scene conversion is implied. |
| Exact optical information | `s_i=w_i normal_pdf(mu_i,d_i)`, `F_i(t)=Phi((t-mu_i)/d_i)`, `A(t)=sum_i w_i(F_i(t)-F_i(a))`, `T(t)=exp(-A(t))`. On a cell `[l,r]`, `Delta A=sum_i w_i(F_i(r)-F_i(l))` and `W=T(l)-T(r)=T(l)(1-exp(-Delta A))`. | Exact formulas over real numbers. Calling binary64 `erf`, `erfc`, or `exp` is not exact or automatically conservative. |
| Sufficient local enclosure | Bound every density over the entire cell by `ell_i<=s_i<=u_i`. Construct the explicit nonnegative source/denominator ratio enclosure below, then multiply its color interval by nonnegative `W`. | Bounds cover the whole continuous cell, not only quadrature nodes. |
| Sufficient global stopping rule | Add all cell lower/upper RGB bounds and the exact attenuated background. Deliver their center only when the maximum channel half-width is at most epsilon. | This is sufficient in real arithmetic. A floating-point implementation must also enclose function evaluation, accumulation, and rounding of the delivered center. |
| Adaptive operator | Start with `[a,b]`; bisect the leaf with largest maximum-channel enclosure width, retaining all cells until the global criterion passes. Child bounds replace the parent's bounds. | No consecutive quadrature-rule agreement is used as a certificate. A resource or representability limit means unresolved accuracy, not successful delivery. |
| Required work | Parameter conversion/recognition; endpoint CDFs, endpoint density exponentials and transmission; per-cell density/source ranges, ratios and bounds; leaf selection, subdivision, accumulation and certified arithmetic if claimed. | Explicit counts below include preprocessing and failed refinement. No pair ordering, scene reuse, or hidden reference solve is supplied. |
| Necessary checks and empirical checks | Constant-color conservation identities can reject inconsistent output; Simpson/GL disagreement can signal a problem. | Neither small residual nor small rule disagreement proves a per-channel error bound. |
| Remaining mapping | The source audit must determine what the acquired paper actually defines and supports; a concrete numerical enclosure backend must be selected and qualified separately. | This local derivation neither fills an unread-paper gap nor authorizes a numerical queue. |

## 1. Whole-cell Gaussian and color ranges

Discard a label with exactly zero declared weight from range work; this is exact removal of a zero term, not a tail threshold. If every weight is zero, the exact answer is `g`. Otherwise each positive-weight Gaussian is strictly positive at every finite real coordinate.

Precompute its peak `K_i=w_i/(sqrt(2*pi)*d_i)`. A Gaussian on `[l,r]` is unimodal, so exact whole-cell density bounds are

```text
ell_i = min(s_i(l), s_i(r))
u_i   = K_i                         if l <= mu_i <= r
        max(s_i(l), s_i(r))         otherwise.
```

These bounds need two endpoint density values and a peak-in-cell test, not an integrand sampling heuristic. Endpoint values can be shared between adjacent cells. Finite clipping does not replace the full-line weight `w_i`: it changes the evaluation interval and the CDF mass difference.

For each channel k define

```text
S_minus = sum_i ell_i               S_plus = sum_i u_i
J_minus[k] = sum_i ell_i*c_i[k]      J_plus[k] = sum_i u_i*c_i[k]
c_min[k] = min_i c_i[k]             c_max[k] = max_i c_i[k].
```

With at least one positive Gaussian and a finite cell, `S_minus>0` in real arithmetic. Since all original channel colors are nonnegative,

```text
m[k] = max(c_min[k], J_minus[k]/S_plus)
M[k] = min(c_max[k], J_plus[k]/S_minus)

m[k] <= c_bar[k](t) := sum_i s_i(t)c_i[k] / sum_i s_i(t) <= M[k]
for every t in [l,r].
```

The proof is just interval division with a positive denominator: the numerator lies in `[J_minus,J_plus]`, the denominator in `[S_minus,S_plus]`, and the mixture is also a convex combination of component colors. Their interval intersection remains conservative. Separate numerator/denominator extrema need not occur at the same point, so this bound can be loose. No claim of tightness, optimality, Gaussian-specific novelty, or speed follows.

If a numerical lower denominator is zero because of underflow or wide enclosures, use the known global color range for that cell; never divide by zero or relabel a positive density as vacuum. Repeated global color bounds alone do not ensure convergence: summing their widths gives `Q*(c_max-c_min)`, independent of subdivision. A numerical implementation must resolve its local range uncertainty or return unresolved accuracy.

The familiar exact branches remain available: common component color gives constant mixture color; identical normalized profiles give the constant weight-averaged color; a single component is a special case. They do not require cell refinement. Their optical and output evaluations still require numerical error accounting if certification is claimed.

## 2. Sufficient emission enclosure and adaptive operation

Let `sigma=sum_i s_i`, so `-T'=T*sigma`. On any cell,

```text
E_cell = integral_l^r T(t)*sigma(t)*c_bar(t) dt
W_cell = integral_l^r T(t)*sigma(t) dt = T(l)-T(r) >= 0
W_cell*m <= E_cell <= W_cell*M.
```

For a partition of the entire original interval, form

```text
L_minus = T(b)*g + sum_cells W_cell*m_cell
L_plus  = T(b)*g + sum_cells W_cell*M_cell
L_hat   = (L_minus+L_plus)/2
radius  = (L_plus-L_minus)/2.
```

Then `abs(L_hat-L)<=radius` componentwise. Acceptance requires `max_k radius[k]<=epsilon`. No omitted extinction, early opacity termination, truncated component support, or background replacement is implicit in this operation. Any such approximation would need a separate counted bound.

A concrete ordinary refinement operator is:

1. Recognize exact parameter cases; otherwise construct the root cell `[a,b]` and its endpoint information and bounds.
2. Maintain the total RGB enclosure and a priority queue keyed by each leaf's maximum-channel enclosure width. Use left endpoint to break ties deterministically.
3. If the global radius satisfies epsilon, deliver the center. Otherwise split the selected leaf at its midpoint, evaluate the one new endpoint, form both child bounds, and replace the parent contribution by the children.
4. If a separately declared work/memory limit or floating-point coordinate resolution prevents sufficient refinement, return an unresolved-accuracy failure. Do not return the current center as though it met epsilon.

Over exact reals the density boxes tighten under cell inclusion; the lower color ratios cannot decrease and the upper ratios cannot increase. The optical masses of the two children sum to the parent's mass. Consequently replacing a parent by its children cannot widen the global real-arithmetic enclosure. For Gaussian mixtures on a fixed compact interval with positive total density, the local ratio ranges approach the point color uniformly as mesh size tends to zero. Since `sum W=1-T(b)<=1`, sufficiently fine uniform subdivision establishes the existence of an arbitrarily narrow real-arithmetic enclosure. This is not a bound on how many cells a particular adaptive run will require, nor a promise that a fixed-precision implementation reaches epsilon.

Equivalently, with optical coordinate `q=1-T(t)`, the emission is an integral of `c_bar` against a nonnegative measure. The construction is ordinary lower/upper integration bracketing. Analytic Gaussian mass makes the weights available; it does not make generic bracketing a new contribution.

## 3. Countable cost of this specific operator

Let N be the number of positive-weight labels after the charged zero-weight scan. With one initial cell and S successful bisections, the algorithm has `S+1` final leaves, `S+2` distinct endpoints, and has built `2*S+1` cell enclosures. This is bookkeeping, not a measured timing result.

| Work category | Count or order, including rejected work |
|---|---|
| Initial parameter work | O(N) conversions, validation/zero scan, peak/scale coefficients, exact-case recognition and three-channel extrema. No mean sort is required. |
| Endpoint Gaussian optical evaluations | `N*(S+2)` scalar CDF endpoint evaluations with endpoint reuse. Alternative stable interval-tail evaluation may require additional function calls; count whichever is implemented. |
| Endpoint density evaluation | `N*(S+2)` density exponential evaluations plus their O(N) coordinate arithmetic. Peaks `K_i` are precomputed. |
| Endpoint cumulative attenuation | O(N) mass-difference/reduction work per endpoint, and `S+1` transmission exponentials when `T(a)=1` is recognized exactly. All endpoint data are local to this delivered ray. |
| One cell enclosure | N endpoint-minimum/peak-maximum decisions; two density reductions; six nonnegative color-weighted reductions; six ratio evaluations, color-range intersections, and six optical-weight products. All are O(N) for fixed RGB dimension. |
| Optical cell weight | A subtraction of cached endpoint transmissions over exact reals. A stable `T(l)*[-expm1(-Delta A)]` implementation or bounded interval evaluation has its own additional counted reductions/transcendentals. |
| Refinement and total bounds | S parent removals, 2S child insertions and S selections; ordinary priority-queue work O(S log(S+1)), plus RGB total-bound updates. Conservative accumulation may cost more. |
| Storage | O(N*(S+2)) if all endpoint CDF/density arrays are cached, plus O(S+1) cell/queue data. A lower-memory recomputation variant must charge the repeated work. |
| Certification and stopping costs | Directed or interval arithmetic, special-function bounds, precision escalation if any, output-center error, failure accounting and all work before a limit. These costs have not been implemented or measured. |

In this exact bookkeeping the arithmetic/range work is O(N*(S+1)) plus queue work, including the root enclosure when S=0; S is accuracy- and input-dependent and has no cheap uniform upper bound asserted here. With a fixed initial multi-cell partition of P0 leaves, the corresponding counts would be `P0+S+1` endpoints and `P0+2*S` cell constructions, and building that partition would also cost work. That is an accounting identity, not authorization to tune a partition or run another workload.

Neither this count nor an integrand-evaluation count alone is a complete-renderer cost. Ray-to-Gaussian conversion, candidate traversal, acceleration structures, scene motion and physical parameter calibration are outside this fixed one-dimensional contract.

## 4. Necessary identities, empirical indicators, and sufficient bounds differ

For any constant vector v and scalar kappa satisfying `v dot c_i=kappa` for all active labels, the exact emission obeys

```text
v dot (L-T(b)*g) = kappa*(1-T(b)).
```

An exactly known residual r of this relation implies a lower bound `abs(r)/sum_k abs(v[k])` on maximum-channel error, when v is nonzero. It can reject output. A zero residual cannot guarantee accurate channels: a nonzero error vector orthogonal to v preserves the relation. For example, red/blue errors `(+delta,0,-delta)` preserve an R+B constraint. Finite-precision checks must account for uncertainty in the alleged exact right-hand side too.

Likewise, for any constant RGB c0,

```text
L = c0*(1-T(b)) + T(b)*g
    + integral_a^b T(t)*sum_i s_i(t)*(c_i-c0) dt.
```

This ordinary constant-part extraction is exact. It neither bounds the remaining integral nor licenses treating its possibly negative channels as nonnegative sources. The safe color-interval interpretation is to shift the already valid local range to `[m-c0,M-c0]` and multiply by nonnegative W. In floating interval arithmetic, signed endpoint products need their appropriate sign-aware minima/maxima; multiplying two lower endpoints is not generally a lower bound for a negative residual.

Consecutive Simpson or GL rule differences are empirical information unless accompanied by a proved enclosure of the remaining error under checked assumptions. Greater precision in summing those empirical differences does not turn them into a bound. The sufficient condition in this contract is containment of the continuous integral followed by the global radius test, not conservation or rule agreement.

Three evidence levels must remain distinct: (1) the real-arithmetic sufficient operator derived here; (2) an implemented binary64 method empirically qualified against a fixed accuracy reference and finite test workload; and (3) a formal numerical enclosure covering implementation errors. Level2 can support an honestly scoped empirical comparison without establishing level3. T19 was such a comparison and failed its actual output-accuracy gate; it did not require a floating-point proof. The certificate requirements below apply when claiming a certified enclosure, not as a blanket prohibition on future ordinary GL or other reasonably qualified empirical baselines.

## 5. Floating-point certificate gaps

The real-arithmetic proof is complete for the stated model; an implemented floating-point certificate is not supplied. At minimum it would require:

- A declared input semantics: exact stored binary64 parameters, or intervals covering uncertain parameters. Conditioning and uncertainties from converting a 3D scene cannot be silently ignored if that wider claim is made.
- Certified outward bounds for normalization, density exponentials, Gaussian CDF/error functions and optical transmission, including underflow and near-equal tail subtraction. Standard-library function calls and successful reference comparisons do not supply these bounds.
- Conservative whole-cell density extrema, nonnegative sum/product accumulation, positive-denominator division and color-range intersections. A computed zero lower bound is a loss of information, not proof of zero extinction.
- Conservative W and background evaluation. For example, valid endpoint intervals for T give `W in [max(0,T_l_lower-T_r_upper), max(0,T_l_upper-T_r_lower)]` with directed subtraction. The original nonnegative color range then permits appropriate interval products. Independent endpoint uncertainty can make these intervals loose.
- Conservative global accumulation and an enclosure for the actual returned binary64 RGB. If y is the representable center, bound each radius by `max(y-L_lower,L_upper-y)` using outward arithmetic; the real half-width formula alone omits center-rounding error.
- Explicit handling of subdivision/precision/work limits. Real-arithmetic monotonic tightening does not automatically survive separate floating enclosures; evaluation uncertainty can prevent convergence. Retaining or intersecting valid previous enclosures cannot manufacture missing precision.

T18's exact-rational charge for a particular omitted interval addresses only that omission. It does not supply any of these missing special-function, range, global-output or residual-integral certificates. This document selects no library, installs nothing, executes no numerical method, and does not label ordinary binary64 evaluation as certified.

## Bounded conclusion

A concrete sufficient ordinary operator and a countable one-dimensional cost contract exist without a new pair-bound mechanism. This is not yet an implemented or empirically qualified strong baseline, and its real-arithmetic assumptions and numerical certification obligations are different claims. T20 stops with its source-access budget exhausted and the required primary-source mapping incomplete; this does not imply that ordinary integration or a future empirical qualification is impossible. An unread paper is not evidence of absence. No subsequent numerical protocol or timing run is prepared here, and no TOG contribution follows from this derivation.
