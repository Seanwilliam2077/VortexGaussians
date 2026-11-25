"""Measure the original calibrated foreground, retaining native site IDs under the solver similarity."""
import importlib.util
import gzip
import hashlib
import json
import math
from pathlib import Path
from time import perf_counter
import numpy as np

HERE=Path(__file__).resolve().parent
TASKS=HERE.parent
def load(path):
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix==".gz" else raw)
def write(path,value):
    raw=(json.dumps(value,separators=(",",":"),allow_nan=False)+"\n").encode()
    if path.exists():
        assert load(path)==value
    else:
        path.write_bytes(gzip.compress(raw,mtime=0) if path.suffix==".gz" else raw)
def main():
    spec=importlib.util.spec_from_file_location("project_reference",TASKS/"t107-visible-burn-progression"/"measure.py")
    matte=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(matte)
    stage=TASKS/"t101-playground-holdout"
    cfg=load(stage/"recipe.json")
    geom=stage/"local"/"scene.ply"
    raw=geom.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==cfg["asset_sha256"]
    head=raw.index(b"end_header\n")+11
    columns=[l for l in raw[:head].decode().splitlines() if l.startswith("property float ")]
    xyz=np.frombuffer(raw[head:],dtype="<f4").reshape(cfg["material_count"],len(columns))[:,:3].astype(float)
    a,b=cfg["picks"]
    ds=np.sum((xyz-xyz[b["site"]])**2,axis=1)
    lf=[]
    for name,rad in (("L",.06),("F",.12)):
        ids=np.flatnonzero(ds<=rad**2).tolist()
        lf.append({**b,"name":name,"radius":rad,"initial_geometric_neighbors":ids})
    assert lf[1]["initial_geometric_neighbors"]==b["initial_geometric_neighbors"]
    shell=np.flatnonzero((ds>.12**2)&(ds<=(.12+.14)**2)).tolist()
    assert shell==load(stage/"shell-ids.json.gz")["B"]
    assert not set(shell)&set(lf[1]["initial_geometric_neighbors"])
    cfg.update(schema="t111-common-parent-playground-v1",seed=59,picks=[a,*lf])
    write(HERE/"recipe.json",cfg)
    write(HERE/"shell.json.gz",shell)
    cp=HERE/"local"/"cameras.json"
    assert hashlib.sha256(cp.read_bytes()).hexdigest()=="f2ad2236ddfaccac88e8b83cbe0c17a9f11f92a2071f3a8a447f79c27e0722d2"
    cams=sorted(load(cp),key=lambda x:x["id"])
    src=stage/"local"/"foreground.ply"
    pos,cov,opacity=matte.splats(src,cfg["original_sha256"],cfg["material_count"])
    np.testing.assert_allclose((pos-np.array(cfg["center_before"]))*cfg["scale"],xyz,atol=6e-8,rtol=0)
    meta={}; costs={}
    for cam in (cams[0],cams[len(cams)//2]):
        cid=cam["id"];start=perf_counter()
        proj=matte.projection(pos,cov,cam)
        weights,img,_,tested=matte.raster(proj,opacity,{},{},[a["site"],b["site"]])
        costs[str(cid)]=perf_counter()-start
        dest=HERE/f"weights-{cid}.json.gz"
        write(dest,dict(camera_id=cid,asset_count=len(pos),eligible_weights=[[i,float(weights[i])] for i in shell]))
        meta[str(cid)]=dict(sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),shell_sites=len(shell),
                    stored_pairs=len(shell),shell_micro_pixels=sum(math.floor(weights[i]*1e6+.5) for i in shell),
                    projected_foreground_pixels=float(img.sum()),checked_pixels=tested, camera=cam)
    write(HERE/"STATIC.json",dict(asset_sha256=cfg["asset_sha256"],original_sha256=cfg["original_sha256"],
              shell_size=len(shell),brush_counts={x["name"]:len(x["initial_geometric_neighbors"]) for x in cfg["picks"]},
              cameras=meta))
    if not (HERE/"projection-cost.json").exists():
        write(HERE/"projection-cost.json",costs)
    print(len(pos),len(shell), {c:(data["shell_micro_pixels"]/1e6,costs[c]) for c,data in meta.items()})
if __name__=="__main__":
    main()
