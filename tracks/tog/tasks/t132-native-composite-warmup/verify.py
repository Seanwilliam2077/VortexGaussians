"""Check the portable T132 receipts, including the exact phase censored by its deadline."""
import argparse
import hashlib
import json
from pathlib import Path
from observe import KEYS, LIMIT, PIN, SOURCE_SHA


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify(folder):
    outer = json.loads((folder / "EXIT.json").read_bytes())
    result = json.loads((folder / "RESULT.json").read_bytes())
    trace = [json.loads(line) for line in (folder / "PHASES.ndjson").read_bytes().splitlines()]
    require(result["source_revision"] == PIN and result["stage_keys_expected"] == KEYS, "Source or stage identity")
    require(outer["limit_s"] == LIMIT and outer["windows_awake_s"] >= 0, "Supervisor clock")
    active = []
    native = {}
    previous = 0
    for row in trace:
        require(row["elapsed_s"] >= previous, "Non-monotone worker trace")
        previous = row["elapsed_s"]
        identity = (row["phase"], row.get("entry"))
        if "key" in row:
            require(row["key"] == KEYS[row["entry"]], "Unexpected native stage key")
        if "source_sha256" in row:
            require(row["source_sha256"] == SOURCE_SHA, "Unexpected expanded native WGSL")
        if row["event"] == "start":
            active.append(identity)
        else:
            require(row["event"] in ("return", "exception") and active.pop() == identity, "Phase pairing")
            if row["event"] == "return" and "key" in row:
                native.setdefault(row["entry"], []).append(row["phase"])
    if outer["status"] == "time_limit":
        require(outer["exit"] != 0 and max(outer["elapsed_wall_s"], outer["monotonic_s"]) >= LIMIT, "Deadline")
    elif outer["exit"] != 0:
        require(result["status"] == "error" and outer["status"] == "returned", "Recorded worker failure")
    else:
        import numpy as np
        require(result["status"] == "complete" and not active and outer["status"] == "returned", "Completion")
        require(result["stage_keys"] == KEYS and result["neutral_frame2_matches_t130"], "Fixture identity")
        for entry in KEYS:
            require(native[entry] == ["create_shader_module","create_bind_group_layout","create_pipeline_layout",
                                      "create_compute_pipeline"], "Native stage sequence")
        with np.load(folder / "composite.npz", allow_pickle=False) as container:
            pixels = container["pixels"]
        expected = result["native_pixels"]
        require(pixels.shape == (180,320,4) and list(pixels.shape) == expected["shape"] and
                pixels.dtype.kind == "f" and str(pixels.dtype) == expected["dtype"] and np.isfinite(pixels).all(),
                "Finite scene-linear RGB and alpha")
        require(hashlib.sha256(pixels.tobytes(order="C")).hexdigest() == expected["sha256"], "Native pixel hash")
        rgb = pixels[...,:3]
        require(result["rgb_range"] == [float(rgb.min()), float(rgb.max())] and
                result["nonzero_rgb_pixels"] == int((rgb!=0).any(axis=2).sum()), "Image statistics")
    return dict(terminal=outer["status"], worker_status=result["status"], last=trace[-1], open_phases=active)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    print(json.dumps(verify(parser.parse_args().folder), indent=2))
