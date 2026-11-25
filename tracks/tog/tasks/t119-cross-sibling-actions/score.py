"""Reconstruct outcomes from old native traces and verify the complete paired action timings."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import median

HERE=Path(__file__).resolve().parent
STUDIES={"firewoods":("t109-common-parent-choice",124),"playground":("t111-playground-shot-choice",153)}
METHODS=["ordinary","repair","sibling","cold-ordinary","cold-repair","cold-sibling"]
FIELDS=("defined","first_frame","count","mass","total","target","eligible","witness")


def read(path):
    b=path.read_bytes()
    return json.loads(gzip.decompress(b) if path.suffix==".gz" else b)


def check(ok,label):
    if not ok: raise ValueError(label)


def reference(scene):
    study,second=STUDIES[scene]
    root=HERE.parent/study
    folder=root/"evidence/native"
    shots=read(folder/"capture-report.json")["shots"]
    shell=set(read(root/"shell.json.gz"))
    view_dir=HERE.parent/"t107-visible-burn-progression/evidence" if scene=="firewoods" else root
    weights={c:{i:math.floor(w*1e6+.5) for i,w in read(view_dir/f"weights-{c}.json.gz")["eligible_weights"]}
             for c in (0,second)}
    expected={}
    for arm,state in shots.items():
        trace=read(folder/(arm+"-trace.json.gz"))
        used=set(state["initial"]["ids"])|set(state["edit"]["ids"])
        for s in trace[:180]:used.update(s["new_ids"])
        eligible=shell-used
        for cam,w in weights.items():
            total=sum(w[i] for i in eligible);target=(total+3)//4
            count=mass=0;first=witness=None;cross_count=cross_mass=None;curve=[]
            for row in trace[180:270]:
                hits=eligible.intersection(row["new_ids"])
                count+=len(hits);mass+=sum(w[i] for i in hits)
                curve.append([row["frame"],len(hits),count,mass])
                if first is None and target>0 and mass>=target:
                    first=row["frame"];witness=min(i for i in hits if w[i]>0);cross_count=count;cross_mass=mass
            expected[arm[-1],cam]=dict(defined=bool(total),first_frame=first,count=count if first is None else cross_count,
                mass=mass if first is None else cross_mass,total=total,target=target,eligible=len(eligible),witness=witness,curve=curve)
    return shots,expected


def verify(scene,round_id,cap,shots,expected):
    def view(row,pick,audit):
        want=expected[pick,row["camera"]]
        check(all(row[k]==want[k] for k in FIELDS),"decision or witness")
        if audit:check(row["curve"]==want["curve"],"native per-frame curve")
    order=METHODS if round_id==1 else METHODS[::-1]
    check(cap["methods"]==order and cap["repeats"]==6 and cap["status"]=="validated" and not cap["errors"],"process")
    check(cap["common_parent"]==shots["AL"]["pre_edit"]==shots["AF"]["pre_edit"],"parent")
    check(set(cap["arms"])==set(shots),"native arms")
    for arm,shot in cap["arms"].items():
        check(shot["verified_frames"]==360 and shot["endpoint"]==shots[arm]["end"],"endpoint")
        check(shot["cut_hashes"]=={str(c["frame"]):c["native_hash"] for c in shots[arm]["cuts"]},"cut")
    sources=cap["sources"];prior=read(HERE.parent/"t115-editorial-process-repeats"/"evidence"/(scene+"-1")/"CAPTURE.json")["sources"]
    diff={k for k in set(prior)|set(sources) if prior.get(k)!=sources.get(k)}
    added=set(sources)-set(prior)
    check(added=={"plugin_11"} and diff==added|{"T111_timing_protocol","T111_runner","staged_html"},"exact native source identities")
    check(sources["plugin_11"]=="1505050a662c4d4d2561346eeff98d9a0d099485d78614a706cfb7a10a3ac0f1","frozen integrated kernel")
    for k,f in (("T111_timing_protocol","PROTOCOL.md"),("T111_runner","run.mjs")):
        check(sources[k]==hashlib.sha256((HERE/f).read_bytes()).hexdigest(),"action driver identity")
    audits=cap["full_audits"]
    for method in ("sibling","cold-sibling"):
        a=audits[method];k=a["work"]["steps"]
        check(a["work"]["checkpointed"] and not a["work"]["fallback"] and a["work"]["reused_steps"]==k,"transport")
        check(a["frames"]==sorted([180+k,181+k,224,270]),"physical checks")
        for x in a["curves"]:
            for v in x["views"]:view(v,x["pick"],True)
    check(audits["sibling"]["physical"]==audits["cold-sibling"]["physical"],"fallback-free physical fingerprints")
    for method in ("cold-ordinary","cold-repair"):
        for pick in ("L","F"):
            for v in audits[method+"_"+pick]["curves"]:view(v,pick,True)
    ops=[]
    for index,q in enumerate(cap["queries"]):
        cams=q["cameras"];second=STUDIES[scene][1];check(cams==([0] if index==0 else [0,second]),"scope")
        wait=[c for c in cams if expected["L",c]["defined"] and expected["L",c]["first_frame"] is None]
        choices={str(c):("undefined" if not expected["L",c]["defined"] else "L" if c not in wait else
                       "F" if expected["F",c]["first_frame"] is not None else "none") for c in cams}
        warm={m:[] for m in order};cold={};mechanism={};phase={};check(len(q["trials"])==42,"calls")
        for i,t in enumerate(q["trials"]):
            rep,slot=divmod(i,len(order));m=order[(rep+slot+index)%len(order)]
            check(t["rep"]==rep and t["method"]==m and t["choices"]==choices,"rotation and result")
            check(0<t["total_browser_ms"]<=t["delivered_ms"]+2,"delivery clock")
            check([x["pick"] for x in t["tried"]]==(["L","F"] if wait else ["L"]),"short circuit")
            for x in t["tried"]:
                pick=x["pick"];check(x["clicked"]==shots["A"+pick]["edit"]["count"],"actual stroke")
                check([v["camera"] for v in x["views"]]==(cams if pick=="L" else wait),"views still needed")
                for v in x["views"]:view(v,pick,False)
            if m.endswith("sibling"):
                w=t["work"];active=w["active"]
                check(not w["fallback"] and w["checkpointed"] and w["prepared_full_sites"]==shots["AF"]["edit"]["count"],"full preparation")
                check(w["reused_steps"]==(w["steps"] if wait else 0),"physical reuse")
                mechanism[m]={key:w[key] for key in ("steps","reused_steps","light_steps","full_steps","checkpoint_material_bytes","checkpoint_particles","prepared_full_sites")}
                keys=("prepare_full_ms","guard_ms","fork_at_boundary_ms","restore_at_boundary_ms","transport_ms")
                if rep:
                    for key in keys:phase.setdefault(m,{}).setdefault(key,[]).append(w[key])
            else:active=[a for x in t["tried"] for a in x["work"]["active"]]
            builds=[a for a in active if a["anchor_built"]]
            check(len(builds)==int(rep==0),"cold anchor or warm retention")
            if rep:warm[m].append(t["delivered_ms"])
            else:cold[m]=dict(total=t["delivered_ms"],anchor_build_ms=builds[0]["anchor_build_ms"],
                               anchor_bytes=builds[0]["anchor_bytes"],flame_geom_ms=t.get("cold_lookup",{}).get("geom_build_ms",0))
        med={m:median(v) for m,v in warm.items()}
        ratios={m+"_over_"+control:med[m]/med[control] for m,control in (
            ("sibling","ordinary"),("sibling","repair"),("cold-sibling","cold-ordinary"),("cold-sibling","cold-repair"),
            ("cold-ordinary","ordinary"),("cold-repair","repair"))}
        ops.append(dict(cameras=cams,choices=choices,raw_warm_ms=warm,cold=cold,median_ms=med,ratios=ratios,work=mechanism,
                        sibling_phase_medians_ms={m:{k:median(v) for k,v in phases.items()} for m,phases in phase.items()}))
    check(len(ops)==2,"two operations")
    return dict(scene=scene,round=round_id,start=cap["started_utc"],runtime=cap["runtime"],
                worker_ms=cap["phases_ms"]["wall_before_receipt"],phase_ms=cap["phases_ms"],
                arm_setup_ms={k:v["phases_ms"] for k,v in cap["arms"].items()},ops=ops)


def score(partial=False):
    blocks=[]
    for rnd,scenes in ((1,list(STUDIES)),(2,list(STUDIES)[::-1])):
        for scene in scenes:
            path=HERE/"evidence"/f"{scene}-{rnd}"/"CAPTURE.json"
            if partial and not path.is_file():continue
            b=verify(scene,rnd,read(path),*reference(scene))
            b["capture_sha"]=hashlib.sha256(path.read_bytes()).hexdigest();blocks.append(b)
    check(len({x["start"] for x in blocks})==len(blocks),"distinct process starts")
    return dict(blocks=blocks)


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--partial",action="store_true");args=p.parse_args()
    out=score(args.partial)
    for b in out["blocks"]:
        for q in b["ops"]:
            print(b["scene"],b["round"],q["cameras"]," ".join(f"{m}={q['median_ms'][m]:.1f}" for m in METHODS))
    if not args.partial:(HERE/"SCORE.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf8")
