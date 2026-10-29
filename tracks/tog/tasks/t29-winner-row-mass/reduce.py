"""One T29 saved-data reduction; no integration or deployment timing.
Default is plan-only. Run needs a pre-execution freeze and a fresh directory.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = "tracks/tog/tasks/t29-winner-row-mass/"
PARENT = "f260268c9c70d8ba297cc7853ed2f365dc212b09"
INPUT = "tracks/tog/tasks/t17-order-inversion-bound/inputs.json"
REF = "tracks/tog/tasks/t18-reference-robustness/run-01/results.json"
OLD = "tracks/tog/tasks/t21-winner-prefix-bound/run-01/results.json"
SOURCE_SHA = {
    INPUT: "5cccf0238c679e14bc50e67d2d24726a58295b484b1d3464bf77d4eca0491cb7",
    REF: "fa4fb6887c6b38e800f18e919634821b3ee51c2fb0122cd0dbb4047eead7873d",
    OLD: "94d3ad607ba70ee6d7192643e6ad39ec3802f2a269b12df8cbfe87e59917bf83",
}
CAPS = ("simple", "jensen")
EPS = (0.001, 0.01)
VARIANTS = ("raw", "cheap", "knapsack")
ARITH = 1e-12
ENCLOSURE = 1e-9
WALL = 60.0

def require(value, message):
    if not value:
        raise ValueError(message)

def check_time(deadline):
    if time.perf_counter() >= deadline:
        raise TimeoutError("T29 saved-reduction deadline")

def read(path):
    def bad(value):
        raise ValueError("Nonfinite JSON: " + value)
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=bad)

def identity(path):
    b = path.read_bytes()
    return {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}

def identities(freeze):
    require(freeze["parent_commit"] == PARENT, "Parent differs")
    got = {}
    for item in freeze["artifacts"]:
        rel = item["path"]
        require(rel not in got and not Path(rel).is_absolute()
                and ".." not in Path(rel).parts, "Invalid freeze path")
        got[rel] = identity(ROOT / rel)
        require(got[rel] == {k: item[k] for k in ("bytes", "sha256")},
                "Changed frozen file: " + rel)
    needed = set(SOURCE_SHA) | {TASK + x for x in
                              ("PROTOCOL.md", "DERIVATION.md", "reduce.py")}
    require(needed <= set(got), "Missing frozen artifact")
    for rel, digest in SOURCE_SHA.items():
        require(got[rel]["sha256"] == digest, "Unexpected source: " + rel)
    return got

def finite(values, lower=None, upper=None):
    for x in values:
        require(isinstance(x, (int, float)) and not isinstance(x, bool)
                and math.isfinite(x), "Nonfinite or nonnumeric value")
        if lower is not None:
            require(x >= lower, "Value below allowed range")
        if upper is not None:
            require(x <= upper, "Value above allowed range")

def structural(f, s, old):
    n = f["n"]
    require(s["fixture"] == f and old["id"] == f["id"], "Fixture mismatch")
    require(n >= 0 and all(len(f[k]) == n for k in ("mu", "sd", "weight", "color")),
            "Invalid fixture sizes")
    order = sorted(range(n), key=f["mu"].__getitem__)
    require(order == s["sorted_input_indices"] == old["sorted_input_indices"],
            "Order mismatch")
    require(old["n"] == n and old["group"] == f["group"], "Old metadata mismatch")
    for k in ("clipped_optical_masses", "ordered_rgb", "G_rgb"):
        require(s[k] == old[k], "T18/T21 disagreement: " + k)
    require(s["gates"]["passed"] and s["gates"]["all_finite"]
            and s["gates"]["reference_global_budget_pass"]
            and not s["gates"]["failures"] and old["checks"]["qualified"],
            "Inherited qualification absent")
    require(len(s["clipped_optical_masses"]) == len(s["alpha"])
            == len(old["prefixes_by_sorted_rank"]) == n, "Input vector shape")
    finite(s["clipped_optical_masses"], 0)
    finite(s["alpha"], 0, 1)
    finite(old["prefixes_by_sorted_rank"], 0, 1)
    if n:
        require(old["prefixes_by_sorted_rank"][0] == 1, "First prefix differs")
    finite(s["G_rgb"], 0)
    finite(s["ordered_rgb"])
    for c in f["color"]:
        require(len(c) == 3, "Color shape")
        finite(c, 0, 1)
    pairs = s["pairs"]
    wanted = {(order[i], order[j]) for i in range(n) for j in range(i + 1, n)}
    got = [(p["i_input"], p["j_input"]) for p in pairs]
    require(len(got) == n*(n-1)//2 == s["pair_count"]
            and len(set(got)) == len(got) and set(got) == wanted, "Pair set differs")
    for p in pairs:
        finite([p["B_simple"], p["B_jensen"]], 0)
        require(p["B_jensen"] <= p["B_simple"] + ARITH, "Inherited cap dominance")
    for ref in ("adaptive_simpson", "gl32", "gl64"):
        require(s["references"][ref]["success"], "Reference unsuccessful")
        finite(s["references"][ref]["rgb"])
    for e in EPS:
        require(str(e) in old["per_epsilon"], "Old population missing")

def row_opt(items, budget, counters):
    """Only coefficients/caps/rank keys and the row budget enter this solver."""
    def fs(values):
        counters["fsum_calls"] += 1
        return math.fsum(values)
    # Each item: j input index, stable sorted rank, nonnegative coefficient, cap.
    ordered = sorted(items, key=lambda t: (-t[2], t[1]))
    counters["coefficient_sort_calls"] += 1
    counters["coefficient_sort_items"] += len(items)
    remaining, lam, exhausted = budget, 0.0, False
    cert = []
    for j, rank, a, cap in ordered:
        counters["greedy_item_visits"] += 1
        take = 0.0 if exhausted else min(cap, remaining)
        if not exhausted:
            remaining = max(0.0, remaining - take)
            counters["budget_subtractions"] += 1
            if remaining == 0.0:
                lam, exhausted = a, True
        cert.append({"j_input": j, "a": a, "C": cap, "x": take})
    raw = fs(a*cap for _, _, a, cap in ordered)
    maximum = max((t[2] for t in ordered), default=0.0)
    cheap = min(raw, budget*maximum)
    primal = fs(t["a"]*t["x"] for t in cert)
    dual = lam*budget + fs(t["C"]*max(t["a"]-lam, 0.0) for t in cert)
    used = fs(t["x"] for t in cert)
    capacity = fs(t["C"] for t in cert)
    counters["row_objective_products"] += 3*len(items)+2
    return {"raw": raw, "cheap": cheap, "knapsack": dual, "primal": primal,
            "lambda": lam, "used": used, "capacity": capacity, "items": cert}

def formula(color, order, alpha, prefixes, pairs, global_bound, deadline):
    """No fixture identifier, saved reference, oracle error, or epsilon input."""
    n = len(order)
    counters = {k: 0 for k in (
        "row_budget_products", "formula_pair_traversals", "prefix_cap_products",
        "color_differences", "coefficient_sort_calls", "coefficient_sort_items",
        "greedy_item_visits", "budget_subtractions", "row_objective_products",
        "fsum_calls")}
    rank = {i: k for k, i in enumerate(order)}
    budgets = [prefixes[k]*alpha[i] for k, i in enumerate(order)]
    counters["row_budget_products"] = n
    row_items = {cap: [[[] for _ in range(6)] for _ in range(n)] for cap in CAPS}
    for pair in pairs:
        check_time(deadline)
        counters["formula_pair_traversals"] += 1
        i, j = pair["i_input"], pair["j_input"]
        ri, rj = rank[i], rank[j]
        differences = [color[j][q]-color[i][q] for q in range(3)]
        counters["color_differences"] += 3
        for cap in CAPS:
            c = prefixes[ri]*pair["B_"+cap]
            counters["prefix_cap_products"] += 1
            for q, d in enumerate(differences):
                if d and c > 0:
                    side = 2*q + (0 if d > 0 else 1)
                    row_items[cap][ri][side].append((j, rj, abs(d), c))
    out = {}
    for cap in CAPS:
        rows = []
        for ri, i in enumerate(order):
            check_time(deadline)
            rows.append({"i_input": i, "q": budgets[ri],
                         "components": [row_opt(items, budgets[ri], counters)
                                        for items in row_items[cap][ri]]})
        variants = {}
        for name in VARIANTS:
            uv = []
            for side in range(6):
                uv.append(math.fsum(r["components"][side][name] for r in rows))
                counters["fsum_calls"] += 1
            upper = [min(global_bound[q], uv[2*q]) for q in range(3)]
            lower = [-min(global_bound[q], uv[2*q+1]) for q in range(3)]
            variants[name] = {"positive_sum_rgb": uv[::2], "negative_sum_rgb": uv[1::2],
                              "lower_rgb": lower, "upper_rgb": upper,
                              "E_rgb": [max(-lower[q], upper[q]) for q in range(3)]}
        out[cap] = {"rows": rows, "variants": variants}
    return {"budgets_by_sorted_rank": budgets, "caps": out, "counters": counters}

def audit(f, s, old, reduced):
    maxima = {"arithmetic_difference": 0.0, "primal_dual_gap": 0.0,
              "row_budget_excess": 0.0, "dominance_excess": 0.0,
              "reference_enclosure_excess": 0.0, "raw_row_bound_above_G": 0.0}
    def close(a, b, key="arithmetic_difference"):
        diff = abs(a-b); maxima[key] = max(maxima[key], diff)
        require(diff <= ARITH, key + " failed: " + str(diff))
    def leq(a, b, key="dominance_excess"):
        excess = max(0.0, a-b); maxima[key] = max(maxima[key], excess)
        require(excess <= ARITH, key + " failed: " + str(excess))
    close(math.fsum(reduced["budgets_by_sorted_rank"]), 1.0-s["total_transmission"])
    for cap in CAPS:
        for row in reduced["caps"][cap]["rows"]:
            finite([row["q"]], 0, 1)
            for comp in row["components"]:
                finite([comp[k] for k in ("raw", "cheap", "knapsack", "primal",
                                          "lambda", "used", "capacity")], 0)
                for item in comp["items"]:
                    finite([item[k] for k in ("a", "C", "x")], 0)
                    leq(item["x"], item["C"], "row_budget_excess")
                leq(comp["used"], row["q"], "row_budget_excess")
                close(comp["primal"], comp["knapsack"], "primal_dual_gap")
                leq(comp["knapsack"], comp["cheap"])
                leq(comp["cheap"], comp["raw"])
        for q in range(3):
            original = old["caps"][cap]["combined"]
            raw = reduced["caps"][cap]["variants"]["raw"]
            for key in ("positive_sum_rgb", "negative_sum_rgb", "lower_rgb", "upper_rgb", "E_rgb"):
                close(raw[key][q], original[key][q])
            for name in VARIANTS:
                values = reduced["caps"][cap]["variants"][name]
                finite(values["E_rgb"], 0)
                if name != "raw":
                    for key in ("positive_sum_rgb", "negative_sum_rgb"):
                        leq(values[key][q], s["G_rgb"][q], "raw_row_bound_above_G")
                if f["n"] <= 2:
                    close(values["E_rgb"][q], raw["E_rgb"][q])
    for name in VARIANTS:
        for q in range(3):
            leq(reduced["caps"]["jensen"]["variants"][name]["E_rgb"][q],
                reduced["caps"]["simple"]["variants"][name]["E_rgb"][q])
    observations = {}
    refs = {k: s["references"][k]["rgb"] for k in ("adaptive_simpson", "gl32", "gl64")}
    if s["analytic_rgb"] is not None:
        refs["analytic"] = s["analytic_rgb"]
    for ref, rgb in refs.items():
        delta = [rgb[q]-s["ordered_rgb"][q] for q in range(3)]
        observations[ref] = {"delta_rgb": delta, "max_abs_error": max(map(abs, delta))}
        for cap in CAPS:
            for name in VARIANTS:
                v = reduced["caps"][cap]["variants"][name]
                for q in range(3):
                    excess = max(0.0, v["lower_rgb"][q]-delta[q],
                                 delta[q]-v["upper_rgb"][q], abs(delta[q])-v["E_rgb"][q])
                    maxima["reference_enclosure_excess"] = max(
                        maxima["reference_enclosure_excess"], excess)
                    require(excess <= ENCLOSURE, "Saved reference enclosure failed")
    per_epsilon = {}
    for e in EPS:
        before = old["per_epsilon"][str(e)]
        unsolved = before["common_unsolved"]
        flags = {"common_unsolved": unsolved, "common_path": before["common_path"], "caps": {}}
        for cap in CAPS:
            accepts = {name: max(reduced["caps"][cap]["variants"][name]["E_rgb"]) <= e
                       for name in VARIANTS}
            # Existing results are also checked without introducing tolerance at admission.
            require(accepts["raw"] == before["caps"][cap]["new_accept"],
                    "Reconstructed T21 threshold classification changed")
            flags["caps"][cap] = {**accepts,
                "cheap_added": unsolved and accepts["cheap"] and not accepts["raw"],
                "lp_added_over_t21": unsolved and accepts["knapsack"] and not accepts["raw"],
                "lp_specific_added": unsolved and accepts["knapsack"]
                                     and not accepts["raw"] and not accepts["cheap"]}
        per_epsilon[str(e)] = flags
    return {"maxima": maxima, "references": observations, "per_epsilon": per_epsilon,
            "qualified": True}

def run(out):
    started = time.perf_counter(); deadline = started+WALL
    out = Path(out).resolve(); out.mkdir(parents=True, exist_ok=False)
    record = {"schema": "t29-row-mass-saved-reduction-v1", "qualified": False,
              "cases": [], "failures": [], "parent_commit": PARENT,
              "epsilons": list(EPS), "allowances": {"arithmetic": ARITH, "enclosure": ENCLOSURE},
              "new_cdf_exp_integrand_quadrature_evaluations": 0,
              "novelty_or_speed_or_TOG_claim": False, "development_data_only": True}
    journal = (out/"journal.jsonl").open("x", encoding="utf-8", newline="\n")
    try:
        freeze_path = HERE/"freeze.json"; freeze = read(freeze_path)
        record["freeze_before"] = identity(freeze_path)
        record["identities_before"] = identities(freeze)
        inputs, refs, prior = read(ROOT/INPUT), read(ROOT/REF), read(ROOT/OLD)
        require(inputs["fixture_count"] == len(inputs["fixtures"]) == len(refs["cases"])
                == len(prior["cases"]) == 48, "Original 48-case count")
        require(refs["summary"]["all_48_numerically_qualified"] and prior["qualified"],
                "Inherited task qualification absent")
        require(sum(f["n"] for f in inputs["fixtures"]) == 399
                and sum(len(c["pairs"]) for c in refs["cases"]) == 3272, "Input totals")
        for f, s, old in zip(inputs["fixtures"], refs["cases"], prior["cases"]):
            check_time(deadline); structural(f, s, old)
        for f, s, old in zip(inputs["fixtures"], refs["cases"], prior["cases"]):
            check_time(deadline)
            reduced = formula(f["color"], s["sorted_input_indices"], s["alpha"],
                              old["prefixes_by_sorted_rank"], s["pairs"], s["G_rgb"], deadline)
            case = {"id": f["id"], "group": f["group"], "n": f["n"], **reduced}
            record["cases"].append(case)
            case["checks"] = audit(f, s, old, reduced)
            # Persist each completed case before proceeding; a timeout can leave
            # an incomplete final line, but cannot erase earlier flushed cases.
            json.dump(case, journal, ensure_ascii=False, allow_nan=False)
            journal.write("\n")
            journal.flush()
        summary = {}
        for e in EPS:
            key = str(e); eligible = [c for c in record["cases"]
                                      if c["checks"]["per_epsilon"][key]["common_unsolved"]]
            require(len(eligible) == 28, "Common-unsolved population changed")
            entry = {"population": [c["id"] for c in eligible], "caps": {}}
            for cap in CAPS:
                entry["caps"][cap] = {
                    name: [c["id"] for c in eligible
                           if c["checks"]["per_epsilon"][key]["caps"][cap][name]]
                    for name in (*VARIANTS, "cheap_added", "lp_added_over_t21", "lp_specific_added")}
                require(len(entry["caps"][cap]["raw"]) == (1 if e == .001 else 4),
                        "Historical T21 count mismatch")
            summary[key] = entry
        specific = sorted(set().union(*(set(summary[str(e)]["caps"]["jensen"]["lp_specific_added"])
                                        for e in EPS)))
        record["summary"] = summary
        record["distinct_lp_specific_added_jensen"] = specific
        record["maxima"] = {k: max(c["checks"]["maxima"][k] for c in record["cases"])
                            for k in record["cases"][0]["checks"]["maxima"]}
        record["counters"] = {k: sum(c["counters"][k] for c in record["cases"])
                              for k in record["cases"][0]["counters"]}
        require(record["counters"]["formula_pair_traversals"] == 3272
                and record["counters"]["prefix_cap_products"] == 6544
                and record["counters"]["row_budget_products"] == 399
                and record["counters"]["coefficient_sort_calls"] == 399*12,
                "Operation counts inconsistent")
        record["identities_after"] = identities(freeze)
        record["freeze_after"] = identity(freeze_path)
        require(record["identities_before"] == record["identities_after"]
                and record["freeze_before"] == record["freeze_after"], "Evidence changed")
        check_time(deadline)
        record["qualified"] = True
        record["decision"] = ("retain_LP_specific_acceptance_observation_prepare_cost_only"
                              if specific else "archive_row_optimization_on_fixed_scope")
        record["allows_preparation_only"] = bool(specific)
    except Exception as exc:
        record["failures"].append({"type": type(exc).__name__, "message": str(exc),
                                   "traceback": traceback.format_exc()})
        record["qualified"] = False
        record["decision"] = "unqualified_no_retry"
        record["allows_preparation_only"] = False
    finally:
        journal.close()
    record["allows_next_execution"] = False
    record["worker_seconds_before_serialization"] = time.perf_counter()-started
    record["accounting"] = "Saved-data analysis only. Pair/mass/prefix production and fallback costs unmeasured."
    with (out/"results.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"qualified": record["qualified"], "cases": len(record["cases"]),
                      "decision": record["decision"], "failures": record["failures"]}))
    return 0 if record["qualified"] else 2

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")
    job = sub.add_parser("run"); job.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command is None:
        print(json.dumps({"mode": "plan-only", "maximum_invocations": 1, "wall_cap_seconds": WALL}))
        return 0
    return run(args.out)

if __name__ == "__main__":
    raise SystemExit(main())
