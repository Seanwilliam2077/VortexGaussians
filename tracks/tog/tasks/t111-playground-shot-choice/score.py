"""Audit each complete single- and dual-camera decision from recorded native trajectories."""
import argparse
import hashlib
import math
from statistics import median
from pathlib import Path

from reference import HERE, build, load

METHODS=("ordinary","restart","repair")
FIELDS=("defined","first_frame","count","mass","total","target","eligible")


def check(ok,reason):
    if not ok: raise ValueError(reason)


def score(directory, *, study=HERE, ground_truth=build, cameras=(0,153), weight_root=None):
    refs=ground_truth()
    check(refs==load(study/"REFERENCE.json"),"recovered native reference")
    expected={(r["arm"][1],r["camera"]):r for r in refs["queries"]}
    source=directory/"CAPTURE.json"; cap=load(source)
    origin=load(study/"evidence/native/capture-report.json")
    traces={a:load(study/"evidence/native"/(a+"-trace.json.gz")) for a in ("AL","AF")}
    shell=set(load(study/"shell.json.gz"))
    weights={c:{i:math.floor(1e6*w+0.5) for i,w in load((weight_root or study)/("weights-"+str(c)+".json.gz"))["eligible_weights"]}
             for c in cameras}
    check(cap["status"]=="validated" and not cap["errors"] and tuple(cap["methods"])==METHODS and cap["repeats"]==3,"run or schedule")
    check(cap["common_parent"]==refs["pre_click"],"parent identity")
    for a,x in cap["arms"].items():
        n=origin["shots"][a]
        check(x["verified_frames"]==360 and x["endpoint"]==n["end"],"ordinary continuation")
        check(x["cut_hashes"]=={str(z["frame"]):z["native_hash"] for z in n["cuts"]},"intermediate checkpoints")
    def verify_view(v,pick):
        c=v["camera"]; e=expected[pick,c]
        check(all(v[k]==e[k] for k in FIELDS),"frame, mass, count or target")
        if v["first_frame"] is not None:
            native=traces["A"+pick][v["first_frame"]-1]
            valid=[i for i in native["new_ids"] if i in shell and weights[c][i]>0]
            check(v["witness"]==min(valid),"positive contributor at this frame")
        else:
            check(v["witness"] is None,"absent witness")
    for pick in ("L","F"):
        audits=cap["full_audits"][pick]
        for m in METHODS:
            for v in audits[m]["views"]:
                verify_view(v,pick);check(v["curve"]==expected[pick,v["camera"]]["curve"],"full 90-step progression")
        check(audits["repair"]["boundaries"]==audits["ordinary"]["boundaries"],"complete repair boundaries")
    scenarios=[[c] for c in cameras]+[list(cameras)]
    check([q["cameras"] for q in cap["queries"]]==scenarios,"registered operations")
    results=[]
    for qi,q in enumerate(cap["queries"]):
        cams=q["cameras"];ts={m:[] for m in METHODS};cold={}
        check(len(q["trials"])==12,"missing action calls")
        choices={}
        unsuccessful=[]
        for c in cams:
            l,f=(expected[a,c] for a in ("L","F"))
            if l["defined"] and l["first_frame"] is None:unsuccessful.append(c)
            choices[str(c)]=("undefined" if not l["defined"] else "L" if l["first_frame"] is not None
                else "undefined" if not f["defined"] else "F" if f["first_frame"] is not None else "none")
        for j,t in enumerate(q["trials"]):
            rep,slot=divmod(j,3);m=METHODS[(rep+slot+qi)%3]
            check(t["rep"]==rep and t["method"]==m and t["choices"]==choices,"rotation or chosen branch")
            check([x["pick"] for x in t["tried"]]==(["L","F"] if unsuccessful else ["L"]),"physical branch short circuit")
            check(0<t["total_browser_ms"]<=t["delivered_ms"]+1,"one host timer")
            builds=[]
            for x in t["tried"]:
                pick=x["pick"]
                check(x["clicked"]==origin["shots"]["A"+pick]["edit"]["count"],"actual painted sites")
                check([v["camera"] for v in x["views"]]==(cams if pick=="L" else unsuccessful),"views still needed")
                check(x["outer_fork_ms"]>=0 and x["outer_restore_ms"]>=0,"sibling fork/restore")
                for v in x["views"]:verify_view(v,pick)
                builds.extend(a for a in x["work"]["active"] if a["anchor_built"])
            check(len(builds)==(1 if rep==0 else 0),"cold/warm anchor accounting")
            if rep:ts[m].append(t)
            else:cold[m]=dict(delivered_ms=t["delivered_ms"],build_ms=builds[0]["anchor_build_ms"],
                              typed_bytes=builds[0]["anchor_bytes"])
        modes={}
        for m,ss in ts.items():
            check(len(ss)==3,"three measured calls")
            totals=[t["delivered_ms"] for t in ss];example=ss[0]
            modes[m]=dict(delivered_ms=median(totals),range_ms=[min(totals),max(totals)],
                cold=cold[m],physical_branches=len(example["tried"]),
                outer_fork_restore_ms=median(sum(x["outer_fork_ms"]+x["outer_restore_ms"] for x in t["tried"]) for t in ss),
                input_dependent_ms=median(sum(x["denominator_ms"]+x["shell_index_ms"] for x in t["tried"]) for t in ss),
                repairs_per_action=sum(x["work"]["repairs"] for x in example["tried"]),
                repaired_steps=sum(x["work"]["repair_steps"] for x in example["tried"]),
                ordinary_steps=sum(x["work"]["ordinary_steps"] for x in example["tried"]),
                projected_steps=sum(x["work"]["sliced_steps"] for x in example["tried"]),
                restarts=sum(x["work"]["restarts"] for x in example["tried"]),
                submitted_strokes=[{"pick":x["pick"],"views":[{k:v[k] for k in ("camera",*FIELDS,"witness")} for v in x["views"]]} for x in example["tried"]])
        for m in METHODS:modes[m]["relative_to_ordinary"]=modes[m]["delivered_ms"]/modes["ordinary"]["delivered_ms"]
        results.append(dict(cameras=cams,choices=choices,methods=modes))
    return dict(operations=results,capture_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                complete_worker_ms=cap["phases_ms"]["wall_before_receipt"],view_caches=cap["view_cache"],
                view_phases_ms={k:v for k,v in cap["arms"]["AL"]["phases_ms"].items() if "_view_" in k})


if __name__=="__main__":
    import json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--capture-dir",type=Path)
    args=p.parse_args();r=score(args.capture_dir or HERE/"evidence/timing")
    (args.capture_dir or HERE).joinpath("SCORE.json").write_text(json.dumps(r,indent=2)+"\n",encoding="utf8")
    for q in r["operations"]:print(q["cameras"],q["choices"],{m:round(v["delivered_ms"],2) for m,v in q["methods"].items()})
