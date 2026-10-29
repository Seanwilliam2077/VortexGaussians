"""One frozen saved-data reduction for T21; default invocation is plan-only.

No numerical solver, Gaussian evaluation, CDF, or historical module is imported.
Reference RGB is used only after each candidate formula has been evaluated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import traceback


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = "tracks/tog/tasks/t21-winner-prefix-bound/"
INPUT_PATH = "tracks/tog/tasks/t17-order-inversion-bound/inputs.json"
SOURCE_PATH = "tracks/tog/tasks/t18-reference-robustness/run-01/results.json"
INPUT_SHA = "5cccf0238c679e14bc50e67d2d24726a58295b484b1d3464bf77d4eca0491cb7"
SOURCE_SHA = "fa4fb6887c6b38e800f18e919634821b3ee51c2fb0122cd0dbb4047eead7873d"
PARENT = "ed47e87b6cc12ec6211e889b5f6c8202f25e7d04"
EPSILONS = (0.001, 0.01)
CAPS = ("simple", "jensen")
REFERENCES = ("adaptive_simpson", "gl32", "gl64")
CONSISTENCY_TOL = 1e-12
ENCLOSURE_TOL = 1e-9
WALL_SECONDS = 60.0
REQUIRED_ARTIFACTS = {
    INPUT_PATH, SOURCE_PATH, TASK + "PROTOCOL.md", TASK + "DERIVATION.md",
    TASK + "reduce.py",
}


class InvalidEvidence(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidEvidence(message)


def deadline_check(deadline):
    if time.perf_counter() >= deadline:
        raise TimeoutError("T21 60-second internal reduction budget exhausted")


def sha256(path, deadline):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            deadline_check(deadline)
            block = stream.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    # Reject non-JSON NaN/Infinity spellings rather than admitting nonfinite data.
    def invalid_constant(value):
        raise InvalidEvidence("Nonfinite JSON constant: " + value)
    return json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=invalid_constant)


def resolve_artifact(relative):
    require(isinstance(relative, str), "Artifact path must be text")
    supplied = Path(relative)
    require(not supplied.is_absolute() and ".." not in supplied.parts,
            "Artifact must be a repository-relative path")
    resolved = (ROOT / supplied).resolve()
    require(resolved.is_relative_to(ROOT), "Artifact escaped repository root")
    return resolved


def frozen_identities(freeze, deadline):
    require(freeze.get("parent_commit") == PARENT, "Unexpected frozen parent commit")
    entries = freeze.get("artifacts")
    require(isinstance(entries, list), "Missing freeze artifacts")
    identities = {}
    for entry in entries:
        deadline_check(deadline)
        relative = entry["path"]
        require(relative not in identities, "Duplicate freeze artifact: " + relative)
        actual = sha256(resolve_artifact(relative), deadline)
        require(actual == entry["sha256"], "Frozen artifact changed: " + relative)
        identities[relative] = actual
    require(REQUIRED_ARTIFACTS <= identities.keys(), "Freeze omitted a required artifact")
    require(identities[INPUT_PATH] == INPUT_SHA, "Original input identity mismatch")
    require(identities[SOURCE_PATH] == SOURCE_SHA, "T18 source-result identity mismatch")
    return identities


def finite_number(value, name, lower=None, upper=None):
    require(isinstance(value, (int, float)) and not isinstance(value, bool),
            name + " is not a number")
    require(math.isfinite(value), name + " is not finite")
    if lower is not None:
        require(value >= lower, name + " is below its allowed range")
    if upper is not None:
        require(value <= upper, name + " is above its allowed range")


def vector(value, size, name, lower=None, upper=None):
    require(isinstance(value, list) and len(value) == size, name + " shape mismatch")
    for item in value:
        finite_number(item, name, lower, upper)


def validate_case(fixture, source, deadline):
    deadline_check(deadline)
    require(source["fixture"] == fixture, "Stored fixture differs from frozen input")
    name, n = fixture["id"], fixture["n"]
    require(isinstance(name, str), "Fixture id must be text")
    require(isinstance(n, int) and not isinstance(n, bool) and n >= 0,
            name + ": invalid label count")
    for field in ("mu", "sd", "weight"):
        vector(fixture[field], n, name + ": " + field)
    require(all(x > 0 for x in fixture["sd"]), name + ": nonpositive width")
    require(all(x >= 0 for x in fixture["weight"]), name + ": negative weight")
    vector(fixture["interval"], 2, name + ": interval")
    require(fixture["interval"][0] < fixture["interval"][1], name + ": reversed interval")
    vector(fixture["background"], 3, name + ": background", 0, 1)
    require(isinstance(fixture["color"], list) and len(fixture["color"]) == n,
            name + ": color shape mismatch")
    for color in fixture["color"]:
        vector(color, 3, name + ": color", 0, 1)
    order = sorted(range(n), key=fixture["mu"].__getitem__)
    require(source["sorted_input_indices"] == order, name + ": unstable saved order")
    vector(source["clipped_optical_masses"], n, name + ": clipped masses", 0)
    vector(source["alpha"], n, name + ": alpha", 0, 1)
    finite_number(source["total_clipped_tau"], name + ": total tau", 0)
    require(abs(math.fsum(source["clipped_optical_masses"])
                - source["total_clipped_tau"]) <= CONSISTENCY_TOL,
            name + ": saved total tau is inconsistent")
    vector(source["ordered_rgb"], 3, name + ": ordered RGB")
    vector(source["G_rgb"], 3, name + ": global bound", 0)
    for cap in CAPS:
        vector(source["E_" + cap + "_rgb"], 3, name + ": old " + cap, 0)
        vector(source["pair_" + cap + "_sum_rgb"], 3, name + ": old pair sum", 0)
    gates = source["gates"]
    require(gates.get("passed") is True and gates.get("all_finite") is True
            and gates.get("reference_global_budget_pass") is True
            and gates.get("failures") == [], name + ": inherited T18 gates failed")
    require(set(source["references"]) == set(REFERENCES), name + ": reference names changed")
    for ref in REFERENCES:
        saved = source["references"][ref]
        vector(saved["rgb"], 3, name + ": " + ref)
        require(saved.get("success", True) is True, name + ": reference failed")
    if source["analytic_rgb"] is not None:
        vector(source["analytic_rgb"], 3, name + ": analytical RGB")
    expected = {(order[i], order[j]) for i in range(n) for j in range(i + 1, n)}
    seen = set()
    pairs = source["pairs"]
    require(isinstance(pairs, list) and len(pairs) == n * (n - 1) // 2,
            name + ": missing pair records")
    require(source["pair_count"] == len(pairs), name + ": saved pair count differs")
    for pair in pairs:
        deadline_check(deadline)
        key = (pair["i_input"], pair["j_input"])
        require(key in expected and key not in seen, name + ": invalid/duplicate pair key")
        seen.add(key)
        for cap in CAPS:
            finite_number(pair["B_" + cap], name + ": pair " + cap, 0)
    require(seen == expected, name + ": incomplete pair keys")


def exact_common_path(fixture, total_tau):
    n = fixture["n"]
    if n == 0:
        return "common_vacuum"
    if total_tau == 0.0:
        return "common_zero_mass"
    if all(c == fixture["color"][0] for c in fixture["color"]):
        return "common_equal_color"
    if (all(mu == fixture["mu"][0] for mu in fixture["mu"])
            and all(sd == fixture["sd"][0] for sd in fixture["sd"])):
        return "common_proportional"
    return None


def signed_result(positive, negative, global_bound):
    # fsum applies separately to each channel's nonnegative terms.
    upper_raw = [math.fsum(channel) for channel in positive]
    negative_raw = [math.fsum(channel) for channel in negative]
    lower = [-min(global_bound[q], negative_raw[q]) for q in range(3)]
    upper = [min(global_bound[q], upper_raw[q]) for q in range(3)]
    bound = [max(-lower[q], upper[q]) for q in range(3)]
    return {"positive_sum_rgb": upper_raw, "negative_sum_rgb": negative_raw,
            "lower_rgb": lower, "upper_rgb": upper, "E_rgb": bound}


def formula(color, order, tau, pairs, global_bound, deadline):
    """Only permitted formula inputs; no fixture tag, reference, or oracle."""
    n = len(order)
    counters = {"prefix_additions": 0, "prefix_exp_evaluations": 0,
                "reduction_pair_traversals": 0, "prefix_cap_products": 0,
                "color_cap_products": 0, "color_differences": 0,
                "nonnegative_channel_fsums": 30}
    prefixes, prefix_tau = [], []
    cumulative = 0.0
    for rank in range(n):
        deadline_check(deadline)
        # Do not add the final tau: no later prefix needs that sum.
        if rank:
            cumulative += tau[order[rank - 1]]
            counters["prefix_additions"] += 1
            prefix = math.exp(-cumulative)
            counters["prefix_exp_evaluations"] += 1
        else:
            prefix = 1.0
        require(math.isfinite(prefix) and 0.0 <= prefix <= 1.0,
                "Invalid computed winner prefix")
        prefixes.append(prefix)
        prefix_tau.append(cumulative)
    prefix_by_input = dict(zip(order, prefixes))
    terms = {cap: {kind: [[] for _ in range(3)] for kind in
                  ("absolute", "positive", "negative", "prefix_positive", "prefix_negative")}
             for cap in CAPS}
    signs = []
    for pair in pairs:
        deadline_check(deadline)
        counters["reduction_pair_traversals"] += 1
        i, j = pair["i_input"], pair["j_input"]
        delta = [color[j][q] - color[i][q] for q in range(3)]
        sign = [(1 if d > 0 else -1 if d < 0 else 0) for d in delta]
        counters["color_differences"] += 3
        signs.append({"i_input": i, "j_input": j, "sign_rgb": sign})
        for cap in CAPS:
            b = pair["B_" + cap]
            c = prefix_by_input[i] * b
            counters["prefix_cap_products"] += 1
            for q in range(3):
                absolute_term = abs(delta[q]) * b
                prefix_term = abs(delta[q]) * c
                counters["color_cap_products"] += 2
                terms[cap]["absolute"][q].append(absolute_term)
                # The signed-only diagnostic reuses the old absolute product.
                side = "positive" if sign[q] > 0 else "negative"
                terms[cap][side][q].append(absolute_term)
                terms[cap]["prefix_" + side][q].append(prefix_term)
    variants = {}
    for cap in CAPS:
        t = terms[cap]
        old_sum = [math.fsum(channel) for channel in t["absolute"]]
        variants[cap] = {
            "reconstructed_old_absolute_sum_rgb": old_sum,
            "reconstructed_old_E_rgb": [min(global_bound[q], old_sum[q]) for q in range(3)],
            "signed_only": signed_result(t["positive"], t["negative"], global_bound),
            "combined": signed_result(t["prefix_positive"], t["prefix_negative"], global_bound),
        }
    return {"prefixes_by_sorted_rank": prefixes, "prefix_tau_by_sorted_rank": prefix_tau,
            "pair_signs": signs, "caps": variants, "counters": counters}


def audit_and_report(fixture, source, reduced):
    failures = []
    observations = {}
    for name in REFERENCES:
        rgb = source["references"][name]["rgb"]
        delta = [rgb[q] - source["ordered_rgb"][q] for q in range(3)]
        observations[name] = {"rgb": rgb, "delta_exact_minus_sorted_rgb": delta,
                              "absolute_error_rgb": [abs(d) for d in delta],
                              "max_absolute_error": max(abs(d) for d in delta)}
    if source["analytic_rgb"] is not None:
        rgb = source["analytic_rgb"]
        delta = [rgb[q] - source["ordered_rgb"][q] for q in range(3)]
        observations["analytic"] = {"rgb": rgb, "delta_exact_minus_sorted_rgb": delta,
                                     "absolute_error_rgb": [abs(d) for d in delta],
                                     "max_absolute_error": max(abs(d) for d in delta)}
    maximum_consistency_difference = 0.0
    maximum_enclosure_excess = 0.0
    for cap in CAPS:
        data = reduced["caps"][cap]
        data["old_E_rgb"] = source["E_" + cap + "_rgb"]
        for q in range(3):
            reconstructed = data["reconstructed_old_E_rgb"][q]
            old = data["old_E_rgb"][q]
            differences = [abs(reconstructed - old),
                           abs(data["reconstructed_old_absolute_sum_rgb"][q]
                               - source["pair_" + cap + "_sum_rgb"][q])]
            new = data["combined"]["E_rgb"][q]
            signed = data["signed_only"]["E_rgb"][q]
            differences.extend((max(0.0, new - old), max(0.0, new - signed),
                                max(0.0, signed - old)))
            maximum_consistency_difference = max(maximum_consistency_difference, *differences)
            if max(differences) > CONSISTENCY_TOL:
                failures.append({"kind": "arithmetic_consistency", "cap": cap,
                                 "channel": q, "differences": differences})
        for variant in ("combined", "signed_only"):
            estimate = data[variant]
            for field in ("positive_sum_rgb", "negative_sum_rgb", "E_rgb", "upper_rgb"):
                vector(estimate[field], 3, cap + " " + variant + " " + field, 0)
            for q in range(3):
                finite_number(estimate["lower_rgb"][q], "interval lower endpoint", upper=0)
                for ref, observation in observations.items():
                    delta = observation["delta_exact_minus_sorted_rgb"][q]
                    interval_excess = max(0.0, estimate["lower_rgb"][q] - delta,
                                          delta - estimate["upper_rgb"][q])
                    absolute_excess = max(0.0, abs(delta) - estimate["E_rgb"][q])
                    maximum_enclosure_excess = max(maximum_enclosure_excess,
                                                   interval_excess, absolute_excess)
                    if max(interval_excess, absolute_excess) > ENCLOSURE_TOL:
                        failures.append({"kind": "reference_enclosure", "cap": cap,
                                         "variant": variant, "channel": q, "reference": ref,
                                         "interval_excess": interval_excess,
                                         "absolute_excess": absolute_excess})
    exact_path = exact_common_path(fixture, source["total_clipped_tau"])
    eligible = fixture["group"] != "control" and fixture["n"] >= 4
    global_max = max(source["G_rgb"])
    populations = {}
    for epsilon in EPSILONS:
        common = exact_path or ("common_global_center" if global_max / 2.0 <= epsilon else None)
        unsolved = eligible and common is None
        flags = {"eligible_noncontrol_n_ge_4": eligible, "common_path": common,
                 "common_unsolved": unsolved, "caps": {}}
        for cap in CAPS:
            data = reduced["caps"][cap]
            old_accept = max(data["old_E_rgb"]) <= epsilon
            new_accept = max(data["combined"]["E_rgb"]) <= epsilon
            signed_accept = max(data["signed_only"]["E_rgb"]) <= epsilon
            flags["caps"][cap] = {
                "old_accept": old_accept, "new_accept": new_accept,
                "signed_only_accept": signed_accept,
                "historical_old_informative": eligible and global_max > epsilon and old_accept,
                "historical_new_informative": eligible and global_max > epsilon and new_accept,
                "common_unsolved_old_accept": unsolved and old_accept,
                "common_unsolved_new_accept": unsolved and new_accept,
                "common_unsolved_newly_accept": unsolved and not old_accept and new_accept,
                "diagnostic_common_unsolved_newly_accept": unsolved and not old_accept and signed_accept,
                "prefix_increment_beyond_signed_only": unsolved and not signed_accept and new_accept,
            }
        flags["saved_reference_opportunity_ceiling"] = (
            unsolved and not flags["caps"]["jensen"]["old_accept"]
            and observations["gl64"]["max_absolute_error"] <= epsilon)
        populations[str(epsilon)] = flags
    return {"id": fixture["id"], "group": fixture["group"], "n": fixture["n"],
            "sorted_input_indices": source["sorted_input_indices"],
            "clipped_optical_masses": source["clipped_optical_masses"],
            "ordered_rgb": source["ordered_rgb"], "G_rgb": source["G_rgb"],
            **reduced, "saved_reference_observations": observations, "per_epsilon": populations,
            "checks": {"qualified": not failures, "failures": failures,
                       "maximum_consistency_difference": maximum_consistency_difference,
                       "maximum_reference_enclosure_excess": maximum_enclosure_excess}}


def counted_ids(cases, predicate):
    ids = [case["id"] for case in cases if predicate(case)]
    return {"count": len(ids), "ids": ids}


def aggregate(cases, source_summary):
    result = {"historical_eligible_denominator": 28, "per_epsilon": {}}
    require(sum(c["group"] != "control" and c["n"] >= 4 for c in cases) == 28,
            "Historical non-control population denominator changed")
    for epsilon in EPSILONS:
        key = str(epsilon)
        summary = {"historical_informative": {"old": {}, "new": {}},
                   "common_unsolved": {}, "saved_reference_opportunity_ceiling": None}
        for version in ("old", "new"):
            for cap in CAPS:
                field = "historical_" + version + "_informative"
                group = counted_ids(cases, lambda c, f=field, b=cap:
                                    c["per_epsilon"][key]["caps"][b][f])
                summary["historical_informative"][version][cap] = group
                if version == "old":
                    old = source_summary["informative_counts"][key]
                    require(group["count"] == old[cap + "_informative_count"]
                            and group["ids"] == old[cap + "_fixture_ids"]
                            and old["eligible_count"] == 28
                            and old["numerically_qualified_eligible_count"] == 28,
                            "Historical informative population did not reproduce")
        summary["common_unsolved"]["population"] = counted_ids(
            cases, lambda c: c["per_epsilon"][key]["common_unsolved"])
        for label, field in (
                ("old", "common_unsolved_old_accept"),
                ("new", "common_unsolved_new_accept"),
                ("newly", "common_unsolved_newly_accept"),
                ("signed_only_diagnostic_newly", "diagnostic_common_unsolved_newly_accept"),
                ("prefix_increment_beyond_signed_only", "prefix_increment_beyond_signed_only")):
            summary["common_unsolved"][label] = {
                cap: counted_ids(cases, lambda c, f=field, b=cap:
                                 c["per_epsilon"][key]["caps"][b][f]) for cap in CAPS}
        summary["saved_reference_opportunity_ceiling"] = counted_ids(
            cases, lambda c: c["per_epsilon"][key]["saved_reference_opportunity_ceiling"])
        result["per_epsilon"][key] = summary
    result["distinct_newly_accepted_jensen"] = counted_ids(
        cases, lambda c: any(c["per_epsilon"][str(e)]["caps"]["jensen"]
                            ["common_unsolved_newly_accept"] for e in EPSILONS))
    return result


def run(out):
    started = time.perf_counter()
    deadline = started + WALL_SECONDS
    out = Path(out).expanduser().resolve()
    # Failure to create a fresh destination never modifies an existing attempt.
    out.mkdir(parents=True, exist_ok=False)
    record = {"schema": "t21-winner-prefix-saved-reduction-v1", "qualified": False,
              "parent_commit": PARENT, "cases": [], "failures": [],
              "allowances": {"arithmetic_consistency": CONSISTENCY_TOL,
                             "empirical_enclosure": ENCLOSURE_TOL},
              "epsilons": list(EPSILONS), "wall_cap_seconds": WALL_SECONDS,
              "speedup_claim": False, "novelty_claim": False,
              "floating_point_certificate": False, "tog_contribution_established": False,
              "development_data_only": True, "t19_stable_wins": "NOT EVALUATED",
              "new_numerical_reference_evaluations": 0, "new_cdf_evaluations": 0,
              "input_or_reference_used_to_tune_formula": False}
    freeze = None
    try:
        freeze_path = HERE / "freeze.json"
        record["freeze_sha256_before"] = sha256(freeze_path, deadline)
        freeze = read_json(freeze_path)
        record["identities_before"] = frozen_identities(freeze, deadline)
        inputs, source = read_json(ROOT / INPUT_PATH), read_json(ROOT / SOURCE_PATH)
        fixtures, sources = inputs["fixtures"], source["cases"]
        require(inputs["fixture_count"] == 48 and len(fixtures) == len(sources) == 48,
                "Expected exactly 48 frozen cases")
        require(len({f["id"] for f in fixtures}) == 48, "Fixture ids are not unique")
        require(source["summary"]["all_48_numerically_qualified"] is True
                and source["summary"]["qualified_count"] == 48
                and source["summary"]["completed_count"] == 48
                and source["summary"]["failures"] == [], "T18 is not fully qualified")
        for fixture, saved in zip(fixtures, sources):
            validate_case(fixture, saved, deadline)
        labels = sum(f["n"] for f in fixtures)
        pairs = sum(len(s["pairs"]) for s in sources)
        require(labels == 399 and pairs == 3272, "Frozen label/pair totals changed")
        record["counts"] = {"fixture_count": 48, "label_count": labels,
                            "pair_records": pairs, "structural_pair_traversals": pairs}
        for index, (fixture, saved) in enumerate(zip(fixtures, sources)):
            deadline_check(deadline)
            reduced = formula(fixture["color"], saved["sorted_input_indices"],
                              saved["clipped_optical_masses"], saved["pairs"],
                              saved["G_rgb"], deadline)
            case = audit_and_report(fixture, saved, reduced)
            record["cases"].append(case)
            for failure in case["checks"]["failures"]:
                record["failures"].append({"id": fixture["id"], **failure})
            if (index + 1) % 8 == 0:
                print(json.dumps({"completed_cases": index + 1, "task": "T21"}), flush=True)
        record["summary"] = aggregate(record["cases"], source["summary"])
        counters = {key: sum(c["counters"][key] for c in record["cases"])
                    for key in record["cases"][0]["counters"]}
        counters["structural_pair_traversals"] = pairs
        counters["total_pair_record_traversals"] = pairs + counters["reduction_pair_traversals"]
        record["counters"] = counters
        require(counters["reduction_pair_traversals"] == 3272
                and counters["prefix_cap_products"] == 2 * 3272,
                "Reduction traversal/product accounting mismatch")
        expected_prefix_work = sum(max(f["n"] - 1, 0) for f in fixtures)
        require(counters["prefix_additions"] == counters["prefix_exp_evaluations"]
                == expected_prefix_work, "Prefix accounting mismatch")
        record["identities_after"] = frozen_identities(freeze, deadline)
        record["freeze_sha256_after"] = sha256(freeze_path, deadline)
        require(record["identities_before"] == record["identities_after"]
                and record["freeze_sha256_before"] == record["freeze_sha256_after"],
                "Evidence changed during the reduction")
        deadline_check(deadline)
        record["qualified"] = not record["failures"]
        added = record["summary"]["distinct_newly_accepted_jensen"]["count"]
        admitted = record["qualified"] and added > 0
        record["admission"] = {"admitted": admitted, "distinct_added_rays": added,
                               "allows_preparation_only": admitted,
                               "allows_further_execution": False,
                               "decision": ("unqualified" if not record["qualified"] else
                                            "retain_acceptance_region_observation" if admitted else
                                            "archive_joint_refinement_on_fixed_scope")}
    except Exception as exc:
        record["qualified"] = False
        record["failures"].append({"type": type(exc).__name__, "message": str(exc),
                                   "traceback": traceback.format_exc()})
        record["admission"] = {"admitted": False, "decision": "unqualified",
                               "allows_preparation_only": False, "allows_further_execution": False}
    record["elapsed_analysis_seconds_before_serialization"] = time.perf_counter() - started
    record["accounting_note"] = (
        "Offline saved-data reduction, not a delivery benchmark. Pair caps were loaded; "
        "their production cost, sorting, masses, preparation and fallback are not measured. "
        "Structural pair scans and formula scans are counted separately. All per-case "
        "acceptance counts are descriptive; only qualified=true permits admission.")
    with (out / "results.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"qualified": record["qualified"], "completed_cases": len(record["cases"]),
                      "results": str(out / "results.json")}), flush=True)
    return 0 if record["qualified"] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command")
    execute = commands.add_parser("run", help="Perform the one explicitly authorized frozen reduction")
    execute.add_argument("--out", required=True, help="New output directory; existing paths are rejected")
    args = parser.parse_args()
    if args.command is None:
        print(json.dumps({"mode": "plan-only", "task": "T21", "execution_performed": False,
                          "command_requires": "run --out NEW_DIRECTORY", "freeze_required": True,
                          "maximum_invocations": 1, "wall_cap_seconds": WALL_SECONDS}, indent=2))
        return 0
    try:
        return run(args.out)
    except Exception as exc:
        # In particular, an existing output destination must remain untouched.
        print(json.dumps({"qualified": False, "type": type(exc).__name__,
                          "message": str(exc)}), file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
