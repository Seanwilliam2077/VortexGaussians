"""Check region-only predictions against archived masks, eligibility and native events."""
import gzip
import hashlib
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
T86 = HERE.parent/"t86-ignition-margin"
METHODS = ("support", "uniform", "weighted")


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def check(ok, message):
    if not ok:
        raise ValueError(message)


def index(data, keys):
    result = {tuple(r[k] for k in keys):r for r in data}
    check(len(result) == len(data), "duplicate query")
    return result


def score():
    pred = read(HERE/"PREDICTIONS.json.gz")
    costs = read(HERE/"COSTS.json")
    full = read(T86/"PREDICTIONS.json.gz")
    check(pred["inputs"] == full["inputs"], "T86 inputs differ")
    check(read(T86/"public/capture-report.json")["status"] == "validated", "unvalidated reference")
    key = ("arm", "cut", "horizon")
    ids = index(pred["queries"], key)
    times = index(costs["queries"], key)
    original = index(full["queries"], key)
    ctimes = index(costs["cuts"], ("arm", "cut"))
    rows = []
    for arm in ("AB","BA"):
        shell = set(pred["shell_ids"][arm])
        check(sorted(shell) == pred["shell_ids"][arm], "duplicate/unordered shell ID")
        trace = read(T86/"public"/f"{arm}-trace.json.gz")
        check([r["frame"] for r in trace] == list(range(1,361)), "trace frame order")
        for cut in (210,240,300):
            snap = read(T86/"public"/f"{arm}-{cut}-eligibility.json.gz")
            eligible = {i for i in shell if snap["state"][i] == 0 and snap["fuel"][i] > 0}
            for horizon in (1,4,8):
                q, t, scene = (v[arm,cut,horizon] for v in (ids,times,original))
                check(sorted(eligible) == q["eligible"], "incorrect query population")
                steps = trace[cut:cut+horizon]
                events = [{"frame":s["frame"], "ids":sorted(eligible.intersection(s["new_ids"]))} for s in steps]
                nonempty = [e for e in events if e["ids"]]
                first = nonempty[0]["frame"] if nonempty else None
                stop = first-cut if nonempty else horizon
                native = 0 if not eligible else sum(s["step_ms"] for s in steps[:stop])
                cut_ms = 1000*ctimes[arm,cut]["read_hash_decode"]
                prep_ms = 1000*t["prepare"]
                row = dict(arm=arm, cut=cut, horizon=horizon, shell_size=len(shell), eligible=len(eligible),
                           events=nonempty, first_ignition_frame=first, persistence_correct=not bool(nonempty),
                           native_full_ms=sum(s["step_ms"] for s in steps), native_first_event_or_end_ms=native,
                           cut_read_hash_decode_ms=cut_ms, query_preparation_ms=prep_ms, methods={})
                for method in METHODS:
                    safe = set(q["certified"][method])
                    check(sorted(safe) == q["certified"][method], "duplicate/unordered prediction ID")
                    check(safe == set(scene["certified"][method]) & eligible, "regional restriction mismatch")
                    wrong = sorted(i for event in nonempty for i in event["ids"] if i in safe)
                    check(not wrong, "false regional certificate")
                    decision = "empty" if not eligible else "no" if safe == eligible else "fallback"
                    check(decision != "no" or not nonempty, "false complete no")
                    compute = 1000*t["method"][method]
                    fallback = native if decision == "fallback" else 0
                    loaded = prep_ms + compute + fallback
                    row["methods"][method] = dict(certified=len(safe), false_certified_ids=wrong, decision=decision,
                        compute_ms=compute, exact_native_fallback_ms=fallback, loaded_plus_fallback_ms=loaded,
                        file_to_answer_plus_fallback_ms=cut_ms+loaded,
                        cold_including_all_geometry_plus_fallback_ms=1000*costs["shared_asset_transform_and_two_shells"]+cut_ms+loaded)
                rows.append(row)
    check(len(rows) == len(ids) == len(times) == len(original) == 18, "missing query")
    result = {}
    for arm in ("AB","BA","both"):
        sample = [r for r in rows if arm=="both" or r["arm"]==arm]
        med = lambda xs: median(list(xs))
        s = dict(queries=len(sample), empty=sum(r["eligible"]==0 for r in sample),
                 true_yes=sum(bool(r["events"]) for r in sample),
                 true_no=sum(not bool(r["events"]) for r in sample),
                 persistence_errors=sum(not r["persistence_correct"] for r in sample),
                 native_first_event_or_end_ms_median=med(r["native_first_event_or_end_ms"] for r in sample),
                 methods={})
        for method in METHODS:
            ms = [r["methods"][method] for r in sample]
            s["methods"][method] = dict(preview_no=sum(m["decision"]=="no" for m in ms),
                fallback=sum(m["decision"]=="fallback" for m in ms),
                certified=sum(m["certified"] for m in ms), false_certificates=sum(len(m["false_certified_ids"]) for m in ms),
                loaded_plus_fallback_ms_median=med(m["loaded_plus_fallback_ms"] for m in ms),
                paired_loaded_ratio_median=med(m["loaded_plus_fallback_ms"]/r["native_first_event_or_end_ms"]
                    for m,r in zip(ms,sample) if r["native_first_event_or_end_ms"]>0),
                paired_file_ratio_median=med(m["file_to_answer_plus_fallback_ms"]/r["native_first_event_or_end_ms"]
                    for m,r in zip(ms,sample) if r["native_first_event_or_end_ms"]>0))
        result[arm]=s
    return {"schema":"t87-stroke-halo-check-v1",
            "predictions_sha256":hashlib.sha256((HERE/"PREDICTIONS.json.gz").read_bytes()).hexdigest(),
            "fullscene_predictions_sha256":hashlib.sha256((T86/"PREDICTIONS.json.gz").read_bytes()).hexdigest(),
            "matched_masks":len(rows)*len(METHODS), "summary":result, "queries":rows}


if __name__=="__main__":
    result = score()
    (HERE/"SCORE.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    print(json.dumps(result["summary"],indent=2))
