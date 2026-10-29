# T28 — independent saved ZIP-directory review

29 October 2026. Reviewer: pressure_screen. **PASS for saved metadata consistency only.** Used Python's standard-library `zipfile` against a read-only virtual file containing exactly the two acquired byte ranges; any uncovered read raises immediately. The guard was explicitly checked with an unavailable byte at offset zero. No network, extraction, member decompression, image/camera/point payload, external package import or numerical research run occurred.

## Independent checks and result

The virtual archive's declared length is 12,535,427,936 bytes. `zipfile` read only EOCD `[12535427914,12535427936)`, ZIP64 locator `[12535427894,12535427914)`, ZIP64 end record `[12535427838,12535427894)`, and central directory `[12534653960,12535427838)`. It recovered **6,583 entries** and an empty archive comment.

Every ordered entry matches `acquired/archive-members.json` on all seven fields: name, compression method, flags, CRC32, compressed size, uncompressed size and local-header offset. Names are unique; recorded member volumes are zero; encryption flags are clear; methods are stored (1,016 entries) or deflate (5,567). Declared offsets and offset-plus-compressed-size lie before the central directory. These checks do not parse the unavailable local headers or establish nonoverlapping complete member extents.

Independent selection by the exact prefixes `bonsai/images/` and `bonsai/sparse/` matches all records in `selected-bonsai-members.json`, including three directory entries. The current summary's file/entry distinction and totals match:

| Selected group | Files | Compressed payload bytes | Uncompressed bytes |
| --- | ---: | ---: | ---: |
| Original images | 292 | 953,118,939 | 954,204,663 |
| Sparse camera/point files | 3 | 55,792,794 | 93,277,555 |
| Total | **295** | **1,008,911,733** | **1,047,482,218** |

There are **298 selected entries**, not 298 payload files. Compressed totals exclude local headers, descriptors, central metadata, request overhead, extraction temporaries and any additional training assets; they are not an end-to-end storage/acquisition estimate.

Both saved range receipts report 206 and exact requested Content-Range, Content-Length, body length and SHA256. Their response ETags equal their sent If-Match value, `"cef2ef3aeaf0c062dbe65130bc249870"`; the total object size agrees. The 65,459 overlapping bytes match exactly. **839,435 archive-body metadata bytes were acquired** across two calls; the union covers 773,976 distinct bytes. Do not subtract the overlap from the paid acquisition count. This review verifies saved receipts, not the server's behavior independently of those receipts.

The first local audit invocation reached full member/selected-list equality and then stopped on a summary-key assumption (`members`): the concurrently revised summary uses `entries`, `files`, and `directory_entries`. The helper was corrected to that explicit schema and rerun locally once; all checks then passed. No source bytes, member lists or historical gates were altered, and no acquisition was repeated.

## Scope limits

Listed CRCs are declarations only: no member content was read or checksummed. Matching metadata, local hashes and ETags do not authenticate the remote dataset or establish image decoding, camera validity, actual extracted bytes, complete permissions or training suitability. The archive requests used **HTTP**, so the receipt/ETag observations are not a TLS authenticity guarantee. No finding here establishes research-use prohibition, redistribution rights, build compatibility, useful candidate frequency or a TOG contribution.

## Audited identities

Paths are relative to `tracks/tog/tasks/t28-bounded-carrier-decision/`. Helper/output remain local and ignored; the table preserves the checked identities.

| File | Bytes | SHA256 |
| --- | ---: | --- |
| `acquired/http-receipts.json` | 6607 | `4b3f9e916a751172361fa6e4472e10163b9caa7dbbfc56d98f793e0233bd187c` |
| `archive-summary.json` | 1966 | `723f6e69114e555d787cd8754ad719d2a148c4fed74cda2de2d34ce0f8d61bc8` |
| `acquired/archive-members.json` | 1413971 | `c8fa3b030731c7b47f6e5905478191ecd22e77dd151617dfe71dfcfa1940b919` |
| `acquired/selected-bonsai-members.json` | 63888 | `6ef14f2d8abaffab89049b37280cc3654d40d55ea9e72e8e6e75938effea966a` |
| `acquired/archive-tail.bin` | 65557 | `d19ecd51acafe98f6e2d10df2c8fc5a3b5aaf9bc3656a443af377e346a2a7112` |
| `acquired/archive-central-directory.bin` | 773878 | `ffcb402cd4b5f7aa5de4f6fc8833933c909725c9524010df91b31efbda57f246` |
| `local/independent_archive_review.py` | 8440 | `d68861383b61e2d09dea06e81f02dc74da148bb491b817e82d3b44ca288886b9` |
| `local/archive-independent-check.json` | 2553 | `e2a788874b6c730d9b1dfa7bdfeb45032955f5ea81683ebc2b9e76c87e5c3809` |
