"""Verify output, state receipts and the paired costs of each exact heat scan."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
MODES = ("active-anchor", "sparse-active", "repair-active", "sparse-repair")
RATIOS = (("sparse-active", "active-anchor"), ("sparse-repair", "repair-active"),
          ("repair-active", "active-anchor"), ("sparse-repair", "sparse-active"),
          ("repair-active", "sparse-active"))


def check(ok, msg):
    if not ok:
        raise ValueError(msg)


def read(path):
    return json.loads(path.read_bytes())


def score(asset):
    f = HERE / "evidence" / asset / "CAPTURE.json"
    data = read(f)
    check(data["status"] == "validated" and not data["errors"] and
          tuple(data["methods"]) == MODES and data["repeats"] == 4, "Frozen schedule")
    target = {q["arm"]: q for q in read(HERE.parent / "t98-edit-to-answer/REFERENCE.json")["queries"]
              if q["asset"] == asset and q["horizon"] == 60}
    out = []
    for qi, q in enumerate(data["queries"]):
        arm = q["arm"]
        ref = target.pop(arm)
        audit = data["arms"][arm]["sparse_audit"]
        check(audit["matched_frames"] == len(audit["native_hashes"]) == 9 and
              data["arms"][arm]["verified_frames"] == 360, "Complete-state audit")
        expiry = data["arms"][arm].get("repair_audit")
        if arm == "AB" and asset == "firewoods":
            check(expiry["status"] == "matched_expiry_and_continuation" and
                  expiry["repair_frame"] == expiry["cut"] + expiry["length"], "Physical repair and next native frame")
        by_method = {m: [] for m in MODES}
        for i, t in enumerate(q["trials"]):
            rep, j = divmod(i, len(MODES))
            m = MODES[(rep + j + qi) % len(MODES)]
            check(t["method"] == m and t["rep"] == rep and q["horizon"] == 60, "Trial order")
            check(t["first_frame"] == ref["first_frame"] and t["yes"] == bool(ref["ids"]) and
                  (t["witness"] in ref["ids"] if ref["ids"] else t["witness"] is None) and
                  t["prefix_steps"] == ref["observed_steps"], "Exact event/frame")
            if rep:
                by_method[m].append(t)
        summary = {}
        for m, records in by_method.items():
            check(len(records) == 4, "Measured repetitions")
            row = {"delivered_ms": median(t["delivered_ms"] for t in records),
                   "compute_ms": median(t["compute_ms"] for t in records)}
            if m.startswith("sparse-"):
                s = records[0]["sparse"]
                row["sparse"] = {k: v for k, v in s.items() if k != "build_ms"}
                check(all(all(t["sparse"][k] == v for k, v in row["sparse"].items()) for t in records),
                      "Sparse work counts")
                row["sparse"]["build_ms"] = median(t["sparse"]["build_ms"] for t in records)
            summary[m] = row
        ratios = {}
        for a, b in RATIOS:
            raw = [x["delivered_ms"] / y["delivered_ms"] for x, y in zip(by_method[a], by_method[b])]
            ratios[a + "/" + b] = {"estimate": summary[a]["delivered_ms"] / summary[b]["delivered_ms"],
                                    "matched_wave_range": [min(raw), max(raw)]}
        out.append({"arm": arm, "first": q["first_frame"], "state_audit": audit, "repair_audit": expiry,
                    "methods": summary, "ratios": ratios})
    check(not target and len(out) == 2, "Two actual brush orders")
    return {"asset": asset, "capture_sha256": hashlib.sha256(f.read_bytes()).hexdigest(), "queries": out}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("asset", choices=("firewoods", "dead-tree"))
    name = p.parse_args().asset
    result = score(name)
    (HERE / "evidence" / name / "SCORE.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    for q in result["queries"]:
        print(q["arm"], {k: round(v["delivered_ms"], 2) for k, v in q["methods"].items()})

