"""Check reference, branch identities, all four query methods and their full delivery cost."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median

from reference import compute, read

HERE=Path(__file__).resolve().parent
METHODS=("active-anchor","restart-active","repair-active","active-fresh")
BINS=("delivered_ms","click_ms","shell_index_ms","fork_ms","compute_ms","restore_ms","total_browser_ms")
LOG=("guards","ordinary_steps","sliced_steps","logged_samples","allocated_log_bytes","max_live_log_bytes",
     "repairs","repair_steps","restart")


def check(condition,label):
    if not condition:
        raise ValueError(label)


def parts(context):
    return parts(context["prefix"])+parts(context["replay"]) if "prefix" in context else [context]


def score(timing_dir):
    reference=compute()
    check(reference==read(HERE/"REFERENCE.json"),"independent reference changed")
    native=read(HERE/"evidence/native/capture-report.json")
    for f in native["files"]:
        raw=(HERE/"evidence/native"/f["name"]).read_bytes()
        check(hashlib.sha256(raw).hexdigest()==f["sha256"],"native trace file")
    capture_path=timing_dir/"CAPTURE.json"
    cap=read(capture_path)
    check(cap["status"]=="validated" and not cap["errors"],"capture failed")
    check(cap["methods"]==list(METHODS) and cap["repeats"]==4,"method schedule")
    check(len(cap["queries"])==2,"query count")
    static=read(HERE/"selection-ids.json.gz")
    out=[]
    for i,(q,e) in enumerate(zip(cap["queries"],reference["queries"])):
        arm=e["arm"]; shot=cap["arms"][arm]; exact=native["shots"][arm]
        check(shot["verified_frames"]==360 and shot["endpoint"]==exact["end"],"unbranched state")
        check(shot["cut_hashes"]=={str(c["frame"]):c["native_hash"] for c in exact["cuts"]},"cut hash")
        check(shot["shell_ids"]==static,"registered sphere")
        check(shot["post_click_eligible"]["count"]==e["eligible"],"eligible site count")
        check((q["arm"],q["cut"],q["horizon"],q["first_frame"],q["expected_ids"])==
              (arm,180,180,e["first_frame"],e["ids"]),"query or reference changed")
        audits=shot["active_audit"]["runs"]
        check(shot["active_audit"]["frames"]==8 and [r["anchor_built"] for r in audits]==[None,False,True,False],
              "full-state audit")
        check(all(r["matched_material_and_frontier_values"]>0 and r["matched_particle_fields"]>0 for r in audits[1:]),
              "native compared fields")
        for audit in shot["repair_audits"]:
            check(all(audit[k]==v for k,v in audit["active_backend"].items()),"same repair with two graph backends")
            if audit["status"]=="event_before_expiry":
                check(audit["event"]==e["first_frame"] and audit["witness"] in e["ids"],"audit witness")
        record=dict(arm=arm,eligible=e["eligible"],first=e["first_frame"],ties=len(e["ids"]),warm_builds=[],methods={})
        rows={m:[] for m in METHODS}
        for j,t in enumerate(q["trials"]):
            rep,ordn=divmod(j,len(METHODS))
            method=METHODS[(rep+ordn+i)%len(METHODS)]
            check(t["rep"]==rep and t["method"]==method,"rotation")
            check(t["yes"]==bool(e["ids"]) and t["first_frame"]==e["first_frame"],"truth")
            check(t["witness"] in e["ids"] if e["ids"] else t["witness"] is None,"witness")
            check(t["clicked"]==exact["edit"]["count"] and all(t[b]>=0 for b in BINS),"click and stage timings")
            if method in ("active-anchor","active-fresh"):
                check(t["prefix_steps"]==e["observed_steps"],"ordinary stops at first outcome")
            for ctx in parts(t["active_stats"]):
                if ctx["anchor_built"]:
                    record["warm_builds"].append({k:ctx[k] for k in ("anchor_build_ms","anchor_bytes","anchor_cells","anchor_donors","anchor_edges")}|{"method":method,"rep":rep})
            if rep: rows[method].append(t)
        check(len(q["trials"])==20,"missing samples")
        for m,times in rows.items():
            r={k:median(t[k] for t in times) for k in BINS}
            r["delivered_range_ms"]=[min(t["delivered_ms"] for t in times),max(t["delivered_ms"] for t in times)]
            r["query_step_evaluations"]=times[0]["prefix_steps"]
            r["graph_work"]={k:median(sum(p[k] for p in parts(t["active_stats"])) for t in times) for k in
                ("fresh_indexed","fresh_index_ms","anchor_validation_ms","local_rows_built","local_edges_built","copied_rows","pruned_edges","branch_bytes")}
            if times[0]["repair_stats"] is not None:
                stable={k:times[0]["repair_stats"][k] for k in LOG}
                check(all(t["repair_stats"][k]==v for t in times for k,v in stable.items()),"nondeterministic repair")
                r["recovery"]=stable
                r["repair_ms"]=median(t["repair_stats"]["repair_ms"] for t in times)
            record["methods"][m]=r
        anchor=record["methods"]["active-anchor"]["delivered_ms"]
        record["paired_delivery_to_ordinary_anchor"]={m:r["delivered_ms"]/anchor for m,r in record["methods"].items()}
        out.append(record)
    return dict(capture_sha256=hashlib.sha256(capture_path.read_bytes()).hexdigest(),whole_profile_ms=cap["phases_ms"]["wall_before_receipt"],queries=out)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timing-dir",type=Path,help="Score a separately regenerated capture")
    args=parser.parse_args()
    out=score(args.timing_dir or HERE/"evidence/timing")
    destination=(args.timing_dir or HERE)/"SCORE.json"
    destination.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    for q in out["queries"]: print(q["arm"],q["first"],q["paired_delivery_to_ordinary_anchor"])
