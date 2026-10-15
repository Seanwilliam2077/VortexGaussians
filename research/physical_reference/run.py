"""Fixed P5c fixtures and raw evidence runner. Formal runs require source pins."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import platform
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import core

HERE = Path(__file__).resolve().parent
CENTER = np.array([0.0, 0.8, 0.0], dtype=np.float64)
OFFSETS = np.array([[-.12, -.08, -.10], [.11, -.06, -.09], [-.10, .13, -.07],
                    [.14, .09, -.12], [-.13, -.11, .15], [.09, -.10, .11],
                    [-.08, .12, .14], [.12, .14, .10]], dtype=np.float64)
STATIC_IDS = ["measure-base", "measure-split2", "measure-split4", "measure-selective2",
              "measure-reverse", "measure-volume-half", "measure-volume-double", "kernel-analytic",
              "field-n8", "field-n16", "field-n32", "field-domain40"]
DYNAMIC_IDS = ["temperature-constant", "temperature-linear-samples", "buoyancy-source-units",
               "strain-dt010", "strain-dt005", "strain-dt0025", "mean-dt010", "mean-dt005", "mean-dt0025"]
SOURCE_FILES = ["core.py", "run.py", "test_core.py", "audit.py", "PROTOCOL.md"]


def plain(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value


def encoded(value):
    return json.dumps(plain(value), ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


def write_json(path, value):
    path.write_bytes(encoded(value) + b"\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes(require_all=True):
    result = {}
    for name in SOURCE_FILES:
        path = HERE / name
        if not path.is_file():
            if require_all:
                raise FileNotFoundError(path)
            continue
        result[name] = sha(path)
    return result


def base_sources():
    answer = []
    for i, offset in enumerate(OFFSETS):
        volume = .001 * (1.0 + .2 * i)
        omega = np.array([.5 + .125 * i, -.25 + .05 * i, .4 - .03 * i])
        answer.append({"id": f"s{i}", "anchorId": f"s{i}", "position": (CENTER + offset).tolist(),
                       "volume": volume, "Gamma": (volume * omega).tolist(), "sigma": .07 + .0025 * i,
                       "temperature": 300.0 + 10.0 * i, "capacityPerVolume": 3.0})
    return answer


def split_sources(sources, multiplicities):
    answer = []
    for i, source in enumerate(sources):
        m = multiplicities[i]
        for j in range(m):
            child = copy.deepcopy(source)
            child["id"] = f"{source['id']}/{j}" if m > 1 else source["id"]
            child["anchorId"] = source["anchorId"]
            child["volume"] = source["volume"] / m
            child["Gamma"] = (np.array(source["Gamma"]) / m).tolist()
            answer.append(child)
    return answer


def regular_queries(n=4, spacing=.1):
    return [{"id": f"q-{i}-{j}-{k}", "position": (CENTER + spacing * np.array([i-(n-1)/2, j-(n-1)/2, k-(n-1)/2])).tolist()}
            for i in range(n) for j in range(n) for k in range(n)]


def totals(p):
    return {"volume": math.fsum(float(v) for v in p["V"]),
            "Gamma": [math.fsum(float(v) for v in p["Gamma"][:, j]) for j in range(3)],
            "energy": core.energy(p)}


def sample_record(case_id, family, sources, queries, velocity_only=False, **extra):
    input_before = encoded(sources)
    p = core.make_parcels(sources)
    parcels_before = encoded(core.source_records(p))
    positions = [q["position"] for q in queries]
    velocity, jacobian = core.velocity_jacobian(p, positions, with_jacobian=not velocity_only)
    output = {"velocity": velocity.tolist()}
    if not velocity_only:
        output["jacobian"] = jacobian.tolist()
        output.update(core.thermal_samples(p, positions))
    if encoded(sources) != input_before or encoded(core.source_records(p)) != parcels_before:
        raise AssertionError("sampling mutated its input")
    return {"id": case_id, "family": family, "sources": sources, "queries": queries, "output": output,
            "totals": totals(p), "inputUnchanged": True,
            "counts": {"sources": len(sources), "queries": len(queries), "sourceQueryPairs": len(sources) * len(queries)}, **extra}


def measure_case(case_id):
    sources = base_sources()
    if case_id.endswith("split2"):
        sources = split_sources(sources, [2] * 8)
    elif case_id.endswith("split4"):
        sources = split_sources(sources, [4] * 8)
    elif case_id.endswith("selective2"):
        sources = split_sources(sources, [1 if i % 2 == 0 else 2 for i in range(8)])
    elif case_id.endswith("reverse"):
        sources.reverse()
    elif case_id.endswith("half") or case_id.endswith("double"):
        scale = .5 if case_id.endswith("half") else 2.0
        for source in sources:
            source["volume"] *= scale
            source["Gamma"] = (np.array(source["Gamma"]) * scale).tolist()
    return sample_record(case_id, "A", sources, regular_queries())


def kernel_case():
    sigma = .07
    source = {"id": "s0", "anchorId": "s0", "position": [0.0, 0.0, 0.0], "volume": .001,
              "Gamma": [0.0, 0.0, .001], "sigma": sigma, "temperature": 450.0, "capacityPerVolume": 3.0}
    q_values = [.01, .1, .25, math.nextafter(.5, 0.0), .5, math.nextafter(.5, math.inf), 1.0, 2.0, 4.0, 8.0]
    directions = [np.array([1., 0., 0.]), np.array([0., 0., 1.]), np.array([2., -1., 2.]) / 3.0]
    queries = [{"id": "q-origin", "position": [0.0, 0.0, 0.0], "requestedQ": 0.0, "actualQ": 0.0, "branch": "series"}]
    for i, q in enumerate(q_values):
        for j, direction in enumerate(directions):
            position = sigma * q * direction
            actual = float(np.hypot.reduce(position) / sigma)
            queries.append({"id": f"q-{i}-{j}", "position": position.tolist(), "direction": direction.tolist(),
                            "requestedQ": q, "actualQ": actual, "branch": "series" if actual < core.Q_SWITCH else "regular"})
    probes = []
    for i, q in enumerate([0., .25, math.nextafter(.5, 0.), .5, math.nextafter(.5, math.inf), 1.]):
        F, D, actual, small = core.gaussian_factors(q, 1.0)
        probes.append({"id": f"radial-{i}", "radius": q, "sigma": 1.0, "q": float(actual),
                       "F": float(F), "D": float(D), "branch": "series" if bool(small) else "regular"})
    c12 = 1.0 / (2.0 ** 12 * math.factorial(12) * 27.0)
    return sample_record("kernel-analytic", "B", [source], queries, radialProbes=probes,
                         constants={"qSwitch": core.Q_SWITCH, "seriesBranch": "q < qSwitch", "seriesTerms": core.SERIES_TERMS,
                                    "dimensionlessFTruncationBound": core.SQRT_2_PI * c12 * .5 ** 24,
                                    "dimensionlessDTruncationBound": core.SQRT_2_PI * 24.0 * c12 * .5 ** 22})


def field_case(case_id):
    n = 40 if case_id == "field-domain40" else int(case_id.removeprefix("field-n"))
    half_width = .625 if n == 40 else .5
    dx = 2.0 * half_width / n
    A, a, sigma = .01, .1, .06
    sources = []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                r = -half_width + (np.array([i, j, k], dtype=np.float64) + .5) * dx
                x, y, z = r
                prefactor = A * math.exp(-float(np.dot(r, r)) / (2.0 * a * a))
                omega = prefactor * np.array([x*z/a**4, y*z/a**4, 2.0/a**2 - (x*x+y*y)/a**4])
                source_id = f"s-{i}-{j}-{k}"
                sources.append({"id": source_id, "anchorId": source_id, "position": (CENTER+r).tolist(),
                                "volume": dx**3, "Gamma": (dx**3*omega).tolist(), "sigma": sigma,
                                "temperature": 300.0, "capacityPerVolume": 3.0})
    return sample_record(case_id, "C", sources, regular_queries(5, .05), velocity_only=True,
                         constants={"A": A, "a": a, "sigma": sigma, "center": CENTER.tolist(),
                                    "halfWidth": half_width, "n": n, "spacing": dx})


def temperature_case(case_id):
    sources = base_sources()
    for source in sources:
        offset = np.array(source["position"]) - CENTER
        source["temperature"] = 450.0 if case_id.endswith("constant") else 450.0 + float(np.dot([40., -25., 30.], offset))
    return sample_record(case_id, "D", sources, regular_queries())


def buoyancy_case():
    sources = base_sources()
    for source in sources:
        source["Gamma"] = [0.0, 0.0, 0.0]
        source["temperature"] = 450.0 + float(np.dot([40., -25., 30.], np.array(source["position"]) - CENTER))
    variants = [("base", sources), ("all-split2", split_sources(sources, [2]*8)),
                ("selective2", split_sources(sources, [1 if i % 2 == 0 else 2 for i in range(8)])),
                ("reverse", copy.deepcopy(list(reversed(sources))))]
    representations = []
    for variant, records in variants:
        before = encoded(records)
        p = core.make_parcels(records)
        u, J = core.velocity_jacobian(p, p["x"])
        gradient = np.broadcast_to([40., -25., 30.], p["x"].shape).copy()
        rhs = core.inviscid_rhs(p, J, gradient, .5, 100.)
        updated = core.euler_step(p, u, rhs, .01)
        if before != encoded(records) or before != encoded(core.source_records(p)):
            raise AssertionError("buoyancy update mutated input")
        representations.append({"id": variant, "sources": records, "gradient": gradient,
                                "velocity": u, "jacobian": J, "rhs": rhs, "updatedSources": core.source_records(updated),
                                "totalsBefore": totals(p), "totalsAfter": totals(updated), "inputUnchanged": True})
    return plain({"id": "buoyancy-source-units", "family": "D", "sources": sources, "representations": representations,
                  "constants": {"ambientTemperature": 300., "temperatureScale": 100., "buoyancy": .5,
                                "dt": .01, "prescribedGradient": [40., -25., 30.]}, "inputUnchanged": True})


def ode_case(case_id):
    mean = case_id.startswith("mean-")
    dt = {"010": .01, "005": .005, "0025": .0025}[case_id.split("dt")[1]]
    steps = round(.1 / dt)
    sources = [{"id": "s0", "anchorId": "s0", "position": [.03, -.04, .05], "volume": .001,
                "Gamma": [0., 0., 0. if mean else .001], "sigma": .07,
                "temperature": 350. if mean else 300., "capacityPerVolume": 3.}]
    p = core.make_parcels(sources)
    strain = np.diag([-.5, -.5, 1.])
    mean_velocity = np.zeros(3)
    states = []
    step_outputs = []
    for step in range(steps + 1):
        state = {"step": step, "time": step*dt, "sources": core.source_records(p), "totals": totals(p)}
        if mean:
            state["meanVelocity"] = mean_velocity.tolist()
        states.append(state)
        if step == steps:
            break
        old = encoded(core.source_records(p))
        if mean:
            updated, next_mean = core.mean_mode_euler(p, mean_velocity, [0., .25, 0.], dt)
            step_outputs.append({"step": step + 1, "velocity": [mean_velocity.tolist()], "rhs": [[0., 0., 0.]],
                                 "acceleration": [0., .25, 0.]})
            mean_velocity = next_mean
        else:
            updated, detail = core.prescribed_strain_euler(p, strain, dt)
            step_outputs.append({"step": step + 1, **plain(detail)})
        if old != encoded(core.source_records(p)):
            raise AssertionError("Euler update mutated old state")
        p = updated
    constants = {"horizon": .1}
    if mean:
        constants.update({"ambientTemperature": 300., "temperatureScale": 100., "buoyancy": .5, "acceleration": [0., .25, 0.]})
    else:
        constants["strain"] = strain.tolist()
    return {"id": case_id, "family": "F" if mean else "E", "sources": sources, "dt": dt, "steps": steps,
            "constants": constants, "states": states, "stepOutputs": step_outputs, "inputUnchanged": True}


def execute(case_id):
    if case_id.startswith("measure-"):
        return measure_case(case_id)
    if case_id == "kernel-analytic":
        return kernel_case()
    if case_id.startswith("field-"):
        return field_case(case_id)
    if case_id.startswith("temperature-"):
        return temperature_case(case_id)
    if case_id == "buoyancy-source-units":
        return buoyancy_case()
    return ode_case(case_id)


def run(args):
    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("output directory must be new or empty; evidence is never overwritten")
    out.mkdir(parents=True, exist_ok=True)
    hashes_before = source_hashes(require_all=not args.preflight)
    if args.formal:
        if args.preflight or not args.freeze:
            raise ValueError("formal requires --freeze and cannot be preflight")
        freeze = json.loads(Path(args.freeze).read_text(encoding="utf-8"))
        if freeze.get("sourceHashes", freeze) != hashes_before:
            raise ValueError("source freeze does not match current files")
    planned = ["measure-base", "kernel-analytic"] if args.preflight else STATIC_IDS + DYNAMIC_IDS
    manifest = {"phase": "P5c", "schemaVersion": 1, "formal": args.formal, "exploratory": not args.formal,
                "planned": planned, "sourceHashes": hashes_before, "status": "running", "protocolComplete": False,
                "environment": {"python": sys.version, "numpy": np.__version__, "platform": platform.platform(),
                                "processor": platform.processor(), "machine": platform.machine()},
                "argv": sys.argv, "cases": [], "interpretation": "Standard source-only physical reference operators; no speed, realism, or novelty claim."}
    raw = {"phase": "P5c", "schemaVersion": 1, "cases": []}
    write_json(out / "manifest.json", manifest)
    started = time.perf_counter()
    try:
        static_gate = None
        for case_id in planned:
            if case_id == DYNAMIC_IDS[0]:
                from audit import audit_cases
                static_gate = audit_cases(raw["cases"], static_only=True)
                write_json(out / "static-audit.json", static_gate)
                manifest["staticAudit"] = {"path": "static-audit.json", "sha256": sha(out / "static-audit.json"),
                                            **{k: static_gate.get(k) for k in ("executionValid", "physicalContractPassed", "referenceValid")}}
                if not all(static_gate.get(k) is True for k in ("executionValid", "physicalContractPassed", "referenceValid")):
                    manifest["status"] = "stopped_after_static" if static_gate.get("executionValid") and static_gate.get("referenceValid") else "invalid_static_reference_or_execution"
                    manifest["stopReason"] = "Independent static audit did not pass; the nine D-F cases were not executed."
                    break
            print(f"P5c {len(raw['cases']) + 1}/{len(planned)} {case_id}", flush=True)
            result = execute(case_id)
            raw["cases"].append(result)
            write_json(out / "cases.json", raw)
            manifest["cases"].append({"id": case_id, "family": result["family"], "recordSha256": hashlib.sha256(encoded(result)).hexdigest()})
            manifest["raw"] = {"path": "cases.json", "sha256": sha(out / "cases.json"), "bytes": (out / "cases.json").stat().st_size}
            write_json(out / "manifest.json", manifest)
        if manifest["status"] == "running":
            if args.preflight:
                manifest["status"] = "preflight_completed"
            else:
                from audit import audit_cases
                final_audit = audit_cases(raw["cases"], static_only=False)
                write_json(out / "audit.json", final_audit)
                manifest["audit"] = {"path": "audit.json", "sha256": sha(out / "audit.json"),
                                     **{k: final_audit.get(k) for k in ("executionValid", "physicalContractPassed", "referenceValid")}}
                manifest["protocolComplete"] = [c["id"] for c in raw["cases"]] == STATIC_IDS + DYNAMIC_IDS
                if not final_audit.get("executionValid") or not final_audit.get("referenceValid"):
                    manifest["status"] = "invalid_reference_or_execution"
                else:
                    manifest["status"] = "passed" if final_audit.get("physicalContractPassed") is True else "contract_failed"
    except Exception as exc:
        manifest["status"] = "execution_failed"
        manifest["error"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    finally:
        manifest["sourceHashesAfter"] = source_hashes(require_all=not args.preflight)
        manifest["sourcesUnchanged"] = manifest["sourceHashesAfter"] == hashes_before
        if not manifest["sourcesUnchanged"]:
            manifest["status"] = "source_changed"
        manifest["elapsedWallSeconds"] = time.perf_counter() - started
        manifest["wallTimeInterpretation"] = "Bookkeeping only; includes JSON I/O and independent audits, not a performance benchmark."
        write_json(out / "manifest.json", manifest)
    print(json.dumps({"status": manifest["status"], "cases": len(raw["cases"]), "out": str(out),
                      "sourcesUnchanged": manifest["sourcesUnchanged"]}), flush=True)
    return 0 if manifest["status"] in ("passed", "preflight_completed", "stopped_after_static", "contract_failed") and manifest["sourcesUnchanged"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--preflight", action="store_true", help="Two static wiring cases only; never formal evidence.")
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--freeze", help="JSON source hash mapping or {sourceHashes:mapping} required by --formal.")
    raise SystemExit(run(parser.parse_args()))
