"""One frozen T75 saved-state diagnostic; no numerical work on import."""

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback


ORDERS = (64, 96, 128, 192, 256)
ROUTES = ((12, 64, 128, 128), (12, 64, 128, 256),
          (12, 96, 192, 128), (12, 96, 192, 256), (8, 96, 192, 256))
COLUMNS = ("c1", "c2", "log_sr1", "log_sz1", "z1", "log_sr2", "log_sz2", "z2")
MAIN_ROUTE = 3


def charge(counts, name, amount=1):
    counts[name] = counts.get(name, 0) + int(amount)


def identity(path, counts):
    body = path.read_bytes()
    charge(counts, "identity_reads")
    charge(counts, "identity_bytes", len(body))
    return {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}, body


def dimensional(np, left, right):
    left, right = np.asarray(left), np.asarray(right)
    error = np.abs(left - right)
    tolerance = 1.0e-10 + 1.0e-9 * np.maximum(np.abs(left), np.abs(right))
    return {"max_absolute_error": float(np.max(error)),
            "max_error_over_tolerance": float(np.max(error / tolerance)),
            "pass": bool(np.all(error <= tolerance))}


def integral(np, weights, values, counts):
    charge(counts, "direct_reductions")
    charge(counts, "direct_reduction_point_visits", values.size)
    answer = float(np.sum(weights * values, dtype=np.float64))
    if not math.isfinite(answer):
        raise ArithmeticError("nonfinite direct reduction")
    return answer


def field_product(matrix, rates, counts):
    charge(counts, "field_matrix_vector_calls")
    charge(counts, "field_matrix_vector_point_columns", matrix.size)
    return matrix @ rates


def circulation_impulse(rates, masses, geometry):
    padded = list(map(float, rates)) + [0.0] * (8 - len(rates))
    rho1, rho2 = geometry[0][0] ** 2, geometry[1][0] ** 2
    return {"circulation": math.fsum(padded[:2]),
            "impulse": 2.0 * math.pi * math.fsum((rho1 * padded[0], rho2 * padded[1],
                2.0 * masses[0] * rho1 * padded[2], 2.0 * masses[1] * rho2 * padded[5]))}


def construct_rules(np, counts, checks):
    result, records = {}, []
    for order in ORDERS:
        k = np.arange(1, order, dtype=float)
        off = k / np.sqrt(4.0 * k * k - 1.0)
        jacobi = np.diag(off, 1) + np.diag(off, -1)
        nodes, vectors = np.linalg.eigh(jacobi)
        weights = 2.0 * vectors[0, :] ** 2
        charge(counts, "rule_eigh_calls")
        charge(counts, "rule_nodes", order)
        valid = bool(np.all(np.isfinite(nodes)) and np.all(np.isfinite(weights))
            and np.all(np.diff(nodes) > 0.0) and np.all(np.abs(nodes) < 1.0)
            and np.all(weights > 0.0))
        errors = {"node_symmetry": float(np.max(np.abs(nodes + nodes[::-1]))),
                  "weight_symmetry": float(np.max(np.abs(weights - weights[::-1]))),
                  "weight_sum": abs(float(np.sum(weights)) - 2.0)}
        passed = valid and all(value <= 1.0e-12 for value in errors.values())
        checks["rule_" + str(order)] = passed
        records.append({"order": order, "finite_ordered_interior_positive": valid,
                        "absolute_errors": errors, "pass": passed})
        if not valid:
            raise ArithmeticError("invalid frozen quadrature rule")
        result[order] = (nodes, weights)
    return result, records


def analytic_gram(np, physics, geometry, masses, counts):
    primitives, moments = {}, {}
    for i, j in ((0, 0), (0, 1), (1, 1)):
        primitives[i, j] = physics.gram(geometry[i], geometry[j])
        sr_i, sz_i, z_i = geometry[i]
        sr_j, sz_j, z_j = geometry[j]
        rho = 1.0 / (sr_i ** -2 + sr_j ** -2)
        nu = 1.0 / (sz_i ** -2 + sz_j ** -2)
        mu = nu * (z_i / sz_i ** 2 + z_j / sz_j ** 2)
        radial = (1.0, 4.0 * rho, 24.0 * rho * rho)
        axial = [1.0, mu]
        for degree in range(2, 5):
            axial.append(mu * axial[-1] + (degree - 1) * nu * axial[-2])
        moments[i, j] = radial, axial
    specs = [(0, {(0, 0): 1.0}), (1, {(0, 0): 1.0})]
    for i, (sr, sz, z0) in enumerate(geometry):
        mass, rho, nu = masses[i], sr * sr, sz * sz
        specs.extend(((i, {(0, 0): -2.0 * mass, (1, 0): mass / rho}),
                      (i, {(0, 0): mass * (z0 * z0 / nu - 1.0),
                           (0, 1): -2.0 * mass * z0 / nu, (0, 2): mass / nu}),
                      (i, {(0, 0): -mass * z0 / nu, (0, 1): mass / nu})))
    gram = np.empty((8, 8), dtype=float)
    for row, (i, left) in enumerate(specs):
        for col, (j, right) in enumerate(specs):
            key = tuple(sorted((i, j)))
            radial, axial = moments[key]
            terms = []
            for (ru, rz), a in left.items():
                for (su, sz), b in right.items():
                    terms.append(a * b * radial[ru + su] * axial[rz + sz])
                    charge(counts, "analytic_polynomial_moment_products")
            gram[row, col] = primitives[key] * math.fsum(terms)
            charge(counts, "analytic_polynomial_gram_entries")
    if not np.all(np.isfinite(gram)) or not np.all(np.diag(gram) > 0.0):
        raise ArithmeticError("invalid analytic Gram or column norms")
    norms = np.sqrt(np.diag(gram))
    return gram, norms, {str(key): value for key, value in primitives.items()}


def projection(np, matrix, weighted_matrix, weighted_F, weights, F, F_norm,
               column_norms, analytic_normalized, direct_gram, dimension,
               masses, geometry, counts):
    B = weighted_matrix[:, :dimension]
    u, singular, vh = np.linalg.svd(B, full_matrices=False)
    charge(counts, "tall_svd_calls")
    charge(counts, "tall_svd_input_values", B.size)
    if not np.all(np.isfinite(singular)) or singular[0] <= 0.0:
        raise ArithmeticError("invalid tangent singular values")
    retained = singular > 1.0e-10 * singular[0]
    rank = int(np.count_nonzero(retained))
    normalized_rates = vh[retained, :].T @ ((u[:, retained].T @ weighted_F) / singular[retained])
    rates = normalized_rates / column_norms[:dimension]
    projected = field_product(matrix[:, :dimension], rates, counts)
    residual_field = F - projected
    residual = integral(np, weights, residual_field ** 2, counts)
    captured = integral(np, weights, projected ** 2, counts)
    normal_equation = B.T @ (np.sqrt(weights) * residual_field) / math.sqrt(F_norm)
    charge(counts, "normal_equation_column_reductions", dimension)
    charge(counts, "normal_equation_point_columns", B.size)
    normalized_direct = direct_gram[:dimension, :dimension] / (
        column_norms[:dimension, None] * column_norms[None, :dimension])
    delta_gram = normalized_direct - analytic_normalized[:dimension, :dimension]
    frobenius = float(np.linalg.norm(delta_gram, ord="fro"))
    charge(counts, "gram_frobenius_reductions")
    gram_minimum = float(singular[-1] ** 2)
    perturbation = frobenius / gram_minimum if gram_minimum > 0.0 else None
    ratio = float(singular[-1] / singular[0])
    decomposition = abs(captured + residual - F_norm) / F_norm
    normal_error = float(np.max(np.abs(normal_equation)))
    entry_error = float(np.max(np.abs(delta_gram)))
    record = {
        "dimension": dimension, "rank": rank, "rank_cutoff": float(1.0e-10 * singular[0]),
        "singular_values": singular.tolist(), "normalized_gram_spectrum": (singular ** 2).tolist(),
        "minimum_to_maximum_singular_ratio": ratio,
        "condition_number": float(singular[0] / singular[-1]) if singular[-1] > 0.0 else None,
        "normalized_coefficients": normalized_rates.tolist(), "raw_coefficients": rates.tolist(),
        "residual_squared": residual, "captured_squared": captured,
        "relative_residual_squared": residual / F_norm, "relative_capture_squared": captured / F_norm,
        "normal_equation_residual": normal_equation.tolist(),
        "normal_equation_maximum": normal_error, "normalized_norm_decomposition_error": decomposition,
        "normalized_gram_maximum_absolute_difference": entry_error,
        "normalized_gram_frobenius_difference": frobenius,
        "gram_perturbation_over_smallest_eigenvalue": perturbation,
        "signed_rates": circulation_impulse(rates, masses, geometry),
        "checks": {"complete_rank": rank == dimension, "conditioning": ratio >= 1.0e-6,
            "normal_equations": normal_error <= 1.0e-9, "norm_decomposition": decomposition <= 1.0e-9,
            "normalized_gram_entries": entry_error <= 1.0e-9,
            "gram_perturbation": perturbation is not None and perturbation <= 1.0e-3,
            "finite_coefficients_and_nonnegative_norms": bool(np.all(np.isfinite(rates))
                and np.all(np.isfinite(normalized_rates)) and residual >= 0.0 and captured >= 0.0)},
    }
    return record, projected


def evaluate_route(np, physics, rules, route, packet, masses, next_masses,
                   gram, column_norms, counts):
    domain, nr, nz, heat = route
    rn, rw = rules[nr]
    zn, zw = rules[nz]
    r = np.repeat(0.5 * domain * (rn + 1.0), nz)
    z = np.tile(domain * zn, nr)
    base_weights = np.repeat(0.5 * domain * rw, nz) * np.tile(domain * zw, nr)
    weights = 2.0 * math.pi * r ** 3 * base_weights
    fields = physics.field(packet["state"], r, z, heat)
    components = sorted(fields["components"], key=lambda item: item["index"])
    if len(components) != 2 or len(fields["ordered_Fij"]) != 4:
        raise ArithmeticError("current state did not retain both components and four interactions")
    matrix = np.empty((r.size, 8), dtype=float)
    for i, component in enumerate(components):
        sr, sz, z0 = packet["state"]["geometry"][i]
        q = component["q"]
        matrix[:, i] = q / masses[i]
        offset = 2 + 3 * i
        matrix[:, offset] = q * (-2.0 + r * r / (sr * sr))
        matrix[:, offset + 1] = q * (-1.0 + (z - z0) ** 2 / (sz * sz))
        matrix[:, offset + 2] = q * (z - z0) / (sz * sz)
    charge(counts, "tangent_column_values", matrix.size)
    if not np.all(np.isfinite(matrix)) or not np.all(weights > 0.0) or not np.all(fields["q"] > 0.0):
        raise ArithmeticError("invalid tangent array, H weights, or current positive field")
    F = fields["F"]
    norm_F = integral(np, weights, F * F, counts)
    if norm_F <= 0.0:
        raise ArithmeticError("nonpositive current derivative norm")
    direct_gram = np.empty((8, 8), dtype=float)
    for i in range(8):
        for j in range(8):
            direct_gram[i, j] = integral(np, weights, matrix[:, i] * matrix[:, j], counts)
            charge(counts, "direct_gram_entries")
    analytic_normalized = gram / (column_norms[:, None] * column_norms[None, :])
    weighted_matrix = np.sqrt(weights)[:, None] * matrix / column_norms[None, :]
    charge(counts, "weighted_normalized_matrix_values", weighted_matrix.size)
    weighted_F = np.sqrt(weights) * F
    weight_record, weight_projection = projection(np, matrix, weighted_matrix, weighted_F,
        weights, F, norm_F, column_norms, analytic_normalized, direct_gram, 2,
        masses, packet["state"]["geometry"], counts)
    full_record, full_projection = projection(np, matrix, weighted_matrix, weighted_F,
        weights, F, norm_F, column_norms, analytic_normalized, direct_gram, 8,
        masses, packet["state"]["geometry"], counts)
    h = packet["h"]
    saved_rates = np.asarray([math.fsum((next_masses[i], -masses[i])) / h for i in range(2)])
    saved_projection = field_product(matrix[:, :2], saved_rates, counts)
    saved_residual = integral(np, weights, (F - saved_projection) ** 2, counts)
    next_q = field_product(matrix[:, :2], np.asarray(next_masses), counts)
    target = fields["q"] + h * F
    target_residual = integral(np, weights, (target - next_q) ** 2, counts)
    unchanged_residual = integral(np, weights, (target - fields["q"]) ** 2, counts)
    q_norm = integral(np, weights, fields["q"] ** 2, counts)
    analytic_q_norm = math.fsum(masses[i] * masses[j] * float(gram[i, j])
                               for i in range(2) for j in range(2))
    saved_control = next(row for row in packet["next_confirmation"]["routes"] if row["order"] == heat)
    ordered_sum = sum((part["value"] for part in fields["ordered_Fij"]), np.zeros_like(F))
    comparisons = {
        "raw_analytic_gram": dimensional(np, direct_gram, gram),
        "ordered_interaction_sum": dimensional(np, ordered_sum, F),
        "current_q_norm_analytic": dimensional(np, q_norm, analytic_q_norm),
        "saved_current_norm": dimensional(np, q_norm, packet["next_confirmation"]["current_norm"]),
        "saved_target_residual": dimensional(np, target_residual, saved_control["N"]),
        "saved_unchanged_residual": dimensional(np, unchanged_residual, saved_control["N_unchanged"]),
        "saved_derivative_target_identity": dimensional(np, target_residual, h * h * saved_residual),
    }
    saved_weight_difference = integral(np, weights, (saved_projection - weight_projection) ** 2, counts)
    geometry_gap = (weight_record["residual_squared"] - full_record["residual_squared"]) / norm_F
    additional_geometry_norm = integral(np, weights, (full_projection - weight_projection) ** 2, counts)
    geometry_pythagorean_error = abs(weight_record["residual_squared"]
        - full_record["residual_squared"] - additional_geometry_norm) / norm_F
    weight_relative = weight_record["relative_residual_squared"]
    fraction_removed = geometry_gap / weight_relative if weight_relative > 0.0 else None
    direct_rates = {
        "circulation": integral(np, base_weights, r * F, counts),
        "impulse": integral(np, base_weights, math.pi * r ** 3 * F, counts),
    }
    record = {
        "name": "D%d-%dx%d-heat%d" % route, "domain": domain, "nr": nr, "nz": nz, "heat": heat,
        "spatial_points": int(r.size), "F_norm_squared": norm_F, "q_norm_squared": q_norm,
        "direct_gram": direct_gram.tolist(), "weight": weight_record, "full": full_record,
        "geometry_gap_over_F_norm_squared": geometry_gap,
        "additional_geometry_field_norm_squared": additional_geometry_norm,
        "additional_geometry_field_norm_over_F_norm_squared": additional_geometry_norm / norm_F,
        "geometry_pythagorean_normalized_error": geometry_pythagorean_error,
        "fraction_weight_residual_squared_removed": fraction_removed,
        "saved_update": {"mass_rates": saved_rates.tolist(), "residual_squared": saved_residual,
            "relative_residual_squared": saved_residual / norm_F,
            "Euler_target_residual_squared": target_residual, "Euler_unchanged_residual_squared": unchanged_residual,
            "field_difference_from_optimal_weights_over_F_norm": math.sqrt(saved_weight_difference / norm_F),
            "residual_gap_from_optimal_weights_over_F_norm_squared": (saved_residual - weight_record["residual_squared"]) / norm_F,
            "signed_rates": circulation_impulse(saved_rates, masses, packet["state"]["geometry"])},
        "direct_F_signed_rates": direct_rates, "dimensional_comparisons": comparisons,
        "checks": {"finite_positive_arrays": True, "nested_residual_order": geometry_gap >= -1.0e-9,
            "geometry_pythagorean_decomposition": geometry_pythagorean_error <= 1.0e-9,
            **{key: value["pass"] for key, value in comparisons.items()}},
    }
    internal = {"matrix": matrix, "weights": weights, "F": F, "fields": fields,
                "weight_projection": weight_projection, "full_projection": full_projection}
    return record, internal


def compare_routes(np, records, internal, counts, checks):
    main = records[MAIN_ROUTE]
    field_comparisons = []
    score_comparisons = []
    for index, (record, arrays) in enumerate(zip(records, internal)):
        errors = {}
        frozen_residuals = {}
        for space in ("weight", "full"):
            rates = np.asarray(main[space]["raw_coefficients"])
            projected = field_product(arrays["matrix"][:, :len(rates)], rates, counts)
            difference_squared = integral(np, arrays["weights"],
                (projected - arrays[space + "_projection"]) ** 2, counts)
            errors[space] = math.sqrt(difference_squared / record["F_norm_squared"])
            checks["main_frozen_field_" + str(index) + "_" + space] = errors[space] <= 1.0e-8
            frozen_residual = integral(np, arrays["weights"], (arrays["F"] - projected) ** 2, counts)
            frozen_relative = frozen_residual / record["F_norm_squared"]
            frozen_error = abs(frozen_relative - main[space]["relative_residual_squared"])
            frozen_residuals[space] = {"direct_residual_squared": frozen_residual,
                "relative_residual_squared": frozen_relative,
                "absolute_relative_score_difference_from_main": frozen_error}
            checks["main_frozen_residual_" + str(index) + "_" + space] = frozen_error <= 1.0e-8
        field_comparisons.append({"route": record["name"], "relative_field_disagreements": errors,
                                  "main_frozen_coefficient_residuals": frozen_residuals})
        score_errors = {}
        for space in ("weight", "full"):
            for key in ("relative_residual_squared", "relative_capture_squared"):
                score_errors[space + "_" + key] = abs(record[space][key] - main[space][key])
        score_errors["saved_relative_residual_squared"] = abs(record["saved_update"]["relative_residual_squared"]
            - main["saved_update"]["relative_residual_squared"])
        score_errors["geometry_gap_over_F_norm_squared"] = abs(record["geometry_gap_over_F_norm_squared"]
            - main["geometry_gap_over_F_norm_squared"])
        if record["fraction_weight_residual_squared_removed"] is not None and main["fraction_weight_residual_squared_removed"] is not None:
            score_errors["fraction_weight_residual_squared_removed"] = abs(record["fraction_weight_residual_squared_removed"]
                - main["fraction_weight_residual_squared_removed"])
        else:
            checks["defined_weight_residual_fraction_" + str(index)] = False
        checks["scores_against_main_" + str(index)] = all(value <= 1.0e-8 for value in score_errors.values())
        score_comparisons.append({"route": record["name"], "absolute_dimensionless_score_differences": score_errors})
    heat_comparisons = []
    for low, high in ((0, 1), (2, 3)):
        errors = {}
        for name in ("q", "qr", "qz", "phi", "phi_r", "phi_z", "ur", "uz", "F"):
            errors[name] = dimensional(np, internal[low]["fields"][name], internal[high]["fields"][name])
        for index in range(4):
            errors["ordered_F_" + str(index)] = dimensional(np,
                internal[low]["fields"]["ordered_Fij"][index]["value"],
                internal[high]["fields"]["ordered_Fij"][index]["value"])
        checks["paired_heat_fields_" + str(low)] = all(item["pass"] for item in errors.values())
        charge(counts, "heat_field_comparison_values", len(errors) * internal[low]["F"].size)
        heat_comparisons.append({"routes": [records[low]["name"], records[high]["name"]], "comparisons": errors})
    norm_comparisons = []
    for left, right, kind in ((0, 1, "heat"), (2, 3, "heat"), (0, 2, "spatial"),
                              (1, 3, "spatial"), (3, 4, "domain")):
        items = {key: dimensional(np, records[left][key], records[right][key])
                 for key in ("F_norm_squared", "q_norm_squared")}
        checks[kind + "_raw_norms_" + str(left) + "_" + str(right)] = all(item["pass"] for item in items.values())
        norm_comparisons.append({"kind": kind, "routes": [records[left]["name"], records[right]["name"]], "comparisons": items})
    return {"main_frozen_fields": field_comparisons, "scores_against_main": score_comparisons,
            "paired_heat_fields": heat_comparisons, "paired_raw_norms": norm_comparisons}


def run(result):
    import numpy as np

    counts, checks = result["counters"], result["checks"]
    folder = Path(__file__).resolve().parent
    repository = folder.parents[3]
    input_path = folder / "input.json"
    physics_path = repository / "tracks/tog/tasks/t70-causal-projector-qualification/physics.py"
    input_before, input_body = identity(input_path, counts)
    packet = json.loads(input_body)
    physics_before, _ = identity(physics_path, counts)
    source_path = repository / packet["source"]["path"]
    source_before, source_body = identity(source_path, counts)
    checks["frozen_source_identity"] = source_before == {key: packet["source"][key] for key in ("bytes", "sha256")}
    if not checks["frozen_source_identity"]:
        raise ValueError("original T71 source does not match the frozen input identity")
    source = json.loads(source_body)
    old_path = source["paths"][packet["path_index"]]
    old_current = old_path["steps"][packet["current_step_index"]]
    old_next = old_path["steps"][packet["next_step_index"]]
    checks["exact_scalar_extraction"] = (old_path["h"] == packet["h"]
        and old_current["time"] == packet["time"] and old_next["time"] == packet["next_time"]
        and old_current["state"] == packet["state"] and old_next["state"] == packet["next_state"]
        and old_next["confirmation"] == packet["next_confirmation"])
    del source, source_body, old_path, old_current, old_next, input_body
    checks["unchanged_saved_geometry"] = packet["state"]["geometry"] == packet["next_state"]["geometry"]
    checks["fixed_selected_state"] = (packet["path_index"] == 1 and packet["current_step_index"] == 20
        and packet["next_step_index"] == 21 and packet["h"] == 0.03125
        and packet["time"] == 0.625 and packet["next_time"] == 0.65625)
    if not all(checks.values()):
        raise ValueError("frozen saved state/extraction contract failed")
    state, next_state = packet["state"], packet["next_state"]
    masses = [state["Gamma"] * (1.0 - state["eta"]), state["Gamma"] * state["eta"]]
    next_masses = [next_state["Gamma"] * (1.0 - next_state["eta"]), next_state["Gamma"] * next_state["eta"]]
    checks["positive_saved_component_masses"] = all(math.isfinite(value) and value > 0.0 for value in masses + next_masses)
    if not checks["positive_saved_component_masses"]:
        raise ValueError("nonpositive saved component mass")
    result["runtime"] = {"python": sys.version, "numpy": np.__version__,
        "thread_environment": {key: os.environ.get(key) for key in
            ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}}
    checks["frozen_runtime"] = sys.version_info[:3] == (3, 12, 14) and np.__version__ == "2.3.5"
    checks["single_thread_environment"] = all(value == "1" for value in result["runtime"]["thread_environment"].values())
    rules, result["quadrature_rules"] = construct_rules(np, counts, checks)
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("t75_frozen_t70_physics", physics_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    physics = module.Physics(np, rules, counts, None)
    gram, norms, primitives = analytic_gram(np, physics, state["geometry"], masses, counts)
    result["analytic"] = {"column_order": list(COLUMNS), "gram": gram.tolist(),
        "common_column_norms": norms.tolist(), "primitive_gram_values": primitives}
    result["input"] = {"state": state, "next_state": next_state, "masses": masses,
        "next_masses": next_masses, "time": packet["time"], "h": packet["h"],
        "source_identity": packet["source"]}
    internal = []
    for index, route in enumerate(ROUTES):
        record, arrays = evaluate_route(np, physics, rules, route, packet, masses, next_masses, gram, norms, counts)
        result["routes"].append(record)
        internal.append(arrays)
        for key, passed in record["checks"].items():
            checks["route_" + str(index) + "_" + key] = passed
        for space in ("weight", "full"):
            for key, passed in record[space]["checks"].items():
                checks["route_" + str(index) + "_" + space + "_" + key] = passed
    result["route_comparisons"] = compare_routes(np, result["routes"], internal, counts, checks)
    del internal
    expected = {"rule_eigh_calls": 5, "rule_nodes": 736,
        "phys_rule_transforms": 3, "phys_rule_nodes_transformed": 448,
        "phys_gram_calls": 3, "analytic_polynomial_gram_entries": 64,
        "analytic_polynomial_moment_products": 256,
        "tall_svd_calls": 10, "tall_svd_input_values": 716800,
        "tangent_column_values": 573440, "weighted_normalized_matrix_values": 573440,
        "direct_gram_entries": 320, "gram_frobenius_reductions": 10,
        "direct_reductions": 405, "direct_reduction_point_visits": 5806080,
        "field_matrix_vector_calls": 30, "field_matrix_vector_point_columns": 1720320,
        "heat_field_comparison_values": 346112, "phys_field_calls": 5,
        "phys_field_spatial_points": 71680, "phys_field_component_points": 143360,
        "phys_field_heat_integrand_points": 29884416, "phys_field_ordered_pair_points": 286720,
        "phys_field_heat_nodes": 2048, "phys_peak_spatial_points": 18432,
        "phys_cross_calls": 0, "phys_initial_exact_calls": 0,
        "normal_equation_column_reductions": 50, "normal_equation_point_columns": 716800}
    result["expected_counts"] = expected
    for key, value in expected.items():
        checks["count_" + key] = counts.get(key, 0) == value
    identities = {}
    for name, path, before in (("input", input_path, input_before), ("physics", physics_path, physics_before),
                               ("T71_source", source_path, source_before)):
        after, _ = identity(path, counts)
        identities[name] = {"path": str(path), "before": before, "after": after}
        checks["preserved_" + name] = before == after
    result["identities"] = identities
    result["main_route"] = result["routes"][MAIN_ROUTE]["name"]
    main = result["routes"][MAIN_ROUTE]
    result["main_outcomes"] = {"weight_relative_residual_squared": main["weight"]["relative_residual_squared"],
        "full_relative_residual_squared": main["full"]["relative_residual_squared"],
        "geometry_gap_over_F_norm_squared": main["geometry_gap_over_F_norm_squared"],
        "fraction_weight_residual_squared_removed": main["fraction_weight_residual_squared_removed"],
        "saved_relative_residual_squared": main["saved_update"]["relative_residual_squared"],
        "saved_weight_field_disagreement": main["saved_update"]["field_difference_from_optimal_weights_over_F_norm"]}
    result["all_checks_pass"] = all(checks.values())
    if not result["all_checks_pass"]:
        result["diagnostic_verdict"] = "unresolved_qualification_failure"
    elif main["geometry_gap_over_F_norm_squared"] > 1.0e-8:
        result["diagnostic_verdict"] = "qualified_local_geometric_capability_gap"
    else:
        result["diagnostic_verdict"] = "qualified_no_resolved_local_geometric_gap"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("refusing existing output: " + str(args.output))
    started = time.perf_counter()
    result = {"schema": "t75-saved-tangent-diagnostic-v1", "all_checks_pass": False,
        "diagnostic_verdict": "unresolved_execution_failure", "checks": {}, "counters": {}, "routes": [],
        "claims": {"ordinary_single_state_diagnostic": True, "formal_tail_certificate": False,
            "finite_step_improvement": False, "full_window_improvement": False, "new_method": False}}
    try:
        run(result)
    except Exception as exc:
        result["all_checks_pass"] = False
        result["diagnostic_verdict"] = "unresolved_execution_failure"
        result["error"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    result["elapsed_before_result_write_seconds"] = time.perf_counter() - started
    body = json.dumps(result, allow_nan=False, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(body)
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
