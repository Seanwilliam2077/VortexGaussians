"""Independent ordinary interval reference for the frozen T31 authored field.

The enclosure argument is in real arithmetic. These scalar binary64 operations
do not provide directed rounding or a formal floating-point certificate. No
ordinary adapter, T22 integrator, BVH, or numerical quadrature is imported.
"""

import heapq
import math
import time


class ReferenceFailure(RuntimeError):
    """A named input, resource, numerical-range, or resolution failure."""

    def __init__(self, code, detail=""):
        self.code = code
        super().__init__(code + (": " + detail if detail else ""))


def _add(counters, key, amount=1):
    counters[key] = counters.get(key, 0) + amount


def _deadline(deadline_ns, counters):
    _add(counters, "reference_deadline_checks")
    if deadline_ns is not None and time.perf_counter_ns() >= deadline_ns:
        raise ReferenceFailure("reference_deadline")


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _exp(value, counters):
    _add(counters, "reference_exp_calls")
    try:
        result = math.exp(value)
    except (OverflowError, ValueError) as exc:
        raise ReferenceFailure("reference_exp_range", str(exc)) from exc
    if not math.isfinite(result):
        raise ReferenceFailure("reference_exp_nonfinite")
    return result


def _expm1(value, counters):
    _add(counters, "reference_exp_calls")
    _add(counters, "reference_expm1_calls")
    try:
        result = math.expm1(value)
    except (OverflowError, ValueError) as exc:
        raise ReferenceFailure("reference_expm1_range", str(exc)) from exc
    if not math.isfinite(result):
        raise ReferenceFailure("reference_expm1_nonfinite")
    return result


def _log(value, counters):
    _add(counters, "reference_log_calls")
    if not _finite(value) or value <= 0:
        raise ReferenceFailure("reference_log_domain")
    return math.log(value)


def independent_ray(params, yaw, width, height, i, j):
    """Construct one unit ray from explicit trigonometric camera basis vectors."""
    if not all(isinstance(x, int) and not isinstance(x, bool) for x in (width, height, i, j)):
        raise ReferenceFailure("reference_pixel_type")
    if width <= 0 or height <= 0 or not (0 <= i < width and 0 <= j < height):
        raise ReferenceFailure("reference_pixel_domain")
    distance, elevation, fov = (params[k] for k in ("camDist", "camElev", "fov"))
    if not all(_finite(x) for x in (distance, elevation, fov, yaw)):
        raise ReferenceFailure("reference_camera_nonfinite")
    if distance <= 0 or abs(elevation) >= math.pi / 2 or not 0 < fov < math.pi:
        raise ReferenceFailure("reference_camera_domain")
    azimuth = yaw * math.pi
    sa, ca = math.sin(azimuth), math.cos(azimuth)
    se, ce = math.sin(elevation), math.cos(elevation)
    back = (ce * sa, se, ce * ca)
    right = (ca, 0.0, -sa)
    up = (-se * sa, ce, -se * ca)
    forward = tuple(-x for x in back)
    origin = [distance * back[0], 1.05 + distance * back[1], distance * back[2]]
    tangent = math.tan(fov / 2)
    horizontal = (2 * (i + 0.5) / width - 1) * (width / height) * tangent
    vertical = (1 - 2 * (j + 0.5) / height) * tangent
    direction = [forward[k] + right[k] * horizontal + up[k] * vertical for k in range(3)]
    length = math.sqrt(math.fsum(x * x for x in direction))
    if not _finite(length) or length <= 0:
        raise ReferenceFailure("reference_direction_range")
    direction = [x / length for x in direction]
    cosine = math.fsum(direction[k] * forward[k] for k in range(3))
    if not _finite(cosine) or cosine <= 0:
        raise ReferenceFailure("reference_clip_domain")
    a, b = 0.05 / cosine, 50.0 / cosine
    if not all(_finite(x) for x in origin + direction + [a, b]):
        raise ReferenceFailure("reference_ray_nonfinite")
    return {"origin": origin, "direction": direction, "a": a, "b": b}


def project_all(primitives, ray, counters):
    """Project every source; residual-vector distance is independent of cross-product projection."""
    origin, direction = ray["origin"], ray["direction"]
    a, b = ray["a"], ray["b"]
    if len(origin) != 3 or len(direction) != 3 or not all(_finite(x) for x in list(origin) + list(direction) + [a, b]):
        raise ReferenceFailure("reference_ray_shape")
    if not a < b or abs(math.fsum(x * x for x in direction) - 1) > 1e-12:
        raise ReferenceFailure("reference_ray_not_unit_or_ordered")
    prepared = {"a": a, "b": b, "mu": [], "sd": [], "weight": [], "color": [], "source_ids": []}
    seen = set()
    for primitive in primitives:
        _add(counters, "reference_projected_components")
        source_id = primitive["source_index"]
        center, h, k, color = primitive["mu"], primitive["h"], primitive["k"], primitive["color"]
        if not isinstance(source_id, int) or isinstance(source_id, bool) or source_id in seen:
            raise ReferenceFailure("reference_source_identity")
        seen.add(source_id)
        if len(center) != 3 or len(color) != 3 or not all(_finite(x) for x in list(center) + list(color) + [h, k]):
            raise ReferenceFailure("reference_primitive_nonfinite")
        if h <= 0 or k < 0 or any(x < 0 for x in color):
            raise ReferenceFailure("reference_primitive_domain")
        delta = [center[d] - origin[d] for d in range(3)]
        z = math.fsum(delta[d] * direction[d] for d in range(3))
        residual = [delta[d] - z * direction[d] for d in range(3)]
        perpendicular2 = math.fsum(x * x for x in residual)
        exponent = -0.5 * (perpendicular2 / h) / h
        if not _finite(z) or not _finite(perpendicular2) or not _finite(exponent):
            raise ReferenceFailure("reference_projection_range")
        # Combine in log space: exp(exponent) alone must not underflow before
        # multiplication by k. A zero positive-source result is charged below.
        q = 0.0 if k == 0 else _exp(_log(k, counters) + exponent, counters)
        prepared["mu"].append(z)
        prepared["sd"].append(h)
        prepared["weight"].append(q)
        prepared["color"].append(list(color))
        prepared["source_ids"].append(source_id)
        if k > 0 and q == 0:
            _add(counters, "reference_projection_underflows")
    return prepared


def _validate(prepared):
    a, b = prepared["a"], prepared["b"]
    if not _finite(a) or not _finite(b) or not a < b:
        raise ReferenceFailure("reference_interval_domain")
    n = len(prepared["mu"])
    if any(len(prepared[k]) != n for k in ("sd", "weight", "color", "source_ids")):
        raise ReferenceFailure("reference_prepared_shape")
    if len(set(prepared["source_ids"])) != n:
        raise ReferenceFailure("reference_prepared_duplicate_ids")
    for z, h, q, rgb in zip(prepared["mu"], prepared["sd"], prepared["weight"], prepared["color"]):
        if len(rgb) != 3 or not all(_finite(x) for x in [z, h, q] + list(rgb)):
            raise ReferenceFailure("reference_prepared_nonfinite")
        if h <= 0 or q < 0 or any(x < 0 for x in rgb):
            raise ReferenceFailure("reference_prepared_domain")
    return n


def _normal_interval(left, right, counters):
    if left > right or math.isnan(left) or math.isnan(right):
        raise ReferenceFailure("reference_normal_interval_domain")
    if left == right:
        return 0.0
    _add(counters, "reference_cdf_intervals")
    _add(counters, "reference_cdf_calls", 2)
    scale = math.sqrt(2.0)
    if left >= 0:
        _add(counters, "reference_erfc_calls", 2)
        value = 0.5 * (math.erfc(left / scale) - math.erfc(right / scale))
    elif right <= 0:
        _add(counters, "reference_erfc_calls", 2)
        value = 0.5 * (math.erfc(-right / scale) - math.erfc(-left / scale))
    else:
        _add(counters, "reference_erf_calls", 2)
        value = 0.5 * (math.erf(right / scale) - math.erf(left / scale))
    if not _finite(value) or not 0 <= value <= 1:
        raise ReferenceFailure("reference_normal_interval_range")
    return value


def _masses(prepared, left, right, counters, deadline_ns=None):
    values = []
    for index, (z, h, q) in enumerate(zip(prepared["mu"], prepared["sd"], prepared["weight"])):
        if index % 32 == 0:
            _deadline(deadline_ns, counters)
        _add(counters, "reference_mass_components")
        mass = q * _normal_interval((left - z) / h, (right - z) / h, counters)
        if not _finite(mass) or mass < 0:
            raise ReferenceFailure("reference_mass_range")
        values.append(mass)
    return values


def analytic_alpha(prepared, counters):
    """Return {'alpha', 'masses'} in source order, using stable CDF intervals."""
    _validate(prepared)
    values = _masses(prepared, prepared["a"], prepared["b"], counters, prepared.get("_deadline_ns"))
    total = math.fsum(values)
    return {"alpha": -_expm1(-total, counters), "masses": values}


def enclose(prepared, cmax, halfwidth_budget, counters, deadline_ns):
    """Enclose full-field RGB with analytic-mass cells and charged tiny omissions.

    Counters persist across rays: reference_created_cells enforces the global
    200000-cell cap. Exp counts include expm1; CDF counts are endpoint counts.
    radius retains all three channel half-widths; max_radius is their maximum.
    Every leaf stores [l,r,W,loR,loG,loB,hiR,hiG,hiB].
    """
    _deadline(deadline_ns, counters)
    n = _validate(prepared)
    if len(cmax) != 3 or not all(_finite(x) and x >= 0 for x in cmax):
        raise ReferenceFailure("reference_cmax_domain")
    if not _finite(halfwidth_budget) or halfwidth_budget <= 0:
        raise ReferenceFailure("reference_budget_domain")
    if any(rgb[channel] > cmax[channel] for rgb in prepared["color"] for channel in range(3)):
        raise ReferenceFailure("reference_cmax_not_upper_bound")
    full = dict(prepared, _deadline_ns=deadline_ns)
    alpha_info = analytic_alpha(full, counters)
    threshold = 1e-10 / (max(1.0, max(cmax)) * n) if n else 0.0
    retained = [i for i, q in enumerate(prepared["weight"]) if q > threshold]
    omitted = [i for i, q in enumerate(prepared["weight"]) if q <= threshold]
    omitted_mass_bound = math.fsum(max(prepared["weight"][i], 1e-300) for i in omitted)
    omission_probability = -_expm1(-omitted_mass_bound, counters)
    omission_rgb = [maximum * omission_probability for maximum in cmax]
    _add(counters, "reference_omitted_components", len(omitted))
    _add(counters, "reference_retained_components", len(retained))
    p = {key: [prepared[key][i] for i in retained] for key in ("mu", "sd", "weight", "color", "source_ids")}
    p.update(a=prepared["a"], b=prepared["b"])
    a, b = p["a"], p["b"]
    retained_mass = math.fsum(alpha_info["masses"][i] for i in retained)
    retained_alpha = -_expm1(-retained_mass, counters)
    local_created = 0
    local_max_depth = 0
    leaves = {}
    heap = []
    analytic_rgb = [0.0, 0.0, 0.0]

    def diagnostic_failure(code, detail="", bounds=None):
        # Only package already computed state. Bounds, when supplied, are the
        # freshly reduced current partition; no integration/projection is run
        # to improve or replace a failing result.
        error = ReferenceFailure(code, detail)
        error.diagnostics = {
            "partial_unqualified": True, "bounds_available": bounds is not None,
            "created_cells": local_created, "max_depth": local_max_depth,
            "retained_ids": p["source_ids"], "retained_mu": p["mu"],
            "retained_sd": p["sd"], "retained_weight": p["weight"],
            "omitted_mass_bound": omitted_mass_bound, "omission_rgb_radius": omission_rgb,
            "full_mu": prepared["mu"], "full_weight": prepared["weight"],
            "source_ids": prepared["source_ids"], "finite_masses": alpha_info["masses"],
            "alpha_full": alpha_info["alpha"], "retained_alpha": retained_alpha,
            "analytic_retained_rgb": analytic_rgb,
            "leaves": [entry[0] for entry in sorted(leaves.values(), key=lambda entry: entry[0][0])],
        }
        if bounds is not None:
            low, high, midpoint, radius = bounds
            error.diagnostics.update(lower=low, upper=high, midpoint=midpoint, radius=radius)
        return error

    def allocate(depth):
        nonlocal local_created, local_max_depth
        _deadline(deadline_ns, counters)
        if local_created >= 8192:
            raise diagnostic_failure("reference_per_ray_cell_cap", "8192 created cells")
        if counters.get("reference_created_cells", 0) >= 200000:
            raise diagnostic_failure("reference_global_cell_cap", "200000 created cells")
        local_created += 1
        local_max_depth = max(local_max_depth, depth)
        _add(counters, "reference_created_cells")
        _add(counters, "reference_cell_depth_sum", depth)
        counters["reference_max_depth"] = max(counters.get("reference_max_depth", 0), depth)
        return local_created

    def global_bounds():
        _deadline(deadline_ns, counters)
        _add(counters, "reference_global_reductions")
        low = [max(0.0, math.fsum([analytic_rgb[k]] + [cell[3 + k] for cell, depth in leaves.values()]) - omission_rgb[k]) for k in range(3)]
        high = [math.fsum([analytic_rgb[k]] + [cell[6 + k] for cell, depth in leaves.values()]) + omission_rgb[k] for k in range(3)]
        if not all(_finite(x) for x in low + high) or any(x > y for x, y in zip(low, high)):
            raise ReferenceFailure("reference_global_interval_range")
        midpoint = [lo + 0.5 * (hi - lo) for lo, hi in zip(low, high)]
        channel_radius = [max(mid - lo, hi - mid) for lo, mid, hi in zip(low, midpoint, high)]
        if not all(_finite(x) for x in midpoint + channel_radius) or any(not lo <= mid <= hi for lo, mid, hi in zip(low, midpoint, high)):
            raise ReferenceFailure("reference_midpoint_range")
        return low, high, midpoint, channel_radius

    def finish(path):
        low, high, midpoint, radius = global_bounds()
        _deadline(deadline_ns, counters)
        if max(radius) > halfwidth_budget:
            raise diagnostic_failure("reference_final_budget", bounds=(low, high, midpoint, radius))
        return {
            "lower": low, "upper": high, "midpoint": midpoint,
            "radius": radius, "max_radius": max(radius),
            "alpha_full": alpha_info["alpha"], "retained_alpha": retained_alpha,
            "finite_masses": alpha_info["masses"],
            "omitted_mass_bound": omitted_mass_bound, "omission_rgb_radius": omission_rgb,
            "omission_threshold": threshold, "omitted_ids": [prepared["source_ids"][i] for i in omitted],
            "retained_ids": p["source_ids"], "retained_mu": p["mu"],
            "retained_sd": p["sd"], "retained_weight": p["weight"],
            "full_mu": list(prepared["mu"]), "full_weight": list(prepared["weight"]),
            "source_ids": list(prepared["source_ids"]),
            "analytic_retained_rgb": analytic_rgb,
            "leaves": [entry[0] for entry in sorted(leaves.values(), key=lambda entry: entry[0][0])],
            "created_cells": local_created, "max_depth": local_max_depth,
            "path": path, "formal_floating_point_certificate": False,
        }

    if not retained:
        _add(counters, "reference_analytic_branches")
        return finish("empty")
    if all(rgb == p["color"][0] for rgb in p["color"]):
        analytic_rgb = [value * retained_alpha for value in p["color"][0]]
        _add(counters, "reference_analytic_branches")
        return finish("equal_color")

    color_min = [min(rgb[k] for rgb in p["color"]) for k in range(3)]
    color_max = [max(rgb[k] for rgb in p["color"]) for k in range(3)]
    log_normalization = 0.5 * _log(2 * math.pi, counters)
    log_peaks = [_log(q, counters) - _log(h, counters) - log_normalization for q, h in zip(p["weight"], p["sd"])]
    cumulative_cache = {a: 0.0}

    def make_cell(left, right, depth):
        serial = allocate(depth)
        if not left < right:
            raise diagnostic_failure("reference_cell_resolution")
        if left not in cumulative_cache:
            cumulative_cache[left] = math.fsum(_masses(p, a, left, counters, deadline_ns))
        mass = math.fsum(_masses(p, left, right, counters, deadline_ns))
        optical_weight = _exp(-cumulative_cache[left], counters) * -_expm1(-mass, counters)
        if not _finite(optical_weight) or optical_weight < 0:
            raise ReferenceFailure("reference_cell_mass_range")
        upper_logs, lower_logs = [], []
        for index, (z, h, peak) in enumerate(zip(p["mu"], p["sd"], log_peaks)):
            if index % 32 == 0:
                _deadline(deadline_ns, counters)
            _add(counters, "reference_density_bound_components")
            nearest = max(left, min(z, right))
            near_distance = abs(nearest - z) / h
            far_distance = max(abs(left - z), abs(right - z)) / h
            upper_logs.append(peak - 0.5 * near_distance * near_distance)
            lower_logs.append(peak - 0.5 * far_distance * far_distance)
        scale = max(upper_logs)
        if not _finite(scale):
            raise ReferenceFailure("reference_density_log_range", "no finite scaling maximum; not vacuum")
        upper_density = [_exp(value - scale, counters) for value in upper_logs]
        lower_density = [_exp(value - scale, counters) for value in lower_logs]
        s_upper, s_lower = math.fsum(upper_density), math.fsum(lower_density)
        if s_upper <= 0 or not _finite(s_upper) or not _finite(s_lower) or s_lower > s_upper:
            raise ReferenceFailure("reference_density_scale_range", "not a vacuum branch")
        lower_color, upper_color = [], []
        for channel in range(3):
            j_lower = math.fsum(rgb[channel] * density for rgb, density in zip(p["color"], lower_density))
            j_upper = math.fsum(rgb[channel] * density for rgb, density in zip(p["color"], upper_density))
            low = min(color_max[channel], max(color_min[channel], j_lower / s_upper))
            high = max(color_min[channel], min(color_max[channel], j_upper / s_lower)) if s_lower > 0 else color_max[channel]
            if not _finite(low) or not _finite(high) or low > high:
                raise ReferenceFailure("reference_color_interval_range")
            lower_color.append(low)
            upper_color.append(high)
        low_rgb = [optical_weight * value for value in lower_color]
        high_rgb = [optical_weight * value for value in upper_color]
        cell = [left, right, optical_weight] + low_rgb + high_rgb
        priority = max(hi - lo for lo, hi in zip(low_rgb, high_rgb))
        if not _finite(priority) or priority < 0:
            raise ReferenceFailure("reference_cell_interval_range")
        leaves[serial] = (cell, depth)
        heapq.heappush(heap, (-priority, serial))
        _deadline(deadline_ns, counters)

    breakpoints = {a, b}
    for z, h in zip(p["mu"], p["sd"]):
        _deadline(deadline_ns, counters)
        for offset in (-6, -3, 0, 3, 6):
            point = z + offset * h
            if a < point < b:
                breakpoints.add(point)
    points = sorted(breakpoints)
    _add(counters, "reference_initial_segments", len(points) - 1)
    for left, right in zip(points, points[1:]):
        make_cell(left, right, 0)
    low, high, midpoint, radius = global_bounds()
    refinements = 0
    while max(radius) > halfwidth_budget:
        _deadline(deadline_ns, counters)
        if not heap:
            low, high, midpoint, radius = global_bounds()
            if max(radius) <= halfwidth_budget:
                break
            raise diagnostic_failure("reference_heap_exhausted", bounds=(low, high, midpoint, radius))
        neg_priority, serial = heapq.heappop(heap)
        cell, depth = leaves[serial]
        if neg_priority == 0:
            low, high, midpoint, radius = global_bounds()
            if max(radius) <= halfwidth_budget:
                break
            raise diagnostic_failure("reference_omission_or_roundoff_floor", bounds=(low, high, midpoint, radius))
        left, right = cell[0], cell[1]
        mid = left + (right - left) / 2
        if not left < mid < right:
            low, high, midpoint, radius = global_bounds()
            if max(radius) <= halfwidth_budget:
                break
            raise diagnostic_failure("reference_subdivision_resolution", bounds=(low, high, midpoint, radius))
        if local_created + 2 > 8192 or counters.get("reference_created_cells", 0) + 2 > 200000:
            low, high, midpoint, radius = global_bounds()
            if max(radius) <= halfwidth_budget:
                break
            if local_created + 2 > 8192:
                raise diagnostic_failure("reference_per_ray_cell_cap", "two children would exceed 8192 created cells", (low, high, midpoint, radius))
            raise diagnostic_failure("reference_global_cell_cap", "two children would exceed 200000 created cells", (low, high, midpoint, radius))
        del leaves[serial]
        make_cell(left, mid, depth + 1)
        make_cell(mid, right, depth + 1)
        refinements += 1
        _add(counters, "reference_refinements")
        # Recompute global sums from current leaves, never accumulate a chain
        # of parent-subtraction errors. Up to 31 extra splits are permissible.
        if refinements % 32 == 0:
            low, high, midpoint, radius = global_bounds()
    return finish("enclosure")
