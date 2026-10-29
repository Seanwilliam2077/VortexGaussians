"""One acquisition invocation; no installation, alternate runtime or retry."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = HERE / 'run-01'
NODE = 'C:/Program Files/nodejs/node.exe'
if OUT.exists():
    raise SystemExit('run-01 exists; no retry')
freeze = HERE / 'freeze.json'
for item in json.loads(freeze.read_bytes())['artifacts']:
    file = (ROOT / item['path']).resolve()
    if not file.is_relative_to(ROOT):
        raise SystemExit('Source path escapes repository')
    data = file.read_bytes()
    if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
        raise SystemExit('Frozen source changed: ' + item['path'])
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
OUT.mkdir()
(OUT/'attempt.json').write_text(json.dumps(dict(invocation=1,started_utc=started,
    freeze_sha256=hashlib.sha256(freeze.read_bytes()).hexdigest(),retry_allowed=False))+'\n',encoding='utf-8',newline='\n')
tic = time.perf_counter()
child = None
stdout, stderr = b'', b''
timed_out = False
cleanup = None
errors = []
try:
    child = subprocess.Popen([NODE, str(HERE/'capture.mjs'), '--execute'], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    stdout, stderr = child.communicate(timeout=120)
except subprocess.TimeoutExpired as exc:
    timed_out = True
    stdout, stderr = exc.stdout or b'', exc.stderr or b''
    errors.append(repr(exc))
except Exception as exc:
    errors.append(repr(exc))
finally:
    if child is not None and child.poll() is None:
        try:
            # Only terminate the process tree created by THIS supervisor.
            cleanup = subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=10).returncode
        except Exception as exc:
            errors.append('tree cleanup: '+repr(exc))
        try:
            if child.poll() is None:
                child.kill()
            stdout, stderr = child.communicate(timeout=10)
        except Exception as exc:
            errors.append('final child cleanup: '+repr(exc))
elapsed = time.perf_counter()-tic
(OUT/'stdout.txt').write_bytes(stdout)
(OUT/'stderr.txt').write_bytes(stderr)
receipt = dict(schema='t31-execution-v1',invocation=1,started_utc=started,
    finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    returncode=None if child is None else child.returncode,timed_out=timed_out,process_tree_cleanup_returncode=cleanup,
    errors=errors,child_still_running=child is not None and child.poll() is None,
    acquisition_deadline_seconds=90,external_wait_cap_seconds=120,supervisor_elapsed_seconds=elapsed,
    freeze_sha256=hashlib.sha256(freeze.read_bytes()).hexdigest(),retries=0,
    stdout_bytes=len(stdout),stdout_sha256=hashlib.sha256(stdout).hexdigest(),
    stderr_bytes=len(stderr),stderr_sha256=hashlib.sha256(stderr).hexdigest(),
    not_a_render_benchmark=True)
(OUT/'execution.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(receipt))
print(stdout.decode('utf-8',errors='replace'))
raise SystemExit(0 if child is not None and child.returncode == 0 and not timed_out and not errors else 2)
