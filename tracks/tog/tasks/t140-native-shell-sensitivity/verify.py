"""Verify the captured opacity totals, original event counts and nonspatial contrast bins."""
import gzip
import hashlib
import json
from math import fsum, isclose
from pathlib import Path

HERE=Path(__file__).resolve().parent
E=HERE/"evidence"


def read(path):
    return json.loads(path.read_bytes())


def need(value, reason):
    if not value: raise ValueError(reason)


def check():
    cap=read(E/"CAPTURE.json")
    score=read(E/"SCORE.json")
    previous=read(HERE.parent/"t127-woodpile-native-camera/evidence/SCORE.json")
    material=read(HERE.parent/"t109-common-parent-choice/REFERENCE.json")["queries"]
    hist=json.loads(gzip.decompress((E/"CONTRAST.json.gz").read_bytes()))
    need(score["capture_sha256"]==hashlib.sha256((E/"CAPTURE.json").read_bytes()).hexdigest(),"Capture digest")
    need(cap["status"]=="complete" and not cap["errors"] and cap["wall_ms"]<=180000,"Capture status")
    draws=cap["draws"]
    expected=[(c,k,False) for c in (0,124) for k in ("eligible","light","full")]+[(0,"eligible",True)]
    need([(d["camera"],d["kind"],d["repeat"]) for d in draws]==expected,"Draw order")
    need(draws[0]["hashes"]==draws[-1]["hashes"],"Repeated camera hashes")
    need(cap["source"]["asset"]==previous["source_sha256"]["foreground.ply"] and
         cap["source"]["cameras"]==previous["source_sha256"]["cameras.json"],"Source inputs")
    need(score["tag_counts"]=={"eligible":2371,"light":190,"full":493},"Tag counts")
    for d in draws:
        s=d["stats"]
        need(s["sites"]==34687 and s["tagCount"]==score["tag_counts"][d["kind"]] and
             s["sourceWidth"]==940 and s["sourceHeight"]==528 and s["dynamic"]==s["suppressed"]==0 and
             s["greenAlpha"]<=.004 and s["exceed"]<=.004 and s["clock"]==draws[0]["stats"]["clock"],"Draw fields")
    for cam in (0,124):
        take={r["kind"]:r for r in draws if r["camera"]==cam and not r["repeat"]}
        need(len({d["hashes"]["all"] for d in take.values()})==1,"View opacity invariant")
        total=take["eligible"]["stats"]["tagged"]
        need(isclose(score["views"][str(cam)]["native_total"],total,rel_tol=1e-12),"Native denominator")
        need(score["views"][str(cam)]["previous_total"]==previous["reference_checks"][str(cam)]["raster_total"],"Prior denominator")
        votes={"gas":{},"material":{}}
        for old in (r for r in previous["comparisons"] if r["camera"]==cam):
            horizon,brush=old["horizon"],old["brush"]
            row=next(r for r in score["gas"] if (r["camera"],r["horizon"],r["brush"])==(cam,horizon,brush))
            bins=hist[f"{brush}-c{cam}-h{horizon}"]
            counts,weights=bins["counts"],bins["weights"]
            need(len(counts)==len(weights)==1021 and sum(counts)==470*264 and min(counts)>=0 and min(weights)>=0,"Bins")
            need(sum(counts[64:])==old["changed_pixels"]==row["changed_cells"],"Fixed mask area")
            num=fsum(weights[64:])
            need(isclose(fsum(weights),total,rel_tol=1e-12) and isclose(num,row["changed_mass"],abs_tol=1e-10)
                 and isclose(row["fraction"],num/total,abs_tol=1e-12) and row["previous_fraction"]==old["fraction"]
                 and row["passes"]==(4*num>=total),"Gas score")
            if horizon==90: votes["gas"][brush]=row["passes"]
        for brush,arm in (("light","AL"),("full","AF")):
            old=next(r for r in material if r["camera"]==cam and r["arm"]==arm)
            row=next(r for r in score["material"] if r["camera"]==cam and r["brush"]==brush)
            mass=take[brush]["stats"]["tagged"]
            need(row["hit_sites"]==old["curve"][-1][2] and old["curve"][-1][0]==270 and
                 row["previous_fraction"]==old["curve"][-1][3]/old["total"] and
                 isclose(row["native_hit_mass"],mass,rel_tol=1e-12) and isclose(row["fraction"],mass/total,rel_tol=1e-12)
                 and row["passes"]==(4*mass>=total),"Material score")
            votes["material"][brush]=row["passes"]
        for kind, passed in votes.items():
            end=score["endpoint"][str(cam)]
            choose=next((b for b in ("light","full") if passed[b]),"neither")
            need(end[kind]==choose and end[kind+"_votes"]==passed,"Endpoint choice")
    need(len(score["gas"])==len(hist)==8 and len(score["material"])==4,"Complete inventory")
    return {"native_draws":len(draws),"original_image_pairs":len(hist),"material_endpoints":4,"choices":score["endpoint"]}


if __name__=="__main__":
    print(json.dumps(check(),indent=2))
