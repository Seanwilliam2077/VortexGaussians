"""CPU-only T05 source/proof preflight; does not freeze or import Torch."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
PATHS = {"runner.py": "runner.py", "config.json": "config.json", "PROTOCOL.md": "PROTOCOL.md",
    "core.py": "../../src/core.py", "approved.npz": "../../fixtures/r22/approved.npz",
    "target-edit.npy": "../t02-authored-upper-bend/run-01/target-edit.npy",
    "brief.json": "../t02-authored-upper-bend/run-01/brief.json",
    "T04-runner.py": "../t04-framewise-feasibility/runner.py",
    "T04-config.json": "../t04-framewise-feasibility/config.json",
    "T04-freeze.json": "../t04-framewise-feasibility/freeze.json",
    "T04-result-summary.json": "../t04-framewise-feasibility/result-summary.json",
    "T04-raw-run-manifest.json": "../t04-framewise-feasibility/raw-run-manifest.json",
    "g0-proof.npz": "g0-proof.npz", "g0-proof.json": "g0-proof.json",
    "prepare_qualification_proof.py": "prepare_qualification_proof.py"}


def main():
    pins = {}
    for name, relative in PATHS.items():
        path = HERE / relative
        pins[name] = {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "bytes": path.stat().st_size}
    for name in ("runner.py", "prepare_qualification_proof.py", "static_check.py"):
        compile((HERE/name).read_text(encoding="utf-8"), str(HERE/name), "exec")
    spec = importlib.util.spec_from_file_location("t05_preflight_only", HERE / "runner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    qualification = module.reuse_qualification(pins, json.loads((HERE/"config.json").read_text()), np)
    assert "torch" not in sys.modules
    report = {"status": "passed_cpu_preparation_only", "executedOptimization": False,
        "importedTorch": False, "sourcePins": {k: {**v, "path": PATHS[k]} for k, v in pins.items()},
        "qualificationProofAuthentication": qualification, "notAnExecutionFreeze": True}
    output = HERE / "static-checks.json"
    if output.exists():
        raise FileExistsError(output)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "rawFDErrors": qualification["compactProof"]["rawScalarFDErrors"],
        "rawArrays": qualification["compactProof"]["verifiedRawArrayCount"], "TorchImported": False}))


if __name__ == "__main__":
    main()
