"""Check every direct and inferred reply against the recorded edit and aggregate by process."""
import gzip
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
SCENES = {"lower":"t121-lower-band-joint-choice","firewoods":"t109-common-parent-choice",
          "playground":"t111-playground-shot-choice"}
METHODS = ["cold-ordinary","cold-repair","cold-sibling","equiv-ordinary","equiv-repair"]


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def evaluate(scene, block):
    study = HERE.parent / SCENES[scene]
    reference = {(q["arm"][-1],q["camera"]):q for q in read(study/"REFERENCE.json")["queries"]}
    native = read(study/"evidence/native/capture-report.json")["shots"]
    cap = read(HERE/"evidence"/f"{scene}-{block}"/"CAPTURE.json")
    assert cap["status"] == "validated" and not cap["errors"]
    assert cap["common_parent"] == native["AL"]["pre_edit"] == native["AF"]["pre_edit"]
    for arm in ("AL","AF"):
        assert cap["arms"][arm]["endpoint"] == native[arm]["end"]
        assert cap["arms"][arm]["verified_frames"] == 360
    q, = cap["queries"]
    views = q["cameras"]
    methods = METHODS if scene=="lower" else METHODS[-2:]
    if block==2: methods = list(reversed(methods))
    repeats = 5 if scene=="lower" else 1
    assert cap["methods"] == methods and cap["repeats"] == repeats
    assert len(q["trials"]) == (1+repeats)*len(methods)
    samples, cold, guard = {m:[] for m in methods},{},{}
    for i,t in enumerate(q["trials"]):
        rep,col=divmod(i,len(methods))
        method=methods[(rep+col)%len(methods)]
        assert t["method"]==method and t["rep"]==rep
        assert 0 < t["delivered_ms"] and t["total_browser_ms"] <= t["delivered_ms"]+1
        if rep: samples[method].append(t["delivered_ms"])
        else: cold[method]=t["delivered_ms"]
        expected={}; waiting=list(views)
        for pick in ("L","F"):
            if not waiting:break
            shot=t["tried"][0 if pick=="L" else 1]
            assert shot["pick"]==pick and shot["clicked"]==native["A"+pick]["edit"]["count"]
            assert [v["camera"] for v in shot["views"]]==waiting
            if method.startswith("equiv"):
                assert bool(shot.get("inferred"))==(pick=="F" and scene=="lower")
            left=[]
            for v in shot["views"]:
                c=v["camera"];r=reference[pick,c]
                for key in ("defined","first_frame","total","target","eligible","count","mass"):
                    assert v[key]==r[key]
                if r["first_frame"] is None:
                    assert v["witness"] is None
                if not v["defined"]:expected[str(c)]="undefined"
                elif v["first_frame"] is not None:expected[str(c)]=pick
                else:expected[str(c)]="none";left.append(c)
            waiting=left
        assert t["choices"]==expected
        if method.startswith("equiv"):
            g=t["equivalence"]
            assert g["admitted"]==(scene=="lower")
            assert g["physical_attempts"]==len(t["tried"])-(1 if g["inferred"] else 0)
            assert g["upper"]>=90 if g["admitted"] else g["upper"]<90
            if g["admitted"]:
                assert g["certified"]==90 and g["inferred"]==views and g["physical_attempts"]==1
            if rep:guard.setdefault(method,[]).append(g["proof_ms"])
    result={"scope":views,"calls":len(q["trials"]),"mode":"timed" if scene=="lower" else "fallback check"}
    if scene=="lower":
        result["warm_ms"]={m:median(xs) for m,xs in samples.items()}
        result["cold_ms"]=cold
        result["proof_ms"]={m:median(xs) for m,xs in guard.items()}
        result["warm_samples_ms"]=samples
    return result


if __name__=="__main__":
    results={f"{s}-{k}":evaluate(s,k) for s,k in (("lower",1),("lower",2),("firewoods",1),("playground",1))}
    doc=HERE/"SCORE.json"
    if doc.exists():assert read(doc)==results
    else:doc.write_text(json.dumps(results,indent=2)+"\n",encoding="utf-8")
    for k,r in results.items(): print(k,r["mode"],r["calls"],{m:round(x,1) for m,x in r.get("warm_ms",{}).items()})
