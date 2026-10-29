# T37 independent saved-output review

**The screen completed correctly; neither cheap arm qualifies on the whole frame.** One independent saved-data audit passed 1,917,160 checks with zero failures. Both arms have definite RGB failures relative to the fixed reference intervals, but the sorted arm's demonstrated failure is confined to four pixels. This establishes limits of these two approximations, not a substantial unsolved rendering task or a new method contribution.

## Accuracy and fixed foreground

All 98,304 records are valid and complete, with no corrupted, failed or unfinished records. Each arm has 49,152 pixels; the foreground denominator remains the original 986 pixels with T35 full alpha at least 0.001. No new output or accuracy result selected that mask.

| Arm | Full frame: qualified / definite failure / unresolved | Fixed foreground: qualified / definite failure / unresolved |
|---|---:|---:|
| sorted | 49,097 / 4 / 51 | 931 / 4 / 51 |
| mixture | 48,956 / 78 / 118 | 790 / 78 / 118 |

Every alpha passes; maximum alpha error for either arm is 0.000013414859907250228. Joint and RGB classifications consequently coincide in this run. All non-qualified pixels are in the fixed foreground. The 51 and 118 unresolved pixels are not proven failures: the retained interval is insufficient to establish either qualification or definite failure for those outputs. No reference refinement was performed.

For sorted output, maximum shortest distance to the reference interval is **0.003496171048897434**, and maximum distance to either endpoint is **0.005355784406043118**. Definite failures occupy exactly the two-by-two box `[126,139,127,140]`, two pixels in each of rows 139 and 140. For mixture, these maxima are **0.022124391522057696** and **0.02410103764251781**, with 78 definite failures bounded by `[123,78,131,141]`. Per-row counts and channel maxima remain in the audit and lossless records.

## Display and interpretation

All six original-size PNGs were independently decoded; every RGB, classification and difference byte matches its stored values and fixed mapping. Green means joint qualification, red definite failure, yellow unresolved, and magenta invalid/unfinished. The screen's successful execution does not change these accuracy meanings.

Relative to the qualified T36 display, sorted changes 51 pixels in the full image and 38 in the fixed foreground, with a maximum channel difference of **1 out of 255**. Only **one of its four definite-failure pixels** changes a display byte. Mixture changes 155 full-image pixels and 142 foreground pixels; 57 of its 78 definite-failure pixels change a display byte, with maximum difference **2 out of 255**. The maps use unamplified absolute display differences.

These comparisons do not promote T36 RGB to exact truth. Quantized display agreement does not prove radiance accuracy, and a one- or two-level difference is not a perceptual judgment or user-study result. The evidence shows small displayed differences on this sparse authored frame, alongside numerical threshold failures. It does not demonstrate meaningful creative difficulty, optimized-GL failure, or necessity of an ordering certificate.

## Identity, cost and limits

All 26 frozen inputs passed before/after checks; freeze SHA256 is `3ff6042feb3cc8e03a1ba9779a383a25e85cb279f7148ab2e98118f11b417626`. Compressed/raw records, previous comparison data, receipts, logs and all PNG identities matched. New numeric evidence totals **11,808,775 bytes**, below 16 MiB. The two arms independently reproduce noncolor preparation fields for all 49,152 positions and independently pay 49,152 queries/outputs, 42,026 retained mass evaluations and their tree construction. Sorted additionally records its sorting and compensated-prefix work. No GL/reference counter or call appears in this invocation.

Computation took **17.2413524 s**; publication/encoding took **2.8086605 s** and supervisor process/cleanup time was **20.1804115 s**, with no timeout, errors or live child. Sorted preparation/output costs were 2.5062296/1.3357101 s; mixture costs were 3.1083412/1.4404178 s. Comparisons, writes, per-arm tree/camera and shared setup/source/decode work are separately recorded. The fixed arm order and single pass do not establish a timing distribution or causal speedup over T36. T35/T36's previously paid computation remains visible; T35–T37 computation totals **708.8417897 s**, excluding separately recorded publication and supervisor overhead.

The audit imported no method, kernel, reference or persistence module and generated no scientific output. It checked 98,304 stored tau/alpha identities using scalar `expm1` as expressly permitted, plus saved-value comparisons and display encoding. It did not evaluate any Gaussian CDF, project a ray, integrate a field or rebuild prior reference leaves. Source-level projection and omitted-mass evidence remain inherited under the fixed-source contract. Qualification is conditional on existing binary64 intervals, not a formal floating-point certificate.

Audit report: `validation/t37-saved-output-audit.json`, SHA256 `b7d907465c21ba02be28dfa65fee8b214786ccbe351efb1cb52040f5aa418e00`. Auditor stdout SHA256 is `2f9e26955f3292057e7a136cba02104d2adf9e5c919f2723c638841178657579`; stderr is empty (`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). Original scientific outputs and history are unchanged.

The fixed decision is “both arms have definite failures,” with the narrow extent above. Before spending on a compiled ordinary comparison or any method, assess whether this frame's small approximation differences are a useful target. No oracle selector, new method, another view, reference refinement or next numerical experiment was executed or authorized by this review.
