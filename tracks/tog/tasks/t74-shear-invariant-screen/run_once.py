"""One supervised T74 confirmation; stdlib only in this parent process."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
WALL_LIMIT = 30.0
MEMORY_LIMIT = 256 * 1024 * 1024
PRIOR_SCIENTIFIC_CHILD_SECONDS = 2017.6732525997795


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    supervisor_start = time.perf_counter()
    # Exclusive creation makes a second invocation fail before spawning a child.
    marker = BASE / "invocation.json"
    with marker.open("x", encoding="utf-8") as stream:
        json.dump({"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   "wall_limit_seconds": WALL_LIMIT,
                   "observed_working_set_cap_bytes": MEMORY_LIMIT,
                   "retry_allowed": False}, stream, indent=2)
        stream.write("\n")
    memory_path = BASE.parent / "t57-finer-short-reference" / "memory.py"
    spec = importlib.util.spec_from_file_location("t74_memory", memory_path)
    memory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(memory)
    inputs = [BASE / name for name in ("BRIEF.md", "PROTOCOL.md", "DERIVATION.md",
              "verify.py", "run_once.py", "SOURCE_READING.md")] + [memory_path]
    frozen = {str(path.relative_to(ROOT)).replace("\\", "/"):
              {"bytes": path.stat().st_size,
               "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in inputs}
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout.strip()
    command = [sys.executable, "-I", "-B", "-X", "utf8", str(BASE / "verify.py"),
               "--output", str(BASE / "result.json")]
    save(BASE / "source_manifest.json", {"git_head_before_invocation": head,
         "inputs": frozen, "command": command, "python": sys.version,
         "host_memory_before": memory.host_memory(), "protocol": "PROTOCOL.md"})
    env = dict(os.environ)
    # One thread also avoids unrelated host-level BLAS scheduling variability.
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        env[key] = "1"
    process = None
    handle = None
    termination = None
    observation_errors = []
    samples = 0
    peaks = {key: 0 for key in ("peak_working_set_bytes", "working_set_bytes",
                               "private_usage_bytes", "peak_pagefile_usage_bytes")}
    child_start = None
    child_seconds = None
    returncode = None
    try:
        with (BASE / "stdout.txt").open("x", encoding="utf-8") as stdout, \
             (BASE / "stderr.txt").open("x", encoding="utf-8") as stderr:
            child_start = time.perf_counter()
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
            handle = memory.open_process(process.pid)
            while True:
                try:
                    current = memory.process_memory(handle)
                    samples += 1
                    for key, value in current.items():
                        peaks[key] = max(peaks[key], value)
                except OSError as error:
                    observation_errors.append(str(error))
                    # An observation failure while still active invalidates supervision.
                    if process.poll() is None:
                        termination = "memory_observation_failed"
                if peaks["peak_working_set_bytes"] > MEMORY_LIMIT:
                    termination = "observed_memory_cap_exceeded"
                if time.perf_counter() - child_start > WALL_LIMIT:
                    termination = "wall_limit_exceeded"
                if termination is not None:
                    if process.poll() is None:
                        process.kill()
                    break
                if process.poll() is not None:
                    break
                time.sleep(0.01)
            returncode = process.wait()
            child_seconds = time.perf_counter() - child_start
    except Exception as error:
        termination = "supervisor_exception: " + repr(error)
        if process is not None:
            if process.poll() is None:
                process.kill()
            returncode = process.wait()
            child_seconds = time.perf_counter() - child_start
    finally:
        if handle:
            memory.kernel.CloseHandle(handle)
    # Check every input after process exit; do not rewrite frozen sources.
    unchanged = all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == record["sha256"]
                    for name, record in frozen.items())
    result_path = BASE / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else None
    numerical_ok = result is not None and result.get("all_checks_pass") is True
    complete = (returncode == 0 and termination is None and unchanged and numerical_ok
                and samples > 0 and child_seconds is not None and child_seconds <= WALL_LIMIT)
    elapsed = time.perf_counter() - supervisor_start
    receipt = {"status": "completed_confirmation" if complete else "failed_confirmation",
        "termination": termination, "child_returncode": returncode,
        "complete_child_seconds": child_seconds,
        "supervisor_elapsed_until_receipt_seconds": elapsed,
        "nonoverlapping_supervisor_overhead_until_receipt_seconds":
            elapsed - (child_seconds or 0),
        "receipt_final_write_not_timed": True,
        "memory_observations": samples, "peak_observations": peaks,
        "memory_observation_errors": observation_errors,
        "source_hashes_unchanged": unchanged, "numerical_checks_pass": numerical_ok,
        "prior_tracked_scientific_child_seconds": PRIOR_SCIENTIFIC_CHILD_SECONDS,
        "tracked_scientific_child_seconds": PRIOR_SCIENTIFIC_CHILD_SECONDS + (child_seconds or 0),
        "cost_scope": "Selected scientific-child intervals only; not project or human/agent research cost.",
        "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest() if result_path.exists() else None}
    save(BASE / "execution.json", receipt)
    print(json.dumps(receipt, ensure_ascii=False, allow_nan=False))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
