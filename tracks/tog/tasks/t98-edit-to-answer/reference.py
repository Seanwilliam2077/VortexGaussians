"""Freeze actual second-click ground truth from full native per-frame onsets."""
import gzip
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
TASKS=HERE.parent

def read(path):
    data=path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix==".gz" else data)

def truth():
    output=[]
    for asset in ("firewoods","dead-tree"):
        if asset == "firewoods":
            base=TASKS/"t86-ignition-margin"/"public"
            shells=read(TASKS/"t87-stroke-halo"/"PREDICTIONS.json.gz")["shell_ids"]
        else:
            base=TASKS/"t92-transfer-workload"/"evidence"
            by_pick=read(TASKS/"t92-transfer-workload"/"shell-ids.json.gz")
            shells={a:by_pick[a[1]] for a in ("AB","BA")}
        receipt=read(base/"capture-report.json")
        for arm in ("AB","BA"):
            ref=receipt["shots"][arm]
            frames=read(base/f"{arm}-trace.json.gz")
            assert [f["frame"] for f in frames] == list(range(1,361))
            lit=set(ref["initial"]["ids"])
            for row in frames[:180]:
                lit.update(row["new_ids"])
            assert len(lit)==ref["pre_edit"]["burning"]+ref["pre_edit"]["charred"]
            direct=set(ref["edit"]["ids"])
            assert not (direct & lit)
            lit |= direct
            assert len(lit)==ref["post_edit"]["burning"]+ref["post_edit"]["charred"]
            shell=set(shells[arm]); eligible=shell-lit
            # A cold never-ignited native PLY site has its initial unit fuel. Reconcile
            # against the later saved native cut on all sites still cold at that cut.
            snap=read(base/f"{arm}-210-eligibility.json.gz") if asset=="firewoods" else read(base/"checkpoints"/f"{arm}-210.json.gz")
            for j in eligible:
                assert snap["state"][j]!=0 or snap["fuel"][j]==1
            for h in (60,180):
                first=next(((f["frame"],sorted(set(f["new_ids"]) & eligible)) for f in frames[180:180+h]
                            if eligible.intersection(f["new_ids"])),None)
                output.append(dict(asset=asset,arm=arm,cut=180,horizon=h,eligible=len(eligible),shell_size=len(shell),
                                   first_frame=first[0] if first else None,ids=first[1] if first else [],
                                   observed_steps=first[0]-180 if first else h))
    return {"schema":"t98-click-reference-v1","queries":output}

if __name__=="__main__":
    result=truth()
    dest=HERE/"REFERENCE.json"
    if dest.exists():
        assert read(dest)==result
    else:
        dest.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    for r in result["queries"]:
        print(r["asset"],r["arm"],r["horizon"],r["eligible"],r["first_frame"],len(r["ids"]))
