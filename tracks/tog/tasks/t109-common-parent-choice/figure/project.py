"""Recreate the registered opacity measurement; omit all source appearance channels."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
TASK=HERE.parent
TASKS=TASK.parent
SPEC=importlib.util.spec_from_file_location("matte_raster",TASKS/"t107-visible-burn-progression/measure.py")
metrics=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(metrics)
sha=lambda f: hashlib.sha256(f.read_bytes()).hexdigest()


def native_labels():
    rows=metrics.read(TASK/"REFERENCE.json")["queries"]
    result={}
    for arm in ("AL","AF"):
        trace=metrics.read(TASK/f"evidence/native/{arm}-trace.json.gz")
        shot=metrics.read(TASK/"evidence/native/capture-report.json")["shots"][arm]
        base=set(shot["initial"]["ids"])|set(shot["edit"]["ids"])
        for r in trace[:180]: base.update(r["new_ids"])
        eligible=set(metrics.read(TASK/"shell.json.gz"))-base
        assert len(eligible)==2371
        hits=set(j for r in trace[180:270] for j in r["new_ids"]) & eligible
        assert len(hits)==next(q for q in rows if q["arm"]==arm)["curve"][-1][2]
        result[arm]=(eligible,hits)
    assert result["AL"][0]==result["AF"][0]
    return result


def project(source):
    np.set_printoptions(precision=10)
    local=HERE/"local";local.mkdir(exist_ok=True)
    ply,camera_file=source/"foreground.ply",source/"cameras.json"
    assert sha(camera_file)=="5cdd4605b0bf11970357c26e66ce3affb6c25ab2823171488fa41288ceb4a5c5"
    pos,cov,opacity=metrics.splats(ply)
    cameras={c["id"]:c for c in metrics.read(camera_file)}
    masks=native_labels()
    shell={a:m[0] for a,m in masks.items()}
    frames={a:np.full(len(pos),999) for a in shell}
    for a in shell: frames[a][list(masks[a][1])]=270
    rows=metrics.read(TASK/"REFERENCE.json")["queries"]
    sites=[p["index"] for p in metrics.read(TASK/"recipe.json")["picks"]]
    inputs=[ply,camera_file,TASK/"shell.json.gz",TASK/"REFERENCE.json",TASK/"evidence/native/capture-report.json",
            *(TASK/f"evidence/native/{a}-trace.json.gz" for a in shell)]
    report={"frame":270,"steps_after_edit":90,"source_sha256":{p.name:sha(p) for p in inputs},"views":{}}
    # The publication background uses only binned center counts. Neither color nor raw points leave this process.
    cell=.014
    voxels,n=np.unique(np.floor(pos/cell).astype("int32"),axis=0,return_counts=True)
    np.savez_compressed(local/"geometric-bins.npz",indices=voxels,count=n,cell=cell)
    for cam in (0,124):
        proj=metrics.projection(pos,cov,cameras[cam])
        weight,coverage,maps,_=metrics.raster(proj,opacity,shell,frames,sites)
        table=TASKS/f"t107-visible-burn-progression/evidence/weights-{cam}.json.gz"
        old=dict(metrics.read(table)["eligible_weights"])
        ids=np.array(sorted(shell["AL"]))
        np.testing.assert_allclose(weight[ids],[old[i] for i in ids],rtol=3e-12,atol=1e-11)
        shellmap=maps["AL"][0]; np.testing.assert_array_equal(maps["AF"][0],shellmap)
        stats={}
        for arm in shell:
            hit=np.array(sorted(masks[arm][1]))
            q=next(x for x in rows if x["arm"]==arm and x["camera"]==cam)
            total=int(np.floor(weight[ids]*1e6+.5).sum());mass=int(np.floor(weight[hit]*1e6+.5).sum())
            assert total==q["total"] and mass==q["deadline_mass"]
            np.testing.assert_allclose(shellmap.sum(),weight[ids].sum(),rtol=3e-13)
            np.testing.assert_allclose(maps[arm][1].sum(),weight[hit].sum(),rtol=3e-13)
            stats[arm]={"eligible_sites":int(len(ids)),"ignited_sites":int(len(hit)),"integer_total":total,"integer_burnt":mass,
                        "raster_total":float(shellmap.sum()),"raster_burnt":float(maps[arm][1].sum()),"percent":100*mass/total}
        np.savez_compressed(local/f"projection-{cam}.npz",shell=shellmap,light=maps["AL"][1],full=maps["AF"][1],coverage=coverage)
        report["views"][str(cam)]={"archive_weight_sha256":sha(table),"mass":stats}
    (HERE/"validation.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=TASK.parents[4]/"real-asset-ingest")
    project(p.parse_args().source)
