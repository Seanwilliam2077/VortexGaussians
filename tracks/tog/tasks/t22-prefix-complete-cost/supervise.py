"""External wall cap for the single T22 scientific worker; default plan-only."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WALL_SECONDS = 300.0


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def identities():
    raw = (HERE / 'freeze.json').read_bytes()
    freeze = json.loads(raw)
    if freeze['parent_commit'] != '2b63234f262f66825255628b28cedc0156911745':
        raise ValueError('Unexpected parent commit')
    found = {}
    for item in freeze['artifacts']:
        path = (ROOT / item['path']).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError('Frozen artifact escaped repository')
        value = hashlib.sha256(path.read_bytes()).hexdigest()
        if value != item['sha256'] or item['path'] in found:
            raise ValueError('Frozen artifact mismatch: ' + item['path'])
        found[item['path']] = value
    for name in ('supervise.py', 'benchmark.py', 'methods.py', 'integrators.py', 'PROTOCOL.md'):
        if (HERE / name).relative_to(ROOT).as_posix() not in found:
            raise ValueError('Missing frozen T22 source: ' + name)
    return {'freeze_sha256': hashlib.sha256(raw).hexdigest(), 'artifacts': found}


def run(destination):
    started = time.perf_counter()
    started_utc = now()
    output = Path(destination).resolve()
    if output.exists() or not output.parent.is_dir():
        raise ValueError('A fresh output path with an existing parent is required')
    initial = identities()
    command = [sys.executable, '-I', '-B', '-u', '-X', 'utf8',
               str(HERE / 'benchmark.py'), 'run', '--out', str(output)]
    code, timed_out, launch_error = None, False, None
    stdout, stderr = b'', b''
    try:
        remaining = WALL_SECONDS - (time.perf_counter() - started)
        if remaining <= 0:
            raise subprocess.TimeoutExpired(command, WALL_SECONDS)
        process = subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                                 capture_output=True, timeout=remaining,
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        code, stdout, stderr = process.returncode, process.stdout, process.stderr
    except subprocess.TimeoutExpired as exc:
        # subprocess.run kills and waits for its child before raising here.
        timed_out = True
        code, stdout, stderr = 124, exc.stdout or b'', exc.stderr or b''
    except Exception as exc:
        code = 2
        launch_error = {'type': type(exc).__name__, 'message': str(exc)}
    child_interval = time.perf_counter() - started
    # A failed launch may leave no worker directory; preserve its evidence too.
    output.mkdir(exist_ok=True)
    with (output / 'worker-stdout.log').open('xb') as stream:
        stream.write(stdout)
    with (output / 'worker-stderr.log').open('xb') as stream:
        stream.write(stderr)
    final, identity_error = None, None
    try:
        final = identities()
    except Exception as exc:
        identity_error = {'type': type(exc).__name__, 'message': str(exc)}
    unchanged = final == initial and identity_error is None
    if not unchanged and code == 0:
        code = 2
    record = {'schema': 't22-single-execution-v1', 'invocation': 1,
              'started_utc': started_utc, 'finished_utc': now(), 'command': command,
              'returncode': code, 'timed_out': timed_out, 'launch_error': launch_error,
              'identity_error': identity_error, 'external_wall_cap_seconds': WALL_SECONDS,
              'supervisor_through_worker_exit_seconds': child_interval,
              'supervisor_before_execution_ledger_seconds': time.perf_counter() - started,
              'identities_before': initial, 'identities_after': final,
              'identities_unchanged': unchanged, 'retry_allowed': False,
              'cap_scope': 'initial identity checks, worker launch/imports/two stages/result serialization; post-exit log publication is separate'}
    with (output / 'execution.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(record, stream, indent=2)
        stream.write('\n')
    print(stdout.decode('utf-8', errors='replace'), end='', flush=True)
    if stderr:
        print(stderr.decode('utf-8', errors='replace'), file=sys.stderr, end='', flush=True)
    print(json.dumps({'returncode': code, 'timed_out': timed_out,
                      'worker_interval_seconds': child_interval,
                      'execution_record': str(output / 'execution.json')}), flush=True)
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command')
    execute = commands.add_parser('run')
    execute.add_argument('--out', required=True)
    args = parser.parse_args()
    if args.command is None:
        print(json.dumps({'mode': 'plan-only', 'scientific_worker_invocations': 0,
                          'maximum_authorized_invocations': 1, 'wall_cap_seconds': WALL_SECONDS}))
        return 0
    return run(args.out)


if __name__ == '__main__':
    raise SystemExit(main())
