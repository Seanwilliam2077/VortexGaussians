# T27 metadata transport clarification

29 October 2026. Recorded after the first official dataset-page extraction and five fixed recipe acquisitions, before any further dataset request. The successful web response exposes numbered archive links but not their complete URL strings. Clicking a ZIP through that tool could fetch its body, which is forbidden here.

Use the remaining two metadata calls as follows: one bounded HTML-text read (maximum256KiB) of the SAME predeclared https://jonbarron.info/mipnerf360/ page solely to recover the actual archive href and any stated permission text; then one HEAD-only request for the first Dataset Pt.1 archive link if resolved. This consumes the optional description/permission-page slot: no separate permission page or additional source will be requested. Total metadata calls remain at mostthree. Do not guess an archive URL, download its body, inspect its ZIP directory, follow a new dataset route or retry an access failure.

This is a disclosed post-initial-access transport adjustment, not part of the original pre-access freeze. The observation source, overall request/byte caps and no-training/no-download gates remain unchanged. If the same-page text does not establish data permission, record that as unresolved rather than inferring it from accessibility. The original protocol and freeze stay byte-identical.
