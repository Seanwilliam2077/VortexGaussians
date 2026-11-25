"""Recover a protected-region first event from full independent native onsets."""
import gzip
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def read(path):
    b=path.read_bytes()
    return json.loads(gzip.decompress(b) if path.suffix==".gz" else b)


def compute():
    region=set(read(HERE/"selection-ids.json.gz"))
    base=HERE/"evidence/native"
    capture=read(base/"capture-report.json")
    assert capture["status"]=="validated" and not capture["errors"]
    rows=[]
    for arm in ("AB","BA"):
        shot=capture["shots"][arm]
        tr=read(base/(arm+"-trace.json.gz"))
        assert [r["frame"] for r in tr]==list(range(1,361))
        lit=set(shot["initial"]["ids"])
        for r in tr[:180]: lit.update(r["new_ids"])
        assert len(lit)==shot["pre_edit"]["burning"]+shot["pre_edit"]["charred"]
        assert lit.isdisjoint(shot["edit"]["ids"])
        lit.update(shot["edit"]["ids"])
        assert len(lit)==shot["post_edit"]["burning"]+shot["post_edit"]["charred"]
        eligible=region-lit
        first=None; ids=[]
        for r in tr[180:]:
            hits=sorted(eligible.intersection(r["new_ids"]))
            if hits:
                first=r["frame"]; ids=hits; break
        rows.append(dict(asset="protected",arm=arm,cut=180,horizon=180,shell_size=len(region),
                         eligible=len(eligible),first_frame=first,ids=ids,
                         last_verified_event_free_frame=first-1 if ids else 360,
                         observed_steps=first-180 if ids else 180))
    return dict(schema="t105-protected-patch-first-event-v1",queries=rows)


if __name__=="__main__":
    result=compute()
    dst=HERE/"REFERENCE.json"
    if dst.exists(): assert read(dst)==result
    else: dst.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    for row in result["queries"]: print(row["arm"],row["eligible"],row["first_frame"],len(row["ids"]))
