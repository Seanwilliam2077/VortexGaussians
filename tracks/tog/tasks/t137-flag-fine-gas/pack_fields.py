"""Keep complete early cloth and scalar fields plus paired words from the large common flow arrays."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from flag import HERE
from observe import arrays_and_values, digest, require

def inputs(folder,arm):
    rows=[json.loads(line) for line in (folder/f"{arm}-steps.ndjson").read_bytes().splitlines()]
    return [row for row in rows if row["kind"]=="input"][:4]


def desc(row,key):
    group,field=key.split(".")
    return row[group][field]


def pack(folder):
    pairs=zip(inputs(folder,"ordinary"),inputs(folder,"stiffer"))
    index={}
    for l,r in pairs:
        i=l["index"]
        require(i==r["index"],"Missing paired early input")
        payload={}
        sections={}
        with np.load(folder/f"ordinary-{i:03d}-fields.npz",allow_pickle=False) as fa, \
             np.load(folder/f"stiffer-{i:03d}-fields.npz",allow_pickle=False) as fb:
            require(set(fa.files)==set(fb.files),"Unmatched fields")
            for key in fa.files:
                a,b=fa[key],fb[key]
                la,lb=desc(l,key),desc(r,key)
                require(arrays_and_values({"a":a,"b":b})=={"a":la,"b":lb},"Raw arrays differ from native ledger")
                if key not in ("gas.vel","gas.p"):
                    payload["ordinary."+key]=a
                    if la!=lb:
                        payload["stiffer."+key]=b
                    sections[key]={"storage":"both" if la!=lb else "shared"}
                    continue
                require(a.shape==b.shape and a.dtype==b.dtype,"Incompatible early layout")
                words=np.dtype(f"u{a.dtype.itemsize}")
                idx=np.flatnonzero(a.view(words).reshape(-1)!=b.view(words).reshape(-1))
                count=len(idx)
                # Uniform equal/unequal samples preserve background values too.
                probes=np.unique(np.linspace(0,a.size-1,1024,dtype=int))
                indices=np.union1d(idx,probes).astype(np.uint32)
                payload["index_increments."+key]=np.diff(indices,prepend=np.uint32(0))
                original=a.reshape(-1)[indices]
                edited=b.reshape(-1)[indices]
                payload["ordinary."+key]=original
                payload["xor."+key]=np.bitwise_xor(original.view(words),edited.view(words))
                sections[key]=dict(storage="words", changed_words=count, all_changed_words_retained=True)
        target=folder/f"early-{i:03d}.npz"
        np.savez_compressed(target,**payload)
        index[str(i)]={"fields":sections,"file_sha256":digest(target.read_bytes())}
    (folder/"early-index.json").write_text(json.dumps(index,indent=2)+"\n",encoding="utf8")


def witnesses(archive,key):
    idx=np.cumsum(archive["index_increments."+key],dtype=np.uint32)
    a=archive["ordinary."+key]
    words=a.view(f"u{a.itemsize}")
    return idx,a,np.bitwise_xor(words,archive["xor."+key]).view(a.dtype)


def check_public(folder,arm,row):
    i=row["index"]
    index=json.loads((folder/"early-index.json").read_bytes())[str(i)]
    p=folder/f"early-{i:03d}.npz"
    require(index["file_sha256"]==digest(p.read_bytes()),"Corrupt early witness archive")
    expected={f"{group}.{k}" for group in ("gas","cloth") for k,s in row[group].items() if isinstance(s,dict)}
    require(expected==set(index["fields"]),"Missing published fields")
    with np.load(p,allow_pickle=False) as archive:
        for key,meta in index["fields"].items():
            state=desc(row,key)
            if meta["storage"] in ("both","shared"):
                label="ordinary" if meta["storage"]=="shared" else arm
                array=archive[label+"."+key]
                require(arrays_and_values({"v":array})["v"]==state,"Unverified original array")
            else:
                idx,a,b=witnesses(archive,key)
                require(len(a)==len(idx)==len(b) and a.dtype==b.dtype==np.dtype(state["dtype"]) and
                        idx.dtype==np.uint32 and len(idx)>0 and np.all(idx[1:]>idx[:-1]) and
                        idx[-1]<math.prod(state["shape"]), "Invalid native word witnesses")
                differing=np.count_nonzero(a.view(f"u{a.itemsize}")!=b.view(f"u{b.itemsize}"))
                require(meta["all_changed_words_retained"] and differing==meta["changed_words"],"Witness word count")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder",type=Path,nargs="?",default=HERE/"evidence")
    pack(parser.parse_args().folder)
