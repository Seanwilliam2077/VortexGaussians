# T78 static review and response

2 November 2026. Neither reviewer ran scientific code, acquired further sources or changed files. No new paper score was assigned.

## Mathematical analyst

The analyst participated in earlier T74–T76 reasoning and review. After an initial conditional derivation from repository notes, Root supplied the pinned source paths. The analyst then read the P2G implementation, kernel and configuration and confirmed the normalization/boundary semantics and rank27 proof. It identified the ordinary 108-statistic mixed representation, preventing a misleading claim that 162 or 351 is necessary.

The analyst also clarified that the final matrix addition is literally in the stencil even though the expensive products and Hessian contraction are outside. Compiler motion is unverified. Its initial claim about half-cell occupancy was explicitly a configuration inference; Root subsequently read init_conditions.py's actual initialization and verified the stated placement. Source-level initialization is still not a later-time occupancy measurement.

## Separate research reviewer

This agent had no role in T76 implementation or writing T78's derivation. It first assessed the finite task against T77's decision, then read the four acquired sources and the drafted operator/algebra documents. This is an internal static review in the same collaboration environment, not blind external review or independent execution.

The reviewer reports no mathematical blocker. The operator retains staggered locations, kernel, all masks and the exact D>1e-5 branch. The rank construction is valid for arbitrary fixed-position inputs, while imposing no runtime or total-memory lower bound. It explicitly allows full-rank structured acceleration and ordinary batching. It confirms the sufficient counts 351/162 and the added108 hybrid, with no minimality or speed claim.

It recommends closing only the two proposed direct arguments: moving already externalized major contractions out of the stencil, and assuming that many particles imply exact low rank. It does not reject every transfer optimization or system contribution. Unmatched source/paper timing cases, unmeasured occupancy and the missing primary GPU-MPM comparison prevent a performance conclusion.

## Root response

Accept the corrections. OPERATOR.md distinguishes the remaining literal addition from major contractions. ANALYSIS.md includes the108 construction and limits its theorem to exact linear intermediate dimension. No benchmark is started to turn ordinary rearrangement into a contribution claim. Keep the actual source audit, operator contract and algebra as reusable evidence; preserve T76 and all historical gates/ratings.
