"""Record ordinary catch-time edits on the released native surface-fire solver."""
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
sys.path.insert(0, str(HERE.parent / "t133-flag-coupling"))
from observe import arrays_and_values, digest, json_hash, require  # previous observer utilities
from admit import PIN, save, select

ARMS = {"default": 0.35, "slow": 0.70}
LIMIT_S = 420


def guard_upper(bound, dt):
    """Upper bound for any previously unlit texel. Return None on first expiry."""
    if bound is None or not 0 < dt < ARMS["default"]:
        return None
    next_value = bound + dt / ARMS["default"] + 2**-10
    return next_value if next_value < 1 else None


def atlas_stats(data):
    x, y, z, w = np.moveaxis(data, -1, 0)
    live = (x > 0) & (z > 0.5)
    return dict(eligible=int(live.sum()), catching=int(np.count_nonzero(live & (y > 0) & (y < 1))),
                lit=int(np.count_nonzero(live & (y >= 1))), smouldering=int(np.count_nonzero((z > .5) & (w > 0))),
                max_progress=float(y.max()), wet=int(np.count_nonzero(y < 0)))


def measure(directory, source, arm):
    start = time.perf_counter()
    info = dict(status="started", pin=PIN, arm=arm, phase="admission")
    receipt = directory / f"{arm}.json"
    save(receipt, info)
    try:
        card = select(source)
        from blackbody.engine.engine import Engine
        from blackbody.engine.gpu import GPU
        from blackbody.scene.presets import make
        scene = make("curtain_fire", fps=24)
        spread = scene.data["spread"]
        require(scene.start == 1 and scene.fps == 24 and scene.data["domain"]["preroll"] == 0
                and spread["catch_time"] == .35 and spread["spotting"] == 0
                and spread["enabled"] and not spread["ground"] and not scene.colliders_animated(),
                "Unsupported source fixture")
        info.update(phase="native preparation", adapter=card, base_scene=json_hash(scene.to_dict()))
        spread["catch_time"] = ARMS[arm]
        scene_bytes = scene.to_dict()
        info["edited_scene"] = json_hash(scene_bytes)
        save(directory / f"{arm}-scene.json", scene_bytes)
        save(receipt, info)
        gpu = GPU(adapter_name=card["device"], backend=card["backend_type"])
        require(gpu.name == card["device"] and gpu.backend == card["backend_type"], "Adapter mismatch")
        engine = Engine(gpu)
        engine.prepare(scene, final=True)
        solver = engine.solver
        require(not engine.cloth.active and not engine.solids.active and not engine.strands_on and not
                scene.data["domain"]["grow"] and not solver.water, "Unsupported external coupling")
        info.update(phase="ordinary steps", dims=list(solver.dims), fine_upres=solver.upres,
                    features=solver.features, setup_s=time.perf_counter()-start)
        save(receipt, info)
        frame = substep = step_count = 0
        bound = 0.0
        previous = None
        initializations = 0
        plain_init, plain_step, plain_frame = solver._init_burn, solver.step, engine.step_frame
        with (directory / f"{arm}-atlas.zlib").open("xb") as archive, (directory / f"{arm}.jsonl").open("x",encoding="utf8") as ledger:
            def write(record):
                ledger.write(json.dumps(record, separators=(",",":"), allow_nan=False) + "\n")
                ledger.flush()

            def capture(kind):
                nonlocal previous
                state = solver.save_state()
                atlas = np.ascontiguousarray(state.pop("burn_obj"))
                require(atlas.ndim == 4 and atlas.shape[-1] == 4 and np.isfinite(atlas).all(), "Invalid atlas")
                floor = state.get("burn")
                require(floor is not None and not np.any(floor[..., 1:]), "Floor participates in spreading")
                values = atlas.view(np.uint8).reshape(-1)
                delta = values if previous is None else np.bitwise_xor(values, previous)
                payload = zlib.compress(delta, 4)
                offset = archive.tell()
                archive.write(payload)
                archive.flush()
                previous = values.copy()
                write(dict(kind=kind, frame=frame, substep=substep, index=step_count,
                           atlas=dict(shape=list(atlas.shape), dtype=atlas.dtype.str, sha256=digest(atlas),
                                      offset=offset, size=len(payload), **atlas_stats(atlas)),
                           state=arrays_and_values(state)))

            def initial(batch, params):
                nonlocal initializations
                plain_init(batch, params)
                batch.submit(restart=True)
                initializations += 1
                require(initializations == 1 and step_count == 0, "Unexpected burn reinitialization")
                capture("initialized")

            def step(batch, dt, params, emitters, colliders=None):
                nonlocal bound, step_count, substep
                args = dataclasses.asdict(params)
                catch_time = args["spread"].pop("catch_time")
                require(catch_time == ARMS[arm] and params.spread.spotting == 0 and not params.spread.ground
                        and all(e.douse <= 0 for e in emitters) and colliders is None
                        and solver.pieces_step is None and solver.water is None, "Effective inputs outside guard")
                bound = guard_upper(bound, dt)
                write(dict(kind="update", index=step_count, frame=frame, substep=substep, dt=dt,
                           catch_time=catch_time, upper_after=bound,
                           forcing=json_hash([args, emitters, solver.colliders, solver.features])))
                plain_step(batch, dt, params, emitters, colliders)
                step_count += 1
                substep += 1
                if frame <= 12:
                    batch.submit(restart=True)
                    capture("post_update")

            def advance(scn, number):
                nonlocal frame, substep
                frame, substep = number, 0
                plain_frame(scn, number)
                require(substep == engine.last_substeps, "Substep count changed")
                if frame > 12:
                    capture("frame_state")
                write(dict(kind="frame_end", index=step_count, frame=frame, substep=substep,
                           embers=arrays_and_values(engine.embers.save_state())))

            with patch.object(solver, "_init_burn", initial), patch.object(solver, "step", step), patch.object(engine, "step_frame", advance):
                require(engine.simulate_to(scene, 36, cache=False) and engine.sim_frame == 36, "Incomplete shot")
        require(initializations == 1, "No native burn initialization")
        info.update(status="complete", updates=step_count, frames=frame, elapsed_s=time.perf_counter()-start)
        save(receipt, info)
        return 0
    except Exception as exc:
        info.update(status="error", error=str(exc).replace(str(source), "<upstream>").replace(str(Path.home()), "<home>")[:900],
                    elapsed_s=time.perf_counter()-start)
        save(receipt, info)
        raise


def supervise(directory, source):
    directory.mkdir(parents=True, exist_ok=False)
    for arm in ARMS:
        start = time.perf_counter()
        cmd = [sys.executable, "-B", __file__, "--source", str(source), "--out", str(directory), "--arm", arm]
        with (directory / f"{arm}.log").open("w",encoding="utf8") as log:
            try:
                run = subprocess.run(cmd, stdout=log, stderr=log, timeout=LIMIT_S)
                result = dict(exit=run.returncode, expired=False)
            except subprocess.TimeoutExpired:
                result = dict(exit=None, expired=True)
        save(directory / f"{arm}-exit.json", dict(**result, wall_s=time.perf_counter()-start, limit_s=LIMIT_S))
        if result["exit"] != 0:
            return 1
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--arm", choices=ARMS)
    a = p.parse_args()
    directory, source = a.out.resolve(), a.source.resolve()
    sys.exit(measure(directory, source, a.arm) if a.arm else supervise(directory, source))
