"""Independent, read-only T42 saved-data audit; never runs the demo or a solver.

Only this script's JSON report is written, exclusively (no overwrite). Program
state hashes are opaque equality witnesses, not independently reconstructed gas
arrays. PNG decoding establishes dimensions/nonblack pixels, not visual merit.
"""
import argparse
import binascii
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
import time
import zlib


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUTER = ROOT.parent.parent
LABELS = ("00-initial", "01-after-A", "02-before-B", "03-after-B",
          "04-endpoint", "05-reset")
FRAMES = (0, 0, 180, 180, 360, 0)
COUNT = 34687
POINT_KEYS = {"id", "group", "position", "fuelInitial", "fuel", "heat",
              "char", "glow", "state", "areaWeight"}
PARTICLE_KEYS = {"count", "hotCount", "coldCount", "smokeCount", "temperatureSum",
                 "dynamicTemperatureSum", "densitySum", "circulationSum",
                 "absCirculationSum", "smokeProxySum", "layerCounts"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def finite(x):
    return type(x) in (int, float) and math.isfinite(x)


def strict_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON key: " + key)
        out[key] = value
    return out


def json_load(data):
    def bad_constant(value):
        raise ValueError("non-finite JSON constant: " + value)
    return json.loads(data, object_pairs_hook=strict_object,
                      parse_constant=bad_constant)


class Audit:
    def __init__(self):
        self.checks = 0
        self.errors = []

    def check(self, code, ok, **detail):
        self.checks += 1
        if not ok:
            self.errors.append({"check": code, **detail})
        return bool(ok)

    def exception(self, code, exc):
        self.check(code, False, error=type(exc).__name__ + ": " + str(exc))


def identity(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": digest(raw)}


def safe_name(value):
    return (isinstance(value, str) and value not in ("", ".", "..")
            and Path(value).name == value and "/" not in value and "\\" not in value)


def verify_manifest(audit, directory, entries, prefix):
    found = {}
    if not audit.check(prefix + ".list", isinstance(entries, list)):
        return found
    for n, item in enumerate(entries):
        try:
            name = item["name"]
            if not audit.check(prefix + ".safe_unique_name", safe_name(name) and name not in found,
                               entry=n, name=name):
                continue
            found[name] = item
            got = identity(directory / name)
            audit.check(prefix + ".identity", got["bytes"] == item["bytes"] and got["sha256"] == item["sha256"],
                        name=name, expected=item, actual=got)
        except Exception as exc:
            audit.exception(prefix + ".entry_" + str(n), exc)
    return found


def png_info(data):
    """Decode ordinary canvas RGB/RGBA PNGs with stdlib, checking every CRC."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("PNG signature")
    pos, chunks, compressed, header, ended = 8, [], bytearray(), None, False
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError("truncated chunk")
        size = struct.unpack_from(">I", data, pos)[0]
        kind = data[pos + 4:pos + 8]
        end = pos + 12 + size
        if end > len(data):
            raise ValueError("truncated payload")
        value = data[pos + 8:pos + 8 + size]
        stored = struct.unpack_from(">I", data, pos + 8 + size)[0]
        if binascii.crc32(kind + value) & 0xffffffff != stored:
            raise ValueError("PNG CRC: " + repr(kind))
        chunks.append(kind.decode("ascii"))
        if kind == b"IHDR":
            if header is not None or len(chunks) != 1 or size != 13:
                raise ValueError("invalid IHDR")
            header = struct.unpack(">IIBBBBB", value)
        elif kind == b"IDAT":
            compressed.extend(value)
        elif kind == b"IEND":
            if size != 0 or end != len(data):
                raise ValueError("invalid/trailing IEND")
            ended = True
            break
        pos = end
    if not header or not ended:
        raise ValueError("missing PNG header/end")
    w, h, depth, color, compression, filtering, interlace = header
    if not (0 < w <= 4096 and 0 < h <= 4096 and depth == 8 and color in (2, 6)
            and compression == filtering == interlace == 0):
        raise ValueError("unsupported canvas PNG format: " + repr(header))
    channels = 3 if color == 2 else 4
    stride = w * channels
    raw = zlib.decompress(compressed)
    if len(raw) != h * (stride + 1):
        raise ValueError("PNG decoded length")
    prev = bytearray(stride)
    nonblack = visible_nonblack = nonopaque = 0
    for y in range(h):
        off = y * (stride + 1)
        method = raw[off]
        if method not in range(5):
            raise ValueError("PNG filter")
        row = bytearray(raw[off + 1:off + 1 + stride])
        for x in range(stride):
            left = row[x - channels] if x >= channels else 0
            above = prev[x]
            corner = prev[x - channels] if x >= channels else 0
            if method == 1:
                add = left
            elif method == 2:
                add = above
            elif method == 3:
                add = (left + above) // 2
            elif method == 4:
                p = left + above - corner
                distances = (abs(p - left), abs(p - above), abs(p - corner))
                add = (left if distances[0] <= distances[1] and distances[0] <= distances[2]
                       else above if distances[1] <= distances[2] else corner)
            else:
                add = 0
            row[x] = (row[x] + add) & 255
        for x in range(0, stride, channels):
            lit = any(row[x:x + 3])
            alpha = row[x + 3] if channels == 4 else 255
            nonblack += int(lit)
            visible_nonblack += int(lit and alpha > 0)
            nonopaque += int(alpha != 255)
        prev = row
    return {"width": w, "height": h, "bit_depth": depth, "color_type": color,
            "chunks": chunks, "rgb_nonblack_pixels": nonblack,
            "visible_nonblack_pixels": visible_nonblack, "nonopaque_pixels": nonopaque,
            "all_rgb_black": nonblack == 0, "visual_identifiability_assessed": False}


def vector(value, n):
    return isinstance(value, list) and len(value) == n and all(finite(x) for x in value)


def close_vector(a, b, tol):
    return vector(a, len(b)) and max((abs(x - y) for x, y in zip(a, b)), default=0) <= tol


def expected_camera(cfg):
    # This recipe fixes unit scale and zero rotations, so no transform fitting,
    # scene projection, ray construction, or general trigonometric model is used.
    p, c = cfg["params"], cfg["camera"]
    if any(p[k] != v for k, v in {"sceneScale": 1, "sceneYaw": 0, "scenePitch": 0,
                                   "sceneOffX": 0, "sceneOffZ": 0}.items()):
        raise ValueError("auditor only covers this frozen unit/zero-rotation placement")
    eye = [c["position"][i] - cfg["source_center"][i] + (p["sceneLift"] if i == 1 else 0)
           for i in range(3)]
    rows = [[(1 if i == 0 else -1) * c["rotation"][j][i] for j in range(3)] for i in range(3)]
    view = [rows[r][col] if r < 3 else 0 for col in range(3) for r in range(4)]
    view += [-sum(rows[i][j] * eye[j] for j in range(3)) for i in range(3)] + [1]
    near, far = .05, 50
    nf = 1 / (near - far)
    projection = [2 * c["fx"] / c["width"], 0, 0, 0, 0, 2 * c["fy"] / c["height"], 0, 0,
                  0, 0, (far + near) * nf, -1, 0, 0, 2 * far * near * nf, 0]
    vp = [sum(projection[k * 4 + r] * view[col * 4 + k] for k in range(4))
          for col in range(4) for r in range(4)]
    return {"eye": eye, "V": view, "VP": vp, "bx": rows[0], "by": rows[1],
            "fh": [-x for x in rows[2]],
            "focal": [c["fx"] * cfg["width"] / c["width"], c["fy"] * cfg["height"] / c["height"]]}


def check_state(audit, label, state, frame, cfg, camera, initial):
    audit.check(label + ".version", state.get("version") == 3)
    audit.check(label + ".frame_time", state.get("frame") == frame and finite(state.get("time"))
                and abs(state["time"] - frame / 60) <= 1e-10,
                frame=state.get("frame"), time=state.get("time"))
    audit.check(label + ".seed", state.get("seed") == cfg["seed"], actual=state.get("seed"))
    audit.check(label + ".params", state.get("params") == cfg["params"])
    audit.check(label + ".buffer", state.get("buffer") == [cfg["width"], cfg["height"]])
    audit.check(label + ".gl", state.get("glError") == 0 and state.get("contextLost") is False)
    audit.check(label + ".scene_center", close_vector(state.get("sceneInfo", {}).get("center"), cfg["source_center"], 1e-12))
    actual_cam = state.get("camera", {})
    for key, expected in camera.items():
        audit.check(label + ".camera_" + key, close_vector(actual_cam.get(key), expected, 1e-5 if key in ("V", "VP") else 1e-10),
                    expected=expected, actual=actual_cam.get(key))
    rows = state.get("points")
    if not audit.check(label + ".points_array", isinstance(rows, list)):
        return None
    ids = [p.get("id") if isinstance(p, dict) else None for p in rows]
    expected_ids = sorted("ply:" + str(i) for i in range(COUNT))
    audit.check(label + ".all_ids_and_lexical_order", ids == expected_ids, count=len(rows))
    indexed = {}
    for row_no, point in enumerate(rows):
        try:
            pid = point["id"]
            index = int(pid.split(":")[1])
            ok = (set(point) == POINT_KEYS and pid == "ply:" + str(index) and 0 <= index < COUNT
                  and index not in indexed and point["group"] == "ply" and point["areaWeight"] is None
                  and point["fuelInitial"] == 1 and vector(point["position"], 3)
                  and all(finite(point[k]) for k in ("fuel", "heat", "char", "glow"))
                  and all(-1e-6 <= point[k] <= 1 + 1e-6 for k in ("fuel", "char", "glow"))
                  and point["heat"] >= -1e-6 and type(point["state"]) is int and point["state"] in (0, 1, 2))
            audit.check(label + ".point_contract", ok, row=row_no, id=pid)
            if ok:
                indexed[index] = point
                if initial is not None and index in initial:
                    audit.check(label + ".fixed_position", point["position"] == initial[index]["position"], id=pid)
        except Exception as exc:
            audit.exception(label + ".point_" + str(row_no), exc)
    if len(indexed) != COUNT:
        return None
    frontier = state.get("frontier")
    valid_frontier = (isinstance(frontier, list) and all(type(x) is int and x in indexed for x in frontier)
                      and len(frontier) == len(set(frontier)))
    audit.check(label + ".frontier_unique_indices", valid_frontier)
    if valid_frontier:
        audit.check(label + ".frontier_equals_burning", set(frontier) == {i for i, p in indexed.items() if p["state"] == 1})
    fuel = 0.0
    for i in range(COUNT):
        fuel += indexed[i]["fuel"]
    expected_counts = {"count": COUNT, "burning": sum(p["state"] == 1 for p in indexed.values()),
                       "charred": sum(p["state"] == 2 for p in indexed.values()),
                       "heated": sum(p["heat"] > .05 for p in indexed.values()),
                       "frontier": len(frontier) if valid_frontier else None}
    scene = state.get("scene", {})
    for key, value in expected_counts.items():
        audit.check(label + ".scene_" + key, scene.get(key) == value, expected=value, actual=scene.get(key))
    audit.check(label + ".fuel_sum_original_index_order", finite(scene.get("fuelRemaining"))
                and abs(scene["fuelRemaining"] - fuel) <= 1e-8, expected=fuel, actual=scene.get("fuelRemaining"))
    for key in ("representedArea", "areaWeightedFuelRemaining", "areaWeightedHeat", "areaWeightedChar"):
        audit.check(label + ".legacy_" + key, key in scene and scene[key] is None)
    particles = state.get("particles", {})
    if audit.check(label + ".particle_aggregate_object", isinstance(particles, dict)):
        audit.check(label + ".particle_aggregate_keys", set(particles) == PARTICLE_KEYS)
        for key, value in particles.items():
            audit.check(label + ".particle_finite_" + key,
                        (isinstance(value, list) and all(finite(x) for x in value)) if key == "layerCounts" else finite(value))
        counts = particles.get("layerCounts")
        audit.check(label + ".layer_count_sum", isinstance(counts, list) and len(counts) == cfg["params"]["simLayers"]
                    and all(type(x) is int and 0 <= x <= cfg["params"]["ppl"] for x in counts)
                    and sum(counts) == particles.get("count"))
    for key in ("hash", "particleStateHash"):
        audit.check(label + ".opaque_" + key + "_present", key in state and isinstance(state[key], (str, int)))
    return indexed


def check_event(audit, name, before, after, old, new, pick, event):
    center, radius = pick["world"], pick["radius"]
    distances = {i: sum((p["position"][k] - center[k]) ** 2 for k in range(3)) for i, p in old.items()}
    neighbors = {i for i, d2 in distances.items() if d2 <= radius * radius}
    eligible = {i for i in neighbors if old[i]["state"] == 0 and old[i]["fuel"] > 0}
    audit.check(name + ".geometric_neighbors", neighbors == set(pick["initial_geometric_neighbors"]))
    audit.check(name + ".center_identity", old[pick["index"]]["position"] == pick["world"])
    changed = set()
    for i in range(COUNT):
        audit.check(name + ".nonstate_material_unchanged", all(old[i][k] == new[i][k] for k in POINT_KEYS - {"state"}), id=old[i]["id"])
        expected = 1 if i in eligible else old[i]["state"]
        audit.check(name + ".eligible_state_transition", new[i]["state"] == expected, id=old[i]["id"], expected=expected, actual=new[i]["state"])
        if old[i]["state"] != new[i]["state"]:
            changed.add(i)
    prior, current = before["frontier"], after["frontier"]
    tail = current[len(prior):]
    audit.check(name + ".frontier_prefix_and_append", current[:len(prior)] == prior
                and len(tail) == len(eligible) and set(tail) == eligible)
    audit.check(name + ".event_return", isinstance(event, dict) and event.get("name") == name
                and event.get("lit") == len(eligible) and event.get("frame") == before["frame"]
                and event.get("time") == before["time"], event=event, expected_lit=len(eligible))
    for key in ("frame", "time", "seed", "randomDraws", "params", "camera", "buffer", "sceneInfo",
                "emitCursor", "particleStateHash", "particles", "counters", "countersByGroup", "areaFeed"):
        audit.check(name + ".zero_time_" + key, key in before and key in after and before[key] == after[key])
    return {"geometric_count": len(neighbors), "eligible_count": len(eligible), "changed_count": len(changed),
            "new_indices": sorted(eligible), "minimum_squared_boundary_distance": min(abs(d - radius * radius) for d in distances.values()),
            "gas_check": "all saved aggregates and opaque program particleStateHash; no complete gas arrays exported"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=OUTER / "outputs/t42-firewoods-sequential-workflow/run-01")
    parser.add_argument("--report", type=Path, default=HERE / "result-audit.json")
    args = parser.parse_args()
    begin = time.perf_counter()
    audit = Audit()
    report = {"schema": "t42-independent-saved-data-audit-v1", "run_directory": str(args.run.resolve()),
              "status": "partial_fail", "input_identities": {}, "checkpoints": {}, "events": {},
              "simulation_browser_or_solver_calls": 0, "visual_identifiability_assessed": False,
              "workflow_served": None, "scientific_contribution_established": False,
              "limits": ["Opaque program hashes are not independent full gas-state reconstruction.",
                         "PNG dimensions/nonblack statistics are not visual task qualification.",
                         "Saved-data consistency establishes neither physical combustion nor TOG contribution."],
              "tolerances": {"frame_time": 1e-10, "fuel_char_glow_bounds": 1e-6,
                             "camera_V_VP": 1e-5, "camera_other_vectors": 1e-10, "fuel_sum": 1e-8}}
    result = {}
    states, points = {}, {}
    try:
        cfg = json_load((HERE / "recipe.json").read_bytes())
        for name in ("PROTOCOL.md", "recipe.json", "capture.mjs", "adapter.js", "supervise.py", "freeze.json", "audit_saved.py"):
            path = HERE / name
            if audit.check("input_exists." + name, path.is_file()):
                report["input_identities"][name] = identity(path)
        camera = expected_camera(cfg)
        result_path = args.run / "result.json"
        audit.check("terminal_result_exists", result_path.is_file())
        if result_path.is_file():
            result = json_load(result_path.read_bytes())
            report["input_identities"]["run/result.json"] = identity(result_path)
        elif (args.run / "progress.json").is_file():
            result = json_load((args.run / "progress.json").read_bytes())
            report["used_partial_progress"] = True
        supervisor_path = args.run / "supervisor.json"
        audit.check("terminal_supervisor_exists", supervisor_path.is_file())
        if supervisor_path.is_file():
            sup = json_load(supervisor_path.read_bytes())
            report["input_identities"]["run/supervisor.json"] = identity(supervisor_path)
            verify_manifest(audit, args.run, sup.get("files"), "supervisor_files")
            audit.check("supervisor_manifest_complete", {p.name for p in args.run.iterdir() if p.is_file()}
                        == {f["name"] for f in sup.get("files", [])} | {"supervisor.json"})
            report["supervisor"] = {k: v for k, v in sup.items() if k != "files"}
            audit.check("supervisor_success", sup.get("exit_code") == 0 and sup.get("status") == "worker_terminal"
                        and sup.get("worker_still_live") is False and sup.get("worker_poll_exit_code") == 0)
            inventory_s = sup.get("file_inventory_hash_seconds")
            receipt_before_s = sup.get("elapsed_before_receipt_write_seconds")
            supervisor_s = sup.get("supervisor_seconds")
            audit.check("supervisor_inventory_cost_scope", all(finite(x) and x >= 0 for x in (inventory_s, receipt_before_s, supervisor_s))
                        and receipt_before_s >= supervisor_s + inventory_s - 1e-6,
                        supervisor_seconds=supervisor_s, file_inventory_hash_seconds=inventory_s,
                        elapsed_before_receipt_write_seconds=receipt_before_s)
        entries = verify_manifest(audit, args.run, result.get("files", []), "worker_files")
        audit.check("capture_complete", result.get("status") == "completed_capture_pending_saved_audit"
                    and result.get("completed_checkpoints") == 6, actual_status=result.get("status"))
        render_checks = result.get("render_checks")
        audit.check("six_post_render_gl_checks", isinstance(render_checks, list)
                    and len(render_checks) == len(LABELS)
                    and all(isinstance(x, dict) for x in render_checks)
                    and [x.get("checkpoint") for x in render_checks] == list(LABELS)
                    and all(x.get("glError") == 0 and x.get("contextLost") is False for x in render_checks),
                    actual=render_checks)
        report["post_render_checks"] = render_checks
        for key in ("failures", "page_errors", "console_errors", "blocked_requests"):
            audit.check("empty_" + key, result.get(key) == [], actual=result.get(key))
        audit.check("internal_deadline_not_expired", result.get("internal_deadline_expired") is False)
        audit.check("full_loaded_scene", result.get("load", {}).get("loaded", {}).get("kept") == COUNT
                    and result.get("load", {}).get("loaded", {}).get("total") == COUNT)
        for label, frame in zip(LABELS, FRAMES):
            summary = report["checkpoints"].setdefault(label, {})
            try:
                name = label + ".json.gz"
                if not audit.check(label + ".state_exists", (args.run / name).is_file()):
                    continue
                raw = gzip.decompress((args.run / name).read_bytes())
                meta = entries.get(name, {})
                audit.check(label + ".raw_identity", len(raw) == meta.get("raw_bytes")
                            and digest(raw) == meta.get("raw_sha256") and len(raw) <= cfg["max_checkpoint_bytes"],
                            raw_bytes=len(raw), raw_sha256=digest(raw))
                state = json_load(raw)
                states[label] = state
                indexed = check_state(audit, label, state, frame, cfg, camera, points.get(LABELS[0]))
                if indexed is not None:
                    points[label] = indexed
                    if label == LABELS[0]:
                        audit.check("initial_fresh_material", all(p["state"] == 0 and p["fuel"] == 1
                                    and p["heat"] == p["char"] == p["glow"] == 0 for p in indexed.values()))
                        audit.check("initial_empty_frontier", state.get("frontier") == [])
                        audit.check("initial_empty_gas", state.get("particles", {}).get("count") == 0)
                summary.update({k: state.get(k) for k in ("frame", "time", "scene", "particles", "counters", "hash", "particleStateHash", "randomDraws")})
            except Exception as exc:
                audit.exception(label + ".state_read_or_schema", exc)
            try:
                name = label + ".png"
                audit.check(label + ".png_in_manifest", name in entries)
                info = png_info((args.run / name).read_bytes())
                summary["png"] = info
                audit.check(label + ".png_dimensions", [info["width"], info["height"]] == [cfg["width"], cfg["height"]])
                audit.check(label + ".png_not_all_black", info["visible_nonblack_pixels"] > 0)
            except Exception as exc:
                audit.exception(label + ".png_read", exc)
        events = result.get("events", [])
        audit.check("two_ordered_events", isinstance(events, list) and [e.get("name") for e in events] == ["A", "B"])
        for name, pre, post, pick, event_no in (("A", LABELS[0], LABELS[1], cfg["picks"][0], 0),
                                               ("B", LABELS[2], LABELS[3], cfg["picks"][1], 1)):
            if pre in points and post in points:
                report["events"][name] = check_event(audit, name, states[pre], states[post], points[pre], points[post], pick,
                                                     events[event_no] if isinstance(events, list) and len(events) > event_no else None)
        if LABELS[0] in states and LABELS[5] in states:
            for key in ("points", "frontier", "emitCursor", "scene", "particles", "hash", "particleStateHash", "randomDraws",
                        "counters", "countersByGroup", "areaFeed", "frame", "time", "seed", "params", "camera", "buffer", "sceneInfo"):
                audit.check("reset_initial." + key, key in states[LABELS[0]] and key in states[LABELS[5]]
                            and states[LABELS[0]][key] == states[LABELS[5]][key])
        if "A" in report["events"]:
            original_a = report["events"]["A"]["new_indices"]
            continuity = {}
            previous = None
            for label in LABELS[1:5]:
                if label not in points:
                    continue
                subset = [points[label][i] for i in original_a]
                continuity[label] = {"original_A_count": len(subset), "burning": sum(p["state"] == 1 for p in subset),
                                     "spent": sum(p["state"] == 2 for p in subset), "cold": sum(p["state"] == 0 for p in subset),
                                     "fuel_sum": math.fsum(p["fuel"] for p in subset), "char_sum": math.fsum(p["char"] for p in subset)}
                if previous is not None:
                    for i in original_a:
                        old, new = points[previous][i], points[label][i]
                        audit.check("A_continuation." + previous + "_to_" + label,
                                    new["state"] >= old["state"] and new["fuel"] <= old["fuel"] + 1e-6
                                    and new["char"] + 1e-6 >= old["char"], id=old["id"])
                previous = label
            report["A_continuation"] = continuity
        progress = result.get("progress", [])
        step_frames = [p.get("step_completed") for p in progress if "step_completed" in p]
        audit.check("exact_twelve_step_blocks", step_frames == list(range(30, 361, 30)), actual=step_frames)
        for p in progress:
            if "step_completed" in p:
                audit.check("progress_time", finite(p.get("time")) and abs(p["time"] - p["step_completed"] / 60) <= 1e-10, frame=p.get("step_completed"))
        checkpoints = [p for p in progress if "checkpoint" in p]
        audit.check("six_ordered_checkpoint_summaries", [p["checkpoint"] for p in checkpoints] == list(LABELS))
        for p in checkpoints:
            label = p["checkpoint"]
            if label in states:
                for key in ("frame", "time", "scene", "particles", "counters", "hash"):
                    audit.check("progress_matches_state." + label + "." + key, p.get(key) == states[label].get(key))
                report["checkpoints"][label]["draw_count"] = p.get("draw_count")
        phases = result.get("phases", [])
        audit.check("phase_costs", isinstance(phases, list) and all(isinstance(p, dict) and isinstance(p.get("name"), str)
                    and finite(p.get("ms")) and p["ms"] >= 0 for p in phases))
        worker_ms = result.get("worker_total_ms")
        phase_sum = math.fsum(p["ms"] for p in phases if isinstance(p, dict) and finite(p.get("ms")))
        audit.check("worker_cost", finite(worker_ms) and worker_ms >= phase_sum - 1e-6 and worker_ms <= cfg["internal_deadline_ms"],
                    phase_sum_ms=phase_sum, worker_ms=worker_ms)
        report["cost"] = {"worker_total_ms": worker_ms, "phase_sum_ms": phase_sum, "phases": phases,
                          "supervisor_seconds": report.get("supervisor", {}).get("supervisor_seconds"),
                          "file_inventory_hash_seconds": report.get("supervisor", {}).get("file_inventory_hash_seconds"),
                          "elapsed_before_receipt_write_seconds": report.get("supervisor", {}).get("elapsed_before_receipt_write_seconds"),
                          "supervisor_timing_scope": report.get("supervisor", {}).get("timing_scope"),
                          "interpretation": "one trajectory including loading, capture and cleanup; inventory hashing separately recorded; final small supervisor receipt write and stdout flush excluded; not FPS or renderer benchmark"}
        complete = len(states) == len(points) == 6 and result.get("status") == "completed_capture_pending_saved_audit"
        report["status"] = ("saved_data_consistent_pending_visual_review" if complete and not audit.errors
                            else "saved_data_fail" if complete else "partial_fail")
    except Exception as exc:
        audit.exception("audit_top_level", exc)
    report["checks"] = {"total": audit.checks, "passed": audit.checks - len(audit.errors), "failed": len(audit.errors)}
    report["errors"] = audit.errors
    report["audit_seconds"] = time.perf_counter() - begin
    report["engineering_consistency_pass"] = report["status"] == "saved_data_consistent_pending_visual_review"
    with args.report.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "checks": report["checks"], "report": str(args.report)}, ensure_ascii=False))
    return 0 if report["engineering_consistency_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
