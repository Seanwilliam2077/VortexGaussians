"""Publish compact existing T08 records; no numerical solver or GPU imports.

The complete original run remains untouched in the Git-ignored runs directory.
This is a packaging step, not the independent numerical audit.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()


def write(path, data):
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")


def metric_summary(m):
    return {"passedOwnStop": m["passed"], "jointPassed": m["jointPassed"],
        "editPassed": m["edit"]["passed"], "protectionPassed": m["protectionPassed"],
        "maxEditRelativeRMS": max(m["edit"]["relativeRMS"]),
        "maxEditAbsoluteRMS": max(m["edit"]["absoluteRMS"]),
        "editPassingFrames": sum(m["edit"]["passedFrames"]),
        "maxProtectRelativeRMS": max(x for p in m["protected"] for x in p["relativeRMS"]),
        "maxProtectAbsoluteRMS": max(x for p in m["protected"] for x in p["absoluteRMS"]),
        "protectPassingROIFrames": sum(x for p in m["protected"] for x in p["passedFrames"]),
        **{k: m[k] for k in ("coefficientMax", "coefficientRMS", "forceMaxComponent", "forceRMS",
                             "densityMin", "densityMax", "alphaMin", "alphaMax", "finite")}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, default=HERE/"runs/run-01")
    args = p.parse_args()
    run = args.run.resolve()
    supervisor = json.loads((run/"supervisor.json").read_text(encoding="utf-8"))
    worker_summary = run/"worker/summary.json"
    report = json.loads(worker_summary.read_text(encoding="utf-8")) if worker_summary.exists() else {
        "status": "failed", "scope": "T08 worker did not produce a summary", "arms": [], "raw": {},
        "qualification": {"status": "unavailable"}, "error": "See preserved supervisor and stdout/stderr"}
    if supervisor["status"] == "starting" or report["status"] in ("starting", "running"):
        raise ValueError("Do not publish a still-running experiment")
    for name in ("result-summary.json", "raw-run-manifest.json", "publication-manifest.json"):
        if (HERE/name).exists():
            raise FileExistsError(HERE/name)
    published = {}
    arms = []
    for arm in report["arms"]:
        name = arm["arm"] + "-final.npz"
        relative = arm["arm"] + "/T06/final.npz"
        src = run/"worker"/relative
        if src.exists():
            if sha(src) != report["raw"][relative]["sha256"]:
                raise ValueError("Final file differs from worker manifest")
            dst = HERE/name
            if dst.exists():
                raise FileExistsError(dst)
            shutil.copyfile(src, dst)
            published[name] = {"bytes": dst.stat().st_size, "sha256": sha(dst),
                               "byteExactLocalCopy": sha(dst) == sha(src)}
        compact = {k: arm[k] for k in ("id", "arm", "warmStart", "status", "rolloutsStarted",
                   "rolloutsCompleted", "closures", "acceptanceRollouts", "returnedSteps", "budget",
                   "termination", "passed", "outerUpdates", "wallSecondsIncludingAcceptanceAndEvidenceIO",
                   "synchronizedClosureSeconds", "synchronizedAcceptanceSeconds", "synchronizedFinalVerificationSeconds", "memory",
                   "backwardCalls", "acceptanceChecks", "acceptanceCacheHits", "acceptanceCacheMisses", "initialForwardCalls",
                   "finalVerificationRollouts", "cacheWriteSeconds", "maxCachePayloadBytes", "cacheStoreFailures",
                   "cacheInvalidations", "lastCacheInvalidation", "taskGatesPassed", "finalVerificationPassed", "finalVerification") if k in arm}
        if "finalMetrics" in arm:
            compact["final"] = metric_summary(arm["finalMetrics"])
            compact["finalPerFrameMetrics"] = arm["finalMetrics"]
        compact["acceptedHistory"] = [{"returnedStep": x["returnedStep"], "rollout": x["rollout"],
             "rawFile": x["rawFile"], "ALObjective": x["ALObjective"], "forwardExecuted":x["forwardExecuted"],
             "cacheResult":x["cacheResult"], "cacheLookupSeconds":x["cacheLookupSeconds"],
             "forwardSeconds":x["forwardSeconds"], "acceptanceAndForceSeconds":x["acceptanceAndForceSeconds"], **metric_summary(x["metrics"])} for x in arm["accepted"]]
        closures = [x for x in arm["calls"] if x["kind"] == "closure"]
        compact["closureDiagnostics"] = {"count": len(closures),
            "withPositiveProtectionViolation": sum(x["penaltyRecord"]["protectedPositiveConstraintCount"] > 0 for x in closures),
            "withPositiveEffectiveProtectionPHR": sum(x["penaltyRecord"]["protectedPHREffective"] > 0 for x in closures),
            "withActiveProtectionBranch": sum(x["penaltyRecord"]["protectedBranchCountEffective"] > 0 for x in closures),
            "withPositiveEditViolation": sum(x["penaltyRecord"]["editPositiveConstraintCount"] > 0 for x in closures),
            "withActiveEditBranch": sum(x["penaltyRecord"]["editBranchCountEffective"] > 0 for x in closures),
            "maxEffectiveProtectionPHR": max((x["penaltyRecord"]["protectedPHREffective"] for x in closures), default=0)}
        if "budgetRollback" in arm:
            compact["budgetRollback"] = arm["budgetRollback"]
        arms.append(compact)
    summary = {"schema": "t08-published-summary-v1", "status": report["status"],
        "decision": report.get("decision"), "scope": report["scope"],
        "allOriginalGatesPassed":report.get("allOriginalGatesPassed"), "allReuseVerificationsPassed":report.get("allReuseVerificationsPassed"),
        "interpretation": "One ordinary closure-output reuse check on the same T07 task and T05 initial x. Prior T07 G0 is authenticated, not rerun. Counts and solve wall include cache/fallback/final verification; differing G0 policies preclude a worker-wall speedup claim. No new optimization method or statistical speedup claim.",
        "qualification": report["qualification"], "arms": arms,
        "costScope": report.get("costScope"),
        "sourcesAndInputsUnchanged": report.get("sourcesAndInputsUnchanged", False),
        "pins": {k: {x: v[x] for x in ("sha256", "bytes")} for k,v in report.get("pinsBefore", {}).items()},
        "environment": report.get("environment"), "resources": report.get("resources", report.get("resourcesAtFailure")),
        "totalWorkerWallSeconds": report.get("totalWallSecondsIncludingStartupQualificationAndIO"),
        "supervisor": {k: supervisor.get(k) for k in ("status", "returnCode", "wallLimitSeconds", "wallSeconds")},
        "completeRun": {"relativePath": str(run.relative_to(HERE)).replace("\\", "/"),
                        "availability": "Local preserved files, Git-ignored; not supplied by a repository clone",
                        "workerSummarySHA256": sha(worker_summary) if worker_summary.exists() else None},
        "publishedFinalArrays": published, "independentAudit": "Recorded separately by the independent reviewer"}
    if "error" in report:
        summary["error"] = report["error"]
    write(HERE/"result-summary.json", summary)
    write(HERE/"raw-run-manifest.json", {"scope": "Hashes of preserved local raw files, not embedded data or replay proof",
        "workerSummarySHA256": sha(worker_summary) if worker_summary.exists() else None, "files": report["raw"],
        "logs": {n: {"sha256": sha(run/n), "bytes": (run/n).stat().st_size} for n in ("stdout.log", "stderr.log", "supervisor.json")}})
    paths = [HERE/n for n in ("runner.py", "PROTOCOL.md", "config.json", "freeze.json", "publish_results.py",
                             "result-summary.json", "raw-run-manifest.json", "static_check.py", "static-checks.json",
                             "evaluation_cache.py", "cache_contract_test.py", "cache-contract-test.json",
                             "cache-contract-test-before-byte-review.json", "g0-proof.npz", "g0-proof.json", "prepare_qualification_proof.py")] + [HERE/n for n in published]
    write(HERE/"publication-manifest.json", {"scope": "Compact T08 package; full accepted trajectories remain local as explicitly documented",
        "files": [{"path": p.name, "bytes": p.stat().st_size, "sha256": sha(p)} for p in paths]})
    print(json.dumps({"status": "published_without_simulation", "arms": [{"arm": a["arm"], "final": a.get("final")} for a in arms],
                      "publicationBytes": sum(p.stat().st_size for p in paths)}, indent=2))


if __name__ == "__main__":
    main()
