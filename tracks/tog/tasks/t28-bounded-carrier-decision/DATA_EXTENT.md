# T28 — one scene's acquisition extent from ZIP metadata

29 October 2026. Bonsai was selected in the [protocol](PROTOCOL.md) before directory access because it is an indoor scene named by the original training script. No preview, learned parameter, ray, overlap distribution or candidate acceptance informed that choice.

## Actual reads and selected scope

Two Range requests to the same T27 archive returned206 with exact requested Content-Range and the saved ETag. A65,557-byte tail supplied ZIP64/end records; a773,878-byte central-directory request supplied all6,583 entries. Total archive-body metadata read is839,435 bytes, including overlapping portions; this is not zero archive-body acquisition. Both read ranges lie in the central-directory/end-record region. No image, camera, point or license-member payload was read, decompressed or extracted. A four-call/4MiB budget was available; the unused calls were not consumed.

| Selected original input | Files | Compressed bytes | Uncompressed bytes declared by directory |
|---|---:|---:|---:|
| bonsai/images |292|953,118,939|954,204,663|
| bonsai/sparse/0 |3|55,792,794|93,277,555|
| Combined payload |295|1,008,911,733|1,047,482,218|

The sparse filenames are cameras.bin, images.bin and points3D.bin. Three directory entries are also present in the298-entry selected inventory; they contribute zero payload bytes. Downsampled images_2/4/8 and poses_bounds.npy exist in directory metadata but are not part of this selected original-input total. No downsampled variant was substituted to improve feasibility. The summary and private inventory hashes are in [archive-summary.json](archive-summary.json) and the [acquisition ledger](acquisition-requests.json).

This is about1.01 decimalGB compressed and1.05GB uncompressed, substantially below the full12.54GB archive. The declared member sizes bound their described payload, not the complete future download: member headers/descriptors, integrity checks, request overhead, temporary files, environment, training output and any changed-object failure still need separate accounting. Saved metadata alone does not validate member CRCs, image resolutions/content, camera validity, point counts or whether the loader succeeds. The observed endpoint is HTTP; an ETag match is object consistency evidence, not authenticated data provenance or an integrity guarantee.

## Data conditions remain separate

The central-directory names contain no identified LICENSE/README/COPYING/TERMS member under the declared filename search. No general statement about arbitrary text inside images or other members follows. The official MultiNeRF repository resolves to5b4d4f64608ec8077222c52fdf814d40acc10bc1; its acquired README describes the images/sparse layout and its LICENSE is Apache2.0 for the repository. Neither inspected text explicitly binds that code license to this separately hosted observation archive. The original official project page and public download establish source provenance; the inspected evidence does not settle all dataset-use or redistribution conditions. Missing terms are not a finding that research use is forbidden.

The size uncertainty has narrowed to a concrete small input scope. It does not independently qualify the complete carrier plan, whose fixed software route remains unresolved. No dataset acquisition protocol or training run follows automatically. [Independent archive review](../../../validation/t28-archive-review.md) cross-checks the saved structure without additional network access.
