# Reference slack and one bounded correction

This is post-result analysis of the frozen T33 failure, with arithmetic on saved values and a real-arithmetic derivation. No new Gaussian projection, density/CDF/exp evaluation, integration or reference implementation is executed. This is an ordinary reference construction, not a proposed TOG contribution.

## Specific evidence

The unresolved red interval has width0.0022034782757317518 including omission uncertainty, exceeding twice the0.0010000001 comparison tolerance. Thus its interval itself prevents acceptance of any answer. The57 retained source colors have red minimum0.9320010346900842 and maximum1.217375068507919, a span of approximately0.285374. Their widths h are equal. The common positive color level is appreciable relative to their variation. The full leaf partition and absorption sum are consistent; the reference omission radius is only4.2050806003502847e-13. These facts locate a concrete candidate for the slack without proving that the GL output is accurate or that a correction will finish the subset.

The current cell construction independently bounds numerator and denominator:

    sum(c_i * ell_i) / sum(u_i) <= mixture color <= sum(c_i * u_i) / sum(ell_i),

then clips to the retained color range. Here ell_i and u_i bound the SAME component density d_i throughout a cell. Independent division discards that shared density. If c_i=c0, the un-clipped formula gives c0*sum(ell)/sum(u) through c0*sum(u)/sum(ell), although the exact color is c0. Existing color-range clipping already fixes that equal-color channel, and the separate global equal-color shortcut also handles the full RGB case. Thus equal colors are not a new failing case or a claimed gain. For unequal colors, the clipped quotient is generally not invariant to a common color offset and can still inherit denominator/numerator dependency slack. This motivates fixing the full density-box optimization rather than adding a sequence of increasingly shifted residual heuristics.

## Exact extrema within the existing density box

For a channel, sort indices by c_1<=...<=c_N once per ray, with source index as deterministic tie breaker. Consider

    R(d) = sum(c_i*d_i) / sum(d_i),   ell_i <= d_i <= u_i.

Assume initially sum(ell)>0. The feasible box is compact and the denominator positive, so extrema exist. At a maximum value R*, a coordinate with c_i>R* must be at u_i, while one with c_i<R* must be at ell_i: changing it toward that endpoint otherwise raises sum((c_i-R*)*d_i) above zero and hence raises the ratio, a contradiction. Coordinates tied at R* can use either endpoint. Therefore a maximum is attained among the N+1 threshold corners

    d_i = ell_i for i<=m; u_i for i>m,  m=0,...,N.

For the minimum, reverse ell/u. Enumerating these ratios and taking their maximum/minimum yields the exact channel extrema over this box in real arithmetic. Different channels may attain extrema at different corners; the resulting per-channel intervals still enclose every RGB value. The ordinary answer is absent from this calculation.

If sum(ell)=0, all lower bounds are zero. Exclude the zero-denominator vector. Any color mixture is a convex combination of components having u_i>0, and each such component alone is feasible with positive mass. Thus the exact extrema are the smallest/largest colors among u_i>0. If no upper bound is positive, the density box cannot support this calculation; report a numerical/bound-construction failure rather than silently declare vacuum. Zero-upper coordinates have no contribution. Equal-color/tied-color cases and single positive components follow directly. Binary64 underflow and accumulated arithmetic remain separate numerical obligations.

These extrema are at least as tight as the old independent quotient bounds intersected with the color range, because those bounds enclose every feasible ratio. They also translate exactly under c_i -> c_i+b: the entire interval shifts by b rather than gaining artificial uncertainty from the common color. The correction removes the whole numerator/denominator dependency relaxation for the current density box. It does not remove the remaining relaxation that different densities reach their endpoint bounds at different spatial positions.

## Complete cost and limits

The three color orderings cost O(3N log N) once per ray and must be counted. Prefix and suffix weighted/unweighted sums give all N+1 corners with O(3N) arithmetic per cell and O(3N) scratch storage; no new CDF, exponential, Gaussian projection or split location is needed. Use prefix/suffix construction, not subtraction from nearly equal totals. A future implementation must specify stable summation, zero-denominator handling and numerical range checks before execution. These are operation bounds, not a measured speedup. Sorting and all extrema scans belong to reference cost.

The same cell absorption W and full-field omission coupling remain. In particular, keep the ORIGINAL full-field maximum color in the omission charge; centering or optimization over retained colors does not permit replacing it with a smaller residual maximum. Existing unit rays, alpha, field semantics and endpoint stopping remain unchanged.

The analysis supports at most one separately frozen qualification using this complete box correction, on the full unchanged geometric subset and original budgets. No implementation or invocation has occurred here. If it still cannot complete, close this density-box reference route on these fields rather than add cells or pursue further local variants. Any independent high-order/high-precision empirical reference would need a distinct, justified contract; GL4/8 self-agreement alone does not become a truth source.
