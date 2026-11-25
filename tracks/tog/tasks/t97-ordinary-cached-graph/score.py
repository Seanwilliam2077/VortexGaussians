"""Reconstruct paired caller costs and separately account for graph-cache construction."""
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
METHODS = ("rank-only","plain","cold-cache","asset-cache")


def audit(asset):
    c=json.loads((HERE/"evidence"/asset/"CAPTURE.json").read_text())
    if c["status"]!="validated" or c["methods"]!=list(METHODS) or c["repeats"]!=4:
        raise ValueError("Wrong or incomplete profile")
    windows=[]
    builds={m:{"new_edges_bytes":0,"rows":0,"build_ms":0,"invocations":0} for m in METHODS[1:]}
    for q in c["queries"]:
        result={key:q[key] for key in ("arm","cut","horizon","first_frame")}
        result["delivered"]={}
        for m in METHODS:
            values=[]
            for trial in (s for s in q["trials"] if s["method"]==m):
                if trial["first_frame"]!=q["first_frame"] or (trial["yes"] and trial["witness"] not in q["expected_ids"]):
                    raise ValueError("Wrong native first event")
                if m in builds:
                    item=trial["cache_build"]
                    builds[m]["new_edges_bytes"]+=item["bytes"]
                    builds[m]["rows"]+=item["entries"]
                    builds[m]["build_ms"]+=item["ms"]
                    builds[m]["invocations"]+=1
                if trial["rep"]>0:
                    values.append(trial["delivered_ms"])
            if len(values)!=4: raise ValueError("Missing timed replicate")
            result["delivered"][m]=median(values)
        windows.append(result)
    for arm in ("AB","BA"):
        if c["arms"][arm]["verified_frames"]!=360 or [len(v) for v in c["arms"][arm]["ordinary_state_audits"].values()] != [8,8,8]:
            raise ValueError("Incomplete native state audit")
    groups={"all":windows}
    groups.update({f"H{h}":[r for r in windows if r["horizon"]==h] for h in (1,4,8)})
    groups.update({key:[r for r in windows if (r["first_frame"] is not None)==(key=="yes")] for key in ("yes","no")})
    summary={}
    for label,group in groups.items():
        summary[label]={m:{"delivered_ms":median(r["delivered"][m] for r in group),
                           "paired_vs_rank":median(r["delivered"][m]/r["delivered"]["rank-only"] for r in group)}
                        for m in METHODS}
    return {"summary":summary,"build_ledger_including_warmup":builds,"windows":windows}

if __name__=="__main__":
    data={asset:audit(asset) for asset in ("firewoods","dead-tree")}
    (HERE/"SCORE.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf8")
    for asset,d in data.items(): print(asset, d["summary"]["all"], d["build_ledger_including_warmup"]["asset-cache"])
