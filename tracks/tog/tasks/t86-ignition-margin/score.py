"""Score saved predictions against future native events, using only public data."""
import gzip
import hashlib
import json
from pathlib import Path
from statistics import median


HERE = Path(__file__).resolve().parent
PUBLIC = HERE / "public"
METHODS = ("global", "support", "uniform", "weighted")
CUTS = (210, 240, 300)
HORIZONS = (1, 4, 8)
ARMS = ("AB", "BA")


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def check(ok, what):
    if not ok:
        raise ValueError(what)


def tally(group, lit, safe):
    certified = group & safe
    events = group & lit
    return dict(eligible=len(group), ignited=len(events), certified=len(certified),
                false_certificates=len(events & certified), abstentions=len(group - safe),
                ignitions_among_abstentions=len(events - safe))


def score():
    source = HERE / "PREDICTIONS.json.gz"
    prediction = read(source)
    costs = read(HERE / "COSTS.json")
    report = read(PUBLIC / "capture-report.json")
    check(report["status"] == "validated", "reference validation missing")
    queries = {(q["arm"], q["cut"], q["horizon"]): q for q in prediction["queries"]}
    check(len(queries) == len(prediction["queries"]) == 18, "duplicate or missing queries")
    times = {(c["arm"], c["cut"]): c for c in costs["cuts"]}
    results = []
    for arm in ARMS:
        frames = read(PUBLIC / f"{arm}-trace.json.gz")
        check([r["frame"] for r in frames] == list(range(1, 361)), "frame index")
        for cut in CUTS:
            snap = read(PUBLIC / f"{arm}-{cut}-eligibility.json.gz")
            n = len(snap["state"])
            check(n == len(snap["fuel"]) == len(snap["heat"]) == 34687, "site counts")
            eligible = {i for i, (s, f) in enumerate(zip(snap["state"], snap["fuel"])) if s == 0 and f > 0}
            warm = {i for i in eligible if snap["heat"][i] > 0}
            near = {i for i in eligible if snap["heat"][i] >= snap["threshold"]/2}
            groups = {"all": eligible, "positive": warm, "half_threshold": near}
            previous = {}
            for horizon in HORIZONS:
                q = queries[arm, cut, horizon]
                future = frames[cut:cut+horizon]
                ids = [i for row in future for i in row["new_ids"]]
                lit = set(ids)
                check(len(lit) == len(ids) and lit <= eligible, "onsets or eligibility")
                check(q["eligible"] == len(eligible) and q["initially_burning"] == snap["state"].count(1),
                      "prediction denominators")
                masks = {m: set(q["certified"][m]) for m in METHODS}
                native_ms = sum(row["step_ms"] for row in future)
                check(native_ms > 0, "native step timer")
                r = dict(arm=arm, cut=cut, horizon=horizon, native_ms=native_ms,
                         native_to_cut_ms=sum(row["step_ms"] for row in frames[:cut]),
                         persistence_false=len(lit), methods={})
                c = times[arm, cut]
                for m, safe in masks.items():
                    check(safe <= eligible and sorted(safe) == q["certified"][m], "invalid prediction IDs")
                    check(not previous or safe <= previous[m], "all-scan prediction expanded over time")
                    compute_ms = 1000 * c["compute_prefix"][m][str(horizon)]
                    fallback_ms = native_ms if eligible - safe else 0.0
                    r["methods"][m] = dict(
                        strata={g: tally(group, lit, safe) for g, group in groups.items()},
                        extra_over_support=len(safe - masks["support"]),
                        lost_vs_support=len(masks["support"] - safe),
                        extra_over_uniform=len(safe - masks["uniform"]),
                        lost_vs_uniform=len(masks["uniform"] - safe),
                        compute_ms=compute_ms, fallback_required=bool(eligible-safe),
                        compute_plus_fallback_ms=compute_ms+fallback_ms)
                results.append(r)
                previous = masks
    summaries = {}
    for arm in (*ARMS, "both"):
        rows = [r for r in results if arm == "both" or r["arm"] == arm]
        methods = {}
        for m in METHODS:
            rs = [r["methods"][m] for r in rows]
            strata = {}
            for g in rs[0]["strata"]:
                strata[g] = {key: sum(x["strata"][g][key] for x in rs) for key in rs[0]["strata"][g]}
            methods[m] = dict(strata=strata, fallback_windows=sum(x["fallback_required"] for x in rs),
                              compute_ms_median=median(x["compute_ms"] for x in rs),
                              compute_plus_fallback_ms_median=median(x["compute_plus_fallback_ms"] for x in rs),
                              paired_cost_ratio_median=median(x["compute_plus_fallback_ms"]/r["native_ms"]
                                                              for x, r in zip(rs, rows)))
        summaries[arm] = dict(windows=len(rows), native_ms_median=median(r["native_ms"] for r in rows), methods=methods)
    return dict(schema="t86-event-score-v1", predictions_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                units="Repeated material-site queries. Timing medians are per window. Hybrid costs add separately measured components and exclude preparation, packing and I/O.",
                summary=summaries, windows=results)


if __name__ == "__main__":
    output = score()
    (HERE / "SCORE.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf8")
    print(json.dumps(output["summary"]["both"], indent=2))
