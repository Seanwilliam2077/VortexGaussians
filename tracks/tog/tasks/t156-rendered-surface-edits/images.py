"""Render the saved edited states in the original camera without advancing physics."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
TASKS = HERE.parent
FORK = TASKS / "t154-native-surface-fork"
sys.path.insert(0, str(TASKS / "t143-classic-playback"))
import classic

render = classic.render


def from_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Two earlier experiments independently use the script name "observe".
# Keep their original reference functions bound to the intended modules.
field_observer = from_file("flag_boundary_observer", TASKS / "t133-flag-coupling/observe.py")
with patch.dict(sys.modules, {"observe": field_observer}):
    fork = from_file("external_surface_fork", FORK / "run.py")


def records(out):
    path = out / "STAGE.ndjson"
    return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []


def archive(path, pixels):
    pixels = np.asarray(pixels)
    if pixels.shape != (180, 320, 4) or pixels.dtype != np.float16 or not np.isfinite(pixels).all():
        raise ValueError(f"Unexpected native image: {pixels.shape}, {pixels.dtype}")
    np.savez_compressed(path, pixels=pixels)
    return hashlib.sha256(pixels.tobytes()).hexdigest()


def restore_catch(engine, arm, generation):
    from blackbody.io.simcache import read_entry
    scene = fork.settings(arm)
    path = FORK / "private" / (arm + "-36.bbc")
    with path.open("rb") as f:
        packet_hash = hashlib.file_digest(f, "sha256").hexdigest()
    fork.require(packet_hash == generation["packets"][arm]["sha256"], "Packet identity")
    packet = read_entry(path)
    fork.require((packet["frame"], packet["arm"], packet["pin"], packet["signature"]) ==
                 (36, arm, fork.PIN, scene.sim_signature(True)), "Wrong restored scene")
    fork.prepare(engine, scene)
    fork.restore(engine, scene, 36, packet)
    del packet
    reference = generation["ordinary"][arm]["36"]
    return scene, reference, {"packet_sha256": packet_hash}


def native(source, out, cache, *, arms=("default", "slow"), restore_state=restore_catch):
    import wgpu
    from blackbody.engine.engine import Engine
    from blackbody.engine.gpu import GPU

    started = time.perf_counter()
    generation = json.loads((FORK / "evidence/generate.json").read_bytes())
    cold = json.loads((FORK / "evidence/reopen.json").read_bytes())
    fork.require(generation["status"] == cold["status"] == "complete", "Unqualified fork outputs")
    receipt = {"pin": fork.PIN, "frame": 36, "status": "starting", "arms": {}}
    def stage(name):
        receipt.update(phase=name, elapsed_s=time.perf_counter() - started)
        fork.save(out / "RESULT.json", receipt)

    sdk = Path(os.environ["ProgramFiles(x86)"]) / "Windows Kits/10/bin/10.0.26100.0/x64"
    hashes = {name: hashlib.sha256((sdk / name).read_bytes()).hexdigest() for name in render.DLLS}
    compiler = {"requested": "Dxc", "sdk": "10.0.26100.0/x64", "dll_sha256": hashes}
    warnings = render.CompilerWarnings()
    wgpu.logger.addHandler(warnings)
    fork.require(hashes == render.DLLS and render.module_path("dxcompiler.dll") is None, "SDK admission")
    opts = {"dx12_compiler": "Dxc", "dxc_path": str(sdk / "dxcompiler.dll"), "dxc_max_shader_model": 6.5}
    try:
        with os.add_dll_directory(str(sdk)):
            stage("device")
            info = fork.select(source, compiler_options=opts)
            gpu = GPU(adapter_name=info["device"], backend=info["backend_type"])
            fork.require(gpu.name == info["device"] and gpu.backend == info["backend_type"], "Adapter fallback")
            render.check_compiler(gpu, out, sdk, compiler, warnings)
            engine = Engine(gpu)
            # A restored state must be sufficient by itself.
            with patch.object(engine, "step_frame", side_effect=RuntimeError("Unexpected physics update")):
                for arm in arms:
                    stage(arm + "/restore")
                    scene, reference, provenance = restore_state(engine, arm, generation)
                    fork.check_equal(fork.summary(fork.state(engine)), reference, arm + " input")
                    item = receipt["arms"][arm] = provenance
                    for mode, name in (("fire", "emission"), ("composite", "composite")):
                        stage(arm + "/" + name)
                        previous = len(records(out))
                        engine.render(scene, 36, (320, 180), mode=mode, final=True, samples=1,
                                      motion_blur=False, seed=0)
                        pixels = engine.aovs()["emission"] if mode == "fire" else engine.linear_comp()
                        item[name] = archive(out / f"{arm}-{name}.npz", pixels)
                        stages = records(out)[previous:]
                        count = sum(r["action"] == "batch_run_returned" and r["entry"] == "main" for r in stages)
                        fork.require(mode != "composite" or count >= 1, "Missing original classic dispatch")
                        item[name + "_classic_dispatches"] = count
                        fork.require(engine.sim_frame == 36, "Unexpected rendered frame")
                        fork.check_equal(fork.summary(fork.state(engine)), reference, arm + " after " + name)
            render.check_compiler(gpu, out, sdk, compiler, warnings)
            receipt.update(status="complete", settings={"size": [320, 180], "seed": 0, "final": True,
                           "samples": 1, "motion_blur": False}, adapter=info)
            stage("complete")
    except Exception as exc:
        receipt.update(status="error", reason=str(exc).replace(str(source), "<upstream>").replace(str(Path.home()), "<home>")[:900])
        stage(receipt.get("phase", "admission"))
        raise
    return 0


def main(worker, script):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--worker-cache", type=Path)
    args = parser.parse_args()
    source, out = args.source.resolve(), args.out.resolve()
    if args.worker_cache is None:
        sys.exit(render.observe.supervise(source, out, limit=660, worker_script=script))
    # Reuse the pinned T138 label adaptation and T143 lazy stage instrumentation.
    with patch.object(render, "run_worker", worker):
        sys.exit(classic.worker(source, out, args.worker_cache))


if __name__ == "__main__":
    main(native, __file__)
