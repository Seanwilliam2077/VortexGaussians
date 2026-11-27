"""Launch one isolated DX12-only upstream device admission; no simulation, shaders, or flames."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

PIN="e2ac951dbfabc6060073943e4c344439ac5f4555"
DEVICE="NVIDIA GeForce RTX 5070 Laptop GPU"
HERE=Path(__file__).resolve().parent


def save(path,row):
    target=path.with_suffix(".tmp")
    target.write_text(json.dumps(row,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    target.replace(path)


def select(source,note=lambda **v:None, *, compiler_options=None):
    assert subprocess.check_output(["git","-C",str(source),"rev-parse","HEAD"],text=True).strip()==PIN
    assert not subprocess.check_output(["git","-C",str(source),"diff","--name-only","HEAD","--","blackbody"],text=True).strip()
    sys.path.insert(0,str(source))
    assert importlib.metadata.version("wgpu")=="0.32.0"
    import wgpu
    from wgpu.backends.wgpu_native import extras, __version__ as native_version
    assert native_version=="29.0.1.1"
    extras.set_instance_extras(backends=["DX12"], **(compiler_options or {}))
    note(stage="enumerating",wgpu="0.32.0",native=native_version)
    cards=[{k:str(v) for k,v in a.info.items() if k in ("vendor","device","backend_type","adapter_type","description")}
           for a in wgpu.gpu.enumerate_adapters_sync()]
    note(stage="enumerated",adapters=cards)
    matched=[c for c in cards if c["device"]==DEVICE and c["backend_type"].lower() in ("dx12","d3d12")
             and c["adapter_type"].lower()!="cpu"]
    if len(matched)!=1:raise RuntimeError("Exact dedicated DX12 adapter unavailable")
    os.environ["BLACKBODY_GPU"]=DEVICE
    os.environ["BLACKBODY_BACKEND"]=matched[0]["backend_type"]
    return matched[0]


def run(source,out):
    row={"status":"started","upstream":PIN,"requested":DEVICE};t=time.perf_counter()
    def note(**values):
        row.update(values);row["elapsed_s"]=time.perf_counter()-t;save(out,row)
    try:
        note(stage="before_instance")
        card=select(source,note)
        from blackbody.engine.gpu import GPU
        note(stage="requesting_native_device")
        gpu=GPU(adapter_name=card["device"],backend=card["backend_type"])
        if gpu.name!=DEVICE or str(gpu.backend).lower()!=str(card["backend_type"]).lower():raise RuntimeError("Adapter fallback")
        note(stage="live_readback",device=gpu.name,backend=gpu.backend,limits=gpu.limits,features=sorted(gpu.device.features))
        if not gpu.alive():raise RuntimeError("Native 4-byte readback failed")
        note(status="admitted",stage="complete")
        return 0
    except Exception as ex:
        note(status="failed",exception=type(ex).__name__,reason=str(ex).replace(str(source),"<upstream>").replace(str(Path.home()),"<home>")[:1000]);return 2


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True);parser.add_argument("--worker",action="store_true")
    args=parser.parse_args();out=args.out.resolve();source=args.source.resolve()
    if args.worker:sys.exit(run(source,out/"ADMISSION.json"))
    out.mkdir(parents=True,exist_ok=False)
    t=time.perf_counter()
    try:
        r=subprocess.run([sys.executable,__file__,"--source",str(source),"--out",str(out),"--worker"],timeout=45)
        save(out/"EXIT.json",dict(exit=r.returncode,limit_s=45,wall_s=time.perf_counter()-t));sys.exit(r.returncode)
    except subprocess.TimeoutExpired:
        save(out/"EXIT.json",dict(status="time_limit",limit_s=45,wall_s=time.perf_counter()-t));sys.exit(2)
