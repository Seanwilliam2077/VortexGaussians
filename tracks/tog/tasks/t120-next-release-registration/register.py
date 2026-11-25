"""Rebuild the prospective lower-band Playground input from three verified local files."""
import gzip
import hashlib
import json
import math
import zlib
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
T101 = HERE.parent / "t101-playground-holdout"
T111 = HERE.parent / "t111-playground-shot-choice"
ORIGINAL = "3f27f88a647d26fa1b1fd6624eb44ba6e6f0e9c2574ab51b5d3e806aa8fee749"
STAGED = "cb048992c117078016d5554b8205ec33e0d8e19d4d0196c0affd529fd20c0914"
CAMERAS = "f2ad2236ddfaccac88e8b83cbe0c17a9f11f92a2071f3a8a447f79c27e0722d2"
SEED_LITERAL = "VortexGaussians:T120:Playground:lower-band:1"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verified(path, expected):
    raw = path.read_bytes()
    if digest(raw) != expected:
        raise ValueError(f"Incorrect input: {path.name}")
    return raw


def xyz(raw):
    start = raw.index(b"end_header\n") + len(b"end_header\n")
    lines = raw[:start].decode("ascii").splitlines()
    fields = [line.split()[-1] for line in lines if line.startswith("property float ")]
    count = int(next(s for s in lines if s.startswith("element vertex ")).split()[-1])
    assert "format binary_little_endian 1.0" in lines and fields[:3] == ["x", "y", "z"]
    assert len(fields) == sum(s.startswith("property ") for s in lines)
    return np.frombuffer(raw[start:], dtype="<f4").reshape(count, len(fields))[:, :3].astype(float)


def publish(name, data):
    raw = (json.dumps(data, separators=(",", ":"), allow_nan=False) + "\n").encode()
    path = HERE / name
    if path.exists():
        stored = path.read_bytes()
        if path.suffix == ".gz":
            stored = gzip.decompress(stored)
        if stored != raw:
            raise ValueError(f"Frozen registration differs: {name}")
        return
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def archive_member(name, offset, packed, raw):
    return dict(member=name, local_header_offset=offset, packed_bytes=packed, bytes=len(raw),
                crc32=zlib.crc32(raw), sha256=digest(raw))


def membership(ids):
    ordered = np.array(ids, dtype="<u4").tobytes()
    return dict(count=len(ids), ordered_uint32le_sha256=digest(ordered))


def main():
    cfg = json.loads((T101 / "recipe.json").read_bytes())
    frozen_cfg = json.loads((T111 / "recipe.json").read_bytes())
    assert all(cfg[key] == frozen_cfg[key] for key in
               ("dt", "params", "camera", "width", "height", "asset_sha256", "original_sha256"))
    assert cfg["asset_sha256"] == STAGED and cfg["original_sha256"] == ORIGINAL
    original = verified(T101 / "local/foreground.ply", ORIGINAL)
    staged = verified(T101 / "local/scene.ply", STAGED)
    cam_bytes = verified(T111 / "local/cameras.json", CAMERAS)
    pos = xyz(staged)
    origin = np.array(cfg["center_before"])
    center = np.array(cfg["source_center"])
    lift = np.array([0.0, cfg["params"]["sceneLift"], 0.0])
    assert len(pos) == cfg["material_count"] == 80023
    assert np.array_equal(((xyz(original)-origin)*cfg["scale"]).astype("<f4"), pos)
    lo, hi = pos.min(axis=0), pos.max(axis=0)
    assert math.isclose(max(hi-lo), 1.6, abs_tol=1e-7)

    old_sites = [p["site"] for p in cfg["picks"]]
    picks = {}
    squared = {}
    for name, x in (("A", .25), ("B", .75)):
        target = lo+(hi-lo)*[x, .10, .50]
        d2 = np.sum((pos-target)**2, axis=1)
        site = int(np.argmin(d2))
        squared[name] = np.sum((pos-pos[site])**2, axis=1)
        picks[name] = dict(site=site, world=(pos[site]-center+lift).tolist())
    shell = np.flatnonzero((squared["B"] > .12**2) & (squared["B"] <= (.12+.14)**2)).tolist()
    seed_digest = digest(SEED_LITERAL.encode())
    seed = int(seed_digest[:8], 16)
    cfg.update(schema="t120-lower-band-playground-v1", seed=seed, picks=[])
    brushes = {}
    for name, anchor, radius in (("A", "A", .12), ("L", "B", .08), ("F", "B", .12)):
        ids = np.flatnonzero(squared[anchor] <= radius**2).tolist()
        brushes[name] = set(ids)
        count = int(np.count_nonzero((squared[anchor] > .12**2) & (squared[anchor] <= (.12+.14)**2)))
        cfg["picks"].append(dict(name=name, **picks[anchor], radius=radius,
                                 initial_geometric_neighbors=ids, shell_size=count))
    assert not brushes["F"].intersection(shell)
    nested = brushes["L"] < brushes["F"]
    distinct = picks["A"]["site"] != picks["B"]["site"]

    cameras = sorted(json.loads(cam_bytes), key=lambda row: row["id"])
    assert len({row["id"] for row in cameras}) == len(cameras)
    poses = []
    for index in (len(cameras)//4, 3*len(cameras)//4):
        cam = cameras[index]
        rotation = np.array(cam["rotation"])
        position = np.array(cam["position"])
        assert position.shape == (3,) and np.isfinite(position).all()
        assert rotation.shape == (3,3) and np.isfinite(rotation).all()
        assert all(math.isfinite(cam[k]) and cam[k] > 0 for k in ("fx", "fy", "width", "height"))
        assert np.max(np.abs(rotation.T@rotation - np.eye(3))) < 1e-6
        assert abs(np.linalg.det(rotation) - 1.0) < 1e-6
        poses.append(dict(sorted_index=index, id=cam["id"], image_name=cam["img_name"],
                          image_size=[cam["width"], cam["height"]],
                          source_row_sha256=digest(json.dumps(cam, sort_keys=True, separators=(",", ":")).encode()),
                          center_world=((position-origin)*cfg["scale"]-center+lift).tolist()))
    acquisition = dict(archive_file_id="1NFXzr0YU3q1_ezjWVEgTmd-R8JX4J0lL", archive_bytes=1049696735,
                       members=[archive_member("Playground/fg/fg_opac_0_burnable.ply", 689019218, 17965855, original),
                                archive_member("Playground/cameras.json", 3265585, 39564, cam_bytes)],
                       transformed_scene_sha256=STAGED, transformed_scene_bytes=len(staged))
    assert [m["crc32"] for m in acquisition["members"]] == [168304271, 3892802308]
    assert [m["bytes"] for m in acquisition["members"]] == [19847234, 123582]
    registration = dict(
        stage="static-registration", asset="FieryGS Playground", n_sites=len(pos), n_cameras=len(cameras),
        rng=dict(literal=SEED_LITERAL, sha256=seed_digest, uint32=seed),
        prior_upper_site_ids=old_sites, lower_sites=picks, new_centers_disjoint_from_prior_ids=(
            not set(old_sites).intersection(v["site"] for v in picks.values())),
        distinct_centers=distinct, strictly_nested=nested, full_minus_light=len(brushes["F"]-brushes["L"]),
        a_full_overlap=len(brushes["A"] & brushes["F"]), b_shell=membership(shell),
        brush_geometry={p["name"]: membership(p["initial_geometric_neighbors"]) for p in cfg["picks"]},
        camera_choices=poses, legacy_t111_camera_ids=[cameras[0]["id"], cameras[len(cameras)//2]["id"]],
        input_transform=dict(source_bbox_mid=origin.tolist(), positive_uniform_scale=cfg["scale"],
                             normalized_foreground_mean=center.tolist(), world_translation_after_center=lift.tolist(),
                             gaussian_order="original PLY vertex order"),
        readout=dict(parent_frame=180, horizon=90, dt=cfg["dt"], second_stroke_radii=[.08, .12],
                     shell="(0.12,0.26] about B", eligible="cold and fuel-positive after parent, before second stroke",
                     denominator="sum of eligible static foreground opacity weights, each rounded to integer micro-pixels",
                     crossing="ceil(eligible mass / 4) for BOTH registered cameras by H; zero mass undefined",
                     policy="light first; try full only if needed, with a common restored parent"),
        acquisition=acquisition
    )
    publish("recipe.json", cfg)
    publish("shell.json.gz", shell)
    publish("REGISTRATION.json", registration)
    print(seed, [p["site"] for p in cfg["picks"]], [len(brushes[k]) for k in ("A","L","F")],
          len(shell), [p["id"] for p in poses], "strict nesting", nested, "distinct centers", distinct)


if __name__ == "__main__":
    main()
