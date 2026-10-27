"""One bounded A06 attempt. No installs, no retry, no user browser/server."""
import argparse
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
NODE = 'C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--execute', action='store_true'); args = parser.parse_args()
    if not args.execute:
        subprocess.run([NODE, str(HERE / 'record.mjs')], check=True)
    else:
        if (HERE / 'supervisor.json').exists() or (HERE / 'run-01').exists():
            raise FileExistsError('A06 attempt already exists; no retry')
        start = time.perf_counter()
        result = {'scope': 'one A06 public-UI recording', 'hardTimeoutSeconds': 180, 'command': [NODE, str(HERE / 'record.mjs'), '--execute']}
        with (HERE / 'execution.stdout.log').open('wb') as stdout, (HERE / 'execution.stderr.log').open('wb') as stderr:
            process = subprocess.Popen(result['command'], stdout=stdout, stderr=stderr)
            result['pid'] = process.pid
            try:
                result['exitCode'] = process.wait(timeout=180)
            except subprocess.TimeoutExpired:
                result['timedOut'] = True
                stop = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, text=True)
                result['termination'] = {'code': stop.returncode, 'stdout': stop.stdout, 'stderr': stop.stderr}
                result['exitCode'] = process.wait(timeout=10)
        result['wallSeconds'] = time.perf_counter() - start
        (HERE / 'supervisor.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result)); raise SystemExit(0 if result['exitCode'] == 0 else 1)
