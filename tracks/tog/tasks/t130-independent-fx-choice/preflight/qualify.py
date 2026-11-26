"""Qualify native output and serialized continuation on an unedited, unheated test fixture."""
import argparse
from contextlib import ExitStack
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
sys.path.insert(0, str(HERE.parents[1] / "t125-nvidia-dx12-admission"))
from admit import save, select

LIMIT = 360


def observe(source, output, cache, native_read_fence=False):
    import numpy as np
    started = time.perf_counter()
    result = {"status": "started", "fixture": "empty gas and one default unheated fabric patch",
              "fence": "native texture read" if native_read_fence else "explicit queue completion"}

    def log(phase, event, **fields):
        row = dict(phase=phase, event=event, elapsed_s=time.perf_counter()-started, **fields)
        with (output / "PHASES.ndjson").open("a", encoding="utf8") as stream:
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def phase(name, function, *args, **kwargs):
        log(name, "start")
        value = function(*args, **kwargs)
        log(name, "returned")
        return value

    def freeze(value):
        if isinstance(value, np.ndarray):
            a = np.ascontiguousarray(value)
            return dict(dtype=str(a.dtype), shape=list(a.shape), sha256=hashlib.sha256(a.tobytes()).hexdigest())
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, dict):
            return {k:freeze(v) for k,v in value.items()}
        if isinstance(value, (list,tuple)):
            return [freeze(v) for v in value]
        return value

    def feedback(engine):
        data = {"ready": bool(getattr(engine.cloth, "_couple_filled", False))}
        if getattr(engine.cloth, "G", None) is not None:
            words = np.frombuffer(engine.gpu.read_buffer(engine.cloth.G), dtype=np.uint32)
            data.update(array=freeze(words),nonzero_words=int(np.count_nonzero(words)))
        return data

    def state(engine):
        data = dict(frame=engine.sim_frame, gas=engine.solver.save_state(), cloth=engine.cloth.save_state(),
                    feedback_ready=getattr(engine.cloth, "_couple_filled", False))
        if getattr(engine.cloth, "G", None) is not None:
            data["feedback_grid"] = np.frombuffer(engine.gpu.read_buffer(engine.cloth.G), dtype=np.uint32)
        return freeze(data)

    def write_result():
        save(output / "PREFLIGHT.json", result)

    try:
        card = phase("adapter", select, source)
        from blackbody.engine.engine import Engine
        from blackbody.engine.gpu import GPU
        from blackbody.scene.model import Scene
        probe = Scene()
        probe.emitters.clear()
        probe.add_fabric()
        for section,key,value in (("domain","resolution",32),("domain","preroll",0),("domain","disk_cache",True),
                                  ("domain","cache_dir",str(cache)),("render","fps",24),("render","auto_resolution",False),
                                  ("render","upres",1),("render","motion_blur",False)):
            probe.set((section,key),value)
        if probe.start != 1 or probe.kind != "fire" or probe.emitters or len(probe.fabrics)!=1:
            raise RuntimeError("Unexpected preflight inputs")
        result["adapter"] = card
        write_result()
        gpu = phase("open_native_device",GPU,adapter_name=card["device"],backend=card["backend_type"])
        if gpu.name!=card["device"] or gpu.backend!=card["backend_type"]:
            raise RuntimeError("Hardware mismatch")
        gpu.on_compile = lambda path: log("native_compute_pipeline", "cache_miss", shader=Path(str(path)).name)
        eng = phase("construct_engine",Engine,gpu)
        phase("prepare",eng.prepare,probe,final=True)
        result["scene"] = dict(grid=list(eng.solver.dims),cloth_vertices=int(eng.cloth.built.n),preroll_frames=eng.preroll_frames(probe))
        phase("frame_1_with_checkpoint",eng.simulate_to,probe,1,cache=True)
        if native_read_fence:
            cloth=eng.cloth.state()
            result["checkpoint_observation"]=dict(feedback=feedback(eng),temperature_k=[float(cloth[:,0].min()),float(cloth[:,0].max())],
                                                 burning_vertices=int((cloth[:,2]>.5).sum()))
            write_result()
        disk=eng.cache.disk
        if disk is None:
            raise RuntimeError("Native disk cache was not mounted")
        phase("flush_disk_checkpoint",disk.flush)
        if list(disk.checkpoints()) != [1]:
            raise RuntimeError("Missing single checkpoint at frame 1")
        phase("ordinary_successor",eng.simulate_to,probe,2,cache=False)
        first=phase("ordinary_successor_digest",state,eng)
        phase("native_reset",eng.reset)
        resume = eng._resume
        def witness(scene, frame):
            ok=resume(scene,frame)
            result["restored_frame"] = eng.sim_frame if ok else None
            return ok
        with patch.object(eng, "_resume", witness):
            phase("restore_and_resume_successor",eng.simulate_to,probe,2,cache=True)
        if result.get("restored_frame")!=1:
            raise RuntimeError("Native resume did not select frame 1")
        second=phase("resumed_successor_digest",state,eng)
        result.update(ordinary_successor=first,resumed_successor=second,successor_equal=(first==second))
        write_result()
        settings=dict(final=True,samples=1,motion_blur=False,seed=0)
        with ExitStack() as stack:
            for obj,name in ((eng,"volume_for"),(eng.renderer,"light"),(eng.cloth,"prepare_light"),
                             (eng,"_draw_raster"),(eng.renderer,"march"),(eng.renderer,"composite")):
                original=getattr(obj,name)
                stack.enter_context(patch.object(obj,name,lambda *args,fn=original,tag=name,**kw:phase(tag,fn,*args,**kw)))
            for mode in ("fire","composite"):
                frame_steps=eng.solver.steps
                phase(mode+"_render",eng.render,probe,2,(320,180),mode=mode,**settings)
                if not native_read_fence:
                    phase(mode+"_queue_fence",gpu.queue.on_submitted_work_done_sync)
                pixels=(phase("emission_readback",gpu.read,eng.renderer.emit) if mode=="fire" else
                        phase("linear_composite_readback",eng.linear_comp))
                if pixels.shape!=(180,320,4) or not np.isfinite(pixels).all():
                    raise ValueError("Unexpected native "+mode+" readback")
                if eng.sim_frame!=2 or eng.solver.steps!=frame_steps:
                    raise RuntimeError("Native rendering advanced physics")
                rgb=pixels[...,:3]
                result[mode]=dict(array=freeze(pixels),rgb_min=float(rgb.min()),rgb_max=float(rgb.max()),
                                  nonzero_rgb_pixels=int((rgb!=0).any(axis=2).sum()))
                if native_read_fence:
                    np.savez_compressed(output/(mode+".npz"),pixels=pixels)
                write_result()
        result["status"]="outputs_returned"
        write_result()
        log("preflight","complete")
        return 0
    except Exception as exc:
        result.update(status="error",exception=type(exc).__name__,
                      reason=str(exc).replace(str(cache),"<cache>").replace(str(source),"<source>").replace(str(Path.home()),"<home>")[:1800])
        write_result()
        log("preflight","error",exception=type(exc).__name__)
        return 2


if __name__ == "__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--cache-worker",type=Path)
    ap.add_argument("--native-read-fence",action="store_true")
    a=ap.parse_args()
    if a.cache_worker:
        sys.exit(observe(a.source.resolve(),a.out.resolve(),a.cache_worker.resolve(),a.native_read_fence))
    a.out.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="t130-neutral-") as tmp:
        argv=[sys.executable,__file__,"--source",str(a.source),"--out",str(a.out),"--cache-worker",tmp]
        if a.native_read_fence:
            argv.append("--native-read-fence")
        try:
            child=subprocess.run(argv,timeout=LIMIT)
            code=child.returncode
            status="returned"
        except subprocess.TimeoutExpired:
            code=2
            status="time_limit"
        save(a.out/"EXIT.json",dict(status=status,exit=code,limit_s=LIMIT,elapsed_s=time.perf_counter()-start))
        sys.exit(code)
