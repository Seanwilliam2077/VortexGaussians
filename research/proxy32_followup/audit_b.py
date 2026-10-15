"""Independent P7b audit; authenticated P7 auditor is the numerical oracle.

The parent is re-audited, not trusted through a saved passed flag. No producer
module is imported. The new arm receives five independent all-pairs replays;
all states, observables, timing, and memory records are separately validated.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

PARENT_ARCHIVE = {
    "filename": "VortexGaussians-P7-shared-state-screen.zip",
    "sha256": "e09b48282f81034a724db19dfb29f4b6bd7eacdde92b3f963e90f66ae746b32d",
    "bytes": 254696730,
    "members": 34,
}
PARENT_AUDITOR_SHA = "8586760bb47bbce84fd35aee55e0c62873d9ad3d17d9a281df287eeecd336e20"
PARENT_SOURCE_NAMES = ["design.mjs", "wrapper.mjs", "metrics.mjs", "run.mjs",
                       "test.mjs", "p6-core.mjs", "PROTOCOL.md", "audit.py"]
SOURCE_FILES = ["PROTOCOL.md", "design.mjs", "run.mjs", "test.mjs",
                "baseline-pins.json", "audit_b.py"] + ["p7-frozen/" + n for n in PARENT_SOURCE_NAMES]
PROXY = {"id": "dev-proxy32-r120", "n": 32, "rate": 120, "role": "proxy"}
REFERENCE_ID = "dev-ref256-r480"
SHARED_ID = "dev-shared64-r120"
INHERITED_IDS = [REFERENCE_ID, SHARED_ID]
PINNED_FILES = {"formal/manifest.json", "freeze.json", "independent-audit.json",
                "VortexGaussians-P7-report.md"} | {
    "formal/" + name + suffix for name in INHERITED_IDS
    for suffix in (".json", ".temperatures.f64.gz")}


def read_json(path):
    def invalid(value):
        raise ValueError("nonfinite JSON token " + value)
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=invalid)


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(name):
    path = PurePosixPath(name)
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name
            or path.is_absolute() or any(p in ("", ".", "..") for p in name.split("/"))):
        raise ValueError("unsafe relative artifact path: " + str(name))
    return path


def source_hashes(source_dir):
    return {name: file_sha(Path(source_dir) / name) for name in SOURCE_FILES}


def write_new_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def authenticate_extract_parent(archive, destination):
    """Verify entire ZIP first, then stream each CRC-checked member to new files."""
    archive, destination = Path(archive), Path(destination)
    if destination.exists():
        raise ValueError("parent extraction directory must not already exist")
    if archive.stat().st_size != PARENT_ARCHIVE["bytes"] or file_sha(archive) != PARENT_ARCHIVE["sha256"]:
        raise ValueError("immutable parent archive identity mismatch")
    with zipfile.ZipFile(archive) as zipped:
        infos = zipped.infolist()
        names = [row.filename for row in infos]
        if len(names) != PARENT_ARCHIVE["members"] or len(set(names)) != len(names):
            raise ValueError("parent archive member coverage/uniqueness mismatch")
        for info in infos:
            safe_relative(info.filename)
            if info.is_dir() or ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError("unexpected directory or symlink in parent archive")
        inventory = json.loads(zipped.read("archive-files.json"))
        if set(inventory) != set(names) - {"archive-files.json"}:
            raise ValueError("parent inventory does not cover exact archive members")
        destination.mkdir(parents=True)
        verified = {}
        for info in infos:
            target = destination.joinpath(*safe_relative(info.filename).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            digest, size = hashlib.sha256(), 0
            with zipped.open(info) as src, target.open("xb") as dst:
                for block in iter(lambda: src.read(1024 * 1024), b""):
                    dst.write(block); digest.update(block); size += len(block)
            actual = {"sha256": digest.hexdigest(), "bytes": size}
            if size != info.file_size or (info.filename in inventory and actual != inventory[info.filename]):
                raise ValueError("parent inventory mismatch: " + info.filename)
            verified[info.filename] = actual
    return verified


def authenticate_existing_parent(archive, destination):
    """Authenticate a read-only extraction against the fixed archive inventory."""
    archive, destination = Path(archive), Path(destination)
    if not destination.is_dir():
        raise ValueError("baseline root must be an existing extracted parent directory")
    if archive.stat().st_size != PARENT_ARCHIVE["bytes"] or file_sha(archive) != PARENT_ARCHIVE["sha256"]:
        raise ValueError("immutable parent archive identity mismatch")
    with zipfile.ZipFile(archive) as zipped:
        names = zipped.namelist()
        if len(names) != PARENT_ARCHIVE["members"] or len(set(names)) != len(names):
            raise ValueError("parent archive member coverage/uniqueness mismatch")
        for name in names:
            safe_relative(name)
        inventory_bytes = zipped.read("archive-files.json")
        inventory = json.loads(inventory_bytes)
        if set(inventory) != set(names) - {"archive-files.json"}:
            raise ValueError("parent archive inventory coverage mismatch")
    verified = dict(inventory)
    verified["archive-files.json"] = {"sha256": hashlib.sha256(inventory_bytes).hexdigest(), "bytes": len(inventory_bytes)}
    for name, identity in verified.items():
        path = destination.joinpath(*safe_relative(name).parts)
        if not path.is_file() or path.stat().st_size != identity["bytes"] or file_sha(path) != identity["sha256"]:
            raise ValueError("parent extracted file mismatch: " + name)
    # Extra previous audit reports in this directory are not dependencies and
    # are never imported or used as evidence. Every original archive member is.
    return verified


def load_parent_auditor(parent_dir):
    path = Path(parent_dir) / "source" / "audit.py"
    if file_sha(path) != PARENT_AUDITOR_SHA:
        raise ValueError("untrusted parent auditor")
    spec = importlib.util.spec_from_file_location("p7b_authenticated_parent_audit", path)
    module = importlib.util.module_from_spec(spec)
    # Do not create __pycache__ files in the authenticated extraction.
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def check_parent_pins(pins, verified, parent_dir, source_dir, parent, checks):
    checks.check("parent:pinned-archive", pins.get("version") == 1 and pins.get("archive") == PARENT_ARCHIVE)
    rows = pins.get("files", [])
    checks.check("parent:pinned-file-coverage", len(rows) == len(PINNED_FILES)
                 and {r.get("path") for r in rows} == PINNED_FILES)
    for row in rows:
        name = row["path"]; safe_relative(name)
        checks.check("parent:pin:" + name, verified.get(name) == {"sha256": row["sha256"], "bytes": row["bytes"]})
    expected = {name: verified["source/" + name]["sha256"] for name in PARENT_SOURCE_NAMES}
    checks.check("parent:source-pin-coverage", pins.get("sourceHashes") == expected)
    checks.check("parent:imported-copies-exact", all(
        file_sha(Path(source_dir) / "p7-frozen" / name) == expected[name] for name in PARENT_SOURCE_NAMES))
    frozen = read_json(Path(parent_dir) / "freeze.json")
    checks.check("parent:frozen-source-identity", frozen.get("sourceHashes") == expected)
    result = {}
    for role, identity in (("reference", REFERENCE_ID), ("shared", SHARED_ID)):
        path = Path(parent_dir) / "formal" / (identity + ".json")
        raw = read_json(path)
        pin = pins.get("cases", {}).get(role, {})
        for key in ("id", "definition", "inputSHA256", "initialEndpoint", "finalEndpoint", "history"):
            checks.check("parent:case-pin:" + role + ":" + key, pin.get(key) == raw.get(key))
        result[role] = raw
    return result


def check_timing_contract(manifest, checks):
    c = manifest.get("timingContract", {})
    checks.check("manifest:timing-contract", c.get("freshStatePairedBlocks") == 6
                 and c.get("warmupsPerArm") == 1
                 and c.get("clock") == "performance.now CPU wall time; no renderer/GPU"
                 and c.get("gc") == "forced before each trajectory outside enclosing interval; incidental GC inside included")


def check_manifest_identity(manifest, config, checks):
    checks.check("manifest:formal-complete", manifest.get("phase") == "P7b" and manifest.get("version") == 1
                 and manifest.get("formal") is True and manifest.get("protocolComplete") is True
                 and manifest.get("executionValid") is True and manifest.get("postResultFollowup") is True
                 and manifest.get("independentAudit") == "pending-parent-reaudit-and-new-audit"
                 and manifest.get("status") == "completed-pending-independent-audit")
    checks.check("manifest:fixed-config", manifest.get("config") == config)
    checks.check("manifest:single-new-arm", manifest.get("planned") == [PROXY]
                 and manifest.get("newQualityIds") == [PROXY["id"]]
                 and manifest.get("completedIds") == [PROXY["id"]]
                 and manifest.get("requiredExecutedIds") == [PROXY["id"]]
                 and manifest.get("inheritedQualityIds") == INHERITED_IDS and manifest.get("skipped") == [])
    checks.check("manifest:fixed-reference", manifest.get("reference", {}).get("id") == REFERENCE_ID
                 and manifest["reference"].get("inherited") is True and manifest["reference"].get("selectedRole") == "R3")
    check_timing_contract(manifest, checks)


def check_baseline_identity(manifest, pins, verified, parent_manifest, archive, checks):
    expected_names = set(PINNED_FILES)
    for row in parent_manifest["cases"]:
        expected_names.add("formal/" + row["file"])
        expected_names.add("formal/" + row["history"]["file"])
    baseline = manifest.get("baseline", {})
    before, after = baseline.get("before", {}), baseline.get("after", {})
    checks.check("baseline:before-after-exact", baseline.get("unchanged") is True and before == after)
    files = before.get("files", [])
    checks.check("baseline:complete-dependency-coverage", len(files) == len(expected_names)
                 and {r.get("path") for r in files} == expected_names)
    for row in files:
        name = row["path"]
        checks.check("baseline:dependency:" + name, verified.get(name) == {"sha256": row.get("sha256"), "bytes": row.get("bytes")})
    checks.check("baseline:archive-identity", before.get("archive") == {
        "path": Path(archive).name, "bytes": PARENT_ARCHIVE["bytes"], "sha256": PARENT_ARCHIVE["sha256"]}
        and before.get("archiveExpectedSHA256") == PARENT_ARCHIVE["sha256"])
    checks.check("baseline:fixed-parent-decision", before.get("parentDecision") == "PROXY_QUALITY_STOP"
                 and before.get("referenceId") == REFERENCE_ID and before.get("sharedId") == SHARED_ID
                 and before.get("parentManifestSHA256") == verified["formal/manifest.json"]["sha256"]
                 and before.get("parentAuditSHA256") == verified["independent-audit.json"]["sha256"]
                 and before.get("sourceHashes") == pins["sourceHashes"]
                 and before.get("certification") == "Authenticated existing parent audit; independent P7b audit must still re-execute the frozen parent auditor.")


def audit_b(run_dir, source_dir, freeze_path, archive, parent_dir, parent_out, *, extract_parent=False):
    run_dir, source_dir, freeze_path = Path(run_dir), Path(source_dir), Path(freeze_path)
    manifest_path = run_dir / "manifest.json"
    manifest_sha, freeze_sha = file_sha(manifest_path), file_sha(freeze_path)
    hashes = source_hashes(source_dir)
    frozen = read_json(freeze_path)
    manifest = read_json(manifest_path)
    pins = read_json(source_dir / "baseline-pins.json")
    # Authentication precedes execution of even the independent parent auditor.
    verified = (authenticate_extract_parent if extract_parent else authenticate_existing_parent)(archive, parent_dir)
    parent = load_parent_auditor(parent_dir)
    checks = parent.Checks()
    checks.check("source:exact-coverage", set(frozen.get("sourceHashes", {})) == set(SOURCE_FILES))
    checks.check("source:before-after-frozen", hashes == frozen.get("sourceHashes") == manifest.get("sourceHashes")
                 == manifest.get("sourceHashesAfter") and manifest.get("sourcesUnchanged") is True)
    reused_raw = check_parent_pins(pins, verified, parent_dir, source_dir, parent, checks)
    parent_manifest = read_json(Path(parent_dir) / "formal" / "manifest.json")
    check_baseline_identity(manifest, pins, verified, parent_manifest, archive, checks)

    # This re-executes the parent's independent all-state checks and 30 selected
    # all-pairs physical replays. It never invokes the producer or re-simulates.
    parent_report = parent.audit_run(Path(parent_dir) / "formal", Path(parent_dir) / "source", Path(parent_dir) / "freeze.json")
    write_new_json(parent_out, parent_report)
    stored_parent = read_json(Path(parent_dir) / "independent-audit.json")
    checks.check("parent:actual-re-audit-passed", parent_report.get("status") == "passed"
                 and parent_report.get("independentAuditPassed") is True and not parent_report.get("failedChecks"))
    checks.check("parent:re-audit-exact-saved-report", parent_report == stored_parent)
    checks.check("parent:fixed-result", parent_report.get("scientificDecision") == "PROXY_QUALITY_STOP"
                 and parent_report.get("reference", {}).get("accepted") is True
                 and parent_report["reference"].get("selectedRole") == "R3"
                 and parent_report.get("quality", {}).get("shared", {}).get("passed") is True
                 and parent_report["quality"]["proxy"].get("passed") is False
                 and parent_report.get("timing", {}).get("status") == "skipped")

    check_manifest_identity(manifest, parent.CONFIG, checks)
    parent.check_subset(manifest["reference"].get("signal"), parent_report["reference"]["signal"], "reference:signal", checks)
    records = manifest.get("newCases", [])
    checks.check("manifest:one-new-record", len(records) == 1)
    if len(records) != 1:
        raise ValueError("exactly one new quality record required")
    record = records[0]; filename = PROXY["id"] + ".json"; path = run_dir / filename
    raw_before = file_sha(path)
    checks.check("proxy:record-identity", record.get("id") == PROXY["id"] and record.get("role") == "proxy"
                 and record.get("file") == filename and record.get("bytes") == path.stat().st_size
                 and record.get("sha256") == raw_before)
    text = path.read_text(encoding="utf-8-sig"); raw = read_json(path)
    checks.check("proxy:history-manifest-link", record.get("history") == raw.get("history"))
    checks.check("manifest:no-unlisted-quality", sorted(p.name for p in run_dir.glob("dev-*.json")) == [filename])
    history_path = run_dir / (PROXY["id"] + ".temperatures.f64.gz")
    history_before = file_sha(history_path)
    checks.check("manifest:no-unlisted-history", sorted(p.name for p in run_dir.glob("dev-*.temperatures.f64.gz")) == [history_path.name])
    proxy_summary, proxy_obs = parent.audit_arm(raw, PROXY, text, run_dir, checks)
    comparison = parent.compare_observations(proxy_obs, reused_raw["reference"]["observations"])
    shared_comparison = parent_report["quality"]["shared"]["comparison"]
    proxy_passed = parent.passes(comparison, .02)
    quality = {"status": "completed", "shared": {"inherited": True, "comparison": shared_comparison, "passed": True},
               "proxy": {"inherited": False, "comparison": comparison, "passed": proxy_passed}}
    checks.check("quality:completed", manifest.get("quality", {}).get("status") == "completed")
    for role in ("shared", "proxy"):
        actual = manifest["quality"][role]; expected = quality[role]
        checks.check("quality:id:" + role, actual.get("id") == (SHARED_ID if role == "shared" else PROXY["id"]))
        checks.check("quality:inheritance:" + role, actual.get("inherited") is expected["inherited"])
        checks.check("quality:pass:" + role, actual.get("passed") is expected["passed"])
        parent.check_comparison(actual["comparison"], expected["comparison"], "quality:" + role, checks)
    shared_summary = next(row for row in parent_report["cases"] if row["id"] == SHARED_ID)
    timing = manifest.get("timing", {})
    if proxy_passed:
        timing_report = parent.audit_timing(timing, {"shared": shared_summary, "proxy": proxy_summary}, checks)
        decision = "PROXY32_STRICT_FOLLOWUP_SCREEN" if timing_report["screen"]["passed"] else "QUALITY_PASS_NO_STRICT_DOMINANCE"
    else:
        decision = "PROXY32_QUALITY_STOP"
        checks.check("timing:required-skip", timing.get("status") == "skipped" and timing.get("reason") == decision
                     and timing.get("order") == parent.TIMING_ORDER and not timing.get("runs")
                     and not timing.get("blocks") and not timing.get("warmups"))
        timing_report = {"status": "skipped", "reason": decision}
    checks.check("manifest:decision", manifest.get("decision") == decision)
    after = source_hashes(source_dir)
    checks.check("source:stable-during-audit", after == hashes == frozen.get("sourceHashes"))
    checks.check("manifest:stable-during-audit", file_sha(manifest_path) == manifest_sha)
    checks.check("freeze:stable-during-audit", file_sha(freeze_path) == freeze_sha)
    checks.check("proxy:raw-stable", file_sha(path) == raw_before)
    checks.check("proxy:history-stable", file_sha(history_path) == history_before)
    checks.check("parent:archive-stable", file_sha(archive) == PARENT_ARCHIVE["sha256"])
    for name, identity in verified.items():
        item = Path(parent_dir) / name
        checks.check("parent:extracted-stable:" + name, item.stat().st_size == identity["bytes"] and file_sha(item) == identity["sha256"])
    failures = [row for row in checks.rows if not row["passed"]]
    return {"phase": "P7b", "status": "failed" if failures else "passed", "independentAuditPassed": not failures,
            "scientificDecision": decision, "sourceHashes": hashes, "sourceHashesAfter": after,
            "freezeSHA256": freeze_sha, "manifestSHA256": manifest_sha,
            "parent": {"archive": PARENT_ARCHIVE, "verifiedMembers": len(verified),
                       "reAuditSHA256": file_sha(parent_out), "reAuditFile": Path(parent_out).name,
                       "reAuditStatus": parent_report["status"], "reAuditExactlyMatchesArchivedReport": parent_report == stored_parent,
                       "inheritedCounts": parent_report["counts"], "referenceId": REFERENCE_ID, "sharedId": SHARED_ID},
            "quality": quality, "timing": timing_report, "cases": [proxy_summary],
            "counts": {"newQualityArms": 1, "inheritedQualityArmsUsed": 2, "allNewStatesAudited": 121,
                       "newTemperatureComponents": 121 * 2080, "newCommonObservations": 121,
                       "newIndependentPhysicalSteps": 5, "newIndependentPhysicalPairs": 5 * 2048 * 32,
                       "timedTrajectories": len(timing_report.get("runs", []))},
            "scope": "Post-P7 single-budget follow-up; parent trajectories reused and independently re-audited; no new physical solver, renderer, novelty, or budget search.",
            "checks": checks.rows, "failedChecks": failures}


def selftest():
    """Tiny schema/cost negative controls; no development-scene trajectory."""
    path = Path(__file__).resolve().parent / "p7-frozen" / "audit.py"
    if file_sha(path) != PARENT_AUDITOR_SHA:
        raise ValueError("selftest requires the authenticated frozen auditor copy")
    spec = importlib.util.spec_from_file_location("p7b_parent_audit_selftest", path)
    parent = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True; spec.loader.exec_module(parent)
    finally:
        sys.dont_write_bytecode = previous
    outcomes = []

    def expect(name, action, passed):
        checks = parent.Checks()
        action(checks)
        result = all(row["passed"] for row in checks.rows)
        outcomes.append({"name": name, "passed": result is passed,
                         "auditAccepted": result, "expectedAcceptance": passed})

    good = {"phase": "P7b", "version": 1, "formal": True, "protocolComplete": True,
            "executionValid": True, "postResultFollowup": True,
            "independentAudit": "pending-parent-reaudit-and-new-audit",
            "status": "completed-pending-independent-audit", "config": parent.CONFIG,
            "planned": [PROXY], "newQualityIds": [PROXY["id"]], "completedIds": [PROXY["id"]],
            "requiredExecutedIds": [PROXY["id"]], "inheritedQualityIds": INHERITED_IDS, "skipped": [],
            "reference": {"inherited": True, "id": REFERENCE_ID, "selectedRole": "R3"},
            "timingContract": {"freshStatePairedBlocks": 6, "warmupsPerArm": 1,
                               "clock": "performance.now CPU wall time; no renderer/GPU",
                               "gc": "forced before each trajectory outside enclosing interval; incidental GC inside included"}}
    expect("exact-new-arm-metadata-accepts", lambda c: check_manifest_identity(good, parent.CONFIG, c), True)
    for name, key, value in (("extra-budget-rejected", "planned", [PROXY, {**PROXY, "n": 48}]),
                             ("missing-new-arm-rejected", "completedIds", []),
                             ("new-reference-rejected", "reference", {"id": "dev-ref512-r480", "inherited": True, "selectedRole": "R3"}),
                             ("concealed-post-result-status-rejected", "postResultFollowup", False)):
        bad = copy.deepcopy(good); bad[key] = value
        expect(name, lambda c, m=bad: check_manifest_identity(m, parent.CONFIG, c), False)

    parent_cases = [{"file": d["id"] + ".json", "history": {"file": d["id"] + ".temperatures.f64.gz"}}
                    for d in parent.DEFINITIONS]
    names = PINNED_FILES | {"formal/" + r[k]["file"] if k == "history" else "formal/" + r["file"]
                           for r in parent_cases for k in ("file", "history")}
    identities = {n: {"sha256": "a" * 64, "bytes": 1} for n in names}
    pins = {"sourceHashes": {n: "b" * 64 for n in PARENT_SOURCE_NAMES}}
    before = {"archive": {"path": PARENT_ARCHIVE["filename"], "bytes": PARENT_ARCHIVE["bytes"], "sha256": PARENT_ARCHIVE["sha256"]},
              "archiveExpectedSHA256": PARENT_ARCHIVE["sha256"],
              "files": [{"path": n, **identities[n]} for n in sorted(names)], "sourceHashes": pins["sourceHashes"],
              "parentManifestSHA256": "a" * 64, "parentAuditSHA256": "a" * 64,
              "parentDecision": "PROXY_QUALITY_STOP", "referenceId": REFERENCE_ID, "sharedId": SHARED_ID,
              "certification": "Authenticated existing parent audit; independent P7b audit must still re-execute the frozen parent auditor."}
    identity_manifest = {"baseline": {"before": before, "after": copy.deepcopy(before), "unchanged": True}}
    verify = lambda m, c: check_baseline_identity(m, pins, identities, {"cases": parent_cases}, PARENT_ARCHIVE["filename"], c)
    expect("complete-parent-dependencies-accept", lambda c: verify(identity_manifest, c), True)
    for name, mutate in (("missing-parent-dependency-rejected", lambda b: b["files"].pop()),
                         ("changed-parent-dependency-rejected", lambda b: b["files"][0].update(sha256="c" * 64)),
                         ("changed-parent-archive-rejected", lambda b: b["archive"].update(sha256="d" * 64))):
        bad = copy.deepcopy(identity_manifest); mutate(bad["baseline"]["before"])
        # Make before/after equal so the substantive identity check must catch it.
        bad["baseline"]["after"] = copy.deepcopy(bad["baseline"]["before"])
        expect(name, lambda c, m=bad: verify(m, c), False)

    sm = {**parent.persistent_memory(64), "maximumAlgorithmOwnedArrayBytes": 600000}
    pm = {**parent.persistent_memory(32), "maximumAlgorithmOwnedArrayBytes": 300000}
    blocks = [{"block": i, "shared": 100., "proxy": 70.} for i in range(6)]
    outcomes.append({"name": "strict-cost-and-dual-memory-positive", "passed": parent.cost_decision(blocks, sm, pm)["passed"]})
    bad = {**pm, "maximumAlgorithmOwnedArrayBytes": sm["maximumAlgorithmOwnedArrayBytes"] - 196608 + 1}
    outcomes.append({"name": "strong-alias-peak-memory-negative", "passed": not parent.cost_decision(blocks, sm, bad)["passed"]})
    bad_blocks = [dict(b, proxy=81.) for b in blocks]
    outcomes.append({"name": "twenty-percent-cost-margin-negative", "passed": not parent.cost_decision(bad_blocks, sm, pm)["passed"]})
    return {"status": "passed" if all(x["passed"] for x in outcomes) else "failed", "checks": outcomes,
            "scope": "Synthetic metadata and cost/memory negative controls only; no proxy32 development trajectory or parent full re-audit."}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        parser = argparse.ArgumentParser(description="P7b audit tiny selftest; no formal trajectory")
        parser.add_argument("--selftest", action="store_true", required=True)
        parser.add_argument("--out", type=Path, required=True)
        args = parser.parse_args(argv)
        if args.out.exists():
            parser.error("selftest output already exists")
        report = selftest(); write_new_json(args.out, report)
        print(json.dumps({"status": report["status"], "checks": len(report["checks"])}))
        return 0 if report["status"] == "passed" else 1
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--source-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--parent-archive", type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--parent-extract", type=Path, help="authenticate and extract parent into a new directory")
    group.add_argument("--baseline-root", type=Path, help="authenticate an existing extraction without modifying it")
    parser.add_argument("--parent-out", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    parent_dir = args.parent_extract if args.parent_extract is not None else args.baseline_root
    for path in (args.out, args.parent_out, args.parent_extract):
        if path is None:
            continue
        if path.exists():
            parser.error("output/extraction destination already exists: " + str(path))
    if args.out.resolve() == args.parent_out.resolve():
        parser.error("new and parent audit outputs must be distinct")
    for output in (args.out.resolve(), args.parent_out.resolve()):
        if parent_dir.resolve() in output.parents:
            parser.error("audit outputs must be outside the authenticated parent extraction")
    report = audit_b(args.run, args.source_dir, args.freeze, args.parent_archive, parent_dir, args.parent_out,
                     extract_parent=args.parent_extract is not None)
    write_new_json(args.out, report)
    print(json.dumps({"status": report["status"], "decision": report["scientificDecision"],
                      "counts": report["counts"], "failedChecks": len(report["failedChecks"])}))
    return 0 if report["independentAuditPassed"] else 1


if __name__ == "__main__":
    sys.exit(main())
