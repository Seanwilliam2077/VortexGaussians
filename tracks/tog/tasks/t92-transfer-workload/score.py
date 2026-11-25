"""Verify portable native traces, checkpoint labels and the fixed regional truth."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)

def require(condition, message):
    if not condition:
        raise ValueError(message)

def evaluate(out):
    report = read(out/"capture-report.json")
    require(report["status"] == "validated", "Capture not validated")
    cfg = read(HERE/"recipe.json")
    shells = read(HERE/"shell-ids.json.gz")
    for record in report["files"]:
        b = (out/record["name"]).read_bytes()
        require(hashlib.sha256(b).hexdigest()==record["sha256"], record["name"]+" identity")
        require(hashlib.sha256(gzip.decompress(b)).hexdigest()==record["decoded_sha256"], "decoded identity")
    rows = []
    for arm, shot in report["shots"].items():
        frames = read(out/f"{arm}-trace.json.gz")
        require([r["frame"] for r in frames]==list(range(1,361)), "discontinuous native trace")
        shell = set(shells[arm[1]])
        require(len(shell) == next(p["shell_size"] for p in cfg["picks"] if p["name"]==arm[1]), "shell count")
        seen = set(shot["initial"]["ids"])
        retired = 0
        for i, r in enumerate(frames):
            born = set(r["new_ids"])
            require(len(born)==len(r["new_ids"]) and born.isdisjoint(seen), "duplicate material event")
            seen.update(born)
            retired += r["retired"]
            require(len(seen)-retired == r["active_count"], "native populated sites")
            if i==179:
                direct=set(shot["edit"]["ids"])
                require(direct.isdisjoint(seen), "stroke double counted")
                seen |= direct
            if r["frame"] not in (210,240,300):
                continue
            cut=r["frame"]
            snap=read(out/"checkpoints"/f"{arm}-{cut}.json.gz")
            require(len(snap["state"])==cfg["material_count"], "unexpected material count")
            require({j for j,s in enumerate(snap["state"]) if s != 0}==seen, "cut states")
            require(snap["native_hash"] == next(v["native_hash"] for v in shot["cuts"] if v["frame"]==cut), "cut hash")
            eligible={j for j in shell if snap["state"][j]==0 and snap["fuel"][j]>0}
            for h in (1,4,8):
                events=[]
                for f in frames[cut:cut+h]:
                    ids=sorted(eligible.intersection(f["new_ids"]))
                    if ids:
                        events.append({"frame":f["frame"],"ids":ids})
                rows.append({"arm":arm,"cut":cut,"horizon":h,"eligible":len(eligible),
                             "first_ignition_frame":events[0]["frame"] if events else None,
                             "witness":events[0]["ids"][0] if events else None,
                             "events":events})
        require(shot["end"]["burning"]==len(seen)-retired and shot["end"]["charred"]==retired, "end states")
    summary={a:{
        "windows":len(t),"empty":sum(not q["eligible"] for q in t),
        "positive":sum(q["witness"] is not None for q in t),
        "negative":sum(q["witness"] is None for q in t),
        "repeated_eligible_site_queries":sum(q["eligible"] for q in t),
        "endpoint_active":report["shots"][a]["end"]["burning"],
        "endpoint_hash":report["shots"][a]["end"]["hash"]
    } for a in ("AB","BA") for t in [[q for q in rows if q["arm"]==a]]}
    return {"schema":"t92-exterior-brush-regional-truth-v1", "windows":rows, "summary":summary}

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference",type=Path,default=HERE/"evidence")
    args=parser.parse_args()
    result=evaluate(args.reference)
    cur=args.reference/"regional-truth.json"
    if cur.exists():
        require(read(cur)==result, "Stored truth differs")
    else:
        cur.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf8")
    print(json.dumps(result["summary"]))
