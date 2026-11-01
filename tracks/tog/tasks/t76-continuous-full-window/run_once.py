"""One supervised T76 scientific child; no numerical imports in this supervisor."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
LIMIT = 180.0
MEMORY_LIMIT = 512 * 1024 * 1024
PRIOR = 2018.39971949975


def save(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


def identity(path):
    if path.suffix.lower() in (".npz", ".npy"):
        raise ValueError("supervisor never opens reference arrays")
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
    return {"bytes": size, "sha256": digest.hexdigest()}


def main():
    supervisor_start = time.perf_counter()
    manifest_path = HERE / "input-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    if manifest["schema"] != "t76-continuous-full-window-freeze-v1":
        raise ValueError("wrong manifest")
    if manifest["child_timeout_seconds"] != LIMIT or manifest["prior_scientific_child_seconds"] != PRIOR:
        raise ValueError("wrong fixed resource/cost contract")
    save(HERE / "invocation.json", {"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "child_timeout_seconds": LIMIT, "observed_working_set_cap_bytes": MEMORY_LIMIT,
        "retry_allowed": False, "manifest": identity(manifest_path)})
    inputs = {}
    for item in manifest["inputs"]:
        path = (REPO / item["path"]).resolve()
        if not path.is_relative_to(REPO):
            raise ValueError("noncontained input")
        expected = {key: item[key] for key in ("bytes", "sha256")}
        if identity(path) != expected:
            raise ValueError("frozen source changed: " + item["path"])
        inputs[path] = expected
    executable = Path(sys.executable).resolve()
    if executable != Path(manifest["executable"]["path"]).resolve():
        raise ValueError("wrong executable")
    inputs[executable] = {key: manifest["executable"][key] for key in ("bytes", "sha256")}
    if identity(executable) != inputs[executable]:
        raise ValueError("executable identity changed")
    inputs[manifest_path.resolve()] = identity(manifest_path)
    memory_path = HERE.parent / "t57-finer-short-reference" / "memory.py"
    spec = importlib.util.spec_from_file_location("t76_memory", memory_path)
    memory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(memory)
    host = memory.host_memory()
    if host["available_physical_bytes"] < 1073741824:
        save(HERE / "execution.json", {"status": "preflight_insufficient_memory", "host": host,
            "complete_child_seconds": 0, "tracked_scientific_child_seconds": PRIOR})
        return 1
    command = [str(executable), "-I", "-B", "-X", "utf8", str(HERE / "measure.py"),
               "--manifest", str(manifest_path)]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    save(HERE / "source_manifest.json", {"git_head_before_invocation": head,
        "source_freeze_commit": manifest["parent_commit"], "input_manifest": identity(manifest_path),
        "frozen_nonarray_files_including_executable_manifest": len(inputs),
        "command": command, "host_memory_before": host})
    env = dict(os.environ)
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[key] = "1"
    child = None
    handle = None
    termination = None
    samples = 0
    observation_errors = []
    peaks = {key: 0 for key in ("peak_working_set_bytes", "working_set_bytes",
        "private_usage_bytes", "peak_pagefile_usage_bytes")}
    child_seconds = None
    returncode = None
    try:
        with (HERE / "stdout.txt").open("x", encoding="utf-8") as out, \
             (HERE / "stderr.txt").open("x", encoding="utf-8") as err:
            child_start = time.perf_counter()
            child = subprocess.Popen(command, cwd=REPO, env=env, stdout=out, stderr=err)
            handle = memory.open_process(child.pid)
            while True:
                try:
                    current = memory.process_memory(handle)
                    samples += 1
                    for key, value in current.items():
                        peaks[key] = max(peaks[key], value)
                except OSError as error:
                    observation_errors.append(str(error))
                    if child.poll() is None:
                        termination = "memory_observation_failed"
                if peaks["peak_working_set_bytes"] > MEMORY_LIMIT:
                    termination = "observed_memory_limit_exceeded"
                if time.perf_counter() - child_start > LIMIT:
                    termination = "wall_limit_exceeded"
                if termination:
                    if child.poll() is None:
                        child.kill()
                    break
                if child.poll() is not None:
                    break
                time.sleep(.25)
            returncode = child.wait()
            child_seconds = time.perf_counter() - child_start
    except Exception as error:
        termination = "supervisor_exception: " + repr(error)
        if child is not None:
            if child.poll() is None:
                child.kill()
            returncode = child.wait()
            child_seconds = time.perf_counter() - child_start
    finally:
        if handle:
            memory.kernel.CloseHandle(handle)
    unchanged = all(identity(path) == previous for path, previous in inputs.items())
    outputs = {}
    for name in ("result.json", "predictions.json"):
        path = HERE / "local" / name
        if path.exists():
            data = path.read_bytes()
            with (HERE / name).open("xb") as stream:
                stream.write(data)
            outputs[name] = identity(path)
    journal = HERE / "local" / "journal.jsonl"
    journal_record = dict(path="local/journal.jsonl", **identity(journal)) if journal.exists() else None
    result = json.loads((HERE / "result.json").read_bytes()) if (HERE / "result.json").exists() else {}
    checks = result.get("checks", [])
    check_names = [item.get("name") for item in checks]
    qualified = (result.get("numerical_qualified") is True and len(check_names) == 9
        and set(check_names) == set(manifest["expected_check_names"])
        and all(item.get("passed") is True for item in checks))
    complete = (qualified and returncode == 0 and termination is None and unchanged
        and samples > 0 and child_seconds is not None and child_seconds <= LIMIT)
    elapsed = time.perf_counter() - supervisor_start
    receipt = {"status": "completed_" + result.get("verdict", "unknown") if complete else "failed_qualification_no_retry",
        "complete_numerical_measurement": complete, "worker_verdict": result.get("verdict"),
        "full_task_validated": bool(complete and result.get("full_task_validated") is True),
        "termination": termination, "returncode": returncode, "complete_child_seconds": child_seconds,
        "supervisor_elapsed_until_receipt_seconds": elapsed,
        "nonoverlapping_supervisor_overhead_until_receipt_seconds": elapsed - (child_seconds or 0),
        "final_receipt_write_not_timed": True, "memory_observations": samples,
        "peak_observations": peaks, "memory_observation_errors": observation_errors,
        "all_frozen_input_identities_preserved": unchanged,
        "prior_tracked_scientific_child_seconds": PRIOR,
        "tracked_scientific_child_seconds": PRIOR + (child_seconds or 0),
        "cost_scope": "Selected complete scientific-child intervals, not project/research cost; no speed claim.",
        "public_scalar_outputs": outputs, "ignored_local_journal": journal_record}
    save(HERE / "execution.json", receipt)
    print(json.dumps(receipt, allow_nan=False))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
