"""Instrument the first failure and measure the two-dispatch overwrite reduction."""
import hashlib
from itertools import islice
from pathlib import Path
import struct
import sys
from time import perf_counter
import traceback

import numpy as np

from guard import HERE, ResidentGuard
from observe import (FeedbackGuard, PIN, SHADER, benchmark, check_cases, controls, digest, expected, launch,
                     resident, save, select, workloads)

LIMIT = 120


def shader_hashes():
    return {name: hashlib.sha256((HERE / name).read_text(encoding="utf-8").encode()).hexdigest()
            for name in ("partial.wgsl", "finish.wgsl")}


def diagnose(gpu):
    original = FeedbackGuard(gpu)
    rows = []
    for name, a, b in islice(controls(), 2):
        first, second = resident(gpu, a, name), resident(gpu, b, name)
        try:
            observed = {}
            for raw in (False, True):
                decision = original.compare(first, second, raw_only=raw)
                flags, = struct.unpack("<I", gpu.read_buffer(original.result))
                observed["raw" if raw else "full"] = dict(returned=decision, direct_storage_word=flags)
            observed["input_sha256"] = [hashlib.sha256(gpu.read_buffer(buf)).hexdigest() for buf in (first, second)]
            observed["inputs_match"] = observed["input_sha256"] == [digest(a), digest(b)]
            rows.append(dict(name=name, expected=expected(a,b), **observed))
        finally:
            first.destroy()
            second.destroy()
    gpu.write_buffer(original.result, np.array([0xFFFFFFFF], dtype="<u4"))
    before, = struct.unpack("<I", gpu.read_buffer(original.result))
    with gpu.batch() as batch:
        batch.clear_buffer(original.result)
    after, = struct.unpack("<I", gpu.read_buffer(original.result))
    return dict(cases=rows, standalone_clear=[before, after])


def worker(source, out):
    start = perf_counter()
    row = dict(status="running", revision=PIN, shader_sha256=hashlib.sha256(SHADER.read_text().encode()).hexdigest(),
               recovery_shaders=shader_hashes())
    def phase(name):
        row["phase"] = name
        row["elapsed_s"] = perf_counter() - start
        save(out / "measurements.json", row)
    try:
        phase("admission")
        row["adapter"] = select(source)
        from blackbody.engine.gpu import GPU
        gpu = GPU(adapter_name=row["adapter"]["device"], backend=row["adapter"]["backend_type"])
        if gpu.name != row["adapter"]["device"] or gpu.backend != row["adapter"]["backend_type"]:
            raise ValueError("Unexpected device")
        row["admission_s"] = perf_counter() - start
        phase("original paired diagnostic")
        row["diagnostic"] = diagnose(gpu)
        phase("overwrite kernels")
        t = perf_counter()
        guard = ResidentGuard(gpu)
        row["build_s"] = perf_counter() - t
        row["kernels"] = {name: {"key": k.key, "compile_s": k.seconds} for name, k in
                          (("axis", guard.axis), ("raw", guard.raw), ("finish", guard.finish))}
        phase("correctness")
        row["controls"] = check_cases(gpu, guard, verify_upload=True)
        row["workloads"] = []
        for name, a, b in workloads():
            phase(name)
            row["workloads"].append(benchmark(gpu, guard, name, a, b))
        row["status"] = "complete"
        phase("done")
        return 0
    except Exception as ex:
        row["status"] = "error"
        row["error"] = f"{type(ex).__name__}: {ex}".replace(str(source), "<source>").replace(str(Path.home()), "<home>")
        phase(row["phase"])
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(launch(worker_fn=worker, limit_s=LIMIT, entry=__file__))
