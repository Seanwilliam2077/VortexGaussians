"""Check cross-stroke transport using a lighter sibling's independently archived onset ledger."""
import gzip
import hashlib
import json
import math
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASKS = HERE.parent


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def digest(frontier):
    return hashlib.sha256(b"".join(struct.pack("<I", i) for i in frontier)).hexdigest()


def parent_service_length(parent, params, dt):
    n, cursor = parent["burning"], parent["cursor"]
    graph, quota = params["spreadFrontierCap"], params["spreadFeedCap"]
    assert (graph, quota) == (1400, 48)
    assert params["spreadMeasureMode"] == "legacy" and params["spreadClockMode"] == "elapsed"
    assert dt == 1 / 60 and params["spreadBurnT"] == 6
    assert n >= max(graph, quota) and parent["charred"] == 0
    available = min(90, (n - 1 - cursor) // quota)
    # Starting at frame zero is the worst possible age of any unit-fuel parent site.
    fuel = 1.
    for _ in range(parent["frame"] + available):
        fuel = struct.unpack("<f", struct.pack("<f", fuel - dt / params["spreadBurnT"]))[0]
    assert fuel > 0
    return available, fuel


def predict(scene):
    native = scene / "evidence/native"
    cfg = read(scene / "recipe.json")
    capture = read(native / "capture-report.json")
    assert capture["status"] == "validated" and not capture["errors"]
    light, full = (capture["shots"][arm] for arm in ("AL", "AF"))
    parent = light["pre_edit"]
    assert parent == full["pre_edit"] and light["initial"] == full["initial"]
    for branch in (light, full):
        for key in ("frame", "particle_hash", "gas_count", "random_draws", "cursor"):
            assert branch["post_edit"][key] == parent[key]
    k, fuel = parent_service_length(parent, cfg["params"], cfg["dt"])
    start = parent["frame"]
    light_trace = read(native / "AL-trace.json.gz")
    base_order = list(light["initial"]["ids"])
    for row in light_trace[:start]:
        assert not row["retired"]
        base_order.extend(row["new_ids"])
    assert len(set(base_order)) == len(base_order) == parent["burning"]
    l_ids, f_ids = light["edit"]["ids"], full["edit"]["ids"]
    extra = set(f_ids) - set(l_ids)
    assert extra and set(l_ids) < set(f_ids) and set(base_order).isdisjoint(f_ids)
    shell = set(read(scene / "shell.json.gz")) - set(base_order)
    assert shell.isdisjoint(f_ids)
    baseline = base_order + f_ids
    assert len(baseline) == full["post_edit"]["burning"]
    records = []
    for row in light_trace[start:start+k]:
        assert not row["retired"]
        events = [i for i in row["new_ids"] if i not in extra]
        baseline.extend(events)
        records.append(dict(frame=row["frame"], events=events, active=len(baseline),
                            gas=row["gas_count"], draws=row["random_draws"],
                            frontier=digest(baseline), suppressed=len(row["new_ids"])-len(events)))
    return records, base_order + f_ids, shell, k, len(extra), fuel


def verify(scene, records, full_initial, shell, k, extra_sites, final_min_fuel):
    full_trace = read(scene / "evidence/native/AF-trace.json.gz")
    reference = read(scene / "REFERENCE.json")
    cams = sorted({q["camera"] for q in reference["queries"]})
    curves = {(q["arm"], q["camera"]): q for q in reference["queries"]}
    weights = {}
    for cam in cams:
        source = TASKS / "t107-visible-burn-progression/evidence" if scene.name.startswith("t109") else scene
        raw = dict(read(source / f"weights-{cam}.json.gz")["eligible_weights"])
        weights[cam] = {i: math.floor(raw[i] * 1e6 + .5) for i in shell}
    frontier = full_initial.copy()
    count = 0
    mass = dict.fromkeys(cams, 0)
    for offset, (prediction, truth) in enumerate(zip(records, full_trace[180:180+k], strict=True)):
        assert prediction["frame"] == truth["frame"] and not truth["retired"]
        assert prediction["events"] == truth["new_ids"]
        frontier.extend(truth["new_ids"])
        assert prediction["frontier"] == digest(frontier)
        assert (prediction["active"], prediction["gas"], prediction["draws"]) == (
            truth["active_count"], truth["gas_count"], truth["random_draws"])
        newly = shell.intersection(prediction["events"])
        count += len(newly)
        for cam in cams:
            mass[cam] += sum(weights[cam][i] for i in newly)
            curve_row = [prediction["frame"], len(newly), count, mass[cam]]
            assert curves["AL",cam]["curve"][offset] == curves["AF",cam]["curve"][offset] == curve_row
    def duration(q):
        return 90 if q["first_frame"] is None else q["first_frame"] - 180
    budgets = []
    for views in [[cams[0]], [cams[1]], cams]:
        first = max(duration(curves["AL",c]) for c in views)
        unresolved = [c for c in views if curves["AL",c]["first_frame"] is None]
        second = max((duration(curves["AF",c]) for c in unresolved), default=0)
        reusable = min(first,second,k)
        budgets.append(dict(views=views, light_steps=first, full_steps=second,
                            potentially_reused_steps=reusable,
                            share_of_executed_steps=reusable/(first+second),
                            unneeded_sibling_checkpoint=second==0))
    return dict(certified_steps=k, extra_direct_sites=extra_sites,
                worst_case_unit_fuel_after_prefix=final_min_fuel,
                suppressed_light_births=sum(r["suppressed"] for r in records),
                remaining_frontier_digest=records[-1]["frontier"],
                prefix_eligible_births=count, actions=budgets)


def main():
    scores = {}
    for name in ("t109-common-parent-choice", "t111-playground-shot-choice"):
        scene = TASKS / name
        # Construct the predictions before loading the larger brush's independent future.
        predictions = predict(scene)
        scores[name] = verify(scene, *predictions)
    assert any(a["potentially_reused_steps"] >= 10 for s in scores.values() for a in s["actions"])
    encoded = json.dumps(scores, indent=2) + "\n"
    out = HERE / "RESULTS.json"
    if out.exists():
        assert json.loads(out.read_text()) == scores
    else:
        out.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    main()
