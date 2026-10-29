"""Lean ordinary integration for T19's fixed continuous-RGB delivery screen.

These routines do not read truth, fixture identifiers, files, or reference data.
The caller supplies prepared ray parameters and an absolute nominal budget
(epsilon / 4). Simpson and consecutive-GL differences are empirical estimates,
not numerical certificates. Only initial unresolvable Simpson intervals receive
the real-arithmetic omission envelope with outward-rounded rational accounting.
"""

from __future__ import annotations

from fractions import Fraction
import math
import time


SQRT_TWO = math.sqrt(2.0)
SQRT_TWO_PI = math.sqrt(2.0 * math.pi)
MAX_DEPTH = 24
MAX_SIMPSON_EVALS = 200_000
GL_ORDERS = (4, 8, 16, 32, 64)


class SolverFailure(RuntimeError):
    """Recordable numerical/implementation failure, never an oracle fallback."""


def _add(counters, key, amount=1):
    counters[key] = counters.get(key, 0) + amount


def _check_deadline(deadline_ns):
    if time.perf_counter_ns() >= deadline_ns:
        raise TimeoutError("T19 supervised wall budget exhausted")


def _normal_interval(lo, hi, mu, sd, counters):
    """Same stable complementary-tail evaluation as T17/T18, in binary64."""
    _add(counters, "normal_interval_calls")
    if hi == lo:
        return 0.0
    if hi < lo:
        raise SolverFailure("Reversed cumulative-density interval")
    zlo, zhi = (lo - mu) / sd, (hi - mu) / sd
    _add(counters, "normal_cdf_calls", 2)
    if zlo >= 0.0:
        return 0.5 * (math.erfc(zlo / SQRT_TWO) - math.erfc(zhi / SQRT_TWO))
    if zhi <= 0.0:
        return 0.5 * (math.erfc(-zhi / SQRT_TWO) - math.erfc(-zlo / SQRT_TWO))
    return 0.5 * (math.erf(zhi / SQRT_TWO) - math.erf(zlo / SQRT_TWO))


class _Integrand:
    def __init__(self, prepared, counters, deadline_ns, kind, evaluation_limit=None):
        self.left = float(prepared["a"])
        self.counters = counters
        self.deadline_ns = deadline_ns
        self.kind = kind
        self.limit = evaluation_limit
        self.evaluations = 0
        # Scalar coefficients are local to this actual delivery, never cached
        # across methods, rays, or passes. Their construction is inside timing.
        self.rows = []
        for mu, sd, weight, color in zip(prepared["mu"], prepared["sd"],
                                          prepared["weight"], prepared["color"]):
            mu, sd, weight = float(mu), float(sd), float(weight)
            if weight == 0.0:
                continue
            self.rows.append((mu, sd, weight, weight / (SQRT_TWO_PI * sd),
                              tuple(float(c) for c in color)))
        _add(counters, "integration_scalar_components", len(self.rows))

    def __call__(self, t):
        _check_deadline(self.deadline_ns)
        if self.limit is not None and self.evaluations >= self.limit:
            raise SolverFailure("Adaptive Simpson integrand-evaluation limit reached")
        self.evaluations += 1
        _add(self.counters, "integration_evaluations")
        _add(self.counters, self.kind + "_evaluations")
        cumulative, sources = [], []
        for mu, sd, weight, pdf_scale, color in self.rows:
            cumulative.append(weight * _normal_interval(self.left, t, mu, sd, self.counters))
            z = (t - mu) / sd
            density = pdf_scale * math.exp(-0.5 * z * z)
            sources.append((density * color[0], density * color[1], density * color[2]))
        _add(self.counters, "normal_pdf_component_evals", len(self.rows))
        transmission = math.exp(-math.fsum(cumulative))
        value = tuple(transmission * math.fsum(row[k] for row in sources) for k in range(3))
        if not all(math.isfinite(v) for v in value):
            raise SolverFailure("Nonfinite continuous emission integrand")
        return value


def _breakpoints(prepared, counters):
    left, right = float(prepared["a"]), float(prepared["b"])
    if not left < right:
        raise SolverFailure("Integration requires a positive ray interval")
    values = {left, right}
    for mu, sd in zip(prepared["mu"], prepared["sd"]):
        mu, sd = float(mu), float(sd)
        for k in (-6, -3, 0, 3, 6):
            value = mu + k * sd
            if left < value < right:
                values.add(value)
    points = sorted(values)
    _add(counters, "integration_breakpoint_builds")
    _add(counters, "integration_original_segments", len(points) - 1)
    return points


def _round_up(value):
    if value < 0:
        raise SolverFailure("Expected nonnegative rational")
    rounded = float(value)
    if not math.isfinite(rounded):
        raise SolverFailure("Rational-to-binary64 overflow")
    if Fraction.from_float(rounded) < value:
        rounded = math.nextafter(rounded, math.inf)
    if not math.isfinite(rounded) or Fraction.from_float(rounded) < value:
        raise SolverFailure("Upward rational conversion failed")
    return rounded


def _round_down(value):
    if value < 0:
        raise SolverFailure("Expected nonnegative rational")
    rounded = float(value)
    if not math.isfinite(rounded):
        raise SolverFailure("Rational-to-binary64 overflow")
    if Fraction.from_float(rounded) > value:
        rounded = math.nextafter(rounded, -math.inf)
    if rounded < 0 or Fraction.from_float(rounded) > value:
        raise SolverFailure("Downward rational conversion failed")
    return rounded


def _simpson_value(left, right, fleft, fmid, fright):
    return tuple((right - left) * (fleft[k] + 4.0 * fmid[k] + fright[k]) / 6.0
                 for k in range(3))


def _result(prepared, emission, path, **diagnostics):
    rgb = [emission[k] + float(prepared["background_term"][k]) for k in range(3)]
    if not all(math.isfinite(v) for v in rgb):
        raise SolverFailure("Nonfinite delivered RGB")
    return {"rgb": rgb, "emission_rgb": list(emission), "path": path, **diagnostics}


def integrate_simpson(prepared, budget, counters, deadline_ns):
    """Adaptive Simpson with T18 initial-gap charging and no recursive omission."""
    _check_deadline(deadline_ns)
    budget = float(budget)
    if not math.isfinite(budget) or budget <= 0.0:
        raise SolverFailure("Simpson requires a positive finite absolute budget")
    _add(counters, "simpson_calls")
    points = _breakpoints(prepared, counters)
    active, omitted_widths = [], []
    for left, right in zip(points[:-1], points[1:]):
        width = Fraction.from_float(right) - Fraction.from_float(left)
        if width <= 0:
            raise SolverFailure("Nonpositive original segment width")
        mid = (left + right) / 2.0
        qleft, qright = (left + mid) / 2.0, (mid + right) / 2.0
        unresolved = (mid == left or mid == right or qleft == left or qleft == mid
                      or qright == mid or qright == right)
        if unresolved:
            omitted_widths.append(width)
        else:
            active.append((left, right, mid, width))
    _add(counters, "simpson_omitted_initial_segments", len(omitted_widths))
    _add(counters, "simpson_active_initial_segments", len(active))

    # Construct the exact envelope rate only when an omission actually needs it.
    # No density or attenuation is deleted from the integrand/background model.
    charge_sum = Fraction(0)
    if omitted_widths:
        envelope_rate = sum((Fraction.from_float(float(w)) / Fraction.from_float(float(sd))
                             for w, sd in zip(prepared["weight"], prepared["sd"])), Fraction(0))
        for width in omitted_widths:
            charge_sum += Fraction.from_float(_round_up(width * envelope_rate))
    charged_total = _round_up(charge_sum)
    charged_fraction = Fraction.from_float(charged_total)
    original_budget = Fraction.from_float(budget)
    remaining_exact = original_budget - charged_fraction
    if remaining_exact <= 0:
        raise SolverFailure("No positive Simpson budget remains after initial omissions")
    remaining = _round_down(remaining_exact)
    if remaining <= 0.0:
        raise SolverFailure("Remaining Simpson budget underflowed")
    remaining_fraction = Fraction.from_float(remaining)
    active_length = sum((entry[3] for entry in active), Fraction(0))
    allocations = []
    allocation_sum = Fraction(0)
    for left, right, mid, width in active:
        allocation = _round_down(remaining_fraction * width / active_length)
        if allocation <= 0.0:
            raise SolverFailure("Required Simpson segment allocation underflowed")
        allocation_sum += Fraction.from_float(allocation)
        allocations.append((left, right, mid, allocation))
    if charged_fraction + allocation_sum > original_budget:
        raise SolverFailure("Simpson charged-plus-allocated budget exceeded")
    counters["simpson_omitted_charge"] = counters.get("simpson_omitted_charge", 0.0) + charged_total

    fun = _Integrand(prepared, counters, deadline_ns, "simpson", MAX_SIMPSON_EVALS)
    leaf_errors = []
    max_depth_used = 0

    def refine(left, right, fleft, fmid, fright, parent, tolerance, depth):
        nonlocal max_depth_used
        max_depth_used = max(max_depth_used, depth)
        counters["simpson_max_depth"] = max(counters.get("simpson_max_depth", 0), depth)
        mid = (left + right) / 2.0
        qleft, qright = (left + mid) / 2.0, (mid + right) / 2.0
        if qleft == left or qleft == mid or qright == mid or qright == right:
            raise SolverFailure("Adaptive Simpson endpoint resolution exhausted during recursion")
        fqleft, fqright = fun(qleft), fun(qright)
        lower = _simpson_value(left, mid, fleft, fqleft, fmid)
        upper = _simpson_value(mid, right, fmid, fqright, fright)
        combined = tuple(lower[k] + upper[k] for k in range(3))
        difference = tuple(combined[k] - parent[k] for k in range(3))
        error = tuple(abs(v) / 15.0 for v in difference)
        if max(error) <= tolerance:
            _add(counters, "simpson_accepted_leaves")
            leaf_errors.append(error)
            return tuple(combined[k] + difference[k] / 15.0 for k in range(3))
        if depth >= MAX_DEPTH:
            raise SolverFailure("Adaptive Simpson maximum depth reached before tolerance")
        value_l = refine(left, mid, fleft, fqleft, fmid, lower, tolerance / 2.0, depth + 1)
        value_r = refine(mid, right, fmid, fqright, fright, upper, tolerance / 2.0, depth + 1)
        return tuple(value_l[k] + value_r[k] for k in range(3))

    segments = []
    for left, right, mid, allocation in allocations:
        fleft, fmid, fright = fun(left), fun(mid), fun(right)
        parent = _simpson_value(left, right, fleft, fmid, fright)
        segments.append(refine(left, right, fleft, fmid, fright, parent, allocation, 0))
    emission = tuple(math.fsum(value[k] for value in segments) for k in range(3))
    # Lean empirical-error reduction replaces T18's verbose Fraction leaf ledger.
    # Initial omission charges and budget allocations above remain exact-accounted.
    estimated = [math.fsum([charged_total] + [error[k] for error in leaf_errors])
                 for k in range(3)]
    if any(value > budget for value in estimated):
        raise SolverFailure("Simpson empirical estimate plus omission charge exceeded budget")
    return _result(prepared, emission, "simpson", estimated_abs_error_rgb=estimated,
                   omitted_emission_charge=charged_total, max_depth_used=max_depth_used)


def _legendre_value_and_derivative(degree, x):
    previous, current = 1.0, x
    for k in range(2, degree + 1):
        previous, current = current, ((2 * k - 1) * x * current - (k - 1) * previous) / k
    return current, degree * (x * current - previous) / (x * x - 1.0)


def _gauss_legendre_rule(degree, counters, deadline_ns):
    """Bounded scalar Newton construction, checked only to the rule's exact degree."""
    if degree not in GL_ORDERS:
        raise SolverFailure("GL degree outside the fixed T19 ladder")
    _add(counters, "gl_rule_builds")
    nodes, weights, residuals = [0.0] * degree, [0.0] * degree, []
    for k in range(degree // 2):
        _check_deadline(deadline_ns)
        z = math.cos(math.pi * (k + 0.75) / (degree + 0.5))
        for iteration in range(1, 33):
            _add(counters, "gl_rule_newton_iterations")
            value, derivative = _legendre_value_and_derivative(degree, z)
            if not math.isfinite(derivative) or derivative == 0.0:
                raise SolverFailure("Invalid GL Newton derivative")
            delta = value / derivative
            updated = z - delta
            if not math.isfinite(updated) or not 0.0 < updated < 1.0:
                raise SolverFailure("Invalid GL Newton root")
            if updated == z or abs(delta) <= 2e-16:
                z = updated
                break
            z = updated
        else:
            raise SolverFailure("GL Newton iteration limit reached")
        value, derivative = _legendre_value_and_derivative(degree, z)
        weight = 2.0 / ((1.0 - z * z) * derivative * derivative)
        nodes[k], nodes[degree - 1 - k] = -z, z
        weights[k] = weights[degree - 1 - k] = weight
        residuals.append(abs(value))
    tolerance = 5e-13
    if (not all(math.isfinite(x) for x in nodes + weights)
            or not all(-1.0 < x < 1.0 for x in nodes)
            or not all(a < b for a, b in zip(nodes[:-1], nodes[1:]))
            or not all(w > 0.0 for w in weights)
            or max(residuals) > tolerance):
        raise SolverFailure("GL node/weight/residual implementation check failed")
    for power in range(min(12, 2 * degree - 1) + 1):
        expected = 0.0 if power % 2 else 2.0 / (power + 1)
        actual = math.fsum(w * x ** power for x, w in zip(nodes, weights))
        _add(counters, "gl_rule_moment_checks")
        if abs(actual - expected) > tolerance:
            raise SolverFailure("GL polynomial-moment implementation check failed")
    return tuple(nodes), tuple(weights)


def _gl_emission(fun, points, nodes, weights):
    segments = []
    for left, right in zip(points[:-1], points[1:]):
        midpoint, half = (left + right) / 2.0, (right - left) / 2.0
        weighted_values = []
        for node, weight in zip(nodes, weights):
            value = fun(midpoint + half * node)
            weighted_values.append(tuple(weight * v for v in value))
        segments.append(tuple(half * math.fsum(value[k] for value in weighted_values)
                              for k in range(3)))
    return tuple(math.fsum(value[k] for value in segments) for k in range(3))


def integrate_gl(prepared, budget, counters, deadline_ns):
    """Gaussian-aware GL4/8/16/32/64 agreement, then full-cost Simpson fallback."""
    _check_deadline(deadline_ns)
    budget = float(budget)
    if not math.isfinite(budget) or budget <= 0.0:
        raise SolverFailure("GL requires a positive finite agreement budget")
    _add(counters, "gl_calls")
    points = _breakpoints(prepared, counters)
    fun = _Integrand(prepared, counters, deadline_ns, "gl")
    cache = prepared["rule_cache"]
    previous = None
    difference = None
    for degree in GL_ORDERS:
        _check_deadline(deadline_ns)
        if degree not in cache:
            cache[degree] = _gauss_legendre_rule(degree, counters, deadline_ns)
        else:
            _add(counters, "gl_rule_cache_hits")
        nodes, weights = cache[degree]
        emission = _gl_emission(fun, points, nodes, weights)
        _add(counters, "gl_refinement_levels")
        counters["gl_last_order"] = degree
        if previous is not None:
            difference = [abs(emission[k] - previous[k]) for k in range(3)]
            if max(difference) <= budget:
                return _result(prepared, emission, "gl", gl_order=degree,
                               estimated_abs_error_rgb=difference)
        previous = emission
    _add(counters, "gl_simpson_fallbacks")
    result = integrate_simpson(prepared, budget, counters, deadline_ns)
    result.update({"path": "gl_simpson_fallback", "gl_order": GL_ORDERS[-1],
                   "gl_last_difference_rgb": difference})
    return result
