"""Native reference from common-ancestor onset ledgers and frozen exterior-shell mattes."""
import hashlib
import math
from prepare import HERE, TASKS, load, write


def build():
    cfg=load(HERE/"recipe.json")
    path=HERE/"evidence/native"
    cap=load(path/"capture-report.json")
    assert cap["status"]=="validated" and not cap["errors"]
    shots=cap["shots"]
    traces={a:load(path/(a+"-trace.json.gz")) for a in ("AL","AF")}
    assert shots["AL"]["initial"]==shots["AF"]["initial"] and shots["AL"]["pre_edit"]==shots["AF"]["pre_edit"]
    shell=set(load(HERE/"shell.json.gz"))
    common=set(shots["AL"]["initial"]["ids"])
    for x,y in zip(traces["AL"][:180],traces["AF"][:180],strict=True):
        assert {k:v for k,v in x.items() if not k.endswith("_ms")}=={k:v for k,v in y.items() if not k.endswith("_ms")}
        common.update(x["new_ids"])
    assert len(common)==shots["AL"]["pre_edit"]["burning"]+shots["AL"]["pre_edit"]["charred"]
    eligible=shell-common
    assert all(len(rows)==360 for rows in traces.values())
    frozen=load(HERE/"STATIC.json")
    queries=[]
    for arm in ("AL","AF"):
        trace=traces[arm]
        assert [r["frame"] for r in trace]==list(range(1,361))
        edit=set(shots[arm]["edit"]["ids"])
        pick=next(p for p in cfg["picks"] if p["name"]==arm[1])
        assert edit==set(pick["initial_geometric_neighbors"])-common and edit.isdisjoint(eligible)
        for cam in (0,124):
            file=TASKS/f"t107-visible-burn-progression/evidence/weights-{cam}.json.gz"
            assert hashlib.sha256(file.read_bytes()).hexdigest()==frozen["cameras"][str(cam)]["sha256"]
            values=dict(load(file)["eligible_weights"])
            weights={j:math.floor(values[j]*1e6+.5) for j in eligible}
            total=sum(weights.values());target=(total+3)//4
            seen=set();curve=[];mass=0;first=None;first_float=None;count_at=mass_at=None
            for row in trace[180:270]:
                group=eligible.intersection(row["new_ids"])
                assert not seen.intersection(group)
                seen.update(group);mass+=sum(weights[j] for j in group)
                curve.append([row["frame"],len(group),len(seen),mass])
                if first is None and target>0 and mass>=target:
                    first,count_at,mass_at=row["frame"],len(seen),mass
                if first_float is None and total>0 and math.fsum(values[j] for j in seen)*4>=math.fsum(values[j] for j in eligible):
                    first_float=row["frame"]
            queries.append(dict(arm=arm,camera=cam,defined=total>0,first_frame=first,count=len(seen) if first is None else count_at,
                                mass=mass if first is None else mass_at,total=total,target=target,eligible=len(eligible),curve=curve,
                                deadline_mass=mass,first_float=first_float))
    return {"schema":"t109-common-parent-reference-v1","pre_click":shots["AL"]["pre_edit"],
            "common_pre_click_frames":180,"eligible_sites":len(eligible),"queries":queries}


if __name__=="__main__":
    result=build();write(HERE/"REFERENCE.json",result)
    for q in result["queries"]:
        print(q["arm"],q["camera"],q["first_frame"],q["deadline_mass"],q["target"])
