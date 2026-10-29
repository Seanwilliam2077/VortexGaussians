"""Timed RGB delivery paths for T19; no fixture identifiers or oracle inputs.

Only unit-interval Gauss-Legendre rules may persist in the caller's per-arm cache.
The harness imports this module and integrators before measuring delivery calls.
normal_cdf_calls counts CDF endpoints (two per nonempty interval, one per Phi),
using erf/erfc internally; it has the same definition in integrators.py.
"""

from __future__ import annotations

import math
import time

import numpy as np

import integrators


ARMS = ("simpson", "gl", "tail", "simple", "jensen")
PARAMETER_KEYS = frozenset(("n", "interval", "mu", "sd", "weight", "color", "background"))
SQRT_TWO = math.sqrt(2.0)


def _add(counters, key, amount=1):
    counters[key] = counters.get(key, 0) + amount


def _deadline(deadline_ns):
    if time.perf_counter_ns() >= deadline_ns:
        raise TimeoutError("T19 delivery deadline reached")


def _normal_interval(left, right, mu, sd, counters):
    _add(counters, "normal_interval_calls")
    if left == right:
        return 0.0
    if left > right:
        raise ValueError("Reversed Gaussian interval")
    zleft, zright = (left - mu) / sd, (right - mu) / sd
    _add(counters, "normal_cdf_calls", 2)
    if zleft >= 0.0:
        return 0.5 * (math.erfc(zleft / SQRT_TWO) - math.erfc(zright / SQRT_TWO))
    if zright <= 0.0:
        return 0.5 * (math.erfc(-zright / SQRT_TWO) - math.erfc(-zleft / SQRT_TWO))
    return 0.5 * (math.erf(zright / SQRT_TWO) - math.erf(zleft / SQRT_TWO))


def _normal_cdf(z, counters):
    _add(counters, "normal_cdf_calls")
    return 0.5 * math.erfc(-z / SQRT_TWO)


def _prepare(parameters, cache, counters):
    # Conversions and all ray-dependent mathematical preparation are timed.
    if frozenset(parameters) != PARAMETER_KEYS:
        raise ValueError("Delivery accepts only the seven declared ray-parameter fields")
    n = int(parameters["n"])
    left, right = (float(x) for x in parameters["interval"])
    mu = np.asarray(parameters["mu"], dtype=np.float64)
    sd = np.asarray(parameters["sd"], dtype=np.float64)
    weight = np.asarray(parameters["weight"], dtype=np.float64)
    color = np.asarray(parameters["color"], dtype=np.float64).reshape((n, 3))
    background = np.asarray(parameters["background"], dtype=np.float64)
    _add(counters, "common_prepare_calls")
    _add(counters, "common_input_components", n)
    _add(counters, "common_input_array_conversions", 5)
    if any(array.shape != (n,) for array in (mu, sd, weight)) or background.shape != (3,):
        raise ValueError("Invalid ray-parameter shapes")
    clipped = []
    for i in range(n):
        if weight[i] == 0.0:
            _add(counters, "common_zero_weight_mass_skips")
            clipped.append(0.0)
        else:
            clipped.append(float(weight[i]) * _normal_interval(left, right, float(mu[i]), float(sd[i]), counters))
            _add(counters, "common_clipped_mass_evaluations")
    tau = np.asarray(clipped, dtype=np.float64)
    total_tau = math.fsum(clipped)
    transmission = math.exp(-total_tau)
    _add(counters, "common_total_attenuation_evaluations")
    return {"n": n, "a": left, "b": right, "mu": mu, "sd": sd, "weight": weight,
            "color": color, "background": background, "tau": tau,
            "total_tau": total_tau, "transmission": transmission,
            "background_term": transmission * background, "rule_cache": cache}


def _result(rgb, path, counters, **diagnostics):
    return {"rgb": [float(x) for x in rgb], "path": path, "counters": counters, **diagnostics}


def _common(prepared, epsilon, counters):
    n, color = prepared["n"], prepared["color"]
    if n == 0:
        _add(counters, "common_exact_accepts")
        return _result(prepared["background"], "common_vacuum", counters)
    if prepared["total_tau"] == 0.0:
        _add(counters, "common_exact_accepts")
        return _result(prepared["background"], "common_zero_mass", counters)
    q = -math.expm1(-prepared["total_tau"])
    prepared["total_alpha"] = q
    _add(counters, "common_color_equality_entries", 3 * n)
    if bool(np.all(color == color[0])):
        _add(counters, "common_exact_accepts")
        return _result(q * color[0] + prepared["background_term"], "common_equal_color", counters)
    _add(counters, "common_profile_mu_equality_entries", n)
    equal_mu = bool(np.all(prepared["mu"] == prepared["mu"][0]))
    if equal_mu:
        _add(counters, "common_profile_sd_equality_entries", n)
        if bool(np.all(prepared["sd"] == prepared["sd"][0])):
            mean_color = np.sum(prepared["tau"][:, None] * color, axis=0) / prepared["total_tau"]
            _add(counters, "common_exact_accepts")
            return _result(q * mean_color + prepared["background_term"], "common_proportional", counters)
    cmin, cmax = np.min(color, axis=0), np.max(color, axis=0)
    _add(counters, "common_extrema_component_entries", 6 * n)
    prepared["color_min"], prepared["color_max"] = cmin, cmax
    prepared["G"] = q * (cmax - cmin)
    half_bound = float(np.max(prepared["G"] / 2.0))
    _add(counters, "common_global_center_tests")
    if half_bound <= epsilon:
        _add(counters, "common_global_center_accepts")
        return _result(q * (cmin + cmax) / 2.0 + prepared["background_term"],
                       "common_global_center", counters, delivered_bound_max=half_bound)
    return None


def _stable_order(prepared, counters):
    _add(counters, "sort_calls")
    _add(counters, "sort_components", prepared["n"])
    return sorted(range(prepared["n"]), key=prepared["mu"].__getitem__)


def _composite(prepared, order, masses, alpha, counters, total_transmission):
    rgb = np.zeros(3, dtype=np.float64)
    prefix = 1.0
    for i in order:
        if alpha[i] == 0.0:
            _add(counters, "composite_zero_mass_skips")
            continue
        rgb += prefix * alpha[i] * prepared["color"][i]
        prefix *= math.exp(-float(masses[i]))
        _add(counters, "composite_nonzero_components")
    return rgb + total_transmission * prepared["background"]


def _integrate(prepared, epsilon, counters, deadline_ns, arm, shortcut_diagnostics=None):
    _deadline(deadline_ns)
    if arm == "gl":
        solved = integrators.integrate_gl(prepared, epsilon / 4.0, counters, deadline_ns)
    else:
        if arm != "simpson":
            _add(counters, "shortcut_simpson_fallback_calls")
        solved = integrators.integrate_simpson(prepared, epsilon / 4.0, counters, deadline_ns)
    # A solver failure raises; it is never replaced by an oracle or a new method.
    result = dict(solved)
    result["solver_path"] = solved["path"]
    result["path"] = arm if arm in ("simpson", "gl") else f"{arm}_fallback_simpson"
    result["rgb"] = [float(x) for x in solved["rgb"]]
    result["counters"] = counters
    if shortcut_diagnostics is not None:
        result.update(shortcut_diagnostics)
    return result


def _tail(prepared, epsilon, counters, deadline_ns):
    order = _stable_order(prepared, counters)
    n = prepared["n"]
    means, widths, weight = prepared["mu"], prepared["sd"], prepared["weight"]
    midpoints = [(float(means[order[k]]) + float(means[order[k + 1]])) / 2.0 for k in range(n - 1)]
    retained = np.zeros(n, dtype=np.float64)
    color_range = (np.maximum(prepared["color_max"], prepared["background"])
                   - np.minimum(prepared["color_min"], prepared["background"]))
    color_range_max = float(np.max(color_range))
    removed_terms = []
    removed_partial = 0.0
    for rank, i in enumerate(order):
        _deadline(deadline_ns)
        left = prepared["a"] if rank == 0 else max(prepared["a"], midpoints[rank - 1])
        right = prepared["b"] if rank == n - 1 else min(prepared["b"], midpoints[rank])
        _add(counters, "tail_bins_visited")
        if left >= right or weight[i] == 0.0:
            _add(counters, "tail_empty_or_zero_weight_bins")
        else:
            mass = float(weight[i]) * _normal_interval(left, right, float(means[i]), float(widths[i]), counters)
            # Clamp only binary64 roundoff to the mathematically valid mass interval.
            retained[i] = min(float(prepared["tau"][i]), max(0.0, mass))
            if retained[i] != mass:
                _add(counters, "tail_retained_mass_roundoff_clamps")
            _add(counters, "tail_retained_mass_evaluations")
        # Removed terms are nonnegative. A partial deletion-bound value can
        # reject the shortcut, but never certifies acceptance before all bins.
        term = float(prepared["tau"][i] - retained[i])
        removed_terms.append(term)
        # O(1) prefix work; downward rounding avoids upward accumulation drift
        # in this rejection-only path. Final acceptance uses one full fsum below.
        removed_partial = math.nextafter(removed_partial + term, 0.0)
        bound_max = -math.expm1(-removed_partial) * color_range_max
        _add(counters, "tail_bound_tests")
        if bound_max > epsilon:
            _add(counters, "tail_early_rejections")
            _add(counters, "tail_shortcut_rejects")
            return _integrate(prepared, epsilon, counters, deadline_ns, "tail", {
                "tail_scan_complete": rank == n - 1,
                "tail_partial_removed_optical_mass": removed_partial,
                "tail_partial_deletion_bound_max": bound_max})
    removed = math.fsum(removed_terms)
    bound_max = -math.expm1(-removed) * color_range_max
    _add(counters, "tail_complete_mass_sums")
    _add(counters, "tail_bound_tests")
    diagnostics = {"tail_removed_optical_mass": removed, "tail_bound_max": bound_max,
                   "tail_scan_complete": True}
    if bound_max <= epsilon:
        _add(counters, "tail_shortcut_accepts")
        alpha = np.asarray([-math.expm1(-float(t)) for t in retained], dtype=np.float64)
        transmission = math.exp(-math.fsum(float(t) for t in retained))
        _add(counters, "tail_retained_alpha_evaluations", n)
        rgb = _composite(prepared, order, retained, alpha, counters, transmission)
        return _result(rgb, "tail_accept", counters, delivered_bound_max=bound_max, **diagnostics)
    _add(counters, "tail_shortcut_rejects")
    return _integrate(prepared, epsilon, counters, deadline_ns, "tail", diagnostics)


def _pair(prepared, epsilon, counters, deadline_ns, arm):
    order = _stable_order(prepared, counters)
    mu, sd, weight = prepared["mu"], prepared["sd"], prepared["weight"]
    tau, color, global_bound = (prepared[k] for k in ("tau", "color", "G"))
    # Individual original alphas are candidate-specific preparation. Ordinary
    # integration, common shortcuts and retained-tail delivery do not need them.
    alpha = np.asarray([-math.expm1(-float(t)) for t in tau], dtype=np.float64)
    _add(counters, "pair_alpha_evaluations", prepared["n"])
    partial = np.zeros(3, dtype=np.float64)
    _add(counters, "pair_total_possible", prepared["n"] * (prepared["n"] - 1) // 2)
    for rank, i in enumerate(order):
        for j in order[rank + 1:]:
            _deadline(deadline_ns)
            _add(counters, "pair_visited")
            if alpha[i] == 0.0 or alpha[j] == 0.0:
                _add(counters, "pair_zero_mass_skips")
                continue
            contrast = np.abs(color[i] - color[j])
            _add(counters, "pair_color_contrast_evaluations")
            if not bool(np.any(contrast)):
                _add(counters, "pair_zero_contrast_skips")
                continue
            z = (float(mu[i]) - float(mu[j])) / math.sqrt(float(sd[i]) ** 2 + float(sd[j]) ** 2)
            inversion = float(weight[i]) * float(weight[j]) * _normal_cdf(z, counters)
            _add(counters, "pair_cdf_evaluations")
            ibar = min(inversion, float(tau[i]) * float(tau[j]))
            alpha_product = float(alpha[i]) * float(alpha[j])
            if arm == "simple":
                pair_bound = min(ibar, alpha_product)
            else:
                h = min(float(alpha[i]), float(alpha[j]))
                pair_bound = min(alpha_product, -h * math.expm1(-ibar / h))
                _add(counters, "pair_jensen_saturation_evaluations")
            partial += contrast * pair_bound
            _add(counters, "pair_nonzero_contrast_terms")
            capped_partial = np.minimum(global_bound, partial)
            if bool(np.any(capped_partial > epsilon)):
                _add(counters, "pair_early_rejections")
                _add(counters, "pair_shortcut_rejects")
                # This is a partial certificate value, NOT a lower bound on true error.
                diagnostics = {"pair_scan_complete": False,
                               "pair_capped_partial_value_max": float(np.max(capped_partial))}
                return _integrate(prepared, epsilon, counters, deadline_ns, arm, diagnostics)
    _add(counters, "pair_complete_scans")
    bound_max = float(np.max(np.minimum(global_bound, partial)))
    if bound_max <= epsilon:
        _add(counters, "pair_shortcut_accepts")
        rgb = _composite(prepared, order, tau, alpha, counters, prepared["transmission"])
        return _result(rgb, f"{arm}_accept", counters, delivered_bound_max=bound_max,
                       pair_scan_complete=True, pair_bound_max=bound_max,
                       pair_shortcut_accepted=True)
    _add(counters, "pair_shortcut_rejects")
    return _integrate(prepared, epsilon, counters, deadline_ns, arm,
                      {"pair_scan_complete": True, "pair_bound_max": bound_max})


def deliver(arm, parameters, epsilon, cache, deadline_ns):
    """Return delivered RGB/path/counters, with all ray-dependent work inside."""
    counters = {}
    try:
        _deadline(deadline_ns)
        if arm not in ARMS:
            raise ValueError("Unknown T19 arm")
        if not math.isfinite(epsilon) or epsilon <= 0.0:
            raise ValueError("epsilon must be finite and positive")
        prepared = _prepare(parameters, cache, counters)
        common = _common(prepared, epsilon, counters)
        if common is not None:
            return common
        if arm in ("simpson", "gl"):
            return _integrate(prepared, epsilon, counters, deadline_ns, arm)
        if arm == "tail":
            return _tail(prepared, epsilon, counters, deadline_ns)
        return _pair(prepared, epsilon, counters, deadline_ns, arm)
    except Exception as exc:
        # The supervisor can preserve work performed before a failing delivery.
        exc.delivery_counters = dict(counters)
        exc.delivery_arm = arm
        raise
