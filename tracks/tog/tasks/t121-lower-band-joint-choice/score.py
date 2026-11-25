"""Verify the fixed four-block schedule, full native trajectories and per-process contrasts."""
import hashlib
import math
from statistics import median
from prepare import HERE, load, write

O, R, S = "cold-ordinary", "cold-repair", "cold-sibling"
ORDERS = ((O,R,S), (S,R,O), (R,S,O), (O,S,R))
CAMS = [76,230]
KERNEL = "1505050a662c4d4d2561346eeff98d9a0d099485d78614a706cfb7a10a3ac0f1"


def main():
    root = HERE/"evidence/native"
    shots = load(root/"capture-report.json")["shots"]
    refs = {(r["arm"][1],r["camera"]):r for r in load(HERE/"REFERENCE.json")["queries"]}
    traces = {p:load(root/f"A{p}-trace.json.gz") for p in ("L","F")}
    burned = set(shots["AL"]["initial"]["ids"])
    for row in traces["L"][:180]:
        burned.update(row["new_ids"])
    elig = set(load(HERE/"shell.json.gz"))-burned
    weights = {c:{i:math.floor(w*1e6+.5) for i,w in load(HERE/f"weights-{c}.json.gz")["eligible_weights"]} for c in CAMS}
    def view(p,v,full):
        c = v["camera"]
        ref = refs[p,c]
        keys = ["defined","first_frame","mass","target","total","eligible"] + (["count"] if ref["defined"] else [])
        assert all(v[k]==ref[k] for k in keys)
        hit = ref["first_frame"]
        witness = min((i for i in traces[p][hit-1]["new_ids"] if i in elig and weights[c][i]>0), default=None) if hit else None
        assert v["witness"] == witness
        if full: assert v["curve"] == ref["curve"]
    need = [c for c in CAMS if refs["L",c]["defined"] and refs["L",c]["first_frame"] is None]
    choices = {str(c):"undefined" if not refs["L",c]["defined"] else "L" if c not in need else
               "F" if refs["F",c]["first_frame"] is not None else "none" for c in CAMS}
    blocks = []
    for idx,order in enumerate(ORDERS, 1):
        path = HERE/"evidence"/f"block-{idx}"/"CAPTURE.json"
        cap = load(path)
        assert cap["status"] == "validated" and not cap["errors"]
        assert cap["methods"] == list(order) and cap["repeats"] == 6
        assert cap["sources"]["plugin_11"] == KERNEL
        assert cap["sources"]["plugin_12"] == hashlib.sha256((HERE/"audit.js").read_bytes()).hexdigest()
        assert cap["common_parent"] == shots["AL"]["pre_edit"] == shots["AF"]["pre_edit"]
        assert cap["common_parent_successor"]["before"]["marker"] == cap["common_parent"]
        for key,s in cap["arms"].items():
            assert s["verified_frames"] == 360 and s["endpoint"] == shots[key]["end"]
            assert s["cut_hashes"] == {str(c["frame"]):c["native_hash"] for c in shots[key]["cuts"]}
        assert len(cap["queries"]) == 1
        q = cap["queries"][0]
        assert q["cameras"] == CAMS and len(q["trials"]) == 21
        warm = {m:[] for m in order}; cold={}; counters={}
        for i,t in enumerate(q["trials"]):
            rep,j=divmod(i,3)
            m=order[(rep+j)%3]
            assert t["rep"]==rep and t["method"]==m and t["choices"]==choices
            assert [x["pick"] for x in t["tried"]]==(["L","F"] if need else ["L"])
            for x in t["tried"]:
                p=x["pick"]
                assert x["clicked"]==shots["A"+p]["edit"]["count"]
                assert [v["camera"] for v in x["views"]]==(CAMS if p=="L" else need)
                for v in x["views"]:view(p,v,False)
            assert 0 <= t["total_browser_ms"] <= t["delivered_ms"]+2
            if rep: warm[m].append(t["delivered_ms"])
            else: cold[m]=t["delivered_ms"]
            if m==S:
                w=t["work"]
                counts={k:w[k] for k in ("steps","fallback","reused_steps","light_steps","full_steps","checkpointed",
                                          "checkpoint_particles","checkpoint_material_bytes","prepared_full_sites")}
                if counters: assert counters==counts
                counters=counts
                assert w["prepared_full_sites"] == shots["AF"]["edit"]["count"]
                if not w["fallback"]: assert w["reused_steps"]==(w["steps"] if need else 0)
        audits=cap["full_audits"]
        assert audits["sibling"]["fallback"] == counters["fallback"]
        if not counters["fallback"]:
            for x in audits["sibling"]["curves"]:
                for v in x["views"]:view(x["pick"],v,True)
        for m in (O,R):
            for p in ("L","F"):
                a=audits[m+"_"+p]
                for v in a["curves"]:view(p,v,a["evaluated_frames"]==90)
        med={m:median(warm[m]) for m in order}
        blocks.append(dict(capture_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),process_start=cap["started_utc"],
                           order=order,choices=choices,cold_ms=cold,warm_ms=warm,median_ms=med,
                           ratio_over_ordinary=med[S]/med[O],ratio_over_repair=med[S]/med[R],sibling=counters,
                           physical_parent_successor=cap["common_parent_successor"]))
    assert len({b["process_start"] for b in blocks})==4
    assert all(b["physical_parent_successor"]==blocks[0]["physical_parent_successor"] for b in blocks)
    gate={}
    for key in ("ratio_over_ordinary","ratio_over_repair"):
        rs=[b[key] for b in blocks]
        gate[key]=max(rs)<1 and sum(r<.9 for r in rs)>=3 and all(b["sibling"]["reused_steps"]>0 for b in blocks)
    write(HERE/"SCORE.json",dict(choices=choices,eligible=len(elig),blocks=blocks,gate=gate))
    print("choices",choices,"gate",gate)
    for n,b in enumerate(blocks,1):print(n,b["median_ms"],b["ratio_over_ordinary"],b["ratio_over_repair"],b["sibling"])


if __name__=="__main__":
    main()
