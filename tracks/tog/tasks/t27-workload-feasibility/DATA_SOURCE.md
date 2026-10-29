# T27 — one observation-source metadata route

29 October 2026. Only the official Mip-NeRF360 route linked by the fixed Vol3DGS README was inspected. No data member, image, archive directory, learned model or alternative dataset was acquired.

The [official page](https://jonbarron.info/mipnerf360/) returned37 extracted lines with Dataset Pt.1 and Pt.2 links and a code link. The extraction did not expose the full archive href strings. The disclosed [transport clarification](METADATA_CLARIFICATION.md), made before additional requests, used the optional description-page slot for a bounded HTML read of the SAME page. That returned11,746 bytes and resolved the first archive link to http://storage.googleapis.com/gresearch/refraw360/360_v2.zip. No new source route or search was added.

One HEAD request to that exact observed URL returned200 and application/zip, with Content-Length and x-goog-stored-content-length both12,535,427,936 bytes. Last-Modified is28 March2022; the receipt records the object's generation and response headers. **Zero archive-body bytes were read.** This establishes the advertised compressed size and availability of that endpoint at capture, not integrity or permission of uninspected contents. The actual link uses HTTP; no transport-security or content-authenticity guarantee is inferred from these headers.

The acquired page text/HTML supplies no explicit dataset-license or permission statement identified in this inspection. The code link was not followed. Public author-provided download access is recorded as provenance and intended benchmark distribution, but no legal conclusion or redistribution grant is invented. The exact data-use terms remain unresolved by this budget.

The archive's members, chosen scene availability, extracted size, image/camera counts, resolution, split, camera validity and any included license files remain uninspected. The Vol3DGS script names Mip-NeRF360 scenes, but that script does not authenticate which members occur in this archive. We did not fetch the ZIP directory to fill these gaps.

All three metadata calls are spent: web extraction, same-page HTML retrieval and HEAD. The original protocol/freeze are unchanged; the additional transport note explicitly distinguishes the post-initial-access adjustment. No extra permission page was visited and no dataset switch, request retry, authorization flow or dataset-body download occurred.

**Result:** a real official observation source and compressed extent are identified, but this is not an acquired or fully qualified training workload. Data terms, selected-member extent and extraction/storage limits must be resolved in a separately justified step before a concrete acquisition/training protocol. A permissions gap in this limited evidence is not proof that research use is prohibited. Together with local prerequisite gaps, it prevents declaring this task's execution gate satisfied.
