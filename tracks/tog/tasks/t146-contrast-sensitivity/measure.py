"""Recompute light-first choices for every representable positive RGB contrast."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASKS = HERE.parent
WOOD = TASKS / "t140-native-shell-sensitivity/evidence"
ROOM = TASKS / "t144-bonsai-repeated-cost/evidence/process-1/RUN.json.gz"


def opacity_curve(bins, denominator):
    assert len(bins) == 1021 and all(math.isfinite(v) and v >= 0 for v in bins)
    assert math.isclose(math.fsum(bins), denominator, rel_tol=1e-11) and denominator > 0
    # Suffixes are summed independently to avoid subtracting almost equal masses.
    fractions = [math.fsum(bins[start:]) / denominator for start in range(1, 1021)]
    assert all(b <= a for a, b in zip(fractions, fractions[1:]))
    return fractions


def choice_intervals(light, full):
    ranges = []
    for tick, (a, b) in enumerate(zip(light, full, strict=True), start=1):
        take = "light" if a >= 0.25 else "full" if b >= 0.25 else "neither"
        if ranges and ranges[-1]["choice"] == take:
            ranges[-1]["last"] = tick / 4
        else:
            ranges.append(dict(first=tick / 4, last=tick / 4, choice=take))
    return ranges


def measure():
    wood = json.loads(gzip.decompress((WOOD / "CONTRAST.json.gz").read_bytes()))
    original = json.loads((WOOD / "SCORE.json").read_bytes())
    room = json.loads(gzip.decompress(ROOM.read_bytes()))
    histograms, targets = {}, {}
    for cam in (0, 124):
        pair = []
        for brush in ("light", "full"):
            bins = wood[f"{brush}-c{cam}-h90"]["weights"]
            denominator = original["views"][str(cam)]["native_total"]
            pair.append(opacity_curve(bins, denominator))
            registered = next(r for r in original["gas"] if
                              (r["brush"], r["camera"], r["horizon"]) == (brush, cam, 90))
            assert math.isclose(pair[-1][63], registered["fraction"], abs_tol=1e-12)
        histograms[f"woodpile_{cam}"] = pair
        targets[f"woodpile_{cam}"] = denominator
    oracle = room["actions"][0]
    assert oracle["method"] == "ordinary-native" and oracle["audit"]
    assert [b["name"] for b in oracle["branches"]] == ["L", "F"]
    pair = []
    for branch in oracle["branches"]:
        result = branch["result"]
        pair.append(opacity_curve(result["contrast"]["massByBlockBin"], result["denominator"]))
        assert pair[-1][63] == result["fraction"] == 0
    histograms["bonsai_0"] = pair
    targets["bonsai_0"] = room["matte"]["total"]
    assert oracle["secondary"] == "undefined"
    sources = [WOOD / "CONTRAST.json.gz", WOOD / "SCORE.json", ROOM]
    score = dict(
        sha256={p.relative_to(TASKS).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        cutoff_count=1020, threshold_scale=4, required_fraction=0.25,
        views={key: dict(denominator=targets[key], choices=choice_intervals(*pair),
                         highest_passing_cutoff=[max((i / 4 for i, f in enumerate(c, 1) if f >= 0.25),
                                                    default=None) for c in pair],
                         fraction_at_smallest=[c[0] for c in pair], fraction_at_16=[c[63] for c in pair])
               for key, pair in histograms.items()},
        undefined=["bonsai_146"])
    return score, histograms


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    score, _ = measure()
    path = HERE / "SCORE.json"
    if args.check:
        assert score == json.loads(path.read_bytes())
    else:
        path.write_text(json.dumps(score, indent=2) + "\n", encoding="utf8")
    for name, view in score["views"].items():
        print(name, view["choices"], view["fraction_at_smallest"])
