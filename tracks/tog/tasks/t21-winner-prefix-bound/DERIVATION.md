# T21: winner-prefix and signed bound for the existing sorted output

29 October 2026. **Real-arithmetic derivation only; no numerical execution, novelty claim, or speed result.** The motivation is the loose dense bounds in [T18's saved qualification](../t18-reference-robustness/README.md). This is a natural tightening of the [T17 first-arrival coupling](../t17-order-inversion-bound/DERIVATION.md), applied to the same continuous model and the same whole-primitive sorted output. It does not establish a Gaussian-specific research contribution.

The selected construction combines one sorted-winner prefix factor with a signed error interval capped by the existing symmetric global bound G. Both inherited simple and Jensen pair bounds are used; Jensen is the primary admission bound. A signed-only calculation with every prefix factor replaced by one is an attribution diagnostic, not a separately selected alternative. This document defines no changed output color or additional bound construction.

## Model, ordering, and sign convention

On the same finite interval `[a,b]`, let `s_i(t)>=0` be integrable continuous ray densities with finite optical masses and constant bounded RGB colors `c_i`. The saved inputs have Gaussian densities and `c_i in [0,1]^3`. Use the existing stable mean order, relabeling its ranks as `1,...,N`. The inequalities `i<j` below concern these sorted ranks, not the numerical ordering of original input indices.

```text
A_i(t) = integral_a^t s_i(u) du
tau_i  = A_i(b)
alpha_i = 1-exp(-tau_i)
P_i = exp(-sum_{k<i} tau_k)
T(t) = exp(-sum_i A_i(t))
Q = 1-T(b)

L_exact  = integral_a^b T(t) sum_i s_i(t)c_i dt + T(b) background
L_sorted = sum_i P_i*alpha_i*c_i + T(b) background
Delta    = L_exact-L_sorted.
```

All bounds and positive/negative parts of colors are componentwise. For N=0 the error bound is zero without evaluating color extrema. Optical masses remain the original clipped masses. The inherited pair bound uses full-line Gaussian weights where the T17 finite-clipping derivation requires them; T21 makes no change to that formula. The two outputs have exactly the same background contribution in real arithmetic.

## Exact winner-event probability

As in T17, couple the outputs using independent inhomogeneous Poisson processes with intensities `s_i`. Let `F_i` be label i's first event, or infinity when that process is empty on `[a,b]`.

- The exact rule returns the earliest event's color, or background if all labels are empty.
- The sorted rule returns the smallest sorted index whose process is nonempty, with the same background event.

When the returned labels differ, the sorted winner i is smaller than the exact winner j. Define

```text
W_ij = {sorted winner is i and exact winner is j},   i<j
w_ij = Pr(W_ij)
E_ij = {F_j < F_i <= b}
D_ij = Pr(E_ij).
```

The events `W_ij` are disjoint. Every differing outcome has exactly one ordered winner pair, so their probability-weighted color difference gives the exact identity

```text
Delta = sum_{i<j} (c_j-c_i)*w_ij.
```

The continuous densities give zero probability of simultaneous first events. No independence between different winner events is assumed.

An exact integral for a winner event is

```text
w_ij = P_i * integral_a^b
       s_j(t) * exp(-sum_{k>i} A_k(t))
       * [exp(-A_i(t))-exp(-tau_i)] dt.
```

To verify it, condition on the first exact event belonging to j at time t. Every label `k<i` must be empty on the entire interval, giving the independent factor `P_i`. Label i must have no event before t but at least one event between t and b, giving `exp(-A_i(t))-exp(-tau_i)`. Label j has its first event at t, contributing `exp(-A_j(t))*s_j(t)dt`. Each other label `k>i` must have no event before t, contributing `exp(-A_k(t))`; its later events do not affect the winners. Multiplying these factors gives the displayed formula.

## Prefix cap from the inherited pair bound

The event that all labels `k<i` are empty is independent of `E_ij`, because those labels are distinct from i and j. Since `W_ij` is contained in the intersection of those two events,

```text
0 <= w_ij <= P_i*D_ij.
```

Equivalently, the exact integral above equals the T17 pair-event integral times `P_i` and the additional factor `exp(-sum_{k>i,k!=j} A_k(t))<=1`. This provides the same inequality without replacing a winner event by an equality to the pair event.

T17 proves both inherited bounds `D_ij<=B_simple_ij` and `D_ij<=B_jensen_ij`, with `0<=B_jensen_ij<=B_simple_ij`. For either fixed choice `B_ij`, the selected cap is therefore

```text
C_ij = P_i*B_ij
0 <= w_ij <= C_ij.
```

Only the prefix is factored out. The cap still ignores some competing labels and the mutual exclusion of winner events within one sorted-winner row. It can remain loose.

## Selected signed interval and scalar-per-channel bound

For the same selected B, define

```text
d_ij = c_j-c_i
U = sum_{i<j} max(d_ij, 0)*C_ij
V = sum_{i<j} max(-d_ij,0)*C_ij
G = Q*(max_i c_i-min_i c_i).
```

For each channel, a nonnegative coefficient `d_ij` contributes between zero and `d_ij*C_ij`; a negative coefficient contributes between `d_ij*C_ij` and zero. Applying these bounds to the exact signed identity, before summing absolute color differences, yields

```text
-V <= Delta <= U.
```

Both exact and sorted emission are nonnegative mixtures of the same component colors with total weight Q. Thus the existing independent global result is `-G<=Delta<=G`. Intersecting these two intervals gives exactly the frozen T21 interval and error bound:

```text
Delta in [-min(G,V), min(G,U)]
E = max(min(G,V), min(G,U))
  = min(G, max(U,V))
abs(L_exact-L_sorted) <= E.
```

The maximum channel of E bounds the error of the original sorted RGB. The signed interval's half-width is not the error radius of that fixed output. The two B choices yield `E_simple_prefix_signed` and `E_jensen_prefix_signed`; the latter is primary. A diagnostic sets `P_i=1` in these same U/V expressions to separate signed treatment from the prefix contribution. It does not change the selected method or output.

This construction does not presume cancellation of unknown positive and negative error terms: their magnitudes are not known. It uses separate upper bounds for the two signs, and then takes their maximum to bound absolute error. The disjoint winner-event interpretation justifies the exact signed sum; no sum of independently sampled pair outcomes is introduced.

## Dominance and limits

For any inherited nonnegative pair bound B,

```text
U+V = sum_{i<j} abs(c_j-c_i)*P_i*B_ij
    <= sum_{i<j} abs(c_j-c_i)*B_ij,
```

because `0<=P_i<=1`. Also `max(U,V)<=U+V`. Applying the same global cap proves componentwise

```text
E_prefix_signed <= E_signed_only <= E_T17_original,
```

where the signed-only diagnostic has `P_i=1` and the original T17 bound is `min(G,sum abs(c_j-c_i)*B_ij)`. The first inequality follows from each nonnegative U and V term decreasing under the prefix; the second follows from `max(U,V)<=U+V`. Since the inherited Jensen B is no larger than the inherited simple B, the same monotonicity proves `E_jensen_prefix_signed<=E_simple_prefix_signed`.

These are non-strict algebraic inequalities. A smaller value does not necessarily cross a useful accuracy threshold or reduce complete delivery cost.

- The first sorted row has `P_1=1` and receives no prefix reduction. Suppression of later rows cannot remove a loose dominant first-row contribution.
- For N=2 there is only the pair `(1,2)`. Its prefix is one; in each channel only one sign is present, so `max(U,V)=abs(c_2-c_1)*B_12`. The selected absolute bound equals the original T17 bound. Prefix and signed treatment supply no improvement in this two-label case.
- With multiple pairs, both signs may occur in a channel. Separating their upper bounds can improve the bound even when all prefix factors in the diagnostic are one. This is why attribution must retain the signed-only diagnostic.
- Empty/zero-mass rays have Q=0. Identical component colors give zero U and V. A zero pair cap contributes zero without any division by it.
- In dense or opaque cases many independent caps can still exceed the probability of a row or of all differing outcomes. The selected global cap prevents an unbounded color estimate, but no informative dense-case result is promised.

## Cost and numerical meaning

From N clipped masses, computing all prefix values costs O(N) prefix accumulation and attenuation work and O(N) storage. Scanning the stored pair table costs O(N^2) arithmetic: one prefix-cap product and fixed RGB positive/negative accumulation per pair. A streaming reduction needs O(N) additional working storage beyond its input table. No new Gaussian CDF, quadrature, integrand evaluation, or sample is required for that saved-data reduction.

Producing the inputs to the bound in a real delivery still requires parameter preparation, clipped optical masses, the declared sort, and the inherited O(N^2) pair construction, including its Gaussian CDF and saturation work. Those costs do not disappear because a saved pair table is available during an audit. Full delivery would also count the sorted output, bound checks, any discarded bound work and fallback. No runtime, amortization, or production-renderer improvement is claimed here.

The probability proof and dominance statements are over exact reals with valid inherited B. Existing stored masses/B values and ordinary binary64 prefix exponentials, products and sums are not outward-rounded enclosures. Underflow of a positive prefix to zero can invalidate a claimed numerical certificate; cumulative and global-cap rounding also need accounting. A saved-data comparison against already qualified references can be empirical evidence under its explicitly fixed tolerance, but is neither a new numerical solve nor a formal floating-point proof. Historical qualifications and their gates remain unchanged.

The prefix factor follows from elementary independence in the existing coupling and works for arbitrary nonnegative continuous ray densities. Signed interval arithmetic and the existing color-range cap are ordinary tools. The derivation supplies a concrete question for a bounded saved-data assessment; it supplies no literature priority, Gaussian-specific distinction, complete-cost result, or TOG contribution.
