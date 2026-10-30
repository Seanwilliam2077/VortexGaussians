"""One T59 scientific child, complete costs and observed resource stops; no retry."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
spec=importlib.util.spec_from_file_location('memory_observer',ROOT.parent/'t57-finer-short-reference'/'memory.py')
memory=importlib.util.module_from_spec(spec);spec.loader.exec_module(memory)
NAMES=['S64','S128','S256','T128','D192','Q128']
CHECKS={'initial_analytic','all_stage_invariants','vorticity_disagreements','velocity_disagreements',
    'centroid_disagreements','covariance_disagreements','spatial_reduction','circulation_ledger',
    'q_squared_drift','axial_impulse_drift','solver_port_regression'}

def identity(path):
    digest=hashlib.sha256();size=0
    with path.open('rb') as stream:
        while chunk:=stream.read(1024*1024):digest.update(chunk);size+=len(chunk)
    return dict(bytes=size,sha256=digest.hexdigest())

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def items(paths):return [dict(path=p.relative_to(ROOT).as_posix(),**identity(p)) for p in paths]

def main():
    start=time.perf_counter();local=ROOT/'local'
    manifest_path=ROOT/'input-manifest.json';manifest=json.loads(manifest_path.read_bytes())
    assert manifest['schema']=='t59-direct-coupled-freeze-v1'
    assert manifest['maximum_scientific_child_invocations']==1 and manifest['child_timeout_seconds']==600
    assert manifest['maximum_new_reference_trajectories']==6 and manifest['reused_reference_trajectories']==0
    assert manifest['peak_working_set_stop_bytes']==2*1024**3
    for item in manifest['inputs']:
        assert identity(REPO/item['path'])=={k:item[k] for k in ('bytes','sha256')},item['path']
    executable=Path(manifest['executable']['path'])
    assert identity(executable)=={k:manifest['executable'][k] for k in ('bytes','sha256')}
    output=ROOT/'result.json';code=ROOT/'reference.py'
    assert not output.exists() and not (ROOT/'execution.json').exists()
    assert not list(local.glob('*.npz')) and not list(local.glob('*-steps.jsonl'))
    assert not (local/'checkpoints.jsonl').exists()
    host=memory.host_memory()
    assert host['available_physical_bytes']>=manifest['minimum_available_host_bytes']
    command=[str(executable),'-I','-B','-u','-X','utf8',str(code)]
    record=dict(schema='t59-direct-coupled-execution-v1',started_utc=now(),command=command,cwd=str(REPO),
        child_timeout_seconds=600,scientific_child_invocations=0,maximum_new_reference_trajectories=6,
        reused_reference_trajectories=0,peak_working_set_stop_bytes=2*1024**3,host_before_launch=host,
        memory_sample_interval_seconds=.25,input_manifest_identity=identity(manifest_path),
        code_identity=identity(code),supervisor_identity=identity(Path(__file__)),executable_identity=identity(executable))
    with (local/'execution-started.json').open('x',encoding='utf8') as stream:json.dump(record,stream,indent=2)
    child=None;handle=None;peak=0;samples=0;begin=time.perf_counter()
    with (local/'stdout.txt').open('xb') as stdout,(local/'stderr.txt').open('xb') as stderr,\
         (local/'memory.jsonl').open('x',encoding='utf8',newline='\n') as memlog:
        try:
            record['scientific_child_invocations']=1
            child=subprocess.Popen(command,cwd=REPO,stdout=stdout,stderr=stderr)
            record['child_pid']=child.pid;handle=memory.open_process(child.pid)
            while True:
                try:observation=memory.process_memory(handle)
                except OSError:
                    if child.poll() is None:raise
                    observation=None;record['final_memory_query_unavailable_after_exit']=True
                if observation is not None:
                    elapsed=time.perf_counter()-begin;peak=max(peak,observation['peak_working_set_bytes'])
                    memlog.write(json.dumps(dict(elapsed_seconds=elapsed,**observation))+'\n');memlog.flush();samples+=1
                elapsed=time.perf_counter()-begin
                if peak>2*1024**3:record['status']='memory_stop_no_retry';break
                if elapsed>=600:record['status']='timeout_no_retry';break
                if child.poll() is not None:record['status']='exited_pending_readback';break
                time.sleep(min(.25,600-elapsed))
        except Exception as exc:
            record.update(status='observer_or_launch_error_no_retry',observer_or_launch_error=repr(exc))
        finally:
            if child is not None:
                if child.poll() is None:child.kill()
                record['returncode']=child.wait()
            else:record['returncode']=None
            if handle is not None:memory.kernel.CloseHandle(handle)
    record['child_supervised_seconds']=time.perf_counter()-begin
    record.update(observed_peak_working_set_bytes=peak,memory_samples=samples,memory_is_observed_not_hard_allocation_limit=True)
    record['logs']=items([local/n for n in ('stdout.txt','stderr.txt','memory.jsonl')])
    record['frozen_inputs_unchanged']=all(identity(REPO/x['path'])=={k:x[k] for k in ('bytes','sha256')} for x in manifest['inputs'])
    record['executable_unchanged']=identity(executable)==record['executable_identity']
    record['result_json_exists']=output.exists();record['qualified_short_reference_only']=False
    record['case_metadata_files']=items([local/(n+'.json') for n in NAMES if (local/(n+'.json')).exists()])
    record['completed_case_records']=[];record['case_validation_errors']=[]
    for item in record['case_metadata_files']:
        try:
            c=json.loads((ROOT/item['path']).read_bytes())
            assert c['name'] in NAMES and Path(item['path']).name==c['name']+'.json'
            assert c['steps']==(200 if c['name']=='T128' else 100)
            assert c['elliptic_solves']==2*c['steps']+3 and c['transport_stages']==2*c['steps']
            for key in ('raw','log'):
                saved=c[key];assert Path(saved['path']).name==saved['path']
                assert identity(local/saved['path'])=={k:saved[k] for k in ('bytes','sha256')}
            record['completed_case_records'].append(item)
        except Exception as exc:
            record['case_validation_errors'].append(dict(path=item['path'],error=repr(exc)))
    record['step_logs']=items(sorted(local.glob('*-steps.jsonl')))
    record['raw_files']=items(sorted(local.glob('*.npz')))
    record['checkpoint_metadata_files']=items(sorted(local.glob('*-snapshot-*.json')))
    record['checkpoint_ledger']=items([local/'checkpoints.jsonl']) if (local/'checkpoints.jsonl').exists() else []
    record['failure_records']=items([local/'failure.json']) if (local/'failure.json').exists() else []
    record['validated_checkpoint_records']=[];record['checkpoint_validation_errors']=[]
    for item in record['checkpoint_metadata_files']:
        try:
            c=json.loads((ROOT/item['path']).read_bytes())
            assert c['name'] in NAMES and c['index'] in (0,1,2)
            assert c['time']==(0.,.125,.25)[c['index']]
            assert c['step']==c['index']*(100 if c['name']=='T128' else 50)
            expected=c['name']+'-snapshot-'+str(c['index'])
            assert Path(item['path']).name==expected+'.json' and c['raw']['path']==expected+'.npz'
            assert identity(local/c['raw']['path'])=={k:c['raw'][k] for k in ('bytes','sha256')}
            record['validated_checkpoint_records'].append(item)
        except Exception as exc:
            record['checkpoint_validation_errors'].append(dict(path=item['path'],error=repr(exc)))
    record['completed_case_count']=len(record['completed_case_records'])
    record['validated_checkpoint_count']=len(record['validated_checkpoint_records'])
    if output.exists():
        record['result_identity']=identity(output)
        try:
            result=json.loads(output.read_bytes());record['result_status']=result['status']
            assert result['schema']=='t59-direct-coupled-reference-v1' and result['code']==identity(code)
            assert result['python']==manifest['expected_python'] and result['numpy']==manifest['expected_numpy']
            assert Path(result['executable'])==executable
            assert set(result['checks'])==CHECKS and all(isinstance(x,bool) for x in result['checks'].values())
            expected='qualified_short_reference_only' if all(result['checks'].values()) else 'failed_checks'
            assert result['status']==expected
            assert [c['name'] for c in result['cases']]==NAMES
            assert result['completed_trajectories']==result['new_completed_trajectories']==6
            assert result['reused_trajectories']==0 and result['time_end']==.25
            assert result['candidate_trajectories']==result['new_CG_solves']==0 and result['full_t1_task_pass'] is None
            assert result['formal_error_certificate'] is False
            assert result['prior_T56_status']=='failed_checks' and result['prior_T57_status']=='timeout_no_retry'
            assert record['returncode']==(0 if expected=='qualified_short_reference_only' else 2)
            assert record['completed_case_count']==6 and record['validated_checkpoint_count']==18
            assert not record['checkpoint_validation_errors'] and not record['case_validation_errors'] and not record['failure_records'] and len(record['raw_files'])==24
            assert len(result['comparisons'])==15 and len(result['port_regressions'])==6
            for key,relative in (('spatial_code','t55-axisymmetric-reference/reference.py'),
                                 ('base_code','t56-coupled-reference/reference.py'),
                                 ('solver_code','t58-separable-solver-qualification/solver.py')):
                assert result[key]==identity(ROOT.parent/relative),key
            for case in result['cases']:
                assert case['steps']==(200 if case['name']=='T128' else 100)
                assert case['elliptic_solves']==2*case['steps']+3 and case['transport_stages']==2*case['steps']
                assert case==json.loads((local/(case['name']+'.json')).read_bytes())
                for key in ('raw','log'):
                    item=case[key]
                    assert Path(item['path']).name==item['path']
                    assert identity(local/item['path'])=={k:item[k] for k in ('bytes','sha256')}
            assert record['status']=='exited_pending_readback'
            assert 0<samples and peak<=2*1024**3 and record['child_supervised_seconds']<=600
            record['status']='completed_'+expected;record['qualified_short_reference_only']=expected=='qualified_short_reference_only'
        except Exception as exc:
            record['result_read_error']=repr(exc)
            if record['status']=='exited_pending_readback':record['status']='failed_result_validation_no_retry'
    elif record['status']=='exited_pending_readback':record['status']='failed_no_complete_result_no_retry'
    if not record['frozen_inputs_unchanged'] or not record['executable_unchanged']:
        record.update(status='failed_preservation_no_retry',qualified_short_reference_only=False)
    record['prior_T56_T57_T58_supervised_seconds']=manifest['prior_T56_T57_T58_supervised_seconds']
    record['cumulative_T56_T57_T58_T59_supervised_seconds']=record['prior_T56_T57_T58_supervised_seconds']+record['child_supervised_seconds']
    record['supervisor_elapsed_before_receipt_write_seconds']=time.perf_counter()-start;record['finished_utc']=now()
    with (ROOT/'execution.json').open('x',encoding='utf8',newline='\n') as stream:json.dump(record,stream,indent=2);stream.write('\n')
    print(json.dumps({k:record[k] for k in ('status','returncode','child_supervised_seconds','completed_case_count',
        'validated_checkpoint_count','observed_peak_working_set_bytes','qualified_short_reference_only')},indent=2))

if __name__=='__main__':main()
