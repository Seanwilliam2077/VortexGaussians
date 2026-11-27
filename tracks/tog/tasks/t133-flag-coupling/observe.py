"""Instrument the two ordinary flag trajectories at every native gas boundary."""
import argparse
import dataclasses
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "t125-nvidia-dx12-admission"))
from admit import PIN, save, select

LIMIT = 240


def encode(value):
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(type(value).__name__)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_hash(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), default=encode,
                             allow_nan=False).encode())


def arrays_and_values(state):
    summary = {}
    for key, value in state.items():
        if isinstance(value, np.ndarray):
            raw = np.ascontiguousarray(value)
            if not np.isfinite(raw).all():
                raise ValueError(f"Nonfinite native {key}")
            summary[key] = dict(shape=list(raw.shape), dtype=raw.dtype.str, sha256=digest(raw))
        else:
            summary[key] = value
    return summary


def require(condition, msg):
    if not condition:
        raise ValueError(msg)


def worker(source, out, arm):
    start = time.perf_counter()
    summary = {"arm":arm, "pin":PIN, "status":"started", "last_phase":"admission"}
    summary_path = out / f"{arm}.json"
    save(summary_path, summary)
    try:
        card = select(source)
        from blackbody.scene.presets import make
        from blackbody.engine.engine import Engine
        from blackbody.engine.gpu import GPU
        scene = make("flag_wind", fps=24)
        require(len(scene.fabrics)==1 and scene.fabrics[0]["bend"] == 1 and
                not scene.fabrics[0]["burnable"] and scene.fabrics[0]["material"]=="nylon" and
                scene.start==1 and scene.fps==24 and scene.data["domain"]["preroll"]==1, "Wrong preset")
        shared = json_hash(scene.to_dict())
        if arm == "stiffer":
            scene.fabrics[0]["bend"] = 2.0
        input_data = scene.to_dict()
        save(out / f"{arm}-scene.json", input_data)
        summary.update(adapter=card, last_phase="native preparation", original_settings=shared,
                       settings=json_hash(input_data), stiffness=scene.fabrics[0]["bend"])
        save(summary_path, summary)
        gpu = GPU(adapter_name=card["device"], backend=card["backend_type"])
        require(gpu.name==card["device"] and gpu.backend==card["backend_type"], "Adapter changed")
        eng = Engine(gpu)
        eng.prepare(scene, final=True)
        solver, cloth = eng.solver, eng.cloth
        require(cloth.active and not eng.solids.active and not eng.strands_on and not scene.colliders_animated()
                and solver.upres==1 and not scene.data["domain"]["grow"], "Unsupported coupling configuration")
        summary.update(last_phase="native trajectories", preparation_wall_s=time.perf_counter()-start,
                       gas_dims=list(solver.dims), h=solver.h, cloth_vertices=cloth.built.n,
                       features=solver.features, scene_signature=scene.sim_signature(True))
        save(summary_path, summary)
        step = solver.step
        frame_step = eng.step_frame
        position = {"frame":None, "substep":0, "index":0}
        with (out/f"{arm}-grids.zlib").open("wb") as archive, (out/f"{arm}-steps.ndjson").open("w", encoding="utf8") as ledger:
            def append(row):
                ledger.write(json.dumps(row, separators=(",", ":"), allow_nan=False, default=encode)+"\n")
                ledger.flush()

            def capture(kind):
                gas = solver.save_state()
                material = cloth.save_state()
                require(material is not None, "Cloth absent at observed input")
                cloth_arrays = {k:v for k,v in material.items() if k!="key"}
                grid = gpu.read_buffer(cloth.G)
                offset = archive.tell()
                payload = zlib.compress(grid, 1)
                archive.write(payload)
                archive.flush()
                if position["index"] < 4:
                    early = {f"{group}.{k}":v for group,st in (("gas",gas),("cloth",cloth_arrays))
                             for k,v in st.items() if isinstance(v,np.ndarray)}
                    np.savez_compressed(out/f"{arm}-{position['index']:03d}-fields.npz", **early)
                return dict(kind=kind, **position, gas=arrays_and_values(gas), cloth=arrays_and_values(cloth_arrays),
                            feedback=dict(dims=cloth.couple_dims, ready=cloth._couple_filled, wet=cloth._may_be_wet,
                                          placed=cloth.placed, active=cloth.active, layout_ok=cloth._couple_ok(solver),
                                          steam_smothers=solver.steam_smothers, sha256=digest(grid), raw_bytes=len(grid),
                                          offset=offset, compressed_bytes=len(payload)))

            def observe_step(batch, dt, params, emitters, colliders=None):
                batch.submit(restart=True)
                row = capture("input")
                require(solver.pieces_step is None, "Additional solid forcing")
                row.update(dt=dt, forcing=json_hash(dict(params=params, emitters=emitters,
                            static_colliders=solver.colliders, moving_colliders=colliders, features=solver.features)))
                append(row)
                position["index"] += 1
                position["substep"] += 1
                return step(batch, dt, params, emitters, colliders)

            def observe_frame(scn, frame):
                position.update(frame=frame, substep=0)
                frame_step(scn, frame)
                require(eng.last_substeps == position["substep"], "Missing substeps")
                append(dict(kind="frame_complete", frame=frame, substeps=eng.last_substeps, next_index=position["index"]))

            with patch.object(solver,"step",observe_step), patch.object(eng,"step_frame",observe_frame):
                require(eng.simulate_to(scene,24,cache=False) and eng.sim_frame==24, "Incomplete flag shot")
            append(capture("final"))
        summary.update(status="complete", frames=48, gas_updates=position["index"], wall_s=time.perf_counter()-start)
        save(summary_path, summary)
        return 0
    except Exception as error:
        summary.update(status="error", exception=type(error).__name__, error=str(error)[:650],
                       wall_s=time.perf_counter()-start)
        save(summary_path, summary)
        raise


def supervise(source, out):
    out.mkdir(parents=True, exist_ok=False)
    exits = {}
    for arm in ("ordinary","stiffer"):
        start = time.perf_counter()
        deadline = time.time()+LIMIT
        args = [sys.executable,"-B",__file__,"--source",str(source),"--out",str(out),"--worker",arm]
        p = subprocess.Popen(args)
        try:
            while p.poll() is None and time.time()<deadline and time.perf_counter()-start<LIMIT:
                time.sleep(0.2)
            timed_out = p.poll() is None
            if timed_out:
                p.kill()
            code = p.wait()
        finally:
            if p.poll() is None:
                p.kill()
                p.wait()
        exits[arm] = dict(pid=p.pid, exit=code, timeout=timed_out, limit_s=LIMIT, wall_s=time.perf_counter()-start)
        save(out/"workers.json",exits)
        first = out/"ordinary-steps.ndjson"
        if arm=="ordinary" and (not first.is_file() or first.stat().st_size==0):
            break
    return int(len(exits)!=2 or any(v["exit"] for v in exits.values()))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--worker",choices=("ordinary","stiffer"))
    a=p.parse_args()
    sys.exit(worker(a.source.resolve(),a.out.resolve(),a.worker) if a.worker else supervise(a.source.resolve(),a.out.resolve()))
