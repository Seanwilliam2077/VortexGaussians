"""Check a frozen T85 edited-prefix prediction against the T81 observed edited data."""
import gzip
import hashlib
import json
from pathlib import Path
import time


HERE = Path(__file__).resolve().parent
PUBLIC = HERE.parent / "t81-firewoods-capacity-causality/public"
MANIFEST_SHA256 = "321229c577bf28dec45fc72b9c190bebe7c49dfb0e3f48b2fc21f28d9eaa1965"
START, END = 180, 360


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    return sha(json.dumps(value, separators=(",", ":"), allow_nan=False).encode())


def arm_reader(arm, locked, identities):
    def read(suffix):
        filename = f"{arm}-{suffix}"
        item = locked[filename]
        raw = (PUBLIC / filename).read_bytes()
        require(len(raw) == item["bytes"] and sha(raw) == item["sha256"], filename)
        decoded = gzip.decompress(raw)
        require(len(decoded) == item["decoded_bytes"] and sha(decoded) == item["decoded_sha256"], filename)
        identities[filename] = sha(raw)
        return decoded
    return read


def load_reference(arm, locked, identities):
    read = arm_reader(arm, locked, identities)
    after = json.loads(read("after-intervention.dynamic.json.gz"))
    end = json.loads(read("endpoint.dynamic.json.gz"))
    rows = [json.loads(line) for line in read("steps.jsonl.gz").splitlines()]
    require([r["frame"] for r in rows] == list(range(1, END + 1)), arm + " step sequence")
    for state, frame in [(after, START), (end, END)]:
        require(state["frame"] == frame and state["seed"] == 11, arm + " checkpoint controls")
        states = {int(r[0].removeprefix("ply:")): (r[2], r[6]) for r in state["material_rows"]}
        require(state["material_columns"] == ["id","fuelInitial","fuel","heat","char","glow","state"], "material schema")
        require(len(state["material_rows"]) == len(states) == 34687, "material IDs")
        require(all(fuel > 0 and phase in (0, 1) for fuel, phase in states.values()), "retirement or unsupported state")
        require(set(state["frontier"]) == {i for i, (_, phase) in states.items() if phase == 1}
                and len(set(state["frontier"])) == len(state["frontier"]), "unique endpoint frontier members")
    order = end["frontier"]
    previous = len(after["frontier"])
    require(order[:previous] == after["frontier"], arm + " append order")
    prior_clock = after["counters"]["clockProcessed"]
    require(prior_clock == rows[START - 1]["counters"]["clockProcessed"], "initial clock")
    counts = {START: previous}
    for row in rows[START:]:
        clock = row["counters"]["clockProcessed"]
        count = clock - prior_clock
        require(previous <= count <= len(order), "monotone append-only active frontier")
        require(order[previous:count] == sorted(order[previous:count]), "native material ignition scan order")
        counts[row["frame"]] = count
        previous, prior_clock = count, clock
    require(previous == len(order), "end frontier length")
    return {"rows": rows, "after": after, "end": end, "order": order, "counts": counts}


def active(ref, frame):
    return set(ref["order"][:ref["counts"][frame]])


def verify_claims(claim, cached, observed):
    complete = claim["complete_steps"]
    unresolved = claim["first_unresolved"]
    require(0 <= complete <= END - START, "invalid complete step count")
    require((unresolved is None) == (complete == END - START), "unresolved/complete disagreement")
    if unresolved:
        require(unresolved["frame"] == START + complete + 1, "nonconsecutive first unresolved frame")
    expected = list(range(START + 1, START + complete + 1 + int(unresolved is not None)))
    require([c["frame"] for c in claim["rows"]] == expected, "predicted row sequence")
    offer_count = 0
    mismatches = []
    for c in claim["rows"]:
        frame = c["frame"]
        cached_row = cached["rows"][frame - 1]
        observed_row = observed["rows"][frame - 1]
        offers = observed_row["offers"]
        certified = c["certified_offers"]
        expected_n = len(offers)
        if unresolved and frame == unresolved["frame"]:
            expected_n = unresolved["slot_zero_based"]
            require(0 <= expected_n < len(offers), "unresolved slot")
            oa, ob = cached_row["offers"][expected_n], offers[expected_n]
            require((unresolved["cached_source"], unresolved["edited_source"], unresolved["cached_outcome"])
                    == (oa[0], ob[0], oa[6]), "unresolved saved source IDs and cached outcome")
            if oa[5] != ob[5]:
                expected_reason = "capacity decision changes the random stream"
            else:
                require(oa[6] == ob[6] == "emitted" and oa[0] != ob[0], "unresolved birth support")
                expected_reason = "accepted birth has a different source ID"
            require(unresolved["reason"] == expected_reason, "unresolved reason vs observed predicates")
        require(certified == expected_n, "certified prefix length")
        actual_active = digest(sorted(active(observed, frame)))
        actual_offers = digest([[o[0], o[1], o[6]] for o in offers[:certified]])
        for key, actual in [("active_sha256", actual_active), ("offers_sha256", actual_offers)]:
            if c[key] != actual:
                mismatches.append({"frame": frame, "field": key, "predicted": c[key], "observed": actual})
        for slot, (oa, ob) in enumerate(zip(cached_row["offers"][:certified], offers[:certified])):
            # Rejected offers can differ in source/layer. A successful birth must carry the same
            # identity and source/layer for this conservative certificate.
            if oa[6] != ob[6] or (oa[6] == "emitted" and (oa[:2], oa[7]) != (ob[:2], ob[7])):
                mismatches.append({"frame": frame, "slot_zero_based": slot, "field": "cached gas admission effect"})
        if frame <= START + complete:
            for key in ("layerCounts", "nativeRemovedIds", "randomDrawsThisStep", "randomDraws"):
                if cached_row[key] != observed_row[key]:
                    mismatches.append({"frame": frame, "field": key, "cached": cached_row[key], "edited": observed_row[key]})
        offer_count += certified
    for tag in (("after", "end") if complete == END - START else ("after",)):
        if kinetics(cached[tag]) != kinetics(observed[tag]) or cached[tag]["random_draws"] != observed[tag]["random_draws"]:
            mismatches.append({"checkpoint": tag, "field": "native gas arrays/layer clocks or RNG count"})
    strict = claim["strict_complete_steps"]
    require(0 <= strict <= complete, "strict vs guarded prefix lengths")
    timing = {}
    for label, n in [("guarded_complete", complete), ("strict_complete", strict)]:
        suffix = observed["rows"][START:START + n]
        timing[label] = {"steps": n, **{key: sum(row["timing"][key] for row in suffix)
                                        for key in ("step_including_hooks_ms", "step_plus_render_ms")}}
    return {"complete_steps": complete, "first_unresolved": unresolved, "active_frame_checks": len(expected),
            "original_edited_arm_timing": timing,
            "ordered_offer_triples_checked": offer_count, "mismatches": mismatches}


def kinetics(state):
    # Observation WeakMap labels encode provenance. Compare layer ordering and all native particle fields separately.
    return [{"idx": layer["idx"], "seed": layer["seed"], "t": layer["t"], "acc": layer["acc"],
             "particles": [p["native"] for p in layer["particles"]]} for layer in state["gas"]]


def pair_diagnostics(a, ab):
    direct = set(ab["after"]["newly_B_indices"])
    require(not a["after"]["newly_B_indices"] and len(direct) == 288, "zero-time direct edit")
    first = {}
    observed_names = ["offer_source_id", "target_layer", "outcome", "emission_descriptor_at_offer",
                      "random_draws_per_frame", "layer_counts", "total_gas_count", "native_removed_ids",
                      "material_overlay_outside_direct"]
    def notice(name, condition, frame, slot=None):
        if condition and name not in first:
            first[name] = {"frame": frame}
            if slot is not None:
                first[name]["slot_zero_based"] = slot

    for frame in range(START, END + 1):
        prior = active(a, frame)
        edited = active(ab, frame)
        diff = (prior ^ edited) - direct
        notice("material_overlay_outside_direct", bool(diff), frame)
        if frame == START:
            continue
        ra, rb = a["rows"][frame - 1], ab["rows"][frame - 1]
        require(len(ra["offers"]) == len(rb["offers"]) == 48, "expected matched offer counts")
        for slot, (oa, ob) in enumerate(zip(ra["offers"], rb["offers"])):
            notice("offer_source_id", oa[0] != ob[0], frame, slot)
            notice("target_layer", oa[1] != ob[1], frame, slot)
            notice("outcome", oa[6] != ob[6], frame, slot)
            da = (oa[0], oa[1]) if oa[6] == "emitted" else None
            db = (ob[0], ob[1]) if ob[6] == "emitted" else None
            notice("emission_descriptor_at_offer", da != db, frame, slot)
        notice("random_draws_per_frame", ra["randomDrawsThisStep"] != rb["randomDrawsThisStep"], frame)
        notice("layer_counts", ra["layerCounts"] != rb["layerCounts"], frame)
        notice("total_gas_count", sum(ra["layerCounts"]) != sum(rb["layerCounts"]), frame)
        notice("native_removed_ids", ra["nativeRemovedIds"] != rb["nativeRemovedIds"], frame)
    material = first.get("material_overlay_outside_direct")
    boundaries = {}
    for key in ("after", "end"):
        left, right = a[key], ab[key]
        boundaries[key] = {"frame": left["frame"], "native_particle_arrays_and_layer_clocks_equal": kinetics(left) == kinetics(right),
                           "A_selected_native_particle_hash": left["original_particle_state_hash"],
                           "AB_selected_native_particle_hash": right["original_particle_state_hash"],
                           "A_rng_draws": left["random_draws"], "AB_rng_draws": right["random_draws"]}
    return {"first_observed_difference": {name: first.get(name) for name in observed_names},
            "observed_outside_direct_material_overlay_exact_through": material["frame"] - 1 if material else END,
            "gas_at_captured_boundaries": boundaries}


def main():
    started = time.perf_counter()
    frozen = (HERE / "PREDICTIONS.json").read_bytes()
    claim = json.loads(frozen)
    manifest = (PUBLIC / "MANIFEST.json").read_bytes()
    require(sha(manifest) == MANIFEST_SHA256, "archive manifest")
    locked = {entry["file"]: entry for entry in json.loads(manifest)["files"]}
    inputs = {}
    checks = {}
    for policy in ("global", "per-layer"):
        a = load_reference(policy + "-A", locked, inputs)
        ab = load_reference(policy + "-AB", locked, inputs)
        predicted = claim["policies"][policy]
        diagnostics = pair_diagnostics(a, ab)
        strict_fork = diagnostics["first_observed_difference"]["offer_source_id"]
        require(predicted["first_strict_source_mismatch"] == strict_fork, "strict control's first changed offer")
        strict_steps = strict_fork["frame"] - START - 1 if strict_fork else END - START
        require(strict_steps == predicted["strict_complete_steps"], "strict control's complete steps")
        checks[policy] = {**verify_claims(predicted, a, ab), **diagnostics}
    passed = all(not result["mismatches"] for result in checks.values())
    result = {"predictions_sha256": sha(frozen), "public_manifest_sha256": MANIFEST_SHA256, "input_sha256": inputs,
              "qualified_saved_comparisons": passed, "policies": checks,
              "limits": "Observed feed descriptors compare source/layer and whether a birth occurred at an ordered slot. Full native gas arrays are available at boundaries. Equal draw counts alone cannot establish equal draw state. Material checks compare burning ID sets, not heat values or the rendered frame."}
    dest = HERE / "CHECK.json"
    output = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if dest.exists():
        require(dest.read_text(encoding="utf-8") == output, "different previous check")
    else:
        with dest.open("x", encoding="utf-8", newline="\n") as f:
            f.write(output)
    print(json.dumps({"passed": passed, "elapsed_s": time.perf_counter() - started, "output": dest.name}))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
