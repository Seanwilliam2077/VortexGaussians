"""Check T90 delivered answers directly against the registered T92 shell truth."""
import argparse
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path, help="T90 dead-tree CAPTURE.json")
    args = parser.parse_args()
    capture = json.loads(args.capture.read_text(encoding="utf8"))
    truth = json.loads((HERE/"evidence/regional-truth.json").read_text(encoding="utf8"))
    expected = {(r["arm"],r["cut"],r["horizon"]):r for r in truth["windows"]}
    assert capture["status"] == "validated" and len(expected) == len(capture["queries"]) == 18
    verified = 0
    groups = {"stopped_before_terminal":[], "reached_terminal":[]}
    for row in capture["queries"]:
        cut, h = row["cut"], row["horizon"]
        true = expected.pop((row["arm"],cut,h))
        ev = true["events"]
        frame = true["first_ignition_frame"]
        ids = {int(i) for i in ev[0]["ids"]} if ev else set()
        assert row["first_frame"] == frame and set(row["expected_ids"]) == ids
        cost = {}
        for t in row["trials"]:
            assert t["yes"] == bool(ev) and t["first_frame"] == frame
            assert t["witness"] in ids if ev else t["witness"] is None
            if t["rep"]:
                cost.setdefault(t["method"],[]).append(t["delivered_ms"])
            verified += 1
        item = {k:median(v) for k,v in cost.items()}
        stopped = frame is not None and frame < cut+h
        groups["stopped_before_terminal" if stopped else "reached_terminal"].append(item)
    assert not expected
    print("Independently verified", verified, "warmup and measured trial answers")
    for group, rows in groups.items():
        print(group, len(rows), "windows")
        for a,b in [("t93","regional"),("rank-only","regional"),("t93","rank-only")]:
            print(f"  {a}/{b}: median paired delivered ratio {median(r[a]/r[b] for r in rows):.3f}")
if __name__ == "__main__":
    main()
