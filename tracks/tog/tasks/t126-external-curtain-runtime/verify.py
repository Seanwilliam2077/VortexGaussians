"""Independently verify complete and interrupted native receipts without starting the graphics engine."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE/"evidence/pair"
FRAMES=list(range(1,12))+[25,73,97,145]


def read(file):
    return json.loads(file.read_text(encoding="utf8"))


def require(ok,label):
    if not ok:raise ValueError(label)


def evaluate(key):
    data=read(ROOT/(key+".json"));samples=data["samples"]
    require([r["frame"] for r in samples]==FRAMES[:len(samples)],"sample sequence")
    file=ROOT/(key+"-sampled-values.npz")
    if samples:require(file.exists(),"expected numerical slices")
    verified=0
    if file.exists():
        with np.load(file,allow_pickle=False) as slices:
            for r in samples:
                for kind in ("gas","velocity","cloth"):
                    v=slices[f"frame-{r['frame']:03d}-{kind}"]
                    expected=r[kind];sh=expected["shape"]
                    target=(3,(sh[1]+7)//8,(sh[2]+7)//8,sh[3]) if kind!="cloth" else ((sh[0]+63)//64,sh[1])
                    require(v.shape==target and str(v.dtype)==expected["dtype"] and np.isfinite(v).all(),"sparse sample")
                    if kind=="cloth":require(v[:,0].min()>=r["cloth_T_K"][0] and v[:,0].max()<=r["cloth_T_K"][1],"cloth sample temperatures")
                    verified+=1
    out={"status":data["status"],"requested_frame":data.get("requested_frame"),"completed_native_frames_sampled":[r["frame"] for r in samples],
         "validated_sparse_arrays":verified,"sampled_burning_vertex_counts":[r["burning_vertices"] for r in samples]}
    if data["status"]=="complete":
        with np.load(ROOT/(key+"-frame.npz"),allow_pickle=False) as f:
            emit=f["emission"];composite=f["composite"];r=data["result"]
            for name,arr in (("emission",emit),("composite",composite)):
                require(hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()==r[name]["sha256"],"image hash")
            rgb=emit[...,:3].astype(np.float64)
            Y=rgb[...,0]*.2126+rgb[...,1]*.7152+rgb[...,2]*.0722
            crop=Y[45:90,80:240];count=int(np.count_nonzero(crop>=1.0))
            require(count==r["count"] and crop.size==r["region_pixels"]==7200 and (count>=72)==r["passes"],"image-based decision")
            require(np.isclose(crop.mean(),r["mean"],rtol=1e-15,atol=1e-14),"ROI luminance")
            out["bright_pixels"]=count;out["qualifies"]=bool(count>=72)
    return out


if __name__=="__main__":
    summary=read(ROOT/"SUMMARY.json");out={k:evaluate(k) for k in ("L","F") if (ROOT/(k+".json")).exists()}
    if summary["status"]=="complete":
        chosen=next((k for k in ("L","F") if out[k]["qualifies"]),"none");require(chosen==summary["choice"],"choice")
    elif summary["status"]=="time_limit":
        require(summary["limit_s"]==240 and summary["worker_s"][summary["arm"]]>=240,"wall bound")
    else:require(summary["status"]=="native_failure" and summary["exit"]!=0,"recorded failure")
    print(json.dumps({"summary":summary,"readbacks":out},indent=2))

