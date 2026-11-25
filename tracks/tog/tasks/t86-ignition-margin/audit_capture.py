"""Verify the T86 native reference and cut features directly from the public files."""
import argparse
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
N = 34687


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_packed(folder, record):
    packed = (folder / record["name"]).read_bytes()
    require(len(packed) == record["bytes"] and digest(packed) == record["sha256"], record["name"])
    raw = gzip.decompress(packed)
    require(len(raw) == record["decoded_bytes"] and digest(raw) == record["decoded_sha256"], record["name"])
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=HERE / "public", help="Public or reproduction output")
    parser.add_argument("--checkpoints", type=Path, help="Optionally verify the complete local checkpoints")
    args = parser.parse_args()
    report = json.loads((args.evidence / "capture-report.json").read_bytes())
    require(report["status"] == "validated" and not report["errors"], "Unqualified capture")
    records = {r["name"]: r for r in report["files"]}
    require(len(records) == 14 == len(report["files"]), "Unexpected artifact list")
    history = HERE.parent / "t84-ignition-edit-footprint" / "material_onsets.csv.gz"
    require(digest(history.read_bytes()) == report["sources"]["T84_onsets"]["sha256"], "T84 table changed")
    with gzip.open(history, "rb") as stream:
        historical = {int(r["material_id"][4:]): (int(r["AB_onset_frame"]), r["AB_status"])
                      for r in csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8"))
                      if r["policy"] == "global" and r["AB_status"] != "right_censored"}
    for arm, shot in report["shots"].items():
        rows = load_packed(args.evidence, records[arm + "-trace.json.gz"])
        require([r["frame"] for r in rows] == list(range(1, 361)), arm + " missing frames")
        require(shot["initial"]["name"] == arm[0] and shot["edit"]["name"] == arm[1], arm + " contact order")
        direct = set(shot["edit"]["ids"])
        onsets = {idx: 0 for idx in shot["initial"]["ids"]}
        for row in rows:
            f = row["frame"]
            ids = set(row["new_ids"])
            require(row["retired"] == 0 and row["step_ms"] >= 0 and row["observer_ms"] >= 0, f)
            require(not (ids & onsets.keys()) and len(ids) == len(row["new_ids"]), f)
            onsets.update(dict.fromkeys(ids, f))
            require(len(onsets) == row["active_count"], f)
            if f == 180:
                require(not (direct & onsets.keys()) and len(direct) == shot["edit"]["count"], "Second stroke")
                onsets.update(dict.fromkeys(direct, 180))
            if f not in (210, 240, 300):
                continue
            label = f"{arm}-{f}"
            eligibility = load_packed(args.evidence, records[label + "-eligibility.json.gz"])
            require(eligibility["arm"] == arm and eligibility["frame"] == f and eligibility["threshold"] > 0, label)
            require(all(len(eligibility[k]) == N for k in ("state", "heat", "fuel")), label)
            require({i for i, s in enumerate(eligibility["state"]) if s != 0} == onsets.keys(), label)
            require(all(s in (0, 1) for s in eligibility["state"]), label)
            require(all(h >= 0 for h in eligibility["heat"]) and all(0 <= x <= 1 for x in eligibility["fuel"]), label)
            if args.checkpoints:
                checkpoint = load_packed(args.checkpoints, records[label + ".json.gz"])
                require(all(checkpoint[k] == eligibility[k] for k in ("arm", "frame", "state", "heat", "fuel", "native_hash")), label)
                require(len(checkpoint["frontier"]) == len(onsets) and set(checkpoint["frontier"]) == onsets.keys(), label)
                require(checkpoint["params"]["spreadIgnH"] == eligibility["threshold"], label)
                require(sum(len(layer["particles"]) for layer in checkpoint["gas"]) == row["gas_count"], label)
        require(len(onsets) == shot["end"]["burning"] and shot["end"]["charred"] == 0, arm)
        require(all(0 <= i < N for i in onsets), arm + " bad PLY index")
        if arm == "AB":
            reconstructed = {i: (max(f, 180), "direct_stroke" if i in direct else
                                 "left_censored" if f <= 180 else "observed") for i, f in onsets.items()}
            require(reconstructed == historical, "Per-ID T84 history differs")
        print(f"{arm}: 360 frames, 3 exact cut projections, {len(onsets)} endpoint active sites.")


if __name__ == "__main__":
    main()
