"""Score causal witnesses and the exact native fallback on the registered shell."""
import gzip
import hashlib
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
T86 = HERE.parent/"t86-ignition-margin"
T87 = HERE.parent/"t87-stroke-halo"


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix==".gz" else data)


def require(condition, issue):
    if not condition:
        raise ValueError(issue)


def index(items, keys):
    rows = {tuple(row[k] for k in keys):row for row in items}
    require(len(rows) == len(items), "duplicate rows")
    return rows


def score():
    positive = read(HERE/"PREDICTIONS.json.gz")
    costs = read(HERE/"COSTS.json")
    registered = read(T87/"PREDICTIONS.json.gz")
    require(registered["shell_ids"] == positive["shell_ids"] and registered["inputs"] == positive["inputs"],
            "registered membership or causal inputs changed")
    key = ("arm","cut","horizon")
    prior = index(read(T87/"SCORE.json")["queries"], key)
    causal = index(positive["queries"], key)
    times = index(costs["queries"],key)
    cut_times = index(costs["cuts"],("arm","cut"))
    require(len(prior) == len(causal) == len(times) == 18, "expected 18 queries")
    rows = []
    for arm in ("AB","BA"):
        shell = set(positive["shell_ids"][arm])
        trace = read(T86/"public"/f"{arm}-trace.json.gz")
        require([r["frame"] for r in trace] == list(range(1,361)), "native frame order")
        for cut in (210,240,300):
            snap = read(T86/"public"/f"{arm}-{cut}-eligibility.json.gz")
            eligible = {i for i in shell if snap["state"][i]==0 and snap["fuel"][i]>0}
            decode = 1000*cut_times[arm,cut]["read_hash_decode_validate"]
            for h in (1,4,8):
                q, old, timer = (data[arm,cut,h] for data in (causal,prior,times))
                require(q["eligible"] == len(eligible) == old["eligible"], "eligibility changed")
                window = trace[cut:cut+h]
                onsets = {i:frame["frame"] for frame in window for i in eligible.intersection(frame["new_ids"])}
                first = min(onsets.values(),default=None)
                native = sum(s["step_ms"] for s in window[:first-cut if first else h])
                require(first == old["first_ignition_frame"] and native == old["native_first_event_or_end_ms"],
                        "T87 native timing or reference changed")
                row = dict(arm=arm,cut=cut,horizon=h,eligible=len(eligible),first_regional_event=first,
                           native_first_event_or_end_ms=native,cut_read_hash_decode_validate_ms=decode,
                           methods={})
                for method in ("residual","graph"):
                    witness = q[method]
                    actual = None
                    if witness is not None:
                        i, due = witness["id"],witness["deadline"]
                        actual = onsets.get(i)
                        require(actual is not None and cut < actual <= due <= cut+h, "false witness")
                    compute = 1000*(timer["prepare_roi_and_residual"] +
                                    (timer["graph_extra"] if method=="graph" else 0))
                    fallback = native if witness is None else 0
                    loaded = compute + fallback
                    row["methods"][method] = dict(witness=witness,actual_witness_frame=actual,
                        compute_including_prepare_ms=compute,exact_fallback_ms=fallback,
                        loaded_plus_fallback_ms=loaded,file_plus_fallback_ms=loaded+decode,
                        cold_including_two_shells_plus_fallback_ms=loaded+decode+1000*costs["shared_geometry_two_shells"])
                rows.append(row)
    summaries = {}
    for arm in ("AB","BA","both"):
        sample = [r for r in rows if arm=="both" or r["arm"]==arm]
        positives = sum(r["first_regional_event"] is not None for r in sample)
        summary = dict(queries=len(sample),true_yes=positives,true_no=len(sample)-positives,
            native_ms_median=median(r["native_first_event_or_end_ms"] for r in sample),methods={})
        for method in ("residual","graph"):
            ms = [r["methods"][method] for r in sample]
            yes = sum(v["witness"] is not None for v in ms)
            summary["methods"][method] = dict(issued_yes=yes,false_yes=0,missed_true_yes=positives-yes,
                fallen_back=len(sample)-yes,ms_including_prepare_median=median(v["compute_including_prepare_ms"] for v in ms),
                loaded_plus_fallback_ms_median=median(v["loaded_plus_fallback_ms"] for v in ms),
                paired_loaded_ratio_median=median(v["loaded_plus_fallback_ms"]/r["native_first_event_or_end_ms"]
                                                  for r,v in zip(sample,ms)),
                paired_file_ratio_median=median(v["file_plus_fallback_ms"]/r["native_first_event_or_end_ms"]
                                                for r,v in zip(sample,ms)))
        summaries[arm] = summary
    return {"schema":"t88-positive-witness-score-v1", "predictions_sha256":
        hashlib.sha256((HERE/"PREDICTIONS.json.gz").read_bytes()).hexdigest(),"summary":summaries,"queries":rows}


if __name__ == "__main__":
    report = score()
    (HERE/"SCORE.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    print(json.dumps(report["summary"]["both"],indent=2))
