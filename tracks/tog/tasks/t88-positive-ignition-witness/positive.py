"""Return causal positive ignition witnesses on the pinned T87 exterior shells."""
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


def graph_lower(recipients, donors, radius, rate_dt):
    """Bound surviving donors' native kernel contributions from below."""
    total = np.zeros(len(recipients))
    writes = np.zeros(len(recipients), dtype=int)
    if not len(recipients) or not len(donors):
        return total, writes
    keys, inverse = np.unique(np.floor(donors/radius).astype(int), axis=0, return_inverse=True)
    region_lo, region_hi = recipients.min(axis=0), recipients.max(axis=0)
    pad = bounds.GEOM_PAD
    for k in range(len(keys)):
        group = donors[inverse == k]
        lo, hi = group.min(axis=0)-radius, group.max(axis=0)+radius
        if np.any(lo > region_hi) or np.any(hi < region_lo):
            continue
        ids = np.flatnonzero(np.all((recipients >= lo) & (recipients <= hi), axis=1))
        diff = recipients[ids, None, :] - group[None, :, :]
        # Source coordinates from pinned float32 vertices, promoted to doubles.
        # Increase distances, decrease upward bias, and drop borderline donors.
        distance = np.sqrt(np.sum(diff*diff, axis=2)) + pad
        weight = np.maximum(0, 1 - distance/radius)
        bias = 1 + 2.2*np.maximum(0, (diff[:, :, 1]-pad)/radius)
        total[ids] += np.sum(weight*bias, axis=1)*rate_dt
        writes[ids] += np.count_nonzero(weight, axis=1)
    return total/bounds.REDUCTION_UP, writes


def decay_native(heat, dt):
    # JS binary64 multiplication before the float32 store. Round-to-nearest is
    # monotone, hence a rounded result on a lower input is still a lower bound.
    return (heat*(1-dt*.35)).astype(np.float32).astype(float)


def first_witness(ids, lower, threshold, frame):
    hits = np.flatnonzero((lower > 0) & (lower >= threshold))
    if len(hits):
        return {"id": int(ids[hits[0]]), "deadline": frame, "heat_lower": float(lower[hits[0]])}
    return None


def current_scan(snap, shell):
    state, fuel, heat = (snap[k] for k in ("state", "fuel", "heat"))
    ids = np.asarray([i for i in shell if state[i] == 0 and fuel[i] > 0], dtype=int)
    scanned = decay_native(np.asarray([heat[i] for i in ids]), snap["dt"])
    witness = first_witness(ids, scanned, snap["params"]["spreadIgnH"], snap["frame"]+1)
    return ids, scanned, witness


def remaining_scans(snap, source, ids, scanned, horizon):
    p, dt = snap["params"], snap["dt"]
    cap = p["spreadFrontierCap"]
    prefix = np.asarray(snap["frontier"][:cap], dtype=int)
    fuel = np.asarray([snap["fuel"][i] for i in prefix])
    # The last needed donor service is at step H-1, preceding the final scan.
    # A surviving original prefix donor cannot move beyond its original rank.
    # Take the slightly stronger survival test through H-1 complete clocks.
    for _ in range(horizon-1):
        fuel = (fuel-dt/p["spreadBurnT"]).astype(np.float32).astype(float)
    donors = prefix[fuel > 0]
    total, n = graph_lower(source[ids], source[donors], p["spreadR"], dt*p["spreadRate"])
    for step in range(2, horizon+1):
        # Omitting other nonnegative additions lowers a round-to-nearest sum.
        # Each retained store loses at most u relative and a subnormal allowance.
        # Subtracting a tiny amount also covers the binary64 sum's conversion.
        factor = 1 - (n+1)*bounds.U32
        lower = np.maximum(0, (scanned + total - (n+1)*bounds.TINY32)*factor)
        scanned = decay_native(lower, dt)
        witness = first_witness(ids, scanned, p["spreadIgnH"], snap["frame"]+step)
        if witness is not None:
            return witness, len(donors)
    return None, len(donors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path, default=HERE.parents[4]/"real-asset-ingest/foreground.ply")
    parser.add_argument("--input-dir", type=Path, default=T86/"local")
    args = parser.parse_args()
    start = perf_counter()
    pins = bounds.geometry
    identities = {}
    recipe = json.loads(pins.checked(pins.RECIPE, pins.RECIPE_SHA, identities))
    source = pins.centers(pins.checked(args.asset, pins.ASSET_SHA, identities))
    world = source - np.asarray(recipe["source_center"])
    world[:, 1] += recipe["params"]["sceneLift"]
    shell = {}
    for arm, pick in zip(bounds.ARMS, [recipe["picks"][1], recipe["picks"][0]]):
        d2 = np.sum((world-np.array(pick["world"]))**2, axis=1)
        shell[arm] = np.flatnonzero((d2 > pick["radius"]**2)
                                    & (d2 <= (pick["radius"]+recipe["params"]["spreadIgnR"])**2)).tolist()
    costs = {"unit": "seconds", "shared_geometry_two_shells": perf_counter()-start, "cuts": [], "queries": []}
    result = {"inputs":identities, "shell_ids":shell, "queries":[]}
    for arm in bounds.ARMS:
        for cut in bounds.CUTS:
            t = perf_counter()
            path = args.input_dir/f"{arm}-{cut}.json.gz"
            raw = path.read_bytes()
            identities[path.name] = hashlib.sha256(raw).hexdigest()
            snap = json.loads(gzip.decompress(raw))
            bounds.require((snap["arm"],snap["frame"],snap["dt"]) == (arm,cut,recipe["dt"]), "cut identity")
            p = snap["params"]
            for key in ("spreadR","spreadRate","spreadBurnT","spreadIgnH","spreadFrontierCap","sceneYaw",
                        "scenePitch","sceneScale","spreadClockMode","spreadMeasureMode","spreadOn"):
                bounds.require(p[key] == recipe["params"][key], "unsupported control")
            costs["cuts"].append({"arm":arm,"cut":cut,"read_hash_decode_validate":perf_counter()-t})
            for h in bounds.HORIZONS:
                t = perf_counter()
                ids, scanned, simple = current_scan(snap, shell[arm])
                mid = perf_counter()
                candidate, used = simple, None
                if simple is None and h > 1 and len(ids):
                    candidate, used = remaining_scans(snap, source, ids, scanned, h)
                end = perf_counter()
                result["queries"].append({"arm":arm, "cut":cut, "horizon":h, "eligible":len(ids),
                                          "residual":simple, "graph":candidate, "graph_donors_used":used})
                costs["queries"].append({"arm":arm, "cut":cut, "horizon":h,
                                         "prepare_roi_and_residual":mid-t, "graph_extra":end-mid})
    t = perf_counter()
    (HERE/"PREDICTIONS.json.gz").write_bytes(gzip.compress(bounds.data_bytes(result),compresslevel=6,mtime=0))
    costs["combined_evidence_json_gzip_write"] = perf_counter()-t
    costs["whole_batch_to_predictions"] = perf_counter()-start
    (HERE/"COSTS.json").write_text(json.dumps(costs,indent=2)+"\n",encoding="utf8")
    print(f"Wrote {len(result['queries'])} retrospective positive-witness queries.")


if __name__ == "__main__":
    main()
