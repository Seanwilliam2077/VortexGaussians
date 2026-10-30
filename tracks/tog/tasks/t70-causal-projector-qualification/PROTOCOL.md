# T70 — fixed current-state evaluator and first-step qualification

This is the numerical task selected by [T69](../t69-causal-mixture-startup/DECISION.md), using its unchanged [ordinary comparator](../t69-causal-mixture-startup/COMPARATOR.md). Freeze this protocol, worker/helpers, supervisor, runtime and nonarray inputs after static review and OS-only memory preflight. No scientific import probe, pilot, quadrature, algebra test, fit or retry is allowed outside the sole paid child.

## Scope, runtime and inputs

One child: <=120 seconds including imports, setup, all qualification, both fits, confirmation, hashing and output; observed working-set ceiling 512 MiB; >=1 GiB available physical memory before launch; observations every .25 seconds. Use the existing bundled Python 3.12.14/NumPy 2.3.5 with OMP/OpenBLAS/MKL/NumExpr threads set to one. No installation, new dataset, reference NPZ, scene or multi-step trajectory. An exclusive marker prevents a repeated invocation. Failure or timeout retains partial records and has no qualified projection.

Scientific scalar inputs are the exact original Gamma0=1.5 sqrt(2pi), geometry ((1,1,0),(1,1,0)), eta=0; its identical-positive-components representation eta=1/3; the fixed T69 fixture Gamma0, eta=1/3, geometries ((.9,1.05,-.2),(1.1,.85,.4)); and two independent step sizes 1/16,1/32 from q0. The fixture is researcher-authored evaluator data, not a scene, true solution or held-out application. T54's saved closed constants calibrate the initial operator. No T63/T68 fitted parameter, future moment or snapshot is loaded into prediction.

All arrays are generated inside the child from these scalar inputs/rules. No source NPZ/NPY is read or hashed, and no new raw array is saved. Read-only metadata references to historical records do not provide predictor data. The inherited T56/T57/T58/T59/T60/T63/T65/T66/T68 scientific-child subtotal is 1990.3707298998488 seconds; add the entire new child even on failure. It is not total project cost.

## Fixed rules and accuracy definitions

Construct exactly five Gauss-Legendre rules of orders 64,96,128,192,256 from their symmetric Jacobi matrices, one eigh each: **736 shared nodes**. Check finite ordered nodes in (-1,1), positive weights, symmetry and sum two within 1e-12. Numerical rule construction is paid.

Heat integration uses orders **64,128,256** with s=(x+1)/2,

    tau=(s/(1-s))², d tau/ds=2s/(1-s)³.

This maps the entire improper interval to (0,1); no finite heat cutoff is introduced. Order 128 alone supplies each search. Orders 64 and 256 are fixed controls, never an adaptive replacement. Rule agreement is numerical evidence, not a rigorous improper-integral error bound.

Direct spatial integration uses both (nr,nz)=(64,128) and (96,192) on both boxes D8=[0,8]x[-8,8] and D12=[0,12]x[-12,12]. These are four grids with 8192 or 18432 points each. Every grid is evaluated at all three heat orders for q0 and the anisotropic fixture: **24 field evaluations**. Direct weights are 2pi r³ dr dz. The all-space fitting objective and finite-box approximations remain distinct. D8/D12 differences and the analytic full-space Gaussian Gram comparisons are empirical tail controls; no exact tail certificate is claimed.

For a dimensional scalar/array comparison, require

    |a-b| <= 1e-10 + 1e-9 max(|a|,|b|).

This absolute term handles parity-zero cross terms. For dimensionless error scores, initial optimal translation coefficient and T54 relative derivative residual, require absolute difference <=1e-8. These tolerances are chosen before measurement to make numerical discrepancies much smaller than the original .10 physical screen and the order-h first-step perturbation; they do not prove future trajectory accuracy. No historical threshold changes.

## Operator and scalar controls, before search

At the 13 fixed (r,z) points

    (0,0),(0,.25),(0,1),(0,2),(.25,0),(.25,.5),(.5,-.5),
    (1,0),(1,1),(2,-1),(3,2),(4,0),(0,4),

compare each heat rule's q0 potential, radial/axial potential derivatives, velocity and F with an independent initial radial formula. With a=3/2, R=sqrt(r²+z²), I2=sqrt(pi/2)erf(R/sqrt(2))-R exp(-R²/2), use phi=a I2/R³ and phi'/R=a(R³exp(-R²/2)-3I2)/R^5 for R>.5. For 0<R<=.5 use the fixed 20-term Taylor series of those same expressions, without adaptive termination; at R=0 use phi=a/3 and phi'/R=-a/5. Independently check F=2z phi q0. Repeat heat evaluation at the same points with the identical-positive-components representation, requiring unchanged fields. These are **six additional field evaluations**, hence **30 total** before fitting. The exact radial oracle is evaluated once at 13 points.

On all 12 initial-state grids/rules, recover the H-optimal axial coefficient <F,zq0>/<zq0,zq0> and the direct residual using the unchanged T54 coefficient c=1.5*beta_best_over_g0. Compare with c and T54 E_best under 1e-8; require positive norms. This is an initial derivative calibration, not future motion validation.

Use three normalized probe components: (1,1,0) and the two fixture geometries. For each of the two physical states and every heat order, compute all ordered-pair one-dimensional F-cross integrals. Compare total and each ordered-pair value with independently formed direct field products on every spatial grid; also compare heat orders, spatial orders and D8/D12. This costs **18 cross calls /45 numerical ordered-pair integrals** before search. Check the summed ordered F_ij fields against the independently assembled -u dot grad q; check q norms and probe Gram products against analytic full-space expressions. The same state is used throughout; no fitting of the fixture occurs.

The inner scalar weight solver receives seven fixed algebra controls, not extra physical fits: identical g0 with targets +g0,-g0,0; the two distinct fixture geometries with targets g1, g2, (2g1+g2)/3 and g1-g2. Closed expected coefficient pairs are respectively (1,0),(0,0),(0,0),(1,0),(0,1),(2/3,1/3), and (max(0,(M11-M12)/M11),0). Equivalent identical-component fields are compared as fields/scales, with the specified endpoint tie. These exercise nonnegative amplitude, B=0, identical/constant and interior stationary cases. Expected coefficients are derived independently of the solver. Count every attempted candidate. No additional random cases or root trials.

## Two independent fixed searches and confirmation

Run the exact T69 bank/bounds/order/ties/refinement twice from the same q0, once per fixed h. Primary heat order is 128 for both; neither result initializes the other. Each search has at most 2280 proposals,1199 component bases and9121 weight/control attempts, including the unchanged-state control. Initial q0 actually has 45 bank components and1035 initial pairs. All starts/levels complete; no early success or parameter change after seeing a confirmation. Expose discarded/cached work, signed/degenerate scalar branches and procedural uncertainty rather than certifying a global optimum.

For each final positive selected tuple, recompute its two component cross products at all three heat orders, without refitting. Also compute cross products for the fixed T54 translated Gaussian at z=c*h at all three orders. These are **12 selected +6 translation cross calls**, all with one active current component. Compare contraction values across rules and with direct spatial products.

On every cached q0 grid/heat rule, form y=q0+hF, compute and pay for C=||y||², and directly integrate nonnegative squared residuals for the unchanged q0, the selected mixture and the fixed T54 translated Gaussian. Check the selected residual against C-J, and its improvement against J-J_control, with the dimensional tolerance above. Check primary/confirmation heat, spatial and domain score differences under 1e-8. Do not clip a negative subtraction residual or replace the direct primary estimate. The chosen full target norm is part of this confirmation route; an improvement difference alone could algebraically cancel it.

Use D12/(64,128)/heat128 as the recorded primary target-residual estimate; all other fixed routes are controls. The selected tuple is identical on every route. Compare the selected target residual with both ordinary controls descriptively, without adding a required performance win to numerical qualification. Check positive state, finite full-space moments and agreement of between-component/raw-second-moment formulas. Report circulation/impulse, whether components differ, and whether the target fit improves the unchanged/translation controls. These do not imply true Euler one-step error or the original t=1 task.

## Work and outcomes

Log every phase, five rule constructions, transformed heat nodes, state setup, scalar control, field/direct route, proposal/evaluation/cache/rejection, inner candidate, selected tuple and final predicate. Keep counters for all scalar/array exponential evaluations, heat ordered-pair integrals and their nodes, field component-node points, Gram terms, geometric proposals, weight attempts, direct node reductions, hashes and output. Component caching is per search; no free warm start from the other h. Repeated rule estimates count as new numerical work, not merely distinct mathematical integrals.

The two searches together have at most4560 proposals and2398 component bases. Since both current states reduce to one active q0 component, search uses at most2398 numerical scalar heat integrals at order128. Together with the fixed controls and readback, cross calls are at most2434, ordered-pair integrals at most2461, and heat-cross integrand points at most316352. The 30 direct/point field calls cover319566 spatial points,479349 current-component spatial points,71582784 component heat-node points and798915 ordered-pair spatial points. Helper bookkeeping and all direct model/probe samples are separately counted; these are not absorbed into the search budget. No scientific arrays are written.

Required qualification categories are frozen identity/runtime; rule/initial operator controls; full self/cross evaluator controls; independent scalar weight controls; both complete prescribed searches; unchanged selected direct confirmation and moments; complete work accounting; and final identity preservation. A fully qualified result is only an ordinary current-state evaluator and two first-step projections. A valid zero/no-positive-state search is a separately retained inconclusive startup, not family exclusion. Any global numerical, identity or resource failure yields no qualified startup even if an intermediate tuple looked useful. Publish the retained result and costs before deciding the next task. Historical outcomes, art, main and the deleted automation remain unchanged; no TOG contribution is established by this qualification.
