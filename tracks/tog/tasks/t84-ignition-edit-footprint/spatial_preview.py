"""Score two ordinary previews of a second ignition on the recorded Firewoods take."""
import argparse
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import time

import numpy as np


TASK = Path(__file__).resolve().parent
TASKS = TASK.parent
PUBLIC = TASKS / "t81-firewoods-capacity-causality/public"
RECIPE = TASKS / "t42-firewoods-sequential-workflow/recipe.json"
N = 34687
ASSET_SHA = "906460f162f704b89666b159ae5b4744e53e6dc11baf448a550de581506919b0"
RECIPE_SHA = "982c98d3187ab26e95e251de562950adaab9a2101d1f1ff6371c93e7f6383013"
MANIFEST_SHA = "321229c577bf28dec45fc72b9c190bebe7c49dfb0e3f48b2fc21f28d9eaa1965"
POLICIES = ("per-layer", "global")


def checked(path, sha, identities):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha:
        raise ValueError(f"Different input bytes for {path.name}")
    identities[path.name] = sha
    return data


def centers(ply):
    """Read the pinned binary little-endian float-only foreground file in vertex order."""
    stream = io.BytesIO(ply)
    header = []
    while True:
        line = stream.readline()
        if not line:
            raise ValueError("Missing PLY header terminator")
        token = line.decode("ascii").strip()
        if token == "end_header":
            break
        header.append(token)
    if header[:3] != ["ply", "format binary_little_endian 1.0", f"element vertex {N}"]:
        raise ValueError("Unexpected pinned PLY layout")
    fields = []
    for prop in header[3:]:
        kind, fmt, name = prop.split()
        if (kind, fmt) != ("property", "float"):
            raise ValueError(prop)
        fields.append(name)
    values = np.frombuffer(ply, dtype="<f4", offset=stream.tell()).reshape(N, len(fields))
    return values[:, [fields.index(k) for k in ("x", "y", "z")]].astype("float64")


def read_state(name, locked, identities):
    raw = checked(PUBLIC / name, locked[name], identities)
    snap = json.loads(gzip.decompress(raw))
    columns = snap["material_columns"]
    states = np.zeros(N, dtype=np.int8)
    fuel = np.zeros(N)
    seen = np.zeros(N, dtype=bool)
    i_col, s_col, f_col = map(columns.index, ("id", "state", "fuel"))
    for row in snap["material_rows"]:
        label = row[i_col]
        index = int(label.split(":")[1])
        if not 0 <= index < N or label != f"ply:{index}" or seen[index]:
            raise ValueError("Invalid material identity")
        seen[index] = True
        if row[s_col] not in (0, 1, 2):
            raise ValueError("Unknown material state")
        states[index], fuel[index] = row[s_col], row[f_col]
    if not np.all(seen):
        raise ValueError("Incomplete material identities")
    return states, fuel


def support_scores(world, direct, depth, layers):
    """Squared distance to nearest direct-B center or its upward half-line at layer depth."""
    sources = world[direct]
    layer_id = np.clip(np.floor((sources[:, 2] / depth + 0.5) * (layers - 1) + 0.5), 0, layers - 1)
    layer_z = (layer_id / (layers - 1) - 0.5) * depth
    radial = np.empty(N)
    up = np.empty(N)
    for start in range(0, N, 256):
        seg = slice(start, min(N, start + 256))
        dx2 = (world[seg, 0, None] - sources[:, 0]) ** 2
        dy = world[seg, 1, None] - sources[:, 1]
        radial[seg] = np.min(dx2 + dy ** 2 + (world[seg, 2, None] - sources[:, 2]) ** 2, axis=1)
        up[seg] = np.min(dx2 + np.minimum(dy, 0) ** 2 + (world[seg, 2, None] - layer_z) ** 2, axis=1)
    return {"radial": radial, "upward_half_line": up}


def counts(tp, fp, fn):
    tp, fp, fn = map(int, (tp, fp, fn))
    union = tp + fn + fp
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "iou": tp / union if union else 1.0}


def measure(predicted, labels):
    return counts(np.sum(predicted & labels), np.sum(predicted & ~labels), np.sum(~predicted & labels))


def best_threshold(distances, labels):
    """Maximum spill IoU over every rank prefix including whole distance ties and empty prefix."""
    order = np.argsort(distances, kind="stable")
    sorted_d, sorted_l = distances[order], labels[order]
    ends = np.flatnonzero(np.r_[sorted_d[:-1] != sorted_d[1:], True]) if len(sorted_d) else np.array([], dtype=int)
    total = int(np.sum(labels))
    best = {"distance": None, **counts(0, 0, total)}
    lower, upper = (0, total) if total else (1, 1)
    cumulative = np.cumsum(sorted_l, dtype=np.int64)
    for end in ends:
        tp = int(cumulative[end])
        fp = int(end + 1 - tp)
        union = total + fp
        if tp * upper > lower * union:
            lower, upper = tp, union
            best = {"distance": math.sqrt(float(sorted_d[end])), **counts(tp, fp, total - tp)}
    return best


def evaluate(asset):
    costs = {}
    begin = time.perf_counter()
    identities = {}
    recipe = json.loads(checked(RECIPE, RECIPE_SHA, identities))
    manifest = json.loads(checked(PUBLIC / "MANIFEST.json", MANIFEST_SHA, identities))
    locked = {row["file"]: row["sha256"] for row in manifest["files"]}
    source = centers(checked(asset, ASSET_SHA, identities))
    params = recipe["params"]
    if [params[k] for k in ("sceneScale", "sceneYaw", "scenePitch", "sceneOffX", "sceneOffZ")] != [1, 0, 0, 0, 0]:
        raise ValueError("Expected frozen unit placement")
    world = source - np.array(recipe["source_center"]) + np.array([0, params["sceneLift"], 0])
    pick = recipe["picks"][1]
    if not np.array_equal(source[pick["index"]], pick["source"]) or not np.allclose(world[pick["index"]], pick["world"], rtol=0, atol=1e-14):
        raise ValueError("B anchor position mismatch")
    prefix_state, prefix_fuel = read_state("global-A-prefix.dynamic.json.gz", locked, identities)
    sphere = np.sum((source - source[pick["index"]]) ** 2, axis=1) <= pick["radius"] ** 2
    if set(np.flatnonzero(sphere)) != set(pick["initial_geometric_neighbors"]):
        raise ValueError("Radius query differs from fixed B sphere")
    direct = sphere & (prefix_state == 0) & (prefix_fuel > 0)
    cached = {p: read_state(p + "-A-endpoint.dynamic.json.gz", locked, identities)[0] != 0 for p in POLICIES}
    costs["immutable_inputs_and_cache_decode_s"] = time.perf_counter() - begin
    t = time.perf_counter()
    rankings = support_scores(world, direct, params["sliceDepth"], params["layers"])
    radius = params["spreadIgnR"]
    predictions = {"direct_overlay": direct, **{k: direct | (v <= radius ** 2) for k, v in rankings.items()}}
    domain = {p: ~a & ~direct for p, a in cached.items()}
    costs["rankings_and_masks_s"] = time.perf_counter() - t

    # Only the evaluator below can inspect edited endpoints. Predictions are complete here.
    t = time.perf_counter()
    arms = {}
    for policy, prior in cached.items():
        target = read_state(policy + "-AB-endpoint.dynamic.json.gz", locked, identities)[0] != 0
        spill = domain[policy]
        targets = target[spill]
        gained, lost = target & ~prior, prior & ~target
        arms[policy] = {
            "gained": int(gained.sum()), "lost": int(lost.sum()), "direct_gained": int((direct & gained).sum()),
            "outside_direct_candidates": int(spill.sum()), "outside_direct_gain": int(targets.sum()),
            "outside_direct_lost": int((lost & ~direct).sum()),
            "fixed_spill": {k: measure(p[spill], targets) for k, p in predictions.items()},
            "fixed_all_gain": {k: measure(p & ~prior, gained) for k, p in predictions.items()},
            "retrospective_best_spill_iou": {k: best_threshold(d[spill], targets) for k, d in rankings.items()}}
    costs["edited_endpoint_scoring_and_oracles_s"] = time.perf_counter() - t
    result = {"reference": "Fixed seed 11, frame 360 material state > 0; paired total edit effect within each policy",
              "prediction": "Union of direct B hits and fixed geometric support, over cached A-only endpoint",
              "radius_world": radius, "direct_B_ids_count": int(direct.sum()), "policies": arms,
              "nulls": "Undefined precision/recall is null; empty-empty IoU is one. Null oracle distance selects no additions.",
              "oracle": "Diagnostic best closed-distance threshold at whole ties for spill only; ties in IoU choose smallest selected set.",
              "input_sha256": identities}
    costs["whole_evaluate_s"] = time.perf_counter() - begin
    return result, costs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path, default=TASK.parents[4] / "real-asset-ingest/foreground.ply")
    args = parser.parse_args()
    result, times = evaluate(args.asset)
    encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
    out = TASK / "SPATIAL.json"
    if out.exists() and out.read_text(encoding="utf-8") != encoded:
        raise RuntimeError("Existing SPATIAL.json has different content")
    if not out.exists():
        with out.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(encoded)
    print(json.dumps({"written_or_verified": out.name, "costs_s": times, "numpy": np.__version__}))
