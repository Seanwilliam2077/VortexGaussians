"""Produce the frozen matched pairs of external curtain alternatives."""
import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

from fork import HERE, HalfGuard, prefix, rehydrate, t154

ORDERS = (("IDS","DSI","SID"),("SDI","DIS","ISD"))
LIMIT = 720
PACKET_LIMIT = 2*1024**3


def file_sha(path):
    with path.open("rb") as src:
        return hashlib.file_digest(src,"sha256").hexdigest()


def deliver(engine, scenes, method, kernels, packets, private, name, stages):
    from blackbody.io.simcache import write_entry
    row = dict(method=method, files={}, fork={})
    @contextmanager
    def phase(label):
        t = time.perf_counter()
        try:
            yield
        finally:
            stages[label] = stages.get(label,0.0) + time.perf_counter()-t

    start = time.perf_counter()
    with phase("prepare_default"):
        t154.prepare(engine,scenes["default"])
    checkpoint = None
    if method != "I":
        checkpoint = prefix(engine,scenes["default"],method,kernels,phase,row["fork"])
    for arm,scene in scenes.items():
        if arm == "slow":
            with phase("prepare_or_restore_slow"):
                if checkpoint is None:
                    t154.prepare(engine,scene)
                else:
                    rehydrate(engine,scene,checkpoint)
                    del checkpoint
        with phase("step_"+arm):
            t154.to_frame(engine,scene,36)
        with phase("read_"+arm):
            packet = t154.state(engine)
            packet.update(frame=36,arm=arm,pin=t154.PIN,scene=scene.to_dict(),signature=scene.sim_signature(True))
        with phase("encode_and_write_"+arm):
            path = private/(name+"-"+arm+".bbc")
            t154.require(not path.exists(),"Cell filename is not fresh")
            write_entry(path,packet)
        with phase("validate_file_"+arm):
            digest = file_sha(path)
            size = path.stat().st_size
            t154.require(digest == packets[arm]["sha256"] and size==packets[arm]["bytes"],
                         f"{arm} packet under {name} differs: sha256={digest}, bytes={size}")
            row["files"][arm] = dict(sha256=digest,bytes=size,raw_state_bytes=t154.raw_bytes(packet),
                                    steps=packet["state"]["steps"])
        del packet
    row["seconds"] = time.perf_counter()-start
    return row


def worker(source, out, private, iw):
    dest = out/f"worker-{iw}.json"
    start = time.perf_counter()
    row = dict(worker=iw, pin=t154.PIN, status="running", cells=[], setup={})
    t154.save(dest,row)
    try:
        free = shutil.disk_usage(private).free
        t154.require(free >= 3*1024**3,"Insufficient free disk")
        row["free_bytes_start"] = free
        start_device = time.perf_counter()
        card = t154.select(source)
        from blackbody.engine.engine import Engine
        from blackbody.engine.gpu import GPU
        gpu = GPU(adapter_name=card["device"], backend=card["backend_type"])
        t154.require(gpu.name == card["device"] and gpu.backend == card["backend_type"], "Wrong GPU")
        engine = Engine(gpu)
        scenes = {arm:t154.settings(arm) for arm in t154.ARMS}
        row["adapter"] = card
        row["setup"]["device_and_engine_s"] = time.perf_counter()-start_device
        row["phase"] = "prepare_warmup"
        t154.save(dest,row)
        t = time.perf_counter()
        t154.prepare(engine,scenes["default"])
        t154.to_frame(engine,scenes["default"],1)
        gpu.sync()
        row["setup"]["native_prepare_and_one_warm_frame_s"] = time.perf_counter()-t
        row["phase"] = "guard_admission"
        t154.save(dest,row)
        t = time.perf_counter()
        kernels = HalfGuard(gpu)
        row["backend_test"] = kernels.admit()
        row["setup"]["single_atlas_compile_and_test_s"] = time.perf_counter()-t
        ref = json.loads((t154.HERE/"evidence"/"generate.json").read_bytes())["packets"]
        projected = sum(p["bytes"] for p in ref.values())*sum(len(s) for seq in ORDERS for s in seq)
        t154.require(projected <= PACKET_LIMIT,"Combined two-worker packet limit would be exceeded")
        for block,order in enumerate(ORDERS[iw]):
            for position,method in enumerate(order):
                name = f"w{iw}-b{block}-{position}-{method}"
                stages = {}
                row["phase"] = name
                t154.save(dest,row)
                try:
                    result = deliver(engine,scenes,method,kernels,ref,private,name,stages)
                finally:
                    row["latest_phase_times"] = stages
                result.update(block=block,position=position,phases=stages)
                row["cells"].append(result)
                t154.save(dest,row)
        row.update(status="complete",phase="complete",elapsed_s=time.perf_counter()-start)
        t154.save(dest,row)
        return 0
    except Exception as exc:
        row.update(status="error",reason=str(exc)[:1000],elapsed_s=time.perf_counter()-start)
        t154.save(dest,row)
        raise


def supervise(source,out,private):
    out.mkdir(exist_ok=False)
    private.mkdir(exist_ok=False)
    for iw in range(2):
        cmd = [sys.executable,"-B",__file__,"--source",str(source),"--out",str(out),"--private",str(private),
               "--worker",str(iw)]
        start = time.perf_counter()
        with (out/f"worker-{iw}.log").open("x",encoding="utf8") as log:
            try:
                code = subprocess.run(cmd,stdout=log,stderr=log,timeout=LIMIT).returncode
                expired = False
            except subprocess.TimeoutExpired:
                code,expired = None,True
        t154.save(out/f"exit-{iw}.json",dict(exit=code,expired=expired,wall_s=time.perf_counter()-start,limit_s=LIMIT))
        if code != 0:
            return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--out",type=Path,default=HERE/"evidence")
    parser.add_argument("--private",type=Path,default=HERE/"private")
    parser.add_argument("--worker",type=int,choices=[0,1])
    args = parser.parse_args()
    locations = (args.source.resolve(),args.out.resolve(),args.private.resolve())
    sys.exit(supervise(*locations) if args.worker is None else worker(*locations,args.worker))
