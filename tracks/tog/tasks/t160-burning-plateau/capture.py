"""Obtain the single registered native burn-duration alternative and two matched-input controls."""
import argparse
import dataclasses
import json
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "t154-native-surface-fork"))
from run import T151, PIN, arrays_and_values, json_hash, require, save, select, settings, state, summary
from capture_surface import atlas_stats, digest

LIMIT = 420
ROI = ((54, 0, 11), (46, 64, 13))


def lower_after(lower, dt):
    if lower is None or not 0 < dt <= float(np.float32(1/24)):
        return None
    value = np.nextafter(lower - float(np.float32(.2)) * dt - 2**-10 - 2**-20, -np.inf)
    return float(value) if value > np.float32(.15) else None


def contrast(batch, solver, zero, dt, fine, original, args, directory, stage):
    """Run the unmodified kernel twice. Only the first dispatch reads the zero object binding."""
    native = batch.run
    calls = 0
    def diagnostic(kernel, bindings, uniforms, size):
        nonlocal calls
        require(kernel is solver._k["react"] and bindings[11] is solver.burn_obj[0] and
                bindings[11].size == zero.size and not any((solver.stain, solver.aux, solver.chem)) and
                bindings[0] is not bindings[6], "Unsupported native reaction resources")
        g = np.frombuffer(uniforms.tobytes(), dtype="<f4").reshape(-1, 4)
        scale = solver.upres if fine else 1
        require(float(g[2,3]) == np.float32(dt) and list(g[8,:3]) == [9.,.5,1.] and
                g[9,1] == 1 and g[12,0] == scale and g[12,3] == 0, "Unexpected reaction uniforms")
        origin, box = [tuple(v*scale for v in xyz) for xyz in ROI]
        require(all(o + n <= d for o,n,d in zip(origin,box,size)), "Control crop outside gas domain")
        control = list(bindings)
        control[11] = zero
        t = time.perf_counter()
        native(kernel, control, uniforms, size)
        batch.submit(restart=True)
        off = solver.gpu.read(bindings[6], origin, box).copy()
        native(kernel, bindings, uniforms, size)
        batch.submit(restart=True)
        on = solver.gpu.read(bindings[6], origin, box)
        key = "fine" if fine else "coarse"
        require(off.shape == on.shape == (*box[::-1],4) and off.dtype == on.dtype == np.float16, "Control format")
        np.savez_compressed(directory / (key + "-react.npz"), off=off, on=on)
        stage[key] = dict(origin=list(origin), size=list(box), grid=list(size), dt_f32=float(g[2,3]),
                          uniforms_sha256=digest(g), off_sha256=digest(off), on_sha256=digest(on),
                          seconds=time.perf_counter()-t)
        calls += 1
    with patch.object(batch, "run", diagnostic):
        original(batch, dt, *args, fine=fine)
    require(calls == 1, "Unexpected number of native reaction dispatches")


def run(source, directory):
    start = time.perf_counter()
    meta = dict(status="started", pin=PIN, phase="admission")
    receipt = directory / "extended.json"
    save(receipt, meta)
    try:
        card = select(source)
        from blackbody.engine.gpu import GPU
        from blackbody.engine.engine import Engine
        scene = settings("default")
        spread = scene.data["spread"]
        require(spread["burn_time"] == 5 and spread["catch_time"] == .35 and spread["coverage"] == 1
                and spread["enabled"] and not spread["ground"] and not spread["spotting"], "Unexpected native preset")
        meta.update(adapter=card, base_scene=json_hash(scene.to_dict()), phase="preparation")
        spread["burn_time"] = 10.
        save(directory / "extended-scene.json", scene.to_dict())
        meta["edited_scene"] = json_hash(scene.to_dict())
        save(receipt, meta)
        gpu = GPU(adapter_name=card["device"], backend=card["backend_type"])
        require(gpu.name == card["device"] and gpu.backend == card["backend_type"], "Device mismatch")
        engine = Engine(gpu)
        engine.prepare(scene, final=True)
        s = engine.solver
        require(not engine.cloth.active and not engine.solids.active and not engine.strands_on and
                not any((s.water, s.chem, s.aux, s.stain)), "Unsupported coupling")
        meta.update(phase="ordinary", dims=list(s.dims), fine_upres=s.upres, features=s.features,
                    preparation_s=time.perf_counter()-start)
        save(receipt, meta)
        frame = substep = count = inits = uniforms_count = 0
        lower = .75
        previous = zero = None
        control = {}
        timing = dict(atlas_and_checkpoint_s=0., frame_end_embers_s=0.)
        init, step, advance, react = s._init_burn, s.step, engine.step_frame, s._react
        native_material_uniforms=s._burn_obj_uniforms
        with (directory / "extended.jsonl").open("x",encoding="utf-8") as ledger, (directory / "extended-atlas.zlib").open("xb") as blob:
            def write(rec):
                ledger.write(json.dumps(rec, allow_nan=False, separators=(",",":"))+"\n")
                ledger.flush()
            def capture(kind, checkpoint):
                nonlocal previous
                begin = time.perf_counter()
                extra = {}
                if checkpoint:
                    native = s.save_state()
                    a = native.pop("burn_obj")
                    require(not np.any(native["burn"][...,1:]), "Floor contributes emission")
                    extra["state"] = arrays_and_values(native)
                else:
                    a = s.read_burn_obj()
                a = np.ascontiguousarray(a)
                require(a.dtype == np.float16 and a.ndim == 4 and a.shape[-1]==4 and np.isfinite(a).all(), "Atlas format")
                if previous is None:
                    live = a[...,2] > .5
                    require(np.any(live) and a[...,0][live].min() >= .75 and a[...,0][live].max() <= 1.25
                            and not np.any(a[...,1]) and not np.any(a[...,3]), "Initial plateau guard failed")
                words = a.view(np.uint8).reshape(-1)
                delta = words if previous is None else words ^ previous
                payload = zlib.compress(delta,4)
                offset = blob.tell()
                blob.write(payload)
                blob.flush()
                previous = words.copy()
                write(dict(kind=kind,index=count,frame=frame,substep=substep,atlas=dict(offset=offset,size=len(payload),
                           sha256=digest(a),shape=list(a.shape),dtype=a.dtype.str,**atlas_stats(a)),**extra))
                timing["atlas_and_checkpoint_s"] += time.perf_counter()-begin
            def initialize(b, prm):
                nonlocal inits, zero
                init(b,prm)
                b.submit(restart=True)
                inits += 1
                require(inits==1 and count==0, "Reinitialized object atlas")
                capture("initialized", True)
                dims = s.burn_obj[0].size
                zero = gpu.texture3d(dims, "rgba16float", "object-off-control")
                gpu.upload(zero, np.zeros((*dims[::-1],4), dtype=np.float16))
                require(not np.any(gpu.read(zero).view("<u2")), "Control atlas is not canonical positive zero")
            def observation(b, dt, prm, ems, fine=False):
                if frame == 36 and substep == 0:
                    contrast(b,s,zero,dt,fine,react,(prm,ems),directory,control)
                else:
                    react(b,dt,prm,ems,fine=fine)
            def material_uniforms(dt,prm,douse):
                nonlocal uniforms_count
                u=native_material_uniforms(dt,prm,douse)
                data=np.frombuffer(u.tobytes(),dtype="<f4").reshape(-1,4)
                if dt>0:
                    require(data[2,3]==np.float32(dt) and data[3,3]==np.float32(.1) and
                            data[3,1]==np.float32(1/.35), "Actual native material uniform changed")
                    write(dict(kind="burn_uniform",index=count,frame=frame,substep=substep,
                               dt_f32=float(data[2,3]),rate_f32=float(data[3,3]),sha256=digest(data)))
                    uniforms_count+=1
                return u
            def native_step(b, dt, prm, ems, colliders=None):
                nonlocal count, substep, lower
                args = dataclasses.asdict(prm)
                dd = args["spread"]
                require(dd.pop("catch_time")==.35 and dd["burn_time"]==10 and dd["coverage"]==1 and not
                        dd["spotting"] and not dd["ground"] and all(e.douse<=0 for e in ems) and
                        colliders is None and s.pieces_step is None, "Unsupported effective forcing")
                dd["burn_time"] = 5.
                dt32, rate = float(np.float32(dt)),float(np.float32(1/prm.spread.burn_time))
                lower = lower_after(lower,dt32)
                write(dict(kind="update",index=count,frame=frame,substep=substep,dt=dt,dt_f32=dt32,rate_f32=rate,
                           lower_after=lower,forcing=json_hash([args,ems,s.colliders,s.features])))
                step(b,dt,prm,ems,colliders)
                count += 1
                require(uniforms_count==count,"Missing or duplicated native material dispatch uniforms")
                substep += 1
                b.submit(restart=True)
                capture("post_update", frame<=12)
            def frame_step(scn, f):
                nonlocal frame, substep
                frame,substep = f,0
                advance(scn,f)
                require(substep==engine.last_substeps,"Adaptive step count differs")
                stage = time.perf_counter()
                end = dict(kind="frame_end",index=count,frame=frame,substep=substep,embers=arrays_and_values(engine.embers.save_state()))
                if frame>12:
                    native = s.save_state()
                    a = native.pop("burn_obj")
                    require(digest(a)==digest(previous) and not np.any(native["burn"][...,1:]), "Frame-end material differs")
                    end["state"] = arrays_and_values(native)
                write(end)
                timing["frame_end_embers_s"] += time.perf_counter()-stage
            with patch.object(s,"_init_burn",initialize), patch.object(s,"_react",observation), patch.object(s,"_burn_obj_uniforms",material_uniforms), patch.object(s,"step",native_step), patch.object(engine,"step_frame",frame_step):
                require(engine.simulate_to(scene,36,cache=False) and engine.sim_frame == 36, "Incomplete native shot")
        require(inits==1 and set(control)=={"coarse","fine"}, "Missing native diagnostics")
        save(directory/"extended-36.json",summary(state(engine)))
        meta.update(status="complete",phase="complete", frames=frame, updates=count, controls=control,
                    observer=timing, elapsed_s=time.perf_counter()-start)
        save(receipt,meta)
    except Exception as exc:
        meta.update(status="error",error=str(exc).replace(str(source),"<engine>").replace(str(Path.home()),"<home>")[:900],
                    elapsed_s=time.perf_counter()-start)
        save(receipt,meta)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--worker", action="store_true")
    a = p.parse_args()
    folder, source = a.out.resolve(), a.source.resolve()
    if a.worker:
        run(source,folder)
    else:
        folder.mkdir(exist_ok=False)
        now = time.perf_counter()
        with (folder/"extended.log").open("x") as log:
            try:
                child = subprocess.run([sys.executable,"-B",__file__,"--worker","--source",str(source),"--out",str(folder)],
                                       stdout=log,stderr=log,timeout=LIMIT)
                code = child.returncode
            except subprocess.TimeoutExpired:
                code = None
        save(folder/"extended-exit.json",dict(exit=code,expired=code is None,limit_s=LIMIT,wall_s=time.perf_counter()-now))
        sys.exit(0 if code==0 else 1)
