"""Apply the registered global similarity and choose both brushes from geometry only."""
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
LOCAL=HERE/"local"
ORIGINAL="3f27f88a647d26fa1b1fd6624eb44ba6e6f0e9c2574ab51b5d3e806aa8fee749"


def publish(name, value):
    out=HERE/name
    data=(json.dumps(value,indent=None,separators=(",",":"),allow_nan=False)+"\n").encode()
    if out.exists():
        stored=out.read_bytes()
        if (gzip.decompress(stored) if name.endswith(".gz") else stored)!=data:
            raise ValueError(f"Frozen asset record differs: {name}")
    else:
        out.write_bytes(gzip.compress(data,compresslevel=6,mtime=0) if name.endswith(".gz") else data)


def main():
    raw=(LOCAL/"foreground.ply").read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL: raise ValueError("Source foreground hash")
    offset=raw.index(b"end_header\n")+len(b"end_header\n")
    lines=raw[:offset].decode("ascii").splitlines()
    if "format binary_little_endian 1.0" not in lines: raise ValueError("PLY endian")
    fields=[s.split()[-1] for s in lines if s.startswith("property float ")]
    n=int(next(s for s in lines if s.startswith("element vertex ")).split()[2])
    rows=np.frombuffer(raw[offset:],dtype="<f4").reshape(n,len(fields)).copy()
    if n!=80023 or fields[:3]!=["x","y","z"] or not np.isfinite(rows).all(): raise ValueError("Unexpected PLY schema")
    positions=rows[:,:3].astype("float64")
    low,high=positions.min(axis=0),positions.max(axis=0)
    scale=1.6/float(np.max(high-low))
    rows[:,:3]=(positions-(low+high)/2)*scale
    for k in range(3):
        c=fields.index(f"scale_{k}")
        rows[:,c]=rows[:,c].astype("float64")+math.log(scale)
    out=raw[:offset]+rows.tobytes()
    (LOCAL/"scene.ply").write_bytes(out)
    pos=rows[:,:3].astype("float64")
    lo,hi=pos.min(axis=0),pos.max(axis=0)
    # Match the demo's ordered binary64 position sum exactly.
    center=[sum(pos[:,i].tolist(),0.0)/n for i in range(3)]
    parent=json.loads((HERE.parent/"t42-firewoods-sequential-workflow/recipe.json").read_text())
    cfg={k:parent[k] for k in ("dt","params","camera","width","height","steps_per_interval","intervals")}
    cfg.update(schema="t101-playground-registered-input-v1",seed=37,source_center=center,material_count=n,
               original_sha256=ORIGINAL,asset_sha256=hashlib.sha256(out).hexdigest(),
               extent_before=(high-low).tolist(),center_before=((low+high)/2).tolist(),scale=scale,picks=[])
    shells={}
    for name,fraction in (("A",.25),("B",.75)):
        target=lo+(hi-lo)*np.array([fraction,.90,.5])
        j=int(np.argmin(np.sum((pos-target)**2,axis=1)))
        squared=np.sum((pos-pos[j])**2,axis=1)
        direct=np.flatnonzero(squared<=.12**2).tolist()
        shells[name]=np.flatnonzero((squared>.12**2)&(squared<=(.12+.14)**2)).tolist()
        world=(pos[j]-center).tolist()
        world[1]+=cfg["params"]["sceneLift"]
        cfg["picks"].append(dict(name=name,site=j,world=world,radius=.12,
                                 initial_geometric_neighbors=direct,shell_size=len(shells[name])))
    publish("recipe.json",cfg)
    publish("shell-ids.json.gz",shells)
    print(n,cfg["asset_sha256"],[(p["site"],len(p["initial_geometric_neighbors"]),p["shell_size"]) for p in cfg["picks"]])

if __name__=="__main__":
    main()
