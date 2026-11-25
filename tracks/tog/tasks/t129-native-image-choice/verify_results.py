"""Recompute native image choices and summarize balanced, matched-cost T129 trials."""
import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
from statistics import median


HERE = Path(__file__).resolve().parent
T127 = HERE.parent / "t127-woodpile-native-camera" / "evidence"
METHODS = ("ordinary", "sibling")
VIEWS = ((0,), (0, 124))
PICKS = {"L": "light", "F": "full"}
SHELL_DIGEST = {0: "535982ac918ef2ff415e7975dd8f93f0899650b590c9bf5ebdf5ac26f13d7e8a",
                124: "a97db4ecb791aed0e1b89d016774d5994cb7db337431f77adf5d0365d7689918"}
# Count and exact lower-left GL bounds from the registered nonzero top-left shell projection.
SHELL_SUPPORT = {0: (880, 436, 166, 76, 80), 124: (3786, 264, 18, 146, 162)}


def check(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def near(actual, expected, field):
    check(math.isfinite(actual) and math.isclose(actual, expected, rel_tol=3e-12, abs_tol=1e-9), field)


def references():
    capture, score = read(T127 / "CAPTURE.json"), read(T127 / "SCORE.json")
    check(capture["status"] == "validated_native_capture" and not capture["errors"], "T127 capture status")
    refs = {(row["brush"], row["camera"]): row for row in score["comparisons"] if row["horizon"] == 90}
    check(len(refs) == 4, "T127 endpoint branches and cameras")
    for pick, brush in PICKS.items():
        arm = capture["arms"]["A" + pick]
        for camera in (0, 124):
            r = refs[brush, camera]
            for mode in ("wood", "full"):
                filename = f"{brush}-c{camera}-h90-{mode}.png"
                draws = [e for e in arm["renders"] if e["frame"] == 270 and e["camera"] == camera
                         and e["mode"] == mode and not e["repeat"]]
                check(len(draws) == 1 and draws[0]["sha256"] == r["sha256"][filename], "T127 audit PNG")
            check(r["passes_quarter"] == (4*r["changed_shell_mass"] >= r["shell_mass"]), "T127 threshold")
    return refs, capture


def verify_view(view, pick, reference, audit):
    camera = view["camera"]
    brush = PICKS[pick]
    expected = reference[brush, camera]
    for field in ("changed_shell_mass", "shell_mass", "fraction"):
        near(view[field], expected[field], "Different native image statistic: " + field)
    check(view["passes_quarter"] is expected["passes_quarter"], "Different native image Boolean")
    if audit:
        hashes = {mode: expected["sha256"][f"{brush}-c{camera}-h90-{mode}.png"] for mode in ("full", "wood")}
        check(view["png_sha256"] == hashes, "Full-frame composite/wood hash differs from T127")


def verify_operation(row, reference, audit=False):
    method = row["method"]
    check(method in METHODS, "Unknown method")
    cameras = (0, 124) if audit else tuple(row["cameras"])
    check(cameras in VIEWS, "Unknown query")
    missed = [camera for camera in cameras if not reference["light", camera]["passes_quarter"]]
    choices = {str(c): ("L" if c not in missed else "F" if reference["full", c]["passes_quarter"] else "none")
               for c in cameras}
    if not audit:
        check(row["choices"] == choices, "Delivered choice")
    strokes = row["strokes"]
    picks = ["L", "F"] if (audit or missed) else ["L"]
    check([s["pick"] for s in strokes] == picks, "Unnecessary or missing simulated stroke")
    shared = 24 if method == "sibling" else 0
    check(row["shared_steps"] == shared and row["reused_steps"] == (shared if "F" in picks else 0),
          "Certified or actually reused steps")
    for stroke in strokes:
        pick = stroke["pick"]
        check(stroke["clicked"] == {"L": 74, "F": 288}[pick], "Direct stroke footprint")
        expected_cameras = list(cameras) if audit or pick == "L" else missed
        check([v["camera"] for v in stroke["views"]] == expected_cameras, "Unnecessary or missing view")
        check(stroke["steps"] == (66 if pick == "F" and method == "sibling" else 90), "Number of solver steps")
        for view in stroke["views"]:
            verify_view(view, pick, reference, audit)


def positive(value, field):
    check(isinstance(value, (float, int)) and math.isfinite(value) and value > 0, field)
    return value


def verify_setup(path):
    setup = read(path)
    weights = setup["weights"]
    base = read(T127 / "SCORE.json")
    check(weights["schema"] == "t129-shell-f64-v1" and weights["source_sha256"] == base["source_sha256"],
          "T127 weight provenance")
    check(weights["observer_sha256"] == sha(T127.parent / "score.py"), "T127 reference implementation")
    for c in (0, 124):
        v = weights["views"][str(c)]
        check(v["sha256"] == SHELL_DIGEST[c] and v["file"] == f"camera-{c}.f64", "Exact floating shell bytes")
        check((v["rows"], v["columns"], v["bytes"]) == (264, 470, 992640), "Float64 raster layout")
        for k, expected in base["reference_checks"][str(c)].items():
            check(v[k] == expected, "T127 shell provenance: " + k)
    kernel_ms = positive(weights["cold_prepare_ms"], "Cold weights preparation")
    host_ms = positive(setup["projection_host_ms"], "Host duration for projection")
    check(0 < weights["raster_and_verify_ms"] <= kernel_ms <= host_ms + 2, "Projection clocks")
    return {"file": path.name, "sha256": sha(path), "projection_host_ms": host_ms,
            "projection_inner_ms": kernel_ms, "projection_covers_cameras": [0, 124], "weight_bytes": 1985280}


def process_result(path, reference, capture):
    block = read(path)
    check(block["status"] == "validated" and not block.get("errors"), "Invalid capture in " + path.name)
    check(path.name == f"process-{block['process']}.json" and block["process"] in (1, 2), "Process identity")
    sources = block["sources"]
    actual = {"T127_capture": sha(T127 / "CAPTURE.json"), "T127_score": sha(T127 / "SCORE.json"),
              "native_kernels": sha(HERE / "native-kernels.js"), "action": sha(HERE / "action.js"),
              "worker": sha(HERE / "run.mjs"), **{f"view_{c}": h for c, h in SHELL_DIGEST.items()}}
    check(all(sources.get(k) == h for k, h in actual.items()), "Changed source or installed view bytes")
    for camera in (0, 124):
        calibration = block["calibration"][str(camera)]
        near(calibration["total"], reference["light", camera]["shell_mass"], "Installed mass")
        roi = calibration["roi_gl"]
        check((calibration["positive_pixels"], roi["x"], roi["y"], roi["width"], roi["height"])
              == SHELL_SUPPORT[camera], "GL readback must exactly bound the registered visible shell")
        positive(block["setup_ms"][f"upload_view_{camera}_ms"], "View upload/install time")
    positive(block["setup_ms"]["read_matte_tables_ms"], "Reading the shared map bytes")
    audits = block["audits"]
    check(len(audits) == 2 and {a["method"] for a in audits} == set(METHODS), "Independent per-method image audits")
    parent = capture["arms"]["AL"]["fork"]["pre"]
    check(block["common_parent"] == parent == capture["arms"]["AF"]["fork"]["pre"], "Common physical parent")
    for audit in audits:
        verify_operation(audit, reference, audit=True)
        for stroke in audit["strokes"]:
            expected = capture["arms"]["A" + stroke["pick"]]["frames"]["270"]
            check(stroke["state"] == expected, "T127 endpoint physical bytes and ordered gas/RNG state")
    trials = block["trials"]
    check(len(trials) == 28, "Two methods x two queries x seven calls")
    grouped = defaultdict(list)
    for row in trials:
        verify_operation(row, reference)
        positive(row["delivered_ms"], "Delivered clock")
        check(0 < row["browser_ms"] <= row["delivered_ms"] + 2, "Browser versus host delivery")
        phases = row["phases_ms"]
        check(isinstance(phases, dict) and bool(phases) and all(isinstance(x, (float, int))
              and math.isfinite(x) and x >= 0 for x in phases.values()), "Completed action phases")
        check(type(row["rep"]) is int and row["rep"] in range(7), "Warm-up/repetition index")
        grouped[tuple(row["cameras"]), row["rep"]].append(row)
    queries = []
    for cameras in VIEWS:
        times = {method: [] for method in METHODS}
        phase_samples = {method: defaultdict(list) for method in METHODS}
        first_measured = []
        for repeat in range(7):
            pair = grouped[cameras, repeat]
            check(len(pair) == 2 and {r["method"] for r in pair} == set(METHODS), "Missing paired trial")
            if repeat:
                first_measured.append(pair[0]["method"])
            for r in pair:
                times[r["method"]].append(r["delivered_ms"])
                if repeat:
                    for name, ms in r["phases_ms"].items():
                        phase_samples[r["method"]][name].append(ms)
        check(first_measured.count("ordinary") == first_measured.count("sibling") == 3, "Unbalanced measurement order")
        medians = {m: median(times[m][1:]) for m in METHODS}
        ratios = [s / o for s, o in zip(times["sibling"][1:], times["ordinary"][1:])]
        queries.append({"cameras": list(cameras), "first_call_ms": {m: times[m][0] for m in METHODS},
                        "measured_ms": {m: times[m][1:] for m in METHODS}, "median_ms": medians,
                        "phase_median_ms": {m: {k: median(v) for k, v in phases.items()}
                                            for m, phases in phase_samples.items()},
                        "first_measured_methods": first_measured, "paired_sibling_wins": sum(r < 1 for r in ratios),
                        "sibling_over_ordinary": medians["sibling"] / medians["ordinary"],
                        "paired_sibling_over_ordinary": ratios})
    scope_order = [list(x) for x in dict.fromkeys(tuple(r["cameras"]) for r in trials)]
    return {"file": path.name, "sha256": sha(path), "setup_ms": block["setup_ms"],
            "issued": len(trials), "scope_order": scope_order, "queries": queries, "pid": block["pid"],
            "start": block["started_utc"], "finish": block["finished_utc"], "process_wall_ms": block["wall_ms"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=HERE / "evidence")
    args = parser.parse_args()
    reference, capture = references()
    cold = verify_setup(args.evidence / "common_setup.json")
    blocks = [process_result(args.evidence / f"process-{n}.json", reference, capture) for n in (1, 2)]
    check(blocks[0]["pid"] != blocks[1]["pid"], "Two fresh processes")
    check(datetime.fromisoformat(blocks[0]["finish"].replace("Z", "+00:00"))
          <= datetime.fromisoformat(blocks[1]["start"].replace("Z", "+00:00")), "Serial process execution")
    check(blocks[0]["scope_order"] == blocks[1]["scope_order"][::-1], "Reversal of camera scope sequence")
    summary = []
    for a, b in zip(blocks[0]["queries"], blocks[1]["queries"]):
        ratios = [q["sibling_over_ordinary"] for q in (a, b)]
        check(a["cameras"] == b["cameras"], "Scope alignment")
        summary.append({"cameras": a["cameras"], "process_ratios": ratios,
                        "sibling_faster_both": all(r < 1 for r in ratios),
                        "ordinary_faster_both": all(r > 1 for r in ratios)})
    print(json.dumps({"schema": "t129-native-choice-verification-v1", "processes": blocks, "cold_projection": cold,
                      "issued": sum(b["issued"] for b in blocks),
                      "measured": 48, "warmups": 8, "warm_paired_directions": summary,
                      "reference_sha256": {f: sha(T127 / f) for f in ("CAPTURE.json", "SCORE.json")}},
                     indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
