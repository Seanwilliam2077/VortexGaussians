"""Verify the neutral preflight from its small receipts and pixel archives, without a device."""
import hashlib
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent


def require(condition,detail):
    if not condition:
        raise ValueError(detail)


def verify(folder):
    root=HERE/folder
    receipt=json.loads((root/"PREFLIGHT.json").read_bytes())
    outer=json.loads((root/"EXIT.json").read_bytes())
    phases=[json.loads(line) for line in (root/"PHASES.ndjson").read_bytes().splitlines()]
    require(outer["limit_s"]==360 and outer["elapsed_s"]>0,"Worker clock")
    if outer["status"]=="time_limit":
        require(outer["elapsed_s"]>=outer["limit_s"] and outer["exit"]!=0,"Invalid timeout receipt")
    else:
        require(outer["status"]=="returned" and outer["elapsed_s"]<outer["limit_s"],"Worker exit/clock")
    require(all(i["elapsed_s"]<=j["elapsed_s"] for i,j in zip(phases,phases[1:])),"Unordered phase ledger")
    require(receipt["restored_frame"]==1 and receipt["successor_equal"],"Native frame-1 resume")
    a,b=receipt["ordinary_successor"],receipt["resumed_successor"]
    require(a==b and a["frame"]==2 and a["gas"]["steps"]>0,"Neutral frame-2 comparison")
    require(set(("vel","p","scal")).issubset(a["gas"]) and set(("X","P","V","S","N","W","MP")).issubset(a["cloth"]),"Incomplete checkpoint witness")
    require(a["feedback_grid"]["shape"] and a["feedback_ready"],"Missing feedback grid")
    done={r["phase"] for r in phases if r["event"]=="returned"}
    if folder=="evidence":
        require(receipt["status"]=="error" and receipt["exception"]=="TypeError","Unpreserved initial failure")
        require("fire_render" in done and "fire_queue_fence" not in done and "emission_readback" not in done,"First attempt phase")
        return {"status":"first completion callback failed","elapsed_s":outer["elapsed_s"]}
    require({"fire_render","emission_readback"}<=done,"Missing native fire output")
    modes=["fire"]
    if outer["status"]=="time_limit":
        require("composite" not in receipt and "linear_composite_readback" not in done,"Unexplained timeout")
    else:
        require(receipt["status"]=="outputs_returned" and outer["exit"]==0,"Final output status")
        require({"composite_render","linear_composite_readback"}<=done,"Missing native composite")
        modes.append("composite")
    setup=receipt["checkpoint_observation"]
    require(setup["burning_vertices"]==0 and setup["feedback"]["ready"],"Neutral parent")
    require(0<setup["feedback"]["nonzero_words"]<=setup["feedback"]["array"]["shape"][0],"Missing frame-1 feedback")
    parent_differs=setup["feedback"]["array"]["sha256"]!=a["feedback_grid"]["sha256"]
    require(parent_differs,"Expected distinct frame-1 and frame-2 coupling grids on this fixture")
    for mode in modes:
        with np.load(root/(mode+".npz"),allow_pickle=False) as archive:
            data=archive["pixels"]
            native=receipt[mode]
            rgb=data[...,:3]
            require(data.shape==(180,320,4) and np.isfinite(data).all(),"Camera output: "+mode)
            require(native["array"]=={"dtype":str(data.dtype),"shape":list(data.shape),
                                     "sha256":hashlib.sha256(data.tobytes()).hexdigest()},"Array digest: "+mode)
            require(native["rgb_min"]==float(rgb.min()) and native["rgb_max"]==float(rgb.max())
                    and native["nonzero_rgb_pixels"]==int((rgb!=0).any(axis=2).sum()),"Range/count: "+mode)
    return {"status":"composite timeout" if outer["status"]=="time_limit" else receipt["status"],
            "elapsed_s":outer["elapsed_s"],"nonzero_feedback_words_at_checkpoint":
            setup["feedback"]["nonzero_words"],"equal_neutral_successor":a==b,
            "frame1_and_frame2_coupling_digests_differ":parent_differs,"fresh_engine_restore_tested":False,
            "pixels_sha256":{mode:receipt[mode]["array"]["sha256"] for mode in modes}}


if __name__=="__main__":
    print(json.dumps({folder:verify(folder) for folder in ("evidence","native-readback")},indent=2))
