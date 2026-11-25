"""Static source check and future instrumentation for an ALREADY prepared Blackbody engine.

The CLI parses local Python source only. The diagnostic function requires an engine and a scene
created by a separately authorized experiment. It never advances a simulated frame.
"""
import argparse
import ast
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter
from unittest.mock import patch

PIN="e2ac951dbfabc6060073943e4c344439ac5f4555"


def _methods(path,cls):
    tree=ast.parse(path.read_text(encoding="utf8"))
    body=next(node.body for node in tree.body if isinstance(node,ast.ClassDef) and node.name==cls)
    return {fn.name:fn for fn in body if isinstance(fn,ast.FunctionDef)}


def check_source(root):
    rev=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    if rev!=PIN:raise ValueError("Unexpected source revision")
    if subprocess.check_output(["git","-C",str(root),"diff","--name-only","HEAD","--","blackbody"],text=True).strip():
        raise ValueError("Modified upstream source")
    p=root/"blackbody/engine/engine.py"
    methods=_methods(p,"Engine")
    calls=lambda fn:{node.func.attr for node in ast.walk(fn) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
    assert "volume_for" in calls(methods["render"]) and "step_frame" in calls(methods["simulate_to"])
    for name in ("render","volume_for","aovs","linear_comp"):
        assert not {"simulate_to","step_frame"}.intersection(calls(methods[name]))
    assert "read" in calls(methods["aovs"])
    renderer=_methods(root/"blackbody/engine/renderer.py","Renderer")
    assert "read" in calls(renderer["read_linear"])
    return {"revision":rev,"device_calls":0,"parsed_methods":{k:[methods[k].lineno,methods[k].end_lineno]
            for k in ("simulate_to","_resume","volume_for","render","aovs","linear_comp")}}


def _atomic(path,writer):
    tmp=path.with_name(path.name+".tmp")
    with tmp.open("xb") as f:
        writer(f);f.flush();os.fsync(f.fileno())
    tmp.replace(path)


def capture_endpoint(engine,scene,directory):
    """Measure the same two T124 output products. Caller owns deadline, hardware and prior simulation."""
    import numpy as np
    out=Path(directory);out.mkdir(parents=True,exist_ok=False)
    start=perf_counter();frame=145;live=engine.sim_frame==frame
    if not live and frame not in engine.cache:raise ValueError("Native render needs the live or cached target frame")
    if engine.kind!="fire" or scene.start!=1 or scene.fps!=24:raise ValueError("Unexpected engine or timeline")
    physical_frame,physical_steps=engine.sim_frame,engine.solver.steps
    def mark(name,event,**data):
        with (out/"PHASES.ndjson").open("a",encoding="utf8") as log:
            log.write(json.dumps({"name":name,"event":event,"s":perf_counter()-start,**data})+"\n")
            log.flush();os.fsync(log.fileno())
    def phase(name,fn,*args,**kwargs):
        mark(name,"begin")
        try:value=fn(*args,**kwargs)
        except Exception as exc:
            mark(name,"exception",type=type(exc).__name__);raise
        mark(name,"returned");return value
    def attach(stack,obj,name,label):
        original=getattr(obj,name)
        def wrapped(*args,**kwargs):return phase(label,original,*args,**kwargs)
        stack.enter_context(patch.object(obj,name,wrapped))
    def write_array(path,a):
        _atomic(path,lambda f:np.save(f,np.ascontiguousarray(a),allow_pickle=False))
    def write_object(path,value):
        payload=(json.dumps(value,indent=2,allow_nan=False)+"\n").encode()
        _atomic(path,lambda f:f.write(payload))
    def unchanged():
        if (engine.sim_frame,engine.solver.steps)!=(physical_frame,physical_steps):
            raise AssertionError("Physical frame or gas step counter changed across render")
    options=dict(final=True,samples=1,motion_blur=False,seed=0)
    mark("frame","start",frame=frame,live=live,source=PIN,solver_steps=physical_steps)
    with ExitStack() as stack:
        # These probe host entry/return while command buffers are being assembled. They are
        # diagnostic operations with synchronous disk I/O and cannot benchmark production latency.
        for obj,method,label in ((engine,"volume_for","volume_selection"),(engine.cloth,"prepare_light","cloth_light_allocation"),
                (engine.renderer,"light","volume_lighting"),(engine,"_draw_raster","cloth_raster"),
                (engine.renderer,"march","volume_march"),(engine.renderer,"composite","encode_composite")):
            attach(stack,obj,method,label)
        old=engine.gpu.on_compile
        def compiling(source):
            mark("native_kernel_cache_miss","begin",source=Path(str(source)).name)
            if old is not None:old(source)
        stack.enter_context(patch.object(engine.gpu,"on_compile",compiling))
        phase("fire_render_call",engine.render,scene,frame,(320,180),mode="fire",**options);unchanged()
        phase("fire_queue_completion",engine.gpu.queue.on_submitted_work_done_sync)
        emit=phase("fire_emission_read",engine.gpu.read,engine.renderer.emit)
        if emit.shape!=(180,320,4) or not np.isfinite(emit).all():raise ValueError("Unexpected emission")
        phase("save_native_emission",write_array,out/"emission.npy",emit)
        def emission_score():
            Y=np.einsum("ijk,k->ij",emit[...,:3].astype(np.float64),np.array([.2126,.7152,.0722]))
            region=Y[45:90,80:240];count=int(np.count_nonzero(region>=1.0))
            return {"frame":frame,"pixels":region.size,"count":count,"required":72,"passes":count>=72,
                "region_mean":float(region.mean()),"region_peak":float(region.max()),"full_luminance_sum":float(Y.sum()),
                "dtype":str(emit.dtype),"shape":list(emit.shape),"sha256":hashlib.sha256(emit.tobytes()).hexdigest()}
        score=phase("score_emission",emission_score)
        phase("persist_decision",write_object,out/"DECISION.json",score)
        phase("composite_render_call",engine.render,scene,frame,(320,180),mode="composite",**options);unchanged()
        phase("composite_queue_completion",engine.gpu.queue.on_submitted_work_done_sync)
        comp=phase("scene_linear_composite_read",engine.linear_comp)
        if comp.shape[:2]!=(180,320) or not np.isfinite(comp).all():raise ValueError("Unexpected composite")
        phase("save_native_composite",write_array,out/"composite.npy",comp)
    mark("frame","complete",frame=frame)
    return score


if __name__=="__main__":
    p=argparse.ArgumentParser(description="Inspect pinned source without importing Blackbody or accessing a device.")
    p.add_argument("--check-source",required=True,type=Path)
    print(json.dumps(check_source(p.parse_args().check_source),indent=2))
