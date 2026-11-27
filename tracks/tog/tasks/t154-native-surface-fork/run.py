"""Deliver both external surface-edit continuations, then reopen their native packets offline."""
import argparse
from contextlib import contextmanager
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
T151 = HERE.parent / "t151-surface-preignition"
sys.path.insert(0, str(T151))
from capture_surface import ARMS, PIN, arrays_and_values, guard_upper, json_hash, require, save, select

MAX_PACKETS = 1536 * 1024**2
LIMITS = {"generate": 720, "reopen": 420}


def settings(arm):
    from blackbody.scene.presets import make
    scene = make("curtain_fire", fps=24)
    scene.data["spread"]["catch_time"] = ARMS[arm]
    reference = json.loads((T151 / "evidence" / f"{arm}-scene.json").read_bytes())
    require(json_hash(scene.to_dict()) == json_hash(reference), "Changed branch scene")
    require(not any(reference[k] for k in ("fabrics", "strands", "matter", "shots"))
            and not scene.colliders_animated()
            and not scene.data["domain"]["grow"] and not scene.data["domain"]["preroll"],
            "Another subsystem would require checkpoint state")
    return scene


def state(engine):
    gpu, heat, rad = engine.gpu, engine.objheat, engine.radiant
    require(heat.matter_j is None and heat.liquid_j is None and rad.grid and rad.built,
            "Unsupported thermal inputs at checkpoint")
    counters = np.frombuffer(gpu.read_buffer(rad.RLC), np.uint32).copy()
    nbytes = int(counters[0])*48
    require(nbytes <= rad.RL.size and not np.any(np.frombuffer(gpu.read_buffer(rad.RA), np.uint32)),
            "Invalid active radiant sources or accumulator")
    live = gpu.read_buffer(rad.RL, nbytes) if nbytes else b""
    # Each pair-contact key is stored as a list so JSON and the native cache preserve its identity.
    extra = dict(temperatures=heat.state(), contacts=[sorted([int(k),v] for k,v in t.touch_s.items()) for t in heat.things],
                 radiant_counts=counters, live_radiant=np.frombuffer(live,np.uint8).copy(),
                 grid=list_grid(rad.grid), cleared=rad._cleared, built=rad.built)
    return {"state": engine.solver.save_state(), "ember_state": engine.embers.save_state(), "thermal": extra}


def list_grid(grid):
    origin, cell, dims, block, h = grid
    return [list(origin), cell, list(dims), block, h]


def summary(packet):
    return {k: arrays_and_values(packet[k]) for k in ("state", "ember_state", "thermal")}


def check_equal(a, b, message):
    differing = {f"{k}.{x}" for k in a for x in a[k].keys() | b[k].keys() if a[k].get(x) != b[k].get(x)}
    require(not differing, message + " " + str(sorted(differing)))


def raw_bytes(packet):
    return sum(v.nbytes for key in ("state", "ember_state", "thermal") for v in packet[key].values() if isinstance(v, np.ndarray))


def t151_endpoint(arm):
    rows = [json.loads(x) for x in (T151 / "evidence" / f"{arm}.jsonl").read_text().splitlines()]
    row, embers = rows[-2:]
    require(row["kind"] == "frame_state" and row["frame"] == embers["frame"] == 36, "T151 endpoint missing")
    gas = row["state"]
    gas["burn_obj"] = {k: row["atlas"][k] for k in ("shape", "dtype", "sha256")}
    return {"state": gas, "ember_state": embers["embers"]}


def prepare(engine, scene):
    engine.prepare(scene, final=True)
    engine.reset()
    # Engine.reset does not reset Radiant, so a preceding arm could otherwise light frame 1.
    engine.radiant.built = False
    engine.radiant._cleared = False
    engine.radiant.grid = None
    engine.radiant.n_objects = 0
    s = engine.solver
    require(engine.kind == "fire" and engine._heat_on() and len(engine.objheat.things) == 2 and not engine.cloth.active
            and not engine.strands_on and not engine.solids.active and not engine.shooting
            and not s.water and s.upres == 3 and list(s.dims) == [152, 176, 80],
            "Unexpected physical coupling or resolution")


def restore(engine, scene, frame, packet):
    # Fixed-layout, fire-only branch of Engine._resume. No earlier frame is simulated.
    s = engine.solver
    require(tuple(s.dims) == tuple(packet["state"]["dims"]) and engine.sim_frame is None,
            "Cold restore requires a matching empty engine")
    s._prm = scene.solver_params(frame)
    s.set_meshes(scene.mesh_items(frame), scene.data["domain"]["mesh_resolution"])
    s.colliders = []
    s.set_colliders(scene.colliders_gpu(frame, None))
    s.load_state(packet["state"])
    engine.embers.load_state(packet["ember_state"])
    heat, rad, extra = engine.objheat, engine.radiant, packet["thermal"]
    heat.load_state(extra["temperatures"])
    for thing, pairs in zip(heat.things, extra["contacts"], strict=True):
        thing.touch_s = dict(pairs)
    rad.layout(s.origin, s.dims, s.h, gas=True)
    require(list_grid(rad.grid) == extra["grid"], "Radiant grid mismatch")
    with engine.gpu.batch() as batch:
        batch.clear_buffer(rad.RA)
    engine.gpu.write_buffer(rad.RLC, extra["radiant_counts"])
    if extra["live_radiant"].size:
        engine.gpu.write_buffer(rad.RL, extra["live_radiant"])
    rad.built, rad._cleared = extra["built"], extra["cleared"]
    engine.sim_frame = frame


def forecast(engine, scene, frame, upper):
    domain = scene.data["domain"]
    fdt = scene.v("domain", "time_scale", frame) / scene.fps
    n = engine.solver.substeps_for(fdt, cfl=domain["cfl"], lo=domain["substeps_min"],
                                   hi=scene.substep_cap(frame, engine.solver.h))
    dt = fdt / n
    for _ in range(n):
        upper = guard_upper(upper, dt)
    return upper, n, dt


def to_frame(engine, scene, frame):
    require(engine.simulate_to(scene, frame, cache=False) and engine.sim_frame == frame, "Incomplete native frame")


def ordinary(engine, scene, timed):
    with timed("reset_prepare"):
        prepare(engine, scene)
    upper = 0.0
    states = {}
    frame = 1
    with timed("ordinary_prefix"):
        while True:
            next_upper, n, _ = forecast(engine, scene, frame, upper)
            if next_upper is None:
                break
            upper = next_upper
            to_frame(engine, scene, frame)
            require(engine.last_substeps == n, "Ordinary schedule changed")
            frame += 1
    require(1 < frame <= 36, "No useful ordinary split")
    split = frame-1
    with timed("read_fork"):
        states[str(split)] = summary(state(engine))
    for target in (36, 37):
        with timed(f"advance_to_{target}"):
            to_frame(engine, scene, target)
        with timed(f"read_{target}"):
            states[str(target)] = summary(state(engine))
    return split, states


def shared(engine, fast, slow, timed):
    with timed("reset_prepare"):
        prepare(engine, fast)
    solver = engine.solver
    native_init, native_react = solver._init_burn, solver._react
    atlases, schedule, submitted = [], [], []
    current = 0
    def initialize(batch, prm):
        require(not atlases and solver.steps == 0, "Secondary atlas initialized twice")
        native_init(batch, prm)
        first = solver.burn_obj[0]
        for label in ("read", "write"):
            texture = engine.gpu.texture3d(first.size, first.format, "t154-slow-"+label)
            batch.copy_texture(first, texture)
            atlases.append(texture)

    def react(batch, dt, prm, emitters, fine=False):
        if not fine:
            require(len(atlases) == 2 and prm.spread.catch_time == .35 and prm.spread.spotting == 0
                    and not prm.spread.ground and not solver.water and all(e.douse <= 0 for e in emitters)
                    and solver.pieces_step is None and dt == schedule[-1]["dt"],
                    "Secondary object pass cannot share inputs")
            # This is the same coarse advected gas the just-recorded fast material pass read.
            slow_prm = replace(prm, spread=replace(prm.spread, catch_time=ARMS["slow"]))
            read, write = atlases
            batch.run(solver._k["burn_obj"], solver._burn_obj_res(read, write),
                      solver._burn_obj_uniforms(dt, slow_prm, []), read.size)
            atlases.reverse()
            submitted.append(current)
        return native_react(batch, dt, prm, emitters, fine=fine)

    upper = 0.0
    with timed("common_gas_both_atlases"):
        with patch.object(solver, "_init_burn", initialize), patch.object(solver, "_react", react):
            for current in range(1, 37):
                candidate, n, dt = forecast(engine, fast, current, upper)
                if candidate is None:
                    break
                schedule.append(dict(frame=current, n=n, dt=dt, upper=candidate))
                upper = candidate
                to_frame(engine, fast, current)
                require(engine.last_substeps == n and submitted.count(current) == n, "Substep hook mismatch")
            else:
                raise ValueError("Bound never expired")
    with timed("copy_fork_state_and_evaluate_scale"):
        split = engine.sim_frame
        require(split and len(schedule) == split, "Unusable split")
        common = state(engine)
        fast_receipt = summary(common)
        slow_atlas = engine.gpu.read(atlases[0])
        for texture in atlases:
            texture.destroy()
        fast_atlas = common["state"]["burn_obj"]
        require(np.any(fast_atlas.view(np.uint16) != slow_atlas.view(np.uint16)), "No material difference")
        prediction = fast_atlas.copy()
        prediction[..., 1] = (fast_atlas[..., 1].astype(np.float32) * np.float32(.5)).astype(fast_atlas.dtype)
        mismatched = int(np.count_nonzero(prediction.view(np.uint16) != slow_atlas.view(np.uint16)))
        common["state"]["burn_obj"] = slow_atlas
        slow_receipt = summary(common)
    return common, (fast_receipt, slow_receipt), dict(split=split, shared_steps=len(submitted), frames=schedule,
            next_frame=dict(frame=current, n=n, dt=dt), scale_mismatch_words=mismatched,
            secondary_texture_bytes=2*slow_atlas.nbytes)


def run_worker(source, mode, evidence, private):
    started = time.perf_counter()
    dest = evidence / (mode+".json")
    trace = dict(mode=mode, pin=PIN, status="running", phase="admission", paths={}, costs=[], states={})
    save(dest, trace)
    current_path = "cold"
    @contextmanager
    def timed(label):
        trace["phase"] = current_path+"/"+label
        save(dest, trace)
        t = time.perf_counter()
        try:
            yield
        finally:
            trace["costs"].append(dict(path=current_path, phase=label, s=time.perf_counter()-t))
            save(dest, trace)
    @contextmanager
    def path(label):
        nonlocal current_path
        current_path = label
        t = time.perf_counter()
        try:
            yield
        finally:
            trace["paths"][label] = time.perf_counter()-t
            save(dest, trace)
    try:
        with path("cold"), timed("admit_and_device"):
            card = select(source)
            from blackbody.engine.engine import Engine
            from blackbody.engine.gpu import GPU
            from blackbody.io.simcache import read_entry, write_entry
            gpu = GPU(adapter_name=card["device"], backend=card["backend_type"])
            require(gpu.name == card["device"] and gpu.backend == card["backend_type"], "Adapter mismatch")
            engine = Engine(gpu)
            trace["adapter"] = card
            scenes = {arm: settings(arm) for arm in ARMS}
        # Cold pipeline creation is common fixed setup, paid once in both device processes.
        with path("cold_prepare"), timed("native_final_prepare"):
            prepare(engine, scenes["default"])
        if mode == "generate":
            require(shutil.disk_usage(private).free >= 3*1024**3, "Less than 3 GiB disk available")
            oracle = trace["ordinary"] = {}
            for arm, scene in scenes.items():
                with path("ordinary_"+arm):
                    split, oracle[arm] = ordinary(engine, scene, timed)
                    check_equal(t151_endpoint(arm), oracle[arm]["36"], arm+" ordinary/T151 at 36")
                    if arm == "default":
                        ordinary_split = split
                    require(split == ordinary_split, "Different ordinary guarded frame")
            with path("fork_prefix"):
                packet, pair, fork = shared(engine, scenes["default"], scenes["slow"], timed)
                trace["fork"] = fork
                split = fork["split"]
                require(split == ordinary_split, "Online and independent split differ")
                for arm, item in zip(ARMS, pair):
                    check_equal(item, oracle[arm][str(split)], arm+" fork boundary")
                trace["fork_receipts"] = dict(zip(ARMS, pair))
            used_raw = used_files = 0
            for arm, scene in scenes.items():
                with path("continue_"+arm):
                    if arm == "slow":
                        with timed("prepare_and_restore_fork"):
                            prepare(engine, scene)
                            restore(engine, scene, split, packet)
                            check_equal(summary(state(engine)), oracle[arm][str(split)], "Rehydrated fork")
                        del packet
                    for frame in (36, 37):
                        with timed("step_to_"+str(frame)):
                            to_frame(engine, scene, frame)
                        with timed("host_read_and_compare_"+str(frame)):
                            actual = state(engine)
                            item = summary(actual)
                            trace["states"].setdefault(arm,{})[str(frame)] = item
                            check_equal(item, oracle[arm][str(frame)], f"{arm} fork output {frame}")
                        if frame == 36:
                            with timed("native_packet_write"):
                                bytes_now = raw_bytes(actual)
                                used_raw += bytes_now
                                require(used_raw <= MAX_PACKETS, "Packet raw capacity exceeded")
                                filename = private / (arm+"-36.bbc")
                                require(not filename.exists(), "Refusing to overwrite prior packet")
                                actual.update(frame=36, arm=arm, pin=PIN, scene=scene.to_dict(),
                                              signature=scene.sim_signature(True))
                                write_entry(filename, actual)
                                used_files += filename.stat().st_size
                                require(used_files <= MAX_PACKETS, "Native cache budget exceeded")
                                with filename.open("rb") as packet_file:
                                    file_hash = hashlib.file_digest(packet_file, "sha256").hexdigest()
                                trace.setdefault("packets", {})[arm] = dict(bytes=filename.stat().st_size,
                                    raw_state_bytes=bytes_now, sha256=file_hash,
                                    signature=actual["signature"], scene=json_hash(actual["scene"]))
                        del actual
        else:
            generation = json.loads((evidence/"generate.json").read_bytes())
            require(generation["status"] == "complete", "Generation did not complete")
            for arm, scene in scenes.items():
                with path("cold_continue_"+arm):
                    with timed("decode_validate_reset_restore"):
                        filename = private/(arm+"-36.bbc")
                        with filename.open("rb") as f:
                            require(hashlib.file_digest(f,"sha256").hexdigest() == generation["packets"][arm]["sha256"],
                                    "Native packet damage")
                        actual = read_entry(filename)
                        require(actual["pin"] == PIN and actual["arm"] == arm and actual["frame"] == 36
                                and json_hash(actual["scene"]) == json_hash(scene.to_dict())
                                and actual["signature"] == scene.sim_signature(True), "Wrong packet")
                        prepare(engine, scene)
                        restore(engine, scene, 36, actual)
                        del actual
                    for frame in (36, 37):
                        with timed("read_36" if frame == 36 else "step_and_read_37"):
                            to_frame(engine, scene, frame)
                            item = summary(state(engine))
                            trace["states"].setdefault(arm,{})[str(frame)] = item
                            check_equal(item, generation["ordinary"][arm][str(frame)], f"Cold {arm} {frame}")
        trace.update(status="complete", phase="complete", elapsed_s=time.perf_counter()-started)
        save(dest, trace)
        return 0
    except Exception as exc:
        trace.update(status="error", error=str(exc)[:950], elapsed_s=time.perf_counter()-started)
        save(dest, trace)
        raise


def supervise(source, evidence, private):
    evidence.mkdir(exist_ok=False)
    private.mkdir(exist_ok=False)
    for mode, budget in LIMITS.items():
        t = time.perf_counter()
        with (evidence/(mode+".log")).open("x", encoding="utf8") as log:
            try:
                cmd = [sys.executable, "-B", __file__, "--source", str(source), "--mode", mode,
                       "--out", str(evidence), "--private", str(private)]
                result = subprocess.run(cmd, stdout=log, stderr=log, timeout=budget)
                code, expired = result.returncode, False
            except subprocess.TimeoutExpired:
                code, expired = None, True
        save(evidence/(mode+"-exit.json"), dict(exit=code, expired=expired, wall_s=time.perf_counter()-t, limit_s=budget))
        if code != 0:
            return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--mode", choices=LIMITS)
    parser.add_argument("--out", type=Path, default=HERE/"evidence")
    parser.add_argument("--private", type=Path, default=HERE/"private")
    args = parser.parse_args()
    evidence, private = args.out.resolve(), args.private.resolve()
    sys.exit(run_worker(args.source.resolve(), args.mode, evidence, private) if args.mode
             else supervise(args.source.resolve(), evidence, private))
