"""Frozen T74 scalar confirmation; importing this module performs no numerics.

Only ``main`` invokes NumPy or quadrature.  The external supervisor owns the
exclusive invocation marker, full child interval, and operating-system limits.
"""

import argparse
import json
import math
from pathlib import Path
import sys
import time


AMPLITUDE = 1.5
TOLERANCE = 1.0e-9
SMALL_SHEAR_TOLERANCE = 1.0e-5
LEGENDRE_ORDERS = (96, 192)
LAGUERRE_ORDERS = (64, 128)
CONDITIONAL_X = (0.0, 0.5, 1.0, 2.0)
SHEAR_AMPLITUDES = (0.0, 0.001, 0.25, 0.5, 1.0, 2.0)


def potential_and_axial_derivative(np, r, z):
    """Independent initial radial erf potential, with the fixed local series."""
    r, z = np.broadcast_arrays(np.asarray(r, dtype=float), np.asarray(z, dtype=float))
    radius = np.hypot(r, z)
    phi = np.empty_like(radius)
    derivative_over_radius = np.empty_like(radius)
    small = radius < 0.5
    if np.any(small):
        radius_squared = radius[small] ** 2
        power = np.ones_like(radius_squared)
        previous_power = np.ones_like(radius_squared)
        potential_sum = np.zeros_like(radius_squared)
        derivative_sum = np.zeros_like(radius_squared)
        coefficient = 1.0
        for n in range(20):
            potential_sum += coefficient * power / (2 * n + 3)
            if n:
                derivative_sum += coefficient * (2 * n) * previous_power / (2 * n + 3)
            previous_power = power
            power = power * radius_squared
            coefficient *= -0.5 / (n + 1)
        phi[small] = AMPLITUDE * potential_sum
        derivative_over_radius[small] = AMPLITUDE * derivative_sum
    regular = ~small
    if np.any(regular):
        radial = radius[regular]
        erf_values = np.fromiter(
            (math.erf(float(value) / math.sqrt(2.0)) for value in radial.flat),
            dtype=float,
            count=int(radial.size),
        ).reshape(radial.shape)
        exponential = np.exp(-0.5 * radial * radial)
        radial_integral = math.sqrt(math.pi / 2.0) * erf_values - radial * exponential
        phi[regular] = AMPLITUDE * radial_integral / radial ** 3
        derivative_over_radius[regular] = (
            AMPLITUDE * (radial ** 3 * exponential - 3.0 * radial_integral) / radial ** 5
        )
    phi_z = z * derivative_over_radius
    if not np.all(np.isfinite(phi)) or not np.all(np.isfinite(phi_z)):
        raise ArithmeticError("nonfinite radial potential or axial derivative")
    return phi, phi_z


def checked_rule(np, nodes, weights, name):
    nodes, weights = np.asarray(nodes, dtype=float), np.asarray(weights, dtype=float)
    if (nodes.ndim != 1 or nodes.shape != weights.shape
            or not np.all(np.isfinite(nodes)) or not np.all(np.isfinite(weights))
            or not np.all(np.diff(nodes) > 0.0) or not np.all(weights > 0.0)):
        raise ArithmeticError("invalid quadrature rule: " + name)
    return nodes, weights


def analytic_values():
    rate0 = 16.0 * AMPLITUDE * math.sqrt(2.0 / 3.0) / 45.0
    j0 = 15.0 * math.sqrt(math.pi) / 16.0
    j1 = math.sqrt(2.0 * math.pi / 3.0) / 3.0
    j2 = math.sqrt(math.pi) * (
        2.0 * math.atan(1.0 / (2.0 * math.sqrt(2.0))) - 5.0 / (6.0 * math.sqrt(2.0))
    )
    captured = j1 * j1 / (j0 * j2)
    translation_residual = 1.0 - captured
    shear_residual = 1.0 - (1.0 + 32.0 / 441.0) * captured
    return {
        "J0": j0, "J1": j1, "J2": j2,
        "rates": {"e0": rate0, "e1": -8.0 * rate0 / 21.0, "n": -4.0 * rate0 / 21.0},
        "metrics": {
            "norm_e1_over_e0": 0.5,
            "norm_n_over_e0": 1.5,
            "orthogonality_e0_e1": 0.0,
            "orthogonality_e0_n": 0.0,
            "orthogonality_e1_n": 0.0,
            "cross_e1_over_e0": -4.0 / 21.0,
            "cross_n_over_e0": -2.0 / 7.0,
            "rate_e0_over_closed_e0": 1.0,
            "rate_e1_over_closed_e0": -8.0 / 21.0,
            "rate_n_over_closed_e0": -4.0 / 21.0,
            "translation_relative_residual_squared": translation_residual,
            "translation_shear_relative_residual_squared": shear_residual,
            "fraction_translation_residual_removed": (translation_residual - shear_residual) / translation_residual,
            "shear_gain_over_translation_energy": 32.0 / 441.0,
            "n_energy_over_translation_energy": 8.0 / 147.0,
            "n_energy_over_shear_gain": 0.75,
        },
        "kinetic_energy_zero": AMPLITUDE ** 2 * math.pi ** 1.5 / 3.0,
        "small_shear_coefficient": 6.0 / 35.0,
    }


def field_integrals(np, legendre_nodes, legendre_weights, closed):
    r = 5.0 * (legendre_nodes + 1.0)
    z = 10.0 * legendre_nodes
    radial_weights = 5.0 * legendre_weights
    axial_weights = 10.0 * legendre_weights
    rr, zz = r[:, None], z[None, :]
    x = 0.5 * rr * rr
    q = AMPLITUDE * np.exp(-x - 0.5 * zz * zz)
    phi, _ = potential_and_axial_derivative(np, rr, zz)
    field = 2.0 * zz * phi * q
    basis = (zz * q, zz * (x - 1.0) * q, (zz ** 3 - 1.5 * zz) * q)
    names = ("e0", "e1", "n")
    measure = 2.0 * math.pi * rr ** 3 * radial_weights[:, None] * axial_weights[None, :]

    def integrate(value):
        answer = float(np.sum(measure * value, dtype=np.float64))
        if not math.isfinite(answer):
            raise ArithmeticError("nonfinite direct integral")
        return answer

    gram = [[integrate(left * right) for right in basis] for left in basis]
    cross = [integrate(field * item) for item in basis]
    diagonal = [gram[index][index] for index in range(3)]
    field_norm = integrate(field * field)
    if min(diagonal + [field_norm]) <= 0.0 or cross[0] == 0.0:
        raise ArithmeticError("nonpositive direct norm or zero translation cross product")
    rates = [cross[index] / diagonal[index] for index in range(3)]
    energies = [cross[index] * rates[index] for index in range(3)]
    if min(energies) <= 0.0:
        raise ArithmeticError("nonpositive projected direction energy")
    # These are positive-weight sums of squares, never norm differences.
    residual0 = integrate((field - rates[0] * basis[0]) ** 2)
    residual01 = integrate((field - rates[0] * basis[0] - rates[1] * basis[1]) ** 2)
    if residual0 <= 0.0 or residual01 < 0.0:
        raise ArithmeticError("invalid direct squared residual")
    closed_rate0 = closed["rates"]["e0"]
    metrics = {
        "norm_e1_over_e0": diagonal[1] / diagonal[0],
        "norm_n_over_e0": diagonal[2] / diagonal[0],
        "orthogonality_e0_e1": gram[0][1] / math.sqrt(diagonal[0] * diagonal[1]),
        "orthogonality_e0_n": gram[0][2] / math.sqrt(diagonal[0] * diagonal[2]),
        "orthogonality_e1_n": gram[1][2] / math.sqrt(diagonal[1] * diagonal[2]),
        "cross_e1_over_e0": cross[1] / cross[0],
        "cross_n_over_e0": cross[2] / cross[0],
        "rate_e0_over_closed_e0": rates[0] / closed_rate0,
        "rate_e1_over_closed_e0": rates[1] / closed_rate0,
        "rate_n_over_closed_e0": rates[2] / closed_rate0,
        "translation_relative_residual_squared": residual0 / field_norm,
        "translation_shear_relative_residual_squared": residual01 / field_norm,
        "fraction_translation_residual_removed": (residual0 - residual01) / residual0,
        "shear_gain_over_translation_energy": energies[1] / energies[0],
        "n_energy_over_translation_energy": energies[2] / energies[0],
        "n_energy_over_shear_gain": energies[2] / energies[1],
    }
    errors = {key: abs(value - closed["metrics"][key]) for key, value in metrics.items()}
    rate_errors = {name: abs(rates[index] - closed["rates"][name]) for index, name in enumerate(names)}
    return {
        "basis_order": list(names), "gram": gram,
        "cross": dict(zip(names, cross)), "rates": dict(zip(names, rates)),
        "direction_energies": dict(zip(names, energies)), "F_norm_squared": field_norm,
        "direct_squared_residuals": {"translation": residual0, "translation_shear": residual01},
        "metrics": metrics, "absolute_errors": errors,
        "rate_absolute_errors": rate_errors,
        "maximum_absolute_normalized_error": max(errors.values()),
        "checks": {
            "closed_normalized_metrics": all(value <= TOLERANCE for value in errors.values()),
            "closed_rates": all(value <= TOLERANCE for value in rate_errors.values()),
            "nonnegative_direct_residuals": residual0 >= 0.0 and residual01 >= 0.0,
        },
    }


def conditional_integrals(np, legendre_nodes, legendre_weights):
    z = 10.0 * legendre_nodes
    gaussian_weights = (10.0 * legendre_weights) * np.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)

    def expectation(value):
        answer = float(np.sum(gaussian_weights * value, dtype=np.float64))
        if not math.isfinite(answer):
            raise ArithmeticError("nonfinite conditional expectation")
        return answer

    mass = expectation(np.ones_like(z))
    if mass <= 0.0:
        raise ArithmeticError("nonpositive conditional normalization")
    mean = expectation(z) / mass
    second = expectation(z ** 2) / mass
    third = expectation(z ** 3) / mass
    variance = second - mean * mean
    results = []
    for x in CONDITIONAL_X:
        phi, phi_z = potential_and_axial_derivative(np, math.sqrt(2.0 * x), z)
        mass_derivative = 2.0 * expectation(z * phi)
        mean_derivative = (2.0 * expectation(z ** 2 * phi) - mean * mass_derivative) / mass
        second_derivative = (2.0 * expectation(z ** 3 * phi) - second * mass_derivative) / mass
        third_derivative = (2.0 * expectation(z ** 4 * phi) - third * mass_derivative) / mass
        centered_derivative = (third_derivative
            - 3.0 * (mean_derivative * second + mean * second_derivative)
            + 6.0 * mean * mean * mean_derivative)
        moment_expression = 2.0 * expectation((z ** 4 - 3.0 * z ** 2) * phi)
        derivative_expression = 2.0 * expectation(z ** 3 * phi_z)
        errors = {
            "normalization": abs(mass - 1.0),
            "initial_mean": abs(mean), "initial_variance": abs(variance - 1.0),
            "initial_third_central_moment": abs(third - 3.0 * mean * second + 2.0 * mean ** 3),
            "normalization_derivative": abs(mass_derivative),
            "second_raw_moment_derivative": abs(second_derivative),
            "two_kappa_expressions": abs(moment_expression - derivative_expression),
            "moment_expression_vs_centered_quotient": abs(moment_expression - centered_derivative),
            "derivative_expression_vs_centered_quotient": abs(derivative_expression - centered_derivative),
        }
        results.append({
            "x": x, "normalization": mass, "initial_mean": mean, "initial_variance": variance,
            "normalization_derivative": mass_derivative, "mean_derivative": mean_derivative,
            "second_raw_moment_derivative": second_derivative,
            "kappa_dot_moment_expression": moment_expression,
            "kappa_dot_derivative_expression": derivative_expression,
            "kappa_dot_centered_quotient": centered_derivative,
            "absolute_errors": errors,
            "checks": {
                "normalization_centering_and_agreement": all(value <= TOLERANCE for value in errors.values()),
                "strictly_negative": max(moment_expression, derivative_expression, centered_derivative) < 0.0,
            },
        })
    return results


def energy_integrals(np, legendre_nodes, legendre_weights, laguerre_nodes, laguerre_weights, closed):
    s = 0.5 * (legendre_nodes + 1.0)
    sw = 0.5 * legendre_weights
    s_squared = s[:, None] ** 2
    factor = s_squared * (1.0 - s_squared) * laguerre_nodes[None, :]
    weights = 3.0 * sw[:, None] * s_squared * (laguerre_weights * laguerre_nodes)[None, :]
    rows = []
    for amplitude in SHEAR_AMPLITUDES:
        denominator = np.sqrt(1.0 + amplitude * amplitude * factor)
        ratio = float(np.sum(weights / denominator, dtype=np.float64))
        if not math.isfinite(ratio) or ratio <= 0.0:
            raise ArithmeticError("invalid kinetic-energy ratio")
        rows.append({"a": amplitude, "ratio": ratio, "deficit": 1.0 - ratio})
    small_coefficient = rows[1]["deficit"] / (SHEAR_AMPLITUDES[1] ** 2)
    errors = {
        "zero_shear_ratio": abs(rows[0]["ratio"] - 1.0),
        "small_shear_coefficient": abs(small_coefficient - closed["small_shear_coefficient"]),
    }
    return {
        "E0": closed["kinetic_energy_zero"], "samples": rows,
        "small_shear_coefficient": small_coefficient, "absolute_errors": errors,
        "checks": {
            "zero_shear_ratio": errors["zero_shear_ratio"] <= TOLERANCE,
            "strict_sampled_decrease": all(rows[index]["ratio"] < rows[index - 1]["ratio"] for index in range(1, len(rows))),
            "positive_sample_deficits": all(row["deficit"] > 0.0 for row in rows[1:]),
            "small_shear_coefficient": errors["small_shear_coefficient"] <= SMALL_SHEAR_TOLERANCE,
        },
    }


def calculate():
    import numpy as np

    closed = analytic_values()
    rules = []
    for order, laguerre_order in zip(LEGENDRE_ORDERS, LAGUERRE_ORDERS):
        legendre_nodes, legendre_weights = checked_rule(
            np, *np.polynomial.legendre.leggauss(order), "Legendre " + str(order))
        laguerre_nodes, laguerre_weights = checked_rule(
            np, *np.polynomial.laguerre.laggauss(laguerre_order), "Laguerre " + str(laguerre_order))
        if not np.all((legendre_nodes > -1.0) & (legendre_nodes < 1.0)) or not np.all(laguerre_nodes > 0.0):
            raise ArithmeticError("quadrature nodes outside prescribed domains")
        rules.append({
            "legendre_order": order, "laguerre_order": laguerre_order,
            "field": field_integrals(np, legendre_nodes, legendre_weights, closed),
            "conditional": conditional_integrals(np, legendre_nodes, legendre_weights),
            "energy": energy_integrals(np, legendre_nodes, legendre_weights, laguerre_nodes, laguerre_weights, closed),
            "point_counts": {
                "field_spatial_points": order * order,
                "conditional_spatial_points": len(CONDITIONAL_X) * order,
                "energy_integrand_points": len(SHEAR_AMPLITUDES) * order * laguerre_order,
            },
        })
    low, high = rules
    field_differences = {
        key: abs(low["field"]["metrics"][key] - high["field"]["metrics"][key])
        for key in closed["metrics"]
    }
    # Norm/cross comparisons use the same positive high-rule norm for both values.
    norm0_high = high["field"]["gram"][0][0]
    for i in range(3):
        for j in range(3):
            field_differences["gram_" + str(i) + str(j) + "_over_high_norm_e0"] = abs(
                low["field"]["gram"][i][j] - high["field"]["gram"][i][j]) / norm0_high
    for name in ("e0", "e1", "n"):
        field_differences["cross_" + name + "_over_high_cross_e0"] = abs(
            low["field"]["cross"][name] - high["field"]["cross"][name]) / abs(high["field"]["cross"]["e0"])
    field_differences["F_norm_squared_relative"] = abs(
        low["field"]["F_norm_squared"] - high["field"]["F_norm_squared"]) / high["field"]["F_norm_squared"]
    conditional_differences = []
    for left, right in zip(low["conditional"], high["conditional"]):
        conditional_differences.append({
            "x": left["x"],
            "absolute_differences": {key: abs(left[key] - right[key]) for key in (
                "normalization", "initial_mean", "initial_variance", "normalization_derivative",
                "mean_derivative", "second_raw_moment_derivative", "kappa_dot_moment_expression",
                "kappa_dot_derivative_expression", "kappa_dot_centered_quotient")},
        })
    energy_differences = [
        {"a": left["a"], "ratio_absolute_difference": abs(left["ratio"] - right["ratio"])}
        for left, right in zip(low["energy"]["samples"], high["energy"]["samples"])
    ]
    checks = {}
    for rule in rules:
        prefix = "order_" + str(rule["legendre_order"]) + "_"
        for key, passed in rule["field"]["checks"].items():
            checks[prefix + "field_" + key] = passed
        for row in rule["conditional"]:
            for key, passed in row["checks"].items():
                checks[prefix + "conditional_x_" + str(row["x"]) + "_" + key] = passed
        for key, passed in rule["energy"]["checks"].items():
            checks[prefix + "energy_" + key] = passed
    checks["adjacent_field_rules"] = all(value <= TOLERANCE for value in field_differences.values())
    checks["adjacent_conditional_rules"] = all(
        value <= TOLERANCE for row in conditional_differences for value in row["absolute_differences"].values())
    checks["adjacent_energy_rules"] = all(row["ratio_absolute_difference"] <= TOLERANCE for row in energy_differences)
    passed = all(checks.values())
    return {
        "schema": "t74-shear-invariant-screen-v1",
        "verdict": "confirmed" if passed else "numerical_confirmation_failed",
        "passed": passed,
        "all_checks_pass": passed,
        "runtime": {"python": sys.version, "numpy": np.__version__},
        "contract": {
            "A": AMPLITUDE, "radial_domain": [0.0, 10.0], "axial_domain": [-10.0, 10.0],
            "H_measure": "2*pi*r^3 dr dz", "local_series_terms": 20,
            "local_series_radius_strict_upper_bound": 0.5,
            "absolute_normalized_tolerance": TOLERANCE,
            "small_shear_coefficient_absolute_tolerance": SMALL_SHEAR_TOLERANCE,
            "finite_domain_empirical_confirmation_only": True,
            "formal_tail_certificate": False, "trajectory_or_solver_comparison": False,
        },
        "analytic": closed, "rules": rules,
        "adjacent_rule_comparison": {
            "field_absolute_normalized_differences": field_differences,
            "maximum_field_absolute_normalized_difference": max(field_differences.values()),
            "conditional": conditional_differences,
            "energy": energy_differences,
            "maximum_energy_ratio_absolute_difference": max(row["ratio_absolute_difference"] for row in energy_differences),
        },
        "checks": checks,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("refusing existing output: " + str(args.output))
    started = time.perf_counter()
    try:
        result = calculate()
    except Exception as exc:
        result = {
            "schema": "t74-shear-invariant-screen-v1", "verdict": "execution_failed",
            "passed": False, "all_checks_pass": False,
            "error_type": type(exc).__name__, "error": str(exc),
        }
    result["elapsed_before_output_seconds"] = time.perf_counter() - started
    serialized = json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n"
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(serialized)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
