"""One T60 scientific child, complete costs and observed resource stops; no retry."""
import datetime
import hashlib
import importlib.util
import json
import math
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
    'q_squared_drift','axial_impulse_drift','full_box_vorticity_disagreements','full_box_spatial_reduction'}
TIMES=(0.,.25,.5,.75,1.)
COUNTS=dict(elliptic_attempts=5630,elliptic_completed=5630,transport_stages=5600,
            completed_steps=2800,snapshots=30,completed_cases=6,new_CG_solves=0)
QUALIFIED={'qualified_reference_ordinary_model_pass','qualified_reference_ordinary_model_fail'}

def identity(path):
    digest=hashlib.sha256();size=0
    with path.open('rb') as stream:
        while chunk:=stream.read(1024*1024):digest.update(chunk);size+=len(chunk)
    return dict(bytes=size,sha256=digest.hexdigest())

def strict_json(raw):
    def unique(pairs):
        result={}
        for key,value in pairs:
            assert key not in result, 'duplicate JSON key: '+key
            result[key]=value
        return result
    def finite(text):
        value=float(text);assert math.isfinite(value);return value
    def invalid(text):raise ValueError('invalid JSON numeric constant: '+text)
    value=json.loads(raw,object_pairs_hook=unique,parse_float=finite,parse_constant=invalid)
    assert isinstance(value,dict)
    return value

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def items(paths):return [dict(path=p.relative_to(ROOT).as_posix(),**identity(p)) for p in paths]

def main():
    start=time.perf_counter();local=ROOT/'local'
    manifest_path=ROOT/'input-manifest.json';manifest=strict_json(manifest_path.read_bytes())
    assert manifest['schema']=='t60-full-window-gaussian-freeze-v1'
    assert manifest['maximum_scientific_child_invocations']==1 and manifest['child_timeout_seconds']==600
    assert manifest['maximum_new_reference_trajectories']==6 and manifest['reused_reference_trajectories']==0
    assert manifest['peak_working_set_stop_bytes']==2*1024**3
    assert manifest['minimum_available_host_bytes']==3*1024**3
    assert manifest['expected_python']=='3.12.14' and manifest['expected_numpy']=='2.3.5'
    assert manifest['maximum_steps']==2800 and manifest['maximum_transport_stages']==5600
    assert manifest['maximum_direct_solves']==5630 and manifest['maximum_completed_checkpoints']==30
    assert manifest['time_end']==1 and manifest['case_names']==NAMES
    assert manifest['ordinary_model_trajectories_permitted']==1 and manifest['candidate_trajectories_permitted']==0
    for item in manifest['inputs']:
        assert identity(REPO/item['path'])=={k:item[k] for k in ('bytes','sha256')},item['path']
    executable=Path(manifest['executable']['path'])
    assert identity(executable)=={k:manifest['executable'][k] for k in ('bytes','sha256')}
    output=ROOT/'result.json';code=ROOT/'reference.py'
    assert not output.exists() and not (ROOT/'execution.json').exists()
    assert not list(local.glob('*.npz')) and not list(local.glob('*-steps.jsonl'))
    assert not (local/'checkpoints.jsonl').exists()
    assert not list(local.glob('*-snapshot-*.json'))
    assert not any((local/(n+'.json')).exists() for n in NAMES)
    assert not any((local/n).exists() for n in ('failure.json','reference-evaluation.json','ordinary-model-screen.json'))
    host=memory.host_memory()
    assert host['available_physical_bytes']>=manifest['minimum_available_host_bytes']
    command=[str(executable),'-I','-B','-u','-X','utf8',str(code)]
    record=dict(schema='t60-full-window-gaussian-execution-v1',started_utc=now(),command=command,cwd=str(REPO),
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
            child=subprocess.Popen(command,cwd=REPO,stdout=stdout,stderr=stderr,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
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
    record['input_manifest_unchanged']=identity(manifest_path)==record['input_manifest_identity']
    record['result_json_exists']=output.exists();record['complete_result_validated']=False
    record['reference_qualified_full_window']=False
    record['ordinary_model_verdict']='unqualified'
    record['full_t1_task_pass']=None
    record['qualified_model_outcome']=False
    record['case_metadata_files']=items([local/(n+'.json') for n in NAMES if (local/(n+'.json')).exists()])
    record['completed_case_records']=[];record['case_validation_errors']=[]
    for item in record['case_metadata_files']:
        try:
            raw=(ROOT/item['path']).read_bytes()
            assert dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())=={k:item[k] for k in ('bytes','sha256')}
            c=strict_json(raw)
            assert c['name'] in NAMES and Path(item['path']).name==c['name']+'.json'
            assert c['steps']==(800 if c['name']=='T128' else 400)
            assert c['elliptic_solves']==2*c['steps']+5 and c['transport_stages']==2*c['steps']
            assert c['method']=='ordinary_FFT_sine_Thomas'
            assert [x['time'] for x in c['snapshots']]==list(TIMES)
            assert [x['step'] for x in c['snapshots']]==[i*(200 if c['name']=='T128' else 100) for i in range(5)]
            assert len(c['checkpoint_records'])==5
            for key in ('raw','log'):
                saved=c[key];assert saved['path']==c['name']+('.npz' if key=='raw' else '-steps.jsonl')
                assert identity(local/saved['path'])=={k:saved[k] for k in ('bytes','sha256')}
            record['completed_case_records'].append(item)
        except Exception as exc:
            record['case_validation_errors'].append(dict(path=item['path'],error=repr(exc)))
    record['step_logs']=items(sorted(local.glob('*-steps.jsonl')))
    record['raw_files']=items(sorted(local.glob('*.npz')))
    record['checkpoint_metadata_files']=items(sorted(local.glob('*-snapshot-*.json')))
    record['checkpoint_ledger']=items([local/'checkpoints.jsonl']) if (local/'checkpoints.jsonl').exists() else []
    record['failure_records']=items([local/'failure.json']) if (local/'failure.json').exists() else []
    record['partial_evaluation_files']=items([local/n for n in ('reference-evaluation.json','ordinary-model-screen.json') if (local/n).exists()])
    record['validated_checkpoint_records']=[];record['checkpoint_validation_errors']=[]
    for item in record['checkpoint_metadata_files']:
        try:
            raw=(ROOT/item['path']).read_bytes()
            assert dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())=={k:item[k] for k in ('bytes','sha256')}
            c=strict_json(raw)
            assert c['name'] in NAMES and type(c['index']) is int and c['index'] in range(5)
            assert c['time']==TIMES[c['index']]
            assert c['step']==c['index']*(200 if c['name']=='T128' else 100)
            assert c['schema']=='t60-partial-snapshot-v1' and c['whole_task_qualified'] is False
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
            raw=output.read_bytes()
            assert dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())==record['result_identity']
            result=strict_json(raw);record['result_status']=result['status']
            assert result['schema']=='t60-full-window-gaussian-screen-v1' and result['code']==identity(code)
            assert result['python']==manifest['expected_python'] and result['numpy']==manifest['expected_numpy']
            assert Path(result['executable'])==executable
            checks=result['reference_checks']
            assert set(checks)==CHECKS and all(type(x) is bool for x in checks.values())
            reference_ok=all(checks.values())
            assert result['reference_qualified_full_window'] is reference_ok
            assert [c['name'] for c in result['cases']]==NAMES
            assert result['completed_trajectories']==result['new_completed_trajectories']==6
            assert result['reused_trajectories']==0 and result['time_end']==1.
            assert result['candidate_trajectories']==result['new_CG_solves']==0
            assert result['runtime_counts']==COUNTS and result['coefficient_refitted'] is False
            assert result['formal_error_certificate'] is False
            assert result['prior_T56_status']=='failed_checks' and result['prior_T57_status']=='timeout_no_retry'
            assert result['prior_T59_status']=='qualified_short_reference_only'
            assert result['prior_child_seconds']==manifest['prior_T56_T57_T58_T59_supervised_seconds']
            assert record['completed_case_count']==6 and record['validated_checkpoint_count']==30
            assert not record['checkpoint_validation_errors'] and not record['case_validation_errors']
            assert not record['failure_records'] and len(record['raw_files'])==36
            assert len(result['comparisons'])==25 and len(result['spatial_reductions'])==4
            assert len(result['checkpoint_records'])==30
            pairs=[('S64','S128'),('S128','S256'),('S128','T128'),('S128','D192'),('S128','Q128')]
            expected_comparison_keys=[(a,b,t) for a,b in pairs for t in TIMES]
            assert [(x['a'],x['b'],x['time']) for x in result['comparisons']]==expected_comparison_keys
            full=result['full_box_controls']
            assert [(x['a'],x['b'],x['time']) for x in full['comparisons']]==expected_comparison_keys
            assert len(full['spatial_reductions'])==4 and [x['time'] for x in full['outside_D8']]==list(TIMES)
            assert set(full['checks'])=={'full_box_vorticity_disagreements','full_box_spatial_reduction'}
            assert all(checks[k] is v for k,v in full['checks'].items())
            for key,relative in (('spatial_code','t55-axisymmetric-reference/reference.py'),
                                 ('base_code','t56-coupled-reference/reference.py'),
                                 ('solver_code','t58-separable-solver-qualification/solver.py'),
                                 ('measurement_code','t60-full-window-gaussian-screen/measurement.py')):
                assert result[key]==identity(ROOT.parent/relative),key
                assert result['source_identities_after'][key]==result[key]
            assert result['source_identities_after']['code']==result['code']
            assert result['source_identities_unchanged'] is True
            coefficient=identity(ROOT.parent/'t54-scalar-verification'/'result.json')
            assert result['coefficient_input']==result['coefficient_input_after']==coefficient
            checkpoint_records=[]
            for case in result['cases']:
                assert case['steps']==(800 if case['name']=='T128' else 400)
                assert case['elliptic_solves']==2*case['steps']+5 and case['transport_stages']==2*case['steps']
                assert case==strict_json((local/(case['name']+'.json')).read_bytes())
                assert case['method']=='ordinary_FFT_sine_Thomas'
                for key in ('raw','log'):
                    item=case[key]
                    assert item['path']==case['name']+('.npz' if key=='raw' else '-steps.jsonl')
                    assert identity(local/item['path'])=={k:item[k] for k in ('bytes','sha256')}
                for index,cp in enumerate(case['checkpoint_records']):
                    expected_name=case['name']+'-snapshot-'+str(index)
                    assert (cp['name'],cp['index'],cp['time'],cp['step'])==(case['name'],index,TIMES[index],index*(200 if case['name']=='T128' else 100))
                    assert cp['path']==expected_name+'.json' and cp['raw']['path']==expected_name+'.npz'
                    assert identity(local/cp['path'])=={k:cp[k] for k in ('bytes','sha256')}
                    assert identity(local/cp['raw']['path'])=={k:cp['raw'][k] for k in ('bytes','sha256')}
                    saved=strict_json((local/cp['path']).read_bytes())
                    assert saved['statistics']==case['snapshots'][index] and saved['raw']==cp['raw']
                    checkpoint_records.append(cp)
            assert result['checkpoint_records']==checkpoint_records
            ledger=result['checkpoint_index'];assert ledger['path']=='local/checkpoints.jsonl'
            assert identity(ROOT/ledger['path'])=={k:ledger[k] for k in ('bytes','sha256')}
            saved=result['reference_evidence'];assert saved['path']=='local/reference-evaluation.json'
            assert identity(ROOT/saved['path'])=={k:saved[k] for k in ('bytes','sha256')}
            evaluation=strict_json((ROOT/saved['path']).read_bytes())
            assert evaluation['schema']=='t60-reference-evaluation-v1'
            assert evaluation['reference_checks']==checks and evaluation['reference_qualified_full_window'] is reference_ok
            assert evaluation['comparisons']==result['comparisons'] and evaluation['full_box_controls']==full
            screen=result['ordinary_model_screen']
            if not reference_ok:
                expected='failed_reference_checks'
                assert screen is None and result['ordinary_model_evidence'] is None
                assert result['score_integration_qualified'] is None and result['meaningful_motion'] is None
                assert result['ordinary_model_trajectories']==0 and result['full_t1_task_pass'] is None
                assert result['ordinary_model_verdict']=='unqualified'
                assert not (local/'ordinary-model-screen.json').exists()
            else:
                assert isinstance(screen,dict) and result['ordinary_model_trajectories']==1
                assert [(x['reference'],x['index'],x['time']) for x in screen['scores']]==[(n,i,t) for n in ('S256','S128') for i,t in enumerate(TIMES)]
                for score in screen['scores']:
                    assert score['primary_8x6']['quadrature_orders']==[8,6]
                    assert score['confirmation_16x12']['quadrature_orders']==[16,12]
                    assert type(score['integration_passed']) is bool
                    assert score['integration_passed'] is (score['score_absolute_difference']<=1e-6)
                integration=all(x['integration_passed'] for x in screen['scores'])
                assert result['score_integration_qualified'] is integration
                assert screen['integration_qualified'] is integration and screen['score_integration_qualified'] is integration
                motion=screen['motion']['passed'];assert type(motion) is bool
                assert motion is (screen['motion']['axial_displacement']>=.25)
                assert result['meaningful_motion'] is motion and screen['meaningful_motion'] is motion
                modelchecks=screen['primary_model_checks']
                assert set(modelchecks)=={'vorticity_L2','axial_centroid','covariance'}
                assert all(type(x) is bool for x in modelchecks.values())
                modelpass=all(modelchecks.values());assert screen['model_pass'] is modelpass
                assert {k:screen['coefficient_identity'][k] for k in ('bytes','sha256')}==coefficient
                if not integration:expected='failed_score_integration'
                elif not motion:expected='insufficient_motion'
                else:expected='qualified_reference_ordinary_model_'+('pass' if modelpass else 'fail')
                if expected in QUALIFIED:
                    assert result['ordinary_model_verdict']==('pass' if modelpass else 'fail')
                    assert result['full_t1_task_pass'] is modelpass
                else:
                    assert result['ordinary_model_verdict']=='unqualified' and result['full_t1_task_pass'] is None
                saved=result['ordinary_model_evidence'];assert saved['path']=='local/ordinary-model-screen.json'
                assert identity(ROOT/saved['path'])=={k:saved[k] for k in ('bytes','sha256')}
                scorefile=strict_json((ROOT/saved['path']).read_bytes())
                assert scorefile['schema']=='t60-ordinary-screen-evidence-v1' and scorefile['ordinary_model_screen']==screen
                for key in ('status','ordinary_model_verdict','score_integration_qualified','meaningful_motion','full_t1_task_pass'):
                    assert scorefile[key]==result[key]
            assert result['status']==expected
            assert record['returncode']==(0 if expected in QUALIFIED else 2)
            assert record['status']=='exited_pending_readback'
            assert 0<samples and peak<=2*1024**3 and record['child_supervised_seconds']<=600
            record.update(status='completed_'+expected,complete_result_validated=True,
                reference_qualified_full_window=reference_ok,
                ordinary_model_verdict=result['ordinary_model_verdict'],full_t1_task_pass=result['full_t1_task_pass'],
                qualified_model_outcome=expected in QUALIFIED)
            record['reported_costs']={k:result[k] for k in ('direct_solver_phase_seconds','comparison_seconds',
                'full_box_comparison_seconds','ordinary_model_measurement_seconds','child_elapsed_before_result_write_seconds')}
        except Exception as exc:
            record['result_read_error']=repr(exc)
            if record['status']=='exited_pending_readback':record['status']='failed_result_validation_no_retry'
    elif record['status']=='exited_pending_readback':record['status']='failed_no_complete_result_no_retry'
    if not record['frozen_inputs_unchanged'] or not record['executable_unchanged'] or not record['input_manifest_unchanged']:
        record.update(status='failed_preservation_no_retry',complete_result_validated=False,
            reference_qualified_full_window=False,qualified_model_outcome=False,
            ordinary_model_verdict='unqualified',full_t1_task_pass=None)
    record['prior_T56_T57_T58_T59_supervised_seconds']=manifest['prior_T56_T57_T58_T59_supervised_seconds']
    record['cumulative_T56_T57_T58_T59_T60_supervised_seconds']=record['prior_T56_T57_T58_T59_supervised_seconds']+record['child_supervised_seconds']
    record['supervisor_elapsed_before_receipt_write_seconds']=time.perf_counter()-start;record['finished_utc']=now()
    with (ROOT/'execution.json').open('x',encoding='utf8',newline='\n') as stream:json.dump(record,stream,indent=2);stream.write('\n')
    print(json.dumps({k:record[k] for k in ('status','returncode','child_supervised_seconds','completed_case_count',
        'validated_checkpoint_count','observed_peak_working_set_bytes','complete_result_validated','ordinary_model_verdict')},indent=2))

if __name__=='__main__':main()
