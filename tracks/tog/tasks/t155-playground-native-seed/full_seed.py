"""Compute native Playground seed masks with all Gaussian geometry on CPU."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile

import numpy as np
from scipy import ndimage as ndi
import torch
import torch.nn.functional as F

HERE = Path(__file__).resolve().parent
T152 = HERE.parent/"t152-playground-brush-clearance"
spec = importlib.util.spec_from_file_location("qualification", T152/"qualify.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
SCENE_SOURCE = "584ceb2a5cc8fd46af918af803a4de8ffcd4f0d74b717d83e7810a3925296979"


def native_functions(source):
    code=(source/"rainy_gs/scene.py").read_bytes()
    if hashlib.sha256(code).hexdigest()!=SCENE_SOURCE:
        raise ValueError("Original scene loader identity mismatch")
    mod=ast.parse(code)
    quaternion=next(n for n in mod.body if isinstance(n,ast.FunctionDef) and n.name=="quaternion_matrix")
    scene=next(n for n in mod.body if isinstance(n,ast.ClassDef) and n.name=="Scene")
    ground=next(n for n in scene.body if isinstance(n,ast.FunctionDef) and n.name=="fit_ground")
    scope={"torch":torch,"F":F}
    exec(compile(ast.Module(body=[quaternion,ground],type_ignores=[]),"official-scene.py","exec"),scope)
    return scope["quaternion_matrix"],scope["fit_ground"]


def ply(path):
    with path.open("rb") as handle:
        lines=[]
        while len(lines)<256:
            line=handle.readline(1024).decode("ascii").strip()
            lines.append(line)
            if line=="end_header": break
        offset=handle.tell()
    assert lines[-1]=="end_header" and "format binary_little_endian 1.0" in lines
    n=int(next(s for s in lines if s.startswith("element vertex")).split()[-1])
    props=[line.split()[2] for line in lines if line.startswith("property float ")]
    dt=np.dtype([(p,"<f4") for p in props])
    assert n==1268409 and path.stat().st_size==offset+n*dt.itemsize
    return np.memmap(path,dtype=dt,mode="r",offset=offset,shape=(n,))


def calculate(model, inputs, source, foreground):
    torch.set_num_threads(3)
    loader_record=json.loads((HERE/"ACQUISITION.json").read_bytes())
    assert loader_record["status"]=="complete"
    with model.open("rb") as f:
        assert hashlib.file_digest(f,"sha256").hexdigest()==loader_record["sha256"]
    acquisition=json.loads((T152/"ACQUISITION.json").read_bytes())
    for filename, record in acquisition["members"].items():
        assert m.digest((inputs/filename).read_bytes())==record["sha256"]
    qmatrix,fit_ground=native_functions(source)
    vertices=ply(model)
    def tensor(keys):
        return torch.from_numpy(np.stack([vertices[k] for k in keys],axis=-1).copy())
    xyz_t=tensor(["x","y","z"]); xyz=xyz_t.numpy()
    scales=tensor([f"scale_{i}" for i in range(3)]).exp().clamp_min(1e-7)
    opacity=tensor(["opacity"])[:,0].sigmoid()
    q=F.normalize(tensor([f"rot_{i}" for i in range(4)]),dim=-1)
    R=qmatrix(q)
    normals=R.gather(2,scales.argmin(-1)[:,None,None].expand(-1,3,1))[:,:,0]
    normals*=torch.where(normals[:,2:3]<0,-1.0,1.0)
    state=SimpleNamespace(config={},means=xyz_t,normals=normals,opacity=opacity)
    ground=fit_ground(state).numpy()
    assert np.isfinite(ground).all()
    # The crop file is the ordered source-model subset, verified directly here.
    with zipfile.ZipFile(inputs/"mask_pts_in_grids.pth") as z:
        mask=np.frombuffer(z.read("mask_pts_in_grids/data/0"),dtype=np.bool_)
    with zipfile.ZipFile(inputs/"indices_pts_in_grids.pth") as z:
        ids=np.frombuffer(z.read("indices_pts_in_grids/data/0"),dtype="<i8").reshape(-1,3)
    cropped=m.load_foreground(foreground)
    fgxyz=np.stack([cropped[c] for c in ("x","y","z")],axis=-1)
    assert len(mask)==len(vertices) and np.array_equal(xyz[mask],fgxyz)
    frac=(xyz[mask]-m.LOWER)/((m.UPPER-m.LOWER)/256)
    max_error=float(np.maximum(ids-frac,frac-ids-1).max())
    assert max_error<=0.001
    material=np.load(inputs/"material_grid.npy",allow_pickle=False,mmap_mode="r")
    labels=np.argwhere(material==1)
    wood=ndi.binary_fill_holes(ndi.binary_closing(m.grid(m.LOWER+(labels+0.5)*(m.UPPER-m.LOWER)/256),iterations=1))
    prior=json.loads((T152/"GEOMETRY.json").read_bytes())
    assert m.digest(wood.astype("u1").tobytes())==prior["wood_grid_u8_c_sha256"]

    bounds=((xyz>[-1.3,-1.1,-0.55])&(xyz<[1.4,1.65,0.5])).all(-1)
    sc=scales.numpy().max(axis=1); op=opacity.numpy()
    coll=bounds&(op>0.6)&(sc<0.08)
    obstacles=m.grid(xyz[coll])
    coordinate=np.meshgrid(*[m.ORIGIN[d]+(np.arange(n)+0.5)*m.DX for d,n in enumerate(m.SHAPE)],indexing="ij")
    floor=coordinate[0][:,:,0]*ground[0]+coordinate[1][:,:,0]*ground[1]+ground[2]
    solid=wood|obstacles|(coordinate[2]<floor[:,:,None])
    w=np.argwhere(wood)
    centers=m.ORIGIN+(w+0.5)*m.DX
    center=centers[np.argmin(((centers-m.TARGET)**2).sum(axis=1))]
    warp_centers=m.ORIGIN.astype("f")+(w.astype("f")+np.float32(0.5))*np.float32(m.DX)
    paint=w[np.linalg.norm(warp_centers-center.astype("f"),axis=1)<=np.float32(1.1*m.DX)]
    assert paint.tolist()==prior["changed_wood_ijk"]
    brush=np.zeros(m.SHAPE,bool);brush[tuple(paint.T)]=True
    def native_seed(hot):
        temp=np.where(wood,np.float32(310),np.float32(0))
        temp[brush]=np.float32(hot)
        hottest=ndi.maximum_filter(temp,footprint=m.CROSS,mode="constant",cval=0)
        return np.where((~solid)&(hottest>450),np.minimum(hottest,np.float32(750)),np.float32(293.15))
    a,b=native_seed(620),native_seed(790)
    changed=np.argwhere(a!=b)
    possible=np.array(prior["candidate_seed_sites_ijk"],dtype=int)
    actually_open=possible[~solid[tuple(possible.T)]]
    assert np.array_equal(changed,actually_open)
    candidates_globally=bounds&((abs(op-0.6)<2e-6)|(abs(sc-0.08)<2e-6))
    near_collision=m.grid(xyz[candidates_globally])
    uncertain_points=possible[near_collision[tuple(possible.T)]]
    if len(uncertain_points):
        closed_strict=m.grid(xyz[bounds&(op>0.600002)&(sc<0.079998)])
        assert np.all(closed_strict[tuple(uncertain_points.T)]),"Threshold rounding affects a candidate site"
    floor_margins=coordinate[2][tuple(possible.T)]-floor[possible[:,0],possible[:,1]]
    assert min(abs(floor_margins))>0.01,"Floor fit too near candidate seed sites"
    exposed=wood&ndi.binary_dilation(~solid,structure=m.CROSS)
    front=brush.copy();D=None
    for depth in range(int(wood.sum())):
        if np.any(front&exposed):
            D=depth;break
        nxt=ndi.binary_dilation(front,structure=m.CROSS,mask=wood)
        if np.array_equal(nxt,front):break
        front=nxt
    return dict(config="unmodified base Playground, dry controls, one registered region in each arm",
                registered_rows=int(mask.sum()),scene_rows=len(vertices),source_registration_max_error=max_error,
                selected_centers_match_raw_foreground=True, ground_plane=ground.tolist(),ground_fit_source_sha256=SCENE_SOURCE,
                wood_hash=prior["wood_grid_u8_c_sha256"],collision_points=int(coll.sum()),
                collision_cells=int(obstacles.sum()),solid_cells=int(solid.sum()),solid_hash=m.digest(solid.astype("u1").tobytes()),
                changed_wood_ijk=paint.tolist(),graph_distance=D,possible_seed_ijk=possible.tolist(),
                open_seed_ijk=actually_open.tolist(),floor_clearance_m=floor_margins.tolist(),
                collision_threshold_ambiguous_sites=uncertain_points.tolist(),different_gas_cells=len(changed),
                gas_keys=[m.digest(field.astype("<f4").tobytes()) for field in (a,b)],
                light_changed_K=a[tuple(changed.T)].tolist(),full_changed_K=b[tuple(changed.T)].tolist(),
                reason="different_initial_gas" if len(changed) else "equal_seed",native_dynamics_run=False)


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ("model","mapping","source","foreground"):ap.add_argument(k,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    x=calculate(args.model,args.mapping,args.source,args.foreground)
    args.out.write_text(json.dumps(x,indent=2,allow_nan=False)+"\n",encoding="utf8")
    print(x["different_gas_cells"],x["graph_distance"],x["reason"])
