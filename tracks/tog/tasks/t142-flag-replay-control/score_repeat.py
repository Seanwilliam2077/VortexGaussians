"""Verify the registered repeat against the ordinary flag, including each archived native buffer."""
import argparse
import hashlib
import json
from pathlib import Path
import zlib

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "t137-flag-fine-gas/evidence"


def read(path):
    return json.loads(path.read_bytes())


def rows(folder):
    return [json.loads(line) for line in (folder / "ordinary-steps.ndjson").read_bytes().splitlines()]


def pending_bytes(stream, row):
    rec = row["feedback"]
    stream.seek(rec["offset"])
    buf = zlib.decompress(stream.read(rec["compressed_bytes"]))
    if len(buf) != rec["raw_bytes"] or hashlib.sha256(buf).hexdigest() != rec["sha256"]:
        raise ValueError("Grid digest or size mismatch")
    return buf


def measure(folder, published=False):
    exits = read(folder / "EXIT.json")
    run = read(folder / "ordinary.json")
    original = read(BASE / "ordinary.json")
    if published and not (folder / "ordinary-grids.zlib").exists():
        # Byte-identical streams were checked before packaging. Reuse the shared bytes by whole-file digest.
        archive = BASE / "ordinary-grids.zlib"
        file_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
        if file_hash != read(folder / "GRID_SHA256.json")["repeat_file_sha256"]:
            raise ValueError("Published reference to shared bytes does not match")
    else:
        archive = folder / "ordinary-grids.zlib"
    identity = ("pin", "adapter", "settings", "stiffness", "scene_signature", "gas_dims", "features")
    if exits["pid"] == read(BASE / "workers.json")["ordinary"]["pid"]:
        raise ValueError("Expected an independent process")
    if not all(run[k] == original[k] for k in identity) or run["settings"] != original["original_settings"]:
        raise ValueError("Source, execution configuration or scene identity differs")
    original_rows, repeat_rows = rows(BASE), rows(folder)
    totals, first, grid_count = {}, {}, 0
    with (BASE / "ordinary-grids.zlib").open("rb") as xg, archive.open("rb") as yg:
        for record, other in zip(original_rows, repeat_rows):
            if record.get("kind") != other.get("kind"):
                raise ValueError("Repeat ledger alignment failure")
            for key in sorted(record.keys() | other.keys()):
                if record.get(key) != other.get(key):
                    totals[key] = totals.get(key, 0) + 1
                    first.setdefault(key, {k:record[k] for k in ("kind","index","frame","substep") if k in record})
            if "feedback" in record:
                if pending_bytes(xg, record) != pending_bytes(yg, other):
                    totals["raw_grid"] = totals.get("raw_grid", 0) + 1
                    first.setdefault("raw_grid", record["index"])
                grid_count += 1
    complete = len(original_rows) == len(repeat_rows) and run["status"] == "complete" and exits["exit"] == 0
    return dict(complete=complete, wall_s=exits["wall_s"], reference_rows=len(original_rows),
                repeat_rows=len(repeat_rows), grid_pairs=grid_count, unequal_records_by_field=totals,
                first_mismatch_by_field=first, exact_full_record_match=complete and not totals,
                repeat_file_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder", type=Path, nargs="?", default=HERE / "evidence")
    p.add_argument("--published", action="store_true")
    args = p.parse_args()
    print(json.dumps(measure(args.folder, args.published), indent=2))
