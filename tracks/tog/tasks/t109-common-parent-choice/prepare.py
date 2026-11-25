"""Freeze both clicks and verify the two archived static mattes directly from the fitted PLY."""
import gzip
import hashlib
import json
import math
import os
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASKS = HERE.parent
ROOT = HERE.parents[3]


def load(f):
    b = f.read_bytes()
    return json.loads(gzip.decompress(b) if f.suffix == ".gz" else b)


def write(p, obj):
    raw = (json.dumps(obj, separators=(",", ":")) + "\n").encode()
    data = gzip.compress(raw, mtime=0) if p.suffix == ".gz" else raw
    if p.exists():
        assert load(p) == obj
    else:
        p.write_bytes(data)


def prepare():
    cfg = load(TASKS / "t42-firewoods-sequential-workflow/recipe.json")
    origin = load(TASKS / "t86-ignition-margin/public/capture-report.json")
    raw = Path(os.environ.get("T86_PLY", ROOT.parent / "real-asset-ingest/foreground.ply")).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == origin["sources"]["Firewoods_foreground"]["sha256"]
    off = raw.index(b"end_header\n") + len(b"end_header\n")
    lines = raw[:off].decode("ascii").splitlines()
    props = [x for x in lines if x.startswith("property ")]
    n = int(next(x for x in lines if x.startswith("element vertex ")).split()[2])
    stride = 4 * len(props)
    assert props[:3] == ["property float " + k for k in "xyz"] and all(x.startswith("property float ") for x in props)
    assert len(raw) == off + n * stride and n == 34687
    xyz = [struct.unpack_from("<fff", raw, off + stride*i) for i in range(n)]
    ctr, lift = cfg["source_center"], cfg["params"]["sceneLift"]
    world = [(x-ctr[0], y-ctr[1]+lift, z-ctr[2]) for x, y, z in xyz]
    orig_a, orig_b = cfg["picks"]
    def ball_dist(p):
        return [math.dist(pos, p["world"]) for pos in world]
    d = ball_dist(orig_b)
    for o, ds in [(orig_a, ball_dist(orig_a)), (orig_b, d)]:
        assert {i for i, v in enumerate(ds) if v <= o["radius"]} == set(o["initial_geometric_neighbors"])
    shell = [i for i, r in enumerate(d) if .12 < r <= .26]
    assert len(shell) == 2371 and shell == load(TASKS / "t87-stroke-halo/PREDICTIONS.json.gz")["shell_ids"]["AB"]
    old = origin["shots"]["AB"]
    trace = load(TASKS / "t86-ignition-margin/public/AB-trace.json.gz")
    prior_lit = set(old["initial"]["ids"]) | set(old["edit"]["ids"])
    for row in trace[:180]:
        prior_lit.update(row["new_ids"])
    assert not prior_lit.intersection(shell)
    matte = {}
    for camera in (0, 124):
        f = TASKS / f"t107-visible-burn-progression/evidence/weights-{camera}.json.gz"
        src = load(f)
        ids = dict(src["eligible_weights"])
        assert len(ids) == len(src["eligible_weights"]) and src["camera_id"] == camera and src["asset_count"] == n
        assert all(i in ids and math.isfinite(ids[i]) and ids[i]>=0 for i in shell)
        matte[str(camera)] = {"sha256": hashlib.sha256(f.read_bytes()).hexdigest(), "shell_sites":len(shell),
                              "stored_pairs":len(ids), "shell_micro_pixels":sum(math.floor(ids[i]*1e6+.5) for i in shell)}
    picks = [orig_a]
    for name, r in [("L", .06), ("F", .12)]:
        ids = [i for i, dist in enumerate(d) if dist <= r]
        assert not set(ids).intersection(shell)
        picks.append({**orig_b, "name":name, "radius":r, "initial_geometric_neighbors":ids})
    cfg.update(schema="t109-common-parent-variants-v1", seed=53, picks=picks, material_count=n, asset_sha256=digest)
    for stale in ("selection", "scientific_claim", "mode_scope", "reset_scope", "parent_commit"):
        cfg.pop(stale, None)
    write(HERE/"recipe.json",cfg)
    write(HERE/"shell.json.gz",shell)
    write(HERE/"STATIC.json",{"asset_sha256":digest,"shell_size":len(shell),"brush_counts":{p["name"]:len(p["initial_geometric_neighbors"]) for p in picks},
                              "cameras":matte, "old_AB_excluded_shell_sites":len(prior_lit.intersection(shell))})


if __name__ == "__main__":
    prepare()
