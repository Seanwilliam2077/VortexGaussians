"""Verify all prerequisite receipts and separate an unused descriptor from an actual stage dispatch."""
import argparse
from collections import Counter
import json
from pathlib import Path
from classic import HERE,LIMIT,render
from verify_labels import check


def verify(folder):
    base=check(folder,limit=LIMIT,compiled_on_construction=("main",))
    path=folder/"STAGE.ndjson"
    rows=[json.loads(line) for line in path.read_bytes().splitlines()] if path.is_file() else []
    compiled=[]
    requested=[]
    dispatched=[]
    for r in rows:
        e,a=r["entry"],r["action"]
        render.require(render.observe.KEYS[e]==r["key"],"Unexpected dispatched kernel")
        if a=="descriptor_deferred":
            render.require(e=="caustics" and e not in requested and r["source"]=="stage.wgsl" and
                           r["source_sha256"]==render.observe.SOURCE_SHA and len(r["bindings"])==39 and
                           r["workgroup"]==[64,1,1],"Invalid deferred descriptor")
            requested.append(e)
        elif a=="materialization_started":
            render.require(e=="caustics" and e in requested,"Unexpected on-demand compilation")
        elif a=="native_pipeline_returned":
            compiled.append(e)
        elif a in ("batch_run_started","batch_run_returned"):
            render.require(e in compiled and min(r["groups"])>0 and r["resources"]==39,
                           "Missing live native pipeline or dispatch")
            if a=="batch_run_returned":
                dispatched.append(e)
        else:
            raise ValueError(a)
    success=base["measurement"]["stage"]["worker_status"]=="complete"
    if success:
        native=json.loads((folder/"RESULT.json").read_bytes())
        render.require(requested==["caustics"] and "main" in compiled and "main" in dispatched and
                       native["neutral_frame2_matches_t130"] and native["stage_keys"]==render.observe.KEYS,
                       "Image without the required scene, keys and main dispatch")
    return dict(underlying=base,returned_stage_pipelines=compiled,deferred_descriptors=requested,
                completed_native_batch_calls=dict(Counter(dispatched)),
                classic_only_observation=("caustics" not in compiled) if success else None)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder",nargs="?",type=Path,default=HERE/"evidence")
    a=parser.parse_args()
    print(json.dumps(verify(a.folder),indent=2))
