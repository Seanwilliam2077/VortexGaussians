"""Check native numerical archives, identify physical differences, and score the registered controls offline."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent


def require(condition, error):
    if not condition:
        raise ValueError(error)


def describe_array(array):
    a=np.ascontiguousarray(array)
    return {"dtype":str(a.dtype),"shape":list(a.shape),"sha256":hashlib.sha256(a.tobytes()).hexdigest()}


def array_specs(value, path):
    if not isinstance(value,dict):
        return {}
    if set(value)=={"dtype","shape","sha256"}:
        return {path:value}
    expected={}
    for k,v in value.items():
        expected.update(array_specs(v,path+"."+k))
    return expected


def check_arrays(path, record, key="state"):
    expected=array_specs(record,key)
    with np.load(path,allow_pickle=False) as arrays:
        require(set(arrays.files)==set(expected),f"Wrong archive inventory: {path.name}")
        for name,spec in expected.items():
            require(describe_array(arrays[name])==spec,f"Array does not match receipt: {path.name}/{name}")
            require(np.isfinite(arrays[name]).all(),f"Nonfinite values: {path.name}/{name}")
    return len(expected)


def differences(a,b,key=""):
    if a==b:
        return []
    if isinstance(a,dict) and isinstance(b,dict) and set(a)!= {"dtype","shape","sha256"}:
        rows=[]
        for field in sorted(a.keys()|b.keys()):
            path=f"{key}.{field}" if key else field
            if field not in a or field not in b:
                rows.append(path)
            else:
                rows.extend(differences(a[field],b[field],path))
        return rows
    return [key]


def compare_words(a,b,channels):
    require(a.dtype==np.uint32 and a.shape==b.shape and b.dtype==np.uint32,"Incompatible feedback arrays")
    a,b=a.reshape(-1,channels),b.reshape(-1,channels)
    return {"words":a.size,"nonzero_reference_words":int(np.count_nonzero(a)),
            "nonidentical_words":int(np.count_nonzero(a!=b)),
            "nonidentical_per_channel":[int(v) for v in np.count_nonzero(a!=b,axis=0)]}


def verify(directory):
    read=lambda name:json.loads((directory/(name+".json")).read_bytes())
    workers=read("workers")
    require(set(workers)=={"reference","ordinary","supplemented"}, "Three worker records required")
    require(len({v["pid"] for v in workers.values()})==3,"Expected independent processes")
    records={name:read(name) for name in workers}
    ref=records["reference"]
    require(ref["status"]=="complete","Reference missing")
    counts={}
    summary={}
    frame_pairs={"native_parent":"parent","successor":"successor","corrected_parent":"corrected-parent"}
    for method,r in records.items():
        require(r["pid"]==workers[method]["pid"] and r["arm"]==method,"Worker identity mismatch")
        if r["status"]=="complete":
            require(workers[method]["returncode"]==0 and not workers[method]["timeout"],"Completed process did not exit cleanly")
            require(r["native_parent"]["frame"]==1 and r["successor"]["frame"]==2,"Unexpected frame numbers")
        require(r["scene"]==ref["scene"] and r["revision"]==ref["revision"] and r["adapter"]==ref["adapter"],
                "Scene/source/device mismatch")
        if "native_checkpoint" in r:
            require(r["native_checkpoint"]==ref["native_checkpoint"],"Checkpoint content differs across methods")
        counts[method]=0
        results={"status":r["status"]}
        for field,suffix in frame_pairs.items():
            if field not in r:
                continue
            counts[method]+=check_arrays(directory/(method+"-"+suffix+".npz"),r[field])
            target=ref["successor" if field=="successor" else "native_parent"]
            results[field+"_mismatches"]=differences(target,r[field])
        if r["status"]!="complete":
            results.update(last_phase=r["last_phase"],error=r.get("reason","no completed outcome"))
        summary[method]=results
    side=records["supplemented"]
    archive=lambda name:np.load(directory/(name+".npz"),allow_pickle=False)
    with archive("reference-parent") as arr:
        parent=arr["state.feedback.grid"]
    with archive("reference-successor") as arr:
        successor=arr["state.feedback.grid"]
    sidecar=ref["supplement"]["metadata"]
    require(sidecar["frame"]==1 and sidecar["scene"]==ref["scene"] and sidecar["channels"]==13,"Wrong supplement metadata")
    require(sidecar["sha256"]==describe_array(parent)["sha256"] and sidecar["bytes"]==parent.nbytes
            and parent.size==int(np.prod(sidecar["feedback"]["dims"]))*13,"Wrong saved supplement")
    require(ref["native_parent"]["frame"]==1 and ref["successor"]["frame"]==2,"Wrong frame numbers")
    summary["reference_grid_change"]=compare_words(parent,successor,13)
    summary["rebuild_status"]=side.get("rebuild_status","not reached")
    if "rebuild_error" in side:
        summary["rebuild_error"]=side["rebuild_error"]
    if side.get("rebuild_status")=="complete":
        counts["supplemented"]+=check_arrays(directory/"rebuild-cold-parent.npz",side["rebuild_native_parent"])
        require(side["rebuild_native_parent"]==side["native_parent"],"Aux control must start at equivalent native restore")
        counts["supplemented"]+=check_arrays(directory/"rebuilt-feedback.npz",side["rebuilt_feedback"],"feedback")
        with archive("rebuilt-feedback") as arr:
            summary["rebuild_grid_difference"]=compare_words(parent,arr["feedback.grid"],13)
        summary["rebuild_feedback_mismatches"]=differences(ref["native_parent"]["feedback"],side["rebuilt_feedback"])
    return {"verified_arrays":counts,"feedback_bytes":parent.nbytes,"native_checkpoint":ref["native_checkpoint"],
            "workers":workers,"comparisons":summary}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence",type=Path,default=HERE/"evidence")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    summary=verify(args.evidence)
    result=json.dumps(summary,indent=2,allow_nan=False)+"\n"
    if args.output:
        args.output.write_text(result,encoding="utf8")
    print(result)
