"""One bounded initial-reference qualification; standard-library supervisor."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
def identity(path):
    b=path.read_bytes()
    return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    start=time.perf_counter();manifest_path=ROOT/'input-manifest.json'
    manifest=json.loads(manifest_path.read_bytes())
    assert manifest['maximum_scientific_child_invocations']==1
    assert manifest['child_timeout_seconds']==180
    for item in manifest['inputs']:
        assert identity(REPO/item['path'])=={k:item[k] for k in ('bytes','sha256')}
    executable=Path(manifest['executable']['path'])
    assert identity(executable)=={k:manifest['executable'][k] for k in ('bytes','sha256')}
    code=ROOT/'reference.py';output=ROOT/'result.json';local=ROOT/'local'
    assert not output.exists() and not (ROOT/'execution.json').exists()
    assert not list(local.glob('*.npz'))
    command=[str(executable),'-I','-B','-u','-X','utf8',str(code)]
    record=dict(schema='t55-initial-reference-execution-v1',started_utc=now(),
        command=command,cwd=str(REPO),child_timeout_seconds=180,scientific_child_invocations=1,
        input_manifest_identity=identity(manifest_path),code_identity=identity(code),
        supervisor_identity=identity(Path(__file__)),executable_identity=identity(executable),
        fluid_trajectories=0)
    with (local/'execution-started.json').open('x',encoding='utf8') as stream:json.dump(record,stream,indent=2)
    begin=time.perf_counter()
    try:
        child=subprocess.run(command,cwd=REPO,capture_output=True,timeout=180)
        stdout,stderr=child.stdout,child.stderr
        record.update(returncode=child.returncode,status='exited_pending_readback')
    except subprocess.TimeoutExpired as exc:
        stdout,stderr=exc.stdout or b'',exc.stderr or b''
        record.update(returncode=None,status='timeout_no_retry')
    except Exception as exc:
        stdout,stderr=b'',repr(exc).encode('utf8')
        record.update(returncode=None,status='launch_error_no_retry')
    record['child_supervised_seconds']=time.perf_counter()-begin
    record['logs']=[]
    for name,data in [('stdout.txt',stdout),('stderr.txt',stderr)]:
        path=local/name
        with path.open('xb') as stream:stream.write(data)
        record['logs'].append(dict(path=path.relative_to(ROOT).as_posix(),**identity(path)))
    record['frozen_inputs_unchanged']=all(identity(REPO/x['path'])=={k:x[k] for k in ('bytes','sha256')}
                                           for x in manifest['inputs'])
    record['executable_unchanged']=identity(executable)==record['executable_identity']
    record['result_json_exists']=output.exists();record['qualified_initial_only']=False
    record['partial_case_records']=[dict(path=p.relative_to(ROOT).as_posix(),**identity(p))
                                     for p in sorted(local.glob('[SQD]*.json'))]
    if output.exists():
        record['result_identity']=identity(output)
        try:
            result=json.loads(output.read_bytes());record['result_status']=result['status']
            expected_status='qualified_initial_only' if all(result['checks'].values()) else 'failed_checks'
            assert result['schema']=='t55-initial-axisymmetric-reference-v1'
            assert result['status']==expected_status and result['code']==identity(code)
            assert [c['name'] for c in result['cases']]==['S32','S64','S128','Q64','D96']
            assert result['fluid_trajectories']==0
            assert record['returncode']==(0 if expected_status=='qualified_initial_only' else 2)
            for case in result['cases']:
                assert identity(local/case['raw']['path'])=={k:case['raw'][k] for k in ('bytes','sha256')}
            record['status']='completed_qualified_initial_only' if expected_status=='qualified_initial_only' else 'completed_failed_checks'
            record['qualified_initial_only']=expected_status=='qualified_initial_only'
        except Exception as exc:
            record.update(status='failed_result_validation_no_retry',result_read_error=repr(exc))
    elif record['status']=='exited_pending_readback':
        record['status']='failed_no_complete_result_no_retry'
    if not record['frozen_inputs_unchanged'] or not record['executable_unchanged']:
        record.update(status='failed_preservation_no_retry',qualified_initial_only=False)
    record['supervisor_elapsed_before_receipt_write_seconds']=time.perf_counter()-start
    record['finished_utc']=now()
    with (ROOT/'execution.json').open('x',encoding='utf8',newline='\n') as stream:
        json.dump(record,stream,indent=2);stream.write('\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
