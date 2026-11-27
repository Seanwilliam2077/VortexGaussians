"""Render the archived neutral successor with an explicitly selected SDK DXC compiler."""
import argparse
import ctypes
from functools import partial
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
TASKS = HERE.parent
COLD = TASKS / "t131-fresh-engine-continuation"
sys.path[:0] = [str(TASKS / "t132-native-composite-warmup"), str(COLD / "portable")]
import observe
from build import checkpoint_data
from run import describe, require
from admit import save, select

LIMIT = 300
DLLS = {
    "dxcompiler.dll": "78b5e21a91707b4a567ef281a519c52a45b709561202f54c5ad79c5a315847ed",
    "dxil.dll": "77e039c905030a641e53658a008b74e90635a5ea9b6b79eabd0f2003bdfca59a",
}


def module_path(filename):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
    kernel.GetModuleHandleW.restype = ctypes.c_void_p
    handle = kernel.GetModuleHandleW(filename)
    if not handle:
        return None
    kernel.GetModuleFileNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32]
    buf = ctypes.create_unicode_buffer(32768)
    count = kernel.GetModuleFileNameW(handle, buf, len(buf))
    if not 0 < count < len(buf):
        raise OSError(ctypes.get_last_error(), "Could not identify loaded module")
    return Path(buf.value)


class CompilerWarnings(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.messages = []

    def emit(self, record):
        msg = record.getMessage()
        if any(term in msg.lower() for term in ("dxc", "fxc", "dxcompiler", "fallback", "falling back")):
            self.messages.append(msg)


def check_compiler(gpu, out, sdk, receipt, warnings):
    loaded = module_path("dxcompiler.dll")
    correct = loaded is not None and loaded.samefile(sdk / "dxcompiler.dll")
    receipt.update(expected_compiler_loaded=correct, adapter=gpu.name, backend=gpu.backend,
                   compiler_warnings=warnings.messages)
    save(out / "COMPILER.json", receipt)
    require(correct and not warnings.messages, "Could not confirm the requested compiler on this device")


def restore_frame(engine, scene, cache, out):
    import numpy as np
    from blackbody.io.simcache import write_entry

    original = json.loads((COLD / "evidence/reference.json").read_bytes())
    target = original["successor"]
    require(target["frame"] == 2 and scene.sim_signature(True) == original["scene"], "Wrong fixture")
    entry, feedback = checkpoint_data(target, COLD / "evidence/reference-successor.npz")
    disk = engine.cache.disk
    require(disk is not None and not disk.frames(), "Expected a fresh cache")
    write_entry(disk.folder / "f+0000002.bbc", entry)
    disk.mark_checkpoint(2)
    require(disk.checkpoints() == [2], "Missing native checkpoint marker")
    with patch.object(engine, "step_frame", side_effect=RuntimeError("Unwanted physics update")):
        require(engine.simulate_to(scene, 2, cache=True) and engine.sim_frame == 2, "Disk restore failed")
    cloth = engine.cloth
    cloth.prepare_frame(engine.solver)
    state = target["feedback"]
    require(cloth._couple_ok(engine.solver) and list(cloth.couple_dims) == state["dims"], "Coupling layout")
    require(len(feedback) == int(np.prod(state["dims"])) * 13 * 4, "Coupling storage size")
    engine.gpu.write_buffer(cloth.G, np.frombuffer(feedback, np.uint32))
    cloth._couple_filled = state["ready"]
    restored = describe(engine, out / "restored-frame2.npz")
    save(out / "RESTORED.json", restored)
    require(restored == target, "Restored gas, cloth, embers or coupling differs from the measured frame")


def run_worker(source, out, cache):
    sdk = Path(os.environ["ProgramFiles(x86)"]) / "Windows Kits/10/bin/10.0.26100.0/x64"
    hashes = {name: hashlib.sha256((sdk / name).read_bytes()).hexdigest() for name in DLLS}
    receipt = {"requested": "Dxc", "max_shader_model": 6.5, "sdk": "10.0.26100.0/x64",
               "dll_sha256": hashes, "compiler_loaded_before_admission": module_path("dxcompiler.dll") is not None}
    save(out / "COMPILER.json", receipt)
    require(hashes == DLLS and not receipt["compiler_loaded_before_admission"], "Fresh SDK compiler required")
    warnings = CompilerWarnings()
    logging.getLogger("wgpu").addHandler(warnings)
    compiler = {"dx12_compiler": "Dxc", "dxc_path": str(sdk / "dxcompiler.dll"), "dxc_max_shader_model": 6.5}
    with os.add_dll_directory(str(sdk)):
        code = observe.worker(source, out, cache, select_device=partial(select, compiler_options=compiler),
                              check_device=partial(check_compiler, sdk=sdk, receipt=receipt, warnings=warnings),
                              restore_frame=restore_frame)
    receipt["compiler_warnings"] = warnings.messages
    save(out / "COMPILER.json", receipt)
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--worker-cache", type=Path)
    args = parser.parse_args()
    root, out = args.source.resolve(), args.out.resolve()
    if args.worker_cache is not None:
        sys.exit(run_worker(root, out, args.worker_cache))
    sys.exit(observe.supervise(root, out, limit=LIMIT, worker_script=__file__))
