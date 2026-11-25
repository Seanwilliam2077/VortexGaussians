"""Check native references, exact grid controls and the frozen Firewoods delivery gate."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from statistics import median
import json

HERE=Path(__file__).resolve().parent
METHODS=("ordinary","repair","sitewise","ordinary-cold","repair-cold","sitewise-cold")
FIELDS=("defined","first_frame","total","target","eligible","count","mass")
def load(path):
    return json.loads(path.read_bytes())

def score(folder):
    cap=load(folder/"CAPTURE.json")
    targets={q["arm"]:q for q in load(HERE.parent/"t108-visible-progression/REFERENCE.json")["queries"]}
    assert cap["status"]=="validated" and not cap["errors"] and tuple(cap["methods"])==METHODS and cap["repeats"]==6
    ans={"source_sha256":sha256((folder/"CAPTURE.json").read_bytes()).hexdigest(),"arms":{}}
    for ix,q in enumerate(cap["queries"]):
        arm=q["arm"];e=targets[arm];shot=cap["arms"][arm];audits=shot["progress_audits"]
        assert q["cut"]==180 and q["horizon"]==180 and shot["verified_frames"]==360
        assert [r["frame"] for r in shot["cold_ordinary_direct"]]==list(range(181,189))
        assert len(q["trials"])==42
        counts={m:[] for m in METHODS};cold_geometry_builds=[]
        for k,t in enumerate(q["trials"]):
            rep,ordinal=divmod(k,len(METHODS));m=METHODS[(ix+rep+ordinal)%len(METHODS)]
            assert (t["method"],t["rep"])==(m,rep) and all(t[key]==e[key] for key in FIELDS)
            counts[m].append(t)
            if m.endswith("-cold"):
                st=t["work"]["flame_grid"]
                assert not st["profile"] and st["builds"]==len(st["registrations"])>0 and st["within_radius"]==0
                if st["geom_build_ms"]>0:
                    cold_geometry_builds.append({"method":m,"rep":rep,"geom_ms":st["geom_build_ms"],"delivered":t["delivered_ms"]})
        assert len(cold_geometry_builds)==1 and cold_geometry_builds[0]["rep"]==0
        rows={}
        for m,all_ts in counts.items():
            ts=all_ts[1:];assert len(ts)==6
            times=[t["delivered_ms"] for t in ts]
            assert audits[m]["curve"]==e["curve"] and audits[m]["boundaries"]==audits["repair"]["boundaries"]
            r=dict(delivered_ms=median(times),min_ms=min(times),max_ms=max(times),waves_ms=times,
                   warmup_ms=all_ts[0]["delivered_ms"],repair_phase_ms=median(t["phases"]["repair_ms"] for t in ts))
            if m.endswith("-cold"):
                grids=[t["work"]["flame_grid"] for t in ts]
                r["grid"]={key:median(st[key] for st in grids) for key in ("build_ms","builds","total_index_bytes","peak_index_bytes","geom_bytes","removals")}
                pr=audits[m]["work"]["flame_grid"]
                assert pr["profile"] and pr["distance_tests"]>=pr["within_radius"]>0
                r["whole_deadline_profile"]={key:pr[key] for key in ("builds","samples","distance_tests","within_radius","removals","peak_index_bytes")}
            if m in ("repair-cold","sitewise-cold"):
                blocks=audits[m]["work"]["recovery_blocks"]
                assert all(b["direct_equal"]["material_bytes"]>0 for b in blocks)
                r["timed_blocks_profiled_separately"]=blocks[:ts[0]["work"]["repairs"]]
            if m=="sitewise":
                r["timed_blocks_profiled_separately"]=audits[m]["work"]["recovery_blocks"][:ts[0]["work"]["repairs"]]
            rows[m]=r
        comparisons={}
        for m in ("repair-cold","sitewise-cold"):
            base=rows["ordinary-cold"]
            ratios=[v/b for v,b in zip(rows[m]["waves_ms"],base["waves_ms"])]
            ratio=rows[m]["delivered_ms"]/base["delivered_ms"]
            wins=sum(v<1 for v in ratios)
            comparisons[m]=dict(median_ratio=ratio,paired_wins=wins,paired_ratios=ratios,qualifies=(ratio<=.9 and wins>=5))
        ans["arms"][arm]=dict(first=e["first_frame"],cold_geometry_first=cold_geometry_builds[0],methods=rows,comparisons=comparisons,
                               direct_equality_boundaries=len(audits["repair"]["boundaries"]))
    assert set(ans["arms"])==set(targets)
    ans["primary_decision"]="qualify-distinct-transfer" if any(r["qualifies"] for r in ans["arms"]["BA"]["comparisons"].values()) else "stop-development-route"
    (folder/"SCORE.json").write_text(json.dumps(ans,indent=2)+"\n",encoding="utf8")
    return ans

if __name__=="__main__":
    cli=ArgumentParser(description=__doc__);cli.add_argument("--capture-dir",type=Path,default=HERE/"evidence/firewoods")
    result=score(cli.parse_args().capture_dir)
    print(result["primary_decision"])
    for a,v in result["arms"].items():print(a,{m:round(r["delivered_ms"],2) for m,r in v["methods"].items()})
