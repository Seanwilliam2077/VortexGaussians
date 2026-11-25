"""Verify the T109 pixel-wise shell and score T127 native gas/no-gas display pairs."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
TASKS = HERE.parent
T109 = TASKS / "t109-common-parent-choice"
PROJECTOR = T109 / "figure" / "project.py"
VALIDATION = T109 / "figure" / "validation.json"
CAMS = (0, 124)
EXPECTED = {0: {"light": False, "full": True}, 124: {"light": False, "full": False}}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def enforce(condition, message):
    if not condition:
        raise ValueError(message)


def verified_shells(source):
    # Reuse T109's label/exclusion logic and the exact T107 projection/raster implementation.
    spec = importlib.util.spec_from_file_location("woodpile_projection", PROJECTOR)
    projector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(projector)
    raster = projector.metrics
    previous = raster.read(VALIDATION)
    inputs = [source / "foreground.ply", source / "cameras.json", T109 / "REFERENCE.json",
              T109 / "shell.json.gz", T109 / "evidence/native/capture-report.json",
              *(T109 / f"evidence/native/{arm}-trace.json.gz" for arm in ("AL", "AF"))]
    source_hashes = {path.name: digest(path) for path in inputs}
    enforce(source_hashes == previous["source_sha256"], "T109 geometry, calibration or shot changed")
    pos, covariance, opacity = raster.splats(source / "foreground.ply")
    cameras = {c["id"]: c for c in raster.read(source / "cameras.json")}
    labels = projector.native_labels()
    eligible = labels["AL"][0]
    enforce(eligible == labels["AF"][0] and len(eligible) == 2371, "Unexpected eligible sites")
    ids = np.array(sorted(eligible), dtype=int)
    sites = [p["index"] for p in raster.read(T109 / "recipe.json")["picks"]]
    shells, checks = {}, {}
    # The first overlay is independent of the event labels that color the second overlay.
    event_frames = {"eligible": np.full(len(pos), 999)}
    for cid in CAMS:
        projection = raster.projection(pos, covariance, cameras[cid])
        weights, _, overlays, _ = raster.raster(projection, opacity, {"eligible": eligible},
                                                event_frames, sites)
        shell = overlays["eligible"][0]
        enforce(shell.shape == (264, 470) and np.all(np.isfinite(shell)) and np.min(shell) >= 0,
                f"Invalid shell pixels for camera {cid}")
        old = previous["views"][str(cid)]
        archived = TASKS / f"t107-visible-burn-progression/evidence/weights-{cid}.json.gz"
        enforce(digest(archived) == old["archive_weight_sha256"], "Changed reference site weights")
        values = dict(raster.read(archived)["eligible_weights"])
        np.testing.assert_allclose(weights[ids], [values[j] for j in ids], rtol=3e-12, atol=1e-11)
        integer_mass = int(np.floor(weights[ids] * 1e6 + .5).sum())
        total = float(shell.sum())
        np.testing.assert_allclose(total, weights[ids].sum(), rtol=3e-13, atol=0)
        for arm in ("AL", "AF"):
            ref = old["mass"][arm]
            enforce(integer_mass == ref["integer_total"], f"Integer denominator mismatch for {cid}")
            np.testing.assert_allclose(total, ref["raster_total"], rtol=3e-12, atol=0)
        shells[cid] = shell
        checks[cid] = {"eligible_sites": len(ids), "world_sites": len(pos), "integer_total": integer_mass,
                       "raster_total": total, "weight_archive_sha256": old["archive_weight_sha256"]}
    return shells, checks, source_hashes


def block_sums(path):
    with Image.open(path) as image:
        enforce(image.format == "PNG" and image.mode in ("RGB", "RGBA") and image.size == (940, 528),
                f"Expected an opaque 940 x 528 RGB(A) PNG: {path.name}")
        pixels = np.asarray(image)
        enforce(pixels.dtype == np.uint8, f"Expected display bytes in {path.name}")
        if image.mode == "RGBA":
            enforce(np.all(pixels[:, :, 3] == 255), f"Nonopaque alpha in {path.name}")
        return pixels[:, :, :3].reshape(264, 2, 470, 2, 3).sum(axis=(1, 3), dtype=np.int32)


def compare(frames, shells):
    rows, choices = [], {}
    for cid, shell in shells.items():
        endpoint = {}
        for horizon in (44, 90):
            for brush in ("light", "full"):
                prefix = f"{brush}-c{cid}-h{horizon}"
                ordinary, wood = (frames / f"{prefix}-{suffix}.png" for suffix in ("full", "wood"))
                delta = np.abs(block_sums(ordinary) - block_sums(wood)).max(axis=2)
                changed = delta >= 64
                mass, total = float(shell[changed].sum()), float(shell.sum())
                passed = 4 * mass >= total
                rows.append({"camera": cid, "brush": brush, "horizon": horizon, "changed_pixels": int(changed.sum()),
                             "max_display_channel_difference": float(delta.max()) / 4, "changed_shell_mass": mass,
                             "shell_mass": total, "fraction": mass / total, "passes_quarter": passed,
                             "sha256": {f.name: digest(f) for f in (ordinary, wood)}})
                if horizon == 90:
                    endpoint[brush] = passed
        choice = next((brush for brush in ("light", "full") if endpoint[brush]), "neither")
        choices[cid] = {"at_90": endpoint, "preferred": choice, "prediction": EXPECTED[cid],
                        "matches_both_predictions": endpoint == EXPECTED[cid]}
    return {"comparisons": rows, "endpoint_choices": choices,
            "all_four_predictions_match": all(x["matches_both_predictions"] for x in choices.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=HERE.parents[4] / "real-asset-ingest")
    parser.add_argument("--frames", type=Path, help="Private PNG directory after capture/state validation")
    args = parser.parse_args()
    shells, checks, source_hashes = verified_shells(args.source)
    result = {"schema": "t127-visible-gas-v1", "source_sha256": source_hashes, "reference_checks": checks,
              "projection_source_sha256": {f.name: digest(f) for f in
                                           (PROJECTOR, VALIDATION, TASKS / "t107-visible-burn-progression/measure.py")},
              "readout": "top-left RGB bytes; 2x2 block means; max channel change >=16; shell fraction >=0.25"}
    if args.frames:
        result.update(compare(args.frames, shells))
    print(json.dumps(result, allow_nan=False, indent=2))


if __name__ == "__main__":
    main()
