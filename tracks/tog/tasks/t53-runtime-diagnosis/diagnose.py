"""One T53 diagnostic slot per call; Python standard library supervisor only."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
RESEARCH = Path('C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/python.exe')
BUNDLED = Path('C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')


def identity(path):
    data = path.read_bytes()
    return dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def stages(record):
    return [entry['stage'] for entry in record['stage_records']]


def load(slot):
    path = ROOT / ('diagnostic-' + slot + '.json')
    return json.loads(path.read_bytes()) if path.exists() else None


def passed(record):
    return (record is not None and record['returncode'] == 0
            and record['frozen_inputs_unchanged'] and 'complete' in stages(record))


def main():
    start = time.perf_counter()
    slot = sys.argv[1]
    assert slot in ('A', 'B', 'C')
    freeze = json.loads((ROOT/'input-manifest.json').read_bytes())
    for item in freeze['inputs']:
        actual = identity(ROOT/item['name'])
        assert all(actual[key] == item[key] for key in ('bytes', 'sha256'))
    a, b, c = (load(key) for key in ('A', 'B', 'C'))
    for prior in (a, b, c):
        if prior is not None:
            assert prior['frozen_inputs_unchanged'], 'invalid prior evidence; stop diagnosis'
    if slot == 'A':
        assert a is None and b is None and c is None
    elif slot == 'B':
        assert a is not None and b is None and c is None
        assert 'numpy_import_begin' in stages(a) and 'numpy_import_ok' not in stages(a)
    else:
        assert a is not None and c is None and not passed(a) and not passed(b)
        if 'numpy_import_begin' in stages(a) and 'numpy_import_ok' not in stages(a):
            assert b is not None
    executable = BUNDLED if slot == 'C' else RESEARCH
    mode = 'dll' if slot == 'B' else 'plain'
    command = [str(executable), '-I', '-B', '-u', '-X', 'utf8', str(ROOT/'probe.py'), mode]
    record = dict(schema='t53-runtime-diagnostic-v1', slot=slot,
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        command=command, cwd=str(REPO), timeout_seconds=20,
        executable_identity=identity(executable), probe_identity=identity(ROOT/'probe.py'),
        supervisor_identity=identity(Path(__file__)),
        input_manifest_identity=identity(ROOT/'input-manifest.json'),
        scientific_measurement_invocations=0)
    local = ROOT/'local'
    local.mkdir(exist_ok=True)
    with (local/(slot+'-started.json')).open('x', encoding='utf8') as stream:
        json.dump(record, stream, indent=2)
    begin = time.perf_counter()
    try:
        child = subprocess.run(command, cwd=REPO, capture_output=True, timeout=20)
        stdout, stderr = child.stdout, child.stderr
        record.update(returncode=child.returncode, execution_status='exited')
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or b'', exc.stderr or b''
        record.update(returncode=None, execution_status='timeout')
    except Exception as exc:
        stdout, stderr = b'', repr(exc).encode('utf8')
        record.update(returncode=None, execution_status='launch_error')
    record['child_supervised_seconds'] = time.perf_counter()-begin
    records, unparsed = [], []
    for line in stdout.decode('utf8', errors='replace').splitlines():
        try:
            entry = json.loads(line)
            if isinstance(entry, dict) and 'stage' in entry:
                records.append(entry)
            else:
                unparsed.append(line)
        except json.JSONDecodeError:
            unparsed.append(line)
    record.update(stage_records=records, unparsed_stdout_lines=unparsed)
    record['logs'] = []
    for kind, data in [('stdout', stdout), ('stderr', stderr)]:
        path = local/(slot+'-'+kind+'.txt')
        with path.open('xb') as stream:
            stream.write(data)
        record['logs'].append(identity(path))
    record['stderr_text'] = stderr.decode('utf8', errors='replace')
    record['frozen_inputs_unchanged'] = all(
        all(identity(ROOT/item['name'])[key] == item[key] for key in ('bytes', 'sha256'))
        for item in freeze['inputs'])
    record['diagnostic_pass'] = passed(record)
    record['supervisor_elapsed_before_receipt_write_seconds'] = time.perf_counter()-start
    with (ROOT/('diagnostic-'+slot+'.json')).open('x', encoding='utf8', newline='\n') as stream:
        json.dump(record, stream, indent=2)
        stream.write('\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
