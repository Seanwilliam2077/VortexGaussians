"""Check the four-way full-action recovery-profile comparison on fixed Playground edits."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from statistics import median

HERE=Path(__file__).resolve().parent
ORIGINAL=HERE.parents[1]/"t111-playground-shot-choice"
sys.path.insert(0,str(ORIGINAL))
from reference import build, load

METHODS=("ordinary","repair","sparse","sitewise")
FIELDS=("defined","first_frame","count","mass","total","target","eligible")


def check(ok,label):
    if not ok:raise ValueError(label)


def score(folder):
    ref=build(); check(ref==load(ORIGINAL/"REFERENCE.json"),"independent native target")
    targets={(q["arm"][1],q["camera"]):q for q in ref["queries"]}
    s=load(ORIGINAL/"shell.json.gz")
    native=load(ORIGINAL/"evidence/native/capture-report.json")
    trace={a:load(ORIGINAL/"evidence/native"/(a+"-trace.json.gz")) for a in ("AL","AF")}
    weights={c:dict(load(ORIGINAL/("weights-"+str(c)+".json.gz"))["eligible_weights"]) for c in (0,153)}
    file=folder/"CAPTURE.json";data=load(file)
    check(data["status"]=="validated" and not data["errors"] and data["methods"]==list(METHODS)
          and data["repeats"]==4,"schedule")
    check(data["common_parent"]==ref["pre_click"],"shared parent")
    for arm,shot in data["arms"].items():
        orig=native["shots"][arm]
        check(shot["verified_frames"]==360 and shot["endpoint"]==orig["end"],"complete native trajectory")
        check(shot["cut_hashes"]=={str(c["frame"]):c["native_hash"] for c in orig["cuts"]},"native cuts")
    def view(v,pick):
        c=v["camera"];t=targets[pick,c]
        check(all(v[k]==t[k] for k in FIELDS),"count, mass, milestone or denominator")
        at=t["first_frame"]
        if at is None:check(v["witness"] is None,"censored witness")
        else:
            onset=trace["A"+pick][at-1]["new_ids"]
            hits=[i for i in set(s).intersection(onset) if math.floor(1e6*weights[c][i]+.5)>0]
            check(v["witness"]==min(hits),"stable opacity contributor")
    profiled={}
    for pk,a in data["full_audits"].items():
        for m in METHODS:
            for v in a[m]["views"]:
                view(v,pk);check(v["curve"]==targets[pk,v["camera"]]["curve"],"full-horizon mass")
            check(a[m]["boundaries"]==a["ordinary"]["boundaries"],"physical boundary and subsequent step")
            for idx,pair in a[m]["boundaries"].items():
                check(pair["state"]["marker"]["frame"]==int(idx) and pair["next"]["marker"]["frame"]==int(idx)+1,"audit clocks")
        profiled[pk]=dict(frames=sorted(map(int,a["ordinary"]["boundaries"])),sitewise=a["sitewise"]["work"]["recovery_blocks"])
    out=[]
    for i,q in enumerate(data["queries"]):
        cams=q["cameras"];check(cams==[[0],[153],[0,153]][i],"operation")
        check(len(q["trials"])==20,"four-way repeated schedule")
        deadlines={str(c):"L" for c in cams}
        samples={m:[] for m in METHODS};cold={}
        for k,t in enumerate(q["trials"]):
            rep,slot=divmod(k,4);m=METHODS[(i+rep+slot)%4]
            check(t["method"]==m and rep==t["rep"] and t["choices"]==deadlines,"method order and choice")
            check(len(t["tried"])==1 and t["tried"][0]["pick"]=="L","expected exact short-circuit")
            x=t["tried"][0];check(x["clicked"]==native["shots"]["AL"]["edit"]["count"],"applied light edit")
            check([v["camera"] for v in x["views"]]==cams,"matched requested views")
            for v in x["views"]:view(v,"L")
            check(t["delivered_ms"]>=t["total_browser_ms"]-1 and x["outer_fork_ms"]>=0 and x["outer_restore_ms"]>=0,"time scope")
            builds=[g for g in x["work"]["active"] if g["anchor_built"]]
            check(len(builds)==(rep==0),"cold anchor")
            blocks=x["work"]["recovery_blocks"]
            check(len(blocks)==x["work"]["repairs"],"per-repair accounting")
            if rep:samples[m].append(t)
            else:cold[m]=dict(delivered_ms=t["delivered_ms"],anchor_ms=builds[0]["anchor_build_ms"],anchor_bytes=builds[0]["anchor_bytes"])
        methods={}
        for m,records in samples.items():
            check(len(records)==4,"complete repeats")
            times=[t["delivered_ms"] for t in records]
            repairs=[t["tried"][0] for t in records]
            counts=[(a["work"]["repairs"],a["work"]["repair_steps"]) for a in repairs]
            check(len(set(counts))==1,"repair decisions")
            methods[m]=dict(warm_median_ms=median(times),range_ms=[min(times),max(times)],
                cold=cold[m],repair_ms=median(x["phases"]["repair_ms"] for x in repairs),
                repairs=counts[0][0],repair_steps=counts[0][1],blocks=repairs[0]["work"]["recovery_blocks"])
        for r in methods.values():r["vs_full"]=r["warm_median_ms"]/methods["ordinary"]["warm_median_ms"]
        best=min(methods[m]["warm_median_ms"] for m in ("repair","sparse"))
        opt=methods["sitewise"]["warm_median_ms"]
        out.append(dict(cameras=cams,methods=methods,sitewise_vs_better_chronological=opt/best,
                        sitewise_faster_than_full_and_both_chronological=opt<min(best,methods["ordinary"]["warm_median_ms"])))
    check(len(out)==3,"all camera operations")
    return dict(operations=out,full_horizon_repair_audits=profiled,
                capture_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                wall_ms=data["phases_ms"]["wall_before_receipt"])


if __name__=="__main__":
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument("--capture-dir",type=Path); opts=args.parse_args()
    r=score(opts.capture_dir or HERE/"evidence")
    (opts.capture_dir or HERE).joinpath("SCORE.json").write_text(json.dumps(r,indent=2)+"\n",encoding="utf8")
    for o in r["operations"]:print(o["cameras"],{m:round(v["warm_median_ms"],2) for m,v in o["methods"].items()})
