"""Derive frozen Bonsai brushes and native camera/scene inputs using only the fitted rest state."""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from acquire import HERE, LOCAL


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_ply(path):
    with path.open("rb") as stream:
        lines = []
        while stream.tell() < 16384:
            line = stream.readline(1024).decode("ascii").strip()
            lines.append(line)
            if line == "end_header":
                break
        else:
            raise ValueError("No PLY header within 16 KiB")
        offset = stream.tell()
    if lines[:2] != ["ply", "format binary_little_endian 1.0"]:
        raise ValueError("Native binary PLY required")
    elements = [line.split() for line in lines if line.startswith("element ")]
    if len(elements) != 1 or elements[0][1] != "vertex":
        raise ValueError("Only a vertex element is supported")
    count = int(elements[0][2])
    expected = (["x","y","z","nx","ny","nz"] + [f"f_dc_{i}" for i in range(3)] +
                [f"f_rest_{i}" for i in range(45)] + ["opacity"] +
                [f"scale_{i}" for i in range(3)] + [f"rot_{i}" for i in range(4)])
    if [line for line in lines if line.startswith("property ")] != ["property float "+k for k in expected]:
        raise ValueError("Unsupported PLY vertex layout")
    if not 0 < count <= 2000000 or path.stat().st_size != offset+count*4*len(expected):
        raise ValueError("Input exceeds native cap or file size disagrees with header")
    rows = np.memmap(path, dtype="<f4", mode="r", offset=offset, shape=(count,len(expected)))
    return expected, rows


def inspect_cameras(path):
    rows = sorted(json.loads(path.read_bytes()), key=lambda cam:cam["id"])
    if len(rows)<2 or len({c["id"] for c in rows})!=len(rows):
        raise ValueError("Missing or duplicate camera IDs")
    for cam in rows:
        rot = np.asarray(cam["rotation"])
        if (np.linalg.norm(rot.T @ rot-np.eye(3)) > 1e-5 or abs(np.linalg.det(rot)-1)>1e-5
                or not np.isfinite(cam["position"]).all() or min(cam[k] for k in ("fx","fy","width","height"))<=0):
            raise ValueError("Invalid source camera")
    return rows, [rows[0], rows[len(rows)//2]]


def pick_rays(fields, rows, cam):
    # T107 uses a 0.3-pixel low-pass covariance, 3-sigma boundary and stable depth order.
    import sys
    sys.path.insert(0, str(HERE.parent/"t107-visible-burn-progression"))
    from measure import covariances, projection
    pieces = [[], []]
    for start in range(0, len(rows), 32768):
        batch = rows[start:start+32768]
        if not np.isfinite(batch).all():
            raise ValueError("Nonfinite Gaussian attribute")
        pos = batch[:,:3].astype(float)
        q = batch[:,fields.index("rot_0"):fields.index("rot_3")+1].astype(float)
        scale = np.exp(batch[:,fields.index("scale_0"):fields.index("scale_2")+1].astype(float))
        raw = batch[:,fields.index("opacity")].astype(float)
        opacity = np.exp(-np.logaddexp(0., -raw))
        w, h, depth, uv, shape = projection(pos, covariances(q,scale), cam)
        inv = np.linalg.inv(shape)
        for ray, u in enumerate((.43,.50)):
            dx = uv - [(w-1)*u,(h-1)*.50]
            mahal = np.einsum("ni,nij,nj->n",dx,inv,dx)
            alpha = np.minimum(.99, opacity*np.exp(-.5*np.maximum(0, mahal)))
            ix = np.flatnonzero((depth>0) & (mahal<=9) & (alpha>=1/255))
            pieces[ray].append((ix+start, depth[ix], alpha[ix]))
    rays = []
    for chunk_list in pieces:
        ids,z,alpha = [np.concatenate(values) for values in zip(*chunk_list)]
        order = np.lexsort((ids,z))
        cumulative = 1-np.cumprod(1-alpha[order])
        crossings = np.flatnonzero(cumulative>=.5)
        if not len(crossings):
            raise ValueError("No half-opacity crossing on registered ray")
        i = int(crossings[0])
        k = order[i]
        rays.append(dict(id=int(ids[k]),depth=float(z[k]),contributors=len(ids),
                         prior_opacity=float(cumulative[i-1]) if i else 0.,
                         crossing_opacity=float(cumulative[i]),front_to_back_rank=i+1))
    return rays


def ordered_mean(pos):
    # The browser uses three row-ordered binary64 sums during parsePLY.
    return np.array([np.cumsum(pos[:,i], dtype=np.float64)[-1]/len(pos) for i in range(3)])


def inspect_coincident_pick(fields, rows, cam, rays):
    """Compare only the already selected primitive to the native vertex shader footprint cap."""
    from measure import covariances, projection
    row = rows[rays[0]["id"]].astype(float)
    source = row[:3]
    scales = np.exp(row[fields.index("scale_0"):fields.index("scale_0")+3])
    rot = np.asarray(cam["rotation"])
    camera_xyz = (source-np.asarray(cam["position"])) @ rot
    cov = covariances(row[None,-4:],scales[None,:])
    w,h,depth,uv,proj = projection(source[None,:],cov,cam)
    uv = uv[0]
    eigen = np.linalg.eigvalsh(proj[0])
    sigma_radii = 3*np.sqrt(eigen)
    # Both native ellipse radii are capped. Any vertex moves horizontally at most sqrt(2)*rmax.
    # Evaluate in quarter-resolution coordinates, exactly half the native half-source viewport.
    rmax = max(w,h)*.5
    dx_bound = np.sqrt(2)*rmax
    x_gap = max(0., -0.5-uv[0], uv[0]-(w-.5))
    screen_pts = np.array([[(w-1)*u,(h-1)*.5] for u in (.43,.50)])
    focal = np.array([cam["fx"]*w/cam["width"],cam["fy"]*h/cam["height"]])
    center = np.array([(w-1)/2,(h-1)/2])
    cam_rays = np.c_[(screen_pts-center)/focal,np.ones(2)]*depth[0]
    xyz_rays = cam_rays @ rot.T + np.asarray(cam["position"])
    scale = cam["fx"]/(.20*cam["width"]*depth[0])
    depths = (xyz_rays-np.asarray(cam["position"])) @ rot
    roundtrip = depths[:,:2]/depths[:,2,None]*focal+center
    return dict(source_center_xyz=source.tolist(),source_axis_scales=scales.tolist(),
                intrinsic_opacity=float(np.exp(-np.logaddexp(0.,-row[fields.index("opacity")]))),
                camera_xyz=camera_xyz.tolist(),camera_rotation_det=float(np.linalg.det(rot)),
                quarter_view_size=[w,h],screen_points=screen_pts.tolist(),quarter_projected_mean=uv.tolist(),
                uncapped_quarter_covariance=proj[0].tolist(),uncapped_quarter_3sigma_radii=sigma_radii.tolist(),
                quarter_native_radius_cap=rmax,any_quad_vertex_horizontal_displacement_upper_bound=dx_bound,
                center_horizontal_distance_outside_viewport=x_gap,
                outside_even_native_bounding_quad=bool(x_gap>dx_bound),
                source_points_on_the_two_rays_at_shared_depth=xyz_rays.tolist(),
                source_distance_between_these_points=float(np.linalg.norm(xyz_rays[1]-xyz_rays[0])),
                reprojection_max_abs_px=float(np.max(np.abs(roundtrip-screen_pts))),
                implied_world_scale_if_staged=scale,implied_world_depth_if_staged=scale*depth[0])


def derive():
    acquisition = json.loads((HERE/"ACQUISITION.json").read_bytes())
    if acquisition["status"]!="complete":
        raise ValueError("Incomplete source acquisition")
    hashes = {r["local_filename"]:r["sha256"] for r in acquisition["members"]}
    if any(sha(LOCAL/name)!=digest for name,digest in hashes.items()):
        raise ValueError("Private input does not match public receipt")
    fields, rows = read_ply(LOCAL/"scene.ply")
    cameras, selected = inspect_cameras(LOCAL/"cameras.json")
    cam = selected[0]
    rays = pick_rays(fields,rows,cam)
    pos = rows[:,:3].astype(float)
    ia,ib = (ray["id"] for ray in rays)
    if ia==ib:
        return dict(schema="t136-rest-input-v1", status="closed_coincident_primitive",
                    material_count=len(rows), n_float32_fields=len(fields), hashes=hashes,
                    all_camera_count=len(cameras),camera_ids=[c["id"] for c in selected],
                    camera_rows_sha256=[hashlib.sha256(json.dumps(c,sort_keys=True,separators=(",",":")).encode()).hexdigest() for c in selected],
                    rays=rays,diagnosis=inspect_coincident_pick(fields,rows,cam,rays),
                    native_simulations=0,native_renders=0,performance_trials=0)
    scale = cam["fx"]/(.20*cam["width"]*rays[1]["depth"])
    center = ordered_mean(pos)
    offset = np.array([0,.75,0])-(pos[ib]-center)*scale
    cfg = json.loads((HERE.parent/"t42-firewoods-sequential-workflow/recipe.json").read_bytes())
    params = dict(cfg["params"],sceneScale=scale,sceneLift=offset[1],sceneOffX=offset[0],sceneOffZ=offset[2])
    # sceneMax limits PLY decoding; research.reset() validates other physics/display settings separately.
    params.pop("sceneMax")
    dims = [(2*round(c["width"]/4),2*round(c["height"]/4)) for c in selected]
    if len(set(dims))!=1:
        raise ValueError("Selected camera viewport dimensions differ")
    picks = []
    shell_indices = None
    for name,j,radius in (("A",ia,.12),("L",ib,.06),("F",ib,.12)):
        squared = ((pos-pos[j])**2).sum(axis=1)*scale**2
        member = np.flatnonzero(squared<=radius**2).astype("<u4")
        world = (pos[j]-center)*scale+offset
        picks.append(dict(name=name,site=j,source=pos[j].tolist(),world=world.tolist(),radius=radius,
                          initial_geometric_neighbors=len(member),
                          neighbor_uint32le_sha256=hashlib.sha256(member.tobytes()).hexdigest()))
        if name=="F":
            shell_indices = np.flatnonzero((squared>.12**2)&(squared<=.26**2)).astype("<u4")
    visibility = []
    for c in selected:
        xyz = (pos[ib]-c["position"]) @ c["rotation"]
        uv = xyz[:2]/xyz[2]*[c["fx"],c["fy"]]+[(c["width"]-1)/2,(c["height"]-1)/2]
        visibility.append(dict(camera=c["id"],native_pixel_B=uv.tolist(),native_depth_B=float(xyz[2]),
                               in_front_and_in_frame=bool(xyz[2]>0 and 0<=uv[0]<c["width"] and 0<=uv[1]<c["height"])))
    static = dict(schema="t136-rest-input-v1",asset_sha256=hashes["scene.ply"],camera_file_sha256=hashes["cameras.json"],
                  material_count=len(pos),n_float32_fields=len(fields),source_center=center.tolist(),
                  all_camera_count=len(cameras),source_camera_ids=[c["id"] for c in selected],
                  camera_rows_sha256=[hashlib.sha256(json.dumps(c,sort_keys=True,separators=(",",":")).encode()).hexdigest() for c in selected],
                  render_width=dims[0][0],render_height=dims[0][1],camera_visibility=visibility,
                  rays=rays,picks=picks,scale=scale,offset=offset.tolist(),seed=73,dt=cfg["dt"],
                  initial_shell_count=len(shell_indices),
                  initial_shell_uint32le_sha256=hashlib.sha256(shell_indices.tobytes()).hexdigest(),
                  params=params,native_decode_cap=2000000)
    np.save(LOCAL/"geometric-shell.npy",shell_indices,allow_pickle=False)
    (LOCAL/"selected-cameras.json").write_text(json.dumps(selected), encoding="utf8")
    return static


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    start=perf_counter()
    report=derive()
    path=HERE/"STATIC.json"
    if args.check:
        if json.loads(path.read_bytes())!=report:
            raise ValueError("Static fit qualification differs")
    else:
        with path.open("x",encoding="utf8") as stream:
            stream.write(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(report.get("status","static_inputs_ready"),f"{perf_counter()-start:.3f} s")
