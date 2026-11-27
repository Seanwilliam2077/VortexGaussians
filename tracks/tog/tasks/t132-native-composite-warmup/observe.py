"""One bounded, neutral native composite on the original Blackbody D3D12 stage."""
import argparse
from contextlib import ExitStack, contextmanager
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
TASKS = HERE.parent
sys.path.insert(0, str(TASKS / "t125-nvidia-dx12-admission"))
from admit import PIN, save, select

LIMIT = 720
KEYS = {"main":"8227724b41a7cd3a076abb47", "caustics":"c9eb1db2b37f2aeed7c82c9c"}
SOURCE_SHA = "5cc9e2d4d340bc8dda0fd8f9d0f58b2582b9c01e5ca5c0af13c8ed73f2fcfbb2"
REFERENCE = TASKS / "t130-independent-fx-choice/preflight/native-readback/PREFLIGHT.json"


def awake_seconds():
    ticks = ctypes.c_ulonglong()
    if not ctypes.windll.kernel32.QueryUnbiasedInterruptTime(ctypes.byref(ticks)):
        raise OSError("Windows awake clock unavailable")
    return ticks.value / 10_000_000


def worker(root, out, cache):
    import numpy as np
    start = time.perf_counter()
    awake_start = awake_seconds()
    result = {"status":"starting", "source_revision":PIN, "stage_keys_expected":KEYS}
    save(out / "RESULT.json", result)

    def log(name, event, **fields):
        with (out / "PHASES.ndjson").open("a", encoding="utf8") as stream:
            stream.write(json.dumps(dict(phase=name, event=event, elapsed_s=time.perf_counter()-start,
                                         awake_s=awake_seconds()-awake_start, **fields),
                                    allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    @contextmanager
    def phase(name, **fields):
        log(name, "start", **fields)
        try:
            yield
        except BaseException as ex:
            log(name, "exception", kind=type(ex).__name__, **fields)
            raise
        else:
            log(name, "return", **fields)

    def digest(v):
        if isinstance(v, np.ndarray):
            return dict(dtype=str(v.dtype), shape=list(v.shape), sha256=hashlib.sha256(v.tobytes(order="C")).hexdigest())
        if isinstance(v, np.generic):
            return v.item()
        if isinstance(v, dict):
            return {k:digest(a) for k,a in v.items()}
        if isinstance(v, (list,tuple)):
            return [digest(a) for a in v]
        return v

    try:
        with phase("device admission"):
            card = select(root)
            from blackbody.engine.engine import Engine
            from blackbody.engine.gpu import GPU, shader_key
            from blackbody.scene.model import Scene
            gpu = GPU(adapter_name=card["device"],backend=card["backend_type"])
            if gpu.name != card["device"] or gpu.backend != card["backend_type"]:
                raise RuntimeError("Unexpected native adapter")
            result["adapter"] = card
            save(out/"RESULT.json", result)
        with phase("engine construction"):
            eng = Engine(gpu)
        if eng._stage is not None:
            raise ValueError("Expected the original lazy stage")

        active = None
        kernel = gpu.kernel
        def trace_kernel(source_file, bindings, entry="main", defines=None, workgroup=(8,8,4), quiet=False):
            nonlocal active
            if source_file != "stage.wgsl":
                return kernel(source_file, bindings, entry, defines, workgroup, quiet)
            active = {"entry":entry, "bindings":bindings, "workgroup":workgroup}
            try:
                with phase("stage kernel", entry=entry, expected_key=KEYS[entry]):
                    k = kernel(source_file, bindings, entry, defines, workgroup, quiet)
                    if k.key != KEYS[entry]:
                        raise ValueError("Native stage identity differs")
                    return k
            finally:
                active = None

        def traced(original, name):
            def capture(*args, **kwargs):
                if active is None:
                    return original(*args, **kwargs)
                entry = active["entry"]
                fields = dict(entry=entry)
                if name=="create_shader_module":
                    fields["source_sha256"] = hashlib.sha256(kwargs["code"].encode()).hexdigest()
                    active["key"] = shader_key(kwargs["code"],entry,active["bindings"],active["workgroup"])
                    if fields["source_sha256"] != SOURCE_SHA or active["key"] != KEYS[entry]:
                        raise ValueError("Unexpected expanded stage source or pipeline key")
                if name=="create_compute_pipeline" and kwargs["compute"]["entry_point"]!=entry:
                    raise ValueError("Unexpected dispatched shader entry")
                fields["key"] = active["key"]
                with phase(name, **fields):
                    return original(*args, **kwargs)
            return capture

        with phase("cold stage on admitted device"), ExitStack() as stack:
            stack.enter_context(patch.object(gpu,"kernel",trace_kernel))
            device_type = type(gpu.device)
            for name in ("create_shader_module","create_bind_group_layout","create_pipeline_layout","create_compute_pipeline"):
                stack.enter_context(patch.object(device_type,name,traced(getattr(device_type,name),name)))
            stage = eng.stage
            result["stage_keys"] = {"main":stage.k.key,"caustics":stage.k_caustics.key}
            if result["stage_keys"]!=KEYS:
                raise ValueError("Unexpected stage kernels")
            save(out/"RESULT.json",result)

        probe=Scene()
        probe.emitters.clear()
        probe.add_fabric()
        for section,key,value in (("domain","resolution",32),("domain","preroll",0),("domain","disk_cache",True),
                ("domain","cache_dir",str(cache)),("render","fps",24),("render","auto_resolution",False),
                ("render","upres",1),("render","motion_blur",False)):
            probe.set((section,key),value)
        if probe.start!=1 or probe.kind!="fire" or probe.emitters or len(probe.fabrics)!=1:
            raise ValueError("Unexpected neutral fixture")
        with phase("prepare neutral fixture"):
            eng.prepare(probe,final=True)
            result["scene"] = dict(grid=list(eng.solver.dims),cloth_vertices=int(eng.cloth.built.n),
                                   preroll_frames=eng.preroll_frames(probe))
            if result["scene"]!=json.loads(REFERENCE.read_bytes())["scene"]:
                raise ValueError("Native scene dimensions differ from T130")
        with phase("ordinary neutral frame 1"):
            eng.simulate_to(probe,1,cache=True)
            eng.cache.disk.flush()
        with phase("ordinary neutral frame 2"):
            eng.simulate_to(probe,2,cache=False)
        with phase("frame 2 native reference check"):
            receipt = digest(dict(frame=eng.sim_frame, gas=eng.solver.save_state(), cloth=eng.cloth.save_state(),
                                  feedback_grid=np.frombuffer(gpu.read_buffer(eng.cloth.G),dtype=np.uint32),
                                  feedback_ready=eng.cloth._couple_filled))
            if receipt!=json.loads(REFERENCE.read_bytes())["ordinary_successor"]:
                raise ValueError("Fresh ordinary state differs from T130")
            result["neutral_frame2_matches_t130"]=True
            save(out/"RESULT.json", result)
        before=(eng.sim_frame,eng.solver.steps)
        with phase("native composite with prepared stage"):
            if eng.stage is not stage:
                raise ValueError("Engine changed stages")
            eng.render(probe,2,(320,180),mode="composite",final=True,samples=1,motion_blur=False,seed=0)
        with phase("synchronous linear composite read"):
            pixels=eng.linear_comp()
        if pixels.shape!=(180,320,4) or not np.isfinite(pixels).all() or before!=(eng.sim_frame,eng.solver.steps):
            raise ValueError("Unexpected output shape, value or physics advance")
        with phase("persist pixels"):
            temp=out/"composite-pending.npz"
            np.savez_compressed(temp,pixels=pixels)
            temp.replace(out/"composite.npz")
            rgb=pixels[...,:3]
            result.update(status="complete",native_pixels=digest(pixels),rgb_range=[float(rgb.min()),float(rgb.max())],
                          nonzero_rgb_pixels=int((rgb!=0).any(axis=2).sum()),frame=eng.sim_frame,steps=eng.solver.steps)
            save(out/"RESULT.json",result)
        return 0
    except Exception as ex:
        result.update(status="error",exception=type(ex).__name__,
                      reason=str(ex).replace(str(root),"<source>").replace(str(Path.home()),"<home>")[:1200])
        save(out/"RESULT.json",result)
        return 2


def supervise(source,out):
    out.mkdir(parents=True,exist_ok=False)
    start=time.time()
    perf=time.perf_counter()
    awake=awake_seconds()
    last=start
    largest_gap=0.
    with tempfile.TemporaryDirectory(prefix="t132-neutral-") as cache:
        argv=[sys.executable,__file__,"--source",str(source),"--out",str(out),"--worker-cache",cache]
        proc=subprocess.Popen(argv)
        try:
            while True:
                now=time.time()
                largest_gap=max(largest_gap,now-last)
                last=now
                if max(now-start,time.perf_counter()-perf)>=LIMIT:
                    if proc.poll() is None:
                        proc.kill()
                    proc.wait()
                    status,code="time_limit",2
                    break
                if proc.poll() is not None:
                    status,code="returned",proc.returncode
                    break
                time.sleep(.25)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
    end=time.time()
    row=dict(status=status,exit=code,worker_exit=proc.returncode,limit_s=LIMIT,
             start_utc=datetime.fromtimestamp(start,timezone.utc).isoformat(),end_utc=datetime.fromtimestamp(end,timezone.utc).isoformat(),
             elapsed_wall_s=end-start,monotonic_s=time.perf_counter()-perf,windows_awake_s=awake_seconds()-awake,
             largest_poll_gap_s=largest_gap)
    save(out/"EXIT.json",row)
    return code


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--worker-cache",type=Path)
    a=p.parse_args()
    if a.worker_cache:
        sys.exit(worker(a.source.resolve(),a.out.resolve(),a.worker_cache))
    sys.exit(supervise(a.source.resolve(),a.out.resolve()))
