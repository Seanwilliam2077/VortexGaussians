# T50 — acquisition and reader accounting

This record audits the single new T50 acquisition authorized by T49 NEXT_EVIDENCE and T50 SCOPE. It does not read or assess the paper's body, equations, methods or scientific claims. T49's oversized web-tool response remains a failed historical acquisition; this local attempt does not rewrite it.

## Scope of the independent audit

The auditor read only T49 NEXT_EVIDENCE, T50 SCOPE, local/acquire.py, local/acquisition-started.json and local/acquisition.json. It independently obtained the downloaded file's filesystem size and SHA-256 without opening it in a PDF reader, extracting text or viewing pages. It made no network request, dependency probe, installation or scientific execution. This audit consumed zero paper-excerpt words and zero rendered-page views from the shared 18,000-word/six-page budget; root maintains the total ledger across other reading work.

## Observed acquisition identity

| Item | Saved record and audit result |
| --- | --- |
| Requested and final URL | `https://sking8.github.io/assets/paper/impulse.pdf` |
| Start time | `2026-10-29T22:13:54.199412+00:00` |
| Outcome | `acquired_pdf` |
| curl/process status | Exit 0; HTTP 200; empty stderr; no reported error |
| Content type | `application/pdf` |
| Redirects | 0 |
| Downloaded and saved size | 24,089,500 bytes |
| Independent SHA-256 | `b63bc95823d764f61d9f80caedd17f57a9bbcbba624294f19cb94780d28b55df` |
| curl transfer time | 4.049478 seconds |
| Helper elapsed time | 4.108999999938533 seconds, approximately 4.109 seconds |
| Recorded finish time | `2026-10-29T22:13:58.312715+00:00` |

The independent file hash and size match both the acquisition receipt and root's reported identity. The PDF remains in the ignored task-local directory. No source bytes or full extraction are included in this document.

## Budget and failure-handling contract

The helper creates its start record exclusively before invoking curl. There is one matching recorded acquisition, one subprocess invocation in the script, and no retry loop or alternate-source path. An existing start record prevents the same helper from silently starting another attempt in that directory; this is an acquisition-record audit, not a forensic proof of all possible network activity outside the helper.

The configured limits are a 32 MiB response body, three redirects, HTTPS for the initial URL and all redirects, zero retries, a 15-second connection timeout, a 55-second curl transfer limit and a 58-second subprocess timeout. Before accepting the file, the helper checks elapsed time below 60 seconds, successful curl status, HTTP 200, final HTTPS URL, redirect count, nonempty body within 33,554,432 bytes, agreement with curl's byte count, and the `%PDF-` prefix. Acceptance renames the partial file; exceptions in the guarded acquisition path record `stopped_no_retry` rather than launching another request.

The observed attempt was below the stated byte and time budgets and followed the specified HTTPS route without redirects. The 60-second check is not a continuous hard watchdog covering every disk read, hash, rename and final receipt write. The recorded helper elapsed time is captured before the final receipt write and stdout print. These implementation limits do not turn the observed 4.109-second acquisition into an overrun, but prevent a universal hard-deadline claim.

The signature result is the helper's actual `startswith(b'%PDF-')` check on the bytes whose hash was recorded. The independent audit verified the same file identity, not a second PDF parser or independent header interpretation. A valid prefix, successful HTTP transfer and byte-count consistency are not complete structural validation of a PDF.

## Reader/dependency facts reported by root

The following are root-observed environment facts supplied to this auditor; the auditor did not repeat the probes:

- The `gs-sph-3d` Python environment had no `fitz`, `pypdf` or `pdfplumber`.
- The bundled runtime located through `load_workspace_dependencies` had `pypdf` and `pdfplumber`; `fitz` was unavailable there.
- Poppler's `pdftoppm` and `pdfinfo` were installed.
- Local curl was version 8.21.0; its local help confirmed the relevant cap and protocol flags.
- No package or tool was installed for this task.
- Bundled `pypdf` indexed twelve pages, but emitted `Unbalanced target operations, expected ET` warnings.

The successful index supplies a usable reader path, not evidence that all extracted equations or text are faithful. The warnings require equation-dependent claims to use the separately budgeted visual checks rather than trusting damaged extraction. This auditor did not read the index, any paper excerpt or any rendered page. No claim about the article's title/version metadata beyond the protocol's identified source, or about its scientific content, is independently certified here.

The acquisition/accounting review finds no actual size, route, retry or observed-time violation. Paper interpretation and the shared reading ledger remain separate evidence tasks, and the historical T49 failure remains unchanged.
