"""T04 post-hoc ordinary solver revision for the same T02 task.

Reads the approved initial bundle, T02 image target, paid T03 accepted x and R20 core.
It never imports scene.py, opens a witness trajectory, or uses a hidden target state.
No rank model, response cache, NumPy BLAS, or parameter search is used.
"""
from __future__ import annotations

import argparse
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


def execute(args):
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    report = {"status": "starting", "createdUTC": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "Post-hoc ordinary solver revision of the same T02 task: 76 framewise constraints, paid T03 accepted-x warm start. Not a new task, independent replication or speedup.",
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
        stage("import_numpy_then_torch_before_numerical_work")
        import numpy as np
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
        # Load x only, never the previous frames/state/AL history. All new
        # rollouts start at the original v0/rho0, including warm acceptance.
        with np.load(pins["warm-start.npz"]["path"], allow_pickle=False) as warm:
            arrays["warm_x"] = warm["x"].copy()
        previous = json.loads(Path(pins["T03-result-summary.json"]["path"]).read_text(encoding="utf-8"))
        old_joint = next(a for a in previous["arms"] if a["arm"] == "joint")
        if (previous["status"] != "completed" or not previous["sourcesAndInputsUnchanged"] or
            old_joint["rolloutsStarted"] != manifest["prior_cost"]["joint_rollouts"] or
            old_joint["wallSecondsIncludingAcceptanceAndEvidenceIO"] != manifest["prior_cost"]["joint_seconds"] or
            previous["publishedFinalArrays"]["joint-final.npz"]["sha256"] != pins["warm-start.npz"]["sha256"]):
            raise ValueError("Paid warm-start provenance/cost mismatch")
        report["paidPrior"] = manifest["prior_cost"]
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
        spec = importlib.util.spec_from_file_location("t04_authenticated_core", core_path)
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

        # The new 76-constraint scalar objective has its own qualification.
        stage("G0_full_objective_76_constraints")
        qualification = report["qualification"]
        qualification.update(status="running", task="T02", rolloutCount=0, backwardCalls=0,
            arms={arm: {"directions": [], "objectiveEvaluationSeconds": 0.0} for arm in report["armOrder"]},
            sharedFiniteDifferenceForwardSeconds=0.0,
            costScope="Nine full rollouts, one backward call; separate from the 120-rollout solve budget, included in whole-worker and cumulative cost")
        qc = config["qualification"]
        objective = objectives["framewise_joint"]
        gen = torch.Generator(device="cpu").manual_seed(qc["x_seed"])
        x_cpu = ((torch.randint(0, 2, tuple(task["control_shape"]), generator=gen, dtype=torch.int64) * 2 - 1).to(torch.float64) * qc["x_amplitude"])
        x = x_cpu.to(device).requires_grad_(True)
        multipliers = torch.full((76,), qc["multiplier"], dtype=torch.float64, device=device)
        sync(); qualification_start = time.perf_counter()
        result = model.rollout(objective.control(x), v0, rho0)
        qualification["rolloutCount"] += 1
        terms = objective.terms(objective.control(x), result["frames"])
        sync()
        qualification["sharedAnalyticForwardSeconds"] = time.perf_counter()-qualification_start
        gradients = {}
        for index, arm in enumerate(report["armOrder"]):
            current = objectives[arm]
            sync(); backward_start = time.perf_counter()
            loss = current.loss(terms, multipliers, qc["penalty"])
            gradient, = torch.autograd.grad(loss, x)
            sync()
            qualification["backwardCalls"] += 1
            arm_q = qualification["arms"][arm]
            arm_q["analyticObjectiveAndBackwardSeconds"] = time.perf_counter()-backward_start
            arm_q["loss"] = scalar(loss)
            margin = (multipliers + qc["penalty"] * terms["constraints"])[current.mask.bool()]
            arm_q["minimumActivePHRBranchMargin"] = scalar(margin.min())
            arm_q["allEffectivePHRBranchesActive"] = bool((margin > 0).all())
            arm_q["finiteAnalytic"] = bool(torch.isfinite(loss) & torch.isfinite(gradient).all() & torch.isfinite(result["frames"]).all())
            arm_q["effectiveConstraintCount"] = int(current.mask.sum())
            gradients[arm] = gradient.detach()
        raw_save("qualification/analytic.npz", x=x, q=objective.control(x),
            gradient=gradients["framewise_joint"],
            frames=result["frames"], constraints=terms["constraints"], multipliers=multipliers,
            mask=objective.mask,
            penalty=np.asarray(qc["penalty"], dtype=np.float64))
        del result, terms, loss, gradient, margin
        gen = torch.Generator(device="cpu").manual_seed(qc["direction_seed"])
        for index in range(qc["directions"]):
            direction = (torch.randint(0, 2, tuple(task["control_shape"]), generator=gen, dtype=torch.int64) * 2 - 1).to(torch.float64).to(device)
            rows = {arm: {"index": index, "gradientDotDirection": scalar((gradients[arm]*direction).sum()), "finiteDifferences": []}
                    for arm in report["armOrder"]}
            raw_save(f"qualification/direction-{index}.npz", direction=direction)
            with torch.no_grad():
                for k, h in enumerate(qc["steps"]):
                    values = {arm: [] for arm in report["armOrder"]}
                    for sign in (1, -1):
                        probe_q = objective.control(x.detach() + sign*h*direction)
                        sync(); forward_start = time.perf_counter()
                        probe = model.rollout(probe_q, v0, rho0)
                        qualification["rolloutCount"] += 1
                        probe_terms = objective.terms(probe_q, probe["frames"])
                        sync()
                        qualification["sharedFiniteDifferenceForwardSeconds"] += time.perf_counter()-forward_start
                        for arm in report["armOrder"]:
                            sync(); objective_start = time.perf_counter()
                            value = objectives[arm].loss(probe_terms, multipliers, qc["penalty"])
                            sync()
                            qualification["arms"][arm]["objectiveEvaluationSeconds"] += time.perf_counter()-objective_start
                            values[arm].append(scalar(value))
                        raw_save(f"qualification/probe-{index}-{k}-{'plus' if sign == 1 else 'minus'}.npz",
                            q=probe_q, frames=probe["frames"], constraints=probe_terms["constraints"])
                    for arm in report["armOrder"]:
                        gd = rows[arm]["gradientDotDirection"]
                        fd = (values[arm][0]-values[arm][1])/(2*h)
                        relative = abs(fd-gd)/max(abs(gd), qc["denominator_floor"])
                        valid = all(math.isfinite(v) for v in values[arm]+[fd, gd, relative])
                        rows[arm]["finiteDifferences"].append({"h": h, "plus": values[arm][0], "minus": values[arm][1],
                            "fd": fd, "relativeError": relative, "passed": valid and relative <= qc["relative_gate"]})
            for arm, row in rows.items():
                row["passed"] = all(entry["passed"] for entry in row["finiteDifferences"])
                qualification["arms"][arm]["directions"].append(row)
            publish()
        for arm_q in qualification["arms"].values():
            arm_q["passed"] = (arm_q["finiteAnalytic"] and arm_q["allEffectivePHRBranchesActive"] and
                len(arm_q["directions"]) == qc["directions"] and all(row["passed"] for row in arm_q["directions"]))
        qualification["passed"] = all(arm_q["passed"] for arm_q in qualification["arms"].values())
        qualification.update(status="completed", wallSecondsIncludingEvidenceIO=time.perf_counter()-qualification_start, memory=memory())
        del x, gradients, direction, multipliers, probe, probe_terms, value
        publish()
        if not qualification["passed"]:
            report.update(status="completed", decision="STOP_OBJECTIVE_DERIVATIVE_QUALIFICATION")
            return_code = 0
        else:
            def solve_task(arm):
                sync(); task_start = time.perf_counter()
                objective = objectives[arm]
                row = {"id": "T02", "arm": arm, "warmStart": "paid_T03_joint_last_accepted_x_only", "status": "running", "rolloutsStarted": 0,
                    "rolloutsCompleted": 0, "closures": 0, "acceptanceRollouts": 0, "returnedSteps": 0,
                    "constraintMask": vector(objective.mask),
                    "accepted": [], "calls": [], "outerUpdates": [], "budget": config["max_rollouts_per_task"]}
                report["arms"].append(row)
                prefix = arm + "/T02"
                x = torch.nn.Parameter(data["warm_x"].detach().clone())
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
                        "stateKind": "accepted_initial" if reason == "initial_paid_warm" else "accepted_returned_step",
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

                metrics = run_acceptance("initial_paid_warm")
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
            report.update(status="completed", decision="FIXED_POSTHOC_FRAMEWISE_FEASIBILITY_COMPLETED",
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
        if "paidPrior" in report:
            prior = report["paidPrior"]
            new_g0 = report["qualification"].get("rolloutCount", 0)
            new_solve = sum(a["rolloutsStarted"] for a in report["arms"])
            report["costLineage"] = {
                "newQualificationRollouts": new_g0, "newSolveRolloutsStarted": new_solve,
                "paidWarmDependencyRolloutsPlusAllT04": prior["joint_rollouts"] + new_g0 + new_solve,
                "paidWarmDependencySecondsPlusT04Worker": prior["joint_seconds"] + report["totalWallSecondsIncludingStartupQualificationAndIO"],
                "dependencyScope": "Prior T03 joint solve plus all T04; excludes earlier T03 shared G0/setup/edit-only, so not complete historical cost",
                "fullChronologicalRolloutsIncludingT03": prior["full_T03_rollouts"] + new_g0 + new_solve,
                "fullChronologicalWorkerSecondsIncludingT03": prior["full_T03_worker_seconds"] + report["totalWallSecondsIncludingStartupQualificationAndIO"],
                "interpretation": "Observed sequential costs, not cold-start performance or an isolated formulation speedup"}
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
            "scope": "New 76-constraint G0: 9 rollouts and 1 backward; one paid T03-x-warm solve, <=120 rollouts; 600s whole worker"}, indent=2))
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
              "scope": "Whole fresh worker: imports, authentication, new G0, paid-warm solve, acceptance, output IO"}
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
