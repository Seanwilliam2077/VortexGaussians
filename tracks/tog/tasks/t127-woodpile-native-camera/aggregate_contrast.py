"""Publish nonspatial contrast histograms for the eight registered T127 image pairs."""
import argparse
import gzip
import itertools
import json
import math
from pathlib import Path

import numpy as np

from score import CAMS, HERE, block_sums, digest, enforce, verified_shells


CUTOFF = 64  # Four 8-bit display pixels per channel, 16 levels in their mean.
BINS = 4 * 255 + 1
PIXELS = 264 * 470


def summarize(frames, shell, row):
    prefix = "{brush}-c{camera}-h{horizon}".format(**row)
    images = [frames / f"{prefix}-{mode}.png" for mode in ("full", "wood")]
    hashes = {p.name: digest(p) for p in images}
    enforce(hashes == row["sha256"], f"{prefix}: private PNG differs from SCORE.json")
    delta = np.abs(block_sums(images[0]) - block_sums(images[1])).max(axis=2)
    enforce(delta.shape == shell.shape, f"{prefix}: shell and image shapes differ")

    # Sort once to sum each bin with double-precision compensated summation.
    order = np.argsort(delta.ravel(), kind="stable")
    counts = np.bincount(delta.ravel(), minlength=BINS).tolist()
    enforce(len(counts) == BINS and sum(counts) == PIXELS, f"{prefix}: invalid display range")
    sorted_weights = shell.ravel()[order]
    bounds = list(itertools.accumulate(counts, initial=0))
    weights = [math.fsum(sorted_weights[lo:hi]) for lo, hi in zip(bounds, bounds[1:])]
    numerator = math.fsum(weights[CUTOFF:])
    denominator = math.fsum(weights)
    reference = {key: row[key] for key in
                 ("changed_pixels", "changed_shell_mass", "shell_mass", "passes_quarter")}
    enforce(sum(counts[CUTOFF:]) == reference["changed_pixels"],
            f"{prefix}: changed-pixel count differs from score")
    for got, want in [(numerator, reference["changed_shell_mass"]), (denominator, reference["shell_mass"])]:
        enforce(math.isclose(got, want, rel_tol=3e-12, abs_tol=1e-12),
                f"{prefix}: shell mass differs from score")
    passed = 4 * numerator >= denominator
    enforce(passed == reference["passes_quarter"], f"{prefix}: quarter decision differs from score")
    return {"camera": row["camera"], "brush": row["brush"], "horizon": row["horizon"],
            "sha256": hashes, "counts": counts, "shell_weights": weights, "reference": reference}, passed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Directory with the fitted PLY and cameras.json")
    parser.add_argument("--frames", type=Path, required=True, help="Private directory with 16 native PNGs")
    parser.add_argument("--output", type=Path, default=HERE / "evidence/CONTRAST.json.gz")
    args = parser.parse_args()
    score = json.loads((HERE / "evidence/SCORE.json").read_bytes())
    rows = score["comparisons"]
    keys = [(r["camera"], r["brush"], r["horizon"]) for r in rows]
    expected = set(itertools.product(CAMS, ("light", "full"), (44, 90)))
    enforce(len(keys) == len(expected) and set(keys) == expected, "Incomplete native pair identities")
    shells, _, sources = verified_shells(args.source)
    enforce(sources == score["source_sha256"], "Projection input differs from SCORE.json")
    results, endpoints = [], {cid: {} for cid in CAMS}
    for row in rows:
        summary, passed = summarize(args.frames, shells[row["camera"]], row)
        results.append(summary)
        if row["horizon"] == 90:
            endpoints[row["camera"]][row["brush"]] = passed
    choices = {}
    for cid, passes in endpoints.items():
        choices[str(cid)] = next((brush for brush in ("light", "full") if passes[brush]), "neither")
        archived = score["endpoint_choices"][str(cid)]
        enforce(passes == archived["at_90"] and choices[str(cid)] == archived["preferred"],
                f"Camera {cid}: endpoint choice differs from score")
    payload = {"schema": "t127-contrast-histogram-v1", "cutoff_sum": CUTOFF, "pixel_count": PIXELS,
               "endpoint_choices": choices, "comparisons": results}
    serialized = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode() + b"\n"
    with args.output.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            compressed.write(serialized)
    print(f"Verified {len(results)} pairs, 16 image identities, and +90 choices {choices}.")


if __name__ == "__main__":
    main()
