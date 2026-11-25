"""Recompute paired prefix costs and check the saved gas/material audits."""
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent / "t94-resumable-gas-query/evidence"
PAIR = (("slice-rank","rank-only"), ("slice-regional","regional"))


def process(directory):
    data = json.loads((directory / "CAPTURE.json").read_bytes())
    assert data["status"] == "validated" and not data["errors"]
    checks = {}
    audit = dict(qualified_cut_horizons=0, matched_nonterminal_frames=0, full_particle_comparisons=0,
                 particle_field_comparisons=0, recipient_state_comparisons=0, ordered_offer_comparisons=0,
                 verified_early_event_cuts=0)
    for arm, shot in data["arms"].items():
        for cut, receipt in shot["resume_checks"].items():
            diag = receipt["slice"]
            assert diag["cut"] == int(cut)
            for test in diag["checks"]:
                checks[arm, int(cut), test["h"]] = test["qualified"]
                audit["qualified_cut_horizons"] += test["qualified"]
            for frame in diag["frames"]:
                audit["matched_nonterminal_frames"] += 1
                audit["full_particle_comparisons"] += frame["particles"]
                audit["particle_field_comparisons"] += frame["particle_fields"]
                audit["recipient_state_comparisons"] += frame["recipient_states"]
                audit["ordered_offer_comparisons"] += frame["ordered_offers"]
            audit["verified_early_event_cuts"] += diag["event"] is not None
    windows = []
    for q in data["queries"]:
        key = (q["arm"],q["cut"],q["horizon"])
        safe = checks.get(key,False)
        times = {}
        for name in {m for pair in PAIR for m in pair}:
            reps = [r for r in q["trials"] if r["method"] == name and r["rep"] > 0]
            assert len(reps) == 9
            for r in reps:
                assert r["first_frame"] == q["first_frame"]
                assert (r["witness"] in q["expected_ids"]) if q["expected_ids"] else r["witness"] is None
                if name.startswith("slice"):
                    assert r["plan_active"] == safe
            times[name] = median(r["delivered_ms"] for r in reps)
        windows.append(dict(arm=q["arm"],cut=q["cut"],horizon=q["horizon"],safe=safe,
                            first_frame=q["first_frame"],median_delivered_ms=times))
    groups = dict(all=windows,guarded=[w for w in windows if w["safe"]],
                  unguarded_multistep=[w for w in windows if w["horizon"]>1 and not w["safe"]])
    for h in (1,4,8):
        groups[f"h{h}"] = [w for w in windows if w["horizon"]==h]
    groups["positive"] = [w for w in windows if w["first_frame"] is not None]
    groups["negative"] = [w for w in windows if w["first_frame"] is None]
    summaries = {}
    for group, rows in groups.items():
        pairs = {}
        for candidate, control in PAIR:
            if not rows:
                continue
            xx = [w["median_delivered_ms"] for w in rows]
            pairs[candidate]=dict(control=control, median_ms=median(x[candidate] for x in xx),
                                   control_ms=median(x[control] for x in xx),
                                   median_ratio=median(x[candidate]/x[control] for x in xx),
                                   faster=sum(x[candidate]<x[control] for x in xx))
        summaries[group]=dict(n=len(rows),methods=pairs)
    return dict(audit=audit,summary=summaries,windows=windows)


if __name__ == "__main__":
    result = {asset: process(BENCH/asset) for asset in ("firewoods","dead-tree")}
    (HERE/"SCORE.json").write_text(json.dumps(result,indent=2)+"\n")
    for asset,r in result.items():
        print(asset,r["audit"],r["summary"]["all"])
