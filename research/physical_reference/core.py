"""P5c: small Float64 direct-sum reference operators, not a full flow solver.

Gamma = volume * vorticity (m^3/s); sigma is each source's per-axis SD.
The vector Gaussian representation need not itself be divergence-free. The
Biot--Savart velocity is its solenoidal reconstruction, not an exact NS solution.
Input order is preserved. NumPy's Float64 reductions are used, without a tree.
"""
from __future__ import annotations

import math
import numpy as np

Q_SWITCH = 0.5
SERIES_TERMS = 12
SQRT_2_PI = math.sqrt(2.0 / math.pi)
FOUR_PI = 4.0 * math.pi
F_COEFFICIENTS = tuple((-1.0) ** k / (2.0 ** k * math.factorial(k) * (2 * k + 3))
                       for k in range(SERIES_TERMS))
D_COEFFICIENTS = tuple(2 * k * F_COEFFICIENTS[k] for k in range(1, SERIES_TERMS))


def _finite(value, shape=None, name="array"):
    result = np.array(value, dtype=np.float64, copy=True)
    if shape is not None and result.shape != shape:
        raise ValueError(f"{name}: shape {result.shape}, expected {shape}")
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name}: nonfinite value")
    return result


def _scalar(value, name, positive=False, nonnegative=False):
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0) or (nonnegative and result < 0):
        raise ValueError(f"{name}: invalid finite scalar")
    return result


def _vectors(value, name, count=None):
    result = _finite(value, name=name)
    if result.shape == (0,):
        result = result.reshape(0, 3)
    if result.ndim != 2 or result.shape[1] != 3 or (count is not None and len(result) != count):
        raise ValueError(f"{name}: expected an explicit N by 3 array")
    return result


def make_parcels(sources):
    """Copy explicit source records into validated Float64 arrays; allow empty."""
    ids = [str(s["id"]) for s in sources]
    if any(not s for s in ids) or len(set(ids)) != len(ids):
        raise ValueError("source IDs must be unique and nonempty")
    n = len(sources)
    p = {"ids": ids, "anchorIds": [str(s.get("anchorId", s["id"])) for s in sources],
         "x": _vectors([s["position"] for s in sources], "x", n),
         "Gamma": _vectors([s["Gamma"] for s in sources], "Gamma", n)}
    for key, field in (("V", "volume"), ("T", "temperature"),
                       ("cV", "capacityPerVolume"), ("sigma", "sigma")):
        p[key] = _finite([s[field] for s in sources], (n,), key)
    validate_parcels(p)
    return p


def validate_parcels(p):
    n = len(p["ids"])
    if len(set(p["ids"])) != n or any(not isinstance(i, str) or not i for i in p["ids"]):
        raise ValueError("invalid source IDs")
    if len(p["anchorIds"]) != n or any(not isinstance(i, str) or not i for i in p["anchorIds"]):
        raise ValueError("invalid anchor IDs")
    for key in ("x", "Gamma"):
        if p[key].shape != (n, 3) or p[key].dtype != np.float64 or not np.all(np.isfinite(p[key])):
            raise ValueError(f"invalid {key}")
    for key in ("V", "T", "cV", "sigma"):
        if p[key].shape != (n,) or p[key].dtype != np.float64 or not np.all(np.isfinite(p[key])):
            raise ValueError(f"invalid {key}")
        invalid_sign = np.any(p[key] < 0) if key == "T" else np.any(p[key] <= 0)
        if invalid_sign:
            raise ValueError(f"invalid positive/nonnegative {key}")
    return n


def source_records(p):
    validate_parcels(p)
    return [{"id": p["ids"][i], "anchorId": p["anchorIds"][i],
             "position": p["x"][i].tolist(), "volume": float(p["V"][i]),
             "Gamma": p["Gamma"][i].tolist(), "sigma": float(p["sigma"][i]),
             "temperature": float(p["T"][i]), "capacityPerVolume": float(p["cV"][i])}
            for i in range(len(p["ids"]))]


def _horner(coefficients, z):
    answer = np.zeros_like(z) + coefficients[-1]
    for coefficient in reversed(coefficients[:-1]):
        answer = answer * z + coefficient
    return answer


def gaussian_factors(radius, sigma):
    """Return F=g/R^3 and D=F'(R)/R, including their finite R=0 limits.

    The alternating series at q<=.5 has first omitted dimensionless terms
    <= |c12|*.5^24 for F and 24*|c12|*.5^22 for D. Terms decrease;
    these bound truncation, not Float64 evaluation rounding. The D limit is
    -sqrt(2/pi)/(5 sigma^5); it multiplies a zero outer product at R=0.
    """
    radius, sigma = np.broadcast_arrays(_finite(radius, name="radius"), _finite(sigma, name="sigma"))
    if np.any(radius < 0) or np.any(sigma <= 0):
        raise ValueError("radius>=0 and sigma>0 required")
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        q = radius / sigma
        small = q < Q_SWITCH
        F = np.empty_like(q)
        D = np.empty_like(q)
        z = q[small] ** 2
        F[small] = SQRT_2_PI * _horner(F_COEFFICIENTS, z) / sigma[small] ** 3
        D[small] = SQRT_2_PI * _horner(D_COEFFICIENTS, z) / sigma[small] ** 5
        qlarge = q[~small]
        # For q>40 the exponential contribution is below Float64 range.
        exp_part = np.zeros_like(qlarge)
        moderate = qlarge <= 40.0
        exp_part[moderate] = np.exp(-0.5 * qlarge[moderate] ** 2)
        erf_part = np.fromiter((math.erf(float(v) / math.sqrt(2.0)) for v in qlarge),
                               dtype=np.float64, count=len(qlarge))
        correction = np.zeros_like(qlarge)
        correction[moderate] = SQRT_2_PI * qlarge[moderate] * exp_part[moderate]
        g = erf_part - correction
        qgp = np.zeros_like(qlarge)
        qgp[moderate] = SQRT_2_PI * qlarge[moderate] ** 3 * exp_part[moderate]
        inv_r = 1.0 / radius[~small]
        F[~small] = g * inv_r ** 3
        D[~small] = (qgp - 3.0 * g) * inv_r ** 5
    if not np.all(np.isfinite(F)) or not np.all(np.isfinite(D)):
        raise FloatingPointError("Gaussian factors not representable in Float64")
    return F, D, q, small


def _cross_matrix(v):
    x, y, z = v
    return np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]], dtype=np.float64)


def velocity_jacobian(p, queries, with_jacobian=True):
    """Source-only Gaussian Biot--Savart; J[a,b]=d u_a / d x_b."""
    validate_parcels(p)
    queries = _vectors(queries, "queries")
    velocity = np.zeros((len(queries), 3), dtype=np.float64)
    jacobian = np.zeros((len(queries), 3, 3), dtype=np.float64) if with_jacobian else None
    for i, x in enumerate(queries):
        r = x - p["x"]
        radius = np.hypot.reduce(r, axis=1)
        F, D, _, _ = gaussian_factors(radius, p["sigma"])
        cross = np.cross(p["Gamma"], r)
        velocity[i] = np.sum(F[:, None] * cross, axis=0) / FOUR_PI
        if with_jacobian:
            first = _cross_matrix(np.sum(F[:, None] * p["Gamma"], axis=0))
            second = np.einsum("n,ni,nj->ij", D, cross, r, optimize=False)
            jacobian[i] = (first + second) / FOUR_PI
    if not np.all(np.isfinite(velocity)) or (with_jacobian and not np.all(np.isfinite(jacobian))):
        raise FloatingPointError("nonfinite field")
    return velocity, jacobian


def thermal_samples(p, queries):
    """Volume-weighted Shepard T/quotient gradient using log-rescaled weights.

    Empty sources are unsupported (None), never implicit ambient. A physical
    D that underflows to zero may still have a finite normalized reconstruction;
    logD and an explicit underflow flag distinguish these cases. T is centered
    on the largest-weight source to preserve constant fields and avoid losing a
    small dominant temperature by subtracting a huge negligible source's T.
    """
    n = validate_parcels(p)
    queries = _vectors(queries, "queries")
    result = {k: [] for k in ("temperature", "gradient", "numerator", "denominator",
                              "logDenominator", "supported", "denominatorUnderflow", "numeratorUnderflow")}
    for x in queries:
        if not n:
            for key in result:
                result[key].append(False if key in ("supported", "denominatorUnderflow", "numeratorUnderflow") else None)
            continue
        r = x - p["x"]
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            q2 = np.sum((r / p["sigma"][:, None]) ** 2, axis=1)
            logw = np.log(p["V"]) - 3.0 * np.log(p["sigma"]) - 1.5 * math.log(2.0 * math.pi) - 0.5 * q2
            scale = float(np.max(logw))
            rescaled = np.exp(logw - scale)
            normalization = float(np.sum(rescaled))
            if not math.isfinite(scale) or not math.isfinite(normalization) or normalization <= 0:
                raise FloatingPointError("thermal weights cannot be normalized")
            weights = rescaled / normalization
            pivot_temperature = p["T"][int(np.argmax(logw))]
            centered = p["T"] - pivot_temperature
            mean_centered = float(np.dot(weights, centered))
            temperature = float(pivot_temperature + mean_centered)
            score = -r / p["sigma"][:, None] ** 2
            gradient = np.sum((weights * (centered - mean_centered))[:, None] * score, axis=0)
            logd = scale + math.log(normalization)
            denominator = math.exp(logd)  # Overflow is an explicit error, never a fabricated value.
            # D may underflow while N remains representable for a large finite T.
            numerator = 0.0 if temperature == 0.0 else math.exp(logd + math.log(temperature))
        if not all(math.isfinite(v) for v in (temperature, logd, denominator, numerator)) or not np.all(np.isfinite(gradient)):
            raise FloatingPointError("nonfinite thermal output")
        values = {"temperature": temperature, "gradient": gradient.tolist(), "numerator": numerator,
                  "denominator": denominator, "logDenominator": logd, "supported": True,
                  "denominatorUnderflow": denominator == 0.0,
                  "numeratorUnderflow": numerator == 0.0 and temperature > 0.0}
        for key, value in values.items():
            result[key].append(value)
    return result


def energy(p):
    validate_parcels(p)
    result = math.fsum(float(v * c * t) for v, c, t in zip(p["V"], p["cV"], p["T"]))
    if not math.isfinite(result):
        raise FloatingPointError("nonfinite parcel energy")
    return result


def inviscid_rhs(p, jacobian, gradient, buoyancy, temperature_scale):
    n = validate_parcels(p)
    jacobian = _finite(jacobian, (n, 3, 3), "jacobian")
    gradient = _finite(gradient, (n, 3), "gradient")
    b = _scalar(buoyancy, "buoyancy")
    delta_t = _scalar(temperature_scale, "temperature_scale", positive=True)
    curl_force = np.column_stack((-gradient[:, 2], np.zeros(n), gradient[:, 0])) * (b / delta_t)
    result = np.einsum("nij,nj->ni", jacobian, p["Gamma"], optimize=False) + p["V"][:, None] * curl_force
    if not np.all(np.isfinite(result)):
        raise FloatingPointError("nonfinite strength RHS")
    return result


def euler_step(p, velocity, gamma_rhs, dt):
    """Synchronous update: both RHS arrays belong to the complete old state."""
    n = validate_parcels(p)
    dt = _scalar(dt, "dt", nonnegative=True)
    velocity = _finite(velocity, (n, 3), "velocity")
    gamma_rhs = _finite(gamma_rhs, (n, 3), "gamma_rhs")
    updated = make_parcels(source_records(p))
    updated["x"] = p["x"] + dt * velocity
    updated["Gamma"] = p["Gamma"] + dt * gamma_rhs
    validate_parcels(updated)
    return updated


def prescribed_strain_euler(p, strain, dt):
    """One prescribed linear-flow Euler step, including the self kernel."""
    n = validate_parcels(p)
    strain = _finite(strain, (3, 3), "strain")
    u_self, j_self = velocity_jacobian(p, p["x"])
    velocity = u_self + p["x"] @ strain.T
    jacobian = j_self + strain[None, :, :]
    rhs = inviscid_rhs(p, jacobian, np.zeros((n, 3)), 0.0, 1.0)
    return euler_step(p, velocity, rhs, dt), {"velocity": velocity, "jacobian": jacobian, "rhs": rhs}


def mean_mode_euler(p, mean_velocity, acceleration, dt):
    """Separate uniform zero-mode ODE, not a periodic Biot--Savart solver."""
    n = validate_parcels(p)
    mean_velocity = _finite(mean_velocity, (3,), "mean_velocity")
    acceleration = _finite(acceleration, (3,), "acceleration")
    dt = _scalar(dt, "dt", nonnegative=True)
    updated = euler_step(p, np.broadcast_to(mean_velocity, (n, 3)), np.zeros((n, 3)), dt)
    with np.errstate(over="raise", invalid="raise"):
        next_mean = mean_velocity + dt * acceleration
    if not np.all(np.isfinite(next_mean)):
        raise FloatingPointError("nonfinite mean velocity")
    return updated, next_mean
