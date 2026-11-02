"""Archive the allowlisted T76 evidence as opaque bytes; Python stdlib only.

Run ``python pack.py`` to create, or verify already existing, packages.
Run ``python pack.py --verify`` to verify without the ignored source files.
No solver, NumPy, NPZ parser, subprocess, network, or scientific calculation
is used. Source files and existing archive files are never overwritten.
"""

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import sys
import zlib


HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
T60 = "tracks/tog/tasks/t60-full-window-gaussian-screen/local/"
T76 = "tracks/tog/tasks/t76-continuous-full-window/"
MANIFEST = HERE / "manifest.json"
MAX_FILE = 45 * 1024 * 1024
MAX_TOTAL = 200 * 1024 * 1024
CHUNK = 1024 * 1024
GZIP_HEADER = b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def repo_path(relative):
    pure = PurePosixPath(relative)
    require(not pure.is_absolute() and ".." not in pure.parts,
            "Unsafe repository path: " + relative)
    path = REPO.joinpath(*pure.parts).resolve()
    require(path.is_relative_to(REPO), "Path escapes repository: " + relative)
    return path


def output_path(filename):
    require(Path(filename).name == filename and filename not in ("", ".", ".."),
            "Unsafe archive filename: " + filename)
    path = (HERE / filename).resolve()
    require(path.parent == HERE, "Output escapes owned directory")
    return path


def identity_stream(stream, maximum=None):
    digest = hashlib.sha256()
    size = 0
    while block := stream.read(CHUNK):
        size += len(block)
        require(maximum is None or size <= maximum, "Decoded size exceeds frozen identity")
        digest.update(block)
    return {"bytes": size, "sha256": digest.hexdigest()}


def identity(path):
    with path.open("rb") as stream:
        return identity_stream(stream)


def read_json(path):
    return json.loads(path.read_bytes().decode("utf-8"))


def original_identity(record):
    return {"bytes": record["bytes"], "sha256": record["sha256"]}


def inventory():
    input_relative = T76 + "input-manifest.json"
    execution_relative = T76 + "execution.json"
    freeze = read_json(repo_path(input_relative))
    execution = read_json(repo_path(execution_relative))
    expected_raw = {
        T60 + f"S{resolution}-snapshot-{index}.npz"
        for resolution in (128, 256) for index in range(5)
    }
    expected_meta = {
        T60 + f"S{resolution}-snapshot-{index}.json"
        for resolution in (128, 256) for index in range(5)
    } | {T60 + "S128.json", T60 + "S256.json"}
    raw = freeze["raw_inputs"]
    require(len(raw) == 10 and {r["path"] for r in raw} == expected_raw,
            "T76 raw input allowlist differs from the ten requested snapshots")
    metadata = [r for r in freeze["inputs"] if r["path"] in expected_meta]
    require(len(metadata) == 12 and {r["path"] for r in metadata} == expected_meta,
            "T76 metadata allowlist differs from the twelve requested JSON files")
    journal = execution["ignored_local_journal"]
    require(journal["path"] == "local/journal.jsonl", "Unexpected journal path")
    require(journal["bytes"] == 178721100, "Unexpected frozen journal size")
    journal = dict(journal, path=T76 + journal["path"])
    records = []
    for category, entries in (("reference_npz", raw), ("reference_metadata", metadata),
                              ("t76_journal", [journal])):
        for entry in entries:
            require(isinstance(entry["bytes"], int) and entry["bytes"] >= 0,
                    "Invalid input size")
            require(len(entry["sha256"]) == 64 and
                    all(c in "0123456789abcdef" for c in entry["sha256"]),
                    "Invalid input SHA256")
            filename = ("T76-journal.jsonl.gz" if category == "t76_journal"
                        else PurePosixPath(entry["path"]).name + ".gz")
            records.append({
                "category": category,
                "original_repo_relative_path": entry["path"],
                "original_bytes": entry["bytes"],
                "original_sha256": entry["sha256"],
                "packaged_filename": filename,
            })
    records.sort(key=lambda r: r["original_repo_relative_path"])
    require(len({r["packaged_filename"] for r in records}) == 23,
            "Archive filename collision")
    provenance = [dict(path=p, **identity(repo_path(p)))
                  for p in (input_relative, execution_relative)]
    return records, provenance


def expected_original(record):
    return {"bytes": record["original_bytes"], "sha256": record["original_sha256"]}


def verify_sources(records):
    errors = []
    for record in records:
        relative = record["original_repo_relative_path"]
        path = repo_path(relative)
        if not path.is_file():
            errors.append({"path": relative, "error": "missing"})
            continue
        observed = identity(path)
        if observed != expected_original(record):
            errors.append({"path": relative, "error": "identity_mismatch", "observed": observed})
    require(not errors, "Source preflight failed: " + json.dumps(errors, sort_keys=True))


def verify_metadata_links(records):
    by_path = {r["original_repo_relative_path"]: r for r in records}
    for resolution in (128, 256):
        aggregate = read_json(repo_path(T60 + f"S{resolution}.json"))
        require(len(aggregate["checkpoint_records"]) == 5, "Unexpected checkpoint count")
        for checkpoint in aggregate["checkpoint_records"]:
            meta = by_path[T60 + checkpoint["path"]]
            require(original_identity(checkpoint) == expected_original(meta),
                    "Aggregate metadata identity disagrees with T76 freeze")
            raw = by_path[T60 + checkpoint["raw"]["path"]]
            require(original_identity(checkpoint["raw"]) == expected_original(raw),
                    "Aggregate raw identity disagrees with T76 freeze")
            snapshot = read_json(repo_path(meta["original_repo_relative_path"]))
            require(T60 + snapshot["raw"]["path"] == raw["original_repo_relative_path"] and
                    original_identity(snapshot["raw"]) == expected_original(raw),
                    "Snapshot raw identity disagrees with T76 freeze")


def verify_member(path, record, expected_package=None):
    require(path.is_file(), "Missing package: " + path.name)
    require(path.stat().st_size <= MAX_FILE, "Package exceeds 45 MiB: " + path.name)
    with path.open("rb") as stream:
        require(stream.read(10) == GZIP_HEADER, "Noncanonical gzip header: " + path.name)
    packaged = identity(path)
    if expected_package is not None:
        require(packaged == expected_package, "Compressed identity mismatch: " + path.name)
    with gzip.open(path, "rb") as stream:
        restored = identity_stream(stream, record["original_bytes"])
    require(restored == expected_original(record), "Round-trip mismatch: " + path.name)
    return packaged


class LimitedWriter:
    def __init__(self, stream, limit):
        self.stream = stream
        self.limit = limit
        self.count = 0

    def write(self, data):
        require(self.count + len(data) <= self.limit,
                "Compression would exceed the 45 MiB single-file or 200 MiB total cap")
        written = self.stream.write(data)
        self.count += written
        return written

    def flush(self):
        self.stream.flush()


def create_member(record, remaining):
    destination = output_path(record["packaged_filename"])
    if destination.exists():
        return verify_member(destination, record)
    temporary = output_path("." + destination.name + ".pending-" + str(os.getpid()))
    require(not temporary.exists(), "Existing temporary file will not be overwritten")
    created_destination = False
    try:
        digest = hashlib.sha256()
        source_size = 0
        with temporary.open("xb") as raw_output:
            bounded = LimitedWriter(raw_output, min(MAX_FILE, remaining))
            with gzip.GzipFile(filename="", mode="wb", fileobj=bounded,
                               compresslevel=9, mtime=0) as compressed:
                with repo_path(record["original_repo_relative_path"]).open("rb") as source:
                    while block := source.read(CHUNK):
                        source_size += len(block)
                        digest.update(block)
                        compressed.write(block)
        require({"bytes": source_size, "sha256": digest.hexdigest()} == expected_original(record),
                "Source changed during compression")
        packaged = verify_member(temporary, record)
        # Exclusive creation is portable and never replaces an existing archive.
        with destination.open("xb") as published:
            created_destination = True
            with temporary.open("rb") as source:
                shutil.copyfileobj(source, published, CHUNK)
        require(identity(destination) == packaged, "Published package copy mismatch")
        return packaged
    except BaseException:
        if created_destination:
            require(destination.resolve().parent == HERE, "Unsafe cleanup target")
            destination.unlink()
        raise
    finally:
        if temporary.exists():
            require(temporary.resolve().parent == HERE, "Unsafe cleanup target")
            temporary.unlink()


def totals(records):
    return {
        "files": len(records),
        "reference_npz_files": sum(r["category"] == "reference_npz" for r in records),
        "reference_metadata_files": sum(r["category"] == "reference_metadata" for r in records),
        "journal_files": sum(r["category"] == "t76_journal" for r in records),
        "original_bytes": sum(r["original_bytes"] for r in records),
        "packaged_bytes": sum(r["packaged_bytes"] for r in records),
        "largest_packaged_file_bytes": max(r["packaged_bytes"] for r in records),
    }


def verify_archive(records, provenance):
    manifest = read_json(MANIFEST)
    require(manifest["schema"] == "t76-handoff-byte-archive-v1", "Unexpected archive schema")
    require(manifest["provenance"] == provenance, "Frozen provenance identity changed")
    require(manifest["limits"] == {"maximum_single_file_bytes": MAX_FILE,
                                   "maximum_compressed_total_bytes": MAX_TOTAL},
            "Archive limits differ")
    require(manifest["generator"]["sha256"] == identity(Path(__file__).resolve())["sha256"],
            "Generator identity changed")
    archived = manifest["files"]
    require(len(archived) == len(records), "Archive inventory count differs")
    for record, saved in zip(records, archived):
        require({key: saved[key] for key in record} == record,
                "Archive inventory differs from frozen receipts")
        verify_member(output_path(saved["packaged_filename"]), saved,
                      {"bytes": saved["packaged_bytes"], "sha256": saved["packaged_sha256"]})
    summary = totals(archived)
    require(summary == manifest["totals"], "Archive totals differ")
    require(summary["packaged_bytes"] <= MAX_TOTAL, "Archive exceeds total cap")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true",
                        help="verify archive and frozen receipts without ignored original inputs")
    args = parser.parse_args()
    records, provenance = inventory()
    if args.verify:
        summary = verify_archive(records, provenance)
        print(json.dumps(dict(status="verified_archive_round_trip", **summary), sort_keys=True))
        return
    verify_sources(records)
    verify_metadata_links(records)
    if MANIFEST.exists():
        summary = verify_archive(records, provenance)
        print(json.dumps(dict(status="verified_existing_archive_and_sources_no_writes", **summary),
                         sort_keys=True))
        return
    complete = []
    total = 0
    for record in records:
        packaged = create_member(record, MAX_TOTAL - total)
        total += packaged["bytes"]
        require(total <= MAX_TOTAL, "Archive exceeds 200 MiB total")
        complete.append(dict(record, packaged_bytes=packaged["bytes"],
                             packaged_sha256=packaged["sha256"]))
        print(json.dumps({"packaged": record["packaged_filename"],
                          "bytes": packaged["bytes"], "round_trip": "verified"}), flush=True)
    manifest = {
        "schema": "t76-handoff-byte-archive-v1",
        "purpose": "User-requested archival handoff while research remains paused; no new scientific run.",
        "scope": "All ten T76 raw reference inputs, twelve local metadata inputs, and its complete saved journal.",
        "provenance": provenance,
        "generator": {"filename": "pack.py", "sha256": identity(Path(__file__).resolve())["sha256"]},
        "compression": {
            "format": "gzip", "level": 9, "mtime": 0, "stored_filename": "",
            "python_version": platform.python_version(),
            "zlib_compile_version": zlib.ZLIB_VERSION,
            "zlib_runtime_version": zlib.ZLIB_RUNTIME_VERSION,
            "determinism_scope": "Fixed source bytes and recorded zlib implementation; no timestamps or filenames in gzip headers.",
        },
        "limits": {"maximum_single_file_bytes": MAX_FILE,
                   "maximum_compressed_total_bytes": MAX_TOTAL},
        "verification": {
            "source_bytes_and_sha256_match_frozen_receipts": True,
            "snapshot_and_aggregate_metadata_identity_links_checked": True,
            "every_gzip_round_trip_bytes_and_sha256_match_original": True,
            "npz_files_treated_as_opaque_bytes": True,
            "numpy_imported": False,
            "scientific_executions": 0,
            "source_files_modified": False,
            "missing_requested_inputs": [],
        },
        "not_in_this_allowlist": [
            T60 + "S128.npz", T60 + "S256.npz",
            T60 + "S128-steps.jsonl", T60 + "S256-steps.jsonl",
        ],
        "non_input_reference_note": "The aggregate metadata names additional T60 final arrays and step logs; these are not the ten T76 raw inputs and are not included in this bounded pack.",
        "totals": totals(complete),
        "files": complete,
    }
    serialized = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with MANIFEST.open("xb") as output:
        output.write(serialized)
    summary = verify_archive(records, provenance)
    print(json.dumps(dict(status="created_and_verified_archive", **summary), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "archive_error", "error": str(exc)}, sort_keys=True),
              file=sys.stderr)
        raise SystemExit(1)
