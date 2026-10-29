"""T54 single scientific attempt; standard-library supervisor only."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]


def identity(path):
    data = path.read_bytes()
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    started = time.perf_counter()
    manifest_path = ROOT/'input-manifest.json'
    manifest = json.loads(manifest_path.read_bytes())
    assert manifest['maximum_scientific_child_invocations'] == 1
    assert manifest['cumulative_scientific_attempt_number'] == 2
    for item in manifest['inputs']:
        assert identity(REPO/item['path']) == {k:item[k] for k in ('bytes','sha256')}
    executable = Path(manifest['executable']['path'])
    assert identity(executable) == {k:manifest['executable'][k] for k in ('bytes','sha256')}
    evaluator = REPO/manifest['evaluator_path']
    output = ROOT/'result.json'
    assert not output.exists() and not (ROOT/'execution.json').exists()
    assert not (evaluator.parent/'result.json').exists()
    command = [str(executable),'-I','-B','-u','-X','utf8',str(evaluator),str(output)]
    record = dict(schema='t54-single-verification-execution-v1', started_utc=now(),
        command=command,cwd=str(REPO), child_timeout_seconds=60,
        scientific_child_invocations=1,cumulative_scientific_attempt_number=2,
        prior_failed_scientific_attempts=1, prior_runtime_diagnostic_invocations=2,
        input_manifest_identity=identity(manifest_path),
        evaluator_identity=identity(evaluator), executable_identity=identity(executable),
        supervisor_identity=identity(Path(__file__)))
    local = ROOT/'local'
    local.mkdir(exist_ok=True)
    with (local/'execution-started.json').open('x', encoding='utf8') as stream:
        json.dump(record,stream,indent=2)
    begin = time.perf_counter()
    try:
        child = subprocess.run(command,cwd=REPO,capture_output=True,timeout=60)
        stdout,stderr = child.stdout,child.stderr
        record.update(returncode=child.returncode,
                      status='child_exit_zero_pending_validation' if child.returncode==0 else 'failed_child_no_retry')
    except subprocess.TimeoutExpired as exc:
        stdout,stderr = exc.stdout or b'',exc.stderr or b''
        record.update(returncode=None,status='timeout_no_retry')
    except Exception as exc:
        stdout,stderr = b'',repr(exc).encode('utf8')
        record.update(returncode=None,status='launch_error_no_retry')
    record['child_supervised_seconds'] = time.perf_counter()-begin
    record['logs'] = []
    for name,data in [('stdout.txt',stdout),('stderr.txt',stderr)]:
        path=local/name
        with path.open('xb') as stream:
            stream.write(data)
        record['logs'].append(dict(path=path.relative_to(ROOT).as_posix(),**identity(path)))
    record['frozen_inputs_unchanged'] = all(
        identity(REPO/item['path']) == {k:item[k] for k in ('bytes','sha256')}
        for item in manifest['inputs'])
    record['executable_unchanged'] = identity(executable) == record['executable_identity']
    record['T52_result_still_absent'] = not (evaluator.parent/'result.json').exists()
    record['result_json_exists'] = output.exists()
    record['scientific_consistency_qualified'] = False
    if output.exists():
        record['result_identity'] = identity(output)
        try:
            result = json.loads(output.read_bytes())
            record['result_status'] = result['status']
            record['result_code_identity_matches'] = result['measurement_script'] == identity(evaluator)
            record['result_settings_match'] = result['settings'] == dict(
                orders=[128,256,512],radius=12.0,tolerance=1e-9,
                series_threshold=.25,series_terms=12,total_nodes=896)
            record['result_schema_matches'] = result['schema'] == 't52-scalar-enstrophy-tangent-measurement-v1'
            if (record['returncode']==0 and result['status']=='consistent'
                    and record['result_code_identity_matches'] and record['result_settings_match']
                    and record['result_schema_matches'] and record['frozen_inputs_unchanged']
                    and record['executable_unchanged'] and record['T52_result_still_absent']):
                record.update(status='completed_consistent',scientific_consistency_qualified=True)
            else:
                record['status']='failed_result_validation_no_retry'
        except Exception as exc:
            record.update(status='failed_result_read_no_retry', result_read_error=repr(exc))
    elif record['returncode']==0:
        record['status']='failed_missing_result_no_retry'
    if not record['frozen_inputs_unchanged'] or not record['executable_unchanged'] or not record['T52_result_still_absent']:
        record.update(status='failed_preservation_no_retry',scientific_consistency_qualified=False)
    record['supervisor_elapsed_before_receipt_write_seconds']=time.perf_counter()-started
    record['finished_utc']=now()
    with (ROOT/'execution.json').open('x',encoding='utf8',newline='\n') as stream:
        json.dump(record,stream,indent=2)
        stream.write('\n')
    print(json.dumps(record,indent=2))


if __name__=='__main__':
    main()
