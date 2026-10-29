"""Reserve one T35 worker; preserve raw evidence without post-timeout computation."""
import datetime
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = HERE / 'run-01'


def verify(frozen):
    for item in json.loads(frozen)['artifacts']:
        path = (ROOT / item['path']).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError('Frozen path escapes repository')
        data = path.read_bytes()
        if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Frozen artifact changed: ' + item['path'])
    if (HERE / 'freeze.json').read_bytes() != frozen:
        raise ValueError('Freeze changed')


def main():
    if OUT.exists():
        raise SystemExit('Existing attempt; no retry')
    total_tic = time.perf_counter()
    frozen = (HERE / 'freeze.json').read_bytes()
    source_tic = time.perf_counter()
    verify(frozen)
    initial_source_seconds = time.perf_counter() - source_tic
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    OUT.mkdir()
    with (OUT / 'attempt.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump({'started_utc': started, 'invocation': 1, 'freeze_sha256': hashlib.sha256(frozen).hexdigest(),
                   'retry_allowed': False, 'computation_seconds': 600, 'outer_seconds': 630}, stream)
        stream.write('\n')
    child = None
    errors = []
    timed_out = False
    wait_tic = time.perf_counter()
    cleanup_seconds = 0.
    with (OUT / 'stdout.txt').open('xb') as stdout, (OUT / 'stderr.txt').open('xb') as stderr:
        try:
            child = subprocess.Popen([sys.executable, '-I', '-B', '-u', '-X', 'utf8', str(HERE / 'run.py')],
                                     cwd=ROOT, stdout=stdout, stderr=stderr,
                                     creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            child.wait(timeout=max(0., 630. - (time.perf_counter() - wait_tic)))
        except subprocess.TimeoutExpired as error:
            timed_out = True
            errors.append(repr(error))
        except Exception as error:
            errors.append(repr(error))
        finally:
            if child is not None and child.poll() is None:
                cleanup_tic = time.perf_counter()
                try:
                    # This worker starts no subprocesses, browser or GPU jobs.
                    child.kill()
                    child.wait(timeout=max(0., 10. - (time.perf_counter() - cleanup_tic)))
                except Exception as error:
                    errors.append('cleanup: ' + repr(error))
                cleanup_seconds = time.perf_counter() - cleanup_tic
    terminated_ns = time.perf_counter_ns()
    process_seconds = time.perf_counter() - wait_tic
    post_tic = time.perf_counter()
    try:
        verify(frozen)
        post_source = {'pass': True}
    except Exception as error:
        post_source = {'pass': False, 'error': repr(error)}
        errors.append('post_source: ' + repr(error))
    post_source_seconds = time.perf_counter() - post_tic
    # Inspection only: never import a scientific module or recover packaging here.
    progress = None
    if (OUT / 'progress.bin').exists():
        raw = (OUT / 'progress.bin').read_bytes()
        if len(raw) == 72 and hashlib.sha256(raw[:40]).digest() == raw[40:]:
            tag, sequence, pixel, code, start_ns = struct.unpack('<8s4Q', raw[:40])
            if tag == b'T35PRG01' and (code >> 32) in (0, 1, 2) and start_ns <= terminated_ns:
                progress = {'sequence': sequence, 'pixel_index': None if pixel == (1 << 64) - 1 else pixel,
                            'stage_code': code & 0xffffffff, 'state_code': code >> 32,
                            'stage_started_perf_counter_ns': start_ns,
                            'active_stage_elapsed_upper_bound_seconds': (terminated_ns - start_ns) / 1e9 if (code >> 32) == 0 else None,
                            'note': 'Hard-stop active elapsed includes termination latency; not a successful solver measurement.'}
        if progress is None:
            progress = {'valid': False, 'reason': 'Missing/checksum-invalid or interrupted fixed progress record'}
    worker = None
    if (OUT / 'result.json').exists():
        try:
            worker = json.loads((OUT / 'result.json').read_bytes())
        except Exception as error:
            errors.append('worker_result: ' + repr(error))
    packaging_needed = (OUT / 'pixels.bin').exists() and (worker is None or worker.get('publication_status') != 'packaged')
    raw_names = ['pixels.bin', 'leaves.bin', 'failure.json', 'frame.json', 'result.json']
    raw_numeric_bytes = sum((OUT / name).stat().st_size for name in raw_names if (OUT / name).exists())
    if raw_numeric_bytes > 32 * 1024 * 1024:
        errors.append('Raw numeric publication cap exceeded; evidence preserved')
    logs = {}
    for name in ['stdout.txt', 'stderr.txt']:
        data = (OUT / name).read_bytes()
        logs[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    alive = child is not None and child.poll() is None
    success = (child is not None and child.returncode == 0 and not timed_out and not errors and
               not alive and post_source['pass'] and worker is not None and
               worker.get('status') == 'qualified_first_complete_frame_only')
    receipt = {'schema': 't35-execution-v1', 'invocation': 1, 'started_utc': started,
               'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'returncode': None if child is None else child.returncode, 'timed_out': timed_out,
               'errors': errors, 'child_still_running': alive, 'success': success,
               'computation_cap_seconds': 600, 'external_wait_seconds': 630, 'cleanup_cap_seconds': 10,
               'process_and_cleanup_seconds': process_seconds, 'cleanup_seconds': cleanup_seconds,
               'initial_source_check': {'pass': True, 'seconds': initial_source_seconds},
               'post_source_check': dict(post_source, seconds=post_source_seconds),
               'supervisor_seconds_before_receipt': time.perf_counter() - total_tic,
               'freeze_sha256': hashlib.sha256(frozen).hexdigest(), 'retries': 0,
               'logs': logs, 'last_progress': progress, 'raw_numeric_bytes': raw_numeric_bytes,
               'packaging_needed': packaging_needed, 'packaging_recovery_invocations': 0,
               'partial_files_preserved': True, 'not_a_strong_baseline_or_speedup_trial': True}
    with (OUT / 'execution.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(receipt, allow_nan=False))
    return 0 if success else 2


if __name__ == '__main__':
    raise SystemExit(main())
