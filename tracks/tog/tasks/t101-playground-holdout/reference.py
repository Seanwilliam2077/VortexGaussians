"""Score the six registered Playground first-event or deadline queries."""
import gzip
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def read(path):
    data=path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix==".gz" else data)


def reference():
    base=HERE/"evidence"
    rep=read(base/"capture-report.json")
    assert rep["status"]=="validated" and not rep["errors"]
    regions=read(HERE/"shell-ids.json.gz")
    out=[]
    for arm in ("AB","BA"):
        q=rep["shots"][arm]
        trace=read(base/f"{arm}-trace.json.gz")
        assert [t["frame"] for t in trace]==list(range(1,361))
        lit=set(q["initial"]["ids"])
        for step in trace[:180]:
            new=set(step["new_ids"])
            assert not lit & new
            lit.update(new)
        assert len(lit)==q["pre_edit"]["burning"]+q["pre_edit"]["charred"]
        assert not lit.intersection(q["edit"]["ids"])
        lit.update(q["edit"]["ids"])
        assert len(lit)==q["post_edit"]["burning"]+q["post_edit"]["charred"]
        shell=set(regions[arm[1]])
        eligible=shell-lit    # native fresh PLY starts with unit fuel at every site
        for h in (30,60,180):
            f=None; ids=[]
            for step in trace[180:180+h]:
                hit=sorted(eligible.intersection(step["new_ids"]))
                if hit:
                    f=step["frame"]; ids=hit
                    break
            out.append(dict(asset="playground",arm=arm,cut=180,horizon=h,eligible=len(eligible),
                            shell_size=len(shell),first_frame=f,ids=ids,observed_steps=h if f is None else f-180))
    return dict(schema="t101-click-reference-v1",queries=out)


if __name__=="__main__":
    result=reference()
    dest=HERE/"REFERENCE.json"
    if dest.exists(): assert read(dest)==result
    else: dest.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    for r in result["queries"]: print(r["arm"],r["horizon"],r["first_frame"],r["observed_steps"])
