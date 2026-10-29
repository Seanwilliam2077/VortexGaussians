"""Consume the sole dynamic attempt, bound its process tree, preserve all output."""
import datetime,hashlib,json,subprocess,time
from pathlib import Path
r=Path.cwd();h=r/'tracks/tog/tasks/t42-firewoods-sequential-workflow'
out=r.parent.parent/'outputs/t42-firewoods-sequential-workflow/run-01'
out.mkdir(parents=True,exist_ok=False)
start=time.perf_counter();attempt={'schema':'t42-one-attempt-v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'internal_seconds':180,'external_seconds':240,'status':'attempt_consumed'}
(out/'attempt.json').write_text(json.dumps(attempt,indent=2)+'\n',encoding='utf-8')
result={'attempt':1,'output_directory':str(out),'status':'not_started'};p=None
with (out/'stdout.txt').open('wb') as stdout,(out/'stderr.txt').open('wb') as stderr:
 try:
  p=subprocess.Popen(['C:/Program Files/nodejs/node.exe',str(h/'capture.mjs'),str(out)],cwd=r,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
  result['worker_pid']=p.pid
  try:result['exit_code']=p.wait(timeout=max(0,210-(time.perf_counter()-start)));result['status']='worker_terminal'
  except subprocess.TimeoutExpired:
   result['status']='external_timeout';remaining=max(.001,240-(time.perf_counter()-start))
   result['termination']=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,text=True,timeout=min(20,remaining)).returncode
   try:result['exit_code']=p.wait(timeout=max(0,240-(time.perf_counter()-start)))
   except subprocess.TimeoutExpired:result['exit_code']=None
 except Exception as e:result['status']='supervisor_error';result['error']=repr(e)
result['worker_launched']=p is not None
result['worker_poll_exit_code']=None if p is None else p.poll()
result['worker_still_live']=p is not None and p.poll() is None
if result['worker_still_live']:result['status']='worker_still_live_requires_cleanup'
result['supervisor_seconds']=time.perf_counter()-start
hash_start=time.perf_counter()
result['files']=[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.iterdir()) if p.is_file()]
result['file_inventory_hash_seconds']=time.perf_counter()-hash_start
result['elapsed_before_receipt_write_seconds']=time.perf_counter()-start
result['timing_scope']='supervisor_seconds: attempt start through worker terminal/live check; inventory hashing separately measured; final supervisor.json write and stdout flush excluded'
(out/'supervisor.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(0 if result.get('exit_code')==0 and result['status']=='worker_terminal' else 1)
