"""Regenerate input pairs and scores offline; report medians in microseconds."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median

from device_guard import SHADER
from inputs import HERE, controls, digest, expected, workloads
from observe import BLOCKS, LIMIT_S, METHODS, PIN


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(folder):
    terminal = json.loads((folder / "exit.json").read_bytes())
    require(terminal["limit_s"] == LIMIT_S and terminal["elapsed_s"] > 0, "Supervisor identity")
    row = json.loads((folder / "measurements.json").read_bytes())
    require(row["revision"] == PIN and row["shader_sha256"] ==
            hashlib.sha256(SHADER.read_text(encoding="utf-8").encode()).hexdigest(), "Source identity")
    if terminal["timeout"] or terminal["returncode"] != 0:
        require(terminal["timeout"] or row["status"] == "error", "Missing terminal explanation")
        return {"status": "incomplete", "phase": row["phase"], "error": row.get("error"), "exit": terminal}
    require(row["status"] == "complete" and row["phase"] == "done", "Incomplete worker")
    require(row["adapter"]["device"] == "NVIDIA GeForce RTX 5070 Laptop GPU" and
            row["adapter"]["backend_type"].lower() in ("dx12", "d3d12"), "Adapter")
    for item, (name, a, b) in zip(row["controls"], controls(), strict=True):
        full = expected(a, b)
        raw = "raw" if full == "raw" else "split"
        require(item == dict(case=name, cells=len(a), first=digest(a), second=digest(b), expected=full,
                             device_full=full, device_raw=raw), f"Incorrect device control {name}")
    summaries = []
    for result, (name, a, b) in zip(row["workloads"], workloads(), strict=True):
        require(result["name"] == name and result["cells"] == len(a), "Workload identity")
        require(result["source_sha256"] == [digest(a), digest(b)] and result["expected"] == expected(a, b),
                "Workload inputs and predicate")
        require(result["read_bytes_per_call"] == {"device": 4, "cpu": 2 * a.nbytes}, "Measured readback scope")
        samples = result["samples_ns"]
        require(set(samples) == set(METHODS) == set(result["first_method_call_ns"]), "Method inventory")
        for key, values in samples.items():
            verdict = "split" if key.endswith("_raw") and result["expected"] != "raw" else result["expected"]
            require(result["observed_decisions"][key] == {verdict: BLOCKS + 1}, "Disagreement in actual returns")
            require(len(values) == BLOCKS and all(type(v) is int and v > 0 for v in values) and
                    result["first_method_call_ns"][key] > 0, "Incomplete timing blocks")
        us = {key: median(samples[key]) / 1000 for key in METHODS}
        faster = us["device_full"] < min(us["batched_cpu_full"], us["two_reads_cpu_full"])
        summaries.append(dict(name=name, expected=result["expected"], median_us=us, device_full_faster=faster))
    return dict(status="complete", controls=len(row["controls"]), measured_calls=BLOCKS*len(METHODS)*len(summaries),
                results=summaries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, default=HERE / "evidence")
    print(json.dumps(verify(parser.parse_args().folder), indent=2))
