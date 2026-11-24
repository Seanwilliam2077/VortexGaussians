"""Certify two native Firewoods edit prefixes using a cached unedited take."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "t84-ignition-edit-footprint"))
import clock_preview as clocks
import spatial_preview as geometry


def require(condition, label):
    if not condition:
        raise ValueError(label)


def encode(values):
    return json.dumps(values, separators=(",", ":")).encode("ascii")


def signature(values):
    return hashlib.sha256(encode(values)).hexdigest()


def snapshot(arm, point, manifest):
    name = f"{arm}-{point}.dynamic.json.gz"
    return json.loads(clocks.source(name, manifest))


def inputs(asset):
    identities = {}
    recipe = json.loads(geometry.checked(geometry.RECIPE, geometry.RECIPE_SHA, identities))
    manifest = json.loads(geometry.checked(geometry.PUBLIC / "MANIFEST.json", geometry.MANIFEST_SHA, identities))
    packed = geometry.checked(asset, geometry.ASSET_SHA, identities)
    positions = geometry.centers(packed)
    params = recipe["params"]
    expected = {"emitterOn": False, "embers": False, "filament": False, "solver": "vpm",
                "simLayers": 9, "layers": 9, "ppl": 600, "sliceMode": "world", "sceneScale": 1,
                "sceneOffZ": 0, "sceneYaw": 0, "scenePitch": 0, "spreadClockMode": "elapsed",
                "spreadMeasureMode": "legacy", "spreadFeedCap": 48, "spreadFrontierCap": 1400,
                "spreadParticlePolicy": "block", "spreadBurnT": 6}
    require(all(params[k] == v for k, v in expected.items()), "unsupported native configuration")
    z = positions[:, 2] - recipe["source_center"][2]
    layer = np.floor((z / params["sliceDepth"] + 0.5) * (params["layers"] - 1) + 0.5)
    layer = np.clip(layer, 0, params["layers"] - 1).astype(int).tolist()
    return recipe, {f["file"]: f for f in manifest["files"]}, layer, identities


def prepare_cache(policy, manifest, recipe):
    a = policy + "-A"
    start = snapshot(a, "prefix", manifest)
    endpoint = snapshot(a, "endpoint", manifest)
    # This input is available immediately on a user's click, before any edited step.
    edit = snapshot(policy + "-AB", "after-intervention", manifest)
    values = clocks.material(start, a)
    clocks.material(endpoint, a)
    old_frontier = start["frontier"]
    edited = edit["frontier"]
    b_ids = edited[len(old_frontier):]
    require(edited[:len(old_frontier)] == old_frontier and len(old_frontier) >= 1400,
            "the edit must append after the serviced graph sources")
    require(set(b_ids) == set(edit["newly_B_indices"]) and len(set(edited)) == len(edited),
            "bad edit input memberships or order")
    require(edit["frame"] == 180 and edit["emit_cursor"] == start["emit_cursor"] and
            edit["gas"] == start["gas"] and edit["random_draws"] == start["random_draws"],
            "instantaneous edit changed the gas, cursor or random counter")
    min_fuel = min(values[i][0] for i in edited)
    for _ in range(180):
        min_fuel = clocks.f32(min_fuel - recipe["dt"] / recipe["params"]["spreadBurnT"])
    require(min_fuel > 0 and all(v[0] == 1 for v in values.values() if v[1] == 0),
            "retirement is possible during the certified window")
    order = endpoint["frontier"]
    require(order[:len(old_frontier)] == old_frontier and not (set(order) - set(values)),
            "nonappend-only cached take")
    rows = [json.loads(line) for line in clocks.source(a + "-steps.jsonl.gz", manifest).splitlines()]
    require([r["frame"] for r in rows] == list(range(1,361)), "missing or reordered native frames")
    return start, list(edited), set(b_ids), order, rows


def shadow(policy, cache, layers):
    start, frontier, direct, order, rows = cache
    cursor = start["emit_cursor"]
    old_cursor = cursor
    active = len(start["frontier"])
    clock = rows[179]["counters"]["clockProcessed"]
    strict = None
    stop = None
    trace = []
    skipped = {"blocked": 0, "randomRejected": 0}
    for row in rows[180:]:
        frame = row["frame"]
        next_clock = row["counters"]["clockProcessed"]
        count = next_clock - clock
        require(active <= count <= len(order), "cached active cardinality")
        appended = order[active:count]
        require(appended == sorted(appended), "cached threshold scan order")
        frontier.extend(i for i in appended if i not in direct)
        active, clock = count, next_clock
        offers = row["offers"]
        require(len(offers) == 48, "unexpected offer count")
        occupancy = row["layerCounts"].copy()
        for old in offers:
            if old[6] == "emitted":
                occupancy[old[1]] -= 1
        events = []
        for slot, old in enumerate(offers):
            cursor = (cursor + 1) % len(frontier)
            old_cursor = (old_cursor + 1) % count
            i = frontier[cursor]
            k = layers[i]
            old_id, old_layer = old[:2]
            require(old_id == order[old_cursor] and old_layer == layers[old_id] and
                    occupancy[old_layer] == old[2] and sum(occupancy) == old[3], "cached offer state")
            if i != old_id and strict is None:
                strict = {"frame": frame, "slot_zero_based": slot}
            full = sum(occupancy) >= 5400 if policy == "global" else occupancy[k] >= 600
            reason = None
            if full != bool(old[5]):
                reason = "capacity decision changes the random stream"
            elif old[6] == "emitted" and i != old_id:
                reason = "accepted birth has a different source ID"
            if reason:
                stop = {"frame": frame, "slot_zero_based": slot, "reason": reason,
                        "cached_source": old_id, "edited_source": i, "cached_outcome": old[6]}
                break
            if old[6] == "emitted":
                occupancy[k] += 1
            elif i != old_id:
                skipped[old[6]] += 1
            events.append([i, k, old[6]])
        trace.append({"frame": frame, "active_sha256": signature(sorted(frontier)),
                      "certified_offers": len(events), "offers_sha256": signature(events)})
        if stop:
            break
        require(occupancy == row["layerCounts"], "certified final occupancy")
    complete = len(trace) - int(stop is not None)
    strict_frames = 180 if strict is None else strict["frame"] - 181
    return {"rows": trace, "complete_steps": complete, "first_unresolved": stop,
            "first_strict_source_mismatch": strict, "strict_complete_steps": strict_frames,
            "certified_extra_steps_vs_strict": complete - strict_frames,
            "certified_different_source_no_birth_offers": skipped,
            "last_material_frame": trace[-1]["frame"], "last_certified_gas_frame": 180 + complete,
            "cached_A_suffix_step_render_ms": sum(r["timing"]["step_plus_render_ms"] for r in rows[180:]),
            "cached_A_prefix_step_render_ms": sum(r["timing"]["step_plus_render_ms"] for r in rows[:180])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path, default=HERE.parents[4] / "real-asset-ingest/foreground.ply")
    args = parser.parse_args()
    begin = time.perf_counter()
    recipe, manifest, layers, identities = inputs(args.asset)
    times = {"geometry_recipe_manifest_s": time.perf_counter() - begin}
    result = {"schema": "t85-prefix-v1", "input_hashes": identities, "policies": {}}
    for policy in ["per-layer", "global"]:
        t = time.perf_counter()
        cache = prepare_cache(policy, manifest, recipe)
        times[policy + "_cache_decode_check_s"] = time.perf_counter() - t
        t = time.perf_counter()
        result["policies"][policy] = shadow(policy, cache, layers)
        times[policy + "_prediction_including_hashing_s"] = time.perf_counter() - t
    target = HERE / "PREDICTIONS.json"
    data = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode()
    if target.exists():
        require(target.read_bytes() == data, "recorded predictions differ")
    else:
        with target.open("xb") as handle:
            handle.write(data)
    times["total_in_process_s"] = time.perf_counter() - begin
    print(json.dumps({p: {k: v for k, v in pred.items() if k != "rows"}
                      for p, pred in result["policies"].items()}))
    print(json.dumps(times))


if __name__ == "__main__":
    main()
