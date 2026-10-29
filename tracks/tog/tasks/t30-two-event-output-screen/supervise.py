"""Single bounded execution; never retry or replace an existing run."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=HERE/'run-01'
def require(condition,message):
    if not condition: raise ValueError(message)
require(not OUT.exists(),'run-01 already exists; no retry')
freeze=HERE/'freeze.json'
for item in json.loads(freeze.read_bytes())['artifacts']:
    path=(ROOT/item['path']).resolve()
    require(path.is_relative_to(ROOT),'Frozen path outside repository')
    data=path.read_bytes()
    require(len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256'],'Frozen artifact changed')
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
tic=time.perf_counter(); timed_out=False
try:
    run=subprocess.run([sys.executable,'-I','-B','-u','-X','utf8',str(HERE/'screen.py'),'--execute','--out',str(OUT)],cwd=ROOT,capture_output=True,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    stdout,stderr,code=run.stdout,run.stderr,run.returncode
except subprocess.TimeoutExpired as exc:
    stdout,stderr,code=exc.stdout or b'',exc.stderr or b'',None
    timed_out=True
elapsed=time.perf_counter()-tic
OUT.mkdir(exist_ok=True)
(OUT/'stdout.txt').write_bytes(stdout);(OUT/'stderr.txt').write_bytes(stderr)
receipt={'schema':'t30-execution-v1','invocation':1,'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'returncode':code,'timed_out':timed_out,'external_wall_cap_seconds':30,'supervisor_elapsed_seconds':elapsed,'retry_allowed':False,'worker_relative':(HERE/'screen.py').relative_to(ROOT).as_posix(),'worker_source_sha256':hashlib.sha256((HERE/'screen.py').read_bytes()).hexdigest(),'freeze_sha256':hashlib.sha256(freeze.read_bytes()).hexdigest(),'stdout_bytes':len(stdout),'stdout_sha256':hashlib.sha256(stdout).hexdigest(),'stderr_bytes':len(stderr),'stderr_sha256':hashlib.sha256(stderr).hexdigest(),'candidate_outputs_evaluated':0,'not_a_delivery_benchmark':True}
(OUT/'execution.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(receipt));print(stdout.decode('utf-8',errors='replace'))
raise SystemExit(0 if code==0 and not timed_out else 2)
