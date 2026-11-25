"""Audit the paired click-to-answer repair measurements using public reference onsets."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median

HERE=Path(__file__).resolve().parent
METHODS=("asset-cache","active-fresh","active-anchor","restart-cache","repair-cache","restart-active","repair-active")
LATENCY=("delivered_ms","total_browser_ms","click_ms","shell_index_ms","fork_ms","compute_ms","restore_ms")
DECISIONS=("guards","ordinary_steps","sliced_steps","repairs","repair_steps","restart",
           "logged_samples","allocated_log_bytes","max_live_log_bytes")


def check(ok,label):
    if not ok:
        raise ValueError(label)


def read(path):
    return json.loads(path.read_bytes())


def score(asset,targets=None,native_path=None,capture_dir=None):
    folder=capture_dir or HERE/"evidence"/asset
    f=folder/"CAPTURE.json"
    cap=read(f)
    check(cap["status"]=="validated" and not cap["errors"],"invalid capture")
    check(tuple(cap["methods"])==METHODS and cap["repeats"]==7,"schedule")
    reference=read(targets or HERE.parent/"t98-edit-to-answer/REFERENCE.json")["queries"]
    expected={(q["arm"],q["horizon"]):q for q in reference if q["asset"]==asset}
    native_path=native_path or HERE.parent/("t86-ignition-margin/public" if asset=="firewoods" else "t92-transfer-workload/evidence")
    native=read(native_path/"capture-report.json")
    audits=[]
    for arm in ("AB","BA"):
        shot=cap["arms"][arm]
        check(shot["verified_frames"]==360 and shot["endpoint"]==native["shots"][arm]["end"],"native continuation")
        active_runs=shot["active_audit"]["runs"]
        check(shot["active_audit"]["frames"]==8 and
              [run["method"] for run in active_runs]==["native","active-fresh","active-anchor","active-anchor"],"active audit arms")
        check([run["anchor_built"] for run in active_runs]==[None,False,True,False],"cold/warm audit")
        check(all(run["matched_particles"]>0 and run["matched_material_and_frontier_values"]>0
                  for run in active_runs[1:]),"complete active comparison")
        for a in shot["repair_audits"]:
            active=a["active_backend"]
            check(all(a[k]==v for k,v in active.items()),"backends disagree at causal boundary")
            if a["status"]=="event_before_expiry" and a["cut"]==180:
                ref=expected[arm,180]
                check(a["event"]==ref["first_frame"] and a["witness"] in ref["ids"],"early audit")
            elif a["status"]=="matched_expiry_and_continuation":
                check(a["repair_frame"]==a["cut"]+a["length"] and len(a["repair_hash"])==8 and
                      len(a["next_hash"])==8 and a["sample_count"]>0,"repair audit")
            audits.append(dict(arm=arm,**a))
    if asset=="firewoods":
        check(any(a["arm"]=="AB" and a["cut"]==210 and a["status"]=="matched_expiry_and_continuation" for a in audits),
              "development natural expiry")
    queries=[]
    cold_builds=[]
    for n,q in enumerate(cap["queries"]):
        e=expected[q["arm"],q["horizon"]]
        check(e["first_frame"]==q["first_frame"] and e["ids"]==q["expected_ids"],"reference labels")
        ts={m:[] for m in METHODS}
        warmup={}
        for k,t in enumerate(q["trials"]):
            rep,ordinal=divmod(k,len(METHODS))
            m=METHODS[(n+rep+ordinal)%len(METHODS)]
            check(m==t["method"] and rep==t["rep"],"paired order")
            check(t["yes"]==(e["first_frame"] is not None) and t["first_frame"]==e["first_frame"] and
                  (t["witness"] in e["ids"] if t["yes"] else t["witness"] is None),"regional answer")
            check(t["clicked"]==native["shots"][q["arm"]]["edit"]["count"],"fresh edit")
            check(all(t[x]>=0 for x in LATENCY) and t["delivered_ms"]>0,"timing")
            active=t["active_stats"]
            if active is not None:
                contexts=[active["prefix"],active["replay"]] if "prefix" in active else [active]
                check(all(s["bytes"]==s["anchor_bytes"]+s["branch_bytes"] for s in contexts),"cache byte accounting")
                for ctx in contexts:
                    if ctx["anchor_built"]:
                        cold_builds.append(dict(arm=q["arm"],horizon=q["horizon"],method=m,rep=rep,
                                                build_ms=ctx["anchor_build_ms"],anchor_bytes=ctx["anchor_bytes"],
                                                delivered_ms=t["delivered_ms"]))
            if rep:
                ts[m].append(t)
            else:
                warmup[m]={key:t[key] for key in ("delivered_ms","cache_build","active_stats")}
        result={}
        for m,records in ts.items():
            check(len(records)==7,"repetitions")
            r={name:median(x[name] for x in records) for name in LATENCY}
            # The last rank-only terminal may evaluate a subset of gas velocities.
            r["query_step_evaluations"]=records[0]["prefix_steps"]
            check(all(t["prefix_steps"]==r["query_step_evaluations"] for t in records),"physical steps")
            r["warmup"]=warmup[m]
            if m.startswith(("restart-","repair-")):
                st=records[0]["repair_stats"]
                r["decisions"]={k:st[k] for k in DECISIONS}
                check(all(all(t["repair_stats"][k]==st[k] for k in DECISIONS) for t in records),"guard or accounting")
                r["guard_ms"]=median(t["repair_stats"]["guard_ms"] for t in records)
                r["repair_ms"]=median(t["repair_stats"]["repair_ms"] for t in records)
            result[m]=r
        queries.append({"arm":q["arm"],"horizon":q["horizon"],"first":q["first_frame"],"methods":result})
    check({(q["arm"],q["horizon"]) for q in queries}==set(expected) and len(queries)==len(expected),"queries")
    check([b["arm"] for b in cold_builds]==["AB","BA"] and all(b["rep"]==0 for b in cold_builds),"asset cold builds")
    summary={}
    for method in METHODS:
        c=[q["methods"][method]["delivered_ms"] for q in queries]
        summary[method]={"delivered_ms":median(c)}
        for base in METHODS:
            ratios=[m/q["methods"][base]["delivered_ms"] for m,q in zip(c,queries)]
            summary[method]["vs_"+base]={"median":median(ratios),"min":min(ratios),"max":max(ratios)}
    return dict(capture_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),audits=audits,cold_builds=cold_builds,
                active_audits={k:v["active_audit"] for k,v in cap["arms"].items()},
                setup_ms={k:v["phases_ms"] for k,v in cap["arms"].items()},
                measured_calls=len(queries)*len(METHODS)*7,warmup_calls=len(queries)*len(METHODS),
                summary=summary,queries=queries)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("asset")
    p.add_argument("--targets",type=Path)
    p.add_argument("--native-dir",type=Path)
    p.add_argument("--capture-dir",type=Path,help="Fresh native output directory; the score is saved alongside its capture.")
    args=p.parse_args()
    if args.asset not in ("firewoods","dead-tree") and not(args.targets and args.native_dir):
        p.error("external assets require --targets and --native-dir")
    out=score(args.asset,args.targets,args.native_dir,args.capture_dir)
    folder=args.capture_dir or HERE/"evidence"/args.asset
    (folder/"SCORE.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf8")
    print(json.dumps(out["summary"],indent=2))
