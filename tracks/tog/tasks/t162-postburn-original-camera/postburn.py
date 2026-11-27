"""Render an externally checked base state and a material reconstructed from that base."""
from functools import partial
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
TASKS = HERE.parent
T160 = TASKS/"t160-burning-plateau/evidence"
T161 = TASKS/"t161-late-burn-duration"
sys.path.insert(0, str(TASKS/"t156-rendered-surface-edits"))
import images

fork = images.fork
recover = images.from_file("deferred_surface_recovery", T161/"recover.py")


def read(path):
    return json.loads(path.read_bytes())


def sha_file(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def restore_duration(engine, arm, generation):
    from blackbody.io.simcache import read_entry

    result = read(T160/"SCORE.json")
    fork.require(result["material_and_state_mechanism"] and result["native_nonzero_control_on_both_grids"],
                 "Active surface-flux condition is unqualified")
    recovery = read(T161/"evidence/SCORE.json")
    fork.require(result["certified_lower_bound_updates"] == result["aligned_updates"] == result["updates"][1],
                 "Window ends before the requested output")
    fork.require(recovery["status"] == "pass" and recovery["summary"]["step_replay"]["total_mismatching_words"] == 0,
                 "Late material recovery unqualified")
    independent = read(T160/"extended-36.json")
    ref5 = generation["ordinary"]["default"]["36"]
    fork.require(independent.keys() == ref5.keys(), "Incomplete endpoint")
    fork.require(all(independent[k] == ref5[k] for k in ("thermal","ember_state")), "Different feedback")
    fork.require({k:v for k,v in independent["state"].items() if k != "burn_obj"} ==
                 {k:v for k,v in ref5["state"].items() if k != "burn_obj"}, "Unshared gas")
    path = images.FORK/"private/default-36.bbc"
    packet_hash = sha_file(path)
    fork.require(packet_hash == generation["packets"]["default"]["sha256"], "Invalid common packet")
    packet = read_entry(path)
    # Only the common fields are taken from the prepared gas checkpoint.
    del packet["state"]["burn_obj"]
    meta, _, states, rows, digests = recover.read_arm(T160, "extended")
    boundary = meta["updates"]
    shape = rows[boundary]["atlas"]["shape"]
    primary = states[boundary].view("<f2").reshape(shape)
    fork.require(hashlib.sha256(primary.tobytes()).hexdigest() == independent["state"]["burn_obj"]["sha256"],
                 "Primary atlas differs from the ordinary ten-second run")
    del states
    scene = fork.settings("default")
    events, times = T161/"evidence/first-debit.bin", T161/"evidence/dt-f32.bin"
    if arm == "ten":
        scene.data["spread"]["burn_time"] = 10.
        fork.require(fork.json_hash(scene.to_dict()) == fork.json_hash(read(T160/"extended-scene.json")), "Wrong source scene")
        atlas = primary
        reference = independent
    elif arm == "five":
        atlas = recover.reconstruct_atlas(primary, events, times, boundary)
        reference = ref5
    else:
        raise ValueError(arm)
    packet["state"]["burn_obj"] = atlas
    fork.check_equal(fork.summary(packet), reference, "Host assembly")
    fork.prepare(engine, scene)
    fork.restore(engine, scene, 36, packet)
    return scene, reference, {"common_packet_sha256": packet_hash, "ten_s_source_archive": digests,
                              "event_file": sha_file(events), "clock_file": sha_file(times),
                              "input_atlas": hashlib.sha256(atlas.tobytes()).hexdigest(), "native_updates": boundary}


if __name__ == "__main__":
    images.main(partial(images.native, arms=("ten", "five"), restore_state=restore_duration), __file__)
