"""Verify the compiler selection, stage trace, measured physical state and any delivered pixels."""
import argparse
import importlib.util
import json
from pathlib import Path

from render import COLD, DLLS, LIMIT, TASKS, require


def read_record(path):
    return json.loads(path.read_bytes())


def verifier(path):
    spec = importlib.util.spec_from_file_location(path.parent.name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(folder):
    stage = verifier(TASKS / "t132-native-composite-warmup/verify.py").verify(folder, limit=LIMIT)
    compiler = read_record(folder / "COMPILER.json")
    require(compiler["requested"] == "Dxc" and compiler["dll_sha256"] == DLLS,
            "Wrong compiler request or file identity")
    require(not compiler["compiler_loaded_before_admission"], "Unexpected prior module")
    phase_rows = [json.loads(line) for line in (folder / "PHASES.ndjson").read_bytes().splitlines()]
    if any(r["phase"] == "cold stage on admitted device" for r in phase_rows):
        require(compiler["expected_compiler_loaded"], "Requested compiler did not load")
    if stage["worker_status"] == "complete":
        require(not compiler["compiler_warnings"], "Unexpected compiler diagnostics on a successful image")
        require(stage["terminal"] == "returned", "Image was not delivered in time")
        measured = read_record(COLD / "evidence/reference.json")["successor"]
        require(read_record(folder / "RESTORED.json") == measured, "Recorded physical fields differ")
        arrays = verifier(COLD / "verify.py").check_arrays(folder / "restored-frame2.npz", measured)
        return {"stage": stage, "restored_arrays": arrays,
                "pixels": read_record(folder / "RESULT.json")["native_pixels"]}
    return {"stage": stage, "compiler": compiler}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    print(json.dumps(verify(parser.parse_args().folder), indent=2))
