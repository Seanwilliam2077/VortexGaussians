"""Register a protected sphere using the original T101 geometry and brush sites."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
UPSTREAM = HERE.parent/"t101-playground-holdout"


def output(name, value):
    data = (json.dumps(value, separators=(",", ":"), allow_nan=False)+"\n").encode()
    dst = HERE/name
    if dst.exists():
        previous = dst.read_bytes()
        assert (gzip.decompress(previous) if name.endswith(".gz") else previous) == data
    else:
        dst.write_bytes(gzip.compress(data, mtime=0) if name.endswith(".gz") else data)


def main():
    recipe = (UPSTREAM/"recipe.json").read_bytes()
    assert hashlib.sha256(recipe).hexdigest() == "57194f5d7558c0d60b383f4ec5ea230834a6d2e454c1d199ed8b55d887f26918"
    cfg = json.loads(recipe)
    data = (UPSTREAM/"local/scene.ply").read_bytes()
    assert hashlib.sha256(data).hexdigest() == cfg["asset_sha256"]
    header_end = data.index(b"end_header\n")+len(b"end_header\n")
    header = data[:header_end].decode("ascii").splitlines()
    fields = [s.split()[-1] for s in header if s.startswith("property float ")]
    assert fields[:3] == ["x","y","z"] and len(cfg["picks"]) == 2
    pos = np.frombuffer(data[header_end:],dtype="<f4").reshape(cfg["material_count"],len(fields))[:,:3].astype("float64")
    midpoint = np.mean([pos[p["site"]] for p in cfg["picks"]], axis=0)
    center_id = int(np.argmin(np.sum((pos-midpoint)**2,axis=1)))
    ids = np.flatnonzero(np.sum((pos-pos[center_id])**2,axis=1) <= 0.12**2).tolist()
    world = (pos[center_id] - cfg["source_center"]).tolist()
    world[1] += cfg["params"]["sceneLift"]
    region = dict(site=center_id, midpoint=midpoint.tolist(), source=pos[center_id].tolist(),world=world,
                  radius=0.12, count=len(ids), brush_intersections={p["name"]:len(set(ids).intersection(
                      p["initial_geometric_neighbors"])) for p in cfg["picks"]})
    cfg["seed"] = 43
    output("recipe.json",cfg)
    output("selection.json",region)
    output("selection-ids.json.gz",ids)
    print(region)


if __name__ == "__main__":
    main()
