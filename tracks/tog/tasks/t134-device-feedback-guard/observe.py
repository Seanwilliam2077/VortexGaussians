"""Measure the resident cloth feedback predicate. The public entry point bounds one worker."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter, perf_counter_ns, sleep
import traceback

import numpy as np

from device_guard import FeedbackGuard, SHADER
from inputs import HERE, controls, digest, expected, workloads

sys.path.insert(0, str(HERE.parent / "t125-nvidia-dx12-admission"))
from admit import PIN, save, select

METHODS = ("device_raw", "device_full", "batched_cpu_raw", "batched_cpu_full", "two_reads_cpu_full")
BLOCKS = 15
LIMIT_S = 180
libc = ctypes.CDLL("ucrtbase" if os.name == "nt" else None)
memcmp = libc.memcmp
memcmp.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t)
memcmp.restype = ctypes.c_int


def cpu_classify(a, b, raw_only=False):
    # All callers pass contiguous resident-grid readbacks of the same layout.
    if memcmp(a.ctypes.data, b.ctypes.data, a.nbytes) == 0:
        return "raw"
    if raw_only or not np.array_equal(a[:, 6:9], b[:, 6:9]) or not np.array_equal(a[:, 12], b[:, 12]):
        return "split"
    for axis in range(3):
        area, other_area = a[:, axis], b[:, axis]
        if (area < 0).any() or (other_area < 0).any():
            return "split"
        if not area.any() and not other_area.any():
            continue
        impulse, other_impulse = a[:, axis + 9], b[:, axis + 9]
        if not impulse.any() and not other_impulse.any() and np.array_equal(area > 0, other_area > 0):
            continue
        if not (np.array_equal(area, other_area) and np.array_equal(impulse, other_impulse)
                and np.array_equal(a[:, axis + 3], b[:, axis + 3])):
            return "split"
    return "axis"


def resident(gpu, array, label):
    buffer = gpu.buffer(array.nbytes, label)
    gpu.write_buffer(buffer, array)
    return buffer


def measure_call(method):
    start = perf_counter_ns()
    verdict = method()
    return verdict, perf_counter_ns() - start


def check_cases(gpu, guard):
    records = []
    for name, a, b in controls():
        gold = expected(a, b)
        first, second = resident(gpu, a, name), resident(gpu, b, name)
        try:
            full = guard.compare(first, second)
            raw = guard.compare(first, second, raw_only=True)
            if full != gold or cpu_classify(a, b) != gold or (raw == "raw") != (gold == "raw"):
                raise ValueError(f"{name}: observed {full}, {raw}, expected {gold}")
            records.append(dict(case=name, cells=len(a), first=digest(a), second=digest(b),
                                expected=gold, device_full=full, device_raw=raw))
        finally:
            first.destroy()
            second.destroy()
    return records


def benchmark(gpu, guard, name, a, b):
    import wgpu
    gold = expected(a, b)
    start = perf_counter()
    first, second = resident(gpu, a, name), resident(gpu, b, name)
    cpu_buffer = gpu.device.create_buffer(size=2 * a.nbytes,
                                           usage=wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.MAP_READ)
    gpu.sync()
    setup_s = perf_counter() - start

    def batched(raw_only):
        encoder = gpu.device.create_command_encoder()
        encoder.copy_buffer_to_buffer(first.buf, 0, cpu_buffer, 0, a.nbytes)
        encoder.copy_buffer_to_buffer(second.buf, 0, cpu_buffer, a.nbytes, b.nbytes)
        gpu.queue.submit([encoder.finish()])
        cpu_buffer.map_sync(wgpu.MapMode.READ)
        try:
            both = np.frombuffer(cpu_buffer.read_mapped(copy=False), "<i4").reshape(2, -1, 13)
            return cpu_classify(both[0], both[1], raw_only)
        finally:
            cpu_buffer.unmap()

    def ordinary():
        one = np.frombuffer(gpu.read_buffer(first), "<i4").reshape(-1, 13)
        two = np.frombuffer(gpu.read_buffer(second), "<i4").reshape(-1, 13)
        return cpu_classify(one, two)

    implementations = (lambda: guard.compare(first, second, raw_only=True),
                       lambda: guard.compare(first, second), lambda: batched(True), lambda: batched(False), ordinary)
    samples = {key: [] for key in METHODS}
    observed = {key: {} for key in METHODS}
    cold = {}
    try:
        for block in range(-1, BLOCKS):
            for j in range(len(METHODS)):
                k = (j + max(0, block)) % len(METHODS)
                key = METHODS[k]
                verdict, ns = measure_call(implementations[k])
                want = "split" if key.endswith("_raw") and gold != "raw" else gold
                if verdict != want:
                    raise ValueError(f"{name}/{key}: observed {verdict}, expected {want}")
                observed[key][verdict] = observed[key].get(verdict, 0) + 1
                if block < 0:
                    cold[key] = ns
                else:
                    samples[key].append(ns)
    finally:
        first.destroy()
        second.destroy()
        cpu_buffer.destroy()
    return dict(name=name, cells=len(a), source_sha256=[digest(a), digest(b)], expected=gold,
                setup_s=setup_s, read_bytes_per_call={"device": 4, "cpu": 2 * a.nbytes},
                first_method_call_ns=cold, samples_ns=samples, observed_decisions=observed)


def worker(source, out):
    import hashlib
    start = perf_counter()
    shader_text = SHADER.read_text(encoding="utf-8")
    row = dict(status="running", revision=PIN, shader_sha256=hashlib.sha256(shader_text.encode()).hexdigest())
    def phase(name):
        row["phase"] = name
        row["elapsed_s"] = perf_counter() - start
        save(out / "measurements.json", row)
    try:
        phase("admit")
        row["adapter"] = select(source)
        from blackbody.engine.gpu import GPU
        gpu = GPU(adapter_name=row["adapter"]["device"], backend=row["adapter"]["backend_type"])
        if gpu.name != row["adapter"]["device"] or gpu.backend != row["adapter"]["backend_type"]:
            raise ValueError("Device changed after admission")
        row["admission_s"] = perf_counter() - start
        phase("build kernels")
        t = perf_counter()
        guard = FeedbackGuard(gpu)
        row["build_s"] = perf_counter() - t
        row["kernels"] = {key: {"key": k.key, "compile_s": k.seconds}
                          for key, k in [("axis", guard.axis), ("raw", guard.raw)]}
        phase("correctness")
        row["controls"] = check_cases(gpu, guard)
        row["workloads"] = []
        for name, a, b in workloads():
            phase(name)
            row["workloads"].append(benchmark(gpu, guard, name, a, b))
        row["status"] = "complete"
        phase("done")
        return 0
    except Exception as error:
        row["status"] = "error"
        row["error"] = f"{type(error).__name__}: {error}".replace(str(source), "<source>").replace(str(Path.home()), "<home>")
        phase(row["phase"])
        traceback.print_exc()
        return 2


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--worker", action="store_true")
    args = p.parse_args()
    if args.worker:
        return worker(args.source.resolve(), args.out.resolve())
    args.out.mkdir(parents=True, exist_ok=False)
    start = perf_counter()
    argv = [sys.executable, "-B", __file__, "--source", str(args.source), "--out", str(args.out), "--worker"]
    proc = subprocess.Popen(argv)
    try:
        while proc.poll() is None and perf_counter() - start < LIMIT_S:
            sleep(.20)
        timed_out = proc.poll() is None
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait()
    save(args.out / "exit.json", dict(limit_s=LIMIT_S, elapsed_s=perf_counter()-start,
                                     timeout=timed_out, returncode=proc.returncode))
    return 2 if timed_out else proc.returncode


if __name__ == "__main__":
    sys.exit(main())
