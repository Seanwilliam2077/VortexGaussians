"""CPU-only test of the source-name argument passed to the installed IDxcCompiler3."""
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import uuid

PTR = C.c_void_p
HRESULT = C.c_int32
GUID = C.c_ubyte * 16
SDK = Path(os.environ["ProgramFiles(x86)"]) / "Windows Kits/10/bin/10.0.26100.0/x64"
SOURCE = b"RWStructuredBuffer<uint> outp : register(u0); [numthreads(1,1,1)] void main() { outp[0] = 42u; }"


class DxcBuffer(C.Structure):
    _fields_ = [("ptr", PTR), ("size", C.c_size_t), ("encoding", C.c_uint32)]


def guid(value):
    return GUID.from_buffer_copy(uuid.UUID(value).bytes_le)


def checked(status):
    if status < 0:
        raise OSError(f"DXC COM method HRESULT {status & 0xffffffff:08x}")


def method(obj, slot, result, *types):
    vtable = C.cast(obj, C.POINTER(C.POINTER(PTR))).contents
    return C.WINFUNCTYPE(result, PTR, *types)(vtable[slot])


def release(obj):
    if obj:
        method(obj, 2, C.c_ulong)(obj)


def compile_source(compiler, source_name):
    """The program lives in the DxcBuffer. Only the optional first argument varies."""
    args = ([source_name] if source_name is not None else []) + [
        "-E", "main", "-T", "cs_6_0", "-HV", "2018", "-no-warnings", "-Ges"]
    argv = (C.c_wchar_p * len(args))(*args)
    text = C.create_string_buffer(SOURCE)
    buf = DxcBuffer(C.cast(text, PTR), len(SOURCE), 65001)
    result_id = guid("58346CDA-DDE7-4497-9461-6F87AF5E0659")
    result, errors, artifact = PTR(), PTR(), PTR()
    try:
        call = method(compiler, 3, HRESULT, C.POINTER(DxcBuffer), C.POINTER(C.c_wchar_p),
                      C.c_uint32, PTR, C.POINTER(GUID), C.POINTER(PTR))
        checked(call(compiler, C.byref(buf), argv, len(argv), None, C.byref(result_id), C.byref(result)))
        status = HRESULT()
        checked(method(result, 3, HRESULT, C.POINTER(HRESULT))(result, C.byref(status)))
        checked(method(result, 5, HRESULT, C.POINTER(PTR))(result, C.byref(errors)))
        diagnostics = ""
        if errors:
            size = method(errors, 4, C.c_size_t)(errors)
            diagnostics = C.string_at(method(errors, 3, PTR)(errors), size).rstrip(b"\x00").decode()
        object_digest = None
        if status.value >= 0:
            checked(method(result, 4, HRESULT, C.POINTER(PTR))(result, C.byref(artifact)))
            bytecode = C.string_at(method(artifact, 3, PTR)(artifact), method(artifact, 4, C.c_size_t)(artifact))
            object_digest = hashlib.sha256(bytecode).hexdigest()
        return dict(module_label=source_name, status=status.value, diagnostic=diagnostics, object_sha256=object_digest)
    finally:
        for obj in (artifact, errors, result):
            release(obj)


if __name__ == "__main__":
    with os.add_dll_directory(str(SDK)):
        dll = C.WinDLL(str(SDK / "dxcompiler.dll"))
        cls = guid("73E22D93-E6CE-47F3-B5BF-F0664F39C1B0")
        iid = guid("228B4687-5A6A-4730-900C-9702B2203F54")
        compiler = PTR()
        dll.DxcCreateInstance.argtypes = [C.POINTER(GUID), C.POINTER(GUID), C.POINTER(PTR)]
        dll.DxcCreateInstance.restype = HRESULT
        checked(dll.DxcCreateInstance(C.byref(cls), C.byref(iid), C.byref(compiler)))
        try:
            rows = [compile_source(compiler, label) for label in ("light_emit.wgsl:main", "light_emit.wgsl_main", None)]
            print(json.dumps(rows, indent=2))
        finally:
            release(compiler)
