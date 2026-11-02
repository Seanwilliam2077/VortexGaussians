"""Index existing public research files; no ignored files, execution or imports."""
from __future__ import annotations

import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXCLUDED = {
    "tracks/STATUS.md", "tracks/EXPLORATION.md", "tracks/AGENT_HANDOFF.md"
}


def blob_identity(reader: subprocess.Popen, oid: str) -> tuple[int, str]:
    """Hash the indexed Git blob, independent of checkout newline conversion."""
    reader.stdin.write((oid + "\n").encode("ascii"))
    reader.stdin.flush()
    header = reader.stdout.readline().decode("ascii").strip().split()
    if len(header) != 3 or header[:2] != [oid, "blob"]:
        raise RuntimeError(f"Unexpected Git blob response: {header}")
    size = int(header[2])
    remaining = size
    h = hashlib.sha256()
    while remaining:
        chunk = reader.stdout.read(min(1024 * 1024, remaining))
        if not chunk:
            raise RuntimeError(f"Truncated Git blob: {oid}")
        h.update(chunk)
        remaining -= len(chunk)
    if reader.stdout.read(1) != b"\n":
        raise RuntimeError(f"Invalid Git blob delimiter: {oid}")
    return size, h.hexdigest()


def kind(name: str) -> str:
    suffix = Path(name).suffix.lower()
    if suffix in {".py", ".js", ".mjs", ".cjs", ".html", ".css", ".sh", ".ps1"}:
        return "source"
    if suffix in {".json", ".jsonl", ".csv", ".tsv", ".npz", ".npy", ".gz"}:
        return "data_or_receipt"
    if suffix in {".png", ".jpg", ".jpeg", ".svg", ".mp4", ".webm", ".pdf"}:
        return "media_or_document"
    if suffix in {".md", ".txt", ".tex", ".bib"}:
        return "text"
    return "other"


def main() -> None:
    raw = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=ROOT)
    indexed = {}
    for record in raw.decode("utf-8").split("\0"):
        if not record:
            continue
        identity, path = record.split("\t", 1)
        _mode, oid, stage = identity.split()
        if stage != "0":
            raise RuntimeError(f"Unmerged indexed path: {path}")
        indexed[path] = oid
    required = "tracks/tog/tasks/t81-firewoods-capacity-causality/README.md"
    if required not in indexed:
        raise RuntimeError("Stage the publication documents, including T81 README, before building the catalog.")
    paths = sorted(p for p in indexed if p not in EXCLUDED
                   and not p.startswith("tracks/evidence/handoff-2026-11-02/"))
    groups: dict[str, list[dict]] = defaultdict(list)
    with subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT,
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE) as reader:
        for rel in paths:
            path = ROOT / rel
            if not path.is_file():
                raise RuntimeError(f"Indexed path missing: {rel}")
            parts = rel.split("/")
            if rel.startswith("tracks/tog/tasks/") or rel.startswith("tracks/art/studies/"):
                group = "/".join(parts[:4])
            elif rel.startswith("research/"):
                group = "research"
            elif rel.startswith("tracks/"):
                group = "/".join(parts[:2]) if len(parts) > 2 else "tracks"
            else:
                group = parts[0] if len(parts) > 1 else "repository_root"
            size, sha = blob_identity(reader, indexed[rel])
            groups[group].append({"path": rel, "bytes": size, "sha256": sha,
                                  "git_blob_oid": indexed[rel], "kind": kind(rel)})
        reader.stdin.close()
        if reader.wait() != 0:
            raise RuntimeError("Git blob reader failed")
    records = []
    for group, files in sorted(groups.items()):
        names = {f["path"] for f in files}
        entry = next((f"{group}/{n}" for n in ("README.md", "BRIEF.md", "TASK.md")
                      if f"{group}/{n}" in names), None)
        title = None
        if entry:
            lines = (ROOT / entry).read_text(encoding="utf-8-sig").splitlines()
            title = next((line.lstrip("# ") for line in lines[:20]
                          if line.startswith("# ")), None)
        records.append({"directory": group, "entry": entry, "historical_title": title,
                        "file_count": len(files), "bytes": sum(f["bytes"] for f in files),
                        "files": files})
    out = {
        "schema": "vortex-public-research-catalog-v1",
        "checkpoint_date": "2026-11-02",
        "science_base_commit": "d1ef60c",
        "current_research_authority": "paused; publication and handoff only",
        "read_first": "tracks/AGENT_HANDOFF.md",
        "scope": "Git-indexed files; excludes this package and changing status/handoff documents. No ignored/private file traversal.",
        "identity_scope": "Canonical indexed Git blob bytes, independent of working-tree newline conversion; stage publication documents before rebuilding.",
        "titles_are_historical_not_current_status": True,
        "kind_is_file_format_not_evidence_validation": True,
        "totals": {"files": len(paths), "bytes": sum(r["bytes"] for r in records),
                   "technical_task_directories": sum(r["directory"].startswith("tracks/tog/tasks/") for r in records),
                   "art_study_directories": sum(r["directory"].startswith("tracks/art/studies/") for r in records)},
        "groups": records,
    }
    (HERE / "CATALOG.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["totals"]))


if __name__ == "__main__":
    main()
