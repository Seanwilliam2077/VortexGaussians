"""Exactly one supervised T56 scientific child; no retry or fallback."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[3]
def identity(path):
    b=path.read_bytes();return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    start=time.perf_counter();manifest_path=ROOT/'input-manifest.json'
    manifest=json.loads(manifest_path.read_bytes());local=ROOT/'local'
    assert manifest['maximum_scientific_child_invocations']==1 and manifest['child_timeout_seconds']==600
    assert manifest['maximum_reference_trajectories']==6
    for item in manifest['inputs']:
        assert identity(REPO/item['path'])=={k:item[k] for k in ('bytes','sha256')}
    executable=Path(manifest['executable']['path'])
    assert identity(executable)=={k:manifest['executable'][k] for k in ('bytes','sha256')}
    output=ROOT/'result.json';code=ROOT/'reference.py'
    assert not output.exists() and not (ROOT/'execution.json').exists()
    assert not list(local.glob('*.npz')) and not list(local.glob('*-steps.jsonl'))
    command=[str(executable),'-I','-B','-u','-X','utf8',str(code)]
    record=dict(schema='t56-coupled-execution-v1',started_utc=now(),command=command,cwd=str(REPO),
        child_timeout_seconds=600,scientific_child_invocations=1,maximum_reference_trajectories=6,
        input_manifest_identity=identity(manifest_path),code_identity=identity(code),
        supervisor_identity=identity(Path(__file__)),executable_identity=identity(executable))
    with (local/'execution-started.json').open('x',encoding='utf8') as stream:json.dump(record,stream,indent=2)
    begin=time.perf_counter()
    try:
        child=subprocess.run(command,cwd=REPO,capture_output=True,timeout=600)
        stdout,stderr=child.stdout,child.stderr
        record.update(returncode=child.returncode,status='exited_pending_readback')
    except subprocess.TimeoutExpired as exc:
        stdout,stderr=exc.stdout or b'',exc.stderr or b''
        record.update(returncode=None,status='timeout_no_retry')
    except Exception as exc:
        stdout,stderr=b'',repr(exc).encode('utf8')
        record.update(returncode=None,status='launch_error_no_retry')
    record['child_supervised_seconds']=time.perf_counter()-begin;record['logs']=[]
    for name,data in [('stdout.txt',stdout),('stderr.txt',stderr)]:
        path=local/name
        with path.open('xb') as stream:stream.write(data)
        record['logs'].append(dict(path=path.relative_to(ROOT).as_posix(),**identity(path)))
    record['frozen_inputs_unchanged']=all(
        identity(REPO/x['path'])=={k:x[k] for k in ('bytes','sha256')} for x in manifest['inputs'])
    record['executable_unchanged']=identity(executable)==record['executable_identity']
    record['result_json_exists']=output.exists();record['qualified_short_reference_only']=False
    record['completed_case_records']=[dict(path=p.relative_to(ROOT).as_posix(),**identity(p))
                                      for p in sorted(local.glob('[STDQ][0-9]*.json'))]
    record['step_logs']=[dict(path=p.relative_to(ROOT).as_posix(),**identity(p))
                         for p in sorted(local.glob('*-steps.jsonl'))]
    record['raw_files']=[dict(path=p.relative_to(ROOT).as_posix(),**identity(p)) for p in sorted(local.glob('*.npz'))]
    record['completed_case_count']=len(record['completed_case_records'])
    if output.exists():
        record['result_identity']=identity(output)
        try:
            result=json.loads(output.read_bytes());record['result_status']=result['status']
            expected='qualified_short_reference_only' if all(result['checks'].values()) else 'failed_checks'
            assert result['schema']=='t56-coupled-reference-v1' and result['code']==identity(code)
            assert result['status']==expected
            assert [c['name'] for c in result['cases']]==['S32','S64','S128','T64','D96','Q64']
            assert result['completed_trajectories']==6 and result['time_end']==.25
            assert result['candidate_trajectories']==0 and result['full_t1_task_pass'] is None
            assert record['returncode']==(0 if expected=='qualified_short_reference_only' else 2)
            assert record['completed_case_count']==6
            for case in result['cases']:
                assert case['steps']==(200 if case['name']=='T64' else 100)
                assert case['elliptic_solves']==2*case['steps']+3
                assert case['transport_stages']==2*case['steps']
                for key in ('raw','log'):
                    item=case[key];assert identity(local/item['path'])=={k:item[k] for k in ('bytes','sha256')}
            record['status']='completed_'+expected
            record['qualified_short_reference_only']=expected=='qualified_short_reference_only'
        except Exception as exc:
            record.update(status='failed_result_validation_no_retry',result_read_error=repr(exc))
    elif record['status']=='exited_pending_readback':record['status']='failed_no_complete_result_no_retry'
    if not record['frozen_inputs_unchanged'] or not record['executable_unchanged']:
        record.update(status='failed_preservation_no_retry',qualified_short_reference_only=False)
    record['supervisor_elapsed_before_receipt_write_seconds']=time.perf_counter()-start;record['finished_utc']=now()
    with (ROOT/'execution.json').open('x',encoding='utf8',newline='\n') as stream:
        json.dump(record,stream,indent=2);stream.write('\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
