"""Frozen ordinary bounded GN polishing; no numerical work or NumPy import here.

The caller supplies the current-state Euler target and performs independent
seed/final physics confirmation.  This module never evaluates induced velocity.
"""

import copy
import math
import time


SCHEMA = "t76-ordinary-continuous-polish-v1"
COUNTER_KEYS = (
    "polish_invocations", "polish_linearizations", "polish_model_calls",
    "polish_model_seed_calls", "polish_model_trial_calls", "polish_model_canonical_calls",
    "polish_model_points", "polish_model_component_points", "polish_model_exp_evaluations",
    "polish_jacobian_calls", "polish_jacobian_column_values", "polish_zero_jacobian_columns",
    "polish_column_norm_reductions", "polish_column_norm_point_visits",
    "polish_gradient_reductions", "polish_gradient_point_visits",
    "polish_svd_calls", "polish_svd_input_values", "polish_svd_input_columns",
    "polish_svd_rhs_reductions", "polish_svd_rhs_point_visits",
    "polish_retained_singular_values", "polish_truncated_singular_values",
    "polish_initial_inactive_geometry_exclusions", "polish_active_bound_exclusions",
    "polish_active_set_resolves", "polish_direction_field_products",
    "polish_direction_field_point_columns", "polish_trial_attempts",
    "polish_invalid_trials", "polish_negative_mass_rejections", "polish_zero_total_rejections",
    "polish_geometry_bound_rejections", "polish_objective_rejections", "polish_accepted_steps",
    "polish_direct_reductions", "polish_direct_reduction_point_visits",
    "polish_width_roundtrip_clamps", "polish_state_canonicalizations",
    "polish_canonical_comparison_values", "polish_seed_fallbacks",
    "polish_canonical_rounding_fallbacks", "polish_changed_returns",
    "polish_cache_validation_values",
)
CAPS = {
    "polish_invocations": 1, "polish_linearizations": 20,
    "polish_svd_calls": 180, "polish_trial_attempts": 160,
    "polish_model_calls": 162, "polish_model_seed_calls": 1,
    "polish_model_trial_calls": 160, "polish_model_canonical_calls": 1,
    "polish_jacobian_calls": 20,
}
EPS64 = 2.220446049250313e-16


def polish_one(np, current, h, found, target_cache, counters, emit, deadline_ns):
    """Return a proposed state and scalar audit; independent confirmation is external.

    Required cache keys: r,z,W,q,F,y,S, where S=h*h*integral(F*F).
    All arrays are the current target's fixed D12-64x128/heat128 route.
    A normal stop retains the best feasible point. Scientific failures raise.
    """
    local = dict.fromkeys(COUNTER_KEYS, 0)

    def clock():
        if time.perf_counter_ns() >= deadline_ns:
            raise TimeoutError("T76 polishing deadline")

    def charge(key, amount=1):
        amount = int(amount)
        value = local[key] + amount
        if key in CAPS and value > CAPS[key]:
            raise ArithmeticError(key + " exceeded its frozen per-target cap")
        local[key] = value
        counters[key] = counters.get(key, 0) + amount

    def event(kind, packet):
        clock()
        emit("polish_" + kind, packet)

    def require(ok, message):
        if not ok:
            raise ValueError(message)

    def finite_scalar(value, label):
        value = float(value)
        if not math.isfinite(value):
            raise ArithmeticError("nonfinite " + label)
        return value

    clock()
    charge("polish_invocations")
    h = finite_scalar(h, "time step")
    current_gamma = finite_scalar(current["Gamma"], "current circulation")
    require(h > 0.0 and current_gamma > 0.0, "positive current circulation and time step required")
    require(found.get("h") == h and found.get("original_state") == current,
            "ordinary search seed must belong to this exact current state and time step")
    require(found.get("selected_state") is not None, "ordinary search supplied no positive seed")
    seed = copy.deepcopy(found["selected_state"])
    seed_gamma = finite_scalar(seed["Gamma"], "seed circulation")
    seed_eta = finite_scalar(seed["eta"], "seed mixture weight")
    require(seed_gamma > 0.0 and 0.0 <= seed_eta <= 1.0, "invalid seed weights")
    require(len(seed["geometry"]) == 2 and all(len(g) == 3 for g in seed["geometry"]), "two seed geometries required")
    seed_geometry = [[finite_scalar(value, "seed geometry") for value in g] for g in seed["geometry"]]
    seed_masses = [seed_gamma * (1.0 - seed_eta), seed_gamma * seed_eta]
    require(all(math.isfinite(c) and c >= 0.0 for c in seed_masses), "invalid seed component circulations")
    bounds = [[finite_scalar(value, "geometry bound") for value in pair] for pair in found["search_bounds"]]
    require(len(bounds) == 3 and all(len(pair) == 2 and pair[0] <= pair[1] for pair in bounds), "invalid search bounds")
    require(bounds[0][0] > 0.0 and bounds[1][0] > 0.0, "positive width bounds required")
    require(all(bounds[k][0] <= g[k] <= bounds[k][1] for g in seed_geometry for k in range(3)), "seed outside original search bounds")
    search_Z = finite_scalar(found["search_scales"]["Z"], "original search Z")
    require(search_Z > 0.0, "positive original search Z required")
    r, z, W, q, F, y = (np.asarray(target_cache[key], dtype=float) for key in ("r", "z", "W", "q", "F", "y"))
    require(all(array.shape == (8192,) for array in (r, z, W, q, F, y)), "fixed 8192-point cache required")
    require(all(bool(np.all(np.isfinite(array))) for array in (r, z, W, q, F, y)), "nonfinite target cache")
    require(bool(np.all(r >= 0.0) and np.all(W > 0.0)), "invalid fixed-grid radii or weights")
    charge("polish_cache_validation_values", 6 * r.size)
    S = finite_scalar(target_cache["S"], "unchanged-target squared norm S")
    require(S > 0.0, "positive unchanged-target squared norm required")
    sqrt_W = np.sqrt(W)
    sqrt_S = math.sqrt(S)
    r_squared = r * r
    sqrt_two_pi = math.sqrt(2.0 * math.pi)
    low = np.asarray([0.0, 0.0, math.log(bounds[0][0]), math.log(bounds[1][0]), bounds[2][0],
                      math.log(bounds[0][0]), math.log(bounds[1][0]), bounds[2][0]])
    high = np.asarray([math.inf, math.inf, math.log(bounds[0][1]), math.log(bounds[1][1]), bounds[2][1],
                       math.log(bounds[0][1]), math.log(bounds[1][1]), bounds[2][1]])
    trust_limits = np.asarray([0.25 * current_gamma, 0.25 * current_gamma, 0.20, 0.20,
                               0.25 * search_Z, 0.20, 0.20, 0.25 * search_Z])
    require(bool(np.all(np.isfinite(trust_limits)) and np.all(trust_limits > 0.0)), "invalid fixed trust limits")

    def integral(values):
        charge("polish_direct_reductions")
        charge("polish_direct_reduction_point_visits", values.size)
        return finite_scalar(np.sum(W * values, dtype=np.float64), "polish direct integral")

    def model(masses, geometry, kind):
        clock()
        charge("polish_model_calls")
        charge("polish_model_" + kind + "_calls")
        charge("polish_model_points", r.size)
        components, unit = [], []
        for mass, (sr, sz, center) in zip(masses, geometry):
            require(math.isfinite(mass) and mass >= 0.0 and math.isfinite(sr) and sr > 0.0
                    and math.isfinite(sz) and sz > 0.0 and math.isfinite(center), "invalid feasible model input")
            charge("polish_model_component_points", r.size)
            charge("polish_model_exp_evaluations", r.size)
            norm = finite_scalar(sr * sr * sqrt_two_pi * sz, "Gaussian normalization")
            require(norm > 0.0, "nonpositive Gaussian normalization")
            g = np.exp(-r_squared / (2.0 * sr * sr) - (z - center) ** 2 / (2.0 * sz * sz)) / norm
            part = mass * g
            if not np.all(np.isfinite(g)) or not np.all(np.isfinite(part)):
                raise ArithmeticError("nonfinite valid-candidate Gaussian field")
            unit.append(g)
            components.append(part)
        field = components[0] + components[1]
        if not np.all(np.isfinite(field)):
            raise ArithmeticError("nonfinite valid-candidate mixture field")
        residual = y - field
        objective = integral(residual * residual)
        require(objective >= 0.0, "negative direct squared objective")
        return {"masses": list(map(float, masses)), "geometry": [list(map(float, g)) for g in geometry],
                "unit": unit, "components": components, "field": field,
                "residual": residual, "E": objective}

    def encode(masses, geometry):
        return np.asarray([masses[0], masses[1], math.log(geometry[0][0]), math.log(geometry[0][1]), geometry[0][2],
                           math.log(geometry[1][0]), math.log(geometry[1][1]), geometry[1][2]], dtype=float)

    def trial_geometry(theta):
        geometry, clamp_records = [], []
        for component in range(2):
            offset = 2 + 3 * component
            values = []
            for k in range(2):
                raw = math.exp(float(theta[offset + k]))
                raw = finite_scalar(raw, "valid log-width exponential")
                bounded = min(bounds[k][1], max(bounds[k][0], raw))
                if bounded != raw:
                    charge("polish_width_roundtrip_clamps")
                    clamp_records.append({"component": component, "coordinate": k,
                        "unclamped": raw, "bound": bounded,
                        "absolute_difference": abs(raw - bounded),
                        "difference_in_bound_ulps": abs(raw - bounded) / math.ulp(bounded)})
                values.append(bounded)
            values.append(float(theta[offset + 2]))
            geometry.append(values)
        return geometry, clamp_records

    def jacobian(at):
        clock()
        charge("polish_jacobian_calls")
        charge("polish_jacobian_column_values", 8 * r.size)
        J = np.empty((r.size, 8), dtype=float)
        for i in range(2):
            sr, sz, center = at["geometry"][i]
            part = at["components"][i]
            J[:, i] = at["unit"][i]
            offset = 2 + 3 * i
            J[:, offset] = part * (-2.0 + r_squared / (sr * sr))
            J[:, offset + 1] = part * (-1.0 + (z - center) ** 2 / (sz * sz))
            J[:, offset + 2] = part * (z - center) / (sz * sz)
        if not np.all(np.isfinite(J)):
            raise ArithmeticError("nonfinite valid-candidate analytic Jacobian")
        charge("polish_column_norm_reductions", 8)
        charge("polish_column_norm_point_visits", J.size)
        norm_squared = np.sum(W[:, None] * J * J, axis=0, dtype=np.float64)
        if not np.all(np.isfinite(norm_squared)) or not np.all(norm_squared >= 0.0):
            raise ArithmeticError("invalid Jacobian column norms")
        scales = np.sqrt(norm_squared)
        zero = scales == 0.0
        if np.any(zero & np.any(J != 0.0, axis=0)):
            raise ArithmeticError("nonzero Jacobian column norm underflowed to zero")
        charge("polish_zero_jacobian_columns", np.count_nonzero(zero))
        scales[zero] = 1.0
        B = sqrt_W[:, None] * J / scales[None, :]
        if not np.all(np.isfinite(B)):
            raise ArithmeticError("nonfinite normalized analytic Jacobian")
        return J, B, scales

    seed_model = model(seed_masses, seed_geometry, "seed")
    seed_E = seed_model["E"]
    delta = 1.0e-10 * S + 64.0 * EPS64 * seed_E
    require(math.isfinite(delta) and delta > 0.0, "invalid frozen resolution floor")
    at = seed_model
    theta = encode(seed_masses, seed_geometry)
    linearizations = []
    stop_reason = "iteration_cap"
    event("started", {"h": h, "seed_state": seed, "seed_objective": seed_E, "S": S,
        "resolution_floor": delta, "search_bounds": bounds, "search_Z": search_Z,
        "trust_limits": trust_limits.tolist()})
    for iteration in range(20):
        clock()
        charge("polish_linearizations")
        J, B, scales = jacobian(at)
        weighted_residual = sqrt_W * at["residual"]
        gradient = B.T @ weighted_residual
        charge("polish_gradient_reductions", 8)
        charge("polish_gradient_point_visits", B.size)
        if not np.all(np.isfinite(gradient)):
            raise ArithmeticError("nonfinite normalized free gradient")
        free = np.ones(8, dtype=bool)
        initial_exclusions = []
        for component in range(2):
            if theta[component] == 0.0:
                excluded = list(range(2 + 3 * component, 5 + 3 * component))
                free[excluded] = False
                initial_exclusions.extend(excluded)
        charge("polish_initial_inactive_geometry_exclusions", len(initial_exclusions))
        record = {"iteration": iteration, "objective_before": at["E"],
            "column_scales": scales.tolist(), "initial_inactive_geometry_exclusions": initial_exclusions,
            "solves": [], "trial_attempts": 0, "accepted": False}
        linearizations.append(record)
        direction = None
        for resolve in range(9):
            clock()
            indices = np.flatnonzero(free)
            if indices.size == 0:
                stop_reason = "no_free_direction"
                break
            gradient_score = finite_scalar(float(np.max(np.abs(gradient[indices]))) / sqrt_S,
                                           "normalized free gradient score")
            record["normalized_free_gradient"] = gradient_score
            if gradient_score <= 1.0e-7:
                stop_reason = "free_gradient_tolerance"
                break
            matrix = B[:, indices]
            charge("polish_svd_calls")
            charge("polish_svd_input_values", matrix.size)
            charge("polish_svd_input_columns", indices.size)
            u, singular, vh = np.linalg.svd(matrix, full_matrices=False)
            if not np.all(np.isfinite(u)) or not np.all(np.isfinite(singular)) or not np.all(np.isfinite(vh)):
                raise ArithmeticError("nonfinite damped SVD")
            smax = float(singular[0])
            if not np.all(singular >= 0.0):
                raise ArithmeticError("negative SVD singular value")
            retained = singular > 1.0e-10 * smax
            rank = int(np.count_nonzero(retained))
            charge("polish_retained_singular_values", rank)
            charge("polish_truncated_singular_values", singular.size - rank)
            solve_record = {"resolve": resolve, "free_columns": indices.tolist(),
                "singular_values": singular.tolist(), "retained_rank": rank,
                "truncated_count": int(singular.size - rank), "rank_cutoff": 1.0e-10 * smax,
                "damping": 1.0e-6 * smax * smax, "outward_active_bound_exclusions": []}
            record["solves"].append(solve_record)
            if rank == 0:
                stop_reason = "zero_retained_rank"
                break
            factors = singular[retained] / (singular[retained] ** 2 + 1.0e-6 * smax * smax)
            charge("polish_svd_rhs_reductions", rank)
            charge("polish_svd_rhs_point_visits", rank * r.size)
            normalized_direction = vh[retained, :].T @ (factors * (u[:, retained].T @ weighted_residual))
            proposed_direction = np.zeros(8, dtype=float)
            proposed_direction[indices] = normalized_direction / scales[indices]
            if not np.all(np.isfinite(proposed_direction)):
                raise ArithmeticError("nonfinite damped direction")
            excluded = [int(index) for index in indices if
                (theta[index] == low[index] and proposed_direction[index] < 0.0)
                or (theta[index] == high[index] and proposed_direction[index] > 0.0)]
            solve_record["outward_active_bound_exclusions"] = excluded
            if excluded:
                free[excluded] = False
                charge("polish_active_bound_exclusions", len(excluded))
                charge("polish_active_set_resolves")
                stop_reason = "active_set_resolve_cap"
                continue
            direction = proposed_direction
            break
        if direction is None:
            record["stop_reason"] = stop_reason
            event("linearization", record)
            break
        relative_trust = finite_scalar(np.max(np.abs(direction) / trust_limits), "relative trust displacement")
        trust_scale = 1.0 / relative_trust if relative_trust > 1.0 else 1.0
        direction = direction * trust_scale
        if not np.all(np.isfinite(direction)):
            raise ArithmeticError("nonfinite trust-scaled direction")
        charge("polish_direction_field_products")
        charge("polish_direction_field_point_columns", J.size)
        direction_field = J @ direction
        g = integral(at["residual"] * direction_field)
        record.update(trust_scale=trust_scale, direction=direction.tolist(), directional_descent=g)
        if g <= 0.0:
            stop_reason = "no_free_descending_direction"
            record["stop_reason"] = stop_reason
            event("linearization", record)
            break
        accepted = False
        for backtrack in range(8):
            clock()
            charge("polish_trial_attempts")
            record["trial_attempts"] += 1
            alpha = math.ldexp(1.0, -backtrack)
            trial_theta = theta + alpha * direction
            if not np.all(np.isfinite(trial_theta)):
                raise ArithmeticError("nonfinite proposal from finite coordinates and direction")
            reason = None
            if np.any(trial_theta[:2] < 0.0):
                reason = "negative_mass"
                charge("polish_negative_mass_rejections")
            elif math.fsum(map(float, trial_theta[:2])) <= 0.0:
                reason = "zero_total_circulation"
                charge("polish_zero_total_rejections")
            elif np.any(trial_theta[2:] < low[2:]) or np.any(trial_theta[2:] > high[2:]):
                reason = "geometry_bound"
                charge("polish_geometry_bound_rejections")
            if reason is not None:
                charge("polish_invalid_trials")
                event("trial", {"iteration": iteration, "backtrack": backtrack, "alpha": alpha,
                    "coordinates": trial_theta.tolist(), "evaluated": False, "accepted": False, "reason": reason})
                continue
            geometry, clamps = trial_geometry(trial_theta)
            candidate = model(trial_theta[:2], geometry, "trial")
            gain = at["E"] - candidate["E"]
            armijo_limit = at["E"] - 2.0e-4 * alpha * g
            accepted = candidate["E"] <= armijo_limit and gain >= delta
            event("trial", {"iteration": iteration, "backtrack": backtrack, "alpha": alpha,
                "coordinates": trial_theta.tolist(), "geometry": geometry, "roundtrip_clamps": clamps,
                "evaluated": True, "objective": candidate["E"], "gain": gain,
                "armijo_limit": armijo_limit, "resolution_floor": delta, "accepted": bool(accepted),
                "reason": "accepted" if accepted else "insufficient_decrease"})
            if accepted:
                charge("polish_accepted_steps")
                theta, at = trial_theta, candidate
                record.update(accepted=True, accepted_alpha=alpha, objective_after=at["E"])
                break
            charge("polish_objective_rejections")
        if not accepted:
            stop_reason = "no_accepted_line"
            record["stop_reason"] = stop_reason
            event("linearization", record)
            break
        event("linearization", record)
    else:
        stop_reason = "iteration_cap"

    charge("polish_state_canonicalizations")
    if local["polish_accepted_steps"] == 0:
        canonical_state = copy.deepcopy(seed)
    else:
        pairs = sorted(zip(at["geometry"], at["masses"]), key=lambda pair: (pair[0][2], pair[0][0], pair[0][1]))
        gamma = finite_scalar(math.fsum(pair[1] for pair in pairs), "canonical circulation")
        require(gamma > 0.0, "nonpositive canonical circulation")
        eta = finite_scalar(pairs[1][1] / gamma, "canonical mixture weight")
        require(0.0 <= eta <= 1.0, "invalid canonical mixture weight")
        canonical_state = {"Gamma": gamma, "eta": eta, "geometry": [list(pair[0]) for pair in pairs]}
    canonical_masses = [canonical_state["Gamma"] * (1.0 - canonical_state["eta"]),
                        canonical_state["Gamma"] * canonical_state["eta"]]
    canonical = model(canonical_masses, canonical_state["geometry"], "canonical")
    charge("polish_canonical_comparison_values", r.size)
    canonical_difference = np.abs(canonical["field"] - at["field"])
    canonical_tolerance = 1.0e-10 + 1.0e-9 * np.maximum(np.abs(canonical["field"]), np.abs(at["field"]))
    require(bool(np.all(canonical_difference <= canonical_tolerance)), "canonical field reevaluation inconsistency")
    canonical_gain = seed_E - canonical["E"]
    changed = local["polish_accepted_steps"] > 0 and canonical_state != seed and canonical_gain >= delta
    if changed:
        selected = canonical_state
        final_E = canonical["E"]
        status = "changed_" + stop_reason
        charge("polish_changed_returns")
    else:
        selected = copy.deepcopy(seed)
        final_E = seed_E
        charge("polish_seed_fallbacks")
        if local["polish_accepted_steps"] > 0:
            charge("polish_canonical_rounding_fallbacks")
            status = "seed_retained_canonical_gain_unresolved"
        else:
            status = "seed_retained_" + stop_reason
    audit = {"seed_objective": seed_E, "final_objective": final_E,
        "canonical_objective": canonical["E"], "best_precanonical_objective": at["E"],
        "S": S, "resolution_floor": delta, "changed": bool(changed), "stop_reason": stop_reason,
        "linearizations": linearizations,
        "finalization": {"canonical_state": canonical_state, "canonical_gain": canonical_gain,
            "canonical_field_maximum_absolute_difference": float(np.max(canonical_difference)),
            "canonical_field_maximum_tolerance_ratio": float(np.max(canonical_difference / canonical_tolerance)),
            "returned_exact_seed": not changed,
            "independent_three_route_confirmation_required": True},
        "stationarity_or_global_optimality_certified": False, "candidate_velocity_evaluations": 0}
    require(local["polish_model_calls"] == local["polish_model_seed_calls"]
        + local["polish_model_trial_calls"] + local["polish_model_canonical_calls"], "model call accounting")
    require(local["polish_trial_attempts"] == local["polish_invalid_trials"]
        + local["polish_model_trial_calls"], "trial accounting")
    require(local["polish_model_trial_calls"] == local["polish_objective_rejections"]
        + local["polish_accepted_steps"], "evaluated trial accounting")
    require(local["polish_invalid_trials"] == local["polish_negative_mass_rejections"]
        + local["polish_zero_total_rejections"] + local["polish_geometry_bound_rejections"], "invalid trial accounting")
    require(local["polish_jacobian_calls"] == local["polish_linearizations"], "Jacobian accounting")
    require(local["polish_model_seed_calls"] == local["polish_model_canonical_calls"] == 1, "seed/canonical model accounting")
    result = {"schema": SCHEMA, "selected_state": selected, "seed_state": seed,
        "status": status, "audit": audit, "counters": dict(local)}
    event("completed", {"status": status, "selected_state": selected, "seed_state": seed,
        "seed_objective": seed_E, "final_objective": final_E, "canonical_objective": canonical["E"],
        "changed": bool(changed), "stop_reason": stop_reason, "counters": dict(local)})
    return result
