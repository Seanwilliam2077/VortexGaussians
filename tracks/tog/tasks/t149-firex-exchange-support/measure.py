"""Four reduced Fire-X wood stencils. No Warp kernels, flow, water, or renderer."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DT, DX, RHO, HEAT_CAPACITY = 1 / 120, 0.04, 16.0, 1600.0
HORIZON, COLD, HOT = 1440, 310.0, 790.0


def neighbors(arr):
    # All wood is inside a collar. Zero padding prevents wrapping grid edges.
    pad = np.pad(arr, 1)
    for axis in range(3):
        for step in (-1, 1):
            sl = [slice(1, k + 1) for k in arr.shape]
            sl[axis] = slice(1 + step, arr.shape[axis] + 1 + step)
            yield pad[tuple(sl)]


def distance_to_wood_surface(painted, wood, exposed):
    reached = painted.copy()
    for depth in range(int(wood.sum()) + 1):
        if (reached & exposed).any():
            return depth
        nxt = reached | (wood & np.logical_or.reduce(list(neighbors(reached))))
        if np.array_equal(nxt, reached):
            return None
        reached = nxt
    raise AssertionError("Unbounded traversal of a finite lattice")


def seed(wood_temperature, wood):
    hottest = np.maximum.reduce(list(neighbors(np.where(wood, wood_temperature, 0.0))))
    return np.where((~wood) & (hottest > 450), np.minimum(hottest, 750.0), 293.15)


def diffuse(old, wood, links, ratio):
    increment = np.zeros_like(old)
    # With equal positive masses the native min(m_i,m_j)/m_i factor is exactly 1.
    for adjacent, link in zip(neighbors(old), links, strict=True):
        increment += np.where(link, adjacent - old, old.dtype.type(0))
    return old + old.dtype.type(ratio) * increment


def trial(x, conductivity, dtype):
    wood = np.zeros((11, 11, 11), dtype=bool)
    wood[1:10, 1:10, 1:10] = True
    coordinates = np.indices(wood.shape)
    painted = wood & (((coordinates - np.array([x, 5, 5])[:, None, None, None]) ** 2).sum(axis=0) <= 0.49 ** 2)
    links = [wood & n for n in neighbors(wood)]
    exposed = wood & np.logical_or.reduce(list(neighbors(~wood)))
    depth = distance_to_wood_surface(painted, wood, exposed)
    a = np.where(wood, COLD, 293.15).astype(dtype)
    b = np.where(painted, HOT, a).astype(dtype)
    gas_a, gas_b = seed(a, wood), seed(b, wood)
    alpha = conductivity / (RHO * HEAT_CAPACITY)
    substeps = max(1, math.ceil(6 * alpha * DT / (DX ** 2 * 0.8))) if alpha else 0
    ratio = alpha * DT / (DX ** 2 * substeps) if substeps else 0
    possible = None if substeps == 0 or depth is None else math.ceil(depth / substeps)
    equal_gas = np.array_equal(gas_a, gas_b)
    prefix = HORIZON if possible is None else max(0, min(HORIZON, possible - 1))
    if not equal_gas:
        prefix = 0
    # The all-cold branch is an exact fixed point of this reduced operator.
    assert not substeps or np.array_equal(diffuse(a, wood, links, ratio), a)
    ledger = []
    for step in range(HORIZON + 1):
        delta = np.abs(b - a)
        surface = delta[exposed]
        ledger.append([step, int(np.count_nonzero(delta[wood])), int(np.count_nonzero(surface)),
                      float(delta.max()), float(surface.max()), float(b[x, 5, 5])])
        if step < HORIZON:
            for _ in range(substeps):
                b = diffuse(b, wood, links, ratio)
    first = next((row[0] for row in ledger if row[2]), None)
    assert first is None or first >= (possible or 0)
    assert int(painted.sum()) == 1
    return dict(graph_distance=depth, wood_cells=int(wood.sum()), exposed_cells=int(exposed.sum()),
                seed_gas_changed_cells=int(np.count_nonzero(gas_a != gas_b)),
                alpha=alpha, diffusion_substeps_per_step=substeps, ratio=ratio,
                conditional_equal_gas_steps=prefix, first_surface_difference=first,
                largest_surface_delta_K=max(row[4] for row in ledger), final_center_K=ledger[-1][5]), ledger


def calculate():
    scores, ledgers = {}, {}
    for name, x, conductivity in [("surface", 1, 0.15), ("shallow", 3, 0.15),
                                   ("buried", 5, 0.15), ("no_conduction", 5, 0.0)]:
        scores[name], ledgers[name] = {}, {}
        for dtype in (np.float32, np.float64):
            scores[name][dtype.__name__], ledgers[name][dtype.__name__] = trial(x, conductivity, dtype)
    return scores, ledgers


def check_sources(path):
    expected = json.loads((HERE / "SOURCES.json").read_bytes())
    for name, rec in expected["files"].items():
        data = (path / name).read_bytes()
        assert len(data) == rec["size"] and hashlib.sha256(data).hexdigest() == rec["sha256"], name


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Optional checkout of the pinned third-party revision")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.source:
        check_sources(args.source)
    score, ledgers = calculate()
    score_path, rows_path = HERE / "SCORE.json", HERE / "steps.json.gz"
    if args.write:
        score_path.write_text(json.dumps(score, indent=2, allow_nan=False) + "\n", encoding="utf8")
        rows_path.write_bytes(gzip.compress(json.dumps(ledgers, separators=(",", ":"), allow_nan=False).encode(), mtime=0))
    else:
        assert score == json.loads(score_path.read_bytes())
        assert ledgers == json.loads(gzip.decompress(rows_path.read_bytes()))
    for case, entries in score.items():
        e = entries["float32"]
        print(case, e["graph_distance"], e["conditional_equal_gas_steps"],
              e["first_surface_difference"], e["largest_surface_delta_K"],
              entries["float64"]["largest_surface_delta_K"])
