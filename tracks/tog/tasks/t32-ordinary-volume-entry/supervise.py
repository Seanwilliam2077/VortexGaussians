"""Reserve and supervise exactly one CPU-only ordinary-entry invocation."""
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
if OUT.exists():raise SystemExit('Existing attempt; no retry')
frozen=(HERE/'freeze.json').read_bytes()
for item in json.loads(frozen)['artifacts']:
    p=(ROOT/item['path']).resolve()
    if not p.is_relative_to(ROOT):raise SystemExit('Frozen path escapes repository')
    b=p.read_bytes()
    if len(b)!=item['bytes'] or hashlib.sha256(b).hexdigest()!=item['sha256']:
        raise SystemExit('Frozen artifact changed: '+item['path'])
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
OUT.mkdir()
(OUT/'attempt.json').write_text(json.dumps({'started_utc':started,'invocation':1,'freeze_sha256':hashlib.sha256(frozen).hexdigest(),'retry_allowed':False})+'\n',encoding='utf-8',newline='\n')
child=None;stdout=b'';stderr=b'';errors=[];timed_out=False;tic=time.perf_counter()
try:
    child=subprocess.Popen([sys.executable,'-I','-B','-u','-X','utf8',str(HERE/'run.py')],cwd=ROOT,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    stdout,stderr=child.communicate(timeout=210)
except subprocess.TimeoutExpired as error:
    timed_out=True;stdout=error.stdout or b'';stderr=error.stderr or b'';errors.append(repr(error))
except Exception as error:
    errors.append(repr(error))
finally:
    if child is not None and child.poll() is None:
        # Worker code creates no child processes or GPU/browser tasks.
        try:
            child.kill();stdout,stderr=child.communicate(timeout=10)
        except Exception as error:errors.append('cleanup: '+repr(error))
elapsed=time.perf_counter()-tic
(OUT/'stdout.txt').write_bytes(stdout);(OUT/'stderr.txt').write_bytes(stderr)
receipt={'schema':'t32-execution-v1','invocation':1,'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'returncode':None if child is None else child.returncode,'timed_out':timed_out,'errors':errors,
 'child_still_running':child is not None and child.poll() is None,'computation_cap_seconds':180,'external_wait_seconds':210,
 'supervisor_seconds':elapsed,'freeze_sha256':hashlib.sha256(frozen).hexdigest(),'retries':0,
 'stdout_bytes':len(stdout),'stdout_sha256':hashlib.sha256(stdout).hexdigest(),
 'stderr_bytes':len(stderr),'stderr_sha256':hashlib.sha256(stderr).hexdigest(),'not_a_delivery_benchmark':True}
(OUT/'execution.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(receipt));print(stdout.decode('utf-8',errors='replace'));print(stderr.decode('utf-8',errors='replace'))
raise SystemExit(0 if child is not None and child.returncode==0 and not timed_out and not errors else 2)
