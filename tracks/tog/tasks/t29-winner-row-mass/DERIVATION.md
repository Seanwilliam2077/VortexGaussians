# T29 — row-mass refinement of the existing winner-prefix bound

29 October 2026. Exact-real algebra for the unchanged whole-primitive sorted output. No fixture values, references or numerical methods were evaluated. The argument adds a probability-budget constraint to [T21](../t21-winner-prefix-bound/DERIVATION.md); its optimization is elementary fractional knapsack, not a novelty or TOG-contribution claim.

## Inherited model and row feasibility

Use T21's stable sorted ranks `i=1,...,N`, nonnegative integrable continuous densities, clipped masses `tau_i`, constant bounded RGB colors `c_i`, and identical background contribution. Retain

```text
alpha_i = 1-exp(-tau_i)
P_i = exp(-sum_{k<i} tau_k)
q_i = P_i*alpha_i
Delta = L_exact-L_sorted = sum_{i<j} (c_j-c_i)*w_ij.
```

Here `w_ij` is the probability that the sorted winner is i and the exact first-arrival winner is j. Conditional on differing winners, necessarily `j>i`. For fixed i these winner events are disjoint subsets of `S_i={sorted winner is i}`. Independence of the label processes gives `Pr(S_i)=q_i`, hence

```text
sum_{j>i} w_ij = Pr(S_i and exact winner differs from i) <= q_i.
```

T21 already proves `0<=w_ij<=C_ij=P_i*B_ij`. Either inherited T17 choice is valid: `B_simple` or `B_jensen`, with `0<=B_jensen<=B_simple<=alpha_i*alpha_j`. Their Gaussian inversion, full-line weights and finite-clipping formulas remain unchanged. Thus each actual row belongs to

```text
K_i(B) = { x : 0<=x_j<=C_ij, sum_{j>i} x_j<=q_i }.
```

This is a relaxation: row probabilities also obey relationships absent from K. Optimizing over K need not recover the true error.

## Signed row optimization

For channel h and sign s in `{+1,-1}`, define

```text
a_ij^(s,h) = max(s*(c_jh-c_ih),0)
F_i^(s,h) = max_{x in K_i(B)} sum_{j>i} a_ij^(s,h)*x_j.
```

Compute F by sorting strictly positive coefficients in descending order, breaking ties deterministically by sorted rank j. Start with remaining budget `r=q_i`. For each coefficient in that order, assign `x_j=min(C_ij,r)`, add `a_ij*x_j`, and subtract x from r; stop when r is zero. Unassigned variables are zero. No division by a coefficient or cap is needed.

An exchange argument proves optimality. If a lower-coefficient variable receives positive mass while a higher-coefficient variable has unused capacity, transferring their feasible minimum amount upward preserves constraints and cannot decrease the objective. Repeating yields greedy allocation; unused budget can be assigned to positive coefficients until budget or capacities are exhausted. Zero coefficients do not affect the optimum. Different channel/sign optima need not share one maximizing probability vector: each supplies a separate valid coordinate bound.

Because actual w is feasible and negative signed contributions can be discarded for an upper bound, set

```text
U_h = sum_i F_i^(+,h);  V_h = sum_i F_i^(-,h)
Q = 1-exp(-sum_i tau_i)
G_h = Q*(max_i c_ih-min_i c_ih)
Delta_h in [-min(G_h,V_h), min(G_h,U_h)]
E_h = min(G_h,max(U_h,V_h)).
```

The independent G bound is inherited unchanged. E bounds error around the original sorted RGB, not an interval midpoint output. For N=0 define G and E as zero without extrema.

## Cheaper envelope and dominance

For one row/sign/channel, discard zero-coefficient or zero-cap variables, which cannot contribute. Define the maximum over that retained support (empty maximum zero) and write

```text
R_i = sum_{j>i} a_ij*C_ij
M_i = max_{j>i, a_ij>0, C_ij>0} a_ij
H_i = min(R_i, q_i*M_i).
```

Every feasible objective is at most R by individual caps and at most `q_i*M_i` by the row budget. Therefore `0<=F_i<=H_i<=R_i`. Summing separately by sign and applying the same G intersection proves componentwise

```text
E_exact_row_LP <= E_row_envelope <= E_T21_prefix_signed.
```

Both signed endpoints tighten as well. T21's further dominance over signed-only and the original absolute pair sum is retained. For Jensen versus simple, q and coefficients coincide while all Jensen capacities decrease. Its feasible set is contained in the simple set, so its F cannot increase. R decreases; positive-cap support can only shrink, so M and `q*M` cannot increase. This gives the same monotonicity for H and the final bounds. None of these inequalities promises strict improvement or an accuracy-threshold crossing.

Zero-mass rows have q=0 and zero inherited capacities. Zero-cap pairs and zero coefficients contribute nothing; equal colors give zero error bound. N<=1 has no pairs. For N=2 only `(1,2)` exists, and `C_12=B_12<=alpha_1*alpha_2<=q_1=alpha_1`; the row constraint is redundant. Both refinements equal T21 in every channel for both inherited B choices.

## Cost and numerical boundary

The envelope requires only a fixed six-channel/sign scan: O(N²) reduction work. The straightforward LP implementation sorts separately per row/sign/channel, costing O(N² log N) time and O(N) temporary storage beyond the pair table. Six global color orders could serve every row by filtering `j>i` (descending c for positive, ascending for negative), but that alternative is not assumed to have been implemented or timed.

These reductions still require the original preparation, clipped masses, stable mean sort, O(N²) Gaussian pair/CDF/saturation work and prefix/cap products. Complete delivery also pays compositing, decisions, discarded work and any fallback. Saved pair tables do not erase these costs.

All feasibility and dominance claims above concern exact reals and valid inherited caps. Binary64 exponentials, products, budget subtraction and sums are not outward-rounded certificates; underflow can invalidate conservativeness. Empirical comparisons with fixed references would require separately frozen tolerances. Formulas use only same-input masses, colors, ordering and inherited caps; fixture labels, unseen colors, references and oracle errors cannot select coefficients, capacities or branches. No numerical, speed, novelty or submission conclusion follows from this derivation.

## Dual accounting and global cap

For any `lambda>=0`,

```text
D(lambda) = lambda*q + sum_j C_j*max(a_j-lambda,0)
```

upper-bounds every feasible objective: `a_j*x_j<=lambda*x_j+C_j*max(a_j-lambda,0)`, then `sum x<=q`. Choose lambda at the greedy cutoff; use zero when budget exceeds all positive-coefficient capacities, or `max a` when q=0. At exact capacity equality, zero or the last allocated coefficient is optimal. The primal and dual coincide over reals, including the real interpretation of stored scalars.

The planned binary64 runner computes both, checks their gap at `1e-12`, and reports the dual as its candidate row bound. Agreement does not establish a formal floating-point certificate or validate inherited rounded capacities.

For the exact row LP and envelope, `sum_i q_i=Q` and each coefficient is at most its channel's color range. Thus both signed sums are already at most G: the global cap is redundant over reals. Retaining it preserves the inherited output contract.
