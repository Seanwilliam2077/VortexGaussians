"""Rebuild a deterministic native PLY from two fixed CC0 glTF files."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
import urllib.request

HERE = Path(__file__).resolve().parent
LOCAL = HERE / "local"
BASE = "https://dl.polyhaven.org/file/ph-assets/Models/gltf/"
SOURCES = {
    "model.gltf": ("1k/dead_tree_trunk/dead_tree_trunk_1k.gltf", 2812,
                   "8baaf1ff66ba1f79acdceed0dc3797a882990a3abb10b18abe56762f34c26e39"),
    "dead_tree_trunk.bin": ("8k/dead_tree_trunk/dead_tree_trunk.bin", 2293788,
                            "c1ac6b3195246e8647a28eee2fbfdd4712a045c7cf2dcb4f5abcc2d40a446ca6"),
}

def require(ok, message):
    if not ok:
        raise ValueError(message)

def read_source(name, download):
    suffix, size, digest = SOURCES[name]
    p = LOCAL / name
    if not p.exists() and download:
        req = urllib.request.Request(BASE + suffix, headers={"User-Agent": "VortexGaussians graphics research"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read(size + 1)
        require(len(data) == size and hashlib.sha256(data).hexdigest() == digest, "Download identity: " + name)
        p.write_bytes(data)
    data = p.read_bytes()
    require(len(data) == size and hashlib.sha256(data).hexdigest() == digest, "Source identity: " + name)
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="fetch the two pinned official files, if missing")
    args = parser.parse_args()
    LOCAL.mkdir(exist_ok=True)
    gltf = json.loads(read_source("model.gltf", args.download))
    buf = read_source("dead_tree_trunk.bin", args.download)
    require(gltf["nodes"] == [{"mesh": 0, "name": "dead_tree_trunk"}], "Unexpected placement")
    a = gltf["accessors"][gltf["meshes"][0]["primitives"][0]["attributes"]["POSITION"]]
    v = gltf["bufferViews"][a["bufferView"]]
    require(a["type"] == "VEC3" and a["componentType"] == 5126 and v["buffer"] == 0
            and v["byteLength"] == 12*a["count"] and v.get("byteStride", 12) == 12, "Unexpected accessor")
    start = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    positions = list(dict.fromkeys(struct.iter_unpack("<fff", buf[start:start+12*a["count"]])))
    n = len(positions)
    center = [0., 0., 0.]
    for p in positions:
        for k in range(3):
            center[k] += p[k]
    center = [c/n for c in center]
    src_min = list(map(min, zip(*positions)))
    src_max = list(map(max, zip(*positions)))
    row = struct.Struct("<14f")
    fields = "x y z f_dc_0 f_dc_1 f_dc_2 opacity scale_0 scale_1 scale_2 rot_0 rot_1 rot_2 rot_3".split()
    header = ["ply", "format binary_little_endian 1.0", f"element vertex {n}"]
    header += ["property float "+f for f in fields] + ["end_header", ""]
    ply = bytearray("\n".join(header).encode("ascii"))
    attributes = (0., 0., 0., 3., *([math.log(0.006)]*3), 1., 0., 0., 0.)
    for p in positions:
        ply.extend(row.pack(*p, *attributes))
    (LOCAL / "scene.ply").write_bytes(ply)
    parent = json.loads((HERE.parent/"t42-firewoods-sequential-workflow"/"recipe.json").read_text())
    cfg = {k: parent[k] for k in ("dt","params","camera","width","height","steps_per_interval","intervals")}
    cfg.update(schema="t92-fixed-transfer-recipe-v1", seed=23, source_center=center, material_count=n,
               asset_sha256=hashlib.sha256(ply).hexdigest(), gltf_position_count=a["count"], picks=[])
    shells = {}
    for name, fraction in [("A", .25), ("B", .75)]:
        target = [src_min[0]+fraction*(src_max[0]-src_min[0]), src_max[1], (src_min[2]+src_max[2])/2]
        j = min(range(n), key=lambda i: math.dist(positions[i], target))
        pos = positions[j]
        radius = .12
        distances = [math.dist(p, pos) for p in positions]
        direct = [i for i, d in enumerate(distances) if d <= radius]
        shells[name] = [i for i, d in enumerate(distances) if radius < d <= radius + .14]
        world = [pos[k]-center[k] for k in range(3)]
        world[1] += cfg["params"]["sceneLift"]
        cfg["picks"].append(dict(name=name, radius=radius, world=world, site=j,
                                 initial_geometric_neighbors=direct, shell_size=len(shells[name])))
    # A native cut's exact governing controls are inherited; camera metadata is a fixed
    # observer on world-fixed layers. No image from the earlier scene is used.
    for name, data in [("recipe.json", cfg), ("shell-ids.json.gz", shells)]:
        dest = HERE / name
        raw = (json.dumps(data, separators=(",", ":"), ensure_ascii=True)+"\n").encode()
        payload = gzip.compress(raw, compresslevel=6, mtime=0) if name.endswith("gz") else raw
        if dest.exists():
            # Gzip metadata can differ across Python/zlib versions; compare decoded contents.
            stored = gzip.decompress(dest.read_bytes()) if name.endswith("gz") else dest.read_bytes()
            require(json.loads(stored) == data, "Frozen staging mismatch: "+name)
        else:
            dest.write_bytes(payload)
    print("Sites", n, "from", a["count"], "mesh vertices; direct/shell", [(len(p["initial_geometric_neighbors"]), p["shell_size"]) for p in cfg["picks"]])
    print("PLY SHA256",cfg["asset_sha256"])

if __name__ == "__main__":
    main()
