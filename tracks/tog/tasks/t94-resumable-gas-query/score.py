"""Audit joint outcomes and calculate per-query paired delivered latency."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from statistics import median

HERE=Path(__file__).resolve().parent
METHODS=("full","trim","regional","rank-only","t93","sweep-rank","sweep-spatial","slice-rank","slice-regional")
TIMES=("delivered_ms","compute_ms","browser_ms","fork_ms","restore_ms")


def read(path):
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix==".gz" else raw)


def require(ok, why):
    if not ok:
        raise ValueError(why)


def summarize(rows):
    out={"n":len(rows)}
    if not rows:
        return out
    for m in METHODS:
        times=[r["methods"][m]["median_ms"] for r in rows]
        rec={f:median(x[f] for x in times) for f in TIMES}
        for baseline in ("regional","trim","rank-only","t93","sweep-rank"):
            ratios=[t["delivered_ms"]/r["methods"][baseline]["median_ms"]["delivered_ms"] for t,r in zip(times,rows)]
            rec["vs_"+baseline]=dict(median=median(ratios),min=min(ratios),max=max(ratios),faster=sum(r<1 for r in ratios))
        out[m]=rec
    return out


def score(asset):
    folder=HERE/"evidence"/asset
    cap=read(folder/"CAPTURE.json")
    previous=read(HERE.parent/"t90-callable-regional-query"/"evidence"/asset/"SCORE.json")
    refs={(q["arm"],q["cut"],q["horizon"]):q for q in previous["windows"]}
    traces=HERE.parent/("t86-ignition-margin/public" if asset=="firewoods" else "t92-transfer-workload/evidence")
    native=read(traces/"capture-report.json")
    require(cap["status"]=="validated" and not cap["errors"] and tuple(cap["methods"])==METHODS and cap["repeats"]==9,"run identity")
    frames={}
    for arm,rec in cap["arms"].items():
        require(rec["endpoint"]==native["shots"][arm]["end"] and rec["verified_frames"]==360,"native endpoint")
        frames[arm]=read(traces/f"{arm}-trace.json.gz")
        for cut in (210,240,300):
            checks=rec["resume_checks"][str(cut)]
            require([r["frame"] for r in checks["sweep"]]==list(range(cut+1,cut+9)),"resumability audit missing")
            require(checks["slice"] is not None,"slice audit missing")
    queries=[]
    for n,q in enumerate(cap["queries"]):
        arm,cut,h=(q[k] for k in ("arm","cut","horizon"))
        shell=set(cap["arms"][arm]["shell_ids"])
        first=next((f for f in frames[arm][cut:cut+h] if shell.intersection(f["new_ids"])),None)
        onset=None if first is None else first["frame"]
        ids=set() if first is None else shell.intersection(first["new_ids"])
        require(refs[arm,cut,h]["first_frame"]==onset==q["first_frame"] and set(q["expected_ids"])==ids,"reference")
        by={m:[] for m in METHODS}
        for k,t in enumerate(q["trials"]):
            rep,ordinal=divmod(k,len(METHODS))
            m=METHODS[(rep+ordinal+n)%len(METHODS)]
            require(t["rep"]==rep and t["method"]==m,"order")
            require(t["yes"]==bool(ids) and t["first_frame"]==onset and (t["witness"] in ids if ids else t["witness"] is None),"answer")
            require(all(t[f]>=0 for f in TIMES) and t["delivered_ms"]>0,"time")
            if rep: by[m].append(t)
        methods={}
        for m,ts in by.items():
            require(len(ts)==9,"repetitions")
            r={"median_ms":{f:median(t[f] for t in ts) for f in TIMES}}
            for key in ("step_counts","terminal_counts","plan_active","prefix_steps"):
                if key in ts[0]:
                    require(all(t[key]==ts[0][key] for t in ts),"discrete cost accounting")
                    r[key]=ts[0][key]
            methods[m]=r
        queries.append(dict(arm=arm,cut=cut,horizon=h,first_frame=onset,methods=methods))
    require(len(queries)==len(refs)==18,"query count")
    groups={"all":queries}
    for h in (1,4,8):
        groups["h"+str(h)]=[r for r in queries if r["horizon"]==h]
    groups["multistep"]=[r for r in queries if r["horizon"]>1]
    groups["early_positive_multistep"]=[r for r in groups["multistep"] if r["first_frame"] is not None and r["first_frame"]<r["cut"]+r["horizon"]]
    groups["no_multistep"]=[r for r in groups["multistep"] if r["first_frame"] is None]
    result=dict(capture_sha256=hashlib.sha256((folder/"CAPTURE.json").read_bytes()).hexdigest(),summary={s:summarize(r) for s,r in groups.items()},queries=queries)
    (folder/"SCORE.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("asset",choices=("firewoods","dead-tree"))
    out=score(p.parse_args().asset)
    for group in ("all","h1","h4","h8","early_positive_multistep","no_multistep"):
        g=out["summary"][group]
        print(group, g["n"], {m:round(g[m]["vs_regional"]["median"],3) for m in ("sweep-rank","sweep-spatial","slice-rank") if m in g})
