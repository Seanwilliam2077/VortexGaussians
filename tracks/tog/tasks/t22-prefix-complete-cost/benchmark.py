"""One T22 two-stage delivery invocation; no arguments only prints the plan."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import statistics
import sys
import time
import traceback
from types import MappingProxyType


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = "tracks/tog/tasks/t22-prefix-complete-cost/"
INPUT = "tracks/tog/tasks/t17-order-inversion-bound/inputs.json"
REFERENCE = "tracks/tog/tasks/t18-reference-robustness/run-01/results.json"
INPUT_SHA = "5cccf0238c679e14bc50e67d2d24726a58295b484b1d3464bf77d4eca0491cb7"
REFERENCE_SHA = "fa4fb6887c6b38e800f18e919634821b3ee51c2fb0122cd0dbb4047eead7873d"
PARENT = "2b63234f262f66825255628b28cedc0156911745"
ARMS = ("gl", "tail", "signed_simple", "signed_jensen", "prefix_simple", "prefix_jensen")
BASELINES = ARMS[:2]
SIGNED = ARMS[2:4]
PREFIX = ARMS[4:]
EPSILONS = (0.001, 0.01)
PASSES = 6
EXPECTED = {"A": 192, "B": 3456}
WALL_SECONDS = 300
COHORT = ("generic-11-n8", "generic-14-n4", "structured-08-n8-span3")
STATE_COUNTERS = ("simpson_max_depth", "gl_last_order")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def deadline_check(deadline):
    if time.perf_counter_ns() >= deadline:
        raise TimeoutError("T22 global 300-second internal deadline reached")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    def invalid_constant(value):
        raise ValueError("Nonfinite JSON constant " + value)
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=invalid_constant)


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, separators=(",", ":"), allow_nan=False)
        stream.write("\n")


def identities(freeze):
    require(freeze.get("parent_commit") == PARENT, "Frozen parent differs")
    entries = freeze.get("artifacts")
    require(isinstance(entries, list), "Missing frozen artifacts")
    result = {}
    for entry in entries:
        relative = entry["path"]
        path = Path(relative)
        require(not path.is_absolute() and ".." not in path.parts,
                "Frozen path must be repository relative")
        actual_path = (ROOT / path).resolve()
        require(actual_path.is_relative_to(ROOT), "Frozen path escaped repository")
        require(relative not in result, "Duplicate frozen path")
        actual = sha(actual_path)
        require(actual == entry["sha256"], "Frozen identity differs: " + relative)
        result[relative] = actual
    required = {INPUT, REFERENCE, TASK + "PROTOCOL.md", TASK + "benchmark.py",
                TASK + "methods.py", TASK + "integrators.py"}
    require(required <= result.keys(), "Freeze omitted a mandatory artifact")
    require(result[INPUT] == INPUT_SHA and result[REFERENCE] == REFERENCE_SHA,
            "Sealed input/reference identity differs")
    return result


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def parameters(fixture):
    # Only immutable raw input values: working arrays/conversions stay in deliver.
    return MappingProxyType({
        "n": fixture["n"], "interval": tuple(fixture["interval"]),
        "mu": tuple(fixture["mu"]), "sd": tuple(fixture["sd"]),
        "weight": tuple(fixture["weight"]),
        "color": tuple(tuple(c) for c in fixture["color"]),
        "background": tuple(fixture["background"]),
    })


def json_values(value):
    if isinstance(value, dict):
        return {str(k): json_values(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_values(v) for v in value]
    if hasattr(value, "tolist"):
        return json_values(value.tolist())
    return value


def finite_tree(value):
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(finite_tree(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(finite_tree(v) for v in value)
    return True


def preserve_nonfinite(value):
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite_repr": repr(value)}
    if isinstance(value, dict):
        return {k: preserve_nonfinite(v) for k, v in value.items()}
    if isinstance(value, list):
        return [preserve_nonfinite(v) for v in value]
    return value


def row_counters(row):
    if "delivery" in row:
        value = row["delivery"].get("counters", {})
    else:
        value = row.get("method_failure", {}).get("counters", {})
    return value if isinstance(value, dict) else {}


def work_counts(rows):
    added, states, paths = {}, {}, {}
    for row in rows:
        for key, value in row_counters(row).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
                if key in STATE_COUNTERS:
                    states.setdefault(key, []).append(value)
                else:
                    added[key] = added.get(key, 0) + value
        path = row.get("delivery", {}).get("path", "METHOD_EXCEPTION")
        if not isinstance(path, str):
            path = "INVALID_PATH_METADATA"
        paths[path] = paths.get(path, 0) + 1
    return {"additive_counters": added, "state_counters": {
        key: {"minimum": min(values), "maximum": max(values),
              "distribution": {str(v): values.count(v) for v in sorted(set(values))}}
        for key, values in states.items()}, "path_counts": paths}


def distribution(values):
    return {"count": len(values), "samples_ns": list(values), "min_ns": min(values),
            "max_ns": max(values), "median_ns": statistics.median(values), "sum_ns": sum(values)}


def call_delivery(methods, arm, params, epsilon, cache, deadline, row, truth):
    exception = None
    delivered = None
    before = time.perf_counter_ns()
    try:
        delivered = methods.deliver(arm, params, epsilon, cache, deadline)
    except Exception as exc:
        exception = exc
    after = time.perf_counter_ns()
    row["elapsed_ns"] = after - before
    check_start = after
    failures = []
    if exception is not None:
        row["method_failure"] = {
            "type": type(exception).__name__, "message": str(exception),
            "traceback": "".join(traceback.format_exception(exception)),
            "counters": preserve_nonfinite(json_values(getattr(exception, "delivery_counters", {}))),
            "arm": getattr(exception, "delivery_arm", arm),
        }
        failures.append("method_exception")
    else:
        delivered = json_values(delivered)
        if not isinstance(delivered, dict):
            row["invalid_delivery_repr"] = repr(delivered)
            failures.append("delivery_not_mapping")
        else:
            if not finite_tree(delivered):
                failures.append("nonfinite_delivery")
            row["delivery"] = preserve_nonfinite(delivered)
            rgb = delivered.get("rgb")
            valid_rgb = (isinstance(rgb, list) and len(rgb) == 3
                         and all(isinstance(x, (int, float)) and not isinstance(x, bool)
                                 and math.isfinite(x) for x in rgb))
            if not valid_rgb:
                failures.append("invalid_rgb")
            else:
                errors = [abs(a - b) for a, b in zip(rgb, truth)]
                row["abs_error_rgb"] = errors
                row["max_abs_error"] = max(errors)
                if max(errors) > epsilon + 5e-10:
                    failures.append("accuracy_violation")
            if not isinstance(delivered.get("path"), str) or not isinstance(delivered.get("counters"), dict):
                failures.append("invalid_delivery_metadata")
    if after >= deadline:
        failures.append("global_deadline_exceeded")
    row["gates"] = {"passed": not failures, "failures": failures,
                    "accuracy_tolerance": epsilon + 5e-10}
    row["validation_and_failure_formatting_ns"] = time.perf_counter_ns() - check_start
    return row


def accounting(records):
    result = {}
    for stage, arms in (("A", BASELINES), ("B", ARMS)):
        rows = [r for r in records if r["stage"] == stage]
        result[stage] = {"planned": EXPECTED[stage], "recorded": len(rows),
                         "passed": sum(r["gates"]["passed"] for r in rows),
                         "failed": sum(not r["gates"]["passed"] for r in rows),
                         "unexecuted": EXPECTED[stage] - len(rows),
                         "actual_delivery_ns": sum(r["elapsed_ns"] for r in rows),
                         "validation_and_failure_formatting_ns": sum(
                             r["validation_and_failure_formatting_ns"] for r in rows),
                         "work": work_counts(rows), "arms": []}
        for arm in arms:
            selected = [r for r in rows if r["arm"] == arm]
            result[stage]["arms"].append({"arm": arm, "recorded": len(selected),
                "delivery_ns": sum(r["elapsed_ns"] for r in selected), "work": work_counts(selected),
                "by_epsilon": [{"epsilon": e, "recorded": sum(r["epsilon"] == e for r in selected),
                    "delivery_ns": sum(r["elapsed_ns"] for r in selected if r["epsilon"] == e)}
                    for e in EPSILONS]})
    return result


def summarize(records, fixtures, identities_unchanged, fatal_failures):
    costs = accounting(records)
    stages_pass = {s: costs[s]["recorded"] == EXPECTED[s] and costs[s]["failed"] == 0
                   for s in EXPECTED}
    complete = all(stages_pass.values()) and identities_unchanged and not fatal_failures
    result = {"planned_deliveries": sum(EXPECTED.values()), "recorded_deliveries": len(records),
              "unexecuted_deliveries": sum(EXPECTED.values()) - len(records),
              "stage_A_qualification_passed": stages_pass["A"],
              "stage_B_completed_and_accurate": stages_pass["B"],
              "complete_and_accurate": complete, "performance_comparison_admitted": complete,
              "identities_unchanged": identities_unchanged, "stage_accounting": costs,
              "t19_stable_wins": "NOT EVALUATED", "floating_point_certificate": False,
              "novelty_claim": False, "tog_contribution_established": False,
              "failed_deliveries": [{k: r[k] for k in
                    ("sequence", "stage", "pass", "epsilon", "id", "arm", "gates")}
                  for r in records if not r["gates"]["passed"]],
              "maximum_observed_error": max((r.get("max_abs_error", 0.0) for r in records), default=0.0)}
    if not complete:
        result["decision"] = "INCOMPLETE_OR_INVALID_NO_PERFORMANCE_CLAIM_NO_RETRY"
        return result
    rows = [r for r in records if r["stage"] == "B"]
    indexed = {(r["id"], r["epsilon"], r["arm"], r["pass"]): r for r in rows}
    require(len(indexed) == EXPECTED["B"], "Duplicate Stage B delivery keys")
    groups = list(dict.fromkeys(f["group"] for f in fixtures))
    result["batch_pass_epsilon_arm"] = [
        {"pass": p, "epsilon": e, "arm": arm, "delivery_ns": sum(
            r["elapsed_ns"] for r in rows if r["pass"] == p and r["epsilon"] == e and r["arm"] == arm)}
        for p in range(PASSES) for e in EPSILONS for arm in ARMS]
    result["group_epsilon_arm"] = [
        {"group": group, "epsilon": e, "arm": arm,
         "per_pass_delivery_ns": [sum(r["elapsed_ns"] for r in rows
             if r["group"] == group and r["epsilon"] == e and r["arm"] == arm and r["pass"] == p)
             for p in range(PASSES)],
         "work": work_counts([r for r in rows if r["group"] == group
                              and r["epsilon"] == e and r["arm"] == arm])}
        for group in groups for e in EPSILONS for arm in ARMS]
    batches = {arm: [sum(r["elapsed_ns"] for r in rows if r["arm"] == arm and r["pass"] == p)
                    for p in range(PASSES)] for arm in ARMS}
    result["whole_batches"] = {arm: {"initial_rule_use_ns": values[0],
        "five_subsequent_batches": distribution(values[1:])} for arm, values in batches.items()}
    result["epsilon_batches"] = [{"epsilon": epsilon, "arm": arm,
        "initial_rule_use_ns": sum(r["elapsed_ns"] for r in rows if r["arm"] == arm
                                   and r["epsilon"] == epsilon and r["pass"] == 0),
        "five_subsequent_batches": distribution([sum(r["elapsed_ns"] for r in rows
            if r["arm"] == arm and r["epsilon"] == epsilon and r["pass"] == p)
            for p in range(1, PASSES)])} for epsilon in EPSILONS for arm in ARMS]
    comparisons, wins = [], {arm: {"joint_delivery": [], "prefix_increment": []} for arm in PREFIX}
    for fixture in fixtures:
        for epsilon in EPSILONS:
            per_arm = {arm: [indexed[(fixture["id"], epsilon, arm, p)] for p in range(PASSES)]
                       for arm in ARMS}
            samples = {arm: distribution([r["elapsed_ns"] for r in per_arm[arm][1:]]) for arm in ARMS}
            common_used = any(r["delivery"]["path"].startswith("common_")
                              for selected in per_arm.values() for r in selected)
            eligible = fixture["group"] != "control" and fixture["n"] >= 4 and not common_used
            signed_accepts = {arm: [r["delivery"].get("pair_shortcut_accepted", False) is True
                                    for r in per_arm[arm]] for arm in SIGNED}
            neither_signed_accepts = not any(flag for flags in signed_accepts.values() for flag in flags)
            candidates = []
            for arm in PREFIX:
                accepts = all(r["delivery"].get("pair_shortcut_accepted", False) is True for r in per_arm[arm])
                beats = {b: samples[arm]["max_ns"] < samples[b]["min_ns"] for b in ARMS[:4]}
                joint = eligible and accepts and all(beats[b] for b in BASELINES)
                increment = joint and neither_signed_accepts and all(beats[b] for b in SIGNED)
                candidate = {"arm": arm, "eligible": eligible, "actual_pair_accepts_every_pass": accepts,
                    "stable_beats_comparator": beats, "joint_delivery_win": joint,
                    "prefix_increment_win": increment,
                    "comparator_over_candidate_warm_median_ratios": {
                        b: samples[b]["median_ns"] / samples[arm]["median_ns"] for b in ARMS[:4]}}
                candidates.append(candidate)
                identity = {"id": fixture["id"], "group": fixture["group"],
                            "n": fixture["n"], "epsilon": epsilon}
                if joint:
                    wins[arm]["joint_delivery"].append(identity)
                if increment:
                    wins[arm]["prefix_increment"].append(identity)
            comparisons.append({"id": fixture["id"], "group": fixture["group"], "n": fixture["n"],
                "epsilon": epsilon, "common_path_used": common_used, "warm_samples": samples,
                "initial_rule_use_ns": {a: per_arm[a][0]["elapsed_ns"] for a in ARMS},
                "paths_all_passes": {a: [r["delivery"]["path"] for r in per_arm[a]] for a in ARMS},
                "signed_shortcut_acceptance_all_passes": signed_accepts,
                "neither_signed_shortcut_accepts_any_pass": neither_signed_accepts,
                "combined_comparisons": candidates})
    primary_cohort_wins = [r for r in wins["prefix_jensen"]["prefix_increment"]
                           if r["id"] in COHORT and r["epsilon"] == 0.01]
    result.update({"case_comparisons": comparisons, "stable_wins": wins,
        "primary_hypothesis": "prefix_jensen", "secondary_hypothesis": "prefix_simple",
        "development_selected_primary_cohort": list(COHORT), "primary_cohort_epsilon": 0.01,
        "primary_cohort_prefix_increment_wins": primary_cohort_wins,
        "primary_cohort_comparisons": [r for r in comparisons if r["id"] in COHORT and r["epsilon"] == 0.01],
        "old_sparse_witness_comparisons": [r for r in comparisons if r["id"] == "structured-04-n4-span3"],
        "prefix_jensen_faster_in_every_whole_warm_batch": {
            other: all(batches["prefix_jensen"][p] < batches[other][p] for p in range(1, PASSES))
            for other in ARMS[:4]},
        "decision": ("RETAIN_LOCAL_PRIMARY_PREFIX_INCREMENT_COST_OBSERVATION" if primary_cohort_wins else
                     "CLOSE_PRIMARY_JENSEN_PREFIX_COST_HYPOTHESIS_ON_FIXED_SCOPE"),
        "secondary_result_changes_primary_decision": False, "automatic_followup_execution": False})
    return result


def run(output):
    started = time.perf_counter_ns()
    deadline = started + WALL_SECONDS * 1_000_000_000
    output = Path(output).expanduser().resolve()
    require(output.parent.is_dir(), "Output parent must already exist")
    output.mkdir(exist_ok=False)
    records, fixtures, fatal = [], [], []
    setup, stage_windows, caches = {}, {}, {}
    initial = final = None
    freeze_before = freeze_after = None
    freeze = None
    journal_ns = 0
    try:
        stamp = time.perf_counter_ns()
        freeze_before = sha(HERE / "freeze.json")
        freeze = read_json(HERE / "freeze.json")
        initial = identities(freeze)
        setup["initial_identity_checks_ns"] = time.perf_counter_ns() - stamp
        stamp = time.perf_counter_ns()
        write_new(output / "attempt.json", {"schema": "t22-attempt-v1", "started_utc": now(),
            "attempt": 1, "retry_allowed": False, "parent_commit": PARENT,
            "freeze_sha256": freeze_before, "identities_before": initial,
            "python_executable": sys.executable, "pid": os.getpid(),
            "wall_cap_seconds": WALL_SECONDS, "planned_deliveries": EXPECTED,
            "external_supervisor": "Provided separately by research root; no nested worker here"})
        setup["attempt_serialization_write_ns"] = time.perf_counter_ns() - stamp
        stamp = time.perf_counter_ns()
        load_module("integrators", HERE / "integrators.py")
        methods = load_module("methods", HERE / "methods.py")
        setup["module_import_ns"] = time.perf_counter_ns() - stamp
        stamp = time.perf_counter_ns()
        payload, reference = read_json(ROOT / INPUT), read_json(ROOT / REFERENCE)
        fixtures = payload["fixtures"]
        saved = reference["cases"]
        require(len(fixtures) == len(saved) == 48 and payload["fixture_count"] == 48,
                "Expected 48 frozen fixtures")
        require(reference["summary"]["all_48_numerically_qualified"] is True,
                "T18 reference qualification missing")
        require(all(f == s["fixture"] and s["gates"]["passed"] is True
                    for f, s in zip(fixtures, saved)), "Frozen fixture/reference mismatch")
        truth = {s["fixture"]["id"]: s["references"]["gl64"]["rgb"] for s in saved}
        require(all(len(rgb) == 3 and finite_tree(rgb) for rgb in truth.values()), "Invalid reference RGB")
        setup["input_reference_parse_and_validation_ns"] = time.perf_counter_ns() - stamp
        stamp = time.perf_counter_ns()
        raw_parameters = [parameters(f) for f in fixtures]
        setup["immutable_raw_parameter_snapshots_ns"] = time.perf_counter_ns() - stamp
        stamp = time.perf_counter_ns()
        setup["hardware"] = {"platform": platform.platform(), "processor": platform.processor(),
            "logical_cpu_count": os.cpu_count(), "python": sys.version,
            "perf_counter_resolution_seconds": time.get_clock_info("perf_counter").resolution}
        setup["hardware_metadata_ns"] = time.perf_counter_ns() - stamp
        with (output / "deliveries.jsonl").open("x", encoding="utf-8", newline="\n") as journal:
            for stage, arms, passes in (("A", BASELINES, 1), ("B", ARMS, PASSES)):
                # Stage B is reached only after every Stage A gate passes.
                if stage == "B":
                    require(len(records) == EXPECTED["A"] and all(r["gates"]["passed"] for r in records),
                            "Stage B requires complete accurate baseline qualification")
                stamp = time.perf_counter_ns()
                caches[stage] = {arm: {} for arm in arms}
                setup["stage_" + stage + "_fresh_empty_cache_creation_ns"] = time.perf_counter_ns() - stamp
                stage_started = time.perf_counter_ns()
                stopped = False
                try:
                    for pass_index in range(passes):
                        for epsilon_index, epsilon in enumerate(EPSILONS):
                            for fixture_index, (fixture, params) in enumerate(zip(fixtures, raw_parameters)):
                                shift = (fixture_index if stage == "A" else
                                         pass_index + epsilon_index + fixture_index) % len(arms)
                                order = arms[shift:] + arms[:shift]
                                for position, arm in enumerate(order):
                                    deadline_check(deadline)
                                    row = {"sequence": len(records) + 1, "stage": stage, "pass": pass_index,
                                        "pass_kind": ("baseline_qualification" if stage == "A" else
                                                      "initial_rule_use_after_qualification" if pass_index == 0 else "subsequent"),
                                        "epsilon_index": epsilon_index, "epsilon": epsilon,
                                        "fixture_index": fixture_index, "id": fixture["id"],
                                        "group": fixture["group"], "n": fixture["n"], "arm": arm,
                                        "arm_position": position, "scheduled_arm_order": list(order)}
                                    call_delivery(methods, arm, params, epsilon, caches[stage][arm],
                                                  deadline, row, truth[fixture["id"]])
                                    records.append(row)
                                    stamp = time.perf_counter_ns()
                                    journal.write(json.dumps(row, allow_nan=False) + "\n")
                                    journal.flush()
                                    journal_ns += time.perf_counter_ns() - stamp
                                    if not row["gates"]["passed"]:
                                        stopped = True
                                        break
                                if stopped:
                                    break
                            if stopped:
                                break
                        print(json.dumps({"stage": stage, "pass": pass_index, "recorded": len(records),
                                          "stopped_on_failure": stopped}), flush=True)
                        if stopped:
                            break
                finally:
                    stage_windows[stage] = time.perf_counter_ns() - stage_started
                if stopped:
                    break
    except Exception as exc:
        fatal.append({"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()})
    if freeze is not None:
        stamp = time.perf_counter_ns()
        try:
            final = identities(freeze)
            freeze_after = sha(HERE / "freeze.json")
        except Exception as exc:
            fatal.append({"type": type(exc).__name__, "message": str(exc), "phase": "final_identity_checks"})
        setup["final_identity_checks_ns"] = time.perf_counter_ns() - stamp
    unchanged = initial is not None and initial == final and freeze_before == freeze_after
    stamp = time.perf_counter_ns()
    try:
        deadline_check(deadline)
        summary = summarize(records, fixtures, unchanged, fatal)
    except Exception as exc:
        fatal.append({"type": type(exc).__name__, "message": str(exc), "phase": "summary",
                      "traceback": traceback.format_exc()})
        summary = summarize(records, fixtures, False, fatal)
    setup["summary_construction_ns"] = time.perf_counter_ns() - stamp
    result = {"schema": "t22-prefix-complete-cost-results-v1", "completed_utc": now(),
        "parent_commit": PARENT, "freeze_sha256_before": freeze_before, "freeze_sha256_after": freeze_after,
        "identities_before": initial, "identities_after": final, "setup": setup,
        "stage_wall_windows_ns": stage_windows, "journal_serialization_flush_ns": journal_ns,
        "cache_rule_degrees_at_end": {stage: {arm: sorted(map(str, cache.keys()))
            for arm, cache in per_arm.items()} for stage, per_arm in caches.items()},
        "cache_contract": "Stage A and B use separate caches; each stage has independent per-arm unit GL rules only.",
        "timing_contract": "Delivery, validation, journal and setup are nested in stage/worker wall intervals; never add them to enclosing totals. Initial Stage B rule use follows Stage A in the same process and is not cold-process timing.",
        "fatal_failures": fatal, "summary": summary, "records": records,
        "worker_wall_ns_before_final_serialization": time.perf_counter_ns() - started}
    stamp = time.perf_counter_ns()
    write_new(output / "results.json", result)
    final_write_ns = time.perf_counter_ns() - stamp
    write_new(output / "publication-accounting.json", {"results_serialization_write_ns": final_write_ns,
        "worker_wall_ns_through_results_write": time.perf_counter_ns() - started,
        "journal_record_count": len(records), "results_include_every_journal_record": True,
        "journal_sha256": sha(output / "deliveries.jsonl") if (output / "deliveries.jsonl").exists() else None,
        "results_sha256": sha(output / "results.json"),
        "note": "Final serialization is outside delivery timing but within the externally supervised invocation."})
    print(json.dumps({"recorded": len(records), "stage_A_passed": summary["stage_A_qualification_passed"],
        "complete_and_accurate": summary["complete_and_accurate"], "decision": summary["decision"]}), flush=True)
    return 0 if summary["complete_and_accurate"] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command")
    execute = commands.add_parser("run")
    execute.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command is None:
        print(json.dumps({"task": "T22", "mode": "plan-only", "executed": False,
            "stage_deliveries": EXPECTED, "arms": ARMS, "epsilons": EPSILONS,
            "attempts_allowed": 1, "retries": 0, "wall_cap_seconds": WALL_SECONDS}, indent=2))
        return 0
    try:
        return run(args.out)
    except Exception as exc:
        print(json.dumps({"qualified": False, "type": type(exc).__name__, "message": str(exc),
            "traceback": traceback.format_exc(), "retry_allowed": False}), file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
