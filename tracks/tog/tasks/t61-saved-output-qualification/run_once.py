"""One standard-library T61 qualification child, never a scientific rerun."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]

def identity(path):
    digest=hashlib.sha256(); size=0
    with path.open('rb') as stream:
        while block:=stream.read(1024*1024):
            digest.update(block); size+=len(block)
    return dict(bytes=size,sha256=digest.hexdigest())

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    start=time.perf_counter()
    local=ROOT/'local'
    manifest_path=ROOT/'input-manifest.json'
    manifest=json.loads(manifest_path.read_bytes())
    assert manifest['schema']=='t61-saved-output-freeze-v1'
    assert manifest['maximum_qualification_child_invocations']==1 and manifest['child_timeout_seconds']==60
    assert manifest['new_scientific_invocations_permitted']==0
    assert manifest['expected_python']=='3.12.13'
    for item in manifest['inputs']:
        assert identity(REPO/item['path'])=={k:item[k] for k in ('bytes','sha256')},item['path']
    for item in manifest['external_inputs']:
        assert identity(Path(item['path']))=={k:item[k] for k in ('bytes','sha256')},item['path']
    exe=Path(manifest['executable']['path'])
    assert identity(exe)=={k:manifest['executable'][k] for k in ('bytes','sha256')}
    output=ROOT/'result.json'
    assert not output.exists() and not (ROOT/'execution.json').exists()
    command=[str(exe),'-I','-B','-u','-X','utf8',str(ROOT/'validate.py')]
    receipt=dict(schema='t61-saved-output-execution-v1',started_utc=now(),command=command,
        cwd=str(REPO),child_timeout_seconds=60,qualification_child_invocations=0,
        new_scientific_invocations=0,new_scientific_trajectories=0,T60_history_reclassified=False,
        input_manifest_identity=identity(manifest_path),supervisor_identity=identity(Path(__file__)),
        validator_identity=identity(ROOT/'validate.py'),executable_identity=identity(exe),
        accepted_saved_evidence=False,ordinary_model_verdict='unqualified',full_t1_task_pass=None)
    with (local/'execution-started.json').open('x',encoding='utf-8') as stream:
        json.dump(receipt,stream,indent=2)
    begin=time.perf_counter(); child=None
    with (local/'stdout.txt').open('xb') as stdout, (local/'stderr.txt').open('xb') as stderr:
        try:
            receipt['qualification_child_invocations']=1
            child=subprocess.Popen(command,cwd=REPO,stdout=stdout,stderr=stderr,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
            receipt['child_pid']=child.pid
            try:
                receipt['returncode']=child.wait(timeout=max(.001,60-(time.perf_counter()-begin)))
                receipt['status']='exited_pending_readback'
            except subprocess.TimeoutExpired:
                child.kill(); receipt['returncode']=child.wait()
                receipt['status']='timeout_no_retry'
        except Exception as exc:
            receipt.update(status='launch_error_no_retry',error=repr(exc))
        finally:
            if child is not None and child.poll() is None:
                child.kill(); receipt['returncode']=child.wait()
    receipt['qualification_child_supervised_seconds']=time.perf_counter()-begin
    receipt['logs']=[dict(path='local/'+name,**identity(local/name)) for name in ('stdout.txt','stderr.txt')]
    receipt['inputs_unchanged']=all(identity(REPO/x['path'])=={k:x[k] for k in ('bytes','sha256')} for x in manifest['inputs'])
    receipt['external_inputs_unchanged']=all(identity(Path(x['path']))=={k:x[k] for k in ('bytes','sha256')} for x in manifest['external_inputs'])
    receipt['input_manifest_unchanged']=identity(manifest_path)==receipt['input_manifest_identity']
    receipt['executable_unchanged']=identity(exe)==receipt['executable_identity']
    receipt['result_exists']=output.exists()
    if output.exists():
        receipt['result_identity']=identity(output)
        try:
            result=json.loads(output.read_bytes())
            assert result['schema']=='t61-saved-output-qualification-v1'
            assert type(result['accepted_saved_evidence']) is bool
            assert result['T60_history_reclassified'] is False
            assert result['new_scientific_invocations']==result['new_scientific_trajectories']==0
            if result['accepted_saved_evidence']:
                assert result['status'] in ('qualified_saved_reference_ordinary_model_pass','qualified_saved_reference_ordinary_model_fail')
                assert result['reference_qualified_full_window'] is True
                assert result['ordinary_model_verdict'] in ('pass','fail')
                assert result['full_t1_task_pass'] is (result['ordinary_model_verdict']=='pass')
                assert result['status']=='qualified_saved_reference_ordinary_model_'+result['ordinary_model_verdict']
                assert receipt['returncode']==0 and receipt['status']=='exited_pending_readback'
                assert receipt['qualification_child_supervised_seconds']<=60
                assert receipt['inputs_unchanged'] and receipt['external_inputs_unchanged'] and receipt['input_manifest_unchanged'] and receipt['executable_unchanged']
                receipt.update(status='completed_'+result['status'],accepted_saved_evidence=True,
                    ordinary_model_verdict=result['ordinary_model_verdict'],full_t1_task_pass=result['full_t1_task_pass'])
            else:
                assert result['status']=='qualification_failed' and result['ordinary_model_verdict']=='unqualified'
                assert result['full_t1_task_pass'] is None and receipt['returncode']==2
                assert receipt['status']=='exited_pending_readback'
                receipt['status']='qualification_failed_no_retry'
        except Exception as exc:
            receipt['readback_error']=repr(exc)
            if receipt['status']=='exited_pending_readback':receipt['status']='failed_result_validation_no_retry'
    elif receipt['status']=='exited_pending_readback':
        receipt['status']='missing_result_no_retry'
    if not all(receipt[k] for k in ('inputs_unchanged','external_inputs_unchanged','input_manifest_unchanged','executable_unchanged')):
        receipt.update(status='failed_preservation_no_retry',accepted_saved_evidence=False,
                       ordinary_model_verdict='unqualified',full_t1_task_pass=None)
    receipt['prior_T56_through_T60_scientific_child_seconds']=1976.6796338998247
    receipt['supervisor_elapsed_before_receipt_write_seconds']=time.perf_counter()-start
    receipt['finished_utc']=now()
    with (ROOT/'execution.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(receipt,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({k:receipt[k] for k in ('status','qualification_child_supervised_seconds',
        'accepted_saved_evidence','ordinary_model_verdict','inputs_unchanged')},indent=2))

if __name__=='__main__':
    main()
