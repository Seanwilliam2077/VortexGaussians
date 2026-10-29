# T44 mathematical/adversarial review

30 October 2026. **CLEAR within the declared analytical scope; the next remainder question remains unproved.** This review read only T44 `SCOPE.md`, `ANALYSIS.md`, `NEXT_EVIDENCE.md`, `README.md` and `SOURCES.md`. The reviewer had already checked the U3/U2 formulas and related caveats in preliminary consultation, so this is not a blind independent derivation. No external source was reacquired, scientific code executed, numerical example evaluated or historical result changed. The source-screen counts and attribution are read from the supplied source record, not independently audited network receipts.

## Cancellation and information boundary

The local expansion has the correct signs and factors. Writing the centered first parameter operator as `-u_i:grad + V_i:grad^2/2`, half its weighted square supplies the mean-mean, mean-covariance and covariance-covariance terms. The between-mean covariance in the merged Gaussian cancels the first of these, leaving `-sum w_i(u_i tensor V_i):grad^3/2` and `sum w_i(V_i tensor V_i):grad^4/8`. Parameter second derivatives otherwise average identically. Smooth parameters and a uniform positive covariance floor justify the stated local density and L2-norm interpretation; this is not a finite-step certificate.

The rotating example has `u_i=(z_i-z_bar)e_x` and `V_i=2(b_i-b_bar)e_x e_x^T`, yielding the stated covariance/variance coefficients. The opposite-cross-covariance pair has a nonzero second-order density error. Equal isotropic component covariances instead give the third-central-moment term; the symmetric depth pair removes it and has fourth-order coefficient `-a^4/12`. Squared L2 errors double the nonzero norm orders. The exact null-direction condition `Q n0=0` also correctly factors Q through P0, without implying an interval guarantee from a single-time derivative test.

The two positive-mixture families have the same fixed retained moments and initial projected Gaussian. Their side-view central optical-depth difference is the stated positive square divided by `4 pi s epsilon`, including the factor `kappa M`. It diverges while the retained state stays fixed. This concerns pointwise optical depth: the constant-white/black-background color limits are zero and one, not unbounded RGB, and no finite-pixel or perceptual conclusion follows.

## Ordinary metrics and reuse

U3 is the weighted component-to-merge KL sum; moment matching cancels its trace, mean and dimension terms. Natural-log Pinsker gives the displayed `sqrt(2 U3)` L1 constant, and probability L1 is at most two. Shared mass-preserving affine pushforward preserves U3; componentwise projection contracts KL, giving `U2<=U3`. Exponential transmittance is 1-Lipschitz for nonnegative optical depth. The physical-area, finite-region and pixel-average qualifications are correct. U2 is an upper bound, not exact mixture KL; arbitrary colored emission is not certified.

The Gaussian-product overlap identity and expanded squared L2 metric are correct. The cost statements distinguish O(k) preparation/projected bounds, general O(k^2) overlap terms, and fixed-cost binary groups. The ordinary retained scalar therefore remains a fair competitor. No useful tightness, numerical stability or speed was measured.

## Status of NEXT_EVIDENCE

The proposed finite-step parameter identities are consistent: the merged depth variance is `d_bar+v_z`; the cross blocks are `b_bar`; hence the displayed xi/Delta and both weighted cancellation identities follow. If `m=min_i lambda_min(Sigma_i)>0`, both projected endpoints are bounded below by `m lambda_min(Q Q^T) I`, as is their convex covariance segment. The parameter differential operator has the stated sign. A third parameter-order remainder requires spatial derivatives through order six.

These checks do **not** prove the complete retained-statistic remainder bound, its constants, useful regime or distinguishable cost/accuracy advantage. NEXT explicitly assigns those questions to one bounded algebra-only task, with no automatic implementation, source expansion, scene or numerical queue. Its comparison, invalidation and unmerging-storage obligations preserve the scope rather than claiming a validated guard.

Reviewed SHA256 identities:

```text
SCOPE.md
ca9580c517aa82c424f59e5f293d59797ae8b871657d39c263f049bffb24dc74
ANALYSIS.md
45e848a062ebc4b3e8d7c05b81958a4930a8daf97e83303a58793816ec51c4ce
NEXT_EVIDENCE.md
873b072c445ab2f1fc2bd710ad8ab84c8d0603996637aa4dfd89686eed3ab82b
README.md
26fa7798cc71f85bdc2033519e6e83fcf430d662450f845362ce4ab0b416686c
SOURCES.md
6caa87f091d343647bdb8200c3af6abb6ca15d4432c7fe649295496f01ae59bc
```
