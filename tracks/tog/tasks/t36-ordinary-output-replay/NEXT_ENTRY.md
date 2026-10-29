# Next entry — does this actual frame require expensive ordinary integration?

T36 finally supplies a qualified saved RGB image, but its visible content is a narrow particle column with 2.006% nontrivial coverage. The scalar GL implementation scans all retained sources at every node of source-derived intervals: typically O(n² sum of orders), with repeated CDF endpoint work and Python allocations. A compiled/SIMD implementation of the same algorithm is a necessary stronger comparator before claiming a method speedup. First, however, answer the cheaper prerequisite: can ordinary approximations already meet the original output tolerance on this exact frame?

This question adds workload evidence. Stable mean-depth whole-primitive composition was already evaluated on T17's 48 synthetic rays and used by T21/T22. Optical-mass-weighted color was used for the common-profile exact case. Neither formula is proposed as new; a repeated two-Gaussian discrepancy would add nothing. The unmeasured fact is their complete-frame applicability and error location on this acquired carrier. Do not change the scene to force a failure.

## One bounded development screen

Prepare, review and freeze one new task before numerical execution. Reuse only the original T31 frame90/front, 270 isotropic primitives, full 256×192 camera, HDR colors, black background, finite ray clips and 0.001+1e-10 RGB/alpha gate. Use the unchanged ordinary BVH/projection and original 0.00025 pruning budget. Each arm independently pays its own tree, ray preparation, projection, stable finite Gaussian masses and output work; no old per-pixel result or reference endpoint is an input to either delivery. Source identities and complete costs must be recorded. No source search, installation, asset, simulation, field edit, new view, GPU work or reference computation.

For retained source i, let m_i be its finite optical mass and c_i its color; tau=sum_i m_i and A=-expm1(-tau). The two fixed ordinary outputs are:

1. **Whole-primitive mean-depth composition.** Sort by projected Gaussian mean depth, breaking ties by original source ID. Return sum_i c_i*(-expm1(-m_i))*exp(-sum_{j<i}m_j), with alpha A. Do not add a pair certificate, adaptive split, clipping-dependent reordering rule, oracle or GL fallback.
2. **Optical-mass mixture.** Return A*sum_i(m_i*c_i)/tau with alpha A; return zero at tau=0. This is exact for common profiles but generally an approximation. Do not present it as the continuous emission integral for arbitrary mixtures.

Both arms cover every pixel. Output inaccuracy is an observation, so continue the fixed schedule to obtain its full extent. An exception, nonfinite/invalid output, source mismatch, malformed persistence, deadline or byte cap stops the invocation and preserves partial evidence. Use explicit unique fields and the now-established saved-value round-trip discipline; necessary pre-freeze structural tests use literal data only, never a scientific pilot. Do not turn this into another general persistence framework.

Allow one scientific invocation, **60 seconds computation, 90 seconds outer wait plus 10 seconds cleanup**, and **16 MiB new raw numerical output** plus small fixed images/receipts. These simple methods replace millions of GL nodes with finite-mass evaluation and linear composition, while paying two preparations. This is a finite feasibility allowance, not an assumption that they finish. No retry, budget escalation, fallback, parameter search or post-result arm selection. The next task must freeze its concrete implementation and evidence schema; this entry alone is not an executable protocol.

## Use the saved intervals without manufacturing truth

Comparison happens outside delivery, using T35's intact lower/upper RGB and full alpha. Ignore its overwritten ordinary blue. Preserve T35's failed classification and the complete reference identity. On each channel, for output x and saved interval [L,U], compute:

- d_max=max(abs(x-L),abs(x-U)); the output qualifies when every channel d_max<=epsilon and alpha passes.
- d_min=max(L-x,0,x-U); a channel with d_min>epsilon demonstrates failure relative to the retained reference enclosure.
- Otherwise it is unresolved. Do not treat interval midpoints as truth, label unresolved as failed, or refine the reference to get a sharper answer.

These are the existing binary64 reference qualifications, not newly certified real-arithmetic intervals. Comparison cannot alter either output. T36 RGB can be shown alongside, but its approximation error is retained and it is not promoted to exact truth. Preserve all per-pixel outputs/classifications, full-frame and original 986-pixel foreground counts, error locations and extent, original-size fixed-exposure displays, preparation/output/evaluation/publication costs and historical paid costs. If reporting per-pixel best-of-two coverage, label it an offline oracle upper bound; it is not an implementable method without a separate selector.

## Decision and stop

If either ordinary arm qualifies on the entire frame, this carrier gives no demonstrated need for expensive continuous-color integration at the fixed tolerance. Close new ordering-certificate development on this carrier; do not rescue it with opacity/color/camera edits or another favorable toy. A wider task would need independent justification.

If neither arm qualifies but there are only unresolved records, retain that uncertainty and stop this screen; no automatic reference refinement. If both have definite failures, record their actual foreground extent and displayed consequences. That establishes only limitations of two cheap approximations. It does not prove a difficult useful task, a failure of optimized ordinary integration, a need for the historical pair bound or a TOG contribution. Review that evidence before spending on one compiled/SIMD ordinary GL comparison; do not jump from approximation error to a new method.

No further five-view batch, new scene, method candidate or compiled implementation is prepared here. The research goal remains active. The point of the next task is to remove an inexpensive explanation of the observed scalar cost, not to fill a run queue.
