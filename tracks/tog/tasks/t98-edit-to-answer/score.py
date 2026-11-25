"""Verify all edit-to-answer trial records and compare query-level paired medians."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median

HERE=Path(__file__).resolve().parent
STAGES=("click_ms","shell_index_ms","fork_ms","compute_ms","restore_ms","total_browser_ms","delivered_ms")
def read(path):
    return json.loads(path.read_bytes())

def require(ok, what):
    if not ok: raise ValueError(what)

def evaluate(ref, capture, asset):
    data=read(capture)
    require(data["status"]=="validated", "Native capture status")
    methods=data["methods"]; rep_count=data["repeats"]
    require(len(methods)==len(set(methods)) and rep_count==len(methods), "Unbalanced schedule")
    targets={(q["arm"],q["horizon"]):q for q in ref["queries"] if q["asset"]==asset}
    require(len(data["queries"])==len(targets)==4, "Four requests fixed per asset")
    windows=[]
    for qi,q in enumerate(data["queries"]):
        target=targets.pop((q["arm"],q["horizon"]))
        require(target["first_frame"]==q["first_frame"] and target["ids"]==q["expected_ids"], "Source truth")
        rows={m:[] for m in methods}
        warming={}
        for n,t in enumerate(q["trials"]):
            rep,j=divmod(n,len(methods)); m=methods[(j+rep+qi)%len(methods)]
            require(t["method"]==m and t["rep"]==rep, "Method ordering")
            require(t["yes"]==bool(target["ids"]) and t["first_frame"]==target["first_frame"], "Outcome")
            require(t["witness"] in target["ids"] if t["yes"] else t["witness"] is None, "Witness")
            require(t["prefix_steps"]==target["observed_steps"], "Number of advanced steps")
            require(all(t[k]>=0 for k in STAGES) and t["delivered_ms"]>=t["total_browser_ms"]-1,
                    "Timing scope")
            if rep:
                rows[m].append(t)
            else:
                warming[m]=dict(delivered_ms=t["delivered_ms"], cache_build=t["cache_build"])
        w=dict(arm=q["arm"],horizon=q["horizon"],steps=target["observed_steps"],eligible=target["eligible"],
               first_frame=target["first_frame"],methods={},warmups=warming)
        for m,rs in rows.items():
            require(len(rs)==rep_count, "Missing repetition")
            a={key:median([t[key] for t in rs]) for key in STAGES}
            a["delivery_range_ms"]=[min(t["delivered_ms"] for t in rs),max(t["delivered_ms"] for t in rs)]
            a["witness_ids"]=sorted({t["witness"] for t in rs if t["witness"] is not None})
            a["plan_active"]=rs[0]["plan_active"]
            require(all(t["plan_active"]==a["plan_active"] for t in rs),"Branch differs")
            if rs[0]["cache_build"] is not None:
                a["cache_build_ms_median"]=median(t["cache_build"]["ms"] for t in rs)
                a["cache_bytes_built_max"]=max(t["cache_build"]["bytes"] for t in rs)
            w["methods"][m]=a
        windows.append(w)
    require(not targets,"Duplicates")
    summary={}
    for ref_method in ("regional","rank-only","cold-cache","asset-cache"):
        summary[ref_method]={m:median(w["methods"][m]["delivered_ms"]/w["methods"][ref_method]["delivered_ms"]
                                      for w in windows) for m in methods}
    return dict(asset=asset, windows=windows, median_paired_delivery_ratios=summary,
                capture_sha256=hashlib.sha256(capture.read_bytes()).hexdigest())

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset",choices=("firewoods","dead-tree"))
    parser.add_argument("--capture-dir",type=Path,help="Directory containing the captured CAPTURE.json")
    args=parser.parse_args()
    dest=args.capture_dir or HERE/"evidence"/args.asset
    result=evaluate(read(HERE/"REFERENCE.json"),dest/"CAPTURE.json",args.asset)
    (dest/"SCORE.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    print(json.dumps(result["median_paired_delivery_ratios"],indent=2))
