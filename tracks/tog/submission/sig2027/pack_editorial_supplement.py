"""Package anonymous, portable native ignition records and native camera-edit comparisons and process repeats."""
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import zipfile

HERE=Path(__file__).resolve().parent
TASKS=HERE.parents[1]/"tasks"
def task(prefix):
    hits=list(TASKS.glob(prefix+"-*"))
    assert len(hits)==1
    return hits[0]
def read(p):
    b=p.read_bytes()
    return json.loads(gzip.decompress(b) if p.suffix==".gz" else b)
def serialized(value):
    return (json.dumps(value,separators=(",",":"),allow_nan=False)+"\n").encode()
def main():
    files={}
    def add(name,obj):
        raw=serialized(obj)
        assert not re.search(rb"(?:[A-Z]:[\\\\/]|https?://|/Users/|seanzjxiao|VortexGaussians)",raw,re.I),name
        files[name]=gzip.compress(raw,mtime=0) if name.endswith(".gz") else raw
    def dataset(label, native, arms, shells, cameras, horizon):
        cap=read(native/"capture-report.json")
        assert cap["status"]=="validated"
        values={}
        for cid,p in cameras.items():
            vals=dict(read(p)["eligible_weights"])
            union=set().union(*map(set,shells.values()))
            # Historical weight-only archive contains precisely the union of the old eligible IDs.
            used=sorted(union.intersection(vals))
            values[cid]=[[i,math.floor(vals[i]*1e6+.5)] for i in used]
        records={}
        for arm in arms:
            shot=cap["shots"][arm]
            trace=read(native/f"{arm}-trace.json.gz")
            assert [t["frame"] for t in trace]==list(range(1,361))
            records[arm]=dict(initial=shot["initial"]["ids"],stroke=shot["edit"]["ids"],
                              events=[t["new_ids"] for t in trace],parent=shot["pre_edit"]["hash"],endpoint=shot["end"]["hash"])
        add(label+".json.gz",dict(horizon=horizon,shells=shells,cameras=values,arms=records))
    old_w=task("t107")/"evidence"
    dataset("geometry-a-development", task("t86")/"public", ("AB","BA"),
            read(task("t87")/"PREDICTIONS.json.gz")["shell_ids"],{0:old_w/"weights-0.json.gz"},180)
    static_a=read(task("t109")/"shell.json.gz");static_b=read(task("t111")/"shell.json.gz")
    dataset("geometry-a-prospective",task("t109")/"evidence/native",("AL","AF"),dict(AL=static_a,AF=static_a),
            {c:old_w/f"weights-{c}.json.gz" for c in (0,124)},90)
    dataset("geometry-b-prospective",task("t111")/"evidence/native",("AL","AF"),dict(AL=static_b,AF=static_b),
            {c:task("t111")/f"weights-{c}.json.gz" for c in (0,153)},90)
    unseen=task("t121")
    shell=read(unseen/"shell.json.gz")
    dataset("geometry-b-lower-band",unseen/"evidence/native",("AL","AF"),dict(AL=shell,AF=shell),
            {c:unseen/f"weights-{c}.json.gz" for c in (76,230)},90)
    sessions=[]
    studies=[
        ("development-multi", "geometry-a-development", "single", task("t108")/"evidence/CAPTURE.json"),
        ("woodpile-candidates", "geometry-a-prospective", "single", task("t109")/"evidence/timing/CAPTURE.json"),
        ("playground-action", "geometry-b-prospective", "action", task("t111")/"evidence/timing/CAPTURE.json"),
        ("woodpile-action", "geometry-a-prospective", "action", task("t113")/"evidence/timing/CAPTURE.json"),
        ("sitewise-woodpile","geometry-a-development","single",task("t114")/"evidence/firewoods/CAPTURE.json"),
        ("sitewise-playground","geometry-b-prospective","action",task("t114")/"playground/evidence/CAPTURE.json"),
        ("cold-contact-woodpile","geometry-a-development","single",task("t116")/"evidence/firewoods/CAPTURE.json"),
    ]
    for asset,geometry in (("firewoods","geometry-a-prospective"),("playground","geometry-b-prospective")):
        for block in range(1,5):
            label=f"{asset}-{block}"
            studies.append((label,geometry,"action",task("t115")/"evidence"/label/"CAPTURE.json"))
    for asset,geometry in (("firewoods","geometry-a-prospective"),("playground","geometry-b-prospective")):
        for block in range(1,3):
            label=f"{asset}-{block}"
            studies.append(("transport-"+label,geometry,"action",task("t119")/"evidence"/label/"CAPTURE.json"))
    for block in range(1,5):
        studies.append((f"heldout-{block}","geometry-b-lower-band","action",
                        task("t121")/"evidence/corrected"/f"block-{block}"/"CAPTURE.json"))
    for scene,block,geometry in (("lower",1,"geometry-b-lower-band"),("lower",2,"geometry-b-lower-band"),
                                 ("firewoods",1,"geometry-a-prospective"),("playground",1,"geometry-b-prospective")):
        label=f"{scene}-{block}"
        studies.append(("equivalence-"+label,geometry,"action",task("t123")/"evidence"/label/"CAPTURE.json"))
    for label,dataset_name,operation,path in studies:
        cap=read(path)
        assert cap["status"]=="validated" and not cap["errors"]
        curves=[]
        if operation=="single" and "progress_audits" in next(iter(cap["arms"].values())):
            for arm,shot in cap["arms"].items():
                for method,v in shot["progress_audits"].items():
                    curves.append(dict(arm=arm,camera=0,method=method,curve=v["curve"],boundaries=v["boundaries"]))
        elif "flow_audits" in cap:
            for key,methods in cap["flow_audits"].items():
                arm,cid=key.split("/")
                for method,v in methods.items():
                    curves.append(dict(arm=arm,camera=int(cid),method=method,curve=v["curve"],boundaries=v["boundaries"]))
        elif label.startswith(("transport-","heldout-")):
            for audit,rows in cap["full_audits"].items():
                if "physical" in rows:
                    for shot in rows["curves"]:
                        for v in shot["views"]:
                            curves.append(dict(arm="A"+shot["pick"],camera=v["camera"],method=audit,
                                               curve=v["curve"],boundaries=rows["physical"]))
                else:
                    method,pick=audit.rsplit("_",1)
                    for v in rows["curves"]:
                        curves.append(dict(arm="A"+pick,camera=v["camera"],method=method,
                                           curve=v["curve"],boundaries={}))
        elif "full_audits" in cap:
            for pick,methods in cap["full_audits"].items():
                for method,trial in methods.items():
                    for v in trial["views"]:
                        curves.append(dict(arm="A"+pick,camera=v["camera"],method=method,curve=v["curve"],boundaries=trial["boundaries"]))
        name=label+"-calls.json.gz"
        add(name,dict(methods=cap["methods"],repeats=cap["repeats"],phases_ms=cap["phases_ms"],
                      runtime={k:cap["runtime"][k] for k in ("node","browser_version","playwright_version")},
                      queries=cap["queries"],curves=curves))
        sessions.append(dict(label=label,dataset=dataset_name+".json.gz",operation=operation,calls=name))
    add("sessions.json",sessions)
    add("native-camera-contrast.json.gz",read(task("t127")/"evidence/CONTRAST.json.gz"))
    files["verify.py"]=(HERE/"verify_editorial.py").read_bytes().replace(b"\r\n",b"\n")
    files["README.txt"]=("""Exact burn-progression editing queries

Extract all files and run python verify.py (Python 3.10+ standard library).
The verifier recomputes eligibility and every integer opacity crossing from native events and fixed camera weights.
It checks each warmup and timed reply, checks the retained full progression curves, reconstructs the requested
light-first decision, verifies short-circuit behavior, and prints directly comparable per-method median milliseconds.
L denotes a light stroke, F the full stroke. The 90-step cases compare both from a common first stroke and identical
initial target. The 180-step development cases use different first strokes. An event-free deadline is retained.
One unit of static weight is one millionth of a pixel-equivalent of front-to-back foreground opacity.
Single-candidate and complete-action sessions have different clocks. Action calls include restoring the initial parent
and can share one physical evolution across two camera readouts. Equivalence calls can infer the other result
from a single physical trajectory when its entire observed exterior is certified equal. The original held-out
physical-precheck session with a clock error in its independent auditing wrapper is excluded. Its failed
receipt and the corrected native-step audit are preserved separately in the research repository.
Eight source-image-free histograms record final native RGB contrast against drawing the same wood without gas.
The verifier reconstructs the fixed display cutoff, target mass and two light-first camera choices from the bins.
Each session records its own excluded warmup and number of measured rotations on one host. Camera construction and shot loading
are separate. Full-precision 3D geometry is externally sourced. This bundle verifies event observations and latency
aggregation, not raster construction, native particle dynamics or independent performance reproduction.
""" ).encode()
    add("MANIFEST.json",{k:hashlib.sha256(v).hexdigest() for k,v in sorted(files.items())})
    out=HERE/"editorial-supplement.zip"
    with zipfile.ZipFile(out,"w") as z:
        for name,b in sorted(files.items()):
            item=zipfile.ZipInfo(name,(2026,11,25,0,0,0))
            item.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(item,b)
    print(out.name,out.stat().st_size,hashlib.sha256(out.read_bytes()).hexdigest())
if __name__=="__main__":
    main()
