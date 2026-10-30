"""One T63 scientific child with fixed OS memory/time observation; no NumPy."""
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
MEMORY_SOURCE=ROOT.parent/'t57-finer-short-reference/memory.py'
PRIOR=1976.6796338998247
CAP=512*1024*1024
REQUIRED=1024*1024*1024
LIMIT=120.
INTERVAL=.25

def identity(path):
    h=hashlib.sha256();size=0
    with path.open('rb') as stream:
        while block:=stream.read(1024*1024):h.update(block);size+=len(block)
    return dict(bytes=size,sha256=h.hexdigest())

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    start=time.perf_counter()
    local=ROOT/'local'
    manifest_path=ROOT/'input-manifest.json'
    manifest=json.loads(manifest_path.read_bytes())
    assert manifest['schema']=='t63-endpoint-capacity-freeze-v1'
    assert manifest['maximum_scientific_child_invocations']==1
    assert manifest['child_timeout_seconds']==LIMIT and manifest['observed_peak_working_set_limit_bytes']==CAP
    assert manifest['required_available_physical_bytes']==REQUIRED
    assert manifest['maximum_primary_geometry_evaluations']==606
    assert manifest['prior_scientific_child_seconds']==PRIOR
    assert all(identity(REPO/x['path'])=={k:x[k] for k in ('bytes','sha256')} for x in manifest['inputs'])
    exe=Path(manifest['executable']['path'])
    assert identity(exe)=={k:manifest['executable'][k] for k in ('bytes','sha256')}
    assert not (ROOT/'result.json').exists() and not (ROOT/'execution.json').exists()
    assert not (local/'execution-started.json').exists()
    preflight=json.loads((ROOT/'preflight.json').read_bytes())
    assert preflight['schema']=='t63-os-preflight-v1' and preflight['passed'] is True
    assert preflight['source']==identity(MEMORY_SOURCE)
    spec=importlib.util.spec_from_file_location('t63_memory',MEMORY_SOURCE)
    memory=importlib.util.module_from_spec(spec);spec.loader.exec_module(memory)
    command=[str(exe),'-I','-B','-u','-X','utf8',str(ROOT/'measure.py')]
    env=dict(os.environ)
    limits={key:'1' for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
    env.update(limits)
    receipt=dict(schema='t63-endpoint-capacity-execution-v1',started_utc=now(),command=command,cwd=str(REPO),
        child_timeout_seconds=LIMIT,observed_peak_working_set_limit_bytes=CAP,
        required_available_physical_bytes=REQUIRED,memory_sample_interval_seconds=INTERVAL,
        thread_environment_overrides=limits,scientific_child_invocations=0,new_scientific_trajectories=0,
        complete_result_validated=False,capacity_verdict='unqualified',capacity_witness=None,
        prior_scientific_child_seconds=PRIOR,T61_qualification_seconds=.9663960000034422,
        T60_history_reclassified=False,input_manifest_identity=identity(manifest_path),
        supervisor_identity=identity(Path(__file__)),worker_identity=identity(ROOT/'measure.py'),
        memory_observer_identity=identity(MEMORY_SOURCE),executable_identity=identity(exe),
        memory_samples=0,peak_observed_working_set_bytes=0,max_observed_private_bytes=0,
        max_observed_peak_pagefile_bytes=0)
    receipt['launch_memory']=memory.host_memory()
    write(local/'execution-started.json',receipt)
    child=None;handle=None;begin=None
    with (local/'stdout.txt').open('xb') as stdout,(local/'stderr.txt').open('xb') as stderr, (local/'memory.jsonl').open('x',encoding='utf-8',newline='\n') as observations:
        def sample(final=False):
            values=memory.process_memory(handle)
            elapsed=time.perf_counter()-begin
            record=dict(elapsed_seconds=elapsed,final=final,**values)
            observations.write(json.dumps(record,allow_nan=False)+'\n');observations.flush()
            receipt['memory_samples']+=1
            receipt['peak_observed_working_set_bytes']=max(receipt['peak_observed_working_set_bytes'],values['peak_working_set_bytes'])
            receipt['max_observed_private_bytes']=max(receipt['max_observed_private_bytes'],values['private_usage_bytes'])
            receipt['max_observed_peak_pagefile_bytes']=max(receipt['max_observed_peak_pagefile_bytes'],values['peak_pagefile_usage_bytes'])
            receipt['last_memory_sample_elapsed_seconds']=elapsed
            return values['peak_working_set_bytes']<=CAP
        if receipt['launch_memory']['available_physical_bytes']<REQUIRED:
            receipt['status']='insufficient_launch_memory_no_invocation'
        else:
            begin=time.perf_counter();receipt['scientific_child_invocations']=1
            try:
                child=subprocess.Popen(command,cwd=REPO,env=env,stdout=stdout,stderr=stderr,
                    creationflags=subprocess.CREATE_NO_WINDOW)
                receipt['child_pid']=child.pid
                handle=memory.open_process(child.pid)
                while True:
                    code=child.poll()
                    if code is not None:
                        receipt.update(returncode=code,status='exited_pending_readback')
                        try:
                            if not sample(final=True):receipt['status']='memory_limit_no_retry'
                        except Exception as exc:
                            receipt['final_memory_query_unavailable']=repr(exc)
                        break
                    if time.perf_counter()-begin>=LIMIT:
                        receipt['status']='timeout_no_retry';break
                    try:
                        if not sample():receipt['status']='memory_limit_no_retry';break
                    except Exception as exc:
                        if child.poll() is not None:
                            receipt.update(returncode=child.returncode,status='exited_pending_readback',final_memory_query_unavailable=repr(exc))
                        else:
                            receipt.update(status='live_memory_observer_error_no_retry',observer_error=repr(exc))
                        break
                    try:
                        child.wait(timeout=min(INTERVAL,max(.001,LIMIT-(time.perf_counter()-begin))))
                    except subprocess.TimeoutExpired:
                        pass
            except Exception as exc:
                receipt.update(status='launch_or_observer_setup_error_no_retry',error=repr(exc))
            finally:
                if child is not None:
                    if child.poll() is None:child.kill()
                    receipt['returncode']=child.wait()
                if handle is not None:memory.kernel.CloseHandle(handle)
    receipt['scientific_child_supervised_seconds']=time.perf_counter()-begin if begin is not None else 0.
    receipt['cumulative_scientific_child_seconds']=PRIOR+receipt['scientific_child_supervised_seconds']
    receipt['inputs_unchanged']=all(identity(REPO/x['path'])=={k:x[k] for k in ('bytes','sha256')} for x in manifest['inputs'])
    receipt['input_manifest_unchanged']=identity(manifest_path)==receipt['input_manifest_identity']
    receipt['executable_unchanged']=identity(exe)==receipt['executable_identity']
    receipt['logs']=[dict(path='local/'+name,**identity(local/name)) for name in ('stdout.txt','stderr.txt','memory.jsonl')]
    receipt['partial_artifacts']=[dict(path=p.relative_to(ROOT).as_posix(),**identity(p)) for p in sorted(local.iterdir())
        if p.is_file() and p.name in ('search.jsonl','failure.json','phases.jsonl','partial.json')]
    receipt['result_exists']=(ROOT/'result.json').exists()
    if receipt['result_exists']:
        receipt['result_identity']=identity(ROOT/'result.json')
        try:
            result=json.loads((ROOT/'result.json').read_bytes())
            assert result['schema']=='t63-endpoint-capacity-v1'
            assert result['status'] in ('qualified_endpoint_witness','search_inconclusive','qualification_failure')
            if receipt['status']=='exited_pending_readback':
                if result['status']=='qualification_failure':
                    assert receipt['returncode']==2 and result['capacity_witness'] is None
                    receipt['status']='qualification_failure_no_retry'
                else:
                    assert receipt['returncode']==0
                    assert receipt['scientific_child_supervised_seconds']<=LIMIT
                    assert receipt['memory_samples']>0 and receipt['peak_observed_working_set_bytes']<=CAP
                    assert receipt['inputs_unchanged'] and receipt['input_manifest_unchanged'] and receipt['executable_unchanged']
                    assert result['input_identities_unchanged'] is True
                    assert result['python']=='3.12.14' and result['numpy']=='2.3.5'
                    assert result['capacity_witness'] is (result['status']=='qualified_endpoint_witness')
                    assert result['prior_scientific_child_seconds']==PRIOR
                    assert set(result['checks'])=={'frozen_inputs_before','reference_readback','calibration',
                        'selected_score_qualification','fixed_work_accounting','frozen_inputs_after'}
                    assert all(type(v) is bool and v for v in result['checks'].values())
                    assert result['prior_evidence_qualification_seconds']==.9663960000034422
                    assert result['new_flow_trajectories']==0 and result['offline_oracle'] is True
                    assert result['sensitivity_parameters_identical'] is True and result['coefficient_refitted'] is False
                    counters=result['counters']; geometries=counters['geometry_evaluations']
                    assert type(geometries) is int and 1<=geometries<=606
                    fixed=dict(array_files_decoded=2,arrays_loaded=12,rules_constructed=6,rule_nodes=47,
                        polynomial_integrals=2,polynomial_node_cell_points=983040,corner_cell_points=655360,
                        calibration_contractions=2,direct_integrals_started=8,direct_integrals_completed=8,
                        direct_node_cell_points=78643200,direct_reference_reconstruction_points=78643200,
                        direct_gaussian_field_points=78643200,contraction_calls=geometries+2,
                        contraction_axis_exponent_evaluations=5120*geometries+7680,
                        contraction_coefficient_cell_visits=393216*geometries+491520)
                    for key,value in fixed.items():
                        assert type(counters[key]) is int and counters[key]==value,key
                    summary=result['search_summary']
                    assert summary['evaluated']==geometries and summary['rejected']==counters['rejected_coordinates']
                    assert counters['search_attempts']==geometries+counters['rejected_coordinates']
                    if summary['route']=='moment_center_shortcut':
                        assert geometries==1 and summary['local_starts']==summary['cycles']==[]
                        assert result['selected']['coordinates']==[0.,0.,0.]
                    else:
                        assert summary['route']=='fixed_grid_pattern' and len(summary['local_starts'])==3
                        assert len(summary['cycles'])<=90
                    assert set(result['selected']['parameters'])=={'A','sr','sz','z0'}
                    assert all(math.isfinite(x) for x in result['selected']['parameters'].values())
                    assert all(result['selected']['parameters'][x]>0 for x in ('A','sr','sz'))
                    assert set(result['selected_scores'])==set(result['calibration'])=={'S256','S128'}
                    for name,points in (('S256',131072),('S128',32768)):
                        for group in ('calibration','selected_scores'):
                            pair=result[group][name]
                            for key,orders in (('primary_8x6',[8,6]),('confirmation_16x12',[16,12])):
                                score=pair[key]
                                assert score['reference']==name and score['orders']==orders
                                assert score['node_cell_points']==points*orders[0]*orders[1]
                                assert score['numerator']>=0 and score['denominator']>0
                                assert math.isclose(score['relative_error'],math.sqrt(score['numerator']/score['denominator']),rel_tol=3e-11,abs_tol=3e-14)
                            assert pair['rule_difference']==abs(pair['primary_8x6']['relative_error']-pair['confirmation_16x12']['relative_error'])<=1e-6
                        selected=result['selected_scores'][name];moments=selected['moments']
                        expected_gates=dict(vorticity_L2=selected['primary_8x6']['relative_error']<=.10,
                            axial_centroid=moments['axial_centroid_absolute']<=.1,covariance=moments['covariance_relative']<=.1)
                        assert selected['physical_gates']==expected_gates
                        assert selected['joint_pass'] is all(expected_gates.values())
                    assert result['capacity_witness'] is result['selected_scores']['S256']['joint_pass']
                    assert result['selected_contraction_direct_difference']==abs(result['selected']['contraction']['relative_error']-
                        result['selected_scores']['S256']['primary_8x6']['relative_error'])<=1e-9
                    admitted={(REPO/x['path']).resolve():{k:x[k] for k in ('bytes','sha256')} for x in manifest['inputs']}
                    admitted[exe.resolve()]=receipt['executable_identity']
                    admitted[manifest_path.resolve()]=receipt['input_manifest_identity']
                    actual={(REPO/x['path']).resolve():{k:x[k] for k in ('bytes','sha256')} for x in result['input_identities']}
                    assert len(actual)==len(result['input_identities']) and actual==admitted
                    assert 0<=result['child_elapsed_before_result_write_seconds']<=receipt['scientific_child_supervised_seconds']
                    receipt.update(status='completed_'+result['status'],complete_result_validated=True,
                        capacity_verdict='endpoint_witness' if result['capacity_witness'] else 'search_inconclusive',
                        capacity_witness=result['capacity_witness'])
        except Exception as exc:
            receipt['result_read_error']=repr(exc)
            if receipt['status']=='exited_pending_readback':receipt['status']='failed_result_validation_no_retry'
    elif receipt['status']=='exited_pending_readback':
        receipt['status']='missing_result_no_retry'
    if not all(receipt[k] for k in ('inputs_unchanged','input_manifest_unchanged','executable_unchanged')):
        receipt.update(status='failed_preservation_no_retry',complete_result_validated=False,capacity_verdict='unqualified',capacity_witness=None)
    receipt['supervisor_elapsed_before_receipt_write_seconds']=time.perf_counter()-start
    receipt['finished_utc']=now()
    write(ROOT/'execution.json',receipt)
    print(json.dumps({k:receipt[k] for k in ('status','scientific_child_invocations','scientific_child_supervised_seconds',
        'capacity_verdict','peak_observed_working_set_bytes','inputs_unchanged')},indent=2))

if __name__=='__main__':main()
