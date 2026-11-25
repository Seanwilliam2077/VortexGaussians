"""Run the frozen thermal bounds on shell recipients before loading any reference events."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

HERE = Path(__file__).resolve().parent
T86 = HERE.parent / "t86-ignition-margin"
sys.dont_write_bytecode = True
sys.path.insert(0, str(T86))
import predict as bounds

METHODS = ("support", "uniform", "weighted")


def graph(recipients, donors, radius, rate_dt):
    """Native same-space additive kernel, computed only at requested, eligible IDs."""
    deposit = np.zeros(len(recipients))
    writes = np.zeros(len(recipients), dtype=int)
    if not len(recipients):
        return deposit, writes
    # The same donor groups and summation order as T86. Skip groups wholly
    # outside the region's bounding box before forming any recipient pairs.
    keys, inverse = np.unique(np.floor(donors / radius).astype(int), axis=0, return_inverse=True)
    lower, upper = recipients.min(axis=0), recipients.max(axis=0)
    pad = radius + bounds.GEOM_PAD
    for k in range(len(keys)):
        group = donors[inverse == k]
        a, b = group.min(axis=0)-pad, group.max(axis=0)+pad
        if np.any(a > upper) or np.any(b < lower):
            continue
        ids = np.flatnonzero(np.all((recipients >= a) & (recipients <= b), axis=1))
        diff = recipients[ids, None, :] - group[None, :, :]
        distance = np.maximum(0, np.sqrt(np.sum(diff*diff, axis=2)) - bounds.GEOM_PAD)
        fraction = np.maximum(0, 1 - distance/radius)
        bias = 1 + 2.2*np.maximum(0, (diff[:, :, 1] + bounds.GEOM_PAD)/radius)
        deposit[ids] += np.sum(fraction*bias, axis=1)*rate_dt
        writes[ids] += np.count_nonzero(fraction, axis=1)
    return deposit, writes


def prepare(cut, world, layer_ids, shell, horizon):
    # The exact cut bytes and controls are pinned to T86. Gas and donor sources
    # remain global because either can affect a recipient across the shell.
    p, dt = cut["params"], cut["dt"]
    state, fuel, heat = (np.asarray(cut[k]) for k in ("state", "fuel", "heat"))
    ids = shell[(state[shell] == 0) & (fuel[shell] > 0)]
    recipients = world[ids]
    frontier = np.asarray(cut["frontier"], dtype=int)
    alive = fuel[frontier].astype(float)
    for _ in range(horizon):
        alive = (alive - dt/p["spreadBurnT"]).astype(np.float32).astype(float)
    cap = p["spreadFrontierCap"]
    fixed_graph = len(frontier) >= cap and np.all(alive[:cap] > 0)
    if horizon == 1:
        graph_heat, graph_n = np.zeros(len(ids)), np.zeros(len(ids), dtype=int)
    elif fixed_graph:
        graph_heat, graph_n = graph(recipients, world[frontier[:cap]], p["spreadR"], dt*p["spreadRate"])
    else:
        graph_n = np.full(len(ids), cap, dtype=int)
        graph_heat = graph_n * dt * p["spreadRate"] * (3.2 + bounds.GEOM_PAD)
    xy, layers, temp = [], [], []
    for layer in cut["gas"]:
        for particle in layer["particles"]:
            if particle["T"] >= .55:
                xy.append((particle["x"], particle["y"]))
                layers.append(layer["idx"])
                temp.append(particle["T"])
    cohorts = [bounds.groups(np.asarray(xy), layers, temp, False)]
    unknown = [0]
    cursor, n = cut["emit_cursor"], p["spreadFeedCap"]
    stable = np.all(alive > 0) and len(frontier) >= n
    for _ in range(1, horizon):
        known = min(n, max(0, len(frontier)-1-cursor)) if stable else 0
        offers = frontier[cursor+1:cursor+1+known]
        cohorts.append(bounds.groups(world[offers, :2], layer_ids[offers], np.ones(len(offers)), True))
        unknown.append(n-known)
        cursor += n
    return {"p": p, "dt": dt, "ids": ids, "world": recipients, "heat": heat[ids],
            "graph": graph_heat, "graph_n": graph_n, "cohorts": cohorts, "unknown": unknown}


def predict(pre, method, horizon):
    p, dt = pre["p"], pre["dt"]
    w = pre["world"]
    upper = pre["heat"].copy()
    safe = np.ones(len(upper), dtype=bool)
    slabs = []
    for layer in range(p["layers"]):
        z = (layer/(p["layers"]-1) - .5) * p["sliceDepth"]
        member = np.flatnonzero(np.abs(w[:, 2] - z) <= p["spreadIgnR"] + bounds.GEOM_PAD)
        ids = member[np.argsort(w[member, 0], kind="stable")]
        slabs.append((ids, w[ids, 0], np.abs(w[ids, 2]-z)))
    for step in range(1, horizon+1):
        flame, writes = bounds.flame_bound(pre, step, method, slabs)
        if method == "support":
            safe &= writes == 0
        before_decay = bounds.upward_sum(upper, flame * (dt*p["spreadHeat"]), writes)
        scanned = bounds.upward_sum(np.zeros(len(upper)), before_decay*(1-dt*.35), 1)
        safe &= scanned < p["spreadIgnH"]
        if step < horizon:
            upper = bounds.upward_sum(scanned, pre["graph"], pre["graph_n"])
    return pre["ids"][safe].tolist()


def argv():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=T86/"local")
    parser.add_argument("--asset", type=Path, default=HERE.parents[4]/"real-asset-ingest/foreground.ply")
    return parser.parse_args()


def main():
    args = argv()
    start = perf_counter()
    pinned = bounds.geometry
    identities = {}
    recipe = json.loads(pinned.checked(pinned.RECIPE, pinned.RECIPE_SHA, identities))
    world = pinned.centers(pinned.checked(args.asset, pinned.ASSET_SHA, identities))
    world -= np.asarray(recipe["source_center"])
    world[:, 1] += recipe["params"]["sceneLift"]
    num_layers, depth = recipe["params"]["layers"], recipe["params"]["sliceDepth"]
    layer_ids = np.clip(np.floor((world[:, 2]/depth+.5)*(num_layers-1)+.5), 0, num_layers-1).astype(int)
    shell = {}
    for arm, pick in zip(bounds.ARMS, [recipe["picks"][1], recipe["picks"][0]]):
        d2 = np.sum((world-np.array(pick["world"]))**2, axis=1)
        r = pick["radius"]
        shell[arm] = np.flatnonzero((d2 > r*r) & (d2 <= (r+recipe["params"]["spreadIgnR"])**2))
    costs = {"unit": "seconds", "shared_asset_transform_and_two_shells": perf_counter()-start, "cuts": [],
             "queries": []}
    predictions = {"inputs": identities, "shell_ids": {a:s.tolist() for a,s in shell.items()}, "queries": []}
    for arm in bounds.ARMS:
        for cut in bounds.CUTS:
            t = perf_counter()
            path = args.input_dir/f"{arm}-{cut}.json.gz"
            raw = path.read_bytes()
            identities[path.name] = hashlib.sha256(raw).hexdigest()
            snapshot = json.loads(gzip.decompress(raw))
            bounds.require((snapshot["arm"], snapshot["frame"]) == (arm,cut), "cut identity")
            costs["cuts"].append({"arm": arm, "cut": cut, "read_hash_decode": perf_counter()-t})
            for h in bounds.HORIZONS:
                t = perf_counter()
                pre = prepare(snapshot, world, layer_ids, shell[arm], h)
                timing = {"arm":arm, "cut":cut, "horizon":h, "prepare":perf_counter()-t, "method":{}}
                row = {"arm":arm, "cut":cut, "horizon":h, "eligible":pre["ids"].tolist(), "certified":{}}
                for method in METHODS:
                    t = perf_counter()
                    row["certified"][method] = predict(pre, method, h)
                    timing["method"][method] = perf_counter()-t
                predictions["queries"].append(row)
                costs["queries"].append(timing)
    t = perf_counter()
    (HERE/"PREDICTIONS.json.gz").write_bytes(gzip.compress(bounds.data_bytes(predictions), compresslevel=6, mtime=0))
    costs["combined_evidence_json_gzip_write"] = perf_counter()-t
    costs["whole_batch_to_predictions"] = perf_counter()-start
    (HERE/"COSTS.json").write_text(json.dumps(costs, indent=2)+"\n", encoding="utf8")
    print(f"Published {len(predictions['queries'])} region-only causal answers.")


if __name__ == "__main__":
    main()

