"""Publish recorded simulation values, excluding third-party scene geometry.

Archival readback only. Does not import the renderer, launch a browser, or simulate.
"""
from pathlib import Path
import gzip
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUTER = ROOT.parent.parent
SOURCE = OUTER / "outputs/t42-firewoods-sequential-workflow/run-01"
DECISION = ROOT / "tracks/tog/tasks/t42-firewoods-sequential-workflow/decision-evidence.json"
COLUMNS = ["id", "fuelInitial", "fuel", "heat", "char", "glow", "state"]
CHECKPOINTS = ["00-initial", "01-after-A", "02-before-B", "03-after-B", "04-endpoint", "05-reset"]

def sha(b):
    return hashlib.sha256(b).hexdigest()

def put(name, value):
    raw = (json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode()
    packed = gzip.compress(raw, compresslevel=9, mtime=0)
    path = HERE / name
    if path.exists():
        assert path.read_bytes() == packed, "existing archive differs: " + name
    else:
        path.write_bytes(packed)
    assert gzip.decompress(path.read_bytes()) == raw
    return {"file": name, "bytes": len(packed), "sha256": sha(packed),
            "decoded_bytes": len(raw), "decoded_sha256": sha(raw)}

def main():
    inventory = {Path(x["path"]).name: x for x in json.loads(DECISION.read_text())["external_run_inventory"]}
    entries = []
    for label in CHECKPOINTS:
        name = label + ".json.gz"
        original = (SOURCE / name).read_bytes()
        expected = inventory[name]
        assert len(original) == expected["bytes"] and sha(original) == expected["sha256"], name
        state = json.loads(gzip.decompress(original))
        points = state["points"]
        assert len(points) == 34687 and len({p["id"] for p in points}) == 34687
        projection = {
            "schema": "t42-public-dynamic-state-projection-v1",
            "checkpoint": label,
            "projection_note": "Recorded numerical values preserved; scene positions, covariance, appearance, camera and images excluded.",
            "frame": state["frame"], "time": state["time"], "seed": state["seed"],
            "original_native_hash": state["hash"],
            "original_particle_state_hash": state["particleStateHash"],
            "random_draws": state["randomDraws"], "scene": state["scene"],
            "particles": state["particles"], "counters": state["counters"],
            "counters_by_group": state["countersByGroup"],
            "frontier": state["frontier"], "emit_cursor": state["emitCursor"],
            "material_columns": COLUMNS,
            "material_rows": [[p[k] for k in COLUMNS] for p in points],
            "complete_gas_arrays_available": False,
        }
        entry = put(label + ".dynamic.json.gz", projection)
        entry.update(original_record=expected, material_rows=len(points), checkpoint=label)
        entries.append(entry)
    original = (SOURCE / "result.json").read_bytes()
    expected = inventory["result.json"]
    assert len(original) == expected["bytes"] and sha(original) == expected["sha256"]
    result = json.loads(original)
    keep = ["schema", "status", "started_utc", "phases", "events", "progress",
            "render_checks", "page_errors", "console_errors", "blocked_requests", "failures",
            "completed_checkpoints", "worker_total_ms", "internal_deadline_expired",
            "timing_scope", "finished_utc"]
    report = {k: result[k] for k in keep}
    report["publication_scope"] = "Original scalar execution ledger; runtime paths and third-party assets omitted."
    entry = put("execution-ledger.json.gz", report)
    entry["original_record"] = expected
    entries.append(entry)
    manifest = {
        "schema": "t42-public-handoff-data-v1",
        "purpose": "Evidence inspection and T81 preparation, not a restartable complete simulator checkpoint.",
        "new_scientific_runs": 0, "historical_visual_verdict": "unqualified",
        "checkpoint_count": 6, "material_rows_total": 6 * 34687,
        "fields_per_material_row": COLUMNS,
        "omitted": ["third-party geometry/appearance", "rendered scene images", "private notes"],
        "unavailable_in_original_records": ["complete gas particle arrays", "per-source emission outcomes", "A-only trajectory"],
        "entries": entries,
        "total_packaged_bytes": sum(x["bytes"] for x in entries),
    }
    output = (json.dumps(manifest, indent=2) + "\n").encode()
    target = HERE / "MANIFEST.json"
    if target.exists():
        assert target.read_bytes() == output, "existing manifest differs"
    else:
        target.write_bytes(output)
    print(json.dumps({"files": len(entries), "material_rows": manifest["material_rows_total"],
                      "compressed_bytes": manifest["total_packaged_bytes"], "new_simulation": False}))

if __name__ == "__main__":
    main()
