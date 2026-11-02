"""Verify the published T42/T76 handoff with Python's standard library only.

Default: read-only archive, decoded-byte, and T42 projection-schema checks.
Optional: --restore-t76-to NEW_DIRECTORY restores only the 23 allowlisted
T76 inputs below an absent root after every archive has passed verification.
No simulation, project-module import, NumPy import, or general tar extraction.
"""

import argparse
import gzip
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CHUNK = 1024 * 1024
T60_PREFIX = "tracks/tog/tasks/t60-full-window-gaussian-screen/local/"
T76_PREFIX = "tracks/tog/tasks/t76-continuous-full-window/"
COLUMNS = ["id", "fuelInitial", "fuel", "heat", "char", "glow", "state"]
CHECKPOINTS = ["00-initial", "01-after-A", "02-before-B", "03-after-B",
               "04-endpoint", "05-reset"]
ROW_COUNT = 34687
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX8 = re.compile(r"[0-9a-f]{8}\Z")
SAFE_PART = re.compile(r"[A-Za-z0-9_.-]+\Z")
ID_PATTERN = re.compile(r"ply:(0|[1-9][0-9]*)\Z")
SCENE_KEYS = set("count burning charred heated fuelRemaining frontier burnHash "
                 "representedArea areaWeightedFuelRemaining areaWeightedHeat areaWeightedChar".split())
PARTICLE_KEYS = set("count hotCount coldCount smokeCount temperatureSum dynamicTemperatureSum "
                    "densitySum circulationSum absCirculationSum smokeProxySum layerCounts".split())
COUNTER_KEYS = set("flameHeatDeposited graphHeatDeposited sceneSeedsEmitted frontierProcessed "
                   "frontierDeferred sceneFeedAttempts sceneFeedCapacityBlocked sceneFeedRandomRejected "
                   "baseParticlesEmitted baseHeatApplied flameSamplesProcessed flameSampleCapHits "
                   "clockProcessed clockFuelConsumed sceneSeedsRecycled sceneFeedRecycleCandidates "
                   "sceneFeedNoColdSlot sceneRecycleSlotsExamined recycledDensitySum recycledCirculationSum "
                   "recycledAbsCirculationSum recycledMaxDensity recycledMaxAbsCirculation recycledSmokeProxySum "
                   "recycledHotRemoved recycledMaxTemperature recycledMaxDynamicTemperature recycledMinAge "
                   "areaWeightedFlameHeatDeposited areaWeightedGraphHeatDeposited areaWeightedFuelConsumed "
                   "areaFeedCreditsGenerated areaFeedAttempts areaFeedAdmitted areaFeedBlocked "
                   "areaFeedServiceCapDropped areaFeedCancelledCredits".split())
GROUP_COUNTER_KEYS = set("flameHeatDeposited graphHeatDeposited sceneSeedsEmitted sceneSeedsRecycled "
                         "clockProcessed clockFuelConsumed areaWeightedFlameHeatDeposited "
                         "areaWeightedGraphHeatDeposited areaWeightedFuelConsumed".split())
CHECKPOINT_KEYS = set("schema checkpoint projection_note frame time seed original_native_hash "
                      "original_particle_state_hash random_draws scene particles counters counters_by_group "
                      "frontier emit_cursor material_columns material_rows complete_gas_arrays_available".split())
LEDGER_KEYS = set("schema status started_utc phases events progress render_checks page_errors console_errors "
                  "blocked_requests failures completed_checkpoints worker_total_ms internal_deadline_expired "
                  "timing_scope finished_utc publication_scope".split())


class VerificationError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def exact_keys(value, keys, label):
    require(isinstance(value, dict), label + ": expected an object")
    actual = set(value)
    require(actual == keys, label + ": unexpected or missing fields; extra=" +
            repr(sorted(actual - keys)) + ", missing=" + repr(sorted(keys - actual)))


def reject_constant(value):
    raise VerificationError("JSON contains a non-finite constant: " + value)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "JSON contains a duplicate key: " + key)
        result[key] = value
    return result


def decode_json(raw, label):
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                          parse_constant=reject_constant)
    except (UnicodeError, json.JSONDecodeError, VerificationError) as exc:
        raise VerificationError(label + ": invalid JSON: " + str(exc)) from exc


def read_json(path):
    return decode_json(path.read_bytes(), str(path))


def relative_parts(value, label):
    require(isinstance(value, str) and value, label + ": expected a nonempty relative path")
    require("\\" not in value and ":" not in value and "\x00" not in value,
            label + ": backslash, drive, stream, or NUL path rejected")
    require(not PurePosixPath(value).is_absolute() and not PureWindowsPath(value).drive,
            label + ": absolute or drive-qualified path rejected")
    parts = value.split("/")
    require(all(p not in ("", ".", "..") and SAFE_PART.fullmatch(p) and
                not p.endswith((".", " ")) and not PureWindowsPath(p).is_reserved()
                for p in parts), label + ": noncanonical, reserved, or traversal path rejected")
    return tuple(parts)


def contained_path(base, relative, label, basename=False):
    parts = relative_parts(relative, label)
    require(not basename or len(parts) == 1, label + ": package filename must be a basename")
    path = base.joinpath(*parts)
    require(path.resolve().is_relative_to(base.resolve()), label + ": resolved path escapes its root")
    return path


def nonnegative_integer(value, label):
    require(type(value) is int and value >= 0, label + ": expected a nonnegative integer")


def finite_number(value, label, nullable=False):
    if nullable and value is None:
        return
    require(type(value) in (int, float) and (type(value) is int or math.isfinite(value)),
            label + ": expected a finite scalar number")


def expected_identity(size, digest, label):
    nonnegative_integer(size, label + " size")
    require(isinstance(digest, str) and HEX64.fullmatch(digest), label + ": invalid SHA256")
    return {"bytes": size, "sha256": digest}


def stream_identity(stream, expected_size=None, collect=False, output=None):
    digest = hashlib.sha256()
    count = 0
    chunks = [] if collect else None
    while block := stream.read(CHUNK):
        count += len(block)
        require(expected_size is None or count <= expected_size,
                "Stream exceeds its declared decoded byte count")
        digest.update(block)
        if collect:
            chunks.append(block)
        if output is not None:
            output.write(block)
    return {"bytes": count, "sha256": digest.hexdigest()}, (b"".join(chunks) if collect else None)


def file_identity(path):
    require(path.is_file(), "Missing file: " + str(path))
    with path.open("rb") as source:
        return stream_identity(source)[0]


def check_identity(actual, expected, label):
    require(actual == expected, label + ": byte-count/SHA256 mismatch; expected=" +
            json.dumps(expected, sort_keys=True) + ", observed=" + json.dumps(actual, sort_keys=True))


def verify_gzip(path, packed, decoded, collect=False):
    check_identity(file_identity(path), packed, str(path) + " compressed")
    try:
        with gzip.open(path, "rb") as source:
            actual, body = stream_identity(source, decoded["bytes"], collect=collect)
    except (OSError, EOFError, VerificationError) as exc:
        raise VerificationError(str(path) + ": gzip verification failed: " + str(exc)) from exc
    check_identity(actual, decoded, str(path) + " decoded")
    return body


def t76_allowed_paths():
    allowed = {}
    for resolution in (128, 256):
        for index in range(5):
            stem = T60_PREFIX + f"S{resolution}-snapshot-{index}"
            allowed[stem + ".npz"] = "reference_npz"
            allowed[stem + ".json"] = "reference_metadata"
        allowed[T60_PREFIX + f"S{resolution}.json"] = "reference_metadata"
    allowed[T76_PREFIX + "local/journal.jsonl"] = "t76_journal"
    return allowed


def load_t76_plan():
    folder = HERE / "t76"
    manifest = read_json(folder / "manifest.json")
    require(manifest["schema"] == "t76-handoff-byte-archive-v1", "T76: unexpected manifest schema")
    allowed = t76_allowed_paths()
    records = manifest["files"]
    require(isinstance(records, list) and len(records) == 23, "T76: expected exactly 23 archives")
    paths, filenames, plan = set(), set(), []
    for record in records:
        relative = record["original_repo_relative_path"]
        relative_parts(relative, "T76 original path")
        require(relative in allowed, "T76: original path is outside the fixed restore allowlist: " + relative)
        require(relative not in paths, "T76: duplicate original path: " + relative)
        require(record["category"] == allowed[relative], "T76: category/path mismatch: " + relative)
        filename = record["packaged_filename"]
        path = contained_path(folder, filename, "T76 archive path", basename=True)
        require(filename not in filenames and filename.endswith(".gz"), "T76: duplicate or invalid filename")
        packed = expected_identity(record["packaged_bytes"], record["packaged_sha256"], filename)
        decoded = expected_identity(record["original_bytes"], record["original_sha256"], relative)
        require(packed["bytes"] <= 45 * 1024 * 1024, "T76: single-file cap exceeded")
        plan.append({"path": path, "relative": relative, "packed": packed, "decoded": decoded,
                     "category": record["category"]})
        paths.add(relative)
        filenames.add(filename)
    require(paths == set(allowed), "T76: incomplete original-path allowlist")
    receipts = {T76_PREFIX + "input-manifest.json", T76_PREFIX + "execution.json"}
    require(len(manifest["provenance"]) == 2 and
            {r["path"] for r in manifest["provenance"]} == receipts,
            "T76: unexpected provenance receipts")
    loaded = {}
    for receipt in manifest["provenance"]:
        path = contained_path(REPO, receipt["path"], "T76 provenance")
        check_identity(file_identity(path), expected_identity(receipt["bytes"], receipt["sha256"],
                       receipt["path"]), "T76 provenance " + receipt["path"])
        loaded[receipt["path"]] = read_json(path)
    freeze = loaded[T76_PREFIX + "input-manifest.json"]
    source_records = freeze["raw_inputs"] + [r for r in freeze["inputs"] if r["path"] in allowed]
    frozen = {r["path"]: expected_identity(r["bytes"], r["sha256"], r["path"]) for r in source_records}
    require(len(source_records) == 22 and len(frozen) == 22, "T76: frozen source inventory differs")
    journal = loaded[T76_PREFIX + "execution.json"]["ignored_local_journal"]
    require(journal["path"] == "local/journal.jsonl", "T76: unexpected frozen journal path")
    frozen[T76_PREFIX + journal["path"]] = expected_identity(journal["bytes"], journal["sha256"], "T76 journal")
    for entry in plan:
        check_identity(entry["decoded"], frozen[entry["relative"]], "T76 frozen identity " + entry["relative"])
    require(sum(e["packed"]["bytes"] for e in plan) <= 200 * 1024 * 1024,
            "T76: total compressed cap exceeded")
    return manifest, plan


def verify_t76(manifest, plan):
    for entry in plan:
        verify_gzip(entry["path"], entry["packed"], entry["decoded"])
    result = {
        "files": len(plan),
        "reference_npz_files": sum(e["category"] == "reference_npz" for e in plan),
        "reference_metadata_files": sum(e["category"] == "reference_metadata" for e in plan),
        "journal_files": sum(e["category"] == "t76_journal" for e in plan),
        "original_bytes": sum(e["decoded"]["bytes"] for e in plan),
        "packaged_bytes": sum(e["packed"]["bytes"] for e in plan),
        "largest_packaged_file_bytes": max(e["packed"]["bytes"] for e in plan),
    }
    require(result == manifest["totals"], "T76: declared totals differ from archive inventory")
    return result


def scalar_object(value, keys, label, nullable=()):
    exact_keys(value, keys, label)
    for key, item in value.items():
        finite_number(item, label + "." + key, nullable=key in nullable)


def check_summaries(value, label):
    scene = value["scene"]
    exact_keys(scene, SCENE_KEYS, label + ".scene")
    require(scene["count"] == ROW_COUNT, label + ": scene material count differs")
    require(isinstance(scene["burnHash"], str) and HEX8.fullmatch(scene["burnHash"]),
            label + ": invalid scalar burn hash")
    for key in SCENE_KEYS - {"burnHash"}:
        finite_number(scene[key], label + ".scene." + key,
                      nullable=key in {"representedArea", "areaWeightedFuelRemaining", "areaWeightedHeat", "areaWeightedChar"})
    particles = value["particles"]
    exact_keys(particles, PARTICLE_KEYS, label + ".particles")
    for key in PARTICLE_KEYS - {"layerCounts"}:
        finite_number(particles[key], label + ".particles." + key)
    layers = particles["layerCounts"]
    require(isinstance(layers, list) and len(layers) == 9, label + ": expected nine scalar layer counts")
    for item in layers:
        nonnegative_integer(item, label + ".particles.layerCounts")
    scalar_object(value["counters"], COUNTER_KEYS, label + ".counters", nullable={"recycledMinAge"})


def verify_checkpoint(value, entry, baseline_ids):
    label = "T42 " + entry["checkpoint"]
    exact_keys(value, CHECKPOINT_KEYS, label)
    require(value["schema"] == "t42-public-dynamic-state-projection-v1", label + ": incorrect schema")
    require(value["checkpoint"] == entry["checkpoint"], label + ": checkpoint label differs")
    require(value["projection_note"] == "Recorded numerical values preserved; scene positions, covariance, appearance, camera and images excluded.",
            label + ": unexpected projection declaration")
    require(value["complete_gas_arrays_available"] is False, label + ": unexpected gas-array claim")
    require(value["material_columns"] == COLUMNS, label + ": material column allowlist/order differs")
    for key in ("frame", "seed", "random_draws", "emit_cursor"):
        nonnegative_integer(value[key], label + "." + key)
    finite_number(value["time"], label + ".time")
    for key in ("original_native_hash", "original_particle_state_hash"):
        require(isinstance(value[key], str) and HEX8.fullmatch(value[key]), label + ": invalid " + key)
    check_summaries(value, label)
    exact_keys(value["counters_by_group"], {"ply"}, label + ".counters_by_group")
    scalar_object(value["counters_by_group"]["ply"], GROUP_COUNTER_KEYS, label + ".counters_by_group.ply")
    frontier = value["frontier"]
    require(isinstance(frontier, list), label + ": frontier must contain scalar indices only")
    require(all(type(index) is int and 0 <= index < ROW_COUNT for index in frontier),
            label + ": invalid frontier index or nested field")
    rows = value["material_rows"]
    require(isinstance(rows, list) and len(rows) == ROW_COUNT and entry["material_rows"] == ROW_COUNT,
            label + ": expected exactly 34687 material rows")
    ids = set()
    for index, row in enumerate(rows):
        row_label = label + ".material_rows[" + str(index) + "]"
        require(isinstance(row, list) and len(row) == len(COLUMNS), row_label + ": expected exactly seven columns")
        identifier = row[0]
        require(isinstance(identifier, str) and ID_PATTERN.fullmatch(identifier) and
                int(identifier.split(":")[1]) < ROW_COUNT, row_label + ": invalid material ID")
        require(identifier not in ids, row_label + ": duplicate material ID: " + identifier)
        ids.add(identifier)
        for column, number in zip(COLUMNS[1:], row[1:]):
            finite_number(number, row_label + "." + column)
        require(type(row[-1]) is int, row_label + ": state must be a scalar integer")
    require(baseline_ids is None or ids == baseline_ids, label + ": checkpoint material IDs differ")
    return ids


def verify_ledger(value):
    label = "T42 execution ledger"
    exact_keys(value, LEDGER_KEYS, label)
    require(value["schema"] == "t42-one-workflow-run-v1" and
            value["status"] == "completed_capture_pending_saved_audit", label + ": unexpected schema/status")
    require(value["publication_scope"] == "Original scalar execution ledger; runtime paths and third-party assets omitted.",
            label + ": unexpected publication scope")
    require(value["completed_checkpoints"] == 6 and value["internal_deadline_expired"] is False,
            label + ": unexpected completion fields")
    for key in ("page_errors", "console_errors", "blocked_requests", "failures"):
        require(value[key] == [], label + ": unexpected nonempty " + key)
    for key in ("started_utc", "finished_utc"):
        require(isinstance(value[key], str) and
                re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z", value[key]),
                label + ": invalid timestamp field " + key)
    require(value["timing_scope"] == "worker_total_ms: module entry through cleanup and error checks, before final progress/result receipts; phase ms excludes the following progress-file write",
            label + ": unexpected timing declaration")
    finite_number(value["worker_total_ms"], label + ".worker_total_ms")
    for phase in value["phases"]:
        exact_keys(phase, {"name", "ms"}, label + ".phases")
        require(isinstance(phase["name"], str) and re.fullmatch(r"[A-Za-z0-9_-]{1,100}", phase["name"]),
                label + ": invalid phase label")
        finite_number(phase["ms"], label + ".phase.ms")
    for event in value["events"]:
        exact_keys(event, {"name", "lit", "frame", "time"}, label + ".events")
        require(event["name"] in ("A", "B"), label + ": unexpected event name")
        nonnegative_integer(event["lit"], label + ".event.lit")
        nonnegative_integer(event["frame"], label + ".event.frame")
        finite_number(event["time"], label + ".event.time")
    completed = []
    for progress in value["progress"]:
        is_checkpoint = isinstance(progress, dict) and "checkpoint" in progress
        keys = {"time", "scene", "particles", "counters", "hash"}
        keys |= {"checkpoint", "frame", "draw_count"} if is_checkpoint else {"step_completed"}
        exact_keys(progress, keys, label + ".progress")
        if is_checkpoint:
            require(progress["checkpoint"] in CHECKPOINTS, label + ": unexpected progress checkpoint")
            completed.append(progress["checkpoint"])
            nonnegative_integer(progress["frame"], label + ".progress.frame")
            nonnegative_integer(progress["draw_count"], label + ".progress.draw_count")
        else:
            nonnegative_integer(progress["step_completed"], label + ".progress.step_completed")
        finite_number(progress["time"], label + ".progress.time")
        require(isinstance(progress["hash"], str) and HEX8.fullmatch(progress["hash"]),
                label + ": invalid progress hash")
        check_summaries(progress, label + ".progress")
    require(completed == CHECKPOINTS, label + ": checkpoint progress sequence differs")
    require(isinstance(value["render_checks"], list) and len(value["render_checks"]) == 6,
            label + ": expected six scalar render-status records")
    for checkpoint, render in zip(CHECKPOINTS, value["render_checks"]):
        exact_keys(render, {"checkpoint", "glError", "contextLost"}, label + ".render_checks")
        require(render["checkpoint"] == checkpoint and render["glError"] == 0 and
                render["contextLost"] is False, label + ": render-status record differs")


def verify_t42():
    folder = HERE / "t42"
    manifest = read_json(folder / "MANIFEST.json")
    require(manifest["schema"] == "t42-public-handoff-data-v1", "T42: unexpected manifest schema")
    require(manifest["fields_per_material_row"] == COLUMNS, "T42: manifest material columns differ")
    require(manifest["checkpoint_count"] == 6 and manifest["material_rows_total"] == 6 * ROW_COUNT,
            "T42: manifest checkpoint/row counts differ")
    require(manifest["new_scientific_runs"] == 0 and manifest["historical_visual_verdict"] == "unqualified",
            "T42: publication changes historical run/verdict claims")
    entries = manifest["entries"]
    expected_files = {name + ".dynamic.json.gz" for name in CHECKPOINTS} | {"execution-ledger.json.gz"}
    require(isinstance(entries, list) and len(entries) == 7 and
            {entry["file"] for entry in entries} == expected_files, "T42: archive inventory differs")
    baseline_ids, checkpoints, compressed, decoded_total = None, [], 0, 0
    for entry in entries:
        filename = entry["file"]
        path = contained_path(folder, filename, "T42 archive path", basename=True)
        packed = expected_identity(entry["bytes"], entry["sha256"], filename)
        decoded = expected_identity(entry["decoded_bytes"], entry["decoded_sha256"], filename + " decoded")
        require(decoded["bytes"] <= 4 * 1024 * 1024, filename + ": unexpected JSON size")
        value = decode_json(verify_gzip(path, packed, decoded, collect=True), filename)
        if filename == "execution-ledger.json.gz":
            verify_ledger(value)
        else:
            require(entry["checkpoint"] in CHECKPOINTS and
                    filename == entry["checkpoint"] + ".dynamic.json.gz", filename + ": label mismatch")
            baseline_ids = verify_checkpoint(value, entry, baseline_ids)
            checkpoints.append(entry["checkpoint"])
        compressed += packed["bytes"]
        decoded_total += decoded["bytes"]
    require(checkpoints == CHECKPOINTS, "T42: checkpoint sequence differs")
    require(compressed == manifest["total_packaged_bytes"], "T42: compressed total differs")
    return {"files": 7, "checkpoints": 6, "material_rows_per_checkpoint": ROW_COUNT,
            "material_rows_total": 6 * ROW_COUNT, "unique_ids_per_checkpoint": len(baseline_ids),
            "packaged_bytes": compressed, "decoded_bytes": decoded_total,
            "strict_field_allowlists_passed": True, "geometry_or_appearance_fields_present": False}


def prepare_restore_root(requested, plan):
    raw = Path(requested).expanduser()
    require(not os.path.lexists(raw), "Restore root already exists; choose an absent new directory: " + str(raw))
    require(raw.name not in ("", ".", ".."), "Restore root must name a new directory")
    require(raw.parent.is_dir(), "Restore root parent must already exist: " + str(raw.parent))
    target = raw.parent.resolve(strict=True) / raw.name
    require(not os.path.lexists(target), "Resolved restore root already exists: " + str(target))
    for entry in plan:
        contained_path(target, entry["relative"], "T76 restore destination")
    return target


def is_link_or_junction(path):
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def restore_t76(root, plan):
    require(not os.path.lexists(root), "Restore root appeared after verification; refusing overwrite")
    root.mkdir()  # Exclusive: no exist_ok and no creation of external parent directories.
    try:
        for entry in plan:
            check_identity(file_identity(entry["path"]), entry["packed"], "Restore source changed")
            require(not is_link_or_junction(root) and root.resolve() == root,
                    "Restore root was replaced or redirected")
            parts = relative_parts(entry["relative"], "T76 restore path")
            parent = root
            for part in parts[:-1]:
                parent = parent / part
                if not parent.exists():
                    parent.mkdir()
                require(parent.is_dir() and not is_link_or_junction(parent) and
                        parent.resolve().is_relative_to(root), "Restore parent is unsafe: " + str(parent))
            destination = parent / parts[-1]
            require(destination.resolve().is_relative_to(root), "Restore destination escapes new root")
            with destination.open("xb") as output:
                with gzip.open(entry["path"], "rb") as source:
                    actual, _ = stream_identity(source, entry["decoded"]["bytes"], output=output)
            check_identity(actual, entry["decoded"], "Restored bytes " + entry["relative"])
            check_identity(file_identity(destination), entry["decoded"], "Restored disk file " + entry["relative"])
    except Exception as exc:
        raise VerificationError("Restore incomplete; partial files remain only in new root " + str(root) +
                                "; original files were not overwritten: " + str(exc)) from exc
    return {"root": str(root), "files": len(plan),
            "bytes": sum(entry["decoded"]["bytes"] for entry in plan),
            "all_restored_files_hash_verified": True, "original_files_overwritten": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore-t76-to", metavar="NEW_DIRECTORY",
                        help="after all checks, restore allowlisted T76 bytes into an absent root with an existing parent")
    args = parser.parse_args()
    manifest, plan = load_t76_plan()
    restore_root = prepare_restore_root(args.restore_t76_to, plan) if args.restore_t76_to else None
    t76 = verify_t76(manifest, plan)
    t42 = verify_t42()
    result = {"status": "verified", "mode": "read_only", "scientific_executions": 0,
              "t76": t76, "t42": t42,
              "total_archive_files": t76["files"] + t42["files"],
              "total_packaged_bytes": t76["packaged_bytes"] + t42["packaged_bytes"],
              "total_decoded_bytes": t76["original_bytes"] + t42["decoded_bytes"]}
    if restore_root is not None:
        result["restoration"] = restore_t76(restore_root, plan)
        result["mode"] = "verified_and_restored_to_new_directory"
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "verification_failed", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(1)
