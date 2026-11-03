# Paper source

`main.tex` is the condensed paper, `supplemental.tex` holds the evidence moved out of it.

## Where this source came from

The LaTeX source of the 31-page paper is not in this repository, in its history, or in the 2026-09-29
migration archive (that migration moved documents only, not `.tex`). This tree was **rebuilt from the
published PDF**, kept at `source/vortex_gaussians_paper_2026-08-31.pdf`:

- Figures are the images embedded in that PDF, at their native resolution.
- Equations were re-typeset by hand against the PDF. Check them against the PDF before submission.
- The reference list is extracted by `tools/extract_refs.py`, which keeps only what each `.tex` cites.
- Figure 2 of the old paper (the TikZ system overview) was not carried over; the project page has it
  as `static/images/pipeline.jpg`.

If the original source turns up, treat this tree as the target text and port it across.

## Build

```bash
python paper/tools/extract_refs.py paper/source/vortex_gaussians_paper_2026-08-31.pdf paper/main.tex -o paper/refs.bbl
python paper/tools/extract_refs.py paper/source/vortex_gaussians_paper_2026-08-31.pdf paper/supplemental.tex -o paper/refs_supp.bbl
cd paper
tectonic -X compile main.tex --outdir ../static
tectonic -X compile supplemental.tex --outdir ../static
```

Rename the outputs to `vortex_gaussians_paper.pdf` and `vortex_gaussians_supplemental.pdf`. The site version
has no review line numbers. `extract_refs.py` needs `pip install pymupdf`.

## Figures that need re-rendering

The teaser and the `kitchen` and `treehill` figures were rendered before the world-space fire light
existed, and the paper says so. Re-rendering them needs the two pre-trained scenes, which are not on
this machine, and `tools/harness.py` can drive them once they are. The same goes for timing the light
at 729,826 splats and running the automatic deflection proxies on a capture.

## New measurements in this revision

Everything below came from `tools/harness.py` on 2026-11-02 on a Ryzen 9 9950X with Chrome 156:

| Measurement | Result |
| --- | --- |
| Replay hashes, branch against `main` | identical, 4 of 4 (`ea909174`, `8e220c1b`, `3fb459a3`, `bf0b161c`) |
| RTX 5070 Ti, fire only | 6.57 ms interactive, 16.51 ms quality |
| Radeon iGPU (desktop part, not a laptop), fire only | 44.55 ms interactive, 97.78 ms quality |
| Deflection, 8 seeds | inside sphere 4.08% → 0.00%, on-axis 81% → 55%, wake width 0.144 → 0.200 |
| Deflection path cost, 12 spheres | sim step 4.54 → 4.93 ms |
| Fire light, 45.8k scene | 10.97 → 10.80 ms over 40 frames (no measurable cost), mean image value 26.4 → 34.4 |
| Hero preset | 26.2k Gaussians, mean image gradient 0.37 → 0.43 against quality |
