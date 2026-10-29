"""T17's fixed CPU qualification. No numerical work occurs without a subcommand.

generate --out inputs.json creates the fixed inputs, without solving them.
run --input inputs.json --out run-01 requires a NEW output directory.
Only NumPy and the Python standard library are used. The parent process enforces
the 300 second attempt cap; all reference results are empirical binary64 values.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
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
SEED = 20261028
BACKGROUND = [0.1, 0.2, 0.3]
ABS_TOL = 1e-11
AGREEMENT_TOL = 5e-10
BOUND_TOL = 1e-9
MAX_DEPTH = 24
MAX_SIMPSON_EVALS = 200000
WALL_SECONDS = 300.0
SQRT_TWO = math.sqrt(2.0)
SQRT_TWO_PI = math.sqrt(2.0 * math.pi)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_json_new(path, value):
    """Never replace any existing input, partial result, or completed result."""
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def make_fixture(name, group, mu, sd, weight, color, interval=(-1.0, 1.0),
                 analytic=None):
    return {
        "id": name, "group": group, "n": len(mu),
        "interval": list(map(float, interval)),
        "mu": list(map(float, mu)), "sd": list(map(float, sd)),
        "weight": list(map(float, weight)),
        "color": [[float(v) for v in row] for row in color],
        "background": BACKGROUND.copy(), "analytic_control": analytic,
    }


def generate_inputs(output):
    import numpy as np

    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    if not output.parent.is_dir():
        raise FileNotFoundError(f"Output parent must already exist: {output.parent}")
    rgb = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    mono = [0.2, 0.5, 0.8]
    fixtures = [
        make_fixture("control-01-vacuum", "control", [], [], [], [],
                     analytic="vacuum"),
        # These immaterial parameters complete the protocol's zero-mass case.
        make_fixture("control-02-zero-mass", "control", [-0.5, 0.0, 0.5],
                     [0.2, 0.3, 0.4], [0.0] * 3, rgb, analytic="vacuum"),
        make_fixture("control-03-single", "control", [0.0], [0.3], [1.2],
                     [mono], analytic="monochrome"),
        make_fixture("control-04-clipped-single", "control", [1.0], [0.6],
                     [3.0], [mono], analytic="monochrome"),
        make_fixture("control-05-equal-color", "control",
                     np.linspace(-0.6, 0.6, 8), [0.4] * 8, [0.3] * 8,
                     [mono] * 8, analytic="monochrome"),
        make_fixture("control-06-coincident-thin", "control", [0.0] * 4,
                     [0.3] * 4, [0.02, 0.03, 0.04, 0.05],
                     rgb + [[1.0, 1.0, 1.0]], analytic="coincident"),
        make_fixture("control-07-coincident-thick", "control", [0.0] * 4,
                     [0.3] * 4, [2.0, 3.0, 4.0, 5.0],
                     rgb + [[1.0, 1.0, 1.0]], analytic="coincident"),
        make_fixture("control-08-coincident-red-blue", "control", [0.0] * 2,
                     [0.3] * 2, [1.0, 1.0], [rgb[0], rgb[2]],
                     analytic="coincident_red_blue"),
    ]
    rng = np.random.default_rng(SEED)
    for ordinal, n in enumerate([2, 4, 8, 16] * 4, 1):
        # The draw order is fixed: mu, log(sd), log(weight), then all RGB values.
        mu = rng.uniform(-1.0, 1.0, n)
        sd = np.exp(rng.uniform(math.log(0.05), math.log(0.8), n))
        weight = np.exp(rng.uniform(math.log(0.01), math.log(3.0), n))
        color = rng.uniform(0.0, 1.0, (n, 3))
        fixtures.append(make_fixture(f"generic-{ordinal:02d}-n{n}", "generic",
                                     mu, sd, weight, color))
    ordinal = 0
    for n in (4, 8, 16, 32):
        for span in (0.0, 0.3, 1.2, 3.0):
            ordinal += 1
            fixtures.append(make_fixture(
                f"structured-{ordinal:02d}-n{n}-span{span:g}", "structured",
                np.linspace(-span / 2.0, span / 2.0, n),
                [0.2 if i % 2 == 0 else 0.25 for i in range(n)],
                [2.0 / n] * n, [rgb[i % 3] for i in range(n)]))
    ordinal = 0
    for mu, sd, weight in (([-0.5, 0.5], [0.25, 0.25], [1.0, 1.0]),
                           ([-0.2, 0.4], [0.8, 0.1], [0.2, 3.0])):
        for interval in ((-0.02, 0.02), (-1.0, 0.1), (0.1, 1.0), (-0.05, 0.05)):
            ordinal += 1
            fixtures.append(make_fixture(f"clipping-{ordinal:02d}", "clipping",
                                         mu, sd, weight, [rgb[0], rgb[2]], interval))
    if len(fixtures) != 48:
        raise AssertionError("Fixture construction must produce exactly 48 cases")
    payload = {
        "schema": "t17-fixed-inputs-v1", "created_utc": utc_now(), "seed": SEED,
        "protocol_sha256": sha256(PROTOCOL),
        "generator_script_sha256": sha256(__file__),
        "numpy_version": np.__version__, "fixture_count": 48,
        "zero_mass_parameter_completion": "mu=(-.5,0,.5), sd=(.2,.3,.4), RGB primaries; all weights zero",
        "fixtures": fixtures,
    }
    write_json_new(output, payload)
    print(json.dumps({"generated": str(output), "sha256": sha256(output),
                      "fixture_count": 48, "numerical_solves": 0}), flush=True)


def normal_cdf(z):
    return 0.5 * math.erfc(-z / SQRT_TWO)


def normal_interval(lo, hi, mu, sd):
    """Use complementary tails instead of subtracting two CDFs close to one.

    This is a binary64 evaluation, not an outward-rounded interval enclosure.
    Near-coincident endpoints can still lose relative precision or underflow.
    """
    if hi == lo:
        return 0.0
    if hi < lo:
        raise ValueError("Reversed integration interval")
    zlo, zhi = (lo - mu) / sd, (hi - mu) / sd
    if zlo >= 0.0:
        return 0.5 * (math.erfc(zlo / SQRT_TWO) - math.erfc(zhi / SQRT_TWO))
    if zhi <= 0.0:
        return 0.5 * (math.erfc(-zhi / SQRT_TWO) - math.erfc(-zlo / SQRT_TWO))
    return 0.5 * (math.erf(zhi / SQRT_TWO) - math.erf(zlo / SQRT_TWO))


class ReferenceFailure(RuntimeError):
    pass


class WallCap(RuntimeError):
    pass


def check_wall(deadline):
    if time.perf_counter() >= deadline:
        raise WallCap("300-second attempt wall cap reached")


class Integrand:
    def __init__(self, fixture, deadline, np, evaluation_limit=None):
        self.fixture = fixture
        self.deadline = deadline
        self.np = np
        self.evaluations = 0
        self.evaluation_limit = evaluation_limit
        self.mu = np.asarray(fixture["mu"], dtype=np.float64)
        self.sd = np.asarray(fixture["sd"], dtype=np.float64)
        self.weight = np.asarray(fixture["weight"], dtype=np.float64)
        self.color = np.asarray(fixture["color"], dtype=np.float64).reshape((-1, 3))
        self.left = fixture["interval"][0]

    def __call__(self, t):
        check_wall(self.deadline)
        if self.evaluation_limit is not None and self.evaluations >= self.evaluation_limit:
            raise ReferenceFailure("Adaptive Simpson integrand-evaluation limit reached")
        self.evaluations += 1
        np = self.np
        if len(self.mu) == 0:
            return np.zeros(3, dtype=np.float64)
        cumulative = math.fsum(float(w) * normal_interval(self.left, t, float(mu), float(sd))
                               for mu, sd, w in zip(self.mu, self.sd, self.weight))
        z = (t - self.mu) / self.sd
        density = self.weight * np.exp(-0.5 * z * z) / (SQRT_TWO_PI * self.sd)
        value = math.exp(-cumulative) * np.sum(density[:, None] * self.color, axis=0)
        if not np.all(np.isfinite(value)):
            raise ReferenceFailure("Nonfinite integrand")
        return value


def breakpoints(fixture):
    left, right = fixture["interval"]
    values = {left, right}
    for mu, sd in zip(fixture["mu"], fixture["sd"]):
        for k in (-6, -3, 0, 3, 6):
            value = mu + k * sd
            if left < value < right:
                values.add(value)
    return sorted(values)


def adaptive_simpson(fixture, points, background_term, deadline, np):
    fun = Integrand(fixture, deadline, np, MAX_SIMPSON_EVALS)
    max_depth_used = 0
    leaves = 0
    start = time.perf_counter()

    def refine(left, right, fleft, fmid, fright, parent, tolerance, depth):
        nonlocal max_depth_used, leaves
        max_depth_used = max(max_depth_used, depth)
        mid = (left + right) / 2.0
        qleft, qright = (left + mid) / 2.0, (mid + right) / 2.0
        if qleft == left or qleft == mid or qright == mid or qright == right:
            raise ReferenceFailure("Adaptive Simpson endpoint resolution exhausted")
        fqleft, fqright = fun(qleft), fun(qright)
        slower = (mid - left) * (fleft + 4.0 * fqleft + fmid) / 6.0
        supper = (right - mid) * (fmid + 4.0 * fqright + fright) / 6.0
        combined = slower + supper
        difference = combined - parent
        error = np.abs(difference) / 15.0
        if float(np.max(error)) <= tolerance:
            leaves += 1
            return combined + difference / 15.0, error
        if depth >= MAX_DEPTH:
            raise ReferenceFailure("Adaptive Simpson maximum depth reached before tolerance")
        value_l, error_l = refine(left, mid, fleft, fqleft, fmid, slower,
                                  tolerance / 2.0, depth + 1)
        value_r, error_r = refine(mid, right, fmid, fqright, fright, supper,
                                  tolerance / 2.0, depth + 1)
        return value_l + value_r, error_l + error_r

    try:
        total = np.zeros(3, dtype=np.float64)
        error = np.zeros(3, dtype=np.float64)
        length = points[-1] - points[0]
        for left, right in zip(points[:-1], points[1:]):
            mid = (left + right) / 2.0
            fleft, fmid, fright = fun(left), fun(mid), fun(right)
            parent = (right - left) * (fleft + 4.0 * fmid + fright) / 6.0
            value, estimate = refine(left, right, fleft, fmid, fright, parent,
                                     ABS_TOL * (right - left) / length, 0)
            total += value
            error += estimate
        return {"success": True, "rgb": (total + background_term).tolist(),
                "emission_rgb": total.tolist(), "estimated_abs_error_rgb": error.tolist(),
                "evaluations": fun.evaluations, "max_depth_used": max_depth_used,
                "accepted_leaves": leaves, "wall_seconds": time.perf_counter() - start}
    except ReferenceFailure as exc:
        return {"success": False, "error": str(exc), "evaluations": fun.evaluations,
                "max_depth_used": max_depth_used, "accepted_leaves": leaves,
                "wall_seconds": time.perf_counter() - start}


def gauss_legendre(fixture, points, background_term, deadline, np, nodes, weights):
    fun = Integrand(fixture, deadline, np)
    start = time.perf_counter()
    try:
        total = np.zeros(3, dtype=np.float64)
        for left, right in zip(points[:-1], points[1:]):
            half, mid = (right - left) / 2.0, (right + left) / 2.0
            values = np.asarray([fun(float(mid + half * node)) for node in nodes])
            total += half * np.sum(weights[:, None] * values, axis=0)
        return {"success": True, "rgb": (total + background_term).tolist(),
                "emission_rgb": total.tolist(), "evaluations": fun.evaluations,
                "points_per_segment": len(nodes), "wall_seconds": time.perf_counter() - start}
    except ReferenceFailure as exc:
        return {"success": False, "error": str(exc), "evaluations": fun.evaluations,
                "points_per_segment": len(nodes), "wall_seconds": time.perf_counter() - start}


def finite_tree(value):
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(finite_tree(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(finite_tree(v) for v in value)
    return True


def validate_inputs(payload):
    if payload.get("schema") != "t17-fixed-inputs-v1" or payload.get("seed") != SEED:
        raise ValueError("Wrong input schema or seed")
    if payload.get("protocol_sha256") != sha256(PROTOCOL):
        raise ValueError("Protocol changed after input generation")
    fixtures = payload.get("fixtures", [])
    if len(fixtures) != 48 or payload.get("fixture_count") != 48:
        raise ValueError("Exactly 48 saved fixtures are required")
    if len({f["id"] for f in fixtures}) != 48:
        raise ValueError("Fixture IDs must be unique")
    if [f["group"] for f in fixtures] != ["control"] * 8 + ["generic"] * 16 + ["structured"] * 16 + ["clipping"] * 8:
        raise ValueError("Wrong fixture group ordering")
    for f in fixtures:
        n = f["n"]
        if not all(len(f[key]) == n for key in ("mu", "sd", "weight", "color")):
            raise ValueError(f"Shape mismatch: {f['id']}")
        if not finite_tree(f) or len(f["interval"]) != 2 or f["interval"][0] >= f["interval"][1]:
            raise ValueError(f"Invalid finite interval or parameter: {f['id']}")
        if any(sd <= 0 for sd in f["sd"]) or any(w < 0 for w in f["weight"]):
            raise ValueError(f"Invalid standard deviation or weight: {f['id']}")
        if any(len(c) != 3 or any(v < 0 or v > 1 for v in c) for c in f["color"]):
            raise ValueError(f"Invalid RGB: {f['id']}")
        if f["background"] != BACKGROUND:
            raise ValueError(f"Wrong background: {f['id']}")


def qualify_fixture(fixture, deadline, np, rules):
    start = time.perf_counter()
    n = fixture["n"]
    left, right = fixture["interval"]
    mu, sd, weight = (fixture[k] for k in ("mu", "sd", "weight"))
    color = np.asarray(fixture["color"], dtype=np.float64).reshape((n, 3))
    tau = [w * normal_interval(left, right, m, s) for m, s, w in zip(mu, sd, weight)]
    alpha = [-math.expm1(-t) for t in tau]
    total_tau = math.fsum(tau)
    transmission = math.exp(-total_tau)
    background_term = transmission * np.asarray(BACKGROUND, dtype=np.float64)
    order = sorted(range(n), key=lambda i: mu[i])  # Python sort preserves input ties.
    ordered = np.zeros(3, dtype=np.float64)
    prefix_transmission = 1.0
    for i in order:
        ordered += prefix_transmission * alpha[i] * color[i]
        prefix_transmission *= math.exp(-tau[i])
    ordered += background_term
    global_bound = (-math.expm1(-total_tau) * (np.max(color, axis=0) - np.min(color, axis=0))
                    if n else np.zeros(3, dtype=np.float64))
    simple_sum = np.zeros(3, dtype=np.float64)
    jensen_sum = np.zeros(3, dtype=np.float64)
    pairs = []
    for rank_i, i in enumerate(order):
        for j in order[rank_i + 1:]:
            check_wall(deadline)
            probability = normal_cdf((mu[i] - mu[j]) / math.sqrt(sd[i] ** 2 + sd[j] ** 2))
            full_mass = weight[i] * weight[j] * probability
            clipped_product = tau[i] * tau[j]
            ibar = min(full_mass, clipped_product)
            alpha_product = alpha[i] * alpha[j]
            simple = min(ibar, alpha_product)
            h = min(alpha[i], alpha[j])
            jensen = min(alpha_product, -h * math.expm1(-ibar / h)) if h > 0.0 else 0.0
            contrast = np.abs(color[i] - color[j])
            simple_sum += contrast * simple
            jensen_sum += contrast * jensen
            pairs.append({"i_input": i, "j_input": j, "full_line_inversion_probability": probability,
                          "full_line_inversion_optical_mass": full_mass,
                          "clipped_tau_product": clipped_product, "Ibar": ibar,
                          "alpha_product": alpha_product, "h": h,
                          "B_simple": simple, "B_jensen": jensen,
                          "color_contrast_rgb": contrast.tolist()})
    simple_bound = np.minimum(global_bound, simple_sum)
    jensen_bound = np.minimum(global_bound, jensen_sum)
    points = breakpoints(fixture)
    references = {
        "adaptive_simpson": adaptive_simpson(fixture, points, background_term, deadline, np),
        "gl32": gauss_legendre(fixture, points, background_term, deadline, np, *rules[32]),
        "gl64": gauss_legendre(fixture, points, background_term, deadline, np, *rules[64]),
    }
    analytic = None
    analytic_error = None
    if fixture["analytic_control"] is not None:
        if total_tau == 0.0:
            analytic = np.asarray(BACKGROUND, dtype=np.float64)
        elif fixture["analytic_control"] == "monochrome":
            analytic = -math.expm1(-total_tau) * color[0] + background_term
        else:
            average_color = np.sum(np.asarray(tau)[:, None] * color, axis=0) / total_tau
            analytic = -math.expm1(-total_tau) * average_color + background_term
        if fixture["analytic_control"] == "coincident_red_blue":
            analytic_error = np.asarray([alpha[0] ** 2 / 2.0, 0.0, alpha[0] ** 2 / 2.0])
    comparisons = {}
    failures = []
    if not all(ref["success"] for ref in references.values()):
        failures.append("reference_failure")
    for name, ref in references.items():
        if not ref["success"]:
            continue
        observed_error = np.abs(ordered - np.asarray(ref["rgb"]))
        entry = {"ordered_abs_error_rgb": observed_error.tolist(),
                 "global_slack_rgb": (global_bound - observed_error).tolist(),
                 "simple_slack_rgb": (simple_bound - observed_error).tolist(),
                 "jensen_slack_rgb": (jensen_bound - observed_error).tolist()}
        for label, bound in (("global", global_bound), ("simple", simple_bound), ("jensen", jensen_bound)):
            if float(np.max(observed_error - bound)) > BOUND_TOL:
                failures.append(f"{name}:{label}_bound_violation")
        if analytic is not None:
            difference = np.abs(np.asarray(ref["rgb"]) - analytic)
            entry["analytic_abs_difference_rgb"] = difference.tolist()
            if float(np.max(difference)) > AGREEMENT_TOL:
                failures.append(f"{name}:analytic_mismatch")
        if analytic_error is not None:
            difference = np.abs(observed_error - analytic_error)
            entry["analytic_ordered_error_abs_difference_rgb"] = difference.tolist()
            if float(np.max(difference)) > AGREEMENT_TOL:
                failures.append(f"{name}:red_blue_error_mismatch")
        comparisons[name] = entry
    for first, second in (("adaptive_simpson", "gl64"), ("gl32", "gl64"), ("adaptive_simpson", "gl32")):
        if references[first]["success"] and references[second]["success"]:
            difference = np.abs(np.asarray(references[first]["rgb"]) - np.asarray(references[second]["rgb"]))
            comparisons[f"{first}_vs_{second}"] = {"abs_difference_rgb": difference.tolist()}
            if float(np.max(difference)) > AGREEMENT_TOL:
                failures.append(f"{first}_vs_{second}:reference_mismatch")
    if float(np.max(jensen_bound - simple_bound)) > BOUND_TOL:
        failures.append("jensen_exceeds_simple")
    record = {
        "fixture": fixture, "sorted_input_indices": order,
        "full_line_optical_masses": weight, "clipped_optical_masses": tau,
        "alpha": alpha, "total_clipped_tau": total_tau,
        "total_transmission": transmission, "ordered_prefix_transmission_product": prefix_transmission,
        "ordered_rgb": ordered.tolist(), "G_rgb": global_bound.tolist(),
        "pair_simple_sum_rgb": simple_sum.tolist(), "pair_jensen_sum_rgb": jensen_sum.tolist(),
        "E_simple_rgb": simple_bound.tolist(), "E_jensen_rgb": jensen_bound.tolist(),
        "pair_count": len(pairs), "pairs": pairs,
        "breakpoints": points, "segment_count": len(points) - 1,
        "references": references, "comparisons": comparisons,
        "analytic_rgb": None if analytic is None else analytic.tolist(),
        "analytic_ordered_abs_error_rgb": None if analytic_error is None else analytic_error.tolist(),
        "wall_seconds": time.perf_counter() - start,
    }
    finite = finite_tree(record)
    if not finite:
        failures.append("nonfinite_output")
    record["gates"] = {"all_finite": finite, "passed": not failures, "failures": failures,
                       "agreement_tolerance": AGREEMENT_TOL, "bound_tolerance": BOUND_TOL}
    return record


def summarize(records):
    eligible = [r for r in records if r["fixture"]["group"] != "control" and r["fixture"]["n"] >= 4]
    counts = {}
    for threshold in (0.001, 0.01):
        qualified = [r for r in eligible if r["gates"]["passed"]]
        passes = [r["fixture"]["id"] for r in qualified
                  if max(r["E_jensen_rgb"]) <= threshold and max(r["G_rgb"]) > threshold]
        simple_passes = [r["fixture"]["id"] for r in qualified
                         if max(r["E_simple_rgb"]) <= threshold and max(r["G_rgb"]) > threshold]
        counts[str(threshold)] = {"eligible_count": len(eligible),
                                  "numerically_qualified_eligible_count": len(qualified),
                                  "jensen_informative_count": len(passes), "jensen_fixture_ids": passes,
                                  "simple_informative_count": len(simple_passes), "simple_fixture_ids": simple_passes}
    return {
        "completed_count": len(records),
        "qualified_count": sum(r["gates"]["passed"] for r in records),
        "all_48_numerically_qualified": len(records) == 48 and all(r["gates"]["passed"] for r in records),
        "failures": [{"id": r["fixture"]["id"], "failures": r["gates"]["failures"]}
                     for r in records if not r["gates"]["passed"]],
        "informative_counts": counts,
        "reference_evaluations": {name: sum(r["references"][name]["evaluations"] for r in records)
                                  for name in ("adaptive_simpson", "gl32", "gl64")},
        "floating_point_certificate": False, "speedup_claim": False,
    }


def worker(input_path, output):
    import numpy as np

    start = time.perf_counter()
    deadline = start + WALL_SECONDS
    output = Path(output).resolve()
    input_path = Path(input_path).resolve()
    manifest = json.loads((output / "attempt.json").read_text(encoding="utf-8"))
    if manifest["input_sha256"] != sha256(input_path) or manifest["script_sha256"] != sha256(__file__) or manifest["protocol_sha256"] != sha256(PROTOCOL):
        raise ValueError("Source/input identity changed before worker start")
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    validate_inputs(payload)
    records = []
    cases_dir = output / "cases"
    cases_dir.mkdir(exist_ok=False)
    try:
        rules = {n: np.polynomial.legendre.leggauss(n) for n in (32, 64)}
        with (output / "progress.jsonl").open("x", encoding="utf-8", newline="\n") as progress:
            for index, fixture in enumerate(payload["fixtures"], 1):
                check_wall(deadline)
                result = qualify_fixture(fixture, deadline, np, rules)
                write_json_new(cases_dir / f"{index:02d}-{fixture['id']}.json", result)
                records.append(result)
                line = {"completed": index, "id": fixture["id"], "passed": result["gates"]["passed"],
                        "elapsed_seconds": time.perf_counter() - start}
                progress.write(json.dumps(line, allow_nan=False) + "\n")
                progress.flush()
                if index % 8 == 0:
                    print(json.dumps(line), flush=True)
        summary = summarize(records)
        final = {"schema": "t17-qualification-results-v1", "completed_utc": utc_now(),
                 "input_sha256": sha256(input_path), "script_sha256": sha256(__file__),
                 "protocol_sha256": sha256(PROTOCOL), "numpy_version": np.__version__,
                 "python_version": sys.version, "worker_wall_seconds": time.perf_counter() - start,
                 "summary": summary, "cases": records}
        write_json_new(output / "results.json", final)
        print(json.dumps({"summary": summary, "worker_wall_seconds": final["worker_wall_seconds"]}), flush=True)
        return 0 if summary["all_48_numerically_qualified"] else 2
    except Exception as exc:
        write_json_new(output / "worker-failure.json", {
            "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc(),
            "completed_count": len(records), "partial_summary": summarize(records),
            "elapsed_seconds": time.perf_counter() - start,
        })
        raise


def run_supervised(input_path, output):
    start = time.perf_counter()
    input_path = Path(input_path).resolve(strict=True)
    output = Path(output).resolve()
    if not output.parent.is_dir():
        raise FileNotFoundError(f"Output parent must already exist: {output.parent}")
    output.mkdir(exist_ok=False)
    before = {"input_sha256": sha256(input_path), "script_sha256": sha256(__file__),
              "protocol_sha256": sha256(PROTOCOL)}
    write_json_new(output / "attempt.json", {
        "schema": "t17-attempt-v1", "started_utc": utc_now(), "input_path": str(input_path),
        "script_path": str(Path(__file__).resolve()), "protocol_path": str(PROTOCOL),
        "wall_cap_seconds": WALL_SECONDS, "python_executable": sys.executable,
        "parent_pid": os.getpid(), **before,
    })
    command = [sys.executable, "-I", "-B", "-u", "-X", "utf8", str(Path(__file__).resolve()),
               "_worker", "--input", str(input_path), "--out", str(output)]
    process = None
    timeout = False
    error = None
    returncode = 1
    try:
        process = subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
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
    after = {"input_sha256": sha256(input_path), "script_sha256": sha256(__file__),
             "protocol_sha256": sha256(PROTOCOL)}
    identities_unchanged = before == after
    if not identities_unchanged and returncode == 0:
        returncode = 2
    write_json_new(output / "execution.json", {
        "completed_utc": utc_now(), "child_pid": None if process is None else process.pid,
        "returncode": returncode, "wall_cap_reached": timeout, "launch_error": error,
        "supervisor_wall_seconds": time.perf_counter() - start,
        "identities_before": before, "identities_after": after,
        "identities_unchanged": identities_unchanged,
    })
    return returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command")
    generate = subs.add_parser("generate", help="Save the 48 fixed fixtures; no solves")
    generate.add_argument("--out", required=True)
    run = subs.add_parser("run", help="Read saved input and use a NEW output directory")
    run.add_argument("--input", required=True)
    run.add_argument("--out", required=True)
    internal = subs.add_parser("_worker", help=argparse.SUPPRESS)
    internal.add_argument("--input", required=True)
    internal.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command is None:
        print(json.dumps({"task": "T17", "default_action": "plan_only", "fixture_count": 48,
                          "commands": ["generate --out NEW_INPUT_JSON", "run --input EXISTING_INPUT_JSON --out NEW_DIRECTORY"],
                          "wall_cap_seconds": WALL_SECONDS, "requires": ["numpy"],
                          "gpu": False, "formal_certificate": False}), flush=True)
        return 0
    if args.command == "generate":
        generate_inputs(args.out)
        return 0
    if args.command == "run":
        return run_supervised(args.input, args.out)
    return worker(args.input, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
