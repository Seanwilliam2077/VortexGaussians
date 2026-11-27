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


def host_facts(a, b):
    flags = int(any(not np.array_equal(a[:, k], b[:, k]) for k in (6, 7, 8, 12))) << 15
    for axis in range(3):
        x, y = a[:, axis], b[:, axis]
        p, q = a[:, 9 + axis], b[:, 9 + axis]
        facts = int((x < 0).any() or (y < 0).any())
        facts |= int(x.any() or y.any()) << 1
        facts |= int(p.any() or q.any()) << 2
        facts |= int(not np.array_equal(x > 0, y > 0)) << 3
        facts |= int(any(not np.array_equal(a[:, k], b[:, k]) for k in (axis, axis + 3, axis + 9))) << 4
        flags |= facts << (5 * axis)
    return flags


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
        def audit_result(name, a, b, raw, decision):
            cells = len(a)
            if raw:
                av, bv = a.ravel(), b.ravel()
                partial = [int(not np.array_equal(av[i:i+64], bv[i:i+64])) for i in range(0, len(av), 64)]
            else:
                partial = [host_facts(a[i:i+64], b[i:i+64]) for i in range(0, cells, 64)]
            observed = np.frombuffer(gpu.read_buffer(guard.partials, size=4*len(partial)), "<u4")
            flags, = struct.unpack("<I", gpu.read_buffer(guard.result))
            expected_flags = int(np.bitwise_or.reduce(partial))
            if not np.array_equal(partial, observed) or flags != expected_flags:
                row["failed_reduction"] = dict(name=name, raw_only=raw, decision=decision, result=flags,
                                               expected_result=expected_flags, partials=observed.tolist(),
                                               expected_partials=partial)
                raise ValueError(f"{name}: direct native reduction differs from the input words")
        row["controls"] = check_cases(gpu, guard, verify_upload=True, audit_result=audit_result)
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
