"""Run the original registered observation on the single admitted (D3D12, NVIDIA) device."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
from admit import HERE, save, select

PRIOR=HERE.parent/"t124-external-curtain-observation"/"observe.py"
ADM="b6aee5a0d3597a778b0396b1250502ee179ca63de38aa23e5ae2b7c6aee1caa3"


def launch(source,out,arm):
    if arm:
        card=select(source)
        save(out/(arm+"-adapter.json"),card)
        spec=importlib.util.spec_from_file_location("frozen_t124",PRIOR)
        observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
        return observer.observe_one(source,out,arm)
    receipt=HERE/"evidence/ADMISSION.json"
    assert hashlib.sha256(receipt.read_bytes()).hexdigest()==ADM and json.loads(receipt.read_text())["status"]=="admitted"
    out.mkdir(parents=True,exist_ok=False)
    completed=[];costs={}
    for arm in ("L","F"):
        start=time.perf_counter()
        try:
            r=subprocess.run([sys.executable,__file__,"--source",str(source),"--out",str(out),"--worker",arm],timeout=240)
            costs[arm]=time.perf_counter()-start
            if r.returncode:
                save(out/"SUMMARY.json",dict(status="native_failure",arm=arm,exit=r.returncode,completed=completed,worker_s=costs));return 2
            completed.append(arm)
        except subprocess.TimeoutExpired:
            costs[arm]=time.perf_counter()-start
            save(out/"SUMMARY.json",dict(status="time_limit",arm=arm,limit_s=240,completed=completed,worker_s=costs));return 2
    results={arm:json.loads((out/(arm+".json")).read_text()) for arm in completed}
    first={k:next((l["frame"] for l,f in zip(results["L"]["samples"],results["F"]["samples"]) if l[k]!=f[k]),None)
           for k in ("gas","velocity","cloth")}
    choice=next((arm for arm in ("L","F") if results[arm]["result"]["passes"]),"none")
    save(out/"SUMMARY.json",dict(status="complete",completed=completed,choice=choice,first_sampled_difference=first,worker_s=costs))
    return 0


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True);p.add_argument("--worker",choices=["L","F"])
    args=p.parse_args()
    raise SystemExit(launch(args.source.resolve(),args.out.resolve(),args.worker))
