"""Run exactly the pinned external paired observation, or import the scene without acquiring a GPU."""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

PIN="e2ac951dbfabc6060073943e4c344439ac5f4555"
PRESET="fabric_curtain"
SIZES={"F":(.05,.07,.05),"L":(.025,.07,.025)}
FRAMES=list(range(1,12))+[25,73,97,145]
HERE=Path(__file__).resolve().parent


def save(path,value):
    tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    tmp.replace(path)


def setup(root,arm):
    import numpy as np
    rev=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    if rev!=PIN:raise ValueError("Expected pinned release source")
    changed=subprocess.check_output(["git","-C",str(root),"diff","--name-only","HEAD","--","blackbody"],text=True).strip()
    if changed:raise ValueError("Upstream engine/package was edited")
    sys.path.insert(0,str(root))
    from blackbody.scene import presets
    from blackbody.engine.engine import Engine
    if Path(presets.__file__).resolve().parent.parent.parent!=root:raise ValueError("Unexpected module source")
    scene=presets.make(PRESET,fps=24)
    path=("emitter",0,"size")
    assert scene.start==1 and scene.end==264 and scene.fps==24 and tuple(scene.get(path))==SIZES["F"]
    assert scene.fabrics[0]["material"]=="cotton" and scene.data["domain"]["resolution"]==160
    if arm=="L":scene.set(path,SIZES["L"])
    assert tuple(scene.get(path))==SIZES[arm]
    metadata=dict(upstream=PIN,preset=PRESET,arm=arm,shape=list(scene.get(path)),fps=scene.fps,
        frame_range=[scene.start,scene.end],requested_resolution=scene.data["domain"]["resolution"],
        python=platform.python_version(),numpy=np.__version__,wgpu=importlib.metadata.version("wgpu"),
        rendercanvas=importlib.metadata.version("rendercanvas"),material=scene.fabrics[0]["material"],
        camera=dict(scene.camera(145)[0].__dict__),no_device_for_preflight=True)
    return scene,Engine,metadata


def digest(a):
    import numpy as np
    a=np.ascontiguousarray(a)
    return dict(sha256=hashlib.sha256(a.tobytes()).hexdigest(),shape=list(a.shape),dtype=str(a.dtype))


def observe_one(root,out,arm):
    import numpy as np
    from PIL import Image
    started=time.perf_counter();path=out/(arm+".json")
    receipt={"status":"starting","samples":[]}
    def record(status):
        receipt["status"]=status;receipt["elapsed_s"]=time.perf_counter()-started;save(path,receipt)
    try:
        scene,Engine,receipt["input"]=setup(root,arm)
        record("opening_device")
        eng=Engine()
        receipt["adapter"]={k:str(v) for k,v in eng.gpu.adapter.info.items()
            if k in ("vendor","device","description","adapter_type","backend_type","architecture")}
        record("preparing_native_scene");eng.prepare(scene,final=True)
        for frame in FRAMES:
            receipt["requested_frame"]=frame;record("simulating")
            eng.simulate_to(scene,frame,cache=False)
            scal=eng.solver.read_scalars();vel=eng.solver.read_velocity();cloth=eng.cloth.state()
            if not all(np.isfinite(a).all() for a in (scal,vel,cloth)):raise ArithmeticError("Nonfinite native fields")
            receipt["samples"].append(dict(frame=frame,gas=digest(scal),velocity=digest(vel),cloth=digest(cloth),
                gas_temperature_field_peak=float(scal[...,0].max()),cloth_T_K=[float(cloth[:,0].min()),float(cloth[:,0].max())],
                burning_vertices=int(np.count_nonzero(cloth[:,2]>.5))))
            record("sampled")
        record("rendering")
        options=dict(final=True,samples=1,motion_blur=False,seed=0)
        eng.render(scene,145,(320,180),mode="fire",**options)
        aov=eng.aovs();emit=aov["emission"]
        assert emit.shape==(180,320,4) and np.isfinite(emit).all()
        Y=np.einsum("ijk,k->ij",emit[...,:3].astype(np.float64),np.array([.2126,.7152,.0722]))
        roi=Y[45:90,80:240];count=int(np.count_nonzero(roi>=1.0))
        eng.render(scene,145,(320,180),mode="composite",**options)
        linear=eng.linear_comp()
        assert linear.shape[:2]==(180,320) and np.isfinite(linear).all()
        # A fixed filmic-independent sRGB display proxy for the native linear composite.
        rgb=np.clip(linear[...,:3].astype(np.float32),0,1)
        srgb=np.where(rgb<=.0031308,12.92*rgb,1.055*np.power(rgb,1/2.4)-.055)
        Image.fromarray(np.uint8(np.rint(srgb*255))).save(out/(arm+"-composite.png"))
        np.savez_compressed(out/(arm+"-frame.npz"),emission=emit,composite=linear)
        receipt["result"]=dict(frame=145,count=count,required=72,passes=count>=72,region_pixels=int(roi.size),
            mean=float(roi.mean()),peak=float(roi.max()),full_frame_luminance_sum=float(Y.sum()),
            emission=digest(emit),composite=digest(linear))
        record("complete");return 0
    except Exception as ex:
        # Never write the absolute paths or driver stack to the published receipt.
        receipt["exception"]=type(ex).__name__
        msg=str(ex)
        for item,label in ((str(root),"<upstream>"),(str(Path.home()),"<home>"),(str(out),"<output>")):
            msg=msg.replace(item,label).replace(item.replace("\\","/"),label)
        receipt["reason"]=msg[:2300];record("failed");return 2


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",type=Path,required=True)
    modes=ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preflight",action="store_true");modes.add_argument("--observe",action="store_true")
    modes.add_argument("--worker",choices=SIZES)
    ap.add_argument("--out",type=Path);a=ap.parse_args();root=a.source.resolve()
    if a.preflight:
        for arm in ("L","F"):
            _,_,metadata=setup(root,arm);print(json.dumps(metadata,sort_keys=True))
        return 0
    if not a.out:ap.error("--out is required for the native run")
    out=a.out.resolve()
    if a.worker:return observe_one(root,out,a.worker)
    out.mkdir(parents=True,exist_ok=False)
    completed=[]
    for arm in ("L","F"):
        try:
            run=subprocess.run([sys.executable,str(HERE/"observe.py"),"--source",str(root),"--worker",arm,"--out",str(out)],
                               timeout=240)
            if run.returncode:
                save(out/"SUMMARY.json",dict(status="native_failure",arm=arm,completed=completed,exit=run.returncode));return 2
            completed.append(arm)
        except subprocess.TimeoutExpired:
            save(out/"SUMMARY.json",dict(status="time_limit",arm=arm,completed=completed,limit_s=240));return 2
    results={arm:json.loads((out/(arm+".json")).read_text()) for arm in completed}
    first={k:next((l["frame"] for l,f in zip(results["L"]["samples"],results["F"]["samples"])
                   if l[k]!=f[k]),None) for k in ("gas","velocity","cloth")}
    pick=next((arm for arm in ("L","F") if results[arm]["result"]["passes"]),"none")
    save(out/"SUMMARY.json",dict(status="complete",completed=completed,choice=pick,first_sampled_difference=first))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
