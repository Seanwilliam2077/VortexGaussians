"""Bounded CPU-only interface checks; no Torch import, solver, or optimization."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from src.spec import load, validate


def main():
    checks = []

    def record(name, value):
        checks.append({"name": name, "passed": bool(value)})

    spec, result = load(HERE/"configs/artist-brief-001.json")
    record("draft_valid_without_target", result["valid"] and not result["targetAttached"])
    record("draft_cannot_score_without_target", not validate(spec, True)["valid"])
    mutations = [
        ("out_of_image_roi", lambda s: s["task"].update(edit_roi=[10, 12, 65, 55])),
        ("overlapping_protection", lambda s: s["task"].update(protected_rois=[[20, 20, 40, 40]])),
        ("duplicate_time", lambda s: s["task"].update(frames=[16, 16])),
        ("out_of_time", lambda s: s["task"].update(frames=[0, 41])),
        ("wrong_control_shape", lambda s: s["control"].update(shape=[3, 8, 8, 8])),
        ("invalid_quality_gate", lambda s: s["task"]["quality"].update(protect_relative=0)),
        ("undeclared_target_origin", lambda s: s["target"].update(origin="unknown")),
        ("machine_path", lambda s: s["target"].update(path="C:/private/target.npy", sha256="0"*64)),
        ("holdout_used_for_tuning", lambda s: (s["target"].update(role="holdout"), s["evaluation"].update(phase="holdout", used_for_tuning=True))),
        ("second_rollout_forbidden", lambda s: s["budget"].update(max_rollouts=2)),
    ]
    for name, mutate in mutations:
        bad = copy.deepcopy(spec); mutate(bad)
        record(name, not validate(bad)["valid"])
    # Subprocess assertion checks the actual default CLI, not an emulation.
    # Use direct imported main so its return does not stop the module check.
    code = "import importlib.util,sys;p=sys.argv[1];s=importlib.util.spec_from_file_location('portable_plan',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);sys.argv=[p];assert m.main()==0;assert 'torch' not in sys.modules;assert 'numpy' not in sys.modules"
    proc = subprocess.run([sys.executable, "-I", "-B", "-c", code, str(HERE/"research.py")], capture_output=True, text=True, timeout=20)
    record("default_plan_no_numpy_no_torch", proc.returncode == 0)
    if proc.returncode:
        print(proc.stderr, file=sys.stderr)
    old = ast.parse((HERE/"fixtures/r20/scene.py").read_text(encoding="utf-8"))
    new = ast.parse((HERE/"src/scene.py").read_text(encoding="utf-8"))
    function = lambda tree: ast.dump(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "initial_state"), include_attributes=False)
    record("initial_state_AST_unchanged", function(old) == function(new))
    import research
    research.source_pins()
    frozen, _ = load(HERE/"fixtures/r22/brief.json", True)
    history = research.history(frozen, HERE/"fixtures/r22/brief.json")
    record("r22_negative_unchanged", history["negativeFixturePreserved"])
    record("r22_pixel_pass_does_not_override_semantic_failure", history["metrics"]["pixelQualityPassed"] and not history["metrics"]["semanticGate"]["passed"])
    record("torch_never_imported", "torch" not in sys.modules)
    summary = {"status": "passed" if all(x["passed"] for x in checks) else "failed",
               "scope": "CPU schema/plan/historical saved-image arithmetic only; no rollout, GPU, gradient, optimization or new qualification",
               "checks": checks, "historicalMaximumUpperShift": history["metrics"]["semanticGate"]["maximumUpperShift"],
               "historicalSemanticFrames": history["metrics"]["semanticGate"]["frameCount"],
               "historicalTaskQualified": history["historicalTaskQualified"],
               "coreSHA256": hashlib.sha256((HERE/"src/core.py").read_bytes()).hexdigest()}
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
