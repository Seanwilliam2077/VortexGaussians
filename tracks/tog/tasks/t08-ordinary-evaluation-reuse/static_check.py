"""Small source/proof preflight; no Torch import, optimizer, freeze or GPU."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
PATHS = {"runner.py":"runner.py", "config.json":"config.json", "PROTOCOL.md":"PROTOCOL.md",
    "PROPOSAL.md":"PROPOSAL.md", "evaluation_cache.py":"evaluation_cache.py",
    "cache_contract_test.py":"cache_contract_test.py", "cache-contract-test.json":"cache-contract-test.json",
    "core.py":"../../src/core.py", "approved.npz":"../../fixtures/r22/approved.npz",
    "target-edit.npy":"../t06-authored-timing-revision/run-01/target-edit.npy",
    "brief.json":"../t06-authored-timing-revision/run-01/brief.json",
    "T06-rule":"../t06-authored-timing-revision/RULE.json",
    "T06-generator":"../t06-authored-timing-revision/generate_target.py",
    "T06-protocol":"../t06-authored-timing-revision/PROTOCOL.md",
    "T06-freeze":"../t06-authored-timing-revision/run-01/freeze.json",
    "T06-evidence-manifest":"../t06-authored-timing-revision/evidence-manifest.json",
    "warm-start.npz":"../t05-framewise-cold-start/framewise_joint-final.npz",
    "T05-result-summary.json":"../t05-framewise-cold-start/result-summary.json",
    "T05-freeze.json":"../t05-framewise-cold-start/freeze.json",
    "T04-runner.py":"../t04-framewise-feasibility/runner.py",
    "T07-runner.py":"../t07-ordinary-timing-revision/runner.py",
    "T07-config.json":"../t07-ordinary-timing-revision/config.json",
    "T07-protocol":"../t07-ordinary-timing-revision/PROTOCOL.md",
    "T07-freeze.json":"../t07-ordinary-timing-revision/freeze.json",
    "T07-result-summary.json":"../t07-ordinary-timing-revision/result-summary.json",
    "T07-raw-run-manifest.json":"../t07-ordinary-timing-revision/raw-run-manifest.json",
    "g0-proof.npz":"g0-proof.npz", "g0-proof.json":"g0-proof.json",
    "prepare_qualification_proof.py":"prepare_qualification_proof.py"}


def main():
    pins = {name:{"path":str((HERE/relative).resolve()), "bytes":(HERE/relative).stat().st_size,
        "sha256":hashlib.sha256((HERE/relative).read_bytes()).hexdigest()} for name,relative in PATHS.items()}
    for name in ("runner.py","evaluation_cache.py","cache_contract_test.py","prepare_qualification_proof.py","static_check.py"):
        compile((HERE/name).read_text(encoding="utf-8"),str(HERE/name),"exec")
    spec = importlib.util.spec_from_file_location("t08_preflight_only", HERE/"runner.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    ast_exact = module.mathematical_source_contract(pins)
    qualification = module.reuse_qualification(pins,json.loads((HERE/"config.json").read_text()),np)
    tests = json.loads((HERE/"cache-contract-test.json").read_text())
    assert tests["passed"] and all(tests["checks"].values()) and tests["checks"]["signed_zero_miss"]
    assert not tests["CUDAInitialized"] and tests["cacheSourceSHA256"] == pins["evaluation_cache.py"]["sha256"]
    assert "torch" not in sys.modules
    report = {"status":"passed_cpu_preparation_only", "mathematicalASTExact":ast_exact,
        "qualificationProofAuthentication":qualification,"cacheTinyPassed":True,
        "importedTorch":False,"executedOptimization":False,"notAnExecutionFreeze":True,
        "sourcePins":{k:{**v,"path":PATHS[k]} for k,v in pins.items()}}
    with (HERE/"static-checks.json").open("x",encoding="utf-8") as f:json.dump(report,f,indent=2);f.write("\n")
    print(json.dumps({"status":report["status"],"mathematicalASTExact":ast_exact,
        "rawFDErrors":qualification["compactProof"]["rawScalarFDErrors"],"cacheTinyPassed":True,"TorchImported":False}))


if __name__ == "__main__":
    main()
