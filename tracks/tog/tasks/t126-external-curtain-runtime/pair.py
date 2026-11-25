"""One unchanged T124 pair on the T125 NVIDIA device after full native preparation."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
from zipfile import ZipFile,ZIP_DEFLATED

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"t125-nvidia-dx12-admission"))
from admit import DEVICE,save,select


def arm(source,out,key):
    import numpy as np
    card=select(source);save(out/(key+"-adapter.json"),card)
    prior=HERE.parent/"t124-external-curtain-observation"/"observe.py"
    spec=importlib.util.spec_from_file_location("frozen_t124",prior)
    observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
    native_digest=observer.digest
    expected=["gas","velocity","cloth"]
    calls=0
    def with_slices(a):
        nonlocal calls
        if calls<3*len(observer.FRAMES):
            frame=observer.FRAMES[calls//3];kind=expected[calls%3];calls+=1
            if kind=="cloth":
                assert a.ndim==2
                smaller=a[::64]
            else:
                assert a.ndim==4
                nz=a.shape[0];smaller=a[[nz//4,nz//2,3*nz//4],::8,::8,:]
            # Already-read native values. Close after every write to survive the wall-time stop.
            with ZipFile(out/(key+"-sampled-values.npz"),"a",compression=ZIP_DEFLATED) as z:
                with z.open(f"frame-{frame:03d}-{kind}.npy","w") as stream:
                    np.lib.format.write_array(stream,np.ascontiguousarray(smaller),allow_pickle=False)
        return native_digest(a)
    observer.digest=with_slices
    return observer.observe_one(source,out,key)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--source",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path);p.add_argument("--worker",choices=["L","F"])
    args=p.parse_args();src=args.source.resolve();out=args.out.resolve()
    if args.worker:sys.exit(arm(src,out,args.worker))
    prep=HERE/"evidence/preparation/PREPARE.json"
    admission=json.loads(prep.read_text());assert admission["stage"]=="prepared" and admission["adapter"]["device"]==DEVICE
    out.mkdir(parents=True,exist_ok=False);completed=[];costs={}
    for key in ("L","F"):
        t=time.perf_counter()
        try:
            r=subprocess.run([sys.executable,__file__,"--worker",key,"--source",str(src),"--out",str(out)],timeout=240)
            costs[key]=time.perf_counter()-t
            if r.returncode:
                save(out/"SUMMARY.json",dict(status="native_failure",arm=key,completed=completed,exit=r.returncode,worker_s=costs));sys.exit(2)
            completed.append(key)
        except subprocess.TimeoutExpired:
            costs[key]=time.perf_counter()-t
            save(out/"SUMMARY.json",dict(status="time_limit",arm=key,limit_s=240,completed=completed,worker_s=costs));sys.exit(2)
    data={k:json.loads((out/(k+".json")).read_text()) for k in completed}
    first={v:next((a["frame"] for a,b in zip(data["L"]["samples"],data["F"]["samples"]) if a[v]!=b[v]),None)
           for v in ("gas","velocity","cloth")}
    choice=next((k for k in completed if data[k]["result"]["passes"]),"none")
    save(out/"SUMMARY.json",dict(status="complete",completed=completed,choice=choice,first_sampled_difference=first,worker_s=costs))
