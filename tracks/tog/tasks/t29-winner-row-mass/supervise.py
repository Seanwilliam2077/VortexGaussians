"""One external 60-second supervisor; runs only the frozen T29 worker."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
out=HERE/"run-01"
assert not out.exists(), "No second T29 invocation"
freeze=json.loads((HERE/"freeze.json").read_text())
for item in freeze["artifacts"]:
    b=(ROOT/item["path"]).read_bytes()
    assert len(b)==item["bytes"] and hashlib.sha256(b).hexdigest()==item["sha256"]
start_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
started=time.perf_counter()
cmd=[sys.executable,"-I","-B","-u","-X","utf8",str(HERE/"reduce.py"),"run","--out",str(out)]
timed_out=False
try:
    p=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=60,
                     creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    stdout,stderr,returncode=p.stdout,p.stderr,p.returncode
except subprocess.TimeoutExpired as exc:
    timed_out=True;stdout=exc.stdout or b"";stderr=exc.stderr or b"";returncode=None
elapsed=time.perf_counter()-started
out.mkdir(exist_ok=True)
(out/"stdout.txt").write_bytes(stdout)
(out/"stderr.txt").write_bytes(stderr)
receipt={"schema":"t29-execution-v1","invocation":1,"started_utc":start_utc,
         "finished_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "returncode":returncode,"timed_out":timed_out,"external_wall_cap_seconds":60,
         "supervisor_elapsed_seconds":elapsed,"retry_allowed":False,
         "worker_relative":"tracks/tog/tasks/t29-winner-row-mass/reduce.py",
         "worker_source_sha256":hashlib.sha256((HERE/"reduce.py").read_bytes()).hexdigest(),
         "freeze_sha256":hashlib.sha256((HERE/"freeze.json").read_bytes()).hexdigest(),
         "stdout_bytes":len(stdout),"stdout_sha256":hashlib.sha256(stdout).hexdigest(),
         "stderr_bytes":len(stderr),"stderr_sha256":hashlib.sha256(stderr).hexdigest(),
         "new_integrand_or_CDF_evaluations":0,"not_a_delivery_benchmark":True}
(out/"execution.json").write_bytes((json.dumps(receipt,indent=2)+"\n").encode())
print(json.dumps(receipt))
print(stdout.decode("utf-8",errors="replace"))
if stderr: print(stderr.decode("utf-8",errors="replace"),file=sys.stderr)
raise SystemExit(0 if returncode==0 and not timed_out else 2)
