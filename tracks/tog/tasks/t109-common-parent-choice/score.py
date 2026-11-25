"""Check both sibling proposals, camera-sensitive answers and actual hot/cold costs."""
import hashlib
from statistics import median
from reference import HERE, TASKS, build, load, write

METHODS=("ordinary","restart","repair")
FIELDS=("defined","first_frame","total","target","eligible","count","mass")
WORK=("ordinary_steps","sliced_steps","repair_steps","repairs","restarts","log_bytes","peak_log_bytes",
      "projected_material_bytes","logged_samples","guards")


def score():
    ref=build();assert ref==load(HERE/"REFERENCE.json")
    tgt={(q["arm"],q["camera"]):q for q in ref["queries"]}
    path=HERE/"evidence/timing/CAPTURE.json"
    cap=load(path)
    assert cap["status"]=="validated" and not cap["errors"] and cap["repeats"]==3 and tuple(cap["methods"])==METHODS
    origin=load(HERE/"evidence/native/capture-report.json")
    shell=load(HERE/"shell.json.gz")
    assert cap["common_parent"]==ref["pre_click"]
    for a,shot in cap["arms"].items():
        n=origin["shots"][a]
        assert shot["verified_frames"]==360 and shot["endpoint"]==n["end"] and shot["shell_ids"]==shell
        assert shot["cut_hashes"]=={str(r["frame"]):r["native_hash"] for r in n["cuts"]}
    summaries=[]
    cold=[]
    for qi,row in enumerate(cap["queries"]):
        a,c=row["arm"],row["camera"];q=tgt.pop((a,c));audit=cap["flow_audits"][f"{a}/{c}"]
        assert row["cut"]==180 and row["horizon"]==90 and len(row["trials"])==12
        for m in METHODS:
            assert audit[m]["curve"]==q["curve"] and all(audit[m][k]==q[k] for k in FIELDS)
        assert audit["repair"]["boundaries"]==audit["ordinary"]["boundaries"]
        measured={m:[] for m in METHODS}
        for i,t in enumerate(row["trials"]):
            rep,j=divmod(i,len(METHODS));m=METHODS[(j+rep+qi)%len(METHODS)]
            assert m==t["method"] and t["rep"]==rep and all(t[k]==q[k] for k in FIELDS)
            assert t["clicked"]==origin["shots"][a]["edit"]["count"]
            for v in t["work"]["active"]:
                if v["anchor_built"]:
                    cold.append({"arm":a,"camera":c,"method":m,"wave":rep,"ms":v["anchor_build_ms"],"bytes":v["anchor_bytes"]})
            if rep:measured[m].append(t)
        modes={}
        for m,trials in measured.items():
            assert len(trials)==3
            work={k:trials[0]["work"][k] for k in WORK}
            assert all(t["work"][k]==v for t in trials for k,v in work.items())
            modes[m]={"delivered_ms":median(t["delivered_ms"] for t in trials),
                      "range_ms":[min(t["delivered_ms"] for t in trials),max(t["delivered_ms"] for t in trials)],
                      "click_ms":median(t["click_ms"] for t in trials),"shell_ms":median(t["shell_index_ms"] for t in trials),
                      "denominator_ms":median(t["denominator_ms"] for t in trials),"work":work}
        summaries.append({"arm":a,"camera":c,"clicked":origin["shots"][a]["edit"]["count"], **{k:q[k] for k in FIELDS},
                          "deadline_mass":q["deadline_mass"],"first_float":q["first_float"],"methods":modes,
                          "repair_audit_frames":list(audit["repair"]["boundaries"]),
                          "ratios":{m:x["delivered_ms"]/modes["ordinary"]["delivered_ms"] for m,x in modes.items()}})
    assert not tgt and len(summaries)==4 and len(cold)==1
    choices={}
    for c in (0,124):
        candidates={q["arm"]:q for q in summaries if q["camera"]==c}
        l,f=(candidates[a] for a in ("AL","AF"))
        assert l["total"]==f["total"] and l["target"]==f["target"] and l["eligible"]==f["eligible"]
        search=[l] if l["first_frame"] is not None else [l,f]
        choices[str(c)]={"selection":next((a for a in ("AL","AF") if candidates[a]["first_frame"] is not None),"none"),
                         "sequential_queried_arms":[q["arm"] for q in search],
                         "sequential_additive_window_medians_ms":{m:sum(q["methods"][m]["delivered_ms"] for q in search) for m in METHODS},
                         "joint_review_sum_of_two_window_medians_ms":{m:sum(q["methods"][m]["delivered_ms"] for q in candidates.values()) for m in METHODS}}
    return {"choices":choices,"queries":summaries,"captured_anchor_builds":cold,"view_cache":cap["view_cache"],
            "view_install_ms":{str(c):cap["arms"]["AL"]["phases_ms"][f"install_camera_{c}"] for c in (0,124)},
            "projection_seconds_T107":load(TASKS/"t107-visible-burn-progression/evidence/cost.json"),
            "sha256":hashlib.sha256(path.read_bytes()).hexdigest()}


if __name__=="__main__":
    result=score();write(HERE/"SCORE.json",result)
    print(result["choices"])
    for q in result["queries"]:print(q["arm"],q["camera"],q["first_frame"],q["ratios"])
