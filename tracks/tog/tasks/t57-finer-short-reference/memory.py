"""Windows byte-valued process/host memory observation, no numerical imports."""
import ctypes
from ctypes import wintypes

class Counters(ctypes.Structure):
    _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[
        (name,ctypes.c_size_t) for name in ('PeakWorkingSetSize','WorkingSetSize',
        'QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage',
        'QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]

class MemoryStatus(ctypes.Structure):
    _fields_=[('dwLength',wintypes.DWORD),('dwMemoryLoad',wintypes.DWORD)]+[
        (name,ctypes.c_ulonglong) for name in ('ullTotalPhys','ullAvailPhys',
        'ullTotalPageFile','ullAvailPageFile','ullTotalVirtual','ullAvailVirtual','ullAvailExtendedVirtual')]

kernel=ctypes.WinDLL('kernel32',use_last_error=True)
psapi=ctypes.WinDLL('psapi',use_last_error=True)
kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
kernel.OpenProcess.restype=wintypes.HANDLE
kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.CloseHandle.restype=wintypes.BOOL
kernel.GlobalMemoryStatusEx.argtypes=[ctypes.POINTER(MemoryStatus)]
kernel.GlobalMemoryStatusEx.restype=wintypes.BOOL
psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
psapi.GetProcessMemoryInfo.restype=wintypes.BOOL

def open_process(pid):
    handle=kernel.OpenProcess(0x0400|0x0010,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    return handle

def process_memory(handle):
    value=Counters();value.cb=ctypes.sizeof(value)
    if not psapi.GetProcessMemoryInfo(handle,ctypes.byref(value),value.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return dict(peak_working_set_bytes=value.PeakWorkingSetSize,working_set_bytes=value.WorkingSetSize,
        private_usage_bytes=value.PrivateUsage,peak_pagefile_usage_bytes=value.PeakPagefileUsage)

def host_memory():
    value=MemoryStatus();value.dwLength=ctypes.sizeof(value)
    if not kernel.GlobalMemoryStatusEx(ctypes.byref(value)):
        raise ctypes.WinError(ctypes.get_last_error())
    return dict(total_physical_bytes=value.ullTotalPhys,available_physical_bytes=value.ullAvailPhys)
