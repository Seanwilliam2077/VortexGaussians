"""T05 ordinary 76-constraint cold-start solve on the same development task.

Reads approved initial fields, T02 target and authenticated R20 core; no former controls.
It never imports scene.py, opens a witness trajectory, or uses a hidden target state.
No rank model, response cache, NumPy BLAS, or parameter search is used.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parent


def authenticate():
    """All required files are relative to this task, including the fixed T02 input."""
    freeze = json.loads((ROOT / "freeze.json").read_text(encoding="utf-8"))
    pins = {}
    for name, row in freeze["files"].items():
        path = (ROOT / row["path"]).resolve()
        actual = {"path": str(path), "sha256": file_sha(path), "bytes": path.stat().st_size}
        if actual["sha256"] != row["sha256"] or actual["bytes"] != row["bytes"]:
            raise ValueError("Frozen source/input changed: " + name)
        pins[name] = actual
    pins["freeze.json"] = {"path": str(ROOT / "freeze.json"), "sha256": file_sha(ROOT / "freeze.json"),
                           "bytes": (ROOT / "freeze.json").stat().st_size}
    return pins


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def crop(frames, roi):
    x0, y0, x1, y1 = roi
    return frames[..., y0:y1, x0:x1]


class Objective:
    """Pure tensor objective; forward rollout and budget are caller-owned."""

    def __init__(self, torch, approved, target, task, baseline, arm):
        self.torch, self.approved, self.target = torch, approved, target
        self.task, self.baseline = task, baseline
        if arm != "framewise_joint":
            raise ValueError("Unknown arm")
        self.arm = arm
        self.mask = approved.new_ones(76)
        self.protected = [crop(approved, roi).detach() for roi in task["protected_rois"]]
        self.protected_scales = [ref.square().mean((-2, -1)).sqrt() for ref in self.protected]
        self.protected_tau = [(scale * task["protect_relative"]).clamp_max(task["protect_absolute"])
                              for scale in self.protected_scales]
        self.target_scale = target.square().mean((-2, -1)).sqrt()
        self.target_tau = (self.target_scale * task["edit_relative"]).clamp_max(task["edit_absolute"])
        if not all(bool((scale >= task["signal_min"]).all()) for scale in self.protected_scales + [self.target_scale]):
            raise ValueError("Fixed approved/target ROI signal below required minimum")
        if tuple(target.shape) != tuple(crop(approved, task["edit_roi"]).shape):
            raise ValueError("Target must contain only the declared edit ROI")

    def control(self, x):
        return self.task["coefficient_max"] * x.tanh()

    def terms(self, q, frames):
        pmse = [(crop(frames, roi) - reference).square().mean((-2, -1))
                for roi, reference in zip(self.task["protected_rois"], self.protected)]
        emse = (crop(frames, self.task["edit_roi"]) - self.target).square().mean((-2, -1))
        constraints = self.torch.cat([mse / tau.square() - 1 for mse, tau in zip(pmse, self.protected_tau)] +
            [emse / self.target_tau.square() - 1] +
            [(q.square().mean() / self.task["coefficient_rms"]**2 - 1).reshape(1)])
        edit = (emse / self.target_tau.square()).mean()
        regularizer = self.baseline["regularizer_weight"] * (q / self.baseline["regularizer_scale"]).square().mean()
        return {"constraints": constraints, "edit": edit, "regularizer": regularizer,
                "protected_mse": pmse, "edit_mse": emse}

    def penalty_terms(self, terms, multipliers, penalty):
        constraints = terms["constraints"]
        branch = multipliers + penalty * constraints
        raw = (branch.clamp_min(0).square() - multipliers.square()) / (2 * penalty)
        return raw, raw*self.mask, branch

    def loss(self, terms, multipliers, penalty):
        _, effective, _ = self.penalty_terms(terms, multipliers, penalty)
        return terms["edit"] + terms["regularizer"] + effective.sum()


class ClosureBudgetExhausted(RuntimeError):
    pass


def reuse_qualification(pins, manifest, np):
    """Authenticate the prior G0; do not import Torch or evaluate the model."""
    start = time.perf_counter()
    previous = json.loads(Path(pins["T04-result-summary.json"]["path"]).read_text(encoding="utf-8"))
    old_config = json.loads(Path(pins["T04-config.json"]["path"]).read_text(encoding="utf-8"))
    if previous["status"] != "completed" or not previous["sourcesAndInputsUnchanged"]:
        raise ValueError("Prior qualification run was not completed with unchanged sources")
    for old_name, current_name in (("runner.py", "T04-runner.py"), ("config.json", "T04-config.json"),
                                   ("freeze.json", "T04-freeze.json"), ("core.py", "core.py"),
                                   ("approved.npz", "approved.npz"), ("target-edit.npy", "target-edit.npy"),
                                   ("brief.json", "brief.json")):
        if previous["pins"][old_name]["sha256"] != pins[current_name]["sha256"]:
            raise ValueError("Prior qualification source/input mismatch: " + old_name)
    for key in ("model", "task", "constraint_order", "array_manifest", "expected_gpu_uuid"):
        prior_value = old_config[key]
        # The old x was a solve-only input, never a G0 input. This worker does
        # not open that file; G0 used its fixed independent random x.
        if key == "array_manifest":
            prior_value = {k:v for k,v in prior_value.items() if k != "warm_x"}
        if prior_value != manifest[key]:
            raise ValueError("Qualified configuration changed: " + key)
    for key, value in old_config["baseline"].items():
        if key != "start_policy" and manifest["baseline"].get(key) != value:
            raise ValueError("Qualified baseline numerical configuration changed: " + key)
    old_tree = ast.parse(Path(pins["T04-runner.py"]["path"]).read_text(encoding="utf-8"))
    new_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    ast_checks = {}
    for name in ("Objective", "acceptance", "force_stats"):
        nodes = []
        for tree in (old_tree, new_tree):
            found = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name]
            if len(found) != 1:
                raise ValueError("Expected one qualified AST node: " + name)
            nodes.append(ast.dump(found[0], include_attributes=False))
        ast_checks[name] = nodes[0] == nodes[1]
    if not all(ast_checks.values()):
        raise ValueError("Qualified objective/acceptance/force AST differs")
    q = previous["qualification"]
    qc = manifest["baseline"]["qualification"]
    if (q["status"] != "completed" or not q["passed"] or q["rolloutCount"] != 9 or q["backwardCalls"] != 1 or
        set(q["arms"]) != {"framewise_joint"}):
        raise ValueError("Prior scalar qualification incomplete")
    arm = q["arms"]["framewise_joint"]
    if (not arm["passed"] or not arm["finiteAnalytic"] or not arm["allEffectivePHRBranchesActive"] or
        arm["effectiveConstraintCount"] != 76 or arm["minimumActivePHRBranchMargin"] <= 0 or
        not math.isfinite(arm["minimumActivePHRBranchMargin"]) or not math.isfinite(arm["loss"]) or
        len(arm["directions"]) != qc["directions"]):
        raise ValueError("Prior analytic/branch qualification failed")
    errors = []
    for index, direction in enumerate(arm["directions"]):
        gd = direction["gradientDotDirection"]
        if direction["index"] != index or not direction["passed"] or not math.isfinite(gd):
            raise ValueError("Prior derivative direction mismatch")
        if [d["h"] for d in direction["finiteDifferences"]] != qc["steps"]:
            raise ValueError("Prior finite-difference steps differ")
        for d in direction["finiteDifferences"]:
            fd = (d["plus"] - d["minus"]) / (2*d["h"])
            relative = abs(fd-gd)/max(abs(gd), qc["denominator_floor"])
            if (not all(math.isfinite(v) for v in (d["plus"], d["minus"], fd, relative)) or
                fd != d["fd"] or relative != d["relativeError"] or relative > qc["relative_gate"] or not d["passed"]):
                raise ValueError("Prior stored finite-difference arithmetic/gate mismatch")
            errors.append(relative)
    proof_meta = json.loads(Path(pins["g0-proof.json"]["path"]).read_text(encoding="utf-8"))
    original_raw = json.loads(Path(pins["T04-raw-run-manifest.json"]["path"]).read_text(encoding="utf-8"))
    if (proof_meta["schema"] != "t05-partial-g0-proof-v1" or
        proof_meta["sourceManifestSHA256"] != pins["T04-raw-run-manifest.json"]["sha256"] or
        proof_meta["sourceRunnerSHA256"] != pins["T04-runner.py"]["sha256"] or
        proof_meta["sourceSummarySHA256"] != pins["T04-result-summary.json"]["sha256"] or
        proof_meta["producerSHA256"] != pins["prepare_qualification_proof.py"]["sha256"] or
        proof_meta["proof"]["sha256"] != pins["g0-proof.npz"]["sha256"] or
        proof_meta["proof"]["bytes"] != pins["g0-proof.npz"]["bytes"]):
        raise ValueError("G0 compact proof provenance mismatch")
    names = ["qualification/analytic.npz"] + [f"qualification/direction-{d}.npz" for d in range(2)]
    names += [f"qualification/probe-{d}-{h}-{s}.npz" for d in range(2) for h in range(2) for s in ("plus", "minus")]
    if (set(proof_meta["files"]) != set(names) or
        {n for n in original_raw["files"] if n.startswith("qualification/")} != set(names)):
        raise ValueError("G0 proof must contain only the 11 qualification files")
    values, key_set = {}, set()
    with np.load(pins["g0-proof.npz"]["path"], allow_pickle=False) as packed:
        for name in names:
            row = proof_meta["files"][name]
            original = original_raw["files"][name]
            retained = set(original["arrays"]) - {"frames"}
            if (row["original"] != original or set(row["packedKeys"]) != retained or
                row["omittedArrays"] != (["frames"] if "frames" in original["arrays"] else [])):
                raise ValueError("G0 proof source descriptor mismatch")
            values[name] = {}
            for key, packed_key in row["packedKeys"].items():
                if packed_key in key_set:
                    raise ValueError("Duplicate proof array alias")
                key_set.add(packed_key)
                value = packed[packed_key]
                descriptor = {"shape": list(value.shape), "dtype": value.dtype.str,
                    "rawSHA256": hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()}
                if descriptor != original["arrays"][key] or not np.isfinite(value).all():
                    raise ValueError("G0 proof raw hash/finite mismatch: " + name + ":" + key)
                values[name][key] = value
        if set(packed.files) != key_set:
            raise ValueError("Unexpected compact proof arrays")
    analytic = values["qualification/analytic.npz"]
    lam, rho, mask = analytic["multipliers"], float(analytic["penalty"]), analytic["mask"]
    if (lam.shape != (76,) or mask.shape != (76,) or not np.all(lam == qc["multiplier"]) or
        not np.all(mask == 1) or rho != qc["penalty"]):
        raise ValueError("G0 proof multiplier/mask/rho mismatch")
    branch = lam + rho * analytic["constraints"]
    if not np.all(branch > 0):
        raise ValueError("G0 proof contains inactive analytic PHR branch")

    def proof_loss(row):
        c = row["constraints"]
        edit = np.mean(c[50:75] + 1)
        regularizer = manifest["baseline"]["regularizer_weight"] * np.mean((row["q"] / manifest["baseline"]["regularizer_scale"])**2)
        phr = (np.maximum(0, lam + rho*c)**2 - lam**2) / (2*rho)
        return float(edit + regularizer + np.sum(phr*mask))

    scalar_differences = []

    def check_scalar(actual, stored):
        # CPU/GPU reduction order need not be bitwise equal. This is a
        # record-consistency tolerance; the original FD gate is unchanged.
        if not math.isclose(actual, stored, rel_tol=1e-12, abs_tol=1e-10):
            raise ValueError("G0 proof scalar differs from authenticated record")
        scalar_differences.append(abs(actual-stored))

    check_scalar(proof_loss(analytic), arm["loss"])
    check_scalar(float(np.min(branch)), arm["minimumActivePHRBranchMargin"])
    raw_errors = []
    for d, direction in enumerate(arm["directions"]):
        vector = values[f"qualification/direction-{d}.npz"]["direction"]
        dot = float(np.sum(analytic["gradient"] * vector))
        check_scalar(dot, direction["gradientDotDirection"])
        for h_index, record in enumerate(direction["finiteDifferences"]):
            plus = proof_loss(values[f"qualification/probe-{d}-{h_index}-plus.npz"])
            minus = proof_loss(values[f"qualification/probe-{d}-{h_index}-minus.npz"])
            check_scalar(plus, record["plus"]); check_scalar(minus, record["minus"])
            finite_difference = (plus-minus)/(2*record["h"])
            error = abs(finite_difference-dot)/max(abs(dot), qc["denominator_floor"])
            if not math.isfinite(error) or error > qc["relative_gate"]:
                raise ValueError("Reused raw G0 scalar derivative gate failed")
            raw_errors.append(error)
    return {"status": "reused_authenticated", "passed": True, "rolloutCount": 0, "backwardCalls": 0,
        "scope": "Authenticated prior T04 scalar G0, not a new AD experiment; no prior optimization arrays opened",
        "sourceReportSHA256": pins["T04-result-summary.json"]["sha256"], "ASTExact": ast_checks,
        "recomputedStoredFDErrors": errors, "gate": qc["relative_gate"],
        "compactProof": {"sha256": pins["g0-proof.npz"]["sha256"], "bytes": pins["g0-proof.npz"]["bytes"],
            "originalFileCount": len(names), "verifiedRawArrayCount": len(key_set), "rawScalarFDErrors": raw_errors,
            "maximumScalarRecordDifference": max(scalar_differences),
            "scope": "All 25 non-frame G0 arrays authenticated against original raw SHA. Scalar PHR recomposed from saved q/constraints and gradient-dot-direction; no new forward, AD, image-to-constraint or force evaluation. Nine original frame arrays are omitted."},
        "expectedEnvironment": previous["environment"],
        "priorCost": {"rollouts": 9, "backwardCalls": 1,
                      "wallSecondsIncludingEvidenceIO": q["wallSecondsIncludingEvidenceIO"],
                      "scope": "Existing development qualification; not charged as new online forward work"},
        "authenticationSeconds": time.perf_counter()-start}


def execute(args):
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    report = {"status": "starting", "createdUTC": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "Ordinary 76-constraint cold start on the fixed T02 development input. Reuses authenticated G0 qualification, never previous controls or states; not holdout or statistical speedup.",
        "armOrder": ["framewise_joint"], "raw": {}, "arms": [], "qualification": {"status": "not_started"}}
    pins = {}

    def publish():
        tmp = out / "summary.partial.json"
        tmp.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        os.replace(tmp, out / "summary.json")

    def stage(name):
        report["stage"] = name
        publish()
        print(f"baseline: {name}", flush=True)

    try:
        stage("authenticate_inputs")
        manifest_path = ROOT / "config.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        pins = authenticate()
        core_path = Path(pins["core.py"]["path"])
        report["pinsBefore"] = pins
        report["configuration"] = manifest
        if os.environ.get("MKL_THREADING_LAYER") != "SEQUENTIAL":
            raise RuntimeError("Worker requires declared local MKL threading policy")
        dll_path = Path(sys.prefix) / "Library" / "bin"
        dll_handle = os.add_dll_directory(str(dll_path)) if os.name == "nt" and dll_path.is_dir() else None
        report["runtimePolicy"] = {"MKL_THREADING_LAYER": os.environ.get("MKL_THREADING_LAYER"),
            "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"), "dllDirectory": str(dll_path),
            "directoryHandleRetained": dll_handle is not None, "python": sys.executable}
        stage("authenticate_reused_G0_before_torch")
        import numpy as np
        report["qualification"] = reuse_qualification(pins, manifest, np)
        publish()
        stage("import_torch_after_reused_G0_authenticated")
        import torch
        torch.set_num_threads(4)
        config, task = manifest["baseline"], manifest["task"]
        if task["ids"] != ["T02"] or config["sessions"] != 1:
            raise ValueError("Only the fixed single-T02 framewise revision is implemented")
        with np.load(pins["approved.npz"]["path"], allow_pickle=False) as packed:
            if set(packed.files) != {"v0", "rho0", "frames"}:
                raise ValueError("Unexpected approved bundle member")
            arrays = {name: packed[key].copy() for name, key in
                      (("v0", "v0"), ("rho0", "rho0"), ("approved", "frames"))}
        arrays["target_T02"] = np.load(pins["target-edit.npy"]["path"], allow_pickle=False)
        if set(manifest["array_manifest"]) != set(arrays):
            raise ValueError("Unexpected input schema")
        for name, value in arrays.items():
            descriptor = manifest["array_manifest"][name]
            if (list(value.shape) != descriptor["shape"] or value.dtype.str != descriptor["dtype"] or
                hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest() != descriptor["sha256"] or
                not np.isfinite(value).all()):
                raise RuntimeError(f"Array authentication/finite failure: {name}")
        brief = json.loads(Path(pins["brief.json"]["path"]).read_text(encoding="utf-8"))
        if (brief["target"]["layout"] != "edit_roi" or brief["target"]["frame_ids"] != task["accepted_steps"] or
            brief["target"]["sha256"] != pins["target-edit.npy"]["sha256"] or brief["task"]["semantic_gate"] is not None or
            brief["task"]["edit_roi"] != task["edit_roi"] or brief["task"]["protected_rois"] != task["protected_rois"] or
            brief["model"] != manifest["model"]):
            raise ValueError("T02 brief/config contract mismatch")
        spec = importlib.util.spec_from_file_location("t05_authenticated_core", core_path)
        core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(core)
        device = torch.device(args.device)
        model_config = dict(manifest["model"])
        if model_config.pop("dtype") != "float64":
            raise ValueError("Frozen baseline is float64")
        stage("construct_shared_model")
        model = core.SmokeModel(**model_config, dtype=torch.float64, device=device)
        data = {name: torch.as_tensor(value, device=device, dtype=torch.float64) for name, value in arrays.items()}
        del arrays
        v0, rho0, approved = data["v0"], data["rho0"], data["approved"]
        objectives = {arm: Objective(torch, approved, data["target_T02"], task, config, arm) for arm in report["armOrder"]}
        report["camera"] = model.camera
        report["environment"] = {"torch": torch.__version__, "numpy": np.__version__,
            "torchBuildCUDA": torch.version.cuda, "dtype": "float64", "threads": torch.get_num_threads(), "device": str(device)}
        if device.type == "cuda":
            properties = torch.cuda.get_device_properties(device)
            report["environment"].update(gpuName=properties.name, uuid=str(getattr(properties, "uuid", "unknown")),
                                          totalDeviceMemoryBytes=properties.total_memory)
            expected_uuid = manifest["expected_gpu_uuid"].removeprefix("GPU-").lower()
            if str(getattr(properties, "uuid", "unknown")).removeprefix("GPU-").lower() != expected_uuid:
                raise RuntimeError("Actual CUDA device UUID differs from frozen device")
            torch.cuda.reset_peak_memory_stats(device)
        expected_environment = report["qualification"]["expectedEnvironment"]
        for key in ("torch", "numpy", "torchBuildCUDA", "dtype", "threads", "device", "uuid"):
            if report["environment"].get(key) != expected_environment.get(key):
                raise RuntimeError("Runtime differs from reused G0 qualification: " + key)

        def sync():
            if device.type == "cuda":
                torch.cuda.synchronize(device)

        def memory():
            if device.type != "cuda":
                return {"scope": "CPU process peak not measured"}
            return {"scope": "Torch allocator, not complete process/device peak",
                "allocatedBytes": torch.cuda.memory_allocated(device), "reservedBytes": torch.cuda.memory_reserved(device),
                "peakAllocatedBytes": torch.cuda.max_memory_allocated(device), "peakReservedBytes": torch.cuda.max_memory_reserved(device)}

        def raw_save(name, **values):
            path = out / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                raise FileExistsError(path)
            raw = {key: (value.detach().cpu().numpy() if isinstance(value, torch.Tensor) else np.asarray(value))
                   for key, value in values.items()}
            if not all(np.isfinite(value).all() for value in raw.values()):
                raise RuntimeError(f"Nonfinite raw result {name}")
            with path.open("xb") as f:
                np.savez(f, **raw)
            report["raw"][name] = {"sha256": file_sha(path), "bytes": path.stat().st_size,
                "arrays": {key: {"shape": list(value.shape), "dtype": value.dtype.str,
                    "rawSHA256": hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()} for key, value in raw.items()}}

        def scalar(t):
            return float(t.detach().cpu())

        def vector(t):
            return t.detach().cpu().tolist()

        def force_stats(q):
            expanded = model._expand_controls(q)
            maximum = q.new_zeros(())
            square_sum = q.new_zeros(())
            for step in range(model.steps):
                force = (expanded * model.time_weights[step, :, None, None, None, None]).sum(0)
                maximum = torch.maximum(maximum, force.abs().max())
                square_sum = square_sum + force.square().sum()
            return maximum, (square_sum / (model.steps * 3 * model.n**3)).sqrt()

        def acceptance(objective, x, frames, final_velocity, final_density):
            q = objective.control(x)
            terms = objective.terms(q, frames)
            force_max, force_rms = force_stats(q)
            protected_rows = []
            for index, (mse, scale) in enumerate(zip(terms["protected_mse"], objective.protected_scales)):
                absolute, relative = mse.sqrt(), mse.sqrt() / scale
                passed = (absolute <= task["protect_absolute"]) & (relative <= task["protect_relative"]) & (scale >= task["signal_min"])
                protected_rows.append({"roi": index, "absoluteRMS": vector(absolute), "relativeRMS": vector(relative),
                    "referenceRMS": vector(scale), "passedFrames": vector(passed), "passed": bool(passed.all())})
            edit_absolute = terms["edit_mse"].sqrt()
            edit_relative = edit_absolute / objective.target_scale
            edit_pass = ((edit_absolute <= task["edit_absolute"]) & (edit_relative <= task["edit_relative"]) &
                         (objective.target_scale >= task["signal_min"]))
            finite = all(bool(torch.isfinite(t).all()) for t in (x, q, frames, final_velocity, final_density, terms["constraints"], force_max, force_rms))
            q_max, q_rms = scalar(q.abs().max()), scalar(q.square().mean().sqrt())
            row = {"finite": finite, "protected": protected_rows,
                "edit": {"absoluteRMS": vector(edit_absolute), "relativeRMS": vector(edit_relative),
                    "referenceRMS": vector(objective.target_scale), "passedFrames": vector(edit_pass), "passed": bool(edit_pass.all())},
                "coefficientMax": q_max, "coefficientRMS": q_rms,
                "forceMaxComponent": scalar(force_max), "forceRMS": scalar(force_rms),
                "densityMin": scalar(final_density.min()), "densityMax": scalar(final_density.max()),
                "alphaMin": scalar(frames.min()), "alphaMax": scalar(frames.max()),
                "constraints": vector(terms["constraints"]), "maxPositiveViolation": scalar(terms["constraints"].clamp_min(0).max()),
                "maxActivePositiveViolation": scalar((terms["constraints"].clamp_min(0)*objective.mask).max()),
                "editLoss": scalar(terms["edit"]), "regularizer": scalar(terms["regularizer"])}
            row["editAndBudgetPassed"] = (finite and row["edit"]["passed"] and
                q_max <= task["coefficient_max"] and q_rms <= task["coefficient_rms"] and
                row["forceMaxComponent"] <= task["applied_force_max"] and row["densityMin"] >= 0 and row["alphaMin"] >= 0 and row["alphaMax"] <= 1)
            row["protectionPassed"] = all(p["passed"] for p in protected_rows)
            row["jointPassed"] = row["editAndBudgetPassed"] and row["protectionPassed"]
            row["passed"] = row["jointPassed"]
            return row, terms["constraints"].detach()

        qualification = report["qualification"]
        publish()
        if not qualification["passed"]:
            report.update(status="completed", decision="STOP_OBJECTIVE_DERIVATIVE_QUALIFICATION")
            return_code = 0
        else:
            def solve_task(arm):
                sync(); task_start = time.perf_counter()
                objective = objectives[arm]
                row = {"id": "T02", "arm": arm, "warmStart": "zero_cold_start", "status": "running", "rolloutsStarted": 0,
                    "rolloutsCompleted": 0, "closures": 0, "acceptanceRollouts": 0, "returnedSteps": 0,
                    "constraintMask": vector(objective.mask),
                    "accepted": [], "calls": [], "outerUpdates": [], "budget": config["max_rollouts_per_task"]}
                report["arms"].append(row)
                prefix = arm + "/T02"
                x = torch.nn.Parameter(torch.zeros(tuple(task["control_shape"]), device=device, dtype=torch.float64))
                lam = torch.full((76,), config["initial_multiplier"], device=device, dtype=torch.float64) * objective.mask
                penalty = config["initial_penalty"]
                accepted_x, cached_frames, cached_c = None, None, None
                cached_velocity, cached_density = None, None
                accepted_q_history = []
                optimizer = None

                def penalty_record(terms):
                    raw_phr, effective_phr, branch = objective.penalty_terms(terms, lam, penalty)
                    return {"constraints": vector(terms["constraints"]), "multipliers": vector(lam), "penalty": penalty,
                        "protectedPHRRaw": scalar(raw_phr[:50].sum()),
                        "protectedPHREffective": scalar(effective_phr[:50].sum()),
                        "editPHRRaw": scalar(raw_phr[50:75].sum()),
                        "editPHREffective": scalar(effective_phr[50:75].sum()),
                        "RMSPHREffective": scalar(effective_phr[-1]), "effectivePHR": scalar(effective_phr.sum()),
                        "protectedPositiveConstraintCount": int((terms["constraints"][:50] > 0).sum()),
                        "editPositiveConstraintCount": int((terms["constraints"][50:75] > 0).sum()),
                        "protectedBranchCountRaw": int((branch[:50] > 0).sum()),
                        "protectedBranchCountEffective": int(((branch[:50] > 0) & objective.mask[:50].bool()).sum()),
                        "protectedPositiveMultiplierCount": int((lam[:50] > 0).sum()),
                        "protectedPenaltyWeights": vector(branch[:50].clamp_min(0)*objective.mask[:50]),
                        "editBranchCountEffective": int((branch[50:75] > 0).sum()),
                        "editPositiveMultiplierCount": int((lam[50:75] > 0).sum()),
                        "editPenaltyWeights": vector(branch[50:75].clamp_min(0))}

                def run_acceptance(reason):
                    nonlocal accepted_x, cached_frames, cached_c, cached_velocity, cached_density
                    if row["rolloutsStarted"] >= row["budget"]:
                        raise RuntimeError("Reserved acceptance forward unavailable")
                    row["rolloutsStarted"] += 1
                    sync(); call_start = time.perf_counter()
                    with torch.no_grad():
                        output = model.rollout(objective.control(x), v0, rho0)
                        metrics, constraints = acceptance(objective, x, output["frames"], output["velocity"], output["density"])
                        accepted_terms = objective.terms(objective.control(x), output["frames"])
                        merit = scalar(objective.loss(accepted_terms, lam, penalty))
                        phr_record = penalty_record(accepted_terms)
                    sync(); seconds = time.perf_counter()-call_start
                    row["rolloutsCompleted"] += 1
                    row["acceptanceRollouts"] += 1
                    accepted_x = x.detach().clone()
                    cached_frames = output["frames"].detach()
                    cached_c = constraints
                    cached_velocity = output["velocity"].detach()
                    cached_density = output["density"].detach()
                    entry = {"reason": reason, "rollout": row["rolloutsStarted"], "seconds": seconds,
                        "stateKind": "accepted_initial" if reason == "initial_zero" else "accepted_returned_step",
                        "returnedStep": row["returnedSteps"], "metrics": metrics, "ALObjective": merit,
                        "penaltyRecord": phr_record}
                    index = len(row["accepted"])
                    entry["rawFile"] = prefix + f"/accepted-{index:03d}.npz"
                    raw_save(entry["rawFile"], x=accepted_x, q=objective.control(accepted_x),
                        frames=cached_frames, constraints=cached_c, multipliers=lam,
                        penalty=np.asarray(penalty, dtype=np.float64), mask=objective.mask)
                    row["accepted"].append(entry)
                    accepted_q_history.append(objective.control(accepted_x).detach().cpu())
                    row["calls"].append({"kind": "acceptance", "reason": reason, "rollout": row["rolloutsStarted"], "seconds": seconds})
                    publish()
                    return metrics

                metrics = run_acceptance("initial_zero")
                stop = "quality_pass" if metrics["passed"] else None
                for outer in range(config["outer_iterations"]):
                    if stop:
                        break
                    # New AL objective invalidates old quasi-Newton curvature.
                    optimizer = torch.optim.LBFGS([x], **config["lbfgs"])
                    violation_before = metrics["maxActivePositiveViolation"]
                    for iteration in range(config["steps_per_outer"]):
                        if row["rolloutsStarted"] >= row["budget"]-1:
                            stop = "rollout_budget_exhausted"
                            break
                        previous_x = accepted_x.clone()

                        def closure():
                            if row["rolloutsStarted"] >= row["budget"]-1:
                                raise ClosureBudgetExhausted("Acceptance rollout reserved")
                            optimizer.zero_grad(set_to_none=True)
                            row["rolloutsStarted"] += 1
                            row["closures"] += 1
                            sync(); closure_start = time.perf_counter()
                            q = objective.control(x)
                            output = model.rollout(q, v0, rho0)
                            t = objective.terms(q, output["frames"])
                            value = objective.loss(t, lam, penalty)
                            if not bool(torch.isfinite(value)):
                                raise RuntimeError("Nonfinite closure objective")
                            value.backward()
                            if x.grad is None or not bool(torch.isfinite(x.grad).all()):
                                raise RuntimeError("Nonfinite/missing closure gradient")
                            sync(); seconds = time.perf_counter()-closure_start
                            row["rolloutsCompleted"] += 1
                            row["calls"].append({"kind": "closure", "outer": outer, "iteration": iteration,
                                "stateKind": "trial_not_accepted",
                                "rollout": row["rolloutsStarted"], "seconds": seconds, "loss": scalar(value),
                                "editLoss": scalar(t["edit"]), "regularizer": scalar(t["regularizer"]),
                                "maxPositiveViolation": scalar(t["constraints"].clamp_min(0).max()),
                                "maxActivePositiveViolation": scalar((t["constraints"].clamp_min(0)*objective.mask).max()),
                                "gradientL2": scalar(x.grad.square().sum().sqrt()), "penaltyRecord": penalty_record(t)})
                            return value

                        sync(); optimizer_start = time.perf_counter()
                        try:
                            optimizer.step(closure)
                        except ClosureBudgetExhausted:
                            with torch.no_grad():
                                x.copy_(previous_x)
                            row["budgetRollback"] = {"outer": outer, "iteration": iteration,
                                "returnedStep": row["returnedSteps"], "rolloutsStarted": row["rolloutsStarted"],
                                "restoredAcceptedX": True, "trialAccepted": False}
                            stop = "rollout_budget_exhausted_during_line_search"
                            publish()
                            break
                        sync()
                        row["returnedSteps"] += 1
                        row["calls"].append({"kind": "optimizer_step_return", "outer": outer, "iteration": iteration,
                            "seconds": time.perf_counter()-optimizer_start,
                            "parameterStepMax": scalar((x.detach()-previous_x).abs().max()),
                            "scope": "Contains closure work; do not add to closure subtotal. Library return is not an independent Wolfe certificate."})
                        metrics = run_acceptance("returned_lbfgs_step")
                        print(f"baseline {arm} T02: accepted {row['returnedSteps']}, rollouts {row['rolloutsStarted']}, arm_pass {metrics['passed']}, joint_pass {metrics['jointPassed']}", flush=True)
                        if metrics["passed"]:
                            stop = "quality_pass"
                            break
                    if stop:
                        break
                    violation_after = metrics["maxActivePositiveViolation"]
                    old_penalty = penalty
                    lam = ((lam + penalty * cached_c).clamp_min(0) * objective.mask).detach()
                    if violation_after > config["violation_reduction_factor"] * violation_before:
                        penalty = min(config["penalty_max"], penalty * config["penalty_growth"])
                    row["outerUpdates"].append({"outer": outer, "violationBefore": violation_before,
                        "violationAfter": violation_after, "oldPenalty": old_penalty, "newPenalty": penalty,
                        "multipliers": vector(lam), "historyResetBeforeNextOuter": True})
                    publish()
                if stop is None:
                    stop = "fixed_outer_step_budget_exhausted"
                row.update(status="completed", termination=stop, passed=metrics["passed"], finalMetrics=metrics)
                # Cache is from the last accepted forward, never a line-search trial.
                raw_save(prefix + "/final.npz", x=accepted_x, q=objective.control(accepted_x), frames=cached_frames,
                    constraints=cached_c, accepted_q_history=torch.stack(accepted_q_history), finalMultipliers=lam,
                    velocity=cached_velocity, density=cached_density)
                sync()
                row["wallSecondsIncludingAcceptanceAndEvidenceIO"] = time.perf_counter()-task_start
                row["synchronizedClosureSeconds"] = sum(call["seconds"] for call in row["calls"] if call["kind"] == "closure")
                row["synchronizedAcceptanceSeconds"] = sum(call["seconds"] for call in row["calls"] if call["kind"] == "acceptance")
                row["memory"] = memory()
                publish()
                return accepted_x.detach(), bool(metrics["passed"])

            for arm in report["armOrder"]:
                stage("solve_" + arm)
                solve_task(arm)
            report.update(status="completed", decision="FIXED_FRAMEWISE_COLD_START_COMPLETED",
                allOriginalGatesPassed=all(arm["passed"] for arm in report["arms"]),
                measuredMethodSpeedup=False)
            return_code = 0
        report["resources"] = memory()
    except Exception as exc:
        report.update(status="failed", decision="IMPLEMENTATION_OR_RESOURCE_FAILURE", error=repr(exc), traceback=traceback.format_exc())
        if "memory" in locals():
            try:
                report["resourcesAtFailure"] = memory()
            except Exception as memory_exc:
                report["resourceQueryError"] = repr(memory_exc)
        return_code = 1
    finally:
        report["totalWallSecondsIncludingStartupQualificationAndIO"] = time.perf_counter()-started
        report["costScope"] = {
            "newQualificationRollouts": 0, "newSolveRolloutsStarted": sum(a["rolloutsStarted"] for a in report["arms"]),
            "currentWorkerSeconds": report["totalWallSecondsIncludingStartupQualificationAndIO"],
            "priorQualification": report["qualification"].get("priorCost"),
            "interpretation": "Current cold-start online cost; prior G0 is an authenticated development prerequisite, not new forward work. T03/T04 optimization cost is not charged to this baseline."}
        try:
            report["pinsAfter"] = {name: {"path": record["path"], "sha256": file_sha(record["path"]),
                "bytes": Path(record["path"]).stat().st_size} for name, record in pins.items()}
            report["sourcesAndInputsUnchanged"] = bool(pins) and report["pinsAfter"] == pins
            if not report["sourcesAndInputsUnchanged"]:
                report.update(status="failed", decision="PROVENANCE_FAILURE")
                return_code = 1
        except Exception as exc:
            report.update(status="failed", decision="PROVENANCE_FAILURE", provenanceError=repr(exc))
            return_code = 1
        publish()
    return return_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "runs" / "run-01")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"status": "planned_not_executed", "config": str(ROOT / "config.json"), "out": str(args.out),
            "device": args.device, "frozen": (ROOT / "freeze.json").exists(),
            "scope": "Authenticated prior G0 only; one zero-x 76-constraint solve, <=120 rollouts; 600s whole worker"}, indent=2))
        return 0
    if args.worker:
        return execute(args)
    authenticate()
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    removed = {}
    for name in list(env):
        if name.upper() in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONUSERBASE") or name.startswith("TI_"):
            removed[name] = env.pop(name)
    dll_path = Path(sys.prefix) / "Library" / "bin"
    env.update(CUDA_VISIBLE_DEVICES=config["expected_gpu_uuid"], MKL_THREADING_LAYER="SEQUENTIAL",
               OMP_NUM_THREADS="4", MKL_NUM_THREADS="4", OPENBLAS_NUM_THREADS="1",
               PYTHONNOUSERSITE="1", PYTHONUNBUFFERED="1", PYTHONUTF8="1")
    if dll_path.is_dir():
        env["PATH"] = str(dll_path) + os.pathsep + env.get("PATH", "")
    command = [sys.executable, "-I", "-B", "-u", "-X", "faulthandler", str(Path(__file__).resolve()),
               "--out", str(out / "worker"), "--device", args.device, "--execute", "--worker"]
    launch = {"status": "starting", "command": command, "wallLimitSeconds": 600,
              "environmentPolicy": {key: env[key] for key in ("CUDA_VISIBLE_DEVICES", "MKL_THREADING_LAYER",
                  "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
              "removedImportOverrideNames": sorted(removed), "dllDirectory": str(dll_path),
              "scope": "Whole fresh worker: imports, source/G0 authentication, cold-start solve, acceptance, output IO"}
    (out / "supervisor.json").write_text(json.dumps(launch, indent=2)+"\n", encoding="utf-8")
    begin = time.perf_counter()
    with (out / "stdout.log").open("xb") as stdout, (out / "stderr.log").open("xb") as stderr:
        try:
            proc = subprocess.run(command, cwd=out, env=env, stdout=stdout, stderr=stderr, timeout=600, check=False)
            launch.update(status="completed" if proc.returncode == 0 else "failed", returnCode=proc.returncode)
        except subprocess.TimeoutExpired:
            launch.update(status="timeout", returnCode=None, workerKilled=True,
                          decision="STOP_WHOLE_WORKER_BUDGET_NO_RETRY")
    launch["wallSeconds"] = time.perf_counter()-begin
    for name in ("stdout.log", "stderr.log"):
        launch[name] = {"sha256": file_sha(out/name), "bytes": (out/name).stat().st_size}
    try:
        launch["sourceAndInputPinsAfter"] = authenticate()
        launch["sourcesAndInputsUnchanged"] = True
    except Exception as exc:
        launch.update(status="failed", sourcesAndInputsUnchanged=False,
                      provenanceError=repr(exc), decision="PROVENANCE_FAILURE")
    (out / "supervisor.json").write_text(json.dumps(launch, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(launch, indent=2))
    return 0 if launch["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
