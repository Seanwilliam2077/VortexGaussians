"""Reconstruct camera threshold decisions and verify every issued edit-action answer."""
import gzip
import hashlib
import json
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parent

def read(name):
    raw=(ROOT/name).read_bytes()
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)

def truth(data,arm,camera):
    shot=data["arms"][arm]
    common=set(shot["initial"]) | set(shot["stroke"])
    for hits in shot["events"][:180]:
        common.update(hits)
    eligible=set(data["shells"][arm])-common
    weights=dict(data["cameras"][str(camera)])
    assert eligible.issubset(weights)
    total=sum(weights[i] for i in eligible)
    threshold=(total+3)//4
    seen=set()
    first=None
    mass=0
    curve=[]
    for step,hits in enumerate(shot["events"][180:180+data["horizon"]],181):
        current=eligible.intersection(hits)
        assert not seen.intersection(current)
        seen.update(current)
        mass+=sum(weights[i] for i in current)
        curve.append([step,len(current),len(seen),mass])
        if total and mass>=threshold and first is None:
            first=(step,len(seen),mass)
    step,count,mass=(None,len(seen),mass) if first is None else first
    return dict(defined=bool(total),first_frame=step,count=count,mass=mass,total=total,target=threshold,eligible=len(eligible)),curve

def check_result(row,reference):
    assert all(row[k]==v for k,v in reference.items()), (row,reference)

def main():
    manifest=read("MANIFEST.json")
    for name,sha in manifest.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
    total_calls=0
    blocks={}
    for session in read("sessions.json"):
        data=read(session["dataset"])
        capture=read(session["calls"])
        truth_table={(arm,int(c)):truth(data,arm,int(c)) for arm in data["arms"] for c in data["cameras"]}
        for q in capture["queries"]:
            groups={}
            for t in q["trials"]:
                assert t["method"] in capture["methods"] and t["delivered_ms"]>0
                if session["operation"]=="single":
                    check_result(t,truth_table[q["arm"],q.get("camera",0)][0])
                else:
                    views=q["cameras"]
                    need=set(views)
                    choices={}
                    attempted=[]
                    for pick in ("L","F"):
                        if not need:
                            break
                        attempted.append(pick)
                        tr=t["tried"][len(attempted)-1]
                        assert tr["pick"]==pick and {v["camera"] for v in tr["views"]}==need
                        for v in tr["views"]:
                            ref=truth_table["A"+pick,v["camera"]][0]
                            check_result(v,ref)
                            if ref["first_frame"] is not None:
                                choices[str(v["camera"])]=pick
                                need.remove(v["camera"])
                    assert len(t["tried"])==len(attempted)
                    for cam in need:
                        ref=truth_table["AF",cam][0]
                        choices[str(cam)]="none" if ref["defined"] else "undefined"
                    assert t["choices"]==choices,(t["choices"],choices)
                if t["rep"]:
                    groups.setdefault(t["method"],[]).append(t["delivered_ms"])
                total_calls+=1
            assert set(groups)==set(capture["methods"])
            assert len(q["trials"])==(1+capture["repeats"])*len(groups)
            assert all(len(rows)==capture["repeats"] for rows in groups.values())
            asset, _, block = session["label"].rpartition("-")
            if asset in ("firewoods","playground") and block.isdigit():
                ratio=median(groups["repair"])/median(groups["ordinary"])
                blocks.setdefault((asset,tuple(q["cameras"])),[]).append(ratio)
            print(session["label"],q.get("cameras",q.get("arm")),q.get("camera",""),{m:round(median(v),1) for m,v in groups.items()})
        for trace in capture["curves"]:
            expected=truth_table[trace["arm"],trace["camera"]][1]
            assert trace["curve"]==expected
    assert len(blocks)==4
    for key, ratios in sorted(blocks.items()):
        assert len(ratios)==4
        print(key, "4 process ratios", [round(x,3) for x in ratios], "median",round(median(ratios),3))
    print("Verified",total_calls,"issued calls and all included native progression curves.")

if __name__=="__main__":
    main()
