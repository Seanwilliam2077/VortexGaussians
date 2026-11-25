"""Reconstruct camera-matte answers and every per-frame count from native onset ledgers."""
import gzip
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
TASKS=HERE.parent


def read(p):
    b=p.read_bytes()
    return json.loads(gzip.decompress(b) if p.suffix==".gz" else b)


def compute():
    weight_path=TASKS/"t107-visible-burn-progression/evidence/weights-0.json.gz"
    assert hashlib.sha256(weight_path.read_bytes()).hexdigest()=="08aade341633cada213895141ae6bbfe0b36ebaa2e729b9227b9fb668caaf432"
    data=read(weight_path)
    assert data["camera_id"]==0 and data["asset_count"]==34687
    floats=dict(data["eligible_weights"])
    weights={j:math.floor(w*1e6+0.5) for j,w in floats.items()}
    native=TASKS/"t86-ignition-margin/public"
    cap=read(native/"capture-report.json")
    shells=read(TASKS/"t87-stroke-halo/PREDICTIONS.json.gz")["shell_ids"]
    outputs=[]
    for arm in ("AB","BA"):
        shot=cap["shots"][arm];frames=read(native/f"{arm}-trace.json.gz")
        lit=set(shot["initial"]["ids"])|set(shot["edit"]["ids"])
        for row in frames[:180]:lit.update(row["new_ids"])
        eligible=set(shells[arm])-lit
        assert not eligible-weights.keys()
        total=sum(weights[j] for j in eligible); target=(total+3)//4
        float_total=math.fsum(floats[j] for j in eligible)
        seen=set();curve=[];first=None;count_at=0;mass_at=0;mass=0;first_float=None
        for row in frames[180:]:
            hits=eligible.intersection(row["new_ids"]);assert hits.isdisjoint(seen)
            seen.update(hits);mass+=sum(weights[j] for j in hits)
            curve.append([row["frame"],len(hits),len(seen),mass])
            if first is None and target and mass>=target:
                first=row["frame"];count_at=len(seen);mass_at=mass
            if first_float is None and float_total and math.fsum(floats[j] for j in seen)*4>=float_total:
                first_float=row["frame"]
        outputs.append(dict(arm=arm,defined=total>0,first_frame=first,total=total,target=target,eligible=len(eligible),
                            count=len(seen) if first is None else count_at,mass=mass if first is None else mass_at,
                            curve=curve,float_total=float_total,first_float=first_float))
    return dict(schema="t108-visible-burn-progress-v1",queries=outputs)


if __name__=="__main__":
    r=compute();p=HERE/"REFERENCE.json"
    if p.exists():assert read(p)==r
    else:p.write_text(json.dumps(r,indent=2)+"\n",encoding="utf8")
    for q in r["queries"]:print(q["arm"],q["first_frame"],q["first_float"],q["count"],q["mass"],q["target"])
