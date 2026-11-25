"""Separate queries that reach their requested last scan from earlier native positives."""
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "t90-callable-regional-query" / "evidence"
METHODS = ("regional", "all-carriers", "rank-only", "t93")


def analyze(asset):
    c = json.loads((BASE / asset / "CAPTURE.json").read_text())
    if c["status"] != "validated":
        raise ValueError("Unvalidated capture")
    rows = []
    for q in c["queries"]:
        elapsed = {}
        for method in METHODS:
            trials = [x for x in q["trials"] if x["rep"] > 0 and x["method"] == method]
            if len(trials) != 7:
                raise ValueError("Incomplete paired measurements")
            if not all(x["first_frame"] == q["first_frame"] and
                       (x["witness"] in q["expected_ids"] if x["yes"] else x["witness"] is None)
                       for x in trials):
                raise ValueError("Native event reference")
            elapsed[method] = median(x["delivered_ms"] for x in trials)
        trial = next(x for x in q["trials"] if x["method"] == "t93")
        reached = q["first_frame"] in (None, q["cut"] + q["horizon"])
        if reached != ("terminal_counts" in trial):
            raise ValueError("Terminal invocation mismatch")
        rows.append(dict(arm=q["arm"], cut=q["cut"], horizon=q["horizon"], terminal=reached,
                         yes=q["first_frame"] is not None, delivered_ms=elapsed,
                         counts=trial.get("terminal_counts")))
    summary = {}
    for label, subset in (("all", rows), ("reached", [r for r in rows if r["terminal"]]),
                          ("earlier_hit", [r for r in rows if not r["terminal"]]),
                          *((f"H{h}", [r for r in rows if r["horizon"] == h]) for h in (1,4,8))):
        v = [r["delivered_ms"] for r in subset]
        summary[label] = dict(windows=len(v),
                              median_delivered_ms={m:median(s[m] for s in v) for m in METHODS},
                              t93_over_regional=median(s["t93"]/s["regional"] for s in v),
                              t93_over_rank=median(s["t93"]/s["rank-only"] for s in v))
    reached = [r["counts"] for r in rows if r["terminal"]]
    totals = {key:sum(row[key] for row in reached) for key in reached[0]}
    return dict(summary=summary, terminal_work=totals, rows=rows)


if __name__ == "__main__":
    score = {a:analyze(a) for a in ("firewoods","dead-tree")}
    (HERE/"SCORE.json").write_text(json.dumps(score,indent=2)+"\n", encoding="utf8")
    for key,data in score.items():
        print(key, data["terminal_work"])
        for label, entry in data["summary"].items():
            print(label,entry["windows"],round(entry["t93_over_regional"],3),round(entry["t93_over_rank"],3))
