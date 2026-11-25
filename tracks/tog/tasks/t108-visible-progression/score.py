"""Verify camera-weighted end-to-end calls against independent native frame ledgers."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median

from reference import compute, read

HERE=Path(__file__).resolve().parent
METHODS=("ordinary","restart","repair")
FIELDS=("defined","first_frame","total","target","eligible","count","mass")
COSTS=("delivered_ms","total_browser_ms","click_ms","shell_index_ms","denominator_ms")
WORK=("ordinary_steps","sliced_steps","repair_steps","repairs","restarts","log_bytes","peak_log_bytes",
      "projected_material_bytes","logged_samples","guards")


def check(ok,label):
    if not ok:
        raise ValueError(label)


def evaluate(directory):
    truth=compute()
    check(truth==read(HERE/"REFERENCE.json"),"reference table differs")
    source=directory/"CAPTURE.json"
    cap=read(source)
    check(cap["status"]=="validated" and not cap["errors"] and cap["methods"]==list(METHODS) and cap["repeats"]==3,"capture incomplete")
    check(len(cap["queries"])==len(truth["queries"])==2,"missing edits")
    native=read(HERE.parent/"t86-ignition-margin/public/capture-report.json")
    floats=read(HERE.parent/"t107-visible-burn-progression/evidence/camera-0.json.gz")
    out=[]
    for i,(q,e) in enumerate(zip(cap["queries"],truth["queries"])):
        arm=e["arm"]; s=cap["arms"][arm]; n=native["shots"][arm]
        check(s["verified_frames"]==360 and s["endpoint"]==n["end"],"ordinary continuation")
        check(s["cut_hashes"]=={str(c["frame"]):c["native_hash"] for c in n["cuts"]},"native cuts")
        check(q["arm"]==arm and q["cut"]==180 and q["horizon"]==180,"query identity")
        check(len(q["trials"])==12,"missing trials")
        matte=floats["orders"][arm]
        check(matte["eligible"]==e["eligible"] and abs(matte["mass"]-e["float_total"])<1e-8,"independent float denominator")
        check((matte["quarter_matte"]+180 if matte["quarter_matte"] is not None else None)==e["first_float"],
              "independent floating camera threshold")
        check(len(matte["counts"])==len(e["curve"])==len(matte["cumulative_mass"]),"float camera frame count")
        for row,count,mass in zip(e["curve"],matte["counts"],matte["cumulative_mass"]):
            check(row[2]==count and abs(row[3]/1e6-mass)<=count*0.5e-6+1e-8,"per-site quantization bound")
        audits=s["progress_audits"]
        for m in METHODS:
            check(audits[m]["curve"]==e["curve"] and len(e["curve"])==180,"full-deadline curve")
            check(all(audits[m][k]==e[k] for k in FIELDS),"audited answer")
        check(audits["repair"]["boundaries"]==audits["ordinary"]["boundaries"],"repaired state")
        rows={m:[] for m in METHODS}
        warm_builds=[]
        for j,t in enumerate(q["trials"]):
            rep,k=divmod(j,3); m=METHODS[(i+k+rep)%3]
            check(t["rep"]==rep and t["method"]==m,"rotation")
            check(t["clicked"]==n["edit"]["count"] and all(t[k]==e[k] for k in FIELDS),"delivered edit answer")
            check(all(t[k]>=0 for k in COSTS) and t["delivered_ms"]>0,"timings")
            for a in t["work"]["active"]:
                if a["anchor_built"]:
                    warm_builds.append({k:a[k] for k in ("anchor_build_ms","anchor_bytes","anchor_rows") if k in a}|
                                       {"method":m,"rep":rep})
            if rep: rows[m].append(t)
        modes={}
        for m,ts in rows.items():
            check(len(ts)==3,"measured repeats")
            ms={k:median(t[k] for t in ts) for k in COSTS}
            ms["delivery_range_ms"]=[min(t["delivered_ms"] for t in ts),max(t["delivered_ms"] for t in ts)]
            for k in ("fork_ms","restore_ms","guard_ms","repair_ms"):ms[k]=median(t["phases"][k] for t in ts)
            work={k:ts[0]["work"][k] for k in WORK}
            check(all(t["work"][k]==v for t in ts for k,v in work.items()),"unstable operation counts")
            modes[m]={"cost":ms,"work":work}
        out.append(dict(arm=arm,defined=e["defined"],eligible=e["eligible"],first_frame=e["first_frame"],
            float_frame=e["first_float"],count=e["count"],mass=e["mass"],total=e["total"],target=e["target"],
            float_total=e["float_total"],full_deadline_repair_frames=sorted(map(int,audits["repair"]["boundaries"])),
            warm_builds=warm_builds,view_load_ms=s["phases_ms"]["load_static_view_weights"],view_cache=s["weight_cache"],
            methods=modes,ratios={m:modes[m]["cost"]["delivered_ms"]/modes["ordinary"]["cost"]["delivered_ms"] for m in METHODS}))
    return dict(windows=out,capture_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                input_raster_seconds=read(HERE.parent/"t107-visible-burn-progression/evidence/cost.json")["0"],
                full_worker_ms=cap["phases_ms"]["wall_before_receipt"])


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--capture-dir",type=Path)
    args=p.parse_args()
    report=evaluate(args.capture_dir or HERE/"evidence")
    dest=(args.capture_dir or HERE)/"SCORE.json"
    dest.write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    for w in report["windows"]: print(w["arm"],w["count"],w["ratios"])
