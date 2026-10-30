"""One T57 scientific child; observed time/memory caps; never retry."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[3]
spec=importlib.util.spec_from_file_location('memory_observer',ROOT/'memory.py')
memory=importlib.util.module_from_spec(spec);spec.loader.exec_module(memory)

def identity(path):
    digest=hashlib.sha256();size=0
    with path.open('rb') as stream:
        while chunk:=stream.read(1024*1024):digest.update(chunk);size+=len(chunk)
    return dict(bytes=size,sha256=digest.hexdigest())

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    start=time.perf_counter();manifest_path=ROOT/'input-manifest.json';local=ROOT/'local'
    manifest=json.loads(manifest_path.read_bytes())
    assert manifest['maximum_scientific_child_invocations']==1 and manifest['child_timeout_seconds']==1200
    assert manifest['maximum_new_reference_trajectories']==4 and manifest['reused_reference_trajectories']==2
    assert manifest['peak_working_set_stop_bytes']==2*1024**3
    for item in manifest['inputs']:
        assert identity(REPO/item['path'])=={k:item[k] for k in ('bytes','sha256')}
    executable=Path(manifest['executable']['path'])
    assert identity(executable)=={k:manifest['executable'][k] for k in ('bytes','sha256')}
    output=ROOT/'result.json';code=ROOT/'reference.py'
    assert not output.exists() and not (ROOT/'execution.json').exists()
    assert not list(local.glob('*.npz')) and not list(local.glob('*-steps.jsonl'))
    assert ROOT.resolve()!=(ROOT.parent/'t56-coupled-reference').resolve()
    host=memory.host_memory()
    assert host['available_physical_bytes']>=manifest['minimum_available_host_bytes']
    command=[str(executable),'-I','-B','-u','-X','utf8',str(code)]
    record=dict(schema='t57-finer-short-execution-v1',started_utc=now(),command=command,cwd=str(REPO),
        child_timeout_seconds=1200,scientific_child_invocations=0,maximum_new_reference_trajectories=4,
        reused_reference_trajectories=2,peak_working_set_stop_bytes=2*1024**3,host_before_launch=host,
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
                # The process handle stays open: read the OS lifetime peak even if exit occurs between samples.
                try:
                    observation=memory.process_memory(handle)
                except OSError:
                    if child.poll() is None:raise
                    observation=None
                    record['final_memory_query_unavailable_after_exit']=True
                if observation is not None:
                    elapsed=time.perf_counter()-begin;peak=max(peak,observation['peak_working_set_bytes'])
                    memlog.write(json.dumps(dict(elapsed_seconds=elapsed,**observation))+'\n');memlog.flush();samples+=1
                elapsed=time.perf_counter()-begin
                if peak>2*1024**3:
                    record['status']='memory_stop_no_retry';break
                if elapsed>=1200:
                    record['status']='timeout_no_retry';break
                if child.poll() is not None:
                    record['status']='exited_pending_readback';break
                time.sleep(min(.25,1200-elapsed))
        except Exception as exc:
            record.update(status='observer_or_launch_error_no_retry',observer_or_launch_error=repr(exc))
        finally:
            if child is not None:
                if child.poll() is None:child.kill()
                record['returncode']=child.wait()
            else:record['returncode']=None
            if handle is not None:memory.kernel.CloseHandle(handle)
    record['child_supervised_seconds']=time.perf_counter()-begin
    record['observed_peak_working_set_bytes']=peak;record['memory_samples']=samples
    record['memory_is_observed_not_hard_allocation_limit']=True
    record['logs']=[dict(path='local/'+name,**identity(local/name)) for name in ('stdout.txt','stderr.txt','memory.jsonl')]
    record['frozen_inputs_unchanged']=all(identity(REPO/x['path'])=={k:x[k] for k in ('bytes','sha256')} for x in manifest['inputs'])
    record['executable_unchanged']=identity(executable)==record['executable_identity']
    record['result_json_exists']=output.exists();record['qualified_short_reference_only']=False
    record['completed_case_records']=[dict(path=p.relative_to(ROOT).as_posix(),**identity(p)) for p in sorted(local.glob('[STDQ][0-9]*.json'))]
    record['step_logs']=[dict(path=p.relative_to(ROOT).as_posix(),**identity(p)) for p in sorted(local.glob('*-steps.jsonl'))]
    record['raw_files']=[dict(path=p.relative_to(ROOT).as_posix(),**identity(p)) for p in sorted(local.glob('*.npz'))]
    record['completed_case_count']=len(record['completed_case_records'])
    if output.exists():
        record['result_identity']=identity(output)
        try:
            result=json.loads(output.read_bytes());record['result_status']=result['status']
            expected='qualified_short_reference_only' if all(result['checks'].values()) else 'failed_checks'
            assert result['schema']=='t57-finer-short-reference-v1' and result['code']==identity(code)
            assert result['python']==manifest['expected_python'] and result['numpy']==manifest['expected_numpy']
            assert result['status']==expected
            assert [c['name'] for c in result['cases']]==['S64','S128','S256','T128','D192','Q128']
            assert result['new_completed_trajectories']==4 and result['reused_trajectories']==2 and result['time_end']==.25
            assert result['candidate_trajectories']==0 and result['full_t1_task_pass'] is None
            assert result['prior_T56_status']=='failed_checks'
            assert record['returncode']==(0 if expected=='qualified_short_reference_only' else 2)
            assert record['completed_case_count']==4
            for case in result['cases']:
                old=case['name'] in ('S64','S128')
                assert result['case_origins'][case['name']]==('reused_T56' if old else 'new_T57')
                assert case['steps']==(200 if case['name']=='T128' else 100)
                assert case['elliptic_solves']==2*case['steps']+3 and case['transport_stages']==2*case['steps']
                base=ROOT.parent/'t56-coupled-reference'/'local' if old else local
                for key in ('raw','log'):
                    item=case[key];assert identity(base/item['path'])=={k:item[k] for k in ('bytes','sha256')}
            assert record['status']=='exited_pending_readback'
            assert 0<samples and peak<=2*1024**3 and record['child_supervised_seconds']<=1200
            record['status']='completed_'+expected;record['qualified_short_reference_only']=expected=='qualified_short_reference_only'
        except Exception as exc:
            record.update(result_read_error=repr(exc))
            if record['status']=='exited_pending_readback':record['status']='failed_result_validation_no_retry'
    elif record['status']=='exited_pending_readback':record['status']='failed_no_complete_result_no_retry'
    if not record['frozen_inputs_unchanged'] or not record['executable_unchanged']:
        record.update(status='failed_preservation_no_retry',qualified_short_reference_only=False)
    record['cumulative_T56_T57_supervised_seconds']=116.53663460002281+record['child_supervised_seconds']
    record['supervisor_elapsed_before_receipt_write_seconds']=time.perf_counter()-start;record['finished_utc']=now()
    with (ROOT/'execution.json').open('x',encoding='utf8',newline='\n') as stream:json.dump(record,stream,indent=2);stream.write('\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
