"""One fixed T19 comparison. Default is plan-only; run requires a new directory."""
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
import subprocess
import sys
import time
import traceback
from types import MappingProxyType

HERE = Path(__file__).resolve().parent
T17 = HERE.parent / "t17-order-inversion-bound"
T18 = HERE.parent / "t18-reference-robustness"
ARMS = ("simpson", "gl", "tail", "simple", "jensen")
ORDINARY = ARMS[:3]
PAIR = ARMS[3:]
EPSILONS = (0.001, 0.01)
PASSES = 6
EXPECTED_DELIVERIES = 2880
WALL_SECONDS = 300.0
PINS = {
    "input": "5cccf0238c679e14bc50e67d2d24726a58295b484b1d3464bf77d4eca0491cb7",
    "reference": "fa4fb6887c6b38e800f18e919634821b3ee51c2fb0122cd0dbb4047eead7873d",
    "governing_contract": "e0c420eb663c09d4eb1ae041253c7561cd154227a3db23fe87dcf133c599aec2",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def identities():
    paths = {
        "input": T17 / "inputs.json", "reference": T18 / "run-01/results.json",
        "governing_contract": T18 / "NEXT_EVIDENCE.md", "protocol": HERE / "PROTOCOL.md",
        "runner": Path(__file__).resolve(), "methods": HERE / "methods.py",
        "integrators": HERE / "integrators.py",
    }
    answer = {key: {"path": str(path.resolve()), "sha256": sha(path)} for key, path in paths.items()}
    for key, expected in PINS.items():
        if answer[key]["sha256"] != expected:
            raise ValueError(f"Sealed {key} identity mismatch")
    return answer


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def immutable_parameters(fixture):
    return MappingProxyType({
        "n": fixture["n"], "interval": tuple(fixture["interval"]),
        "mu": tuple(fixture["mu"]), "sd": tuple(fixture["sd"]),
        "weight": tuple(fixture["weight"]),
        "color": tuple(tuple(row) for row in fixture["color"]),
        "background": tuple(fixture["background"]),
    })


def finite_tree(value):
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(finite_tree(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(finite_tree(v) for v in value)
    return True


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if hasattr(value, "tolist"):
        return json_safe(value.tolist())
    return value


def distribution(values):
    return {"count": len(values), "min_ns": min(values), "max_ns": max(values),
            "median_ns": statistics.median(values), "sum_ns": sum(values)}


def add_counters(rows):
    total = {}
    for row in rows:
        for key, value in row.get("delivery", {}).get("counters", {}).items():
            if key in ("simpson_max_depth", "gl_last_order"):
                continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                total[key] = total.get(key, 0) + value
    return total


def state_counters(rows):
    answer = {}
    for key in ("simpson_max_depth", "gl_last_order"):
        values = [r["delivery"]["counters"][key] for r in rows
                  if key in r.get("delivery", {}).get("counters", {})]
        if values:
            answer[key] = {"minimum": min(values), "maximum": max(values),
                           "distribution": {str(v): values.count(v) for v in sorted(set(values))}}
    return answer


def summarize(records, fixtures, identities_unchanged):
    failures = [{"sequence": r["sequence"], "id": r["id"], "arm": r["arm"],
                 "pass": r["pass"], "epsilon": r["epsilon"], "failures": r["gates"]["failures"]}
                for r in records if not r["gates"]["passed"]]
    valid = len(records) == EXPECTED_DELIVERIES and not failures and identities_unchanged
    result = {"planned_deliveries": EXPECTED_DELIVERIES, "recorded_deliveries": len(records),
              "unexecuted_deliveries": EXPECTED_DELIVERIES - len(records),
              "failed_deliveries": failures, "complete_and_accurate": valid,
              "identities_unchanged": identities_unchanged,
              "performance_comparison_admitted": valid, "floating_point_certificate": False,
              "submission_ready": False,
              "max_observed_error": max((r.get("max_abs_error", 0.0) for r in records), default=0.0)}
    if not valid:
        result["decision"] = "INCOMPLETE_OR_INVALID_NO_PERFORMANCE_CLAIM_NO_RETRY"
        return result
    indexed = {(r["id"], r["epsilon"], r["arm"], r["pass"]): r for r in records}
    if len(indexed) != EXPECTED_DELIVERIES:
        raise ValueError("Duplicate delivery identity")
    grouped = []
    for arm in ARMS:
        selected = [r for r in records if r["arm"] == arm]
        batches = [sum(r["elapsed_ns"] for r in selected if r["pass"] == p) for p in range(PASSES)]
        branches = {}
        for row in selected:
            path = row["delivery"]["path"]
            branches[path] = branches.get(path, 0) + 1
        grouped.append({"arm": arm, "first_use_batch_ns": batches[0],
                        "warm_batch_ns": batches[1:], "warm_batches": distribution(batches[1:]),
                        "all_delivery_ns": sum(batches), "path_counts": branches,
                        "work_counters_all_passes": add_counters(selected),
                        "state_counters_all_passes": state_counters(selected),
                        "by_epsilon": [{"epsilon": e,
                            "per_pass_batch_ns": [sum(r["elapsed_ns"] for r in selected if r["pass"] == p and r["epsilon"] == e) for p in range(PASSES)]}
                            for e in EPSILONS],
                        "by_group": [{"group": g,
                            "per_pass_batch_ns": [sum(r["elapsed_ns"] for r in selected if r["pass"] == p and r["group"] == g) for p in range(PASSES)]}
                            for g in ("control", "generic", "structured", "clipping")]})
    case_comparisons, stable_wins = [], []
    for fixture in fixtures:
        for epsilon in EPSILONS:
            rows = {arm: [indexed[(fixture["id"], epsilon, arm, p)] for p in range(PASSES)] for arm in ARMS}
            samples = {arm: distribution([r["elapsed_ns"] for r in rows[arm][1:]]) for arm in ARMS}
            eligible = fixture["group"] != "control" and fixture["n"] >= 4
            candidates = []
            for arm in PAIR:
                # The method API exposes this boolean only on an actual accepted
                # pair shortcut, never on shared exact/center paths or fallback.
                accepted = all(r["delivery"].get("pair_shortcut_accepted", False) for r in rows[arm])
                stable = eligible and accepted and all(samples[arm]["max_ns"] < samples[b]["min_ns"] for b in ORDINARY)
                candidate = {"arm": arm, "eligible": eligible, "pair_accepts_every_pass": accepted,
                             "stable_win": stable,
                             "ordinary_over_candidate_median_ratios": {
                                 b: samples[b]["median_ns"] / samples[arm]["median_ns"] for b in ORDINARY}}
                candidates.append(candidate)
                if stable:
                    stable_wins.append({"id": fixture["id"], "n": fixture["n"], "epsilon": epsilon, **candidate})
            case_comparisons.append({"id": fixture["id"], "group": fixture["group"], "n": fixture["n"],
                                     "epsilon": epsilon, "warm_samples": samples,
                                     "paths_all_passes": {a: [r["delivery"]["path"] for r in rows[a]] for a in ARMS},
                                     "pair_comparisons": candidates})
    result.update({"arms": grouped, "case_comparisons": case_comparisons,
                   "stable_eligible_wins": stable_wins,
                   "decision": "LIMITED_STABLE_WIN_ASSESS_TASK_AND_PRIOR_GAPS" if stable_wins else "CLOSE_DIRECT_SHORTCUT_ON_FIXED_DEVELOPMENT_SCOPE"})
    return result


def worker(output):
    start = time.perf_counter_ns()
    deadline = start + int(WALL_SECONDS * 1e9)
    output = Path(output).resolve()
    manifest = json.loads((output / "attempt.json").read_text(encoding="utf-8"))
    initial = identities()
    if initial != manifest["identities_before"]:
        raise ValueError("Identity changed before worker start")
    records = []
    try:
        import_start = time.perf_counter_ns()
        load_module("integrators", HERE / "integrators.py")
        methods = load_module("methods", HERE / "methods.py")
        import_ns = time.perf_counter_ns() - import_start
        parse_start = time.perf_counter_ns()
        payload = json.loads((T17 / "inputs.json").read_text(encoding="utf-8"))
        reference = json.loads((T18 / "run-01/results.json").read_text(encoding="utf-8"))
        fixtures = payload["fixtures"]
        if len(fixtures) != 48 or not reference["summary"]["all_48_numerically_qualified"]:
            raise ValueError("Invalid inherited input/reference qualification")
        if [f["id"] for f in fixtures] != [r["fixture"]["id"] for r in reference["cases"]]:
            raise ValueError("Reference fixture ordering mismatch")
        truth = {r["fixture"]["id"]: r["references"]["gl64"]["rgb"] for r in reference["cases"]}
        parsed = [immutable_parameters(f) for f in fixtures]
        parse_ns = time.perf_counter_ns() - parse_start
        cache_start = time.perf_counter_ns()
        caches = {arm: {} for arm in ARMS}
        cache_setup_ns = time.perf_counter_ns() - cache_start
        setup = {"module_import_ns": import_ns, "input_and_reference_parse_and_immutable_records_ns": parse_ns,
                 "empty_arm_cache_setup_ns": cache_setup_ns,
                 "hardware": {"platform": platform.platform(), "processor": platform.processor(),
                              "logical_cpu_count": os.cpu_count(), "python": sys.version,
                              "perf_counter_resolution_seconds": time.get_clock_info("perf_counter").resolution}}
        write_new(output / "setup.json", setup)
        stop = False
        with (output / "deliveries.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
            for pass_index in range(PASSES):
                for epsilon in EPSILONS:
                    for fixture_index, (fixture, parameters) in enumerate(zip(fixtures, parsed)):
                        shift = (pass_index + fixture_index) % len(ARMS)
                        order = ARMS[shift:] + ARMS[:shift]
                        for position, arm in enumerate(order):
                            if time.perf_counter_ns() >= deadline:
                                raise TimeoutError("T19 worker deadline reached")
                            row = {"sequence": len(records) + 1, "pass": pass_index,
                                   "pass_kind": "first_use" if pass_index == 0 else "warm",
                                   "epsilon": epsilon, "id": fixture["id"], "group": fixture["group"],
                                   "n": fixture["n"], "arm": arm, "arm_position": position,
                                   "scheduled_arm_order": list(order)}
                            failure = None
                            failure_exception = None
                            delivered = None
                            before = time.perf_counter_ns()
                            try:
                                delivered = methods.deliver(arm, parameters, epsilon, caches[arm], deadline)
                            except Exception as exc:
                                failure_exception = exc
                            after = time.perf_counter_ns()
                            row["elapsed_ns"] = after - before
                            failures = []
                            if failure_exception is not None:
                                failure = {"type": type(failure_exception).__name__,
                                           "message": str(failure_exception),
                                           "traceback": "".join(traceback.format_exception(failure_exception)),
                                           "counters": json_safe(getattr(failure_exception, "delivery_counters", {})),
                                           "arm": getattr(failure_exception, "delivery_arm", arm)}
                            if failure is not None:
                                row["method_failure"] = failure
                                failures.append("method_exception")
                            else:
                                delivered = json_safe(delivered)
                                if not finite_tree(delivered):
                                    failures.append("nonfinite_delivery")
                                    row["nonfinite_delivery_repr"] = repr(delivered)
                                else:
                                    row["delivery"] = delivered
                                    rgb = delivered.get("rgb", [])
                                    if len(rgb) != 3:
                                        failures.append("invalid_rgb_shape")
                                    else:
                                        errors = [abs(float(a) - float(b)) for a, b in zip(rgb, truth[fixture["id"]])]
                                        row["abs_error_rgb"] = errors
                                        row["max_abs_error"] = max(errors)
                                        if max(errors) > epsilon + 5e-10:
                                            failures.append("accuracy_violation")
                                    if "path" not in delivered or "counters" not in delivered:
                                        failures.append("missing_delivery_metadata")
                            row["gates"] = {"passed": not failures, "failures": failures,
                                            "accuracy_tolerance": epsilon + 5e-10}
                            records.append(row)
                            stream.write(json.dumps(row, allow_nan=False) + "\n")
                            stream.flush()
                            if failures:
                                stop = True
                                break
                        if stop:
                            break
                    if stop:
                        break
                print(json.dumps({"pass": pass_index, "recorded": len(records), "stopped_on_failure": stop,
                                  "elapsed_seconds": (time.perf_counter_ns() - start) / 1e9}), flush=True)
                if stop:
                    break
        final = identities()
        summary = summarize(records, fixtures, initial == final)
        result = {"schema": "t19-complete-cost-results-v1", "completed_utc": now(),
                  "identities_before": initial, "identities_after": final, "setup": setup,
                  "unit_rule_cache_degrees_at_end": {a: sorted(map(str, caches[a].keys())) for a in ARMS},
                  "summary": summary, "records": records,
                  "worker_wall_seconds_before_final_serialization": (time.perf_counter_ns() - start) / 1e9}
        write_new(output / "results.json", result)
        print(json.dumps({"recorded": len(records), "complete_and_accurate": summary["complete_and_accurate"],
                          "decision": summary["decision"], "stable_wins": summary.get("stable_eligible_wins", []),
                          "worker_seconds": result["worker_wall_seconds_before_final_serialization"]}), flush=True)
        return 0 if summary["complete_and_accurate"] else 2
    except Exception as exc:
        write_new(output / "worker-failure.json", {"type": type(exc).__name__, "message": str(exc),
                  "traceback": traceback.format_exc(), "recorded_deliveries": len(records),
                  "planned_deliveries": EXPECTED_DELIVERIES, "elapsed_seconds": (time.perf_counter_ns() - start) / 1e9})
        raise


def supervised(output):
    start = time.perf_counter_ns()
    output = Path(output).resolve()
    initial = identities()
    if not output.parent.is_dir():
        raise FileNotFoundError("Output parent must exist")
    output.mkdir(exist_ok=False)
    write_new(output / "attempt.json", {"schema": "t19-attempt-v1", "started_utc": now(),
              "identities_before": initial, "python": sys.executable, "parent_pid": os.getpid(),
              "planned_deliveries": EXPECTED_DELIVERIES, "wall_cap_seconds": WALL_SECONDS,
              "attempt": 1, "retry_allowed": False})
    process = None
    code, timed_out, launch_error = 1, False, None
    try:
        with (output / "worker-stdout.log").open("xb") as stdout, (output / "worker-stderr.log").open("xb") as stderr:
            process = subprocess.Popen([sys.executable, "-I", "-B", "-u", "-X", "utf8", str(Path(__file__).resolve()),
                                        "_worker", "--out", str(output)], stdin=subprocess.DEVNULL, stdout=stdout,
                                       stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            remaining = WALL_SECONDS - (time.perf_counter_ns() - start) / 1e9
            if remaining <= 0:
                raise subprocess.TimeoutExpired(process.args, WALL_SECONDS)
            code = process.wait(timeout=remaining)
    except subprocess.TimeoutExpired:
        timed_out = True
        if process is not None:
            process.kill()
            process.wait()
        code = 124
    except Exception as exc:
        launch_error = {"type": type(exc).__name__, "message": str(exc)}
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
    final = identities()
    if final != initial and code == 0:
        code = 2
    write_new(output / "execution.json", {"completed_utc": now(), "returncode": code,
              "wall_cap_reached": timed_out, "launch_error": launch_error,
              "child_pid": None if process is None else process.pid,
              "supervisor_wall_seconds": (time.perf_counter_ns() - start) / 1e9,
              "identities_before": initial, "identities_after": final, "identities_unchanged": initial == final,
              "retry_allowed": False, "stdout": "worker-stdout.log", "stderr": "worker-stderr.log"})
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command")
    for name in ("run", "_worker"):
        sub = subs.add_parser(name)
        sub.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command is None:
        print(json.dumps({"task": "T19", "default": "plan_only", "planned_deliveries": EXPECTED_DELIVERIES,
                          "arms": ARMS, "epsilons": EPSILONS, "passes": PASSES,
                          "attempts_allowed": 1, "retries": 0, "wall_cap_seconds": WALL_SECONDS}), flush=True)
        return 0
    return supervised(args.out) if args.command == "run" else worker(args.out)


if __name__ == "__main__":
    raise SystemExit(main())
