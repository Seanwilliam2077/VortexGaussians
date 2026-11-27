"""Score the sixteen pinned PNGs against the captured native rest matte."""
import argparse
import gzip
import importlib.util
import json
from pathlib import Path

import numpy as np

from prepare import HERE, T109, T127, labels, sha


def require(condition, msg):
    if not condition:
        raise ValueError(msg)


def pick(passes):
    return next((brush for brush in ("light", "full") if passes[brush]), "neither")


def calculate(source, frames, local, capture):
    spec=importlib.util.spec_from_file_location("prior_score", T127/"score.py")
    prior_score=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior_score)
    prior=json.loads((T127/"evidence/SCORE.json").read_bytes())
    ref=json.loads((T109/"REFERENCE.json").read_bytes())["queries"]
    mask_ids=labels(source, frames)
    cap=json.loads(capture.read_bytes())
    require(cap["status"]=="complete" and len(cap["draws"])==7 and not cap["errors"],"Native run failure")
    rows=[]; material=[]; choices={}; histograms={}; views={}
    for cam in (0,124):
        all_opacity=None
        tags={}
        for key in ("eligible","light","full"):
            draw=next(r for r in cap["draws"] if r["camera"]==cam and r["kind"]==key and not r["repeat"])
            s=draw["stats"]
            require(s["tagCount"]==len(mask_ids[key]) and s["sites"]==34687 and
                    (s["sourceWidth"],s["sourceHeight"])==(940,528),"Draw input")
            for channel in ("eligible","all"):
                p=local/f"c{cam}-{key}-{channel}.f32"
                require(sha(p)==draw["hashes"][channel],"Captured array hash")
                v=np.fromfile(p,"<f4").reshape(264,470)
                require(np.isfinite(v).all() and v.min()>=0 and v.max()<=1.004,"Invalid mass map")
                if channel=="eligible":
                    tags[key]=v
                    expected=s["tagged"]
                else:
                    if all_opacity is None: all_opacity=v
                    require(np.array_equal(v,all_opacity),"All-opacity map changed between draws")
                    expected=s["total"]
                require(np.isclose(v.sum(dtype=np.float64),expected,rtol=1e-12),"Draw/host mass mismatch")
        shell=tags["eligible"].astype(np.float64)
        total=float(shell.sum())
        old_total=prior["reference_checks"][str(cam)]["raster_total"]
        require(total>0,"Undefined native target")
        views[str(cam)]=dict(native_total=total,previous_total=old_total,total_ratio=total/old_total,
                              all_opacity=float(all_opacity.sum(dtype=np.float64)))
        gas_votes={}; material_votes={}
        for old in (r for r in prior["comparisons"] if r["camera"]==cam):
            h,b=old["horizon"],old["brush"]
            tag=f"{b}-c{cam}-h{h}"
            pixels=[prior_score.block_sums(frames/f"{tag}-{v}.png") for v in ("full","wood")]
            contrasts=np.abs(pixels[0]-pixels[1]).max(axis=2)
            changed=contrasts>=64
            require(int(changed.sum())==old["changed_pixels"],"Historical contrast mask count changed")
            num=float(shell[changed].sum())
            masses=np.bincount(contrasts.ravel(),weights=shell.ravel(),minlength=1021)
            counts=np.bincount(contrasts.ravel(),minlength=1021)
            require(np.isclose(masses[64:].sum(),num,rtol=1e-12,atol=1e-10),"Contrast bins")
            histograms[tag]=dict(counts=counts.tolist(),weights=masses.tolist())
            passes=4*num>=total
            rows.append(dict(camera=cam,horizon=h,brush=b,changed_cells=int(changed.sum()),changed_mass=num,
                             fraction=num/total,previous_fraction=old["fraction"],passes=passes))
            if h==90: gas_votes[b]=passes
        for b,arm in (("light","AL"),("full","AF")):
            require((tags[b]<=shell+.004).all(),"Ignition projection exceeds eligible shell")
            num=float(tags[b].sum(dtype=np.float64))
            previous=next(r for r in ref if r["camera"]==cam and r["arm"]==arm)
            end_frame, _, hits, end_mass = previous["curve"][-1]
            require(end_frame==270 and hits==len(mask_ids[b]),"Material comparison deadline")
            passes=4*num>=total
            material.append(dict(camera=cam,brush=b,hit_sites=len(mask_ids[b]),native_hit_mass=num,
                                 fraction=num/total,previous_fraction=end_mass/previous["total"],passes=passes))
            material_votes[b]=passes
        choices[str(cam)]=dict(gas=pick(gas_votes),material=pick(material_votes),gas_votes=gas_votes,material_votes=material_votes)
    score=dict(schema="t140-rest-native-projection",capture_sha256=sha(capture),inputs_sha256=prior["source_sha256"],
               tag_counts={k:len(v) for k,v in mask_ids.items()},views=views,gas=rows,material=material,endpoint=choices)
    return score,histograms


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("source","frames","local"): p.add_argument(key,type=Path)
    p.add_argument("--output",type=Path,default=HERE/"evidence")
    args=p.parse_args()
    result,hist=calculate(args.source,args.frames,args.local,args.output/"CAPTURE.json")
    (args.output/"SCORE.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    (args.output/"CONTRAST.json.gz").write_bytes(gzip.compress(json.dumps(hist,separators=(",",":"),allow_nan=False).encode(),mtime=0))
    print(json.dumps(result["endpoint"]))
