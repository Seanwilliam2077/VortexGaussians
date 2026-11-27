"""Describe magnitudes in the actual first four archived ordinary-pair inputs."""
import argparse
import json
from pathlib import Path
import numpy as np
from pack_fields import desc, witnesses

HERE=Path(__file__).resolve().parent
FIELDS=("cloth.X","cloth.V","gas.vel","gas.scal","gas.scal_fine")


def stats(a,b,channels):
    """Accumulate in double precision, a slab at a time for the 3-D fine field."""
    if a.ndim!=b.ndim or a.shape!=b.shape or a.dtype!=b.dtype or a.dtype.kind!="f":
        raise ValueError("Unmatched floating-point inputs")
    a,b=a[...,:channels],b[...,:channels]
    if a.ndim==2:
        a,b=a[None,...],b[None,...]
    sq=np.zeros(channels,dtype=float)
    maximum=np.zeros_like(sq)
    changed=np.zeros(channels,dtype=np.int64)
    count=0
    for x,y in zip(a,b):
        delta=(x.astype(np.float64)-y.astype(np.float64)).reshape(-1,channels)
        maximum=np.maximum(maximum,np.max(np.abs(delta),axis=0))
        changed+=np.count_nonzero(delta,axis=0)
        sq+=np.sum(delta*delta,axis=0)
        count+=len(delta)
    return dict(samples=count,changed=changed.tolist(),max_abs=maximum.tolist(),
                rms=np.sqrt(sq/count).tolist())


def describe(folder,raw=False):
    inputs=[]
    for arm in ("ordinary","stiffer"):
        rows=[json.loads(v) for v in (folder/f"{arm}-steps.ndjson").read_bytes().splitlines()]
        inputs.append([r for r in rows if r["kind"]=="input"])
    result=[]
    for l,r in zip(inputs[0][:4],inputs[1][:4]):
        coord={k:l[k] for k in ("index","frame","substep")}
        if any(v!=r[k] for k,v in coord.items()) or l["dt"]!=r["dt"]:
            continue
        i=coord["index"]
        obs={}
        if raw:
            with np.load(folder/f"ordinary-{i:03d}-fields.npz",allow_pickle=False) as fa, \
                 np.load(folder/f"stiffer-{i:03d}-fields.npz",allow_pickle=False) as fb:
                for key in FIELDS:
                    if key in fa.files:
                        a,b=fa[key],fb[key]
                        obs[key]=stats(a,b,3 if key in ("cloth.X","cloth.V","gas.vel") else a.shape[-1])
        else:
            sections=json.loads((folder/"early-index.json").read_bytes())[str(i)]["fields"]
            with np.load(folder/f"early-{i:03d}.npz",allow_pickle=False) as archive:
                for key in FIELDS:
                    if key not in sections:
                        continue
                    mode=sections[key]["storage"]
                    if mode=="words":
                        # Omitted background words are identical across arms and contribute zero to every delta.
                        field=desc(l,key)
                        a=np.zeros(field["shape"],field["dtype"])
                        b=np.zeros_like(a)
                        idx,x,y=witnesses(archive,key)
                        a.ravel()[idx],b.ravel()[idx]=x,y
                    else:
                        a=archive["ordinary."+key]
                        b=a if mode=="shared" else archive["stiffer."+key]
                    obs[key]=stats(a,b,3 if key in ("cloth.X","cloth.V","gas.vel") else a.shape[-1])
        result.append(dict(**coord,fields=obs))
    return dict(meaning="First four synchronized pre-gas-step states; components are in native field units",inputs=result)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder",type=Path,nargs="?",default=HERE/"evidence")
    parser.add_argument("--output",type=Path)
    parser.add_argument("--raw",action="store_true",help="Read full locally generated snapshots instead of paired witnesses.")
    args=parser.parse_args()
    txt=json.dumps(describe(args.folder,args.raw),indent=2,allow_nan=False)+"\n"
    if args.output:
        args.output.write_text(txt,encoding="utf8")
    print(txt,end="")
