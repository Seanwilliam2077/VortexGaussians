"""Verify callable answers and summarize paired query-level timing (Python standard library)."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
METHODS = ("full", "trim", "regional", "t91", "t93", "rank-only", "all-carriers")
BINS = ("delivered_ms", "browser_ms", "compute_ms", "fork_ms", "restore_ms")


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def check(value, label):
    if not value:
        raise ValueError(label)


def method_summary(rows, name):
    costs = {}
    for key in BINS:
        vals = [r["methods"][name][key] for r in rows]
        costs[key] = median(vals)
    ratios = [r["methods"][name]["delivered_ms"] / r["methods"]["regional"]["delivered_ms"] for r in rows]
    return dict(median_query_ms=costs, median_paired_delivery_ratio=median(ratios),
                min_paired_delivery_ratio=min(ratios), max_paired_delivery_ratio=max(ratios),
                windows_faster_than_regional=sum(x < 1 for x in ratios))


def summarize(rows):
    result = {}
    for arm in ("both", "AB", "BA"):
        by_arm = [r for r in rows if arm == "both" or r["arm"] == arm]
        result[arm] = {}
        for group in ("all", "1", "4", "8", "yes", "no"):
            if group == "all":
                sample = by_arm
            elif group in ("yes", "no"):
                sample = [r for r in by_arm if (r["first_frame"] is not None) == (group=="yes")]
            else:
                sample = [r for r in by_arm if r["horizon"] == int(group)]
            if not sample:
                result[arm][group] = {"windows": 0}
                continue
            result[arm][group] = dict(windows=len(sample),t91_direct=sum(r["t91_direct"] for r in sample),
                                      methods={m:method_summary(sample,m) for m in METHODS})
    return result


def score(capture_dir, reference_dir, reference_file):
    path = capture_dir/"CAPTURE.json"
    cap = read(path)
    check(cap["status"] == "validated" and not cap["errors"], "failed capture")
    check(tuple(cap["methods"]) == METHODS and cap["repeats"] == len(METHODS), "schedule differs")
    reference = read(reference_file)
    rows = []
    traces = {}
    for arm in ("AB", "BA"):
        shot = cap["arms"][arm]
        expected = reference["shots"][arm]
        check(shot["verified_frames"] == 360 and shot["endpoint"] == expected["end"], "native continuation")
        check(all(shot["cut_hashes"][str(c["frame"])]==c["native_hash"] for c in expected["cuts"]), "native cut")
        traces[arm] = read(reference_dir/f"{arm}-trace.json.gz")
    for qi, query in enumerate(cap["queries"]):
        arm, cut, h = (query[k] for k in ("arm","cut","horizon"))
        shell = set(cap["arms"][arm]["shell_ids"])
        first, ids = None, set()
        for frame in traces[arm][cut:cut+h]:
            ids = shell.intersection(frame["new_ids"])
            if ids:
                first = frame["frame"]
                break
        check((first, sorted(ids)) == (query["first_frame"], sorted(query["expected_ids"])), "expected witnesses")
        by_method = {m:[] for m in METHODS}
        for k, trial in enumerate(query["trials"]):
            rep, ordinal = divmod(k,len(METHODS))
            method = METHODS[(rep+ordinal+qi)%len(METHODS)]
            check(trial["rep"] == rep and trial["method"] == method, "order")
            check(trial["yes"] == bool(ids) and trial["first_frame"] == first, "boolean/frame")
            check(trial["witness"] in ids if ids else trial["witness"] is None, "witness")
            check(all(trial[b]>=0 for b in BINS) and trial["delivered_ms"]>0, "time")
            if rep:
                by_method[method].append(trial)
        check(all(len(t)==len(METHODS) for t in by_method.values()), "repetitions")
        result = {}
        for name, trials in by_method.items():
            row = {k:median(t[k] for t in trials) for k in BINS}
            row["min_delivered_ms"] = min(t["delivered_ms"] for t in trials)
            row["max_delivered_ms"] = max(t["delivered_ms"] for t in trials)
            row["observed_witnesses"] = sorted({t["witness"] for t in trials if t["witness"] is not None})
            counts=trials[0].get("terminal_counts")
            check(all(t.get("terminal_counts")==counts for t in trials), "nondeterministic field counters")
            if counts is not None:
                row["terminal_counts"]=counts
            result[name] = row
        t91 = by_method["t91"]
        direct = all(t["prefix_steps"]==0 for t in t91)
        check(direct or all(t["prefix_steps"]>0 for t in t91), "nondeterministic predicate")
        rows.append(dict(arm=arm,cut=cut,horizon=h,first_frame=first,t91_direct=direct,methods=result))
    check(len({(r["arm"],r["cut"],r["horizon"]) for r in rows})==len(rows)==18,"query count")
    return dict(schema="t90-delivered-regional-v1",capture_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                summary=summarize(rows),windows=rows)


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("asset",choices=("firewoods","dead-tree"))
    a=p.parse_args()
    reference=HERE.parent/("t86-ignition-margin/public" if a.asset=="firewoods" else "t92-transfer-workload/evidence")
    output=HERE/"evidence"/a.asset
    result=score(output,reference,reference/"capture-report.json")
    (output/"SCORE.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    print(json.dumps(result["summary"]["both"]["all"],indent=2))
