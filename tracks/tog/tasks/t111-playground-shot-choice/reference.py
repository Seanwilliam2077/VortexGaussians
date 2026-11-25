"""Independently reconstruct the common parent, integer-matte curves and light-first choices."""
import hashlib
import math
from prepare import HERE, load, write

def build():
    cfg=load(HERE/"recipe.json")
    static=load(HERE/"STATIC.json")
    root=HERE/"evidence"/"native"
    report=load(root/"capture-report.json")
    assert report["status"]=="validated" and not report["errors"]
    native=report["shots"]
    traces={a:load(root/f"{a}-trace.json.gz") for a in ("AL","AF")}
    assert native["AL"]["pre_edit"]==native["AF"]["pre_edit"] and native["AL"]["initial"]==native["AF"]["initial"]
    common=set(native["AL"]["initial"]["ids"])
    for x,y in zip(traces["AL"][:180],traces["AF"][:180],strict=True):
        assert {k:v for k,v in x.items() if not k.endswith("_ms")}=={k:v for k,v in y.items() if not k.endswith("_ms")}
        common.update(x["new_ids"])
    assert len(common)==native["AL"]["pre_edit"]["burning"]+native["AL"]["pre_edit"]["charred"]
    shell=set(load(HERE/"shell.json.gz"))
    elig=shell-common
    out=[]
    for arm,trace in traces.items():
        assert [r["frame"] for r in trace]==list(range(1,361))
        expected=next(p for p in cfg["picks"] if p["name"]==arm[1])
        assert set(native[arm]["edit"]["ids"])==set(expected["initial_geometric_neighbors"])-common
        assert not shell.intersection(native[arm]["edit"]["ids"])
        for cid_string,meta in static["cameras"].items():
            cid=int(cid_string)
            file=HERE/f"weights-{cid}.json.gz"
            assert hashlib.sha256(file.read_bytes()).hexdigest()==meta["sha256"]
            raw=dict(load(file)["eligible_weights"])
            assert set(raw)==shell
            weights={i:math.floor(raw[i]*1e6+.5) for i in elig}
            total=sum(weights.values());target=(total+3)//4
            total_float=math.fsum(raw[i] for i in elig)
            curve=[];burned=set();mass=0;first=None;first_float=None;at_mass=None;at_count=None
            for row in trace[180:270]:
                hits=elig.intersection(row["new_ids"])
                assert not burned.intersection(hits)
                burned.update(hits)
                mass+=sum(weights[i] for i in hits)
                curve.append([row["frame"],len(hits),len(burned),mass])
                if first is None and target>0 and mass>=target:
                    first,at_mass,at_count=row["frame"],mass,len(burned)
                if first_float is None and total_float>0 and math.fsum(raw[i] for i in burned)*4>=total_float:
                    first_float=row["frame"]
            out.append(dict(arm=arm,camera=cid,defined=total>0,first_frame=first,first_float=first_float,
                      count=len(burned) if first is None else at_count,mass=mass if first is None else at_mass,
                      total=total,target=target,eligible=len(elig),curve=curve,deadline_mass=mass))
    return dict(schema="t111-common-parent-reference-v1",pre_click=native["AL"]["pre_edit"],
                common_pre_click_frames=180,eligible_sites=len(elig),queries=out)

if __name__=="__main__":
    result=build()
    write(HERE/"REFERENCE.json",result)
    for r in result["queries"]:
        print(r["camera"],r["arm"],r["first_frame"],r["eligible"],r["deadline_mass"],r["total"])
