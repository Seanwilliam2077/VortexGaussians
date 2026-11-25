"""Verify T114's Firewoods timing and boundary/continuation evidence using published JSON."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median

HERE=Path(__file__).resolve().parent
METHODS=("ordinary","repair","sparse","sitewise")
def read(p):
    return json.loads(p.read_bytes())

def score(folder,strict):
    file=folder/"CAPTURE.json"
    data=read(file)
    targets={r["arm"]:r for r in read(HERE.parent/"t108-visible-progression/REFERENCE.json")["queries"]}
    assert data["status"]=="validated" and not data["errors"] and tuple(data["methods"])==METHODS and data["repeats"]==4
    result={}
    fields=("first_frame","total","target","eligible","count","mass","defined")
    for index,q in enumerate(data["queries"]):
        arm=q["arm"];ref=targets[arm];shot=data["arms"][arm]
        assert shot["verified_frames"]==360 and q["horizon"]==180 and q["first_frame"]==ref["first_frame"]
        audits=shot["progress_audits"]
        for m in METHODS:
            assert all(audits[m][k]==ref[k] for k in fields) and audits[m]["curve"]==ref["curve"]
            assert audits[m]["boundaries"]==audits["repair"]["boundaries"]
        assert all(set(v)=={"now","next"} for v in audits["repair"]["boundaries"].values())
        site_audit=audits["sitewise"]["work"]["recovery_blocks"]
        if strict:
            assert not q["trials"] and all(b["direct_state"]["matched_boundary"] and b["direct_state"]["matched_next"] for b in site_audit)
            result[arm]=[b["direct_state"] for b in site_audit]
            continue
        groups={m:[] for m in METHODS}
        for k,t in enumerate(q["trials"]):
            rep,ordinal=divmod(k,4);m=METHODS[(rep+ordinal+index)%4]
            assert t["method"]==m and t["rep"]==rep and all(t[f]==ref[f] for f in fields)
            if rep:groups[m].append(t)
        assert all(len(ts)==4 for ts in groups.values())
        records={}
        for m,ts in groups.items():
            delivered=[t["delivered_ms"] for t in ts]
            records[m]=dict(delivered_ms=median(delivered),range_ms=[min(delivered),max(delivered)],
                            delivered_waves_ms=delivered,phase_ms=median(t["phases"]["repair_ms"] for t in ts),
                            repaired_steps=ts[0]["work"]["repair_steps"])
        last_steps=groups["sitewise"][0]["work"]["repairs"]
        blocks=site_audit[:last_steps]
        assert sum(b["frames"] for b in blocks)==records["sitewise"]["repaired_steps"]
        for b in blocks:
            assert b["profile_counts"] and b["flame_writes"]<=b["hit_calls"] and b["clock_sites"]==b["old_burning"]+b["added_sites"]
        result[arm]=dict(first=ref["first_frame"],methods=records,timed_blocks_profiled_separately=blocks,
                         audit_boundaries=[int(k) for k in audits["repair"]["boundaries"]])
    assert set(result)==set(targets)
    report=dict(capture_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),strict_direct=strict,arms=result)
    (folder/"SCORE.json").write_text(json.dumps(report,indent=2)+"\n",encoding='utf8')
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--capture-dir",type=Path,default=HERE/"evidence/firewoods")
    p.add_argument("--direct",action="store_true");args=p.parse_args()
    print(json.dumps(score(args.capture_dir,args.direct),indent=2))
