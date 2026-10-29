# T49 — bounded impulse/magnetization source screen

30 October 2026. Parent `0b327f19423b835927c335b0fb8d396e22c652d3`. This screen follows [SCOPE.md](SCOPE.md). The source analyst received the candidate curl-Gaussian representation and evolution question before searching. It is a targeted comparison, not a blind novelty assessment or exhaustive historical survey.

## Exact query and access ledger

The following queries were issued separately, in this order:

1. `magnetization impulse formulation Navier Stokes velocity projection covector Gaussian vortex particles`
2. `"impulse" "Gaussian" "magnetization" vortex particle`

After query 1, documents 1 and 2 below were opened together. After query 2, document 3, already identified by query 1, was opened. No other result or snippet is used for a technical claim. The second query did not supply an additional acquired primary document matching the particular Gaussian parameterization.

| Order / primary item | Exact requested URL | Observed access and inspected material |
|---|---|---|
| 1. Pooley, magnetization-variable formulation | [Warwick author manuscript](https://wrap.warwick.ac.uk/97331/13/WRAP-model-Navier%E2%80%93Stokes-equations-magnetization-variables-Pooley-2017.pdf) | PDF extraction succeeded; 15 pages / 1,226 extracted lines reported. Returned lines 0–466 were inspected: bibliography on the cover, formulation, classical equivalence, and part of the weak/prescribed-velocity discussion. The remaining pages were not read. |
| 2. _Impulse Fluid Simulation_ | [Author-hosted paper](https://sking8.github.io/assets/paper/impulse.pdf) | Tool returned error 400: content length too large, 24,089,500 bytes. No paper body was acquired. This is a tool access limit, not evidence of an invalid paper, an origin-server restriction, or a formulation failure. No retry or alternate copy was requested. |
| 3. Summers and Chorin, impulse-based vorticity creation | [Primary PNAS article in PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC39876/) | HTML succeeded, 143 extracted lines. Used bibliographic information at lines 33–61 and abstract at lines 62–64. The PDF and scanned article pages were not opened. |

Final accounting: **2 queries / 2 allowed; 3 primary documents / 4 allowed; 2 successful document opens and 1 failed open**. The failed paper counts toward the document budget even though its body was unavailable. Acquisition stopped before the fourth item because the general ordinary formulation and a particle-method/gauge precedent were already established. No citation chase, further search, local source download, code acquisition, installation, asset, numerical calculation or simulation occurred. The reported oversized response length is a tool diagnostic, not measured transferred bytes.

## Attributable source summaries

Each source summary, including its comparison limits, is under 140 words.

**1. Benjamin C. Pooley, _On a Model for the Navier–Stokes Equations Using Magnetization Variables_, Journal of Differential Equations 264 (2018), 5180–5196.** Equations (3–4) give `w_t+(u·∇)w+(∇u)^T w−Δw=0` and `u=P w`; viscosity is set to one. Section 2 proves classical equivalence using `u=w−∇q` and treats prescribed-velocity evolution separately. Its weak-solution results have stated regularity and periodic-domain assumptions. Thus projected velocity and covector transport/diffusion are established ordinary formulation components. The paper's later global well-posedness model changes a nonlinear term; that theorem must not be transferred to Navier–Stokes. **Limit:** the inspected material does not supply T49's finite-dimensional `a G_C` closure, a localized-particle evaluator or performance evidence. [Primary manuscript](https://wrap.warwick.ac.uk/97331/13/WRAP-model-Navier%E2%80%93Stokes-equations-magnetization-variables-Pooley-2017.pdf).

**2. _Impulse Fluid Simulation_.** The selected author-hosted PDF exceeded the tool's content-size limit. No equations, solver details, empirical claims, or Gaussian-closure assertions from this paper are used. The unacquired paper is recorded solely to disclose the failed acquisition and budget consumption. [Attempted primary document](https://sking8.github.io/assets/paper/impulse.pdf).

**3. D. M. Summers and A. J. Chorin, _Numerical Vorticity Creation Based on Impulse Conservation_, PNAS 93 (1996), 1881–1885.** The primary abstract describes impulse elements at walls followed by conversion to solenoidal vortex loops for no-slip boundary treatment. It explicitly notes that gauge freedom makes the algorithm nonunique and that the numerically optimal gauge remains undetermined in that work. **Match:** impulse-based particle construction and gauge-dependent numerical choices have concrete prior treatment. **Limit:** this is abstract-only evidence, not a derivation of localized anisotropic Gaussian impulses, their affine/viscous closure, or present-day performance. Its historical unresolved-gauge statement is not a claim that no later work resolved particular gauge choices. [Primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC39876/).

## Consequence for the candidate comparison

From the acquired relation `u=w−∇q`, the local inference `curl u=curl w` follows wherever the stated differentiability permits commuting derivatives. This connects the general formulation to T49's declared `omega=curl(m), u=P m`; it does **not** make every vector potential, gauge choice, boundary condition or finite particle family equivalent.

The particular `m=a G_C(x−mu)` parameter equations under a prescribed affine velocity remain the project's local algebraic specialization. The source screen neither attributes that exact specialization to an unread paper nor treats its absence from this small sample as novelty. Likewise, prescribed affine closure must remain separate from self-consistent evolution, which also requires reconstruction of the inducing velocity and its derivatives. The ordinary formulation is sufficiently matched to reject a broad claim of inventing curl-based impulse representation or covector diffusion. Whether the particular state contract enables a useful method still needs evidence beyond closure; this screen selects no implementation or numerical queue.
