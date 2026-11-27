"""Verify fixed-target image choices, timing comparisons and failed attempts."""
import hashlib
import json
import math
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
METHODS = ["ordinary-indexed", "transport"]


def read(name):
    return json.loads((HERE / name).read_bytes())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_manifest():
    manifest = read("manifest.json")
    expected = {"README.txt", "published.json", "verify.py", "woodpile/cut-histograms.json",
                "room/reference.json", "room/full-process-1.json", "room/full-process-2.json",
                "room/crop-initial-process-1.json", "room/crop-process-1.json", "room/crop-process-2.json"}
    require(set(manifest) == expected, "Missing manifest members")
    for name in expected:
        require(hashlib.sha256((HERE / name).read_bytes()).hexdigest() == manifest[name], name)


def histogram(branch, matte, published):
    data = branch["result"]["contrast"]
    require([data["width"], data["height"]] == [1560, 1040], "Frame size")
    for name, bins, factor, cutoff in (("pixel", 256, 1, 16), ("block", 1021, 4, 64)):
        source = data[name]
        for scope in ("all", "target"):
            values = source[scope]
            sample_count = (data["width"] * data["height"] if scope == "all" else
                            matte["nonzero_cells"] * 4) // factor
            require(len(values) == bins and sum(values) == sample_count and
                    all(isinstance(v, int) and v >= 0 for v in values), "Histogram sample count")
            result = dict(changed=sum(values[1:]), at_threshold=sum(values[cutoff:]),
                          maximum=max(i for i, v in enumerate(values) if v))
            require(result == published[name][scope], "Image contrast statistics")
        require(all(t <= a for t, a in zip(source["target"], source["all"])), "Target exceeds frame")
        # Locations are capture receipts. They cannot be recovered from a nonspatial histogram.
        require(source["bounds"] == published[name]["bounds"], "Bounding-box receipt")
    mass = data["massByBlockBin"]
    require(math.isclose(math.fsum(mass), matte["total"], rel_tol=1e-12) and
            math.isclose(math.fsum(mass[1:]), published["target_mass_any_change"], abs_tol=1e-12) and
            math.fsum(mass[64:]) == published["target_mass_at_threshold"] == branch["result"]["mass"],
            "Weighted contrast")
    return mass


def verify_process(run, reference, study, process, success, action_count):
    exit_record = run["exit"]
    require(exit_record["process"] == process and not exit_record["expired"] and
            0 < exit_record["elapsed_s"] <= exit_record["limit_s"] == 210 and
            0 < run["elapsed_ms"] <= 1000 * exit_record["elapsed_s"], "Process budget")
    require(exit_record["returncode"] == (0 if success else 1) and
            run["status"] == ("replication_complete" if success else "failed"), "Terminal status")
    require(run["parent"] == reference["parent"] and run["rest"] == reference["rest"] and
            run["shell"] == reference["shell"], "Reference geometry and parent")
    require(run["hardware"]["kept"] == 1244819 and len(run["actions"]) == action_count,
            "Geometry or operator count")
    if success:
        require(not run["failure"] and action_count == 17, "Missing successful process")
    elif study == "full":
        require(run["final_phase"] == "full_scene_rest_native_matte_then_restore" and action_count == 0 and
                run["failure"] == ["EPERM: operation not permitted, rename temporary receipt"], "Full stop")
    else:
        require(run["final_phase"] == "ordinary-indexed-audit" and action_count == 1 and
                run["failure"] == ["page.evaluate: Error: ROI preconditions changed"], "Crop stop")
    if not action_count:
        return {}
    require(run["matte"] == reference["matte"], "Target weighting")
    is_crop = study != "full"
    if is_crop:
        roi = run["roi"]
        require(roi["crop"] == run["matte"]["box"] == dict(x=714, y=418, w=156, h=164) and
                roi["sceneScissor"] == [713,417,158,166] and roi["viewport"] == [1560,1040] and
                roi["targetCells"] == run["matte"]["nonzero_cells"] == 2996 and
                roi["total"] == run["matte"]["total"] and run["roi_setup_ms"] > 0, "Crop extent")
    crops = {}
    for i, a in enumerate(run["actions"]):
        require(a["audit"] == (i < 3) and a["host_ms"] > 0 and a["elapsed_ms"] > 0 and
                a["choice"] == "none" and a["secondary"] == "undefined", "Action receipt")
        if i < 3:
            require(a["method"] == ["ordinary-native", *METHODS][i], "Audit order")
        steps = 35 if a["method"] == "transport" else 0
        require(a["shared_steps"] == a["reused_steps"] == steps, "Physics prefix")
        for branch, oracle in zip(a["branches"], reference["branches"], strict=True):
            result = branch["result"]
            require(branch["name"] == oracle["name"] and branch["clicked"] == oracle["clicked"] and
                    result["mass"] == result["fraction"] == 0 and result["denominator"] == run["matte"]["total"]
                    and result["passes"] == (4 * result["mass"] >= result["denominator"]), "Branch decision")
            if a["audit"]:
                require(branch["endpoint"] == oracle["endpoint"] and branch["successor"] == oracle["successor"],
                        "Physical endpoint or successor digest")
            require(result["hashes"] == (oracle["result"]["hashes"] if a["audit"] and
                    (not is_crop or i == 0) else []), "Native full-frame digest")
            if is_crop:
                if i == 0:
                    crops[branch["name"]] = result["cropHashes"]
                require(result["cropHashes"] == (crops[branch["name"]] if a["audit"] else []), "Crop digest")
    if is_crop:
        values = crops["L"] + crops["F"]
        require(len(set(values)) == 4 and all(len(bytes.fromhex(h)) == 32 for h in values), "Four native crops")
    return crops


def timing(run, expected):
    actions = run["actions"]
    process = run["exit"]["process"]
    first_order = METHODS if process == 1 else METHODS[::-1]
    require([r.get("timing_role") for r in actions[3:]] == ["warmup"] * 2 + ["measured"] * 12 and
            [r["method"] for r in actions[3:5]] == first_order and len(run["waves"]) == 6, "Warm-up order")
    times, ratios, savings = {m: [] for m in METHODS}, [], []
    for i, wave in enumerate(run["waves"]):
        pair = actions[5 + 2*i:7 + 2*i]
        order = first_order if i % 2 == 0 else first_order[::-1]
        require([r["method"] for r in pair] == order == wave["order"] and
                all(r["wave"] == wave["wave"] == i+1 for r in pair), "Counterbalancing")
        for r in pair:
            times[r["method"]].append({"host_ms": r["host_ms"], **r["phases"]})
        ordinary, transported = (times[m][-1]["host_ms"] for m in METHODS)
        ratios.append(transported / ordinary)
        savings.append(ordinary - transported)
    med = {m: {key: median(r[key] for r in rows)
               for key in ("host_ms", "physics_ms", "image_ms", "fork_restore_ms")} for m, rows in times.items()}
    hosts = {m: row["host_ms"] for m, row in med.items()}
    require((med == expected["medians"] if "medians" in expected else hosts == expected["medians_ms"]) and
            hosts["transport"] / hosts["ordinary-indexed"] == expected["ratio_of_medians"] and
            median(ratios) == expected["median_paired_ratio"] and sum(s > 0 for s in savings) ==
            expected["transport_wins"], "Measured paired timings")
    if "median_paired_saving_ms" in expected:
        require(median(savings) == expected["median_paired_saving_ms"], "Median within-pair saving")
    print(f"  process {process}: {hosts[METHODS[0]]:.2f} -> {hosts[METHODS[1]]:.2f} ms, "
          f"{expected['transport_wins']}/6 wins, median paired ratio {median(ratios):.5f}")


def sensitivity(name, bins, expected):
    total = expected["denominator"]
    curves = []
    for weights in bins:
        require(len(weights) == 1021 and all(math.isfinite(x) and x >= 0 for x in weights) and
                math.isclose(math.fsum(weights), total, rel_tol=1e-11), "Sensitivity source mass")
        curves.append([math.fsum(weights[i:])/total for i in range(1,1021)])
    intervals = []
    for i, (light, full) in enumerate(zip(*curves), 1):
        vote = "light" if light >= 0.25 else "full" if full >= 0.25 else "neither"
        if intervals and intervals[-1]["choice"] == vote:
            intervals[-1]["last"] = i/4
        else:
            intervals.append(dict(choice=vote, first=i/4, last=i/4))
    highest = [max((i/4 for i, f in enumerate(curve,1) if f >= 0.25), default=None) for curve in curves]
    require(intervals == expected["choices"] and highest == expected["highest_passing_cutoff"] and
            [c[0] for c in curves] == expected["fraction_at_smallest"] and
            [c[63] for c in curves] == expected["fraction_at_16"], "All positive cutoffs")
    print(" ", name, intervals)


def main():
    check_manifest()
    expected = read("published.json")
    require(len(expected["crop"]) == 2, "Expected two completed target-crop processes")
    reference = read("room/reference.json")
    require([b["name"] for b in reference["branches"]] == ["L", "F"] and all(
        (b["endpoint"]["frame"], b["successor"]["frame"]) == (270,271)
        for b in reference["branches"]), "Reference trajectory")
    full = read("room/full-process-1.json")
    verify_process(full, reference, "full", 1, True, 17)
    verify_process(read("room/full-process-2.json"), reference, "full", 2, False, 0)
    print("Full viewport: one completed process, second failed before timing.")
    timing(full, expected["full"])
    initial = read("room/crop-initial-process-1.json")
    previous_crops = verify_process(initial, reference, "initial", 1, False, 1)
    print("Initial crop: one native reference action, zero measured requests.")
    print("Corrected target crop:")
    for i, costs in enumerate(expected["crop"],1):
        run = read(f"room/crop-process-{i}.json")
        require(verify_process(run, reference, "crop", i, True, 17) == previous_crops, "Cross-process crops")
        timing(run, costs)
    room_weights = [histogram(b, full["matte"], expected["full"]["histograms"][b["name"]])
                    for b in full["actions"][0]["branches"]]
    observed = expected["sensitivity"]
    require(observed["cutoff_count"] == 1020 and observed["threshold_scale"] == 4 and
            observed["required_fraction"] == .25 and observed["undefined"] == ["bonsai_146"] and
            len(observed["views"]) == 3, "Sensitivity specification")
    print("Every positive cutoff, 0.25 through 255 display levels:")
    wood = read("woodpile/cut-histograms.json")
    for camera in (0,124):
        bins = [wood[f"{camera}-{b}"] for b in ("light","full")]
        require(all(len(s["counts"]) == 1021 and sum(s["counts"]) == 470*264 and
                    min(s["counts"]) >= 0 for s in bins), "Woodpile sample counts")
        name = f"woodpile_{camera}"
        sensitivity(name, [s["weights"] for s in bins], observed["views"][name])
    sensitivity("bonsai_0", room_weights, observed["views"]["bonsai_0"])


if __name__ == "__main__":
    main()
