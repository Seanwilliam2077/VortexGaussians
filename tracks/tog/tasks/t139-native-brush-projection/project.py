"""Evaluate the room's two fixed brush rays with the original native renderer's footprint rules."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/"t136-bonsai-shot"))
from prepare import LOCAL, inspect_cameras, ordered_mean, read_ply, sha
sys.path.insert(0, str(HERE.parent/"t107-visible-burn-progression"))
from measure import covariances

OLD = 867267
PES = np.float32(0.0111089965)


def project_shape(batch, fields, cam_points, rotation, scale, size, focal):
    """Return display mean and capped GL x/right, y/up axes for front-clipped splats."""
    dtype = np.float32
    deviation = np.exp(batch[:,fields.index("scale_0"):fields.index("scale_0")+3].astype(float))
    q = batch[:,fields.index("rot_0"):fields.index("rot_0")+4].astype(float)
    cov_world = (covariances(q,deviation)*scale**2).astype(dtype)
    # The source camera provides right/down/forward. Native view uses right/up/backwards.
    view = (np.diag([1.,-1.,-1.])@rotation.T).astype(dtype)
    cv = view@cov_world@view.T
    x, up, d = cam_points[:,0], -cam_points[:,1], cam_points[:,2]
    fx,fy = focal
    width,height = size
    jac = np.zeros((len(batch),2,3),dtype=dtype)
    jac[:,0,0] = fx/d
    jac[:,1,1] = fy/d
    for axis,(v,f,pixels) in enumerate(((x,fx,width),(up,fy,height))):
        limit = dtype(1.3*.5*pixels/f)
        tx = d*np.clip(v/d,-limit,limit)
        jac[:,axis,2] = f*tx/(d*d)
    s2 = jac@cv@jac.transpose(0,2,1)
    a,b,c = s2[:,0,0]+dtype(.3),s2[:,1,0],s2[:,1,1]+dtype(.3)
    mid = dtype(.5)*(a+c)
    rad = np.sqrt(np.maximum(dtype(.01),mid*mid-(a*c-b*b)))
    major,minor = mid+rad,np.maximum(dtype(.01),mid-rad)
    e1 = np.stack((b,major-a),axis=1)
    fallback = np.abs(b)<=dtype(1e-6)
    e1[fallback] = [1,0]
    e1 /= np.linalg.norm(e1,axis=1)[:,None]
    e2 = np.stack((-e1[:,1],e1[:,0]),axis=1)
    r1 = np.minimum(3*np.sqrt(major),dtype(.5*max(size)))
    r2 = np.minimum(3*np.sqrt(minor),r1)
    mean = np.c_[x/d*fx+(width-1)*.5,-up/d*fy+(height-1)*.5]
    return mean,e1,e2,r1,r2


def crossing(ids, alphas, half):
    current = 0.
    for n,(idx,alpha) in enumerate(zip(ids,alphas)):
        prior = current
        current = prior+(1-prior)*float(alpha)
        if half:
            current = float(np.float16(current))
        if current>=.5:
            return dict(id=int(idx),rank=n+1,before=prior,after=current)
    return dict(id=None,rank=None,before=None,after=current)


def probe(rows, fields, cam, scale, size, targets):
    rotation = np.array(cam["rotation"])
    focal = np.array([cam["fx"]*size[0]/cam["width"],cam["fy"]*size[1]/cam["height"]],np.float32)
    parts = [[] for _ in targets]
    all_depth = ((rows[:,:3]-cam["position"])@rotation[:,2])*scale
    minimum,maximum = all_depth.min(),all_depth.max()
    depth_keys = all_depth.astype("<f4").astype(float)
    buckets = np.clip(np.trunc((depth_keys-minimum)*(1536/(maximum-minimum))),0,1535).astype(np.uint16)
    valid = np.flatnonzero((all_depth.astype(np.float32)>=.2) & (all_depth.astype(np.float32)<=50))
    for start in range(0,len(valid),32768):
        ids = valid[start:start+32768]
        batch = rows[ids]
        cam_points = (((batch[:,:3]-cam["position"])@rotation)*scale).astype(np.float32)
        mean,e1,e2,r1,r2 = project_shape(batch,fields,cam_points,rotation,scale,size,focal)
        if not all(np.isfinite(x).all() for x in (mean,e1,e2,r1,r2)):
            raise ArithmeticError("Nonfinite native-style projection")
        raw = batch[:,fields.index("opacity")].astype(float)
        opacity = np.exp(-np.logaddexp(0.,-raw)).astype(np.float32)
        for target,save in zip(targets,parts):
            dx = np.stack((np.float32(target[0])-mean[:,0],mean[:,1]-np.float32(target[1])),axis=1)
            v1 = np.einsum("ni,ni->n",dx,e1)/r1
            v2 = np.einsum("ni,ni->n",dx,e2)/r2
            rho2 = v1*v1+v2*v2
            hit = np.flatnonzero(rho2<1)
            alpha = opacity[hit]*(np.exp(np.float32(-4.5)*rho2[hit])-PES)/(np.float32(1)-PES)
            keep = alpha>0
            save.append((ids[hit][keep],alpha[keep]))
    logs = []
    streams = {}
    for j,pieces in enumerate(parts):
        ids,alpha = [np.concatenate(x) for x in zip(*pieces)]
        order = np.lexsort((ids,buckets[ids]))
        ids,alpha = ids[order].astype("<u4"),alpha[order].astype("<f4")
        key = "ray_"+str(j)
        streams[key+"_ids"]=ids
        streams[key+"_alpha"]=alpha
        streams[key+"_buckets"]=buckets[ids]
        logs.append(dict(display_pixel_center_xy=list(targets[j]),contributors=len(ids),
                         source_ids_sha256=hashlib.sha256(ids.tobytes()).hexdigest(),
                         alpha_sha256=hashlib.sha256(alpha.tobytes()).hexdigest(),
                         full=crossing(ids,alpha,False),fp16=crossing(ids,alpha,True),
                         old_primitive_alpha=float(alpha[ids==OLD].sum())))
    return logs,streams,dict(clipped_in=len(valid),full_min_depth=float(minimum),full_max_depth=float(maximum))


def write_result(check):
    old = json.loads((HERE.parent/"t136-bonsai-shot/STATIC.json").read_bytes())
    for name,digest in old["hashes"].items():
        if sha(LOCAL/name)!=digest:
            raise ValueError("T136 input hash changed")
    fields,rows = read_ply(LOCAL/"scene.ply")
    cameras,views = inspect_cameras(LOCAL/"cameras.json")
    if [c["id"] for c in views]!=old["camera_ids"]:
        raise ValueError("Source camera selection differs")
    cam=views[0]
    baselines=np.linalg.norm(np.array([c["position"] for c in cameras[1:]])-cam["position"],axis=1)
    median=float(np.median(baselines))
    if not median>0 or not np.isfinite(median):
        raise ValueError("Degenerate camera baseline")
    scale=4/median
    w,h=[2*v for v in old["diagnosis"]["quarter_view_size"]]
    rays=2*np.array(old["diagnosis"]["screen_points"])+.5
    physical=np.ceil(rays-.5).astype(int)
    samples=np.vstack((rays,physical)).tolist()
    logs,streams,depths=probe(rows,fields,cam,scale,(w,h),samples)
    ids=[l["full"]["id"] for l in logs[:2]]
    stable=all(l["full"]["id"]==l["fp16"]["id"] for l in logs[:2])
    passed=(all(i is not None for i in ids) and ids[0]!=ids[1] and stable)
    out=dict(schema="t139-native-style-bonsai-picking-v1",prior_status=old["status"],
             fit_sha256=old["hashes"]["scene.ply"],source_camera_ids=old["camera_ids"],
             source_rows=len(rows),median_camera_baseline=median,scale=scale,view_size=[w,h],
             depth_summary=depths,nominal=logs[:2],nearest_pixel_diagnostic=logs[2:],
             status="admitted_for_native_validation" if passed else "closed_no_stable_distinct_crossing")
    if passed:
        positions=rows[:,:3].astype(float)
        center=ordered_mean(positions)
        offset=np.array([0,.75,0])-(positions[ids[1]]-center)*scale
        params=json.loads((HERE.parent/"t42-firewoods-sequential-workflow/recipe.json").read_bytes())["params"]
        # Set __demo.P.sceneMax=2000000 BEFORE loadPLY. After loading research.reset validates other controls.
        params.pop("sceneMax")
        params.update(sceneScale=scale,sceneOffX=offset[0],sceneLift=offset[1],sceneOffZ=offset[2])
        picks=[]
        for name,idx,radius in (("A",ids[0],.12),("L",ids[1],.06),("F",ids[1],.12)):
            diff=positions-positions[idx]
            squared=np.einsum("ij,ij->i",diff,diff)*scale**2
            direct=np.flatnonzero(squared<=radius**2).astype("<u4")
            world=(positions[idx]-center)*scale+offset
            picks.append(dict(name=name,site=idx,radius=radius,world=world.tolist(),source=positions[idx].tolist(),
                              initial_geometric_count=len(direct),member_sha256=hashlib.sha256(direct.tobytes()).hexdigest()))
            if name=="F":
                shell=np.flatnonzero((squared>.12**2)&(squared<=.26**2)).astype("<u4")
                np.save(LOCAL/"t139-geometric-shell.npy",shell,allow_pickle=False)
        view_checks=[]
        for c in views:
            xyz=(positions[ids]-c["position"])@c["rotation"]
            uv=xyz[:,:2]/xyz[:,2,None]*[c["fx"]*w/c["width"],c["fy"]*h/c["height"]]+[(w-1)/2,(h-1)/2]
            normalized=xyz[:,2]*scale
            inside=(normalized>=.2)&(normalized<=50)&(uv[:,0]>=-.5)&(uv[:,0]<w-.5)&(uv[:,1]>=-.5)&(uv[:,1]<h-.5)
            view_checks.append(dict(id=c["id"],world_depth_A_B=normalized.tolist(),fitted_center_uv_A_B=uv.tolist(),
                                    centers_in_view_A_B=inside.tolist()))
        out["native_input"]=dict(width=w,height=h,decode_cap=2000000,material_count=len(rows),
                                 camera_ids=old["camera_ids"],source_center=center.tolist(),seed=73,dt=1/60,
                                 params=params,picks=picks,geometric_shell_count=len(shell),
                                 geometric_shell_sha256=hashlib.sha256(shell.tobytes()).hexdigest(),view_geometry=view_checks)
        (LOCAL/"t139-cameras.json").write_text(json.dumps(views),encoding="utf8")
    path=HERE/"RESULTS.json"
    archive=HERE/"contributions.npz"
    if check:
        if json.loads(path.read_bytes())!=out:
            raise ValueError("Output differs from published analysis")
        with np.load(archive,allow_pickle=False) as data:
            if set(data.files)!=set(streams) or any(not np.array_equal(data[k],v) for k,v in streams.items()):
                raise ValueError("Contributor evidence differs")
    else:
        if path.exists() or archive.exists():
            raise FileExistsError("Evidence already exists")
        np.savez_compressed(archive,**streams)
        path.write_text(json.dumps(out,indent=2,allow_nan=False)+"\n",encoding="utf8")
    return out


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    start=perf_counter()
    report=write_result(args.check)
    print(report["status"],[r["full"] for r in report["nominal"]],f"{perf_counter()-start:.3f} s")
