"""Bound native cold-site ignition up to each future scan using only a present cut."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent / "t84-ignition-edit-footprint"))
import spatial_preview as geometry

ARMS = ("AB", "BA")
CUTS = (210, 240, 300)
HORIZONS = (1, 4, 8)
METHODS = ("global", "support", "uniform", "weighted")
# SI units here are native scene units. The scene, native live particles and
# their eight-step enclosures have coordinate magnitudes below 16. This pad
# exceeds binary64 error in transforms, distance evaluation and eight updates.
GEOM_PAD = 1e-9
SPEED_UP = 4.000002  # the native norm cap is 4 before storing two float32 components
U32 = 2.0 ** -24
TINY32 = np.finfo(np.float32).tiny
REDUCTION_UP = 1.0 + 1e-11  # positive double sums have at most 1400 (graph) or 5400+336 terms


def require(condition, message):
    if not condition:
        raise ValueError(message)


def data_bytes(obj):
    return json.dumps(obj, separators=(",", ":"), allow_nan=False).encode("utf8")


def upward_sum(initial, addition, writes):
    """Cover n sequential nonnegative float32 additions and subnormal writes."""
    return (initial + addition * REDUCTION_UP + writes * TINY32) / (1 - writes * U32)


def groups(xy, layers, temperatures, jitter):
    """Group at the native ignition-radius width; retain bounding box, count and hottest T."""
    if not len(xy):
        return []
    cells = np.column_stack((layers, np.floor(xy / .14).astype(np.int64)))
    keys, inverse, counts = np.unique(cells, axis=0, return_inverse=True, return_counts=True)
    lo = np.full((len(keys), 2), np.inf)
    hi = np.full((len(keys), 2), -np.inf)
    tmax = np.zeros(len(keys))
    np.minimum.at(lo, inverse, xy)
    np.maximum.at(hi, inverse, xy)
    np.maximum.at(tmax, inverse, temperatures)
    if jitter:
        lo[:, 0] -= .02
        hi[:, 0] += .02
        hi[:, 1] += .03
    return [(int(k[0]), a, b, float(t), int(n)) for k, a, b, t, n in zip(keys, lo, hi, tmax, counts)]


def graph_upper(world, donors, p, dt):
    """All serviced source centers are fixed in space. Group donors solely to accelerate queries."""
    radius = p["spreadR"]
    donor_xyz = world[donors]
    keys, inverse = np.unique(np.floor(donor_xyz / radius).astype(int), axis=0, return_inverse=True)
    heat = np.zeros(len(world))
    writes = np.zeros(len(world), dtype=int)
    for k in range(len(keys)):
        pos = donor_xyz[inverse == k]
        padded = radius + GEOM_PAD
        mask = np.all((world >= pos.min(axis=0) - padded) & (world <= pos.max(axis=0) + padded), axis=1)
        ids = np.flatnonzero(mask)
        delta = world[ids, None, :] - pos[None, :, :]
        distance = np.maximum(0, np.sqrt(np.sum(delta * delta, axis=2)) - GEOM_PAD)
        weight = np.maximum(0, 1 - distance / radius)
        upward = 1 + 2.2 * np.maximum(0, (delta[:, :, 1] + GEOM_PAD) / radius)
        heat[ids] += np.sum(weight * upward, axis=1) * (dt * p["spreadRate"])
        writes[ids] += np.count_nonzero(weight, axis=1)
    # A boundary hit with zero delta writes precisely the same float32 value.
    return heat, writes


def prepare(snapshot, recipe, world):
    p = snapshot["params"]
    keys = ("simLayers", "layers", "sceneScale", "sceneYaw", "scenePitch", "sceneLift", "sceneOffX",
            "sceneOffZ", "spreadOn", "spreadHeat", "spreadFlameHeat", "spreadSampleCap",
            "spreadFeedCap", "spreadFrontierCap", "spreadParticlePolicy", "spreadMeasureMode",
            "spreadClockMode", "spreadSceneFeed", "spreadRate", "spreadIgnR", "spreadIgnH",
            "spreadR", "spreadBurnT", "solver", "dimMode", "sliceMode", "sliceDepth", "emitterOn",
            "interZ", "embers", "filament", "cool", "ppl")
    require(all(p[k] == recipe["params"][k] for k in keys), "unsupported native controls")
    dt = snapshot["dt"]
    require(snapshot["schema"] == "t86-native-cut-v1" and snapshot["policy"] == "global"
            and dt == recipe["dt"] and np.array_equal(snapshot["scene_center"], recipe["source_center"]),
            "unexpected checkpoint placement, timestep or policy")
    state, fuel, heat = (np.asarray(snapshot[k]) for k in ("state", "fuel", "heat"))
    require(all(a.shape == (geometry.N,) for a in (state, fuel, heat)), "incomplete material input")
    require(np.all(np.isin(state, (0, 1, 2))) and np.isfinite(heat).all() and np.min(heat) >= 0
            and np.isfinite(fuel).all() and np.array_equal(heat, heat.astype(np.float32))
            and np.array_equal(fuel, fuel.astype(np.float32)), "invalid native heat/fuel/state")
    frontier = np.asarray(snapshot["frontier"], dtype=int)
    require(np.array_equal(np.sort(frontier), np.flatnonzero(state == 1)), "invalid active frontier")
    require(0 <= snapshot["emit_cursor"] < len(frontier), "invalid emission cursor")
    # The subtract is in binary64, followed by the native binary32 fuel store.
    surviving = fuel[frontier].astype(np.float64)
    for _ in range(max(HORIZONS)):
        surviving = (surviving - dt / p["spreadBurnT"]).astype(np.float32).astype(np.float64)
    graph_cap = p["spreadFrontierCap"]
    fixed = len(frontier) >= graph_cap and np.all(surviving[:graph_cap] > 0)
    if fixed:
        graph, graph_n = graph_upper(world, frontier[:graph_cap], p, dt)
    else:
        # Future donors can be anywhere. Within radius upward bias <= 1+2.2.
        graph_n = np.full(len(world), graph_cap)
        graph = graph_n * dt * p["spreadRate"] * (3.2 + GEOM_PAD)
    old_xy, old_layers, old_t = [], [], []
    require([g["idx"] for g in snapshot["gas"]] == list(range(p["layers"])), "missing gas layer")
    for layer in snapshot["gas"]:
        for particle in layer["particles"]:
            x, y, temp = (particle[k] for k in ("x", "y", "T"))
            require(abs(x) <= 16 and abs(y) <= 16 and 0 <= temp <= 1, "gas outside proven envelope")
            if temp >= .55:
                old_xy.append((x, y))
                old_layers.append(layer["idx"])
                old_t.append(temp)
    cohorts = [groups(np.array(old_xy), old_layers, old_t, False)]
    unknown = [0]
    layer_ids = np.clip(np.floor((world[:, 2]/p["sliceDepth"] + .5) * (p["layers"]-1) + .5),
                        0, p["layers"] - 1).astype(int)
    # New ignitions append at the tail. Each slot preceding the first possible
    # wrap still selects its original source if the entire old frontier survives.
    # After that, or after a possible retirement, allow offers anywhere.
    cursor = snapshot["emit_cursor"]
    stable = np.all(surviving > 0) and len(frontier) >= p["spreadFeedCap"]
    n_offers = p["spreadFeedCap"]
    for _ in range(1, max(HORIZONS)):
        known = min(n_offers, max(0, len(frontier) - 1 - cursor)) if stable else 0
        ids = frontier[cursor+1:cursor+1+known]
        cohorts.append(groups(world[ids, :2], layer_ids[ids], np.ones(len(ids)), True))
        unknown.append(n_offers - known)
        cursor += n_offers
    eligible = (state == 0) & (fuel > 0)
    return {"heat": heat[eligible], "ids": np.flatnonzero(eligible), "burning": len(frontier),
            "world": world[eligible], "graph": graph[eligible], "graph_n": graph_n[eligible],
            "cohorts": cohorts, "unknown": unknown, "fixed_graph": bool(fixed), "p": p, "dt": dt}


def upper_temp(t, age, dt, cool):
    # On [0,1+1e-10] x-dt*cool*x*x increases. Include roundoff at each iteration.
    for _ in range(age):
        t = t - dt * cool * t * t + 1e-13
    return min(1.0, t)


def flame_bound(pre, k, method, slabs):
    p, dt = pre["p"], pre["dt"]
    cap, radius = p["spreadSampleCap"], p["spreadIgnR"]
    size = len(pre["ids"])
    if method == "global":
        return np.full(size, cap, dtype=float), np.full(size, cap, dtype=int)
    # Each unknown offer can add at most one carrier. It can be anywhere.
    unknown = sum(pre["unknown"][:k])
    counts = np.full(size, unknown, dtype=int)
    weighted = np.full(size, float(unknown)) if method == "weighted" else None
    w = pre["world"]
    for birth, cohort in enumerate(pre["cohorts"][:k]):
        age = k - birth
        travel = SPEED_UP * dt * age + GEOM_PAD
        for layer, lo, hi, t0, count in cohort:
            temp = upper_temp(t0, age, dt, p["cool"])
            if temp < .55:
                continue
            ids, xs, dz = slabs[layer]
            left, right = np.searchsorted(xs, [lo[0]-travel-radius-GEOM_PAD, hi[0]+travel+radius+GEOM_PAD],
                                          side="left")
            subset = ids[left:right]
            # AABB represents the cohort's initial centers including possible
            # birth jitter, then a speed-limited XY disk and fixed layer plane.
            patch = w[subset, :2]
            xy_gap = np.maximum(0, np.maximum(lo - patch, patch - hi))
            xy_dist = np.maximum(0, np.hypot(xy_gap[:, 0], xy_gap[:, 1]) - travel)
            dmin = np.maximum(0, np.hypot(xy_dist, dz[left:right]) - GEOM_PAD)
            hit = dmin < radius
            rec = subset[hit]
            counts[rec] += count
            if weighted is not None:
                weighted[rec] += count * temp * (1 - dmin[hit]/radius)
    counts = np.minimum(counts, cap)
    if method == "support":
        # If there is possible gas contact we abstain irrespective of native heat.
        # Returning the global thermal bound still covers the arithmetic recurrence.
        return np.where(counts > 0, cap, 0), counts
    if weighted is None:
        return counts.astype(float), counts
    return np.minimum(weighted * REDUCTION_UP, counts), counts


def predict(pre, method):
    p, dt = pre["p"], pre["dt"]
    upper = pre["heat"].copy()
    safe = np.ones(len(upper), dtype=bool)
    outputs, timings = {}, {}
    slabs = []
    begin = perf_counter()
    if method != "global":
        w = pre["world"]
        for layer in range(p["layers"]):
            z = (layer/(p["layers"]-1) - .5) * p["sliceDepth"]
            member = np.flatnonzero(np.abs(w[:, 2] - z) <= p["spreadIgnR"] + GEOM_PAD)
            ids = member[np.argsort(w[member, 0], kind="stable")]
            slabs.append((ids, w[ids, 0], np.abs(w[ids, 2]-z)))
    output_seconds = 0
    for k in range(1, max(HORIZONS) + 1):
        flame, writes = flame_bound(pre, k, method, slabs)
        if method == "support":
            safe &= writes == 0
        before_decay = upward_sum(upper, flame * (dt * p["spreadHeat"]), writes)
        scanned = upward_sum(np.zeros(len(upper)), before_decay * (1-dt*.35), 1)
        safe &= scanned < p["spreadIgnH"]
        # Even a crossing in an earlier scan followed by cooling invalidates
        # an all-window certificate. Graph deposits for k enter scan k+1 only.
        upper = upward_sum(scanned, pre["graph"], pre["graph_n"])
        if k in HORIZONS:
            t = perf_counter()
            timings[k] = t - begin - output_seconds
            outputs[k] = pre["ids"][safe].tolist()
            output_seconds += perf_counter() - t
    return outputs, timings, output_seconds


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--asset", type=Path, default=HERE.parents[4]/"real-asset-ingest/foreground.ply")
    ap.add_argument("--input-dir", type=Path, default=HERE/"local")
    ap.add_argument("--output", type=Path, default=HERE/"PREDICTIONS.json.gz")
    ap.add_argument("--costs", type=Path, default=HERE/"COSTS.json")
    args = ap.parse_args()
    start = perf_counter()
    identities = {}
    recipe = json.loads(geometry.checked(geometry.RECIPE, geometry.RECIPE_SHA, identities))
    world = geometry.centers(geometry.checked(args.asset, geometry.ASSET_SHA, identities))
    world -= np.array(recipe["source_center"])
    world[:, 1] += recipe["params"]["sceneLift"]
    require(np.max(np.abs(world)) < 16, "material coordinate range")
    costs = {"unit": "seconds", "geometry_read_hash_transform": perf_counter()-start, "cuts": []}
    result = {"schema": "t86-cold-predictions-v1", "inputs": identities, "methods": list(METHODS), "queries": []}
    for arm in ARMS:
        for cut in CUTS:
            t = perf_counter()
            path = args.input_dir/f"{arm}-{cut}.json.gz"
            raw = path.read_bytes()
            identities[path.name] = hashlib.sha256(raw).hexdigest()
            snapshot = json.loads(gzip.decompress(raw))
            require((snapshot["arm"], snapshot["frame"]) == (arm, cut), "wrong cut identity")
            prep_start = perf_counter()
            pre = prepare(snapshot, recipe, world)
            row = {"arm": arm, "cut": cut, "checkpoint_read_hash_decode": prep_start-t,
                   "checkpoint_preprocess": perf_counter()-prep_start, "compute_prefix": {}, "mask_to_id_lists": {}}
            values = {}
            for method in METHODS:
                masks, times, packing = predict(pre, method)
                values[method] = masks
                row["compute_prefix"][method] = times
                row["mask_to_id_lists"][method] = packing
            for horizon in HORIZONS:
                result["queries"].append({"arm": arm, "cut": cut, "horizon": horizon, "eligible": len(pre["ids"]),
                                          "initially_burning": pre["burning"], "fixed_graph": pre["fixed_graph"],
                                          "unknown_prior_offers": sum(pre["unknown"][:horizon]),
                                          "certified": {m: values[m][horizon] for m in METHODS}})
            costs["cuts"].append(row)
    write_start = perf_counter()
    args.output.write_bytes(gzip.compress(data_bytes(result), compresslevel=6, mtime=0))
    costs["combined_evidence_json_gzip_write"] = perf_counter()-write_start
    costs["total_until_prediction_written"] = perf_counter()-start
    args.costs.write_text(json.dumps(costs, indent=2) + "\n", encoding="utf8")
    print(f"{len(result['queries'])} causal predictions written to {args.output}")


if __name__ == "__main__":
    main()

