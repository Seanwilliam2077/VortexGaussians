"""Join the causal decisions to independently timed browser calls, using only saved data."""
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
T90 = HERE.parent / "t90-callable-regional-query/evidence"


def summarize(name, prefix):
    cap = json.loads((T90 / name / "CAPTURE.json").read_bytes())
    pred = json.loads((HERE / (prefix + "PREDICTIONS.json")).read_bytes())
    causal = {(r["arm"], r["cut"]): r["methods"]["sampled"] for r in pred["rows"]}
    assert cap["status"] == "validated" and not cap["errors"]
    windows = []
    for q in cap["queries"]:
        a = causal[q["arm"], q["cut"]]
        direct = a["decision"] == "yes" or (q["horizon"] == 1 and a["decision"] == "no")
        times = {}
        for m in ("t91", "regional", "t93", "rank-only"):
            runs = [r for r in q["trials"] if r["method"] == m and r["rep"] > 0]
            assert len(runs) == 7
            if m == "t91":
                for run in runs:
                    assert run["estimated"] == a["decision"]
                    assert (run["prefix_steps"] == 0) == direct
                    if direct:
                        assert run["witness"] == a["witness"] and run["fork_ms"] == 0
            times[m] = median(r["delivered_ms"] for r in runs)
        windows.append({"arm":q["arm"], "cut":q["cut"], "horizon":q["horizon"], "direct":direct,
                        "times_ms":times})
    groups = {}
    for name, group in (("all", windows), ("direct", [w for w in windows if w["direct"]]),
                        ("fallback", [w for w in windows if not w["direct"]])):
        if not group:
            groups[name] = {"windows":0}
            continue
        times = [w["times_ms"] for w in group]
        groups[name] = {"windows":len(group), "median_ms":{m:median(t[m] for t in times) for m in times[0]},
                        "median_times_ratio":{m:median(t["t91"]/t[m] for t in times)
                                              for m in ("regional", "t93", "rank-only")}}
    return {"groups":groups, "windows":windows}


if __name__ == "__main__":
    rows = {n:summarize(n,p) for n,p in (("firewoods",""),("dead-tree","TRANSFER-"))}
    (HERE / "CALLABLE.json").write_text(json.dumps(rows, indent=2)+"\n")
    for name, result in rows.items():
        print(name,result["groups"])
