# T23 independent model and access review

29 October 2026. Reviewer: `volume_screen`. **CLEAR for closing this finite source audit; the evidence does not qualify preparation of an asset measurement.** No blocking inconsistency remains in the reviewed documents.

This review read the frozen protocol/allocation, semantic note, both paper notes, both finalized paper ledgers and repository ledger. It checked local receipt sizes/hashes. It performed no external access, paper reacquisition, code import, numerical evaluation, new sample, asset acquisition or source-file modification. The conditional algebra below was checked symbolically. Source-specific paper observations rely on the bounded inspections documented by the source reviewers; this is not a second independent full-paper or implementation audit.

## Conditional mathematical mapping

For a positive-definite Q and a valid nonzero direction d, write v=o-m, q=d^T Q d and r=d^T Q v. Then q>0 and

```text
(v+t*d)^T Q (v+t*d) = q*(t+r/q)^2 + h,
h = v^T Q v - r^2/q >= 0.
```

The last inequality follows from Cauchy–Schwarz in the Q inner product. Thus the note's mu=-r/q, sd=1/sqrt(q), and w=kappa*exp(-h/2)*sqrt(2*pi/q) correctly represent the spatial field restricted to the ray as w times a normalized one-dimensional Gaussian. A finite interval uses the corresponding CDF difference; zero kappa gives zero mass.

Optical depth, however, integrates against world distance. For x(t)=o+t*d, the parameter-space extinction is ||d||*sigma(o+t*d), so its normalized Gaussian mass is **||d|| times the displayed w** when d is nonunit. The note explicitly supplies this factor. Ray parameter units, interval endpoints and source term must all follow the same convention. This is a conditional identity for actual nonnegative extinction, not a conversion from an unverified stored alpha field. Exact h>=0 does not guarantee a cancellation-prone floating-point evaluation remains nonnegative.

The finite-color statement is also correct: with nonnegative optical masses and a finite constant component color along each ray, first-arrival expectations and their signed differences remain defined for arbitrary finite RGB values. Actual per-channel extrema can replace the [0,1] development range in the global convex-mixture bound. Background cancels from the compared errors when its common transmission is unchanged. This does not validate release coefficients, color-space units, spatial SH evaluation, an identical numerical tolerance scale, or clipping of colors. It does not extend the target automatically to scattering or independently parameterized emission.

## Access, budgets and evidence level

The ledgers account for two named paper acquisition attempts: one successful Vol3DGS v3 HTML acquisition and one tool-reported Hybrid publisher 403. The two additional Vol3DGS reads are paging of that already acquired document, with displayed and inspected extractor ranges recorded. No PDF fallback or PDF page was used. There were no searches, mirrors or added paper families. The unused conditional fallback allowance is not a requirement to guess an endpoint.

The official repository revision request used one of four metadata-request slots and returned HTTP 403/rate-limit failure. No fixed commit was obtained. The ledgers consequently record zero code files, zero inspected implementation lines, zero asset-metadata requests and zero asset downloads, within the six-file/1,800-line and two-asset-endpoint maxima. Stopping at the prerequisite failure is consistent with the protocol. It is not evidence that the repository or compatible assets do not exist.

The three local Vol3DGS receipts total 83,649 bytes and match their declared hashes. They are saved tool-response representations, not measured origin-body/network byte counts, a complete offline paper, or checkpoint metadata. The successful paper-level read cannot supply the missing pinned release semantics, camera carrier, complete support, background/domain and asset permissions. Hybrid's inherited historical description is appropriately separated from this round's zero acquired article text.

The final Vol3DGS assessment now distinguishes the observed domain difference from unresolved color/support semantics. This publication clarification resolves the earlier wording that called all three mismatches; it neither changes the scientific outcome nor adds source access. The protocol's preparation wording is the frozen pre-access contract, while these ledgers record the completed source audit; no numerical experiment was executed.

## Decision and review limits

The elementary density-to-ray route is mathematically possible under explicit conditions. Those conditions have not been verified against a pinned implementation and official asset carrier. Therefore the binding prerequisite for preparing an applicability measurement is unmet. The notes correctly retain concrete missing fields instead of preparing a numerical protocol, choosing a replacement scene, retrying a source or interpreting access failure as novelty.

T22 remains one local development-ray cost observation with modest complete-workload benefit. This source audit does not measure useful-ray frequency, provide a same-model executable comparator, resolve full prior-method coverage, establish demand, or establish a TOG contribution. Closing T23 under its stop rule does not close the broader research objective.

## Reviewed identities

Paths are relative to `tracks/tog/tasks/t23-model-workload-audit/`. These are the final note/ledger identities after the publication wording clarification.

| File | SHA256 |
| --- | --- |
| `PROTOCOL.md` | `a9388576aab275c188dc8343900d7caecdae93a0eea76a39e2bfdaab2b55f1b4` |
| `freeze.json` | `74ef4bbbd88b5305b94e2261e18f296a946870046dc602495111487cea58a4f9` |
| `SEMANTICS.md` | `79706cbd90fd31c24ef75965a0217cba4e99928841c66120729988ef1141999f` |
| `VOL3DGS_PAPER.md` | `7c82eebe0dee95ef11bd51f0211266dc0ef55132f4f0b1074db1eca3ddaaf76b` |
| `HYBRID_PAPER.md` | `e91f6b6872cf262ca6c8cdfa81d66b9d85bec64a7804e569333a5adabaca5ff0` |
| `repository-access.json` | `1f75359d03d0dfd0415959c737c9a756b73386b7157ba4372a50f1f10f8e329c` |
| `vol3dgs-paper-access.json` | `71b1e7607e6c9228efc6382a11a27ddecec8d7aaaf8d3468922e1a98b70801cc` |
| `hybrid-paper-access.json` | `e8a8d6ca95d041632424b4764310a3d2e705f7451608ad148d299052e4a8b17f` |

Retained local receipts in `acquired/vol3dgs-paper/`:

| File | Bytes | SHA256 |
| --- | ---: | --- |
| `01-html.web.txt` | 28,721 | `dfa8fd62e37baefadc41937f3be60c055c212892e0fa30db858ba7eb025a406d` |
| `02-same-document-page.web.txt` | 27,364 | `cb0c231046d355456a5fcfd2f2282de2a267596274f90fd5ace9a84c09640b08` |
| `03-same-document-page.web.txt` | 27,564 | `e95cb2ea06656f521d509f0a7e5e6a35bcd0bdfce467623d814fa7f445fe3a49` |
