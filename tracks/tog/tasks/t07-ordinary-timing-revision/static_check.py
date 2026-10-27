"""Small CPU-only source/input preflight; no Torch import, fitting or freeze."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
PATHS = {"runner.py": "runner.py", "config.json": "config.json", "PROTOCOL.md": "PROTOCOL.md",
    "PROPOSAL.md": "PROPOSAL.md", "core.py": "../../src/core.py",
    "approved.npz": "../../fixtures/r22/approved.npz",
    "target-edit.npy": "../t06-authored-timing-revision/run-01/target-edit.npy",
    "brief.json": "../t06-authored-timing-revision/run-01/brief.json",
    "T06-rule": "../t06-authored-timing-revision/RULE.json",
    "T06-generator": "../t06-authored-timing-revision/generate_target.py",
    "T06-protocol": "../t06-authored-timing-revision/PROTOCOL.md",
    "T06-freeze": "../t06-authored-timing-revision/run-01/freeze.json",
    "T06-evidence-manifest": "../t06-authored-timing-revision/evidence-manifest.json",
    "warm-start.npz": "../t05-framewise-cold-start/framewise_joint-final.npz",
    "T05-result-summary.json": "../t05-framewise-cold-start/result-summary.json",
    "T05-freeze.json": "../t05-framewise-cold-start/freeze.json",
    "T04-runner.py": "../t04-framewise-feasibility/runner.py",
    "T04-config.json": "../t04-framewise-feasibility/config.json"}


def main():
    pins = {name: {"path": str((HERE/relative).resolve()), "bytes": (HERE/relative).stat().st_size,
        "sha256": hashlib.sha256((HERE/relative).read_bytes()).hexdigest()} for name, relative in PATHS.items()}
    for name in ("runner.py", "static_check.py"):
        compile((HERE/name).read_text(encoding="utf-8"), str(HERE/name), "exec")
    spec = importlib.util.spec_from_file_location("t07_preflight_only", HERE/"runner.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    exact = module.mathematical_source_contract(pins)
    config = json.loads((HERE/"config.json").read_text())
    old = json.loads(Path(pins["T04-config.json"]["path"]).read_text())
    assert config["model"] == old["model"]
    assert {k:v for k,v in config["task"].items() if k != "ids"} == {k:v for k,v in old["task"].items() if k != "ids"}
    assert {k:v for k,v in config["baseline"].items() if k != "start_policy"} == {k:v for k,v in old["baseline"].items() if k != "start_policy"}
    with np.load(pins["approved.npz"]["path"], allow_pickle=False) as z:
        arrays = {"v0":z["v0"], "rho0":z["rho0"], "approved":z["frames"]}
    arrays["target_T06"] = np.load(pins["target-edit.npy"]["path"], allow_pickle=False)
    with np.load(pins["warm-start.npz"]["path"], allow_pickle=False) as z:
        arrays["warm_x"] = z["x"]
    assert set(arrays) == set(config["array_manifest"])
    for key, value in arrays.items():
        assert {"shape":list(value.shape),"dtype":value.dtype.str,
                "sha256":hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()} == config["array_manifest"][key]
        assert np.isfinite(value).all()
    source = json.loads(Path(pins["T05-result-summary.json"]["path"]).read_text())
    assert source["status"] == "completed" and source["sourcesAndInputsUnchanged"] and source["arms"][0]["final"]["jointPassed"]
    assert source["publishedFinalArrays"]["framewise_joint-final.npz"]["sha256"] == pins["warm-start.npz"]["sha256"]
    assert "torch" not in sys.modules
    report = {"status":"passed_cpu_preparation_only", "mathematicalASTExact":exact,
        "sameNumericalConfiguration":True, "authenticatedInputArrays":list(arrays), "T05QualifiedSource":True,
        "TorchImported":False,"GPUExecuted":False,"qualificationExecuted":False,"optimizationExecuted":False,
        "notAnExecutionFreeze":True,"sourcePins":{k:{**v,"path":PATHS[k]} for k,v in pins.items()}}
    with (HERE/"static-checks.json").open("x",encoding="utf-8") as f:json.dump(report,f,indent=2);f.write("\n")
    print(json.dumps({k:v for k,v in report.items() if k != "sourcePins"}))


if __name__ == "__main__":
    main()
