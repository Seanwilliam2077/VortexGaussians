# Post-run implication: the saved Euler-target candidate has a descent direction

This analysis was added after the sole T75 measurement. It does not alter the frozen protocol, derivation, input, worker or original results. Root proposed the argument; it is separately reviewed as mathematics, not a second numerical experiment.

Let q be the saved current state, q+ its saved successor, h=1/32, F the derivative at q, and y=q+hF the same Euler target used by the original ordinary search. The two states have identical component geometries and strictly positive component circulation coefficients c_i and c_i+. Thus

\[
v_s=(q_+-q)/h\in W,\qquad y-q_+=h(F-v_s).
\]

Their full ordinary tangent spaces coincide: amplitude columns g_i are unchanged, while each geometry column at q+ is its column at q multiplied by c_i+/c_i. These nonzero factors change coordinates, not the span V. Consequently

\[
P_V(y-q_+)=h(P_VF-v_s).
\]

Set d=P_VF-v_s. Because v_s lies in W and W is contained in V, exact orthogonal projections give

\[
\|d\|_H^2=\|P_VF-P_WF\|_H^2+\|P_WF-v_s\|_H^2.
\]

The measured additional geometry term is well resolved and positive. Equality of the saved weight solution with its optimum is therefore not required for the nonstationarity conclusion. It merely explains why the second term is negligible here.

At the positive state q+, any finite parameter rate in V can be realized by a smooth sufficiently short curve of positive component coefficients and positive logarithmic widths. Choose such a curve p(epsilon), p(0)=q+, p'(0)=d. For the unchanged Euler-target objective,

\[
\left.\frac{d}{d\epsilon}\|y-p(\epsilon)\|_H^2\right|_0
=-2\langle y-q_+,d\rangle_H=-2h\|d\|_H^2<0.
\]

The geometry rates in coordinates at q+ are obtained from the original projected rates by multiplication by c_i/c_i+; amplitude rates subtract those of v_s. There is no zero-weight boundary or coincident rank loss at this selected state. This feasibility statement concerns the positive two-Gaussian family used for the tangent. A claim of feasible descent inside an additional hard geometry box would also require checking that q+ is a strict interior point; T75 does not add that numerical claim.

The same argument applies to each positive-weight discrete quadrature objective. The numerical checks establish a large, consistently resolved discrete gap; transferring it to the intended all-space H problem has the empirical integration limitations already stated in PROTOCOL.md. This is not a formal floating-point/tail certificate.

This sharpens the practical diagnosis: the saved candidate is supported as nonstationary for the ordinary fixed Euler-target problem, and a sufficiently small admissible local decrease exists in the mathematical model. It does **not** construct or measure an improved finite candidate, prescribe a useful step size, settle a bounded nonlinear optimizer, prove global optimality, remove Euler time-discretization error, preserve invariants, or explain the full T71 trajectory. The worker's `finite_step_improvement=false` remains correct as an experimental claim. A further fixed-budget ordinary solver measurement is needed before claiming practical finite-step or full-window improvement.
