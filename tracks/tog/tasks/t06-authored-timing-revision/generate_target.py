"""One frozen CPU-only authored image transformation; no Torch/solver imports."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
TRACK = HERE.parent.parent


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def authenticate():
    rule = read(HERE/"RULE.json")
    # Only bytes are authenticated for D01 fixtures; witness arrays are never decoded.
    old = read(TRACK/"source-manifest.json")
    for row in old["files"]:
        p = TRACK/row["path"]
        if sha(p) != row["sha256"] or p.stat().st_size != row["bytes"]:
            raise RuntimeError("D01 changed: "+row["path"])
    asset = HERE/rule["input"]
    if sha(asset) != rule["input_sha256"]:
        raise RuntimeError("Approved input changed")
    files = {name: HERE/name for name in ("RULE.json", "PROTOCOL.md", "brief.template.json", "generate_target.py")}
    files.update({"D01/source-manifest.json": TRACK/"source-manifest.json", "approved.npz": asset})
    pins = {name: {"bytes": p.stat().st_size, "sha256": sha(p)} for name, p in files.items()}
    return rule, asset, pins


def previews(out, approved, target, rule, brief):
    import numpy as np
    from PIL import Image, ImageDraw
    scale = rule["visualization"]["scale"]
    side, header = 64*scale, 26
    steps = rule["visualization"]["frames"]
    limit = rule["visualization"]["signed_difference_range"][1]
    panels = {key: [] for key in ("approved", "target", "difference")}
    for step in steps:
        a, b = approved[step-16], target[step-16]
        delta = np.clip((b-a)/limit, -1, 1)
        rgb = np.stack((np.maximum(delta, 0), np.zeros_like(delta), np.maximum(-delta, 0)), -1)
        values = {"approved": np.repeat(a[..., None], 3, -1), "target": np.repeat(b[..., None], 3, -1), "difference": rgb}
        for name, value in values.items():
            raw = np.rint(np.clip(value[::-1], 0, 1)*255).astype(np.uint8)
            image = Image.fromarray(raw).resize((side, side), Image.Resampling.NEAREST)
            canvas = Image.new("RGB", (side, side+header), (28, 28, 28));canvas.paste(image, (0, header))
            draw = ImageDraw.Draw(canvas)
            label = "target - approved (-.25 blue / +.25 red)" if name == "difference" else name+" alpha [0,1]"
            draw.text((8, 7), f"frame {step} | {label}", fill="white")
            for roi, color in [(brief["task"]["edit_roi"], (255, 174, 40))]+[(r, (90, 225, 130)) for r in brief["task"]["protected_rois"]]:
                x0,y0,x1,y1=roi
                draw.rectangle((x0*scale, header+(64-y1)*scale, x1*scale-1, header+(64-y0)*scale-1), outline=color, width=1)
            for y in range(header, side+header, 12):
                draw.line((32*scale,y,32*scale,min(y+5,side+header-1)),fill=(150,150,150),width=1)
            panels[name].append(canvas)
    sheet = Image.new("RGB", (side*3, (side+header)*3+26), (28,28,28))
    for column, (name, images) in enumerate(panels.items()):
        strip = Image.new("RGB", (side, (side+header)*3), (28,28,28))
        for row, image in enumerate(images):
            strip.paste(image, (0, row*(side+header)))
            sheet.paste(image, (column*side, row*(side+header)))
        strip.save(out/(name+".png"))
    ImageDraw.Draw(sheet).text((8, sheet.height-19), "Image-authored development draft. A=4 defines the warp, NOT a measured centroid gate. No optimization or physical feasibility claim.", fill="white")
    sheet.save(out/"review-sheet.png")


def execute(out):
    import numpy as np
    import PIL
    rule, asset, pins = authenticate()
    freeze = read(out/"freeze.json")
    if freeze["pins"] != pins or set(p.name for p in out.iterdir()) != {"freeze.json"}:
        raise RuntimeError("Freeze mismatch or output already contains a run; no overwrite/retry")
    report = {"status": "starting", "createdUTC": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "scope": "One deterministic CPU image edit; no simulation, control search, Torch or GPU",
              "pinsBefore": pins, "freezeSHA256": sha(out/"freeze.json"), "outputs": {},
              "versions": {"python": sys.version.split()[0], "numpy": np.__version__, "Pillow": PIL.__version__}}
    start = time.perf_counter()
    try:
        with np.load(asset, allow_pickle=False) as z:
            approved = z[rule["input_key"]].copy()
        if approved.shape != tuple(rule["shape"]) or approved.dtype != np.dtype("float64") or not np.isfinite(approved).all():
            raise ValueError("Unexpected approved frames")
        if rule["amplitudes_output_pixels"] != [4.0]:
            raise ValueError("Only the frozen A=4 variant exists")
        S = lambda t: np.clip(t,0,1)**2*(3-2*np.clip(t,0,1))
        y,x = np.meshgrid(np.arange(64,dtype=np.float64)+.5, np.arange(64,dtype=np.float64)+.5, indexing="ij")
        temporal = S((np.asarray(rule["frame_ids"],dtype=np.float64)-rule["time_start"])/(rule["time_end"]-rule["time_start"]))
        spatial = S((y-rule["y_start"])/rule["y_ramp"])*S((x-rule["x_left"])/rule["x_left_ramp"])*(1-S((x-rule["x_right_start"])/rule["x_right_ramp"]))
        displacement = 4*temporal[:,None,None]*spatial[None]
        source_index = (x-.5)[None]-displacement
        floor = np.floor(source_index);frac=source_index-floor
        i0 = floor.astype(np.int64);i1=i0+1
        a0 = np.take_along_axis(approved, i0.clip(0,63), axis=2)
        a1 = np.take_along_axis(approved, i1.clip(0,63), axis=2)
        warped = a0*(1-frac)+a1*frac
        x0,y0,x1,y1=rule["roi"]
        target = approved.copy();target[:,y0:y1,x0:x1]=warped[:,y0:y1,x0:x1]
        roi_mask = np.zeros((64,64),dtype=bool);roi_mask[y0:y1,x0:x1]=True
        outside_exact = bool(np.array_equal(target[:,~roi_mask],approved[:,~roi_mask]))
        frame16_exact = bool(np.array_equal(target[0],approved[0]))
        if not (outside_exact and frame16_exact and np.isfinite(target).all() and (target>=0).all() and (target<=1).all()):
            raise RuntimeError("Generation invariant failed; no clipping permitted")
        for name, array in (("target-full.npy",target),("target-edit.npy",target[:,y0:y1,x0:x1])):
            with (out/name).open("xb") as f:np.save(f,array,allow_pickle=False)
            report["outputs"][name]={"sha256":sha(out/name),"bytes":(out/name).stat().st_size,"shape":list(array.shape),"dtype":array.dtype.str,
                "rawSHA256":hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()}
        brief = read(HERE/"brief.template.json")
        brief["target"].update(path="target-edit.npy",sha256=sha(out/"target-edit.npy"))
        write(out/"brief.json",brief)
        sys.path.insert(0,str(TRACK))
        from src.spec import validate
        from src.metrics import evaluate,crop
        validation=validate(brief,True)
        if not validation["valid"]:raise ValueError(validation["errors"])
        edit_target=target[:,y0:y1,x0:x1]
        zero=evaluate(approved,approved,edit_target,brief)
        # This is a property of an authored image, not a synthesized control solution.
        target_self=evaluate(target,approved,edit_target,brief)
        rms = np.sqrt(np.mean((edit_target-crop(approved,rule["roi"]))**2,axis=(-2,-1)))
        ref_rms = np.sqrt(np.mean(crop(approved,rule["roi"])**2,axis=(-2,-1)))
        difference=target-approved
        report.update(validation=validation,invariants={"outsideROIExact":outside_exact,"frame16Exact":frame16_exact,
            "finite":True,"alphaRange":[float(target.min()),float(target.max())],"same25FrameOrder":True},
            authoredTargetVsApproved={"absoluteRMS":rms.tolist(),"relativeRMSWithApprovedDenominator":(rms/ref_rms).tolist(),
                "nonzeroChangeFrames":int(np.count_nonzero(rms)),"maximumDefinedDisplacement":float(displacement.max()),
                "topInsideRowMaxAbsChangePerFrame":np.max(np.abs(difference[:,y1-1,x0:x1]),axis=-1).tolist(),
                "topOutsideRowMaxAbsChangePerFrame":np.max(np.abs(difference[:,y1,x0:x1]),axis=-1).tolist()},
            zeroControlMetrics=zero,zeroControlSummary={"editPassedFrameIds":[f for f,p in zip(rule["frame_ids"],zero["edit"]["passedFrames"]) if p],
                "editFailedFrameIds":[f for f,p in zip(rule["frame_ids"],zero["edit"]["passedFrames"]) if not p],
                "allProtectedFramesPass":all(r["passed"] for r in zero["protected"]),"coefficientAndForceBudget":"zero exactly, no new rollout"},
            authoredImageMetrics=target_self,artistRequirementValidated=False,physicalReachability="unknown",semanticQualification="not_defined; historical R22 2px gate not used")
        previews(out,approved,target,rule,brief)
        for name in ("brief.json","approved.png","target.png","difference.png","review-sheet.png"):
            report["outputs"][name]={"sha256":sha(out/name),"bytes":(out/name).stat().st_size}
        report["status"]="completed"
    except Exception as exc:
        report.update(status="failed",error=repr(exc),traceback=traceback.format_exc())
    finally:
        _,_,after=authenticate();report["pinsAfter"]=after;report["sourcesAndD01Unchanged"]=after==pins
        report["wallSecondsIncludingIO"]=time.perf_counter()-start
        if after!=pins:report["status"]="failed"
        write(out/"summary.json",report)
    print(json.dumps({"status":report["status"],"zeroControl":report.get("zeroControlSummary"),"invariants":report.get("invariants")},indent=2))
    return 0 if report["status"]=="completed" else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,default=HERE/"run-01")
    mode=parser.add_mutually_exclusive_group();mode.add_argument("--freeze",action="store_true");mode.add_argument("--execute",action="store_true")
    args=parser.parse_args();rule,asset,pins=authenticate()
    if args.freeze:
        args.out.mkdir(parents=True,exist_ok=False)
        write(args.out/"freeze.json",{"status":"frozen_before_target_generation","createdUTC":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"pins":pins,"rule":rule})
        print("Frozen; no target generated")
        return 0
    if args.execute:return execute(args.out)
    print(json.dumps({"status":"planned_not_executed","amplitudes":rule["amplitudes_output_pixels"],"inputSHA256":pins["approved.npz"]["sha256"],"scope":"CPU image edit only; freeze then exactly one execution"},indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
