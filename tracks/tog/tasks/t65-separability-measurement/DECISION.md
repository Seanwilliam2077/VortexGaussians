# T65 decision — test the saved leading product's joint requirements

## What the result changes

The relaxed separable error is about .09016, below .10 on both qualified references and under both matrix constructions. The original field criterion therefore does not compel a representation with radial/axial coupling. T63's local Gaussian miss remains unresolved: marginal shape, moment constraints or search coverage could matter. Neither the previous local miss nor the present relaxed optimum establishes Gaussian impossibility.

The next useful question is whether the **already computed S256 leading product** meets the other endpoint requirements. This reuses an ordinary result that already exists; no larger search, extra SVD, mixture or causal model is selected.

## Fixed next task T66: one saved-product diagnostic

Implement, statically review and freeze one saved-factor readback with **one <=60-second scientific child**, observed **512 MiB** peak working-set ceiling sampled every .25 seconds, >=1 GiB available memory at OS-only preflight and launch, and the same bundled Python 3.12.14/NumPy 2.3.5 with per-child thread limits one. The budget includes imports, input/output hashing, decoding, recovery, all integrals/checks and artifacts. Preserve failures and add complete cost to **1979.5974398998078 seconds**; T61's .9663960000034422-second qualification stays separate. No pilot, retry, SVD/eigensolver, fit, clipping, smoothing, adaptive rule or flow is allowed.

The only numerical inputs are the frozen T65 S256 audit bundle and the two existing T60 endpoint snapshots, anchored by their metadata/receipts. Decode seven audit arrays U_F,s_F,Vh_F,Lr,Lz,r,z and six reference arrays q,qr,qz,r,rc,z from each reference: exactly **three files/nineteen arrays**. Inspect only the saved leading singular pair; the S128 decomposition is not used to choose or alter the candidate. Validate all identities, array shapes, dtypes, finiteness and coordinates before use.

Recover coefficients in the **scaled midpoint basis** using the stored 2×2 triangular blocks:

    a_i = Lr_i^(-T) U_F[2i:2i+2,0] sqrt(s_F[0]),
    b_j = Lz_j^(-T) Vh_F[0,2j:2j+2] sqrt(s_F[0]).

Use explicit two-component back substitution, not a new decomposition. Require relative Frobenius recovery residuals <=1e-10 against the stored vectors. This yields u(r)=a_i0+a_i1(r-m_i)/h and v(z)=b_j0+b_j1(z-zc_j)/h. Do not interpret a_i1 or b_j1 as the old unscaled annular slopes. Their product has the SVD's fixed amplitude; no rescaling to enforce circulation or moments is allowed.

Orient the common sign by the exact-formula polynomial radial integral R0=integral(r u(r) dr): if R0<0, multiply both a and b by -1, which leaves the product unchanged. R0=0 is a failed candidate-definition check. Check both endpoints of every linear segment after orientation and record their actual minima. Nonnegative factor endpoints establish positivity of the piecewise-linear factors; negative values remain an explicit candidate limitation, even if tiny. Do not introduce a tolerance that turns a negative value into a positive witness, clip it away or change one factor's sign independently.

The candidate is defined on D8 with **explicit zero extension outside**. Report finite-D8 moments first; their full-space interpretation relies on this declared extension. Record r=8 and z=±8 boundary product magnitudes, jumps between adjacent factor pieces, and the extension's possible discontinuity. This is a broader sampled-field representation diagnostic, not a smooth fluid model or a Gaussian with unknown exterior tails.

## Exact polynomial evaluation and unchanged physical tests

Use exactly orders 3 and 2, five one-dimensional rule nodes. Evaluate both references and the same fixed candidate on the **S256 partition**: S128 coefficients are evaluated in their containing coarse cells, with their saved coarse annular centers and slopes. No interpolation/refit of S128 coefficients is permitted. Six node pairs per fine cell and two references give **1572864 reference node-cell samples**. The one candidate need only be evaluated once at the six fine-cell node pairs (**786432 candidate samples**) and reused for both comparisons. The model is bilinear within each fine cell; squared error times r³ has radial degree <=5 and axial degree <=2, so these rules integrate the same reconstructed-field metric exactly in real arithmetic.

Compute original reference statistics in those same loops and require agreement with the frozen metadata using rtol=3e-11 and atol=3e-14. Accumulate each nonnegative squared-difference numerator and independent reference norm. Require the S256 candidate score to agree with T65's S256 F relaxed error within 1e-10; this checks recovery/evaluation of the existing fit, not a new fit. Report S128's same-candidate score and require absolute score sensitivity <=.001 for a stable positive witness.

Compute candidate circulation, centroid, covariance, q-squared, axial impulse and physical-vorticity-squared integrals both by the shared quadrature and by separable polynomial factor integrals. With Rk=integral(r^(k+1)u dr), Zk=integral(z^k v dz), circulation is R0 Z0, means are R1/R0 and Z1/Z0, diagonal covariance is R2/R0-mean_r² and Z2/Z0-mean_z², and cross covariance is zero. The same factor moments give axial impulse πR2Z0. Squared-factor polynomial moments give both squared norms. Require the two routes to agree with rtol=3e-11 and atol=3e-14; nonpositive circulation or undefined ratios prevent a physical witness and must remain explicit.

Retain the original **field <=.10, absolute axial-centroid error <=.10, normalized covariance error <=.10** gates. Use the same original S256 initial covariance norm D0=1.0882203729522952 for both comparisons, copied from frozen T63 metadata. Report each reference's exact gate values. Report circulation/impulse differences as diagnostics, without silently adding conservation gates or refitting amplitude. No radial-centroid gate is introduced.

## Outcomes and claim limits

A complete numerically qualified run with nonnegative factor endpoints, positive circulation, all three original gates passing against both references and stable held-candidate sensitivity may report `broader_separable_endpoint_witness`. This is explicitly a zero-extended sampled-field witness in a larger family. It is neither a Gaussian witness nor a causal or conservation-preserving dynamics solution.

If any original physical gate or factor positivity fails, report that specific candidate miss. Nonpositive circulation or undefined moment ratios also prevent a witness; retain defined diagnostics, and encode undefined values as null with an explicit reason rather than nonfinite JSON numbers. Failure of held-candidate reference sensitivity is reference-sensitive/inconclusive and cannot produce a stable positive witness. None of these outcomes excludes another separable product, which could trade some field accuracy for moments. Numerical, identity or resource failure gives no candidate verdict. Preserve negative endpoints and undefined diagnostics without reclassifying them. No outcome justifies automatic marginal fitting, global Gaussian optimization, new trajectories or a new-method claim.

Save a scalar result, phase/work journal, full execution/resource receipt and one ignored recovered-factor NPZ with shapes/hashes. Account separately for all fixed quadrature samples, polynomial moment evaluations, triangular-block recovery, boundary/corner checks and output bytes. Review may inspect saved scalar records and hash arrays without numerical recomputation. Publish this finite outcome before choosing the next method question. The full TOG goal remains active and unachieved; historical outcomes, inactive art, main and deleted automation are preserved.
