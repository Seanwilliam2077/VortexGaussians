"""Apply the predeclared gas-hook sufficient condition to two archived native grids."""
import hashlib
import json
import math
from pathlib import Path
import zlib

import numpy as np


ROOT = Path(__file__).resolve().parent.parent / "evidence"


def read_grid(frame, archive):
    feedback = frame["feedback"]
    with np.load(archive, allow_pickle=False) as data:
        words = data["state.feedback.grid"]
    if words.dtype != np.dtype("<u4") or words.ndim != 1:
        raise ValueError("Expected little-endian native uint32 buffer")
    if hashlib.sha256(words.tobytes()).hexdigest() != feedback["grid"]["sha256"]:
        raise ValueError("Native grid digest differs from its frame receipt")
    x, y, z = feedback["dims"]
    return words.view("<i4").reshape(z, y, x, 13)


def neighbors(mask):
    """Cells that can share an eight-corner stencil with an active cell."""
    z, y, x = mask.shape
    padded = np.pad(mask, 1)
    answer = np.zeros_like(mask)
    for dz, dy, dx in np.ndindex(3, 3, 3):
        answer |= padded[dz:dz+z, dy:dy+y, dx:dx+x]
    return answer


def grid_info(grid):
    payload = grid.tobytes()
    tail = np.ascontiguousarray(grid[..., 9:13]).tobytes()
    return {
        "native_sha256": hashlib.sha256(payload).hexdigest(),
        "nonzero_by_channel": np.count_nonzero(grid, axis=(0,1,2)).tolist(),
        "full_raw_bytes": len(payload),
        "full_zlib6_bytes": len(zlib.compress(payload, 6)),
        "history_raw_bytes": len(tail),
        "history_zlib6_bytes": len(zlib.compress(tail, 6)),
    }


def compare(first, second):
    if first.shape != second.shape or first.ndim != 4 or first.shape[-1] != 13:
        raise ValueError("Expected equal layouts and 13 channels")
    different = first != second
    changed = np.count_nonzero(different, axis=(0,1,2))
    nonnegative = bool(np.all(first[..., :3] >= 0) and np.all(second[..., :3] >= 0))
    axes = []
    certified = nonnegative and not np.any(changed[6:])
    for a in range(3):
        live = (first[..., a+9] != 0) | (second[..., a+9] != 0)
        near = neighbors(live)
        support = (first[..., a] > 0) != (second[..., a] > 0)
        unequal_near = near & (different[..., a] | different[..., a+3])
        certified = certified and not np.any(support) and not np.any(unequal_near)
        axes.append({"axis": "xyz"[a], "impulse_cells_either": int(live.sum()),
                     "area_support_changes": int(support.sum()),
                     "near_impulse_area_or_velocity_changes": int(unequal_near.sum())})
    return {"changed_words_by_channel": changed.tolist(), "raw_equal": not bool(np.any(different)),
            "nonnegative_areas": nonnegative, "axes": axes, "operator_certified": bool(certified)}


def measure():
    receipt = json.loads((ROOT/"reference.json").read_bytes())
    a, b = receipt["native_parent"], receipt["successor"]
    if [a["frame"], b["frame"]] != [1, 2]:
        raise ValueError("Unexpected reference frames")
    flags = ("dims","ready","wet","active","placed")
    if any(a["feedback"][k] != b["feedback"][k] for k in flags):
        raise ValueError("Mismatched feedback layout or flags")
    if not all(a["feedback"][k] for k in ("ready","active","placed")):
        raise ValueError("Expected an enabled native hook")
    for k in ("dims", "h", "origin"):
        if a["gas"][k] != b["gas"][k]:
            raise ValueError("Mismatched gas layout")
    if list(a["gas"]["dims"]) != [2*n for n in a["feedback"]["dims"]]:
        raise ValueError("Expected the registered aligned grid")
    coarse_h = np.float32(2 * a["gas"]["h"])
    volume = coarse_h * coarse_h * coarse_h
    if not (math.isfinite(volume) and volume > 0):
        raise ValueError("Invalid coupling cell volume for native arithmetic")
    first = read_grid(a, ROOT/"reference-parent.npz")
    second = read_grid(b, ROOT/"reference-successor.npz")
    return {"schema":"t131-pending-feedback-effect-v1", "zlib_runtime":zlib.ZLIB_RUNTIME_VERSION,
            "gas_dims_xyz": a["gas"]["dims"], "coupling_dims_xyz": a["feedback"]["dims"],
            "simulation_cell_size_m": a["gas"]["h"],
            "frame_1":grid_info(first), "frame_2":grid_info(second), "comparison":compare(first, second)}


if __name__ == "__main__":
    print(json.dumps(measure(), indent=2))
