# T48 — bounded primary-source screen

30 October 2026. This is a source-limited comparison for the family fixed in [SCOPE.md](SCOPE.md), not an independent novelty determination. The source analyst received the proposed family before searching. No mathematical, rendering, simulation, or timing experiment was run.

## Query and access ledger

Both permitted queries were submitted together through the web search tool, exactly as follows:

1. `deforming ellipsoidal Gaussian vortex blobs three dimensional Biot Savart velocity`
2. `anisotropic Gaussian vortex particles solenoidal Piola transformation`

The four selected primary items below were then opened once each, together in one access call. The budget is exhausted: **2 queries / 2 allowed; 4 primary items / 4 allowed; 2 successful opens and 2 failed opens**. The substantive publisher-indexed abstract for item 4 counts as the same item despite its subsequent access failure. No other search-result snippet is used for a technical claim. There was no alternate-route retry, citation chase, additional page request, code acquisition, installation, or asset download.

| Item | Exact primary URL | Observed access and inspected scope |
|---|---|---|
| 1 | [Rossi author manuscript, institutional PDF](https://udspace.udel.edu/server/api/core/bitstreams/afa26722-ec53-4381-aba6-3f1d8f1d4b99/content) | Successful PDF text extraction; tool reports 26 pages / 2,567 lines. Inspected returned lines 0–321, spanning pages 0–6, including abstract, model definition and start of evolution equations. This does not mean all pages were read. |
| 2 | [Rossi 2005 repository record](https://udspace.udel.edu/items/42183c02-3e81-4ce9-a683-ab19e0fa6268) | Successful HTML, 119 extracted lines. Used title/author/date and abstract at lines 76–97. Its linked PDF was **not** opened. |
| 3 | [Oxford report PDF route](https://ora.ox.ac.uk/objects/uuid%3A3da840e3-1e4a-4cf7-9dcb-501a8aa4e54f/files/ma5a79f99e85ddf9a71ebcef0d40f3be5) | Failed: HTTP 403 Forbidden. Search identified the route as “Report no. 08/15”; no report body was acquired. No alternative route was tried. |
| 4 | [Highly anisotropic vorticity blobs, publisher record](https://www.sciencedirect.com/science/article/abs/pii/S0021999196901382) | Failed open: HTTP 403 Forbidden. Only the primary publisher's indexed abstract returned by search is used below. No full article or authorship record was acquired. |

Successful tool extraction is not a measured HTTP transfer size or a locally archived PDF. No response-byte, latency, or performance claim is made.

## Source-limited comparisons

Each numbered comparison below is under 140 words, including its match/limit assessment.

**1. Louis F. Rossi, _High Order Vortex Methods with Deforming Elliptical Gaussian Blobs 1: Derivation and Validation_.** The manuscript bears a 2001 author copyright; publication venue/year was not independently established. It represents **two-dimensional scalar vorticity** using elliptical Gaussians whose position, orientation, axes and width evolve under local linearized flow and viscosity. The abstract specifies fourth-order asymptotic Biot–Savart velocity/derivative evaluation and adaptive refinement. The manuscript also distinguishes local linearized closure from general Navier–Stokes self-similarity (lines 24–26, 171–176, 224–278). **Match:** deforming Gaussian vortex representation, evolution and reconstruction costs are concrete prior capabilities. **Limit:** this inspected model does not establish the T48 three-dimensional vector projector, its exact Piola closure, or an exact evaluator for that family. [Primary manuscript](https://udspace.udel.edu/server/api/core/bitstreams/afa26722-ec53-4381-aba6-3f1d8f1d4b99/content).

**2. Louis F. Rossi, _Evaluation of the Biot-Savart Integral for Deformable Elliptical Gaussian Vortex Elements_ (2005 repository record).** The abstract describes direct-interaction streamfunction perturbation in `(a−1)/(a+1)`, with `a²` the aspect ratio. It separately discusses far-field multipole evaluation, the noncompact basis's computational length scale, and a finest-mesh restriction for a specified tolerance. **Match:** anisotropic-kernel reconstruction and fast summation already require explicit approximation/cost contracts. **Limit:** this is **abstract-only** evidence. No expansion coefficients, error theorem, implementation, exact T48 correspondence or measured advantage was obtained. [Primary record](https://udspace.udel.edu/items/42183c02-3e81-4ce9-a683-ab19e0fa6268).

**3. Oxford “Report no. 08/15” search result.** The primary report route failed with 403. No technical result, authorship, complete bibliographic identity or reconstruction algorithm from this report is used. It contributes an **access limitation**, not positive or negative evidence about T48. [Failed primary route](https://ora.ox.ac.uk/objects/uuid%3A3da840e3-1e4a-4cf7-9dcb-501a8aa4e54f/files/ma5a79f99e85ddf9a71ebcef0d40f3be5).

**4. _A Method for Determining the Velocity Induced by Highly Anisotropic Vorticity Blobs_.** The publisher-indexed abstract, bearing a 1996 Academic Press copyright, describes an asymptotic induced-velocity approximation using a small blob aspect ratio and explicitly applies it to anisotropic Gaussian blobs in **two and three dimensions**. **Match:** a broad claim of first evaluating three-dimensional anisotropic Gaussian vortex velocity is unsupported. **Limit:** the direct publisher page failed; this is indexed-abstract evidence only. It does not identify the T48 exact projector, prove its affine closure, or give us a usable exact velocity/Jacobian evaluator. Reported numerical tests and performance comparisons are not imported into this project's evidence. [Primary publisher record](https://www.sciencedirect.com/science/article/abs/pii/S0021999196901382).

## Consequence for this screen

The useful comparison is representation **plus** deformation assumptions **plus** reconstruction work, rather than parameter count alone. Sources 1, 2 and 4 already provide concrete deforming or anisotropic Gaussian vortex/evaluation precedents. The particular T48 Fourier projector was not matched by the inspected material; that limited observation cannot establish a literature gap. Exact-family equivalence, a reproducible evaluator, self-consistent evolution, practical error/cost advantage and a suitable task remain separate questions. The current evidence warrants an ordinary-method comparison and explicit source limits, not a novelty or speed claim and not an automatic numerical follow-up.
