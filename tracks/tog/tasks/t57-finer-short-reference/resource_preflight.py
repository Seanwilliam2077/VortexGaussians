"""One OS-only preparation probe; no scientific imports or solver execution."""
import ctypes
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('memory_observer',ROOT/'memory.py')
memory=importlib.util.module_from_spec(spec);spec.loader.exec_module(memory)
assert os.name=='nt' and ctypes.sizeof(memory.Counters)==80
handle=memory.open_process(os.getpid())
try:current=memory.process_memory(handle)
finally:memory.kernel.CloseHandle(handle)
host=memory.host_memory()
assert 0<current['working_set_bytes']<=current['peak_working_set_bytes']<2*1024**3
assert 3*1024**3<=host['available_physical_bytes']<=host['total_physical_bytes']
raw=Path(sys.executable).read_bytes()
record=dict(schema='t57-os-preflight-v1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    status='passed_OS_only_preparation',pid=os.getpid(),python=platform.python_version(),
    executable=dict(path=sys.executable,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),
    host=host,probe_process=current,counters_structure_bytes=ctypes.sizeof(memory.Counters),
    minimum_available_host_bytes=3*1024**3,peak_working_set_stop_bytes=2*1024**3,
    new_scientific_children=0,numerical_imports=0,solver_executions=0)
with (ROOT/'resource-preflight.json').open('x',encoding='utf8',newline='\n') as stream:
    json.dump(record,stream,indent=2);stream.write('\n')
print(json.dumps(record,indent=2))
