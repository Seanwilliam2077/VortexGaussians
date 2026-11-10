"""One guarded T81 invocation; root must review frozen code before calling."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path.cwd()
HERE = ROOT / 'tracks/tog/tasks/t81-firewoods-capacity-causality'
OUT = HERE / 'local/run-01'
FREEZE = HERE / 'freeze.json'


def main():
    start = time.perf_counter()
    frozen_bytes = FREEZE.read_bytes()
    frozen = json.loads(frozen_bytes)
    # Consumed before any process or output allocation; never delete to retry.
    invocation = {'schema': 't81-one-shot-invocation-v1', 'status': 'attempt_consumed',
                  'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'freeze_sha256': hashlib.sha256(frozen_bytes).hexdigest(),
                  'worker_seconds': 600, 'external_seconds': 660, 'steps': 1440}
    with (HERE / 'invocation.json').open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(invocation, indent=2) + '\n')
    OUT.mkdir(parents=True, exist_ok=False)
    report = {'status': 'not_started', 'worker_launched': False}
    process = None
    with (OUT / 'stdout.txt').open('xb') as stdout, (OUT / 'stderr.txt').open('xb') as stderr:
        try:
            process = subprocess.Popen([frozen['runtime']['node_executable'], str(HERE / 'capture.mjs')],
                                       cwd=ROOT, stdout=stdout, stderr=stderr,
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            report.update(worker_launched=True, worker_pid=process.pid)
            while process.poll() is None:
                elapsed = time.perf_counter() - start
                size = sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
                # Reserve final 20 seconds for process-tree cleanup and receipts.
                if elapsed >= 640 or size > frozen['budget']['max_output_bytes']:
                    report['status'] = 'external_timeout' if elapsed >= 640 else 'output_budget_exceeded'
                    terminated = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                                capture_output=True, text=True, timeout=max(1, min(10, 655-elapsed)))
                    report['termination_exit_code'] = terminated.returncode
                    process.wait(timeout=max(0.1, 658-(time.perf_counter()-start)))
                    break
                time.sleep(0.5)
            report['exit_code'] = process.poll()
            if report['status'] == 'not_started': report['status'] = 'worker_terminal'
        except Exception as exc:
            report.update(status='supervisor_error', error=repr(exc))
            if process is not None and process.poll() is None:
                try:
                    remaining=660-(time.perf_counter()-start)
                    if remaining<=0: raise RuntimeError('No external cleanup time remains')
                    cleanup=subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=min(10,remaining))
                    report['secondary_termination_exit_code']=cleanup.returncode
                except Exception as cleanup_exc:
                    report['secondary_cleanup_error']=repr(cleanup_exc)
    report['worker_still_live'] = process is not None and process.poll() is None
    report['supervisor_seconds_before_inventory'] = time.perf_counter()-start
    inventory_start = time.perf_counter()
    report['files'] = [{'name':str(p.relative_to(OUT)).replace('\\','/'), 'bytes':p.stat().st_size,
                        'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUT.rglob('*')) if p.is_file()]
    report['output_bytes'] = sum(f['bytes'] for f in report['files'])
    report['inventory_seconds'] = time.perf_counter()-inventory_start
    report['elapsed_before_receipt_seconds'] = time.perf_counter()-start
    report['within_external_deadline'] = report['elapsed_before_receipt_seconds'] <= 660
    report['within_output_budget'] = report['output_bytes'] <= frozen['budget']['max_output_bytes']
    (OUT / 'supervisor.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))
    return 0 if (report.get('exit_code')==0 and report['status']=='worker_terminal' and
                 not report['worker_still_live'] and report['within_external_deadline'] and report['within_output_budget']) else 1


if __name__=='__main__':
    raise SystemExit(main())
