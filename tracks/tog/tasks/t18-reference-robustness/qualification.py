"""T18: one supervised reference-robustness qualification, using sealed T17 data.

Default: print a plan without importing NumPy or the inherited implementation.
run --input ../t17-order-inversion-bound/inputs.json --out NEW_DIRECTORY
No input generation, repair loop, new numerical fixtures, or GPU work is provided.
"""

from __future__ import annotations

import argparse
import datetime as dt
from fractions import Fraction
import functools
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


HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "PROTOCOL.md"
T17 = HERE.parent / "t17-order-inversion-bound"
T17_SOURCE = T17 / "qualification.py"
T17_PROTOCOL = T17 / "PROTOCOL.md"
T17_INPUT = T17 / "inputs.json"
PINNED = {
    "t17_source": "d648567e27b030c454ba37fdbee11b0df1b7de6b9e2a78c10a66cc0031557831",
    "t17_protocol": "4c631c90d08d1e5b9ac19ebc6e52cbd2c902c267af105ccbedeb1cccc292586c",
    "input": "5cccf0238c679e14bc50e67d2d24726a58295b484b1d3464bf77d4eca0491cb7",
}
WALL_SECONDS = 300.0


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_json_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def identities(input_path):
    paths = {"input": Path(input_path), "t17_source": T17_SOURCE,
             "t17_protocol": T17_PROTOCOL, "t18_source": Path(__file__).resolve(),
             "t18_protocol": PROTOCOL}
    return {key: {"path": str(path.resolve()), "sha256": sha256(path)} for key, path in paths.items()}


def verify_pins(chain, input_path):
    if Path(input_path).resolve() != T17_INPUT.resolve():
        raise ValueError("Read T17's original inputs.json in place")
    for key, expected in PINNED.items():
        if chain[key]["sha256"] != expected:
            raise ValueError(f"Sealed {key} identity mismatch")


def load_sealed_t17():
    if sha256(T17_SOURCE) != PINNED["t17_source"]:
        raise ValueError("Sealed T17 source changed before import")
    spec = importlib.util.spec_from_file_location("t17_sealed_qualification", T17_SOURCE)
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load sealed T17 implementation")
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    # This changes only the imported module's function binding in this process.
    # Its PROTOCOL remains T17's protocol, as required by the unchanged inputs.
    base.adaptive_simpson = functools.partial(robust_adaptive_simpson, base)
    return base


def fraction_record(value):
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def round_fraction_up(value):
    if value < 0:
        raise ValueError("Expected a nonnegative rational")
    rounded = float(value)
    if not math.isfinite(rounded):
        raise ValueError("Rational-to-binary64 overflow")
    if Fraction.from_float(rounded) < value:
        rounded = math.nextafter(rounded, math.inf)
    if not math.isfinite(rounded) or Fraction.from_float(rounded) < value:
        raise ValueError("Upward rational conversion failed")
    return rounded


def round_fraction_down(value):
    if value < 0:
        raise ValueError("Expected a nonnegative rational")
    rounded = float(value)
    if not math.isfinite(rounded):
        raise ValueError("Rational-to-binary64 overflow")
    if Fraction.from_float(rounded) > value:
        rounded = math.nextafter(rounded, -math.inf)
    if rounded < 0 or Fraction.from_float(rounded) > value:
        raise ValueError("Downward rational conversion failed")
    return rounded


def initial_segment_geometry(left, right):
    # Operations and recursive guard agree with the sealed T17 implementation.
    mid = (left + right) / 2.0
    qleft, qright = (left + mid) / 2.0, (mid + right) / 2.0
    comparisons = (("mid == left", mid == left), ("mid == right", mid == right),
                   ("qleft == left", qleft == left), ("qleft == mid", qleft == mid),
                   ("qright == mid", qright == mid), ("qright == right", qright == right))
    return mid, qleft, qright, [label for label, equal in comparisons if equal]


def robust_adaptive_simpson(base, fixture, points, background_term, deadline, np):
    """Charge only initially unresolvable segments; preserve all attenuation."""
    start = time.perf_counter()
    fun = base.Integrand(fixture, deadline, np, base.MAX_SIMPSON_EVALS)
    maximum_depth, leaves = 0, 0
    original_budget = Fraction.from_float(base.ABS_TOL)
    ledger = {"envelope": "(r-l) * sum_i(weight_i / sd_i), uniform RGB upper bound",
              "original_budget": base.ABS_TOL,
              "original_budget_exact": fraction_record(original_budget),
              "full_original_cumulative_attenuation_retained": True,
              "original_background_term_retained": True,
              "segments": [], "budget_account_pass": False}

    def refine(left, right, fleft, fmid, fright, parent, tolerance, depth):
        nonlocal maximum_depth, leaves
        maximum_depth = max(maximum_depth, depth)
        mid = (left + right) / 2.0
        qleft, qright = (left + mid) / 2.0, (mid + right) / 2.0
        # No omission/envelope branch is permitted inside recursive refinement.
        if qleft == left or qleft == mid or qright == mid or qright == right:
            raise base.ReferenceFailure("Adaptive Simpson endpoint resolution exhausted during recursion")
        fqleft, fqright = fun(qleft), fun(qright)
        slower = (mid - left) * (fleft + 4.0 * fqleft + fmid) / 6.0
        supper = (right - mid) * (fmid + 4.0 * fqright + fright) / 6.0
        combined = slower + supper
        difference = combined - parent
        error = np.abs(difference) / 15.0
        if float(np.max(error)) <= tolerance:
            leaves += 1
            # Sum the empirical binary64 leaf estimates exactly, then round up
            # only for reporting. This does not make Simpson a rigorous bound.
            return combined + difference / 15.0, tuple(Fraction.from_float(float(e)) for e in error)
        if depth >= base.MAX_DEPTH:
            raise base.ReferenceFailure("Adaptive Simpson maximum depth reached before tolerance")
        value_l, error_l = refine(left, mid, fleft, fqleft, fmid, slower, tolerance / 2.0, depth + 1)
        value_r, error_r = refine(mid, right, fmid, fqright, fright, supper, tolerance / 2.0, depth + 1)
        return value_l + value_r, tuple(a + b for a, b in zip(error_l, error_r))

    try:
        base.check_wall(deadline)
        envelope_rate = sum((Fraction.from_float(float(w)) / Fraction.from_float(float(sd))
                             for w, sd in zip(fixture["weight"], fixture["sd"])), Fraction(0))
        ledger["envelope_rate_exact"] = fraction_record(envelope_rate)
        exact_gap_bounds, rounded_gap_charges, active = [], [], []
        for index, (left, right) in enumerate(zip(points[:-1], points[1:])):
            width = Fraction.from_float(right) - Fraction.from_float(left)
            if width <= 0:
                raise base.ReferenceFailure("Nonpositive original segment width")
            mid, qleft, qright, triggers = initial_segment_geometry(left, right)
            entry = {"index": index, "left": left, "right": right,
                     "midpoint": mid, "left_quarter": qleft, "right_quarter": qright,
                     "width_exact": fraction_record(width), "width_binary64": right - left,
                     "trigger_equalities": triggers, "initially_unresolvable": bool(triggers),
                     "status": "omitted_with_charge" if triggers else "pending_adaptive"}
            if triggers:
                exact_bound = width * envelope_rate
                charge = round_fraction_up(exact_bound)
                exact_gap_bounds.append(exact_bound)
                rounded_gap_charges.append(Fraction.from_float(charge))
                entry.update({"uniform_U_exact": fraction_record(exact_bound),
                              "charged_uniform_upper": charge,
                              "charged_upper_exact": fraction_record(Fraction.from_float(charge)),
                              "emission_rgb": [0.0, 0.0, 0.0], "allocated_budget": 0.0})
            else:
                entry.update({"uniform_U_exact": None, "charged_uniform_upper": 0.0,
                              "charged_upper_exact": fraction_record(Fraction(0))})
                active.append((entry, width))
            ledger["segments"].append(entry)
        raw_bound_sum = sum(exact_gap_bounds, Fraction(0))
        charge_sum = sum(rounded_gap_charges, Fraction(0))
        charged_total = round_fraction_up(charge_sum)
        charged_total_fraction = Fraction.from_float(charged_total)
        remaining_exact = original_budget - charged_total_fraction
        ledger.update({"omitted_segment_count": len(rounded_gap_charges),
                       "adaptive_segment_count": len(active),
                       "all_original_segments_unresolvable": not active,
                       "exact_envelope_sum": fraction_record(raw_bound_sum),
                       "rounded_charge_sum_exact": fraction_record(charge_sum),
                       "charged_total_upper": charged_total,
                       "charged_total_upper_exact": fraction_record(charged_total_fraction),
                       "remaining_before_rounding_exact": fraction_record(remaining_exact)})
        if remaining_exact <= 0:
            raise base.ReferenceFailure("No positive Simpson budget remains after charged omissions")
        remaining = round_fraction_down(remaining_exact)
        if remaining <= 0:
            raise base.ReferenceFailure("Remaining Simpson budget underflowed to zero")
        remaining_fraction = Fraction.from_float(remaining)
        active_length = sum((width for _, width in active), Fraction(0))
        allocation_sum = Fraction(0)
        for entry, width in active:
            target = remaining_fraction * width / active_length
            allocation = round_fraction_down(target)
            if allocation <= 0:
                raise base.ReferenceFailure("A required positive segment allocation underflowed to zero")
            allocation_fraction = Fraction.from_float(allocation)
            entry.update({"allocation_target_exact": fraction_record(target),
                          "allocated_budget": allocation,
                          "allocated_budget_exact": fraction_record(allocation_fraction)})
            allocation_sum += allocation_fraction
        budget_account_pass = charged_total_fraction + allocation_sum <= original_budget
        ledger.update({"remaining_budget_down": remaining,
                       "remaining_budget_down_exact": fraction_record(remaining_fraction),
                       "adaptive_total_length_exact": fraction_record(active_length),
                       "allocation_sum_exact": fraction_record(allocation_sum),
                       "allocation_sum_upper": round_fraction_up(allocation_sum),
                       "charged_plus_allocated_exact": fraction_record(charged_total_fraction + allocation_sum),
                       "budget_account_pass": budget_account_pass})
        if not budget_account_pass:
            raise base.ReferenceFailure("Global charged-plus-allocated budget exceeded 1e-11")
        total = np.zeros(3, dtype=np.float64)
        recursive_error = (Fraction(0), Fraction(0), Fraction(0))
        for entry, _ in active:
            left, right, mid = entry["left"], entry["right"], entry["midpoint"]
            evaluations_before = fun.evaluations
            fleft, fmid, fright = fun(left), fun(mid), fun(right)
            parent = (right - left) * (fleft + 4.0 * fmid + fright) / 6.0
            value, error = refine(left, right, fleft, fmid, fright, parent, entry["allocated_budget"], 0)
            total += value
            recursive_error = tuple(a + b for a, b in zip(recursive_error, error))
            entry.update({"status": "adaptive_complete", "evaluations": fun.evaluations - evaluations_before,
                          "emission_rgb": value.tolist(),
                          "empirical_error_exact_rgb": [fraction_record(e) for e in error],
                          "empirical_error_upper_rgb": [round_fraction_up(e) for e in error]})
        # When active is empty, total and recursive_error intentionally remain zero.
        combined_exact = tuple(charged_total_fraction + e for e in recursive_error)
        combined_upper = [round_fraction_up(e) for e in combined_exact]
        error_budget_pass = all(e <= original_budget for e in combined_exact) and all(e <= base.ABS_TOL for e in combined_upper)
        ledger.update({"recursive_error_exact_rgb": [fraction_record(e) for e in recursive_error],
                       "combined_error_exact_rgb": [fraction_record(e) for e in combined_exact],
                       "returned_error_estimate_budget_pass": error_budget_pass})
        if not error_budget_pass:
            raise base.ReferenceFailure("Combined empirical estimate plus omission charge exceeded 1e-11")
        return {"success": True, "rgb": (total + background_term).tolist(),
                "emission_rgb": total.tolist(), "estimated_abs_error_rgb": combined_upper,
                "recursive_estimated_abs_error_rgb": [round_fraction_up(e) for e in recursive_error],
                "omitted_emission_charge_rgb": [charged_total] * 3,
                "evaluations": fun.evaluations, "max_depth_used": maximum_depth,
                "accepted_leaves": leaves, "wall_seconds": time.perf_counter() - start,
                "initial_segment_ledger": ledger}
    except (base.ReferenceFailure, ValueError, OverflowError) as exc:
        return {"success": False, "error": str(exc), "evaluations": fun.evaluations,
                "max_depth_used": maximum_depth, "accepted_leaves": leaves,
                "wall_seconds": time.perf_counter() - start, "initial_segment_ledger": ledger}


def worker(input_path, output):
    import numpy as np

    start = time.perf_counter()
    deadline = start + WALL_SECONDS
    input_path, output = Path(input_path).resolve(), Path(output).resolve()
    manifest = json.loads((output / "attempt.json").read_text(encoding="utf-8"))
    chain = identities(input_path)
    verify_pins(chain, input_path)
    if chain != manifest["identities_before"]:
        raise ValueError("Source/input identities changed before worker start")
    base = load_sealed_t17()
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    base.validate_inputs(payload)
    records = []
    cases_dir = output / "cases"
    cases_dir.mkdir(exist_ok=False)
    try:
        rules, rule_diagnostics = {}, {}
        for degree in (32, 64):
            rules[degree], rule_diagnostics[str(degree)] = base.gauss_legendre_rule(degree, np, deadline)
        write_json_new(output / "quadrature-rules.json", rule_diagnostics)
        with (output / "progress.jsonl").open("x", encoding="utf-8", newline="\n") as progress:
            for index, fixture in enumerate(payload["fixtures"], 1):
                base.check_wall(deadline)
                result = base.qualify_fixture(fixture, deadline, np, rules)
                reference = result["references"]["adaptive_simpson"]
                accounting = reference["initial_segment_ledger"]
                accounting_pass = accounting["budget_account_pass"] and accounting.get("returned_error_estimate_budget_pass", False)
                result["gates"]["reference_global_budget_pass"] = accounting_pass
                if not accounting_pass:
                    result["gates"]["passed"] = False
                    result["gates"]["failures"].append("adaptive_simpson:global_budget_not_verified")
                write_json_new(cases_dir / f"{index:02d}-{fixture['id']}.json", result)
                records.append(result)
                update = {"completed": index, "id": fixture["id"], "passed": result["gates"]["passed"],
                          "omitted_segments": accounting.get("omitted_segment_count"),
                          "elapsed_seconds": time.perf_counter() - start}
                progress.write(json.dumps(update, allow_nan=False) + "\n")
                progress.flush()
                if index % 8 == 0:
                    print(json.dumps(update), flush=True)
        summary = base.summarize(records)
        ledgers = [r["references"]["adaptive_simpson"]["initial_segment_ledger"] for r in records]
        summary["omitted_initial_segment_count"] = sum(l.get("omitted_segment_count", 0) for l in ledgers)
        summary["rays_with_omissions"] = [r["fixture"]["id"] for r in records
                                        if r["references"]["adaptive_simpson"]["initial_segment_ledger"].get("omitted_segment_count", 0)]
        summary["global_budget_accounts_all_pass"] = all(r["gates"]["reference_global_budget_pass"] for r in records)
        final_chain = identities(input_path)
        unchanged = final_chain == chain
        summary["source_identities_unchanged"] = unchanged
        final = {"schema": "t18-qualification-results-v1", "completed_utc": utc_now(),
                 "inherited_override": "Only t17_sealed_qualification.adaptive_simpson replaced in memory",
                 "cumulative_full_qualification_invocation": 3, "t18_attempt": 1,
                 "t18_reexecution_allowed": False, "identities_before": chain,
                 "identities_after": final_chain, "numpy_version": np.__version__,
                 "python_version": sys.version, "worker_wall_seconds": time.perf_counter() - start,
                 "quadrature_rules_sha256": sha256(output / "quadrature-rules.json"),
                 "quadrature_rule_diagnostics": rule_diagnostics, "summary": summary, "cases": records}
        write_json_new(output / "results.json", final)
        print(json.dumps({"summary": summary, "worker_wall_seconds": final["worker_wall_seconds"]}), flush=True)
        return 0 if summary["all_48_numerically_qualified"] and unchanged else 2
    except Exception as exc:
        write_json_new(output / "worker-failure.json", {
            "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc(),
            "completed_count": len(records), "partial_summary": base.summarize(records),
            "elapsed_seconds": time.perf_counter() - start})
        raise


def run_supervised(input_path, output):
    start = time.perf_counter()
    input_path = Path(input_path).resolve(strict=True)
    output = Path(output).resolve()
    before = identities(input_path)
    verify_pins(before, input_path)
    if not output.parent.is_dir():
        raise FileNotFoundError(f"Output parent must already exist: {output.parent}")
    output.mkdir(exist_ok=False)
    write_json_new(output / "attempt.json", {
        "schema": "t18-attempt-v1", "started_utc": utc_now(), "identities_before": before,
        "wall_cap_seconds": WALL_SECONDS, "python_executable": sys.executable,
        "parent_pid": os.getpid(), "t18_attempt": 1, "t18_reexecution_allowed": False,
        "cumulative_full_qualification_invocation": 3,
        "inherited_override": "Only t17_sealed_qualification.adaptive_simpson replaced in memory"})
    command = [sys.executable, "-I", "-B", "-u", "-X", "utf8", str(Path(__file__).resolve()),
               "_worker", "--input", str(input_path), "--out", str(output)]
    process = None
    timeout, error, returncode = False, None, 1
    try:
        with (output / "worker-stdout.log").open("xb") as stdout_log, (output / "worker-stderr.log").open("xb") as stderr_log:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout_log, stderr=stderr_log,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            remaining = WALL_SECONDS - (time.perf_counter() - start)
            if remaining <= 0:
                raise subprocess.TimeoutExpired(command, WALL_SECONDS)
            returncode = process.wait(timeout=remaining)
    except subprocess.TimeoutExpired:
        timeout = True
        if process is not None:
            process.kill()
            process.wait()
        returncode = 124
    except Exception as exc:
        error = {"error_type": type(exc).__name__, "error": str(exc)}
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
    after = identities(input_path)
    unchanged = before == after
    if not unchanged and returncode == 0:
        returncode = 2
    write_json_new(output / "execution.json", {
        "completed_utc": utc_now(), "child_pid": None if process is None else process.pid,
        "returncode": returncode, "wall_cap_reached": timeout, "launch_error": error,
        "child_stdout": "worker-stdout.log", "child_stderr": "worker-stderr.log",
        "supervisor_wall_seconds": time.perf_counter() - start,
        "identities_before": before, "identities_after": after, "identities_unchanged": unchanged,
        "cumulative_full_qualification_invocation": 3, "t18_reexecution_allowed": False})
    return returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command")
    run = subs.add_parser("run", help="One T18 attempt, using sealed inputs and a NEW output directory")
    run.add_argument("--input", required=True)
    run.add_argument("--out", required=True)
    internal = subs.add_parser("_worker", help=argparse.SUPPRESS)
    internal.add_argument("--input", required=True)
    internal.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command is None:
        print(json.dumps({"task": "T18", "default_action": "plan_only", "fixtures": 48,
                          "input_sha256": PINNED["input"], "t18_attempts_allowed": 1,
                          "repair_attempts_allowed": 0, "wall_cap_seconds": WALL_SECONDS,
                          "gpu": False, "formal_certificate": False}), flush=True)
        return 0
    if args.command == "run":
        return run_supervised(args.input, args.out)
    return worker(args.input, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
