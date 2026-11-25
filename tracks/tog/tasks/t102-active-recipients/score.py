"""Account for the ordinary active-recipient backend in the joint edit-to-answer captures."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
TIMED = ("asset-cache", "active-fresh", "active-anchor", "repair-active", "restart-active")
ACTIVE = TIMED[1:]


def require(value, message):
    if not value:
        raise ValueError(message)


def contexts(stats):
    """A restart may charge two active contexts, one on each side of the rewind."""
    if "prefix" in stats:
        return contexts(stats["prefix"]) + contexts(stats["replay"])
    return [stats]


def check_audit(audit):
    runs = audit["runs"]
    require(audit["frames"] == 8 and
            [r["method"] for r in runs] == ["native", "active-fresh", "active-anchor", "active-anchor"],
            "Native audit sequence")
    require([r["anchor_built"] for r in runs] == [None, False, True, False], "Rollback/reuse")
    keys = ["matched_particles", "matched_particle_fields", "matched_material_and_frontier_values"]
    for key in keys:
        require(runs[1][key] > 0 and len({r[key] for r in runs[1:]}) == 1, f"Incomplete audit {key}")
    require(runs[2]["preserved_anchor_rows"] == runs[3]["preserved_anchor_rows"] > 0,
            "Unverified anchor")
    return {"frames_per_backend": audit["frames"], "matched_per_backend": {k: runs[1][k] for k in keys},
            "preserved_anchor_rows": runs[2]["preserved_anchor_rows"]}


def score(asset):
    capture = HERE.parent / "t100-material-repair/evidence" / asset / "CAPTURE.json"
    cap = json.loads(capture.read_bytes())
    require(cap["status"] == "validated" and not cap["errors"] and cap["repeats"] == 7, "Joint capture")
    ref_file = (HERE.parent / "t101-playground-holdout/REFERENCE.json"
                if asset == "playground" else HERE.parent / "t98-edit-to-answer/REFERENCE.json")
    ref = json.loads(ref_file.read_bytes())
    targets = {(q["arm"], q["horizon"]): q for q in ref["queries"] if q["asset"] == asset}
    audits = {a: check_audit(shot["active_audit"]) for a, shot in cap["arms"].items()}
    builds, queries = [], []
    for qi, q in enumerate(cap["queries"]):
        tgt = targets.pop((q["arm"], q["horizon"]))
        require(tgt["first_frame"] == q["first_frame"] and tgt["ids"] == q["expected_ids"], "Native labels")
        by_method = {m: [] for m in TIMED}
        for k, t in enumerate(q["trials"]):
            num = len(cap["methods"])
            rep, j = divmod(k, num)
            m = cap["methods"][(qi + rep + j) % num]
            require(m == t["method"] and rep == t["rep"], "Trial order")
            require(t["yes"] == bool(tgt["ids"]) and t["first_frame"] == tgt["first_frame"] and
                    (t["witness"] in tgt["ids"] if t["yes"] else t["witness"] is None), "Exact query")
            if m not in TIMED:
                continue
            if m in ACTIVE:
                parts = contexts(t["active_stats"])
                for s in parts:
                    if s["anchor_built"]:
                        builds.append({"arm": q["arm"], "horizon": q["horizon"], "method": m, "rep": rep,
                                       "first_delivered_ms": t["delivered_ms"], **{
                                           key: s[key] for key in ("anchor_build_ms", "anchor_bytes",
                                               "anchor_cells", "anchor_edges", "anchor_donors", "anchor_indexed")}})
                if m.startswith("active-"):
                    require(t["prefix_steps"] == tgt["observed_steps"], "Regional first-event stop")
            if rep:
                by_method[m].append(t)
        results = {}
        for m, rows in by_method.items():
            require(len(rows) == 7, "Complete balanced repeats")
            results[m] = {"delivered_ms": median(r["delivered_ms"] for r in rows)}
            if m not in ACTIVE:
                continue
            p = [contexts(r["active_stats"]) for r in rows]
            for key in ("anchor_validation_ms", "anchor_build_ms", "fresh_index_ms", "fresh_indexed",
                        "fresh_cells", "local_rows_built", "local_edges_built", "copied_rows", "pruned_edges",
                        "branch_bytes", "branch_resets"):
                results[m][key] = median(sum(st[key] for st in parts) for parts in p)
            results[m]["anchor_bytes"] = median(max(st["anchor_bytes"] for st in parts) for parts in p)
        queries.append({"arm": q["arm"], "horizon": q["horizon"], "first_frame": q["first_frame"],
                        "steps": tgt["observed_steps"], "methods": results})
    require(not targets and len(queries) in (4, 6), "Required distinct queries")
    ratios = {}
    for candidate, base in [("active-fresh", "asset-cache"), ("active-anchor", "asset-cache"),
                            ("active-anchor", "active-fresh"), ("repair-active", "active-anchor"),
                            ("restart-active", "active-anchor")]:
        pairs = [q["methods"][candidate]["delivered_ms"] / q["methods"][base]["delivered_ms"] for q in queries]
        ratios[f"{candidate}/{base}"] = {"median": median(pairs), "range": [min(pairs), max(pairs)]}
    return {"asset": asset, "capture_sha256": hashlib.sha256(capture.read_bytes()).hexdigest(),
            "matched_state_audits": audits, "anchor_builds_observed_across_all_edit_trials": builds,
            "median_query_delivery_ratios": ratios, "queries": queries}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset", choices=("firewoods", "dead-tree", "playground"))
    args = parser.parse_args()
    result = score(args.asset)
    out = HERE / "evidence" / (args.asset + ".json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    print(json.dumps(result["median_query_delivery_ratios"], indent=2))

