"""Qualify the pinned brush on original Playground wood and guaranteed obstacles."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import zipfile

import numpy as np
from scipy import ndimage as ndi
from scipy import __version__ as scipy_version

HERE = Path(__file__).resolve().parent
SHAPE = (88, 88, 104)
ORIGIN = np.array([-1.7, -1.5, -0.65])
DX = 0.04
TARGET = np.array([0.05, 0.2, 0.15])
LOWER = np.array([-1.190500020980835, -0.9205000400543213, -1.2904999256134033])
UPPER = np.array([1.2404999732971191, 1.5104999542236328, 1.1405000686645508])
FOREGROUND = "3f27f88a647d26fa1b1fd6624eb44ba6e6f0e9c2574ab51b5d3e806aa8fee749"
CROSS = ndi.generate_binary_structure(3, 1)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_foreground(path):
    data = path.read_bytes()
    assert digest(data) == FOREGROUND
    pos = data.index(b"end_header\n") + len(b"end_header\n")
    header = data[:pos].decode().splitlines()
    assert "format binary_little_endian 1.0" in header and "element vertex 80023" in header
    props = [line.split()[2] for line in header if line.startswith("property float ")]
    result = np.frombuffer(data[pos:], dtype=[(p, "<f4") for p in props])
    assert len(result) == 80023
    return result


def grid(points):
    ids = np.floor((points - ORIGIN) / DX).astype(int)
    valid = ((ids >= 0) & (ids < SHAPE)).all(axis=1)
    mask = np.zeros(SHAPE, dtype=bool)
    mask[tuple(ids[valid].T)] = True
    return mask


def geometry_check(inputs, cropped_ply):
    receipt = json.loads((HERE / "ACQUISITION.json").read_bytes())
    for name, meta in receipt["members"].items():
        assert digest((inputs/name).read_bytes()) == meta["sha256"], name

    def storage(name, dtype, shape):
        # These exact-pinned PyTorch archives each contain one contiguous CPU-readable
        # tensor storage. No pickle or imported upstream code is executed.
        with zipfile.ZipFile(inputs/(name+".pth")) as z:
            b = z.read(name+"/data/0")
        return np.frombuffer(b, dtype=dtype).reshape(shape)

    ids = storage("indices_pts_in_grids", "<i8", (80023, 3))
    mask = storage("mask_pts_in_grids", np.bool_, (1268409,))
    labels = np.load(inputs/"material_grid.npy", allow_pickle=False, mmap_mode="r")
    fg = load_foreground(cropped_ply)
    xyz = np.stack([fg[c] for c in ("x","y","z")], axis=-1)
    frac = (xyz - LOWER) / ((UPPER-LOWER)/256)
    err = np.maximum(ids-frac, frac-ids-1).max()
    assert labels.shape == (256,256,256) and mask.sum() == len(ids) and err <= 0.001
    assert (ids >= 0).all() and (ids < 256).all()
    wood_ids = np.argwhere(labels == 1)
    wood_before = grid(LOWER+(wood_ids+0.5)*(UPPER-LOWER)/256)
    wood = ndi.binary_fill_holes(ndi.binary_closing(wood_before, iterations=1))
    # PhysStudio's scene uses raw means for this preset. Use only safely interior
    # logit/log-scale inequalities to form a subset of its complete obstacle mask.
    logscale = np.maximum.reduce([fg[f"scale_{i}"] for i in range(3)])
    collision_subset = ((xyz > [-1.3,-1.1,-0.55]) & (xyz < [1.4,1.65,0.5])).all(axis=-1)
    collision_subset &= (fg["opacity"] > np.log(1.5) + 1e-5) & (logscale < np.log(0.08)-1e-5)
    obstacles = grid(xyz[collision_subset])
    known_solid = wood | obstacles
    # A missing ground/obstacle can delete open faces. Distance to possible
    # exposed wood is a lower bound on distance to actual exposed wood.
    possible_exposed = wood & ndi.binary_dilation(~known_solid, structure=CROSS)
    w = np.argwhere(wood)
    centers = ORIGIN+(w+0.5)*DX
    d2 = ((centers-TARGET)**2).sum(axis=1)
    closest = np.flatnonzero(d2 == d2.min())
    center_id, center = w[closest[0]], centers[closest[0]]
    # Simulate Warp's binary32 point/center/radius convention for the brush.
    brush_centers = ORIGIN.astype("f") + (w.astype("f")+np.float32(0.5))*np.float32(DX)
    distance = np.sqrt(np.sum((brush_centers-center.astype("f"))**2, axis=1))
    footprint = w[distance <= np.float32(1.1*DX)]
    brush = np.zeros_like(wood)
    brush[tuple(footprint.T)] = True
    connected = ndi.label(brush, CROSS)[1]
    assert len(footprint) > 0 and connected == 1
    front = brush.copy()
    lower_bound = None
    for step in range(int(wood.sum())):
        if (front & possible_exposed).any():
            lower_bound=step
            break
        nxt = ndi.binary_dilation(front, structure=CROSS, mask=wood)
        if np.array_equal(nxt,front):
            break
        front=nxt
    adj = ndi.binary_dilation(brush, structure=CROSS) & ~known_solid
    candidates = np.argwhere(adj)
    return dict(shape=SHAPE,dx=DX,original_foreground_sha256=FOREGROUND,
                mapped_rows=int(mask.sum()),full_scene_rows=len(mask),mapping_max_cell_error=float(err),
                source_wood_label_cells=len(wood_ids),wood_before_closing=int(wood_before.sum()),
                wood_after_fill=int(wood.sum()),wood_grid_u8_c_sha256=digest(wood.astype("u1").tobytes()),
                known_collision_points=int(collision_subset.sum()),known_collision_cells=int(obstacles.sum()),
                known_solid_cells=int(known_solid.sum()),known_solid_u8_c_sha256=digest(known_solid.astype("u1").tobytes()),
                target=TARGET.tolist(),center_ijk=center_id.tolist(),center_world=center.tolist(),
                nearest_distance=float(np.sqrt(d2.min())),nearest_tied=closest.size,
                brush_radius=float(1.1*DX),changed_wood_ijk=footprint.tolist(),wood_support_components=int(connected),
                lower_bound_to_open_face=lower_bound,maximum_seed_disagreements=len(candidates),
                candidate_seed_sites_ijk=candidates.tolist(),
                exact_seed_agreement_proved=(len(candidates)==0),complete_obstacles_available=False,
                ground_fit_available=False,measured_native_gas_steps=0)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("labels_and_mapping",type=Path)
    parser.add_argument("original_foreground_ply",type=Path)
    parser.add_argument("--write",action="store_true")
    args=parser.parse_args()
    start=time.perf_counter()
    result=geometry_check(args.labels_and_mapping,args.original_foreground_ply)
    path=HERE/"GEOMETRY.json"
    if args.write:
        path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    else:
        assert json.loads(json.dumps(result)) == json.loads(path.read_bytes())
    print(json.dumps(dict(seconds=time.perf_counter()-start,numpy=np.__version__,scipy=scipy_version,
                          distance=result["lower_bound_to_open_face"],
                          candidate_seed_sites=len(result["candidate_seed_sites_ijk"]))))
