"""Reconstruct camera threshold decisions and verify every issued edit-action answer."""
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parent

def read(name):
    raw=(ROOT/name).read_bytes()
    return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)

def verify_camera_observations():
    from math import fsum, isclose
    data = read("native-camera-contrast.json.gz")
    assert data["schema"] == "t127-contrast-histogram-v1" and data["cutoff_sum"] == 64
    assert data["pixel_count"] == 470 * 264
    arms = ("light", "full")
    seen, endpoints, references = set(), {}, {}
    for pair in data["comparisons"]:
        key = pair["camera"], pair["horizon"], pair["brush"]
        assert key not in seen
        seen.add(key)
        counts, weights = pair["counts"], pair["shell_weights"]
        assert len(counts) == len(weights) == 1021
        assert all(type(n) is int and n >= 0 for n in counts)
        assert all(w >= 0 for w in weights) and sum(counts) == data["pixel_count"]
        cut = data["cutoff_sum"]
        num, den = fsum(weights[cut:]), fsum(weights)
        ref = pair["reference"]
        assert sum(counts[cut:]) == ref["changed_pixels"]
        assert isclose(num, ref["changed_shell_mass"], rel_tol=3e-12, abs_tol=1e-12)
        assert isclose(den, ref["shell_mass"], rel_tol=3e-12, abs_tol=1e-12)
        passed = 4 * num >= den
        assert passed == ref["passes_quarter"]
        if pair["horizon"] == 90:
            endpoints[pair["camera"], pair["brush"]] = passed
            stem = f"{pair['brush']}-c{pair['camera']}-h90-"
            references[pair["camera"], pair["brush"]] = dict(mass=num, total=den, passed=passed,
                png={mode:pair["sha256"][stem + mode + ".png"] for mode in ("full","wood")})
    assert seen == {(c,h,b) for c in (0,124) for h in (44,90) for b in arms}
    choices = {str(c):next((b for b in arms if endpoints[c,b]), "neither") for c in (0,124)}
    assert choices == data["endpoint_choices"] == {"0":"light", "124":"neither"}
    print("Verified eight final-image gas comparisons and both camera choices:", choices)
    return references


def verify_image_delivery(references):
    data=read("t129-native-image-choice.json.gz")
    assert data["schema"]=="native-image-delivery-v1" and len(data["processes"])==2
    assert 0<data["projection_inner_ms"]<=data["projection_host_ms"]
    original=read("geometry-a-prospective.json.gz")
    assert data["parent"]["hash"]==original["arms"]["AL"]["parent"]==original["arms"]["AF"]["parent"]
    assert set(data["endpoints"])=={"L","F"}
    print("Shared cold projection for both cameras (ms)",round(data["projection_host_ms"],2))
    methods=["ordinary","sibling"]
    scopes=[[0],[0,124]]
    def verify_row(row,audit):
        method=row["method"];cams=row["cameras"]
        assert method in methods and cams in scopes and 0<row["browser_ms"]<=row["delivered_ms"]+2
        phases=row["phases_ms"]
        assert set(phases)=={"fork_restore_ms","pick_ms","guard_ms","physics_ms","transport_ms","render_read_ms","score_ms"}
        assert all(math.isfinite(t) and t>=0 for t in phases.values())
        assert phases["physics_ms"]>0 and phases["render_read_ms"]>0
        missed=[c for c in cams if not references[c,"light"]["passed"]]
        choices={str(c):("L" if c not in missed else "F" if references[c,"full"]["passed"] else "none") for c in cams}
        assert row["choices"]==choices
        expected=["L","F"] if audit or missed else ["L"]
        shared=24 if method=="sibling" else 0
        assert row["shared_steps"]==shared and row["reused_steps"]==(shared if "F" in expected else 0)
        assert [s["pick"] for s in row["strokes"]]==expected
        for stroke in row["strokes"]:
            pick=stroke["pick"]
            assert stroke["clicked"]==len(original["arms"]["A"+pick]["stroke"])
            assert stroke["steps"]==(90-shared if pick=="F" else 90)
            assert [v["camera"] for v in stroke["views"]]==(cams if pick=="L" or audit else missed)
            if audit: assert stroke["state"]==data["endpoints"][pick]
            for v in stroke["views"]:
                ref=references[v["camera"],"light" if pick=="L" else "full"]
                assert v["passes_quarter"] is ref["passed"]
                for key,want in (("shell_mass",ref["total"]),("changed_shell_mass",ref["mass"]),("fraction",ref["mass"]/ref["total"])):
                    assert math.isclose(v[key],want,rel_tol=3e-12,abs_tol=1e-9)
                if audit: assert v["png_sha256"]==ref["png"]
    total=0
    for index,block in enumerate(data["processes"],1):
        assert block["process"]==index and block["common_parent"]==data["parent"]
        for c in (0,124):
            view=data["mapped_views"][str(c)]
            assert (view["rows"],view["columns"],view["bytes"])==(264,470,992640)
            assert block["installed_map_sha256"][str(c)]==view["sha256"]
            assert math.isclose(block["calibration"][str(c)]["total"],references[c,"light"]["total"],rel_tol=3e-12)
        assert [a["method"] for a in block["audits"]]==methods
        for a in block["audits"]:
            assert a["cameras"]==[0,124] and a["rep"]==-1
            verify_row(a,True)
        assert len(block["trials"])==28
        scope_order=scopes if index==1 else list(reversed(scopes))
        for slot,cams in enumerate(scope_order):
            times={m:[] for m in methods}
            for rep in range(7):
                order=methods if (rep+index-1+slot)%2==0 else methods[::-1]
                for j,m in enumerate(order):
                    row=block["trials"][14*slot+2*rep+j]
                    assert row["method"]==m and row["cameras"]==cams and row["rep"]==rep
                    verify_row(row,False)
                    times[m].append(row["delivered_ms"])
                    total+=1
            published=next(q for q in block["verified_timings"] if q["cameras"]==cams)
            for m in methods:
                assert times[m]==[published["first_call_ms"][m]]+published["measured_ms"][m]
            medians={m:round(median(times[m][1:]),2) for m in methods}
            wins=sum(s<o for o,s in zip(times["ordinary"][1:],times["sibling"][1:]))
            print("T129 native image choice, process",index,"cameras",cams,"median ms",medians,"paired sibling wins",wins,"/ 6")
    assert total==56
    return total


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
    witness=None
    curve=[]
    for step,hits in enumerate(shot["events"][180:180+data["horizon"]],181):
        current=eligible.intersection(hits)
        assert not seen.intersection(current)
        seen.update(current)
        mass+=sum(weights[i] for i in current)
        curve.append([step,len(current),len(seen),mass])
        if total and mass>=threshold and first is None:
            first=(step,len(seen),mass)
            witness=min(i for i in current if weights[i]>0)
    step,count,mass=(None,len(seen),mass) if first is None else first
    return dict(defined=bool(total),first_frame=step,count=count,mass=mass,total=total,target=threshold,eligible=len(eligible)),curve,witness

def check_result(row,reference):
    assert all(row[k]==v for k,v in reference.items()), (row,reference)

def main():
    manifest=read("MANIFEST.json")
    for name,sha in manifest.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
    total_calls=0
    blocks={}
    sibling_blocks={}
    heldout=[]
    one_trace=[]
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
                            assert v["witness"] == truth_table["A"+pick,v["camera"]][2]
                            if not ref["defined"]:
                                choices[str(v["camera"])]="undefined"
                                need.remove(v["camera"])
                            elif ref["first_frame"] is not None:
                                choices[str(v["camera"])]=pick
                                need.remove(v["camera"])
                    assert len(t["tried"])==len(attempted)
                    for cam in need:
                        ref=truth_table["AF",cam][0]
                        choices[str(cam)]="none" if ref["defined"] else "undefined"
                    assert t["choices"]==choices,(t["choices"],choices)
                    if t["method"].startswith("equiv-"):
                        recorded=t["equivalence"]
                        inferred=[v["camera"] for row in t["tried"] if row.get("inferred") for v in row["views"]]
                        assert inferred==recorded["inferred"]
                        assert len(t["tried"])-sum(bool(row.get("inferred")) for row in t["tried"])==recorded["physical_attempts"]
                        assert recorded["admitted"]==(session["label"].startswith("equivalence-lower-"))
                        if recorded["admitted"]: assert recorded["certified"]==90 and recorded["physical_attempts"]==1
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
            if asset in ("transport-firewoods","transport-playground") and block.isdigit():
                values={m:median(rows) for m,rows in groups.items()}
                sibling_blocks.setdefault((asset,tuple(q["cameras"])),[]).append(
                    [round(values[m]/values["cold-ordinary"],3) for m in ("cold-repair","cold-sibling")])
            if asset=="heldout":
                heldout.append([median(groups["cold-sibling"])/median(groups[m]) for m in ("cold-ordinary","cold-repair")])
            if asset=="equivalence-lower":
                one_trace.append([median(groups[m]) for m in ("cold-ordinary","cold-repair","cold-sibling","equiv-ordinary","equiv-repair")])
            print(session["label"],q.get("cameras",q.get("arm")),q.get("camera",""),{m:round(median(v),1) for m,v in groups.items()})
        for trace in capture["curves"]:
            expected=truth_table[trace["arm"],trace["camera"]][1]
            assert trace["curve"]==expected
    assert len(blocks)==4
    for key, ratios in sorted(blocks.items()):
        assert len(ratios)==4
        print(key, "4 process ratios", [round(x,3) for x in ratios], "median",round(median(ratios),3))
    for key, ratios in sorted(sibling_blocks.items()):
        assert len(ratios)==2
        print(key,"cold repair / cold sibling ratios to cold ordinary, per process",ratios)
    assert len(heldout)==4 and len(one_trace)==2
    print("Held-out transport ratios to full and regional", [[round(x,3) for x in row] for row in heldout])
    print("Retrospective complete-equivalence test times", [[round(x,1) for x in row] for row in one_trace])
    assert total_calls==912
    direct_calls=verify_image_delivery(verify_camera_observations())
    print("Verified",total_calls,"material calls and all included native progression curves,",
          direct_calls,"direct image calls (48 measured and 8 warmups), and 8 paired display observations.")

if __name__=="__main__":
    main()
