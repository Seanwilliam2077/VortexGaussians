"""Small, dependency-free task-spec validator. No simulation or asset loading."""
import json
import math
from pathlib import Path, PurePosixPath, PureWindowsPath

MODEL = {"n": 32, "steps": 40, "dt": 0.025, "image_size": 64,
         "frame_start": 16, "render_size": 32, "render_samples": 64,
         "kappa": 1.0, "dtype": "float64"}


def relative_file(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("File references must be nonempty relative POSIX paths")
    if PurePosixPath(value).is_absolute() or PureWindowsPath(value).drive or ":" in value:
        raise ValueError("Absolute machine paths and URLs are not input file references")
    return value


def validate(spec, require_target=False):
    errors, warnings = [], []

    def need(ok, message):
        if not ok:
            errors.append(message)

    def positive(value):
        return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value) and value > 0

    def rect(value, label):
        ok = (isinstance(value, list) and len(value) == 4 and
              all(type(x) is int for x in value) and
              0 <= value[0] < value[2] <= 64 and 0 <= value[1] < value[3] <= 64)
        need(ok, label + ": expected integer [x0,y0,x1,y1] within 64x64, half-open")
        return ok

    try:
        need(spec["schema"] == "tog-brief-v1", "Unsupported schema")
        need(isinstance(spec["id"], str) and bool(spec["id"].strip()), "Missing task id")
        need(spec["model"] == MODEL, "This CLI supports only the explicit, unchanged R20 model configuration")
        brief = spec["artist_brief"]
        need(bool(brief["requested_change"].strip()) and bool(brief["preserve"].strip()), "Brief must state change and preservation intent")
        need(brief["validation_status"] in ("draft_unvalidated", "documented_user_requirement", "historical_synthetic"), "Unknown brief evidence status")
        if brief["validation_status"] == "draft_unvalidated":
            warnings.append("Artist need is an unvalidated draft; passing pixels does not validate it.")
        if brief["validation_status"] == "documented_user_requirement":
            need(bool(brief.get("evidence", "").strip()), "Validated need requires an evidence description")
        task = spec["task"]
        need(task["pixel_coordinates"] == "lower-left-half-open", "Pixel coordinates must be explicit lower-left, half-open")
        frames = task["frames"]
        need(isinstance(frames, list) and bool(frames) and all(type(x) is int and 16 <= x <= 40 for x in frames)
             and frames == sorted(set(frames)), "Frames must be unique sorted accepted step IDs in 16..40")
        edit_ok = rect(task["edit_roi"], "edit_roi")
        regions = task["protected_rois"]
        need(isinstance(regions, list) and len(regions) > 0, "At least one protected ROI required")
        for i, roi in enumerate(regions):
            if rect(roi, f"protected_rois[{i}]") and edit_ok:
                e = task["edit_roi"]
                need(not (max(e[0], roi[0]) < min(e[2], roi[2]) and max(e[1], roi[1]) < min(e[3], roi[3])),
                     "Edit and protected ROIs must be disjoint in this interface")
        gates = task["quality"]
        for name in ("protect_relative", "protect_absolute", "edit_relative", "edit_absolute", "signal_min"):
            need(positive(gates[name]), "Quality threshold must be positive and finite: " + name)
        for name in ("upper_roi", "lower_roi"):
            rect(task["motion_diagnostics"][name], name)
        need(task["motion_diagnostics"]["role"] == "descriptive_not_gate", "Motion diagnostics cannot silently become acceptance gates")
        semantic = task["semantic_gate"]
        need(semantic in (None, "r22_frozen_negative"), "No new semantic gate has been implemented")
        if semantic == "r22_frozen_negative":
            need(brief["validation_status"] == "historical_synthetic", "R22 historical gate is only for its frozen negative fixture")
            need(task["frames"] == list(range(16, 41)) and task["edit_roi"] == [10, 12, 34, 55]
                 and task["protected_rois"] == [[35, 13, 53, 33], [35, 33, 53, 55]], "R22 fixture ROIs/frames must remain frozen")
            need(gates == {"protect_relative": .02, "protect_absolute": .005, "edit_relative": .05,
                           "edit_absolute": .01, "signal_min": .01}, "R22 fixture thresholds must remain frozen")
            need(task["motion_diagnostics"]["upper_roi"] == [10, 33, 34, 55]
                 and task["motion_diagnostics"]["lower_roi"] == [10, 12, 34, 33], "R22 semantic regions must remain frozen")
        control = spec["control"]
        need(control["shape"] == [4, 3, 8, 8, 8] and control["kind"] == "mac_body_acceleration", "Control interface must be the existing MAC body force")
        need(control["update_knots"] == [0, 13, 26, 39], "Force hats use zero-based updates 0,13,26,39")
        need(control["coefficient_max"] == .5 and control["coefficient_rms"] == .2 and control["applied_force_max_component"] == .5,
             "The portable initial track retains the existing coefficient and force budgets")
        budget = spec["budget"]
        need(budget["max_rollouts"] == 1 and budget["optimizer"] == "none", "This inspection CLI permits one rollout, no optimizer")
        need(type(budget["wall_seconds"]) is int and 1 <= budget["wall_seconds"] <= 3600, "Wall budget must be 1..3600 seconds")
        target = spec["target"]
        need(target["origin"] in ("authored", "synthetic_witness", "observation"), "Declare target origin")
        need(target["role"] in ("development", "holdout", "historical"), "Declare target role")
        need(target["layout"] in ("edit_roi", "full_frames"), "Target layout is edit_roi or full_frames")
        need(target["frame_ids"] == frames, "Target frame order must equal task frame IDs")
        need(isinstance(target["description"], str) and bool(target["description"].strip()), "Target provenance needs a description")
        evaluation = spec["evaluation"]
        need(evaluation["phase"] == target["role"], "Development/holdout/historical roles cannot be mixed")
        need(type(evaluation["used_for_tuning"]) is bool and type(evaluation["frozen_before_evaluation"]) is bool, "Evaluation role flags must be explicit booleans")
        if target["role"] == "holdout":
            need(not evaluation["used_for_tuning"] and evaluation["frozen_before_evaluation"], "Holdout must be frozen and unused for tuning")
            need(bool(evaluation.get("freeze_evidence", "").strip()), "Holdout requires a freeze evidence reference")
        if target["path"] is None:
            warnings.append("No authored target attached; approve/plan work, full task evaluation is not ready.")
            need(not require_target, "Evaluation requires an attached target")
            need(target["sha256"] is None, "Missing target cannot carry a hash")
        else:
            relative_file(target["path"])
            digest = target["sha256"]
            need(isinstance(digest, str) and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest), "Target needs lowercase SHA256")
            need(bool(target.get("author_or_source", "").strip()), "Attached target needs author/source attribution")
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        errors.append("Malformed specification: " + str(exc))
    return {"valid": not errors, "errors": errors, "warnings": warnings,
            "targetAttached": bool(spec.get("target", {}).get("path")),
            "scope": "Schema/declared-role validation only; no proof of authorship, feasibility, or user value"}


def load(path, require_target=False):
    spec = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    result = validate(spec, require_target)
    if not result["valid"]:
        raise ValueError("; ".join(result["errors"]))
    return spec, result
