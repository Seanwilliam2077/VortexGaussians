"""Check full physical continuation and estimate conditional keep/discard costs."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean, median

HERE = Path(__file__).resolve().parent
MODES = ("ordinary-discard", "slice-discard", "ordinary-keep", "slice-keep")


def require(ok, text):
    if not ok:
        raise ValueError(text)


def regime(discard, keep):
    if discard == keep:
        return {"pattern": "tie" if keep == 0 else ("slice-always" if keep < 0 else "ordinary-always")}
    crossing = discard / (discard - keep)
    if 0 <= crossing <= 1:
        return {"pattern": "slice-below" if discard < keep else "slice-above", "crossing": crossing}
    return {"pattern": "slice-always" if discard < 0 else "ordinary-always"}


def read(p):
    return json.loads(p.read_bytes())


def score(asset):
    path = HERE / "evidence" / asset / "CAPTURE.json"
    cap = read(path)
    require(cap["status"] == "validated" and not cap["errors"] and
            tuple(cap["methods"]) == MODES and cap["repeats"] == 4, "Registered schedule")
    targets = {q["arm"]: q for q in read(HERE.parent / "t98-edit-to-answer/REFERENCE.json")["queries"]
               if q["asset"] == asset and q["horizon"] == 60}
    output = []
    for qi, q in enumerate(cap["queries"]):
        arm = q["arm"]
        ref = targets.pop(arm)
        frame = ref["first_frame"] or 240
        audit = cap["arms"][arm]["keep_audit"]
        require(len(audit["rows"]) == 2 and cap["arms"][arm]["verified_frames"] == 360, "Independent trajectories")
        for a in audit["rows"]:
            require(a["decision_frame"] == frame and a["commit_frame"] == frame + 1 and
                    a["cross_hash"] == audit["reference_cross_hash"] and
                    a["next_hash"] == audit["reference_next_hash"], "Two complete matching states")
        records = {m: [] for m in MODES}
        for i, t in enumerate(q["trials"]):
            rep, j = divmod(i, len(MODES))
            m = MODES[(j + rep + qi) % len(MODES)]
            require(t["method"] == m and t["rep"] == rep and t["decision_frame"] == frame and
                    t["first_frame"] == ref["first_frame"] and t["yes"] == bool(ref["ids"]) and
                    (t["witness"] in ref["ids"] if ref["ids"] else t["witness"] is None), "Native event answer")
            keep = m.endswith("-keep")
            require(t["keep"] == keep and t["committed_frame"] == (frame + 1 if keep else None), "Action")
            require(abs(t["delivered_ms"] - t["preview_delivered_ms"] - t["action_delivered_ms"]) < 1e-5,
                    "Two delivered actions")
            work = t["work"]
            require(work["ordinary_steps"] + work["sliced_steps"] + work["terminal"] == ref["observed_steps"],
                    "No duplicated gas prefix")
            if m.startswith("ordinary"):
                require(not work["sliced_steps"] and not work["repaired_steps"], "Ordinary one-pass control")
            elif keep:
                require(work["repaired_steps"] == work["sliced_steps"], "Exact reconstruction")
            if rep:
                records[m].append(t)
        summary = {}
        for m, rows in records.items():
            require(len(rows) == 4, "Missing measured wave")
            summary[m] = {k: median(t[k] for t in rows) for k in ("delivered_ms", "preview_delivered_ms",
                            "action_delivered_ms", "preview_ms", "action_ms")}
            summary[m]["range_ms"] = [min(t["delivered_ms"] for t in rows), max(t["delivered_ms"] for t in rows)]
            summary[m]["work"] = rows[0]["work"].copy()
            for k in summary[m]["work"]:
                if k.endswith("_ms"):
                    summary[m]["work"][k] = median(t["work"][k] for t in rows)
                else:
                    require(all(t["work"][k] == rows[0]["work"][k] for t in rows), "Deterministic prefix work")
            summary[m]["anchor_validation_ms"] = median(t["active_stats"]["anchor_validation_ms"] for t in rows)
        for backend in ("ordinary", "slice"):
            for k in ("ordinary_steps", "sliced_steps", "guards", "allocated_log_bytes", "logged_samples", "terminal"):
                require(summary[backend + "-discard"]["work"][k] == summary[backend + "-keep"]["work"][k],
                        "Preview used an unknown keep/discard action")
        def deltas(reducer):
            times = {m: reducer([t["delivered_ms"] for t in records[m]]) for m in MODES}
            return [times["slice-" + a] - times["ordinary-" + a] for a in ("discard", "keep")]
        waves = [deltas(lambda ts: ts[i]) for i in range(4)]
        d, k = deltas(median)
        # Both preview paths return to the host before the keep action exists.
        # Pool the two preview-time samples within a backend as a sensitivity check.
        common = {backend: median([t["preview_delivered_ms"] for action in ("discard", "keep")
                                  for t in records[backend + "-" + action]]) for backend in ("ordinary", "slice")}
        shared_deltas = [common["slice"] - common["ordinary"] + summary["slice-" + action]["action_delivered_ms"] -
                         summary["ordinary-" + action]["action_delivered_ms"] for action in ("discard", "keep")]
        work = summary["slice-discard"]["work"]
        pending = work["sliced_steps"] - work["repaired_steps"]
        bytes_per_step = work["allocated_log_bytes"] // work["sliced_steps"] if work["sliced_steps"] else 0
        require(bytes_per_step * work["sliced_steps"] == work["allocated_log_bytes"], "Fixed log allocation")
        answer = {"arm": arm, "first": ref["first_frame"], "frame": frame, "methods": summary, "audit": audit,
                  "slice_pending_log_steps_at_decision": pending,
                  "slice_additional_typed_bytes_at_decision": pending * bytes_per_step + (work["peak_held_heat_bytes"] if pending else 0),
                  "median_deltas_ms": [d, k], "conditional_median_cost_regime": regime(d, k),
                  "common_preview_sensitivity": {"median_ms": common, "deltas_ms": shared_deltas,
                                                 **regime(*shared_deltas)},
                  "conditional_mean_cost_regime": regime(*deltas(mean)), "matched_waves": [
                      {"delta_ms": row, **regime(*row)} for row in waves]}
        output.append(answer)
    require(not targets and len(output) == 2, "Four development edits across both assets")
    return {"asset": asset, "capture_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "queries": output}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("asset", choices=("firewoods", "dead-tree"))
    asset = ap.parse_args().asset
    result = score(asset)
    (HERE / "evidence" / asset / "SCORE.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    for q in result["queries"]:
        print(q["arm"], q["median_deltas_ms"], q["conditional_median_cost_regime"], q["matched_waves"])

