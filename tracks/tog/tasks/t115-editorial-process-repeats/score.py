"""Check full reported outputs and estimate within-machine variation across independent processes."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import median

HERE=Path(__file__).resolve().parent
STUDIES={"firewoods":("t109-common-parent-choice",124),"playground":("t111-playground-shot-choice",153)}
METHODS=("ordinary","repair")
FIELDS=("defined","first_frame","count","mass","total","target","eligible","witness")


def read(path):
    b=path.read_bytes()
    return json.loads(gzip.decompress(b) if path.suffix==".gz" else b)


def check(ok,label):
    if not ok: raise ValueError(label)


def reference(scene):
    name,cam=STUDIES[scene];base=HERE.parent/name
    folder=base/"evidence/native"
    ref=read(folder/"capture-report.json")["shots"]
    shell=set(read(base/"shell.json.gz"))
    views=HERE.parent/"t107-visible-burn-progression/evidence" if scene=="firewoods" else base
    weights={c:{i:math.floor(1e6*w+.5) for i,w in read(views/f"weights-{c}.json.gz")["eligible_weights"]}
             for c in (0,cam)}
    result={}
    for arm,state in ref.items():
        tr=read(folder/(arm+"-trace.json.gz"))
        lit=set(state["initial"]["ids"])|set(state["edit"]["ids"])
        for step in tr[:180]:lit.update(step["new_ids"])
        eligible=shell-lit
        for c in (0,cam):
            w=weights[c];total=sum(w[i] for i in eligible);threshold=(total+3)//4
            count=mass=0;first=None;witness=None
            for row in tr[180:270]:
                hits=eligible.intersection(row["new_ids"])
                count+=len(hits);mass+=sum(w[i] for i in hits)
                if threshold and mass>=threshold:
                    first=row["frame"];witness=min(i for i in hits if w[i]>0);break
            result[arm[-1],c]=dict(defined=total>0,first_frame=first,count=count,mass=mass,total=total,
                      target=threshold,eligible=len(eligible),witness=witness)
    return ref,result


def evaluate(scene,rnd,cap,ref,expected):
    cam=STUDIES[scene][1]
    order=list(METHODS) if rnd in (1,4) else list(reversed(METHODS))
    check(cap["status"]=="validated" and not cap["errors"] and cap["methods"]==order and cap["repeats"]==2,"worker")
    prior="t113-firewoods-editorial-action" if scene=="firewoods" else "t111-playground-shot-choice"
    pins=read(HERE.parent/prior/"evidence/timing/CAPTURE.json")["sources"]
    actual=cap["sources"]
    altered={k for k in actual.keys()|pins.keys() if actual.get(k)!=pins.get(k)}
    check(altered=={"T111_timing_protocol","T111_runner"},"previous native inputs, solver and weight identities")
    for k,f in (("T111_timing_protocol","PROTOCOL.md"),("T111_runner","run.mjs")):
        check(actual[k]==hashlib.sha256((HERE/f).read_bytes()).hexdigest(),"pinned repeat driver")
    check(cap["common_parent"]==ref["AL"]["pre_edit"]==ref["AF"]["pre_edit"],"common parent")
    for arm,shot in cap["arms"].items():
        check(shot["verified_frames"]==360 and shot["endpoint"]==ref[arm]["end"],"native full continuation")
        check(shot["cut_hashes"]=={str(c["frame"]):c["native_hash"] for c in ref[arm]["cuts"]},"native cuts")
    check([q["cameras"] for q in cap["queries"]]==[[0],[0,cam]],"operation set")
    operational=[]
    for i,q in enumerate(cap["queries"]):
        cams=q["cameras"];warm={m:[] for m in METHODS};cold={}
        need=[c for c in cams if expected["L",c]["defined"] and expected["L",c]["first_frame"] is None]
        chosen={str(c):("undefined" if not expected["L",c]["defined"] else "L" if c not in need else
                        "F" if expected["F",c]["first_frame"] is not None else "none") for c in cams}
        check(len(q["trials"])==6,"blocks of three calls for both methods")
        for k,t in enumerate(q["trials"]):
            rep,slot=divmod(k,2);m=order[(rep+slot+i)%2]
            check(t["rep"]==rep and t["method"]==m and t["choices"]==chosen,"rotation/choice")
            check(0<t["total_browser_ms"]<=t["delivered_ms"]+1,"host time")
            check([x["pick"] for x in t["tried"]]==(["L","F"] if need else ["L"]),"stopping rule")
            builds=[]
            for x in t["tried"]:
                pick=x["pick"]
                check(x["clicked"]==ref["A"+pick]["edit"]["count"],"true brush")
                check([v["camera"] for v in x["views"]]==(cams if pick=="L" else need),"requested views")
                check(x["outer_fork_ms"]>=0 and x["outer_restore_ms"]>=0,"transaction branch")
                for v in x["views"]:
                    check({key:v[key] for key in FIELDS}==expected[pick,v["camera"]],"onset/mass/identity")
                builds.extend(a for a in x["work"]["active"] if a["anchor_built"])
            check(len(builds)==(rep==0),"independent cold warmup, retained warm index")
            if rep:warm[m].append(t["delivered_ms"])
            else:cold[m]=dict(full_action_ms=t["delivered_ms"],build_ms=builds[0]["anchor_build_ms"],
                              typed_bytes=builds[0]["anchor_bytes"])
        med={m:median(warm[m]) for m in METHODS}
        operational.append(dict(cameras=cams,first_method=order[i],choices=chosen,raw_warm_ms=warm,
                            cold=cold,medians_ms=med,repair_over_ordinary=med["repair"]/med["ordinary"]))
    return dict(scene=scene,round=rnd,start=cap["started_utc"],runtime=cap["runtime"],first_order=order,
                worker_ms=cap["phases_ms"]["wall_before_receipt"],browser_launch_ms=cap["phases_ms"]["browser_launch"],
                setup_and_validation_ms={arm:shot["phases_ms"] for arm,shot in cap["arms"].items()},operations=operational)


def all_blocks(partial=False):
    refs={scene:reference(scene) for scene in STUDIES}
    blocks=[];receipt_dates=[];runtime=None
    for rnd in range(1,5):
        order=("firewoods","playground") if rnd%2 else ("playground","firewoods")
        for scene in order:
            path=HERE/"evidence"/f"{scene}-{rnd}"/"CAPTURE.json"
            if not path.exists() and partial:continue
            r=evaluate(scene,rnd,read(path),*refs[scene])
            r["capture_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
            receipt_dates.append(r["start"]);blocks.append(r)
            if runtime is None:runtime=r["runtime"]
            check(r["runtime"]==runtime,"runtime consistency")
    check(list(sorted(set(receipt_dates)))==receipt_dates,"chronological distinct starts")
    summary={}
    for scene in STUDIES:
        rows=[b for b in blocks if b["scene"]==scene]
        if not rows:continue
        if not partial:check(len(rows)==4,"four fresh processes")
        summary[scene]={}
        for i,label in enumerate(("camera0","joint")):
            ratios=[r["operations"][i]["repair_over_ordinary"] for r in rows]
            summary[scene][label]=dict(rounds=[r["round"] for r in rows],paired_ratios=ratios,median=median(ratios),
                minimum=min(ratios),maximum=max(ratios),repair_faster_blocks=sum(v<1 for v in ratios))
    return dict(blocks=blocks,summary=summary)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partial",action="store_true",help="Report completed blocks without writing final score")
    p=parser.parse_args();result=all_blocks(p.partial)
    print(json.dumps(result["summary"],indent=2))
    if not p.partial:(HERE/"SCORE.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
