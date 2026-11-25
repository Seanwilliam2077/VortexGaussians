"""Project the registered reference cameras, accumulate transmittance and score burn milestones."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from time import perf_counter

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
TASKS = HERE.parent
NATIVE = TASKS / "t86-ignition-margin" / "public"


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def save(path, data):
    raw = (json.dumps(data, separators=(",", ":"), allow_nan=False) + "\n").encode()
    if path.exists():
        if read(path) != data:
            raise ValueError(f"Frozen evidence changed at {path.name}")
    else:
        path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def splats(path):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != "906460f162f704b89666b159ae5b4744e53e6dc11baf448a550de581506919b0":
        raise ValueError("Unknown foreground PLY")
    end = raw.index(b"end_header\n") + len(b"end_header\n")
    columns = [l.split()[2] for l in raw[:end].decode().splitlines() if l.startswith("property float ")]
    data = np.frombuffer(raw[end:], dtype="<f4").reshape(34687, len(columns)).astype(float)
    def cols(fields):
        return data[:, [columns.index(k) for k in fields]]
    pos = cols(("x", "y", "z"))
    q = cols(f"rot_{i}" for i in range(4))
    scale = np.exp(cols(f"scale_{i}" for i in range(3)))
    return pos, covariances(q, scale), 1 / (1 + np.exp(-cols(["opacity"])[:, 0]))


def covariances(quats, scales):
    norm = np.linalg.norm(quats, axis=1)
    if np.any(norm == 0):
        raise ValueError("Degenerate quaternion")
    w, x, y, z = (quats / norm[:, None]).T
    rows = np.stack((1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y),
                     2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x),
                     2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)), axis=1).reshape(-1, 3, 3)
    transform = rows * scales[:, None, :]
    return transform @ transform.transpose(0, 2, 1)


def projection(pos, cov, camera):
    w, h = round(camera["width"]/4), round(camera["height"]/4)
    fx, fy = camera["fx"] * w/camera["width"], camera["fy"] * h/camera["height"]
    rot = np.array(camera["rotation"])
    cam = (pos - camera["position"]) @ rot
    depth = cam[:, 2]
    if np.any(depth == 0):
        raise ValueError("Center on camera plane")
    uv = cam[:, :2] / depth[:, None] * [fx, fy] + [(w-1)/2, (h-1)/2]
    jac = np.zeros((len(pos), 2, 3))
    jac[:, 0, 0], jac[:, 1, 1] = fx/depth, fy/depth
    jac[:, :, 2] = -cam[:, :2] * [fx, fy] / depth[:, None]**2
    projected = jac @ (rot.T @ cov @ rot) @ jac.transpose(0, 2, 1) + 0.3*np.eye(2)
    return w, h, depth, uv, projected


def pixel_check(projection_data, opacity, samples, rendered_t, individual):
    """Evaluate each pixel by projecting all centers directly, without footprint boxes."""
    _, _, depth, uv, proj = projection_data
    order = np.argsort(depth, kind="stable")
    inv = np.linalg.inv(proj)
    for i, xy in enumerate(samples):
        delta = np.array(xy) - uv
        dist = np.einsum("ni,nij,nj->n", delta, inv, delta)
        alpha = np.minimum(.99, opacity*np.exp(-.5*np.maximum(0, dist)))
        alpha[(dist > 9) | (depth <= 0) | (alpha < 1/255)] = 0
        sorted_alpha = alpha[order]
        prefixes = np.r_[1., np.cumprod(1-sorted_alpha)]
        direct = np.empty(len(order))
        direct[order] = prefixes[:-1]*sorted_alpha
        np.testing.assert_allclose(direct, individual[i], atol=2e-13, rtol=2e-13)
        np.testing.assert_allclose(prefixes[-1], rendered_t[xy[1], xy[0]], atol=2e-13)


def raster(projection_data, opacity, shells, event_frames, picks):
    w, h, depth, uv, proj = projection_data
    samples = []
    for center in picks:
        u, v = np.rint(uv[center]).astype(int)
        samples.extend((int(x), int(y)) for x, y in ((u,v),(u+1,v),(u,v+1)) if 0<=x<w and 0<=y<h)
    if not samples:
        samples = [(w//2, h//2)]
    samples = list(dict.fromkeys(samples))
    individual = np.zeros((len(samples), len(depth)))
    trans = np.ones((h, w))
    weights = np.zeros(len(depth))
    overlays = {arm:np.zeros((2,h,w)) for arm in shells}
    for site in np.argsort(depth, kind="stable"):
        if depth[site] <= 0 or opacity[site] < 1/255:
            continue
        u, v = uv[site]
        sx, sy = 3*np.sqrt(np.diag(proj[site]))
        left, right = max(0, math.ceil(u-sx)), min(w-1, math.floor(u+sx))
        top, bottom = max(0, math.ceil(v-sy)), min(h-1, math.floor(v+sy))
        if left>right or top>bottom:
            continue
        xs = np.arange(left, right+1)-u
        ys = (np.arange(top, bottom+1)-v)[:, None]
        a, b, c = proj[site,0,0], proj[site,0,1], proj[site,1,1]
        dist = (c*xs*xs-2*b*xs*ys+a*ys*ys)/(a*c-b*b)
        alpha = np.minimum(.99, opacity[site]*np.exp(-.5*dist))
        alpha[(dist>9) | (alpha<1/255)] = 0
        box = np.s_[top:bottom+1, left:right+1]
        contribution = trans[box]*alpha
        weights[site] = contribution.sum()
        for j, (x,y) in enumerate(samples):
            if left<=x<=right and top<=y<=bottom:
                individual[j,site] = contribution[y-top,x-left]
        for arm,ids in shells.items():
            if site in ids:
                overlays[arm][0][box] += contribution
                if event_frames[arm][site] <= 360:
                    overlays[arm][1][box] += contribution
        trans[box] *= 1-alpha
    pixel_check(projection_data, opacity, samples, trans, individual)
    np.testing.assert_allclose(weights.sum(), (1-trans).sum(), atol=1e-8, rtol=3e-13)
    return weights, 1-trans, overlays, samples


def masks(pos, recipe):
    native = read(NATIVE/"capture-report.json")
    eligible, events = {}, {}
    for arm in ("AB", "BA"):
        cfg = next(p for p in recipe["picks"] if p["name"]==arm[1])
        delta = pos - pos[cfg["index"]]
        d2 = np.einsum("ij,ij->i", delta, delta)
        region = set(np.flatnonzero((d2 > .12**2) & (d2 <= .26**2)).tolist())
        shot = native["shots"][arm]
        rows = read(NATIVE/f"{arm}-trace.json.gz")
        already = set(shot["initial"]["ids"]) | set(shot["edit"]["ids"])
        for row in rows[:180]:
            already.update(row["new_ids"])
        eligible[arm] = region - already
        events[arm] = np.full(len(pos), 361, dtype=int)
        for row in rows[180:]:
            events[arm][row["new_ids"]] = row["frame"]
    return eligible, events


def score(weights, eligible, event):
    ids = np.array(sorted(eligible), dtype=int)
    counts = np.bincount(event[ids], minlength=362)[181:361].cumsum()
    masses = np.bincount(event[ids], weights=weights[ids], minlength=362)[181:361].cumsum()
    def first(x, t):
        meets = np.flatnonzero(x >= t)
        return int(meets[0])+1 if meets.size else None
    total = weights[ids].sum()
    return dict(eligible=len(ids), represented=int(np.count_nonzero(weights[ids])),
                mass=float(total), first_site=first(counts,1), quarter_sites=first(counts,len(ids)/4),
                quarter_matte=first(masses,total/4) if total>0 else None,
                counts=counts.tolist(), cumulative_mass=masses.tolist())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=HERE.parents[4]/"real-asset-ingest")
    parser.add_argument("--out", type=Path, default=HERE/"evidence")
    args = parser.parse_args()
    args.out.mkdir(exist_ok=True, parents=True)
    np.testing.assert_allclose(covariances(np.array([[1.,0,0,0],[.5**.5,0,0,.5**.5]]),
                                           np.array([[2.,1,3],[2.,1,3]])), [np.diag([4,1,9]),np.diag([1,4,9])], atol=2e-14)
    pos, cov, opacity = splats(args.source/"foreground.ply")
    cams = sorted(read(args.source/"cameras.json"), key=lambda c:c["id"])
    cfg = read(TASKS/"t42-firewoods-sequential-workflow"/"recipe.json")
    assert cams[0] == cfg["camera"]
    eligible, events = masks(pos, cfg)
    cost = {}
    for camera in (cams[0], cams[len(cams)//2]):
        start = perf_counter()
        proj = projection(pos, cov, camera)
        weights, coverage, views, samples = raster(proj, opacity, eligible, events, [p["index"] for p in cfg["picks"]])
        cid = camera["id"]
        cost[cid] = perf_counter()-start
        rows = {arm:score(weights,ids,events[arm]) for arm,ids in eligible.items()}
        union = sorted(eligible["AB"] | eligible["BA"])
        save(args.out/f"weights-{cid}.json.gz", dict(camera_id=cid, asset_count=len(weights),
             eligible_weights=[[i,float(weights[i])] for i in union]))
        save(args.out/f"camera-{cid}.json.gz", dict(camera=camera,checked_pixels=samples,
             total_projected_mass=float(coverage.sum()),eligible_weights=[[i,float(weights[i])] for i in union],orders=rows))
        for arm, (shell, burnt) in views.items():
            rgb = (1-coverage[:,:,None])*255 + (coverage-shell)[:,:,None]*[121,131,137]
            rgb += (shell-burnt)[:,:,None]*[38,135,167] + burnt[:,:,None]*[219,80,32]
            Image.fromarray(np.rint(np.clip(rgb,0,255)).astype("uint8")).save(args.out/f"camera-{cid}-{arm}.png")
            r = rows[arm]
            print(cid,arm,{k:v for k,v in r.items() if not isinstance(v,list)})
    print("Raster and verification seconds",cost)
    if not (args.out/"cost.json").exists():
        save(args.out/"cost.json", {str(k):v for k,v in cost.items()})


if __name__ == "__main__":
    main()
