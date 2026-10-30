"""One supervised A16 recording/media worker. No execution without --execute."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import traceback

HERE = Path(__file__).resolve().parent
NODE = 'C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
MODULE = 'C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'
BROWSER = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    command = [NODE, str(HERE / 'record.mjs'), '--execute']
    plan = dict(command=command, attempts=1, browser_seconds=150,
                worker_wait_seconds=270, supervisor_seconds=300)
    if not args.execute:
        print(json.dumps(dict(execution=False, **plan)))
        return 0
    for name in ('run-01', 'attempt.json', 'supervisor.json', 'execution.stdout.log', 'execution.stderr.log'):
        if (HERE / name).exists():
            raise FileExistsError('Existing A16 evidence; no retry: ' + name)
    began = time.perf_counter()
    write_new(HERE / 'attempt.json', dict(schema='a16-attempt-v1',
              created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **plan))
    process = None
    receipt = dict(schema='a16-supervisor-v1', **plan, timed_out=False,
                   errors=[], termination_attempted=False)
    env = dict(os.environ, PLAYWRIGHT_MODULE=MODULE, BROWSER_EXECUTABLE=BROWSER)

    def terminate_own_tree():
        receipt['termination_attempted'] = True
        remaining = 300 - (time.perf_counter() - began)
        if remaining <= 0:
            receipt['errors'].append('No remaining total budget for own-tree cleanup')
            return
        try:
            stopped = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                capture_output=True, text=True, timeout=min(15, remaining),
                creationflags=subprocess.CREATE_NO_WINDOW)
            receipt['termination'] = {key: getattr(stopped, key) for key in ('returncode', 'stdout', 'stderr')}
        except BaseException as error:
            receipt['errors'].append('termination: ' + repr(error))
        remaining = 300 - (time.perf_counter() - began)
        if remaining > 0:
            try:
                receipt['exit_code'] = process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                receipt['errors'].append('Own worker remained live at total budget')

    try:
        with (HERE / 'execution.stdout.log').open('xb') as stdout, \
             (HERE / 'execution.stderr.log').open('xb') as stderr:
            launched = time.perf_counter()
            process = subprocess.Popen(command, cwd=HERE, stdout=stdout,
                stderr=stderr, env=env, creationflags=subprocess.CREATE_NO_WINDOW)
            receipt['pid'] = process.pid
            try:
                receipt['exit_code'] = process.wait(timeout=max(.001, 270 - (time.perf_counter() - began)))
            except subprocess.TimeoutExpired:
                receipt['timed_out'] = True
                terminate_own_tree()
            finally:
                receipt['worker_lifetime_observed_seconds'] = time.perf_counter() - launched
    except BaseException as error:
        receipt['errors'].append(repr(error))
        receipt['traceback'] = traceback.format_exc()
    finally:
        if process is not None and process.poll() is None and not receipt['termination_attempted']:
            terminate_own_tree()
        receipt['worker_launched'] = process is not None
        receipt['poll_exit_code'] = process.poll() if process is not None else None
        receipt['still_live'] = process is not None and process.poll() is None
        receipt['requires_cleanup'] = receipt['still_live']
        result_path = HERE / 'run-01' / 'result.json'
        receipt['partial_result_exists'] = result_path.exists()
        if result_path.exists():
            try:
                result = json.loads(result_path.read_bytes())
                receipt['worker_status'] = result.get('status')
                receipt['resources_closed'] = result.get('resourcesClosed', {})
                receipt['requires_cleanup'] |= any(receipt['resources_closed'].get(key) is not True
                                                    for key in ('context', 'browser', 'server'))
                for source, target in [('recordingCompleted', 'recording_completed'),
                                       ('mediaValidated', 'media_validated'), ('sourcesUnchanged', 'sources_unchanged')]:
                    receipt[target] = result.get(source) is True
                receipt['worker_failure'] = result.get('failure')
            except BaseException as error:
                receipt['errors'].append('partial-result-readback: ' + repr(error))
        elif process is not None:
            receipt['requires_cleanup'] = True
        receipt['parent_terminal_check_seconds'] = time.perf_counter() - began
        receipt['success'] = bool(process is not None and receipt['poll_exit_code'] == 0
            and not receipt['timed_out'] and not receipt['errors'] and not receipt['requires_cleanup']
            and receipt.get('worker_status') == 'completed_recording_and_media'
            and receipt.get('recording_completed') and receipt.get('media_validated') and receipt.get('sources_unchanged')
            and receipt.get('worker_lifetime_observed_seconds', 301) <= 270
            and receipt['parent_terminal_check_seconds'] <= 300)
        receipt['no_retry'] = True
        receipt['stop_recording_loop_after_failure'] = True
        receipt['timing_limit'] = ('Child launch, wait, and attempted own-tree cleanup are included; final receipt/stdout writing is excluded. '
                                   'Parent poll is not a proof that every descendant exited.')
        write_new(HERE / 'supervisor.json', receipt)
        print(json.dumps(receipt, ensure_ascii=False))
    return 0 if receipt['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
