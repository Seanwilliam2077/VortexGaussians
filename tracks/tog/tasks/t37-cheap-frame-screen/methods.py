"""Two ordinary approximations of the fixed finite-ray emission operation.

This module never reads saved answers, fixture identifiers, files, or reference bounds.
It does not certify either approximation or fall back to integration. The caller
owns preparation and the frozen T22 normal-interval implementation. Counters
record explicit scalar operations and fsum input sizes, not hidden operations
inside fsum, erfc, sorting, validation, or the interpreter.
"""
import math
import time


ARMS = ("sorted", "mixture")


class CheapFailure(RuntimeError):
    pass


def _add(counters, key, amount=1):
    counters[key] = counters.get(key, 0) + amount


def _deadline(deadline_ns):
    if time.perf_counter_ns() >= deadline_ns:
        raise TimeoutError("T37 ordinary approximation deadline")


def _finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _sum(values, counters, phase):
    _add(counters, "cheap_fsum_calls")
    _add(counters, "cheap_fsum_input_terms", len(values))
    _add(counters, phase + "_fsum_calls")
    return math.fsum(values)


def _insert_partial(partials, value, counters):
    """Maintain a local accurate-sum expansion for successive prefixes.

    Prefixes are fsum(partials), avoiding repeated scans of all earlier masses.
    This is ordinary floating-point summation, not an outward-rounded bound.
    The finite nonnegative total mass has already been checked by the caller.
    """
    write = 0
    for previous in partials:
        _add(counters, "sorted_prefix_expansion_steps")
        if abs(value) < abs(previous):
            value, previous = previous, value
            _add(counters, "sorted_prefix_expansion_swaps")
        high = value + previous
        low = previous - (high - value)
        _add(counters, "cheap_add_operations")
        _add(counters, "cheap_subtract_operations", 2)
        if low:
            partials[write] = low
            write += 1
            _add(counters, "sorted_prefix_residuals_retained")
        value = high
    partials[write:] = [value]


def _validate(prepared, counters, deadline_ns):
    _deadline(deadline_ns)
    a, b = prepared["a"], prepared["b"]
    if not (_finite_number(a) and _finite_number(b) and a < b):
        raise CheapFailure("Invalid finite ray domain")
    n = len(prepared["mu"])
    if any(len(prepared[key]) != n for key in ("sd", "weight", "color", "source_ids")):
        raise CheapFailure("Mismatched parameter lengths")
    if prepared["background_term"] != [0, 0, 0]:
        raise CheapFailure("T37 only admits the frozen black background")
    identifiers = prepared["source_ids"]
    if any(type(index) is not int or index < 0 for index in identifiers):
        raise CheapFailure("Invalid source identifier")
    if len(set(identifiers)) != n:
        raise CheapFailure("Duplicate source identifiers")
    for z, h, q, color in zip(prepared["mu"], prepared["sd"],
                              prepared["weight"], prepared["color"]):
        _deadline(deadline_ns)
        if not (all(_finite_number(x) for x in (z, h, q)) and h > 0 and q >= 0):
            raise CheapFailure("Invalid Gaussian parameter")
        if len(color) != 3 or any(not _finite_number(c) or c < 0 for c in color):
            raise CheapFailure("Invalid nonnegative HDR color")
        _add(counters, "cheap_validated_components")
    return n


def solve(prepared, arm, counters, deadline_ns, kernel):
    """Deliver a cheap RGB approximation; accuracy is assessed outside.

    Returned alpha and tau concern the supplied retained field. The caller
    accounts for pruning against the full field. Each call recomputes its own
    finite masses; no state persists between rays or arms.
    """
    _add(counters, "cheap_calls")
    if arm not in ARMS:
        raise CheapFailure("Unknown ordinary approximation arm")
    n = _validate(prepared, counters, deadline_ns)
    masses = []
    for z, h, q in zip(prepared["mu"], prepared["sd"], prepared["weight"]):
        _deadline(deadline_ns)
        if q == 0:
            mass = 0.0
            _add(counters, "cheap_zero_weight_cdf_skips")
        else:
            probability = kernel._normal_interval(prepared["a"], prepared["b"], z, h, counters)
            if not math.isfinite(probability) or not 0 <= probability <= 1:
                raise CheapFailure("Invalid computed finite Gaussian mass fraction")
            mass = q * probability
            _add(counters, "cheap_multiply_operations")
            _add(counters, "cheap_mass_evaluations")
        if not math.isfinite(mass) or mass < 0:
            raise CheapFailure("Invalid computed finite optical mass")
        masses.append(mass)
    tau = _sum(masses, counters, "total_mass")
    if not math.isfinite(tau) or tau < 0:
        raise CheapFailure("Nonfinite total optical mass")
    _add(counters, "cheap_expm1_calls")
    alpha = -math.expm1(-tau)
    if not math.isfinite(alpha) or not 0 <= alpha <= 1:
        raise CheapFailure("Invalid total alpha")
    if n == 0 or tau == 0:
        # Computed zero mass need not imply an exact real-arithmetic vacuum.
        _add(counters, "cheap_computed_zero_paths")
        return {"rgb": [0.0, 0.0, 0.0], "alpha": alpha, "tau": tau}

    active = [index for index, mass in enumerate(masses) if mass > 0]
    _add(counters, "cheap_zero_mass_component_skips", n - len(active))
    contributions = [[], [], []]
    if arm == "sorted":
        order = sorted(active, key=lambda i: (prepared["mu"][i], prepared["source_ids"][i]))
        _add(counters, "cheap_sort_calls")
        _add(counters, "cheap_sort_key_evaluations", len(order))
        partials = []
        for index in order:
            _deadline(deadline_ns)
            prefix = _sum(partials, counters, "sorted_prefix")
            transmission = math.exp(-prefix)
            component_alpha = -math.expm1(-masses[index])
            _add(counters, "cheap_exp_calls")
            _add(counters, "cheap_expm1_calls")
            coefficient = transmission * component_alpha
            _add(counters, "cheap_multiply_operations")
            for channel in range(3):
                contributions[channel].append(coefficient * prepared["color"][index][channel])
            _add(counters, "cheap_multiply_operations", 3)
            _add(counters, "sorted_composited_components")
            _insert_partial(partials, masses[index], counters)
        rgb = [_sum(values, counters, "sorted_rgb") for values in contributions]
    else:
        for index in active:
            _deadline(deadline_ns)
            for channel in range(3):
                contributions[channel].append(masses[index] * prepared["color"][index][channel])
            _add(counters, "cheap_multiply_operations", 3)
            _add(counters, "mixture_weighted_components")
        rgb = []
        for values in contributions:
            mean_color = _sum(values, counters, "mixture_source") / tau
            rgb.append(alpha * mean_color)
        _add(counters, "cheap_divide_operations", 3)
        _add(counters, "cheap_multiply_operations", 3)
    _deadline(deadline_ns)
    if len(rgb) != 3 or any(not math.isfinite(value) or value < 0 for value in rgb):
        raise CheapFailure("Invalid computed approximation RGB")
    _add(counters, "cheap_nonzero_paths")
    return {"rgb": rgb, "alpha": alpha, "tau": tau}
