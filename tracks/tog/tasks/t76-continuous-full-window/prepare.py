"""Freeze T76 nonarray sources and inherited reference metadata, without numerics."""
import ast
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OLD = HERE.parent / "t71-causal-full-window" / "input-manifest.json"
NAMES = ["frozen_identity_runtime", "rules_and_startup_regression",
    "complete_causal_paths_and_counts", "path_and_checkpoint_evaluator",
    "continuous_polishing_and_fallback", "reference_eligibility_and_score_integration",
    "time_comparison_integration_and_moments", "complete_work_accounting",
    "final_identity_preservation"]


def identity(path):
    if path.suffix.lower() in (".npz", ".npy"):
        raise ValueError("no raw array reads or hashes during preparation")
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def contained(relative):
    path = (REPO / relative).resolve()
    if not path.is_relative_to(REPO) or ":" in relative or ".." in Path(relative).parts:
        raise ValueError("noncontained source")
    return path


def main():
    if sys.argv[1:] != ["freeze"]:
        print("Preparation only. Explicit command: python prepare.py freeze. No scientific invocation.")
        return 0
    destination = HERE / "input-manifest.json"
    if destination.exists() or (HERE / "invocation.json").exists():
        raise FileExistsError("existing T76 freeze or invocation")
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip()
    if branch != "research/dual-track-exploration":
        raise ValueError("wrong branch")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    if subprocess.check_output(["git", "diff", "--name-only"], cwd=REPO).strip() or \
       subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=REPO).strip():
        raise ValueError("freeze reviewed sources in Git first")
    previous = json.loads(OLD.read_bytes())
    inputs = {}
    for item in previous["inputs"]:
        relative = item["path"]
        current = identity(contained(relative))
        if current != {key: item[key] for key in ("bytes", "sha256")}:
            raise ValueError("inherited nonarray evidence changed: " + relative)
        inputs[relative] = dict(path=relative, **current)
    # The old manifest inherits the original three-way T60/T61 raw identity chain.
    # Rehash its unchanged nonarray evidence; do not parse old reference statistics.
    additions = [OLD] + [HERE / name for name in
        (".gitignore", "BRIEF.md", "PROTOCOL.md", "polish.py", "measure.py", "prepare.py", "run_once.py")]
    for path in additions:
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        relative = path.relative_to(REPO).as_posix()
        inputs[relative] = dict(path=relative, **identity(path))
    raw_stats = []
    for item in previous["raw_inputs"]:
        path = contained(item["path"])
        size = path.stat().st_size
        if size != item["bytes"]:
            raise ValueError("raw file metadata length changed: " + item["path"])
        raw_stats.append({"path": item["path"], "bytes": size, "body_opened": False})
    if len(raw_stats) != 10:
        raise ValueError("expected ten inherited snapshots")
    executable = dict(previous["executable"])
    if Path(sys.executable).resolve() != Path(executable["path"]).resolve() or \
       identity(Path(executable["path"])) != {key: executable[key] for key in ("bytes", "sha256")}:
        raise ValueError("bundled executable changed")
    memory_path = HERE.parent / "t57-finer-short-reference" / "memory.py"
    spec = importlib.util.spec_from_file_location("t76_preflight_memory", memory_path)
    memory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(memory)
    host = memory.host_memory()
    if host["available_physical_bytes"] < 1073741824:
        raise RuntimeError("insufficient launch memory")
    manifest = dict(previous)
    manifest.pop("parent_preservation", None)
    manifest.update(schema="t76-continuous-full-window-freeze-v1",
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), parent_commit=head,
        inputs=[inputs[key] for key in sorted(inputs)], expected_check_names=NAMES,
        child_timeout_seconds=180, prior_scientific_child_seconds=2018.39971949975,
        prior_scientific_series_scope=previous["prior_scientific_series_scope"] + ["T71", "T74", "T75"],
        prediction_source_paths=["tracks/tog/tasks/t70-causal-projector-qualification/physics.py",
            "tracks/tog/tasks/t70-causal-projector-qualification/search.py",
            (HERE / "polish.py").relative_to(REPO).as_posix()],
        inherited_reference_manifest=dict(path=OLD.relative_to(REPO).as_posix(), **identity(OLD)),
        raw_identity_origin="Unchanged T71 manifest and all inherited nonarray evidence; T60 execution + snapshot metadata + T61 qualification chain, checked again by post-seal scorer.",
        preparation=dict(scientific_invocations=0, raw_array_reads=0, raw_array_hashes=0,
            raw_file_metadata=raw_stats, host_memory=host, source_files=len(inputs)),
        polishing=dict(maximum_linearizations=20, maximum_backtracks=8,
            maximum_svds_per_linearization=9, maximum_model_evaluations_per_step=162,
            rank_relative_cutoff=1e-10, relative_damping=1e-6,
            normalized_gradient_limit=1e-7, improvement_motion_scale=1e-10,
            seed_roundoff_factor=64, armijo_squared_norm_factor=2e-4,
            dc_over_current_Gamma_cap=.25, dlog_width_cap=.20, dz_over_search_Z_cap=.25,
            final_gain_spread_factor=10),
        freezer=dict(path=(HERE / "prepare.py").relative_to(REPO).as_posix(), **identity(HERE / "prepare.py")))
    with destination.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"manifest": identity(destination), "inputs": len(inputs),
                      "raw_files_stat_only": len(raw_stats), "source_commit": head}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
