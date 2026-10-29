"""Read-only T27 environment evidence. No model, tensor, compiler or install."""
from pathlib import Path
import ctypes
import datetime
import hashlib
import importlib.metadata as metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "local"
OUT.mkdir(exist_ok=True)
RECEIPT = OUT / "environment-receipt.json"
if RECEIPT.exists():
    raise SystemExit("Refusing repeated T27 probe.")
START = time.monotonic()
LIMIT = 150.0
records = []
flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

def run(label, argv, timeout=10):
    remaining = LIMIT - (time.monotonic() - START)
    if remaining <= 0:
        return {"label": label, "status": "total_budget_exhausted", "argv": argv}
    t = time.monotonic()
    try:
        r = subprocess.run(argv, capture_output=True, timeout=min(timeout, remaining),
                           creationflags=flags)
        def dec(b):
            if b.count(b"\x00") > len(b) // 5:
                return b.decode("utf-16-le", errors="replace")
            return b.decode("utf-8", errors="replace")
        return {"label": label, "argv": argv, "returncode": r.returncode,
                "stdout": dec(r.stdout), "stderr": dec(r.stderr),
                "elapsed_seconds": time.monotonic()-t, "status": "completed",
                "timeout_seconds": min(timeout, remaining)}
    except subprocess.TimeoutExpired as e:
        return {"label": label, "argv": argv, "status": "timeout",
                "elapsed_seconds": time.monotonic()-t,
                "stdout": (e.stdout or b"").decode("utf-8", errors="replace"),
                "stderr": (e.stderr or b"").decode("utf-8", errors="replace")}
    except Exception as e:
        return {"label": label, "argv": argv, "status": "launch_error",
                "error_type": type(e).__name__, "message": str(e),
                "elapsed_seconds": time.monotonic()-t}

class MemoryStatus(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                ("total_phys", ctypes.c_ulonglong), ("avail_phys", ctypes.c_ulonglong),
                ("total_page", ctypes.c_ulonglong), ("avail_page", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong), ("avail_virtual", ctypes.c_ulonglong),
                ("avail_extended", ctypes.c_ulonglong)]

hardware = {"os": platform.system(), "release": platform.release(),
            "machine": platform.machine(), "cpu_logical_count": os.cpu_count(),
            "python_version": platform.python_version()}
if os.name == "nt":
    mem = MemoryStatus()
    mem.length = ctypes.sizeof(mem)
    ok = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
    hardware["memory_query_success"] = bool(ok)
    if ok:
        hardware["physical_memory_bytes"] = mem.total_phys
        hardware["available_physical_memory_bytes"] = mem.avail_phys
disk = shutil.disk_usage(ROOT)
hardware["workspace_volume_total_bytes"] = disk.total
hardware["workspace_volume_free_bytes"] = disk.free
packages = {}
for name in ["torch", "torchvision", "torchaudio", "numpy", "scipy", "plyfile",
             "Pillow", "opencv-python", "tqdm", "slangtorch", "ninja",
             "fused-ssim", "simple-knn", "diff-gaussian-rasterization",
             "slang-gaussian-rasterization", "wandb", "matplotlib", "lpips"]:
    try:
        packages[name] = metadata.version(name)
    except metadata.PackageNotFoundError:
        packages[name] = None

nvcc = shutil.which("nvcc")
cuda_root = os.environ.get("CUDA_PATH")
if not nvcc and cuda_root:
    candidate = Path(cuda_root) / "bin" / "nvcc.exe"
    if candidate.is_file():
        nvcc = str(candidate)
vswhere = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
tools = [
    ("nvidia-smi", shutil.which("nvidia-smi"), ["--query-gpu=name,memory.total,memory.free,driver_version", "--format=csv,noheader,nounits"]),
    ("nvcc", nvcc, ["--version"]),
    ("cmake", shutil.which("cmake"), ["--version"]),
    ("ninja", shutil.which("ninja"), ["--version"]),
    ("wsl", shutil.which("wsl"), ["--list", "--verbose"]),
    ("vswhere", str(vswhere) if vswhere.is_file() else None,
     ["-latest", "-products", "*", "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
      "-find", "VC\\Tools\\MSVC\\**\\bin\\Hostx64\\x64\\cl.exe"])
]
for label, exe, args in tools:
    records.append(run(label, [exe]+args) if exe else {"label": label, "status": "not_found_in_probed_locations"})
cl = shutil.which("cl")
v = next(x for x in records if x["label"] == "vswhere")
if not cl and v.get("returncode") == 0:
    for line in v.get("stdout", "").splitlines():
        q = Path(line.strip())
        if q.name.lower() == "cl.exe" and q.is_file():
            cl = str(q)
            break
records.append(run("cl", [cl]) if cl else {"label": "cl", "status": "not_found_in_path_or_vswhere_result"})
torch_query = """import json,torch
x={'torch_version':str(torch.__version__),'torch_compiled_cuda':torch.version.cuda,
   'cuda_available':torch.cuda.is_available(),'device_count':torch.cuda.device_count()}
if x['cuda_available']:
 x['devices']=[{'name':torch.cuda.get_device_name(i),'capability':list(torch.cuda.get_device_capability(i)),
                'total_memory_bytes':torch.cuda.get_device_properties(i).total_memory}
               for i in range(x['device_count'])]
print(json.dumps(x))
"""
records.append(run("installed_torch_query", [sys.executable, "-I", "-B", "-u", "-X", "utf8", "-c", torch_query], 45))
out = {"schema": "t27-local-environment-v1",
       "captured_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "probe_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       "hardware": hardware, "package_metadata": packages, "commands": records,
       "elapsed_seconds": time.monotonic()-START, "total_budget_seconds": LIMIT,
       "external_tool_attempts": sum(x["label"] != "installed_torch_query" and "argv" in x for x in records),
       "torch_query_attempts": 1, "no_tensor_model_compilation_or_install": True}
assert out["external_tool_attempts"] <= 8
RECEIPT.write_text(json.dumps(out, indent=2)+"\n", encoding="utf-8", newline="\n")
print(json.dumps(out, indent=2))
