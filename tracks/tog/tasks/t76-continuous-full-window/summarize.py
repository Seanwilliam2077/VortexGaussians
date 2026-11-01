"""Post-run scalar readback only: no scientific imports, fits or new trajectories.

Run from any directory; --write stores the deterministic SUMMARY.json next to this
script. This reader was written after the sole scientific result and is not part
of its frozen input set. It does not replace the original qualification checks.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def endpoint_rows(result):
    return [
        {"h": row["h"], "reference": row["name"],
         "field_relative_l2": row["primary"]["relative_error"],
         "axial_centroid_error": row["moment_errors"]["axial_centroid_error"],
         "normalized_covariance_error": row["moment_errors"]["normalized_covariance_error"],
         "passed": row["passed"]}
        for row in result["scoring"]["checkpoint_scores"] if row["time"] == 1.0
    ]


def time_max(result):
    rows = result["scoring"]["time_sensitivity"]["records"]
    return {"field_relative_l2": max(x["primary"]["relative_error"] for x in rows),
            "axial_centroid_difference": max(x["axial_centroid_difference"] for x in rows),
            "normalized_covariance_difference": max(x["normalized_covariance_difference"] for x in rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    receipt = read(base / "execution.json")
    identities = {}
    for name, expected in receipt["public_scalar_outputs"].items():
        data = (base / name).read_bytes()
        actual = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        if actual != expected:
            raise ValueError(f"Saved output identity mismatch: {name}")
        identities[name] = actual
    result = read(base / "result.json")
    prior_path = base.parent / "t71-causal-full-window" / "result.json"
    prior = read(prior_path)
    identities["T71/result.json"] = {"bytes": prior_path.stat().st_size,
        "sha256": hashlib.sha256(prior_path.read_bytes()).hexdigest()}
    if result["prediction_seal"]["sha256"] != identities["predictions.json"]["sha256"]:
        raise ValueError("Prediction seal mismatch")
    moments = []
    for path in result["paths"]:
        first, last = path["steps"][0]["moments"], path["steps"][-1]["moments"]
        moments.append({"h": path["h"], "relative_to_own_initial": {
            key: {"initial": first[key], "final": last[key],
                  "signed_final_change": (last[key] - first[key]) / first[key],
                  "maximum_absolute_change": max(abs(step["moments"][key] - first[key]) / first[key]
                                                 for step in path["steps"])}
            for key in ("Gamma", "I_z")}})
    counts = result["counters"]
    count_keys = ("search_proposals", "search_component_evaluations", "search_pair_evaluations",
        "search_weight_attempts", "search_control_attempts", "polish_linearizations", "polish_svd_calls",
        "polish_trial_attempts", "polish_model_calls", "polish_accepted_steps", "polish_invalid_trials",
        "polish_objective_rejections", "polish_truncated_singular_values", "polish_active_bound_exclusions",
        "root_polish_accepted", "polish_seed_fallbacks", "phys_field_calls", "phys_field_spatial_points",
        "phys_field_heat_integrand_points", "phys_cross_calls", "phys_cross_integrand_points")
    summary = {
        "schema": "t76-postrun-scalar-readback-v1",
        "scope": "Derived only from saved scalar results; no scientific rerun or new acceptance test.",
        "saved_output_identities": identities,
        "verdict": result["verdict"],
        "qualification_categories": {x["name"]: x["passed"] for x in result["checks"]},
        "physical_pass": result["physical_pass"],
        "time_sensitivity_pass": result["scoring"]["time_sensitivity"]["passed"],
        "reference_sensitivity_pass": result["scoring"]["reference_sensitivity"]["passed"],
        "T71_endpoint": endpoint_rows(prior), "T76_endpoint": endpoint_rows(result),
        "T71_maximum_time_difference": time_max(prior),
        "T76_maximum_time_difference": time_max(result),
        "T76_maximum_reference_score_difference": {
            k: max(x["differences"][k] for x in result["scoring"]["reference_sensitivity"]["records"])
            for k in ("field", "centroid", "covariance")},
        "moments": moments,
        "optimizer_stop_reasons": dict(collections.Counter(
            x["polish"]["audit"]["stop_reason"] for x in result["polishes"])),
        "stationarity_or_global_optimality_certified": False,
        "selected_counts": {k: counts[k] for k in count_keys},
        "execution_cost": {k: receipt[k] for k in ("complete_child_seconds",
            "supervisor_elapsed_until_receipt_seconds", "nonoverlapping_supervisor_overhead_until_receipt_seconds",
            "final_receipt_write_not_timed", "peak_observations", "tracked_scientific_child_seconds")},
        "new_method_claim": False,
        "generalization_or_convergence_theorem": False,
    }
    text = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    if args.write:
        destination = base / "SUMMARY.json"
        if destination.exists() and destination.read_text(encoding="utf-8") != text:
            raise ValueError("Refusing to replace a different saved summary")
        destination.write_text(text, encoding="utf-8", newline="\n")
        print(f"Saved scalar readback: {destination.name}, {len(text.encode('utf-8'))} bytes")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
