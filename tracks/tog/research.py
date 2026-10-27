"""Portable task inspection. Default: plan/validate only, without importing Torch.

Simulation requires --execute. There is no optimizer, cache method, or target
generation from a hidden witness in this entry point.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from src.spec import load as load_spec


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def source_pins():
    manifest = json.loads((HERE/"source-manifest.json").read_text(encoding="utf-8"))
    for row in manifest["files"]:
        p = HERE/row["path"]
        if p.stat().st_size != row["bytes"] or sha(p) != row["sha256"]:
            raise ValueError("Source/fixture changed: "+row["path"])
    return manifest


def array_file(path, key=None):
    import numpy as np
    if Path(path).suffix.lower() == ".npz":
        with np.load(path, allow_pickle=False) as pack:
            if key is None or key not in pack.files:
                raise ValueError("NPZ needs the declared member: "+str(key))
            a = pack[key].copy()
    else:
        a = np.load(path, allow_pickle=False)
    if a.dtype.kind != "f" or not np.isfinite(a).all():
        raise ValueError("Only finite floating-point arrays accepted")
    return a.astype(np.float64, copy=False)


def target_array(brief_path, spec):
    from src.metrics import crop
    descriptor = spec["target"]
    path = (brief_path.parent/descriptor["path"]).resolve()
    if sha(path) != descriptor["sha256"]:
        raise ValueError("Target SHA256 mismatch")
    data = array_file(path, descriptor.get("key"))
    if descriptor["layout"] == "full_frames":
        expected = (len(spec["task"]["frames"]), 64, 64)
        if data.shape != expected:
            raise ValueError("Full target must already follow target.frame_ids: "+str(expected))
        data = crop(data, spec["task"]["edit_roi"])
    return data, path


def history(spec, brief):
    """Only saved-array arithmetic. Never imports Torch or re-simulates."""
    from src.metrics import evaluate
    base = HERE/"fixtures/r22"
    approved = array_file(base/"approved.npz", "frames")
    frames = array_file(base/"witness.npz", "frames")
    target, _ = target_array(brief, spec)
    result = evaluate(frames, approved, target, spec)
    original = json.loads((base/"summary.json").read_text(encoding="utf-8"))
    exact_outcome = (original["taskQualified"] is False and
                     result["semanticGate"]["passed"] is False and
                     result["semanticGate"]["frameCount"] == original["semantic"]["frameCount"] and
                     abs(result["semanticGate"]["maximumUpperShift"]-max(original["semantic"]["regions"]["upper"]["shift"])) < 1e-12)
    return {"status": "completed", "scope": "Offline saved R22 images only; no solver replay or new task qualification",
            "historicalTaskQualified": original["taskQualified"], "negativeFixturePreserved": exact_outcome,
            "historicalDecision": original["decision"], "metrics": result}


def pgm(path, image):
    """Lossy, top-left display preview; numerical outputs remain float64 arrays."""
    import numpy as np
    pixels = np.rint(np.clip(image[::-1], 0, 1)*255).astype(np.uint8)
    Path(path).write_bytes(f"P5\n{pixels.shape[1]} {pixels.shape[0]}\n255\n".encode()+pixels.tobytes())


def worker(args):
    import numpy as np
    # Torch is deliberately absent from every plan/validation/history path.
    import torch
    from src.core import SmokeModel
    from src.scene import initial_state
    from src.metrics import evaluate
    out, brief = args.out.resolve(), args.brief.resolve()
    report = {"status": "starting", "command": args.command, "rollouts": 0,
              "scope": "One control inspection, no optimization or performance benchmark",
              "createdUTC": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    pins = {}
    started = time.perf_counter()
    try:
        spec, validation = load_spec(brief, require_target=(args.command == "evaluate"))
        pins = {"source-manifest.json": sha(HERE/"source-manifest.json"), "brief": sha(brief)}
        source_pins()
        report.update(brief=spec, validation=validation, pinsBefore=pins.copy(), outputs={})
        torch.set_num_threads(args.threads)
        device = torch.device(args.device)
        cfg = dict(spec["model"]); cfg.pop("dtype")
        model = SmokeModel(**cfg, device=device, dtype=torch.float64)
        v0, rho0 = initial_state(model)
        report["environment"] = {"python": sys.version.split()[0], "numpy": np.__version__, "torch": torch.__version__,
            "device": str(device), "threads": torch.get_num_threads(), "dtype": "float64"}
        if device.type == "cuda":
            prop = torch.cuda.get_device_properties(device)
            report["environment"].update(gpu=prop.name, uuid=str(getattr(prop, "uuid", "unknown")))
        report["camera"] = model.camera
        report["model"] = spec["model"]
        report["modelSourceSHA256"] = sha(HERE/"src/core.py")

        def sync():
            if device.type == "cuda":
                torch.cuda.synchronize(device)

        def save(name, **values):
            a = {key: value.detach().cpu().numpy() if isinstance(value, torch.Tensor) else value for key, value in values.items()}
            with (out/name).open("xb") as f:
                np.savez(f, **a)
            report["outputs"][name] = {"sha256": sha(out/name), "bytes": (out/name).stat().st_size,
                "arrays": {k: {"shape": list(v.shape), "dtype": v.dtype.str,
                    "rawSHA256": hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest()} for k, v in a.items()}}

        if args.command == "approve":
            q = torch.zeros(spec["control"]["shape"], device=device, dtype=torch.float64)
        else:
            if args.controls is None or args.approved is None:
                raise ValueError("evaluate requires --controls and --approved")
            q_np = array_file(args.controls, "q")
            if q_np.shape != tuple(spec["control"]["shape"]):
                raise ValueError("Control array must be (4,3,8,8,8), not optimizer x")
            if (np.max(np.abs(q_np)) > spec["control"]["coefficient_max"] or
                np.sqrt(np.mean(q_np*q_np)) > spec["control"]["coefficient_rms"]):
                raise ValueError("Given controls exceed the declared coefficient budget; no clipping or rollout")
            pins["controls"] = sha(args.controls)
            pins["approved"] = sha(args.approved)
            # Bind approval frames to the model and the file actually generated.
            approval_report = args.approved.parent/"summary.json"
            previous = json.loads(approval_report.read_text(encoding="utf-8"))
            if (previous.get("status") != "completed" or previous.get("command") != "approve" or
                previous.get("model") != spec["model"] or previous["outputs"][args.approved.name]["sha256"] != pins["approved"] or
                previous.get("modelSourceSHA256") != report["modelSourceSHA256"] or not previous.get("sourcesUnchanged")):
                raise ValueError("Approved bundle/model/provenance mismatch")
            pins["approval_report"] = sha(approval_report)
            approved = array_file(args.approved, "frames")
            old_v, old_r = array_file(args.approved, "v0"), array_file(args.approved, "rho0")
            if old_v.shape != tuple(v0.shape) or old_r.shape != tuple(rho0.shape):
                raise ValueError("Approval initial-state shape mismatch")
            if max(np.max(np.abs(old_v-v0.cpu().numpy())), np.max(np.abs(old_r-rho0.cpu().numpy()))) > 1e-12:
                raise ValueError("Approval initial state differs from this explicit scene fork")
            target, target_path = target_array(brief, spec)
            pins["target"] = sha(target_path)
            q = torch.as_tensor(q_np, device=device, dtype=torch.float64)
        report["pinsBefore"] = pins.copy()
        write(out/"summary.json", report)
        with torch.no_grad():
            sync(); begin = time.perf_counter()
            result = model.rollout(q, v0, rho0)
            sync(); report["synchronizedRolloutSeconds"] = time.perf_counter()-begin
            report["rollouts"] = 1
            expanded = model._expand_controls(q)
            force_max = 0.0
            for step in range(model.steps):
                force = (expanded*model.time_weights[step, :, None, None, None, None]).sum(0)
                force_max = max(force_max, float(force.abs().max().cpu()))
        frames = result["frames"].cpu().numpy()
        finite = all(bool(torch.isfinite(x).all()) for x in (q, result["frames"], result["velocity"], result["density"]))
        physical = {"finite": finite, "densityMin": float(result["density"].min().cpu()),
                    "alphaMin": float(result["frames"].min().cpu()), "alphaMax": float(result["frames"].max().cpu())}
        physical["passed"] = finite and physical["densityMin"] >= 0 and physical["alphaMin"] >= 0 and physical["alphaMax"] <= 1
        control = {"coefficientMax": float(q.abs().max().cpu()), "coefficientRMS": float(q.square().mean().sqrt().cpu()),
                   "appliedForceMaxComponent": force_max}
        control["passed"] = (control["coefficientMax"] <= spec["control"]["coefficient_max"] and
                             control["coefficientRMS"] <= spec["control"]["coefficient_rms"] and
                             force_max <= spec["control"]["applied_force_max_component"])
        report.update(physical=physical, control=control)
        if not physical["passed"]:
            raise RuntimeError("Nonfinite or nonphysical numerical output")
        if args.command == "approve":
            save("approved.npz", v0=v0, rho0=rho0, frames=result["frames"], velocity=result["velocity"], density=result["density"])
            report["approvalMeaning"] = "Zero-control reference artifact; artistic approval still requires human review."
        else:
            report["metrics"] = evaluate(frames, approved, target, spec)
            report["declaredPixelAndControlGatesPassed"] = report["metrics"]["pixelQualityPassed"] and control["passed"]
            report["artistIntentValidated"] = False
            save("evaluated.npz", q=q, frames=result["frames"], velocity=result["velocity"], density=result["density"])
        for index in (0, 12, 24):
            name = f"preview-{index+16:02d}.pgm"
            pgm(out/name, frames[index])
            report["outputs"][name] = {"sha256": sha(out/name), "scope": "8-bit display preview, vertically flipped for top-left viewers"}
        report["status"] = "completed"
    except Exception as exc:
        report.update(status="failed", error=repr(exc), traceback=traceback.format_exc())
    finally:
        report["totalWallSecondsIncludingSetupReadbackIO"] = time.perf_counter()-started
        try:
            source_pins()
            after = {"source-manifest.json": sha(HERE/"source-manifest.json"), "brief": sha(brief)}
            if args.command == "evaluate" and "controls" in pins:
                after.update(controls=sha(args.controls), approved=sha(args.approved),
                             approval_report=sha(args.approved.parent/"summary.json"))
                if "target" in pins:
                    after["target"] = sha(target_path)
            report["pinsAfter"] = after
            report["sourcesUnchanged"] = bool(pins) and after == pins
            if not report["sourcesUnchanged"]:
                report.update(status="failed", provenanceError="Source/input changed")
        except Exception as exc:
            report.update(status="failed", provenanceError=repr(exc), sourcesUnchanged=False)
        write(out/"summary.json", report)
    return 0 if report["status"] == "completed" else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("validate", "approve", "evaluate", "history"), nargs="?", default="validate")
    p.add_argument("--brief", type=Path, default=HERE/"configs/artist-brief-001.json")
    p.add_argument("--controls", type=Path, help="NPY q or NPZ member q; raw control coefficients, never optimizer x")
    p.add_argument("--approved", type=Path, help="approved.npz and its adjacent summary.json from approve")
    p.add_argument("--out", type=Path, help="Fresh output directory; no overwrite")
    p.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    p.add_argument("--threads", type=int, default=4)
    p.add_argument("--require-target", action="store_true")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = p.parse_args()
    if args.command == "history":
        args.brief = HERE/"fixtures/r22/brief.json"
    spec, validation = load_spec(args.brief, args.require_target or (args.execute and args.command == "evaluate"))
    source_pins()
    if not 1 <= args.threads <= 64:
        p.error("threads must be in 1..64")
    if args.worker:
        if not args.execute or args.command not in ("approve", "evaluate") or args.out is None:
            p.error("Internal worker requires explicit simulation command and output")
        return worker(args)
    if args.command == "validate" or not args.execute:
        print(json.dumps({"status": "validated" if args.command == "validate" else "planned_not_executed", "command": args.command,
            "validation": validation, "taskId": spec["id"], "model": spec["model"], "target": spec["target"],
            "runtimeImported": False, "rollouts": 0}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "history":
        result = history(spec, args.brief)
        if args.out:
            args.out.mkdir(parents=True, exist_ok=False)
            write(args.out/"summary.json", result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["negativeFixturePreserved"] else 1
    if args.out is None:
        p.error("--execute requires --out FRESH_DIRECTORY")
    if args.command == "evaluate" and (args.controls is None or args.approved is None):
        p.error("evaluate requires --controls and --approved")
    args.out.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, "-B", str(Path(__file__).resolve()), args.command,
               "--brief", str(args.brief.resolve()), "--out", str(args.out.resolve()),
               "--device", args.device, "--threads", str(args.threads), "--execute", "--worker"]
    for flag, value in (("--controls", args.controls), ("--approved", args.approved)):
        if value is not None:
            command += [flag, str(value.resolve())]
    before = time.perf_counter()
    limit = spec["budget"]["wall_seconds"]
    supervisor = {"wallLimitSeconds": limit, "scope": "Whole worker, including imports, setup, one rollout and IO"}
    with (args.out/"stdout.log").open("wb") as stdout, (args.out/"stderr.log").open("wb") as stderr:
        try:
            proc = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=limit, check=False)
            supervisor.update(status="completed" if proc.returncode == 0 else "failed", returnCode=proc.returncode)
        except subprocess.TimeoutExpired:
            supervisor.update(status="timeout", returnCode=None)
    supervisor["wallSeconds"] = time.perf_counter()-before
    write(args.out/"supervisor.json", supervisor)
    print(json.dumps(supervisor, indent=2))
    return 0 if supervisor["status"] == "completed" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "rejected", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
