"""Test cold native continuation with a single neutral disk cache and independent processes."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from time import perf_counter, sleep
from unittest.mock import patch

import numpy as np


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "t125-nvidia-dx12-admission"))
from admit import PIN, save, select

ARMS = ("reference", "ordinary", "supplemented")
LIMIT = 180


def digest(b):
    return hashlib.sha256(b).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def make_fixture(cache):
    from blackbody.scene.model import Scene
    scene = Scene()
    scene.emitters.clear()
    scene.add_fabric()
    for group, key, value in (
        ("domain", "resolution", 32), ("domain", "preroll", 0), ("domain", "disk_cache", True),
        ("domain", "cache_dir", str(cache)), ("render", "fps", 24), ("render", "auto_resolution", False),
        ("render", "upres", 1), ("render", "motion_blur", False),
    ):
        scene.set((group, key), value)
    require(scene.start == 1 and scene.kind == "fire" and not scene.emitters and len(scene.fabrics) == 1,
            "Neutral scene mismatch")
    return scene


def freeze(value, prefix, arrays):
    if isinstance(value, np.ndarray):
        a = np.ascontiguousarray(value)
        arrays[prefix] = a
        return {"dtype": str(a.dtype), "shape": list(a.shape), "sha256": digest(a.tobytes())}
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): freeze(v, prefix+"."+str(k), arrays) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [freeze(v, prefix+"."+str(i), arrays) for i, v in enumerate(value)]
    return value


def layout(engine):
    s = engine.solver
    return dict(dims=list(map(int, s.dims)), origin=list(map(float, s.origin)), cell=float(s.h))


def pending(engine):
    c = engine.cloth
    return dict(dims=list(map(int, c.couple_dims)) if c.couple_dims is not None else None,
                ready=bool(getattr(c, "_couple_filled", False)), wet=bool(c._may_be_wet),
                placed=bool(c.placed), active=bool(c.active),
                grid=None if c.G is None else np.frombuffer(engine.gpu.read_buffer(c.G), np.uint32).copy())


def describe(engine, target):
    arrays = {}
    state = dict(frame=int(engine.sim_frame), gas=engine.solver.save_state(), cloth=engine.cloth.save_state(),
                 embers=engine.embers.save_state(), feedback=pending(engine))
    receipt = freeze(state, "state", arrays)
    np.savez_compressed(target, **arrays)
    return receipt


def native_restore(engine, scene):
    require(engine.sim_frame is None and engine.cloth.G is None and not engine.cloth.placed,
            "Restore engine has previous live state")
    disk = engine.cache.disk
    require(disk is not None and disk.readonly and list(disk.checkpoints()) == [1], "Expected single readonly checkpoint")
    with patch.object(engine, "step_frame", side_effect=RuntimeError("Unwanted simulation during disk restore")):
        require(engine.simulate_to(scene, 1, cache=True) and engine.sim_frame == 1, "Native restore failed")


def save_supplement(engine, scene, cache, out):
    from blackbody.engine.cloth import COUPLE_CHANNELS
    start = perf_counter()
    f = pending(engine)
    read_s = perf_counter()-start
    g = f.pop("grid")
    require(COUPLE_CHANNELS == 13 and f["ready"] and len(g) == np.prod(f["dims"])*13, "Unexpected feedback layout")
    raw = g.tobytes()
    meta = dict(frame=engine.sim_frame, scene=scene.sim_signature(True), gas_layout=layout(engine),
                format="uint32", channels=13, feedback=f, bytes=len(raw), sha256=digest(raw))
    start_write = perf_counter()
    (cache/"feedback.bin").write_bytes(raw)
    metadata = json.dumps(meta, allow_nan=False, sort_keys=True, separators=(",",":")).encode()
    (cache/"feedback.json").write_bytes(metadata)
    write_s = perf_counter()-start_write
    verifier = out/"reference-parent.npz"
    with np.load(verifier, allow_pickle=False) as observed:
        require(np.array_equal(observed["state.feedback.grid"],g), "Supplement differs from audited parent")
    return dict(metadata=meta, metadata_bytes=len(metadata), read_s=read_s, write_s=write_s)


def restore_supplement(engine, scene, cache):
    from blackbody.engine.cloth import COUPLE_CHANNELS
    started = perf_counter()
    meta = json.loads((cache/"feedback.json").read_bytes())
    raw = (cache/"feedback.bin").read_bytes()
    f = meta["feedback"]
    require(meta["frame"]==engine.sim_frame and meta["scene"]==scene.sim_signature(True), "Unexpected supplement identity")
    require(meta["gas_layout"]==layout(engine) and COUPLE_CHANNELS==meta["channels"]==13, "Incompatible gas layout")
    c = engine.cloth
    require(f["placed"]==c.placed and f["active"]==c.active and f["wet"]==c._may_be_wet, "Incompatible cloth flags")
    require(meta["format"]=="uint32" and len(raw)==meta["bytes"] and digest(raw)==meta["sha256"], "Invalid feedback file")
    c.prepare_frame(engine.solver)
    require(list(c.couple_dims)==f["dims"] and c._couple_ok(engine.solver), "Incompatible cloth grid")
    require(len(raw)==int(np.prod(c.couple_dims))*COUPLE_CHANNELS*4, "Incorrect feedback byte size")
    engine.gpu.write_buffer(c.G, np.frombuffer(raw,np.uint32))
    c._couple_filled=f["ready"]
    submitted=perf_counter()
    require(bytes(engine.gpu.read_buffer(c.G))==raw, "Native feedback copy differs")
    return dict(raw_bytes=len(raw),validated_read_and_upload_submit_s=submitted-started,
                verification_read_s=perf_counter()-submitted)


def run_worker(arm, source, cache, out):
    from time import time
    row = dict(arm=arm, revision=PIN, pid=os.getpid(), status="running", timings_s={})
    dest = out/(arm+".json")
    begin = perf_counter()
    @contextmanager
    def phase(key):
        row["last_phase"] = key
        save(dest, row)
        started = perf_counter()
        try:
            yield
        finally:
            row["timings_s"][key] = perf_counter()-started
            row["wall_s"] = perf_counter()-begin
            save(dest, row)
    try:
        with phase("device_and_scene"):
            card = select(source)
            row["adapter"] = card
            from blackbody.engine.engine import Engine
            from blackbody.engine.gpu import GPU
            gpu = GPU(adapter_name=card["device"], backend=card["backend_type"])
            require(gpu.name==card["device"] and gpu.backend==card["backend_type"], "Wrong adapter")
            scene = make_fixture(cache)
            row["scene"] = scene.sim_signature(True)
        with phase("construct_and_prepare"):
            engine = Engine(gpu)
            engine.cache_readonly = arm != "reference"
            engine.prepare(scene, final=True)
            require(engine.cloth.built.n==1470 and list(engine.solver.dims)==[16,32,16], "Unexpected fixture")
        if arm == "reference":
            with phase("create_native_checkpoint"):
                require(engine.simulate_to(scene, 1, cache=True), "Reference failed")
                engine.cache.disk.flush()
                require(list(engine.cache.disk.checkpoints())==[1], "No disk checkpoint")
                file = engine.cache.disk._path(1)
                row["native_checkpoint"] = dict(bytes=file.stat().st_size, sha256=digest(file.read_bytes()))
        else:
            with phase("cold_native_restore"):
                native_restore(engine, scene)
                file = engine.cache.disk._path(1)
                row["native_checkpoint"] = dict(bytes=file.stat().st_size, sha256=digest(file.read_bytes()))
                ref = json.loads((out/"reference.json").read_bytes())
                require(row["native_checkpoint"]==ref["native_checkpoint"], "Native checkpoint bytes changed")
        with phase("audit_parent"):
            row["native_parent"]=describe(engine,out/(arm+"-parent.npz"))
        if arm == "reference":
            with phase("save_supplement"):
                row["supplement"]=save_supplement(engine,scene,cache,out)
        elif arm == "supplemented":
            with phase("restore_supplement"):
                row["supplement"]=restore_supplement(engine,scene,cache)
            with phase("audit_supplement"):
                row["corrected_parent"]=describe(engine,out/"supplemented-corrected-parent.npz")
        with phase("advance_one_native_frame"):
            require(engine.simulate_to(scene, 2, cache=False) and engine.sim_frame==2, "Successor failed")
        with phase("audit_successor"):
            row["successor"]=describe(engine,out/(arm+"-successor.npz"))
        row["status"]="primary_complete"
        save(dest,row)
        if arm=="supplemented":
            try:
                with phase("new_engine_warm_device"):
                    other=Engine(gpu)
                    other.cache_readonly=True
                    other.prepare(scene,final=True)
                    native_restore(other,scene)
                    require(other.cloth.G is None and not getattr(other.cloth,"_couple_filled",False), "Unexpected old feedback")
                    aux_parent=describe(other,out/"rebuild-cold-parent.npz")
                    row["rebuild_native_parent"]=aux_parent
                    require(aux_parent==row["native_parent"], "Auxiliary engine did not start from identical cold restore")
                    imp=np.frombuffer(gpu.read_buffer(other.cloth.bufs["IMP"]),np.uint32)
                    row["rebuild_cold_imp"]=dict(bytes=imp.nbytes,nonzero=int(np.count_nonzero(imp)),sha256=digest(imp.tobytes()))
                with phase("rebuild_and_synchronize"):
                    other.cloth.prepare_frame(other.solver)
                    with gpu.batch() as batch:
                        other.cloth.splat(batch,other.solver,scene.look(1))
                    rebuilt=pending(other)
                arrays={}
                row["rebuilt_feedback"]=freeze(rebuilt,"feedback",arrays)
                np.savez_compressed(out/"rebuilt-feedback.npz",**arrays)
                row["rebuild_status"]="complete"
            except Exception as exc:
                row["rebuild_status"]="failed"
                row["rebuild_error"]=str(exc).replace(str(Path.home()),"<home>").replace(str(cache),"<cache>")
        row["status"]="complete"
        save(dest,row)
        return 0
    except Exception as exc:
        row.update(status="failed",exception=type(exc).__name__,
                   reason=str(exc).replace(str(Path.home()),"<home>").replace(str(cache),"<cache>")[:1600])
        save(dest,row)
        return 2


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--worker",choices=ARMS)
    parser.add_argument("--cache",type=Path)
    a=parser.parse_args()
    out=a.out.resolve()
    if a.worker:
        return run_worker(a.worker,a.source.resolve(),a.cache.resolve(),out)
    out.mkdir(parents=True,exist_ok=False)
    exits={}
    with tempfile.TemporaryDirectory(prefix="vg-fresh-checkpoint-") as cache:
        for arm in ARMS:
            started=perf_counter()
            argv=[sys.executable,__file__,"--source",str(a.source),"--out",str(out),"--worker",arm,"--cache",cache]
            child=subprocess.Popen(argv)
            timeout=False
            while child.poll() is None:
                if perf_counter()-started>=LIMIT:
                    timeout=True
                    child.kill()
                    break
                sleep(.25)
            exitcode=child.wait()
            elapsed=perf_counter()-started
            exits[arm]=dict(pid=child.pid,returncode=exitcode,timeout=timeout,limit_s=LIMIT,elapsed_s=elapsed)
            save(out/"workers.json",exits)
            if arm=="reference" and (exitcode or timeout):
                break
    return int(len(exits)!=len(ARMS) or any(x["returncode"] or x["timeout"] for x in exits.values()))


if __name__=="__main__":
    sys.exit(main())
