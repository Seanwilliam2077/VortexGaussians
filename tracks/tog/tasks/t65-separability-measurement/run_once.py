"""One T65 scientific child with fixed OS memory/time observation; no NumPy."""
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
PRIOR=1978.636870399816
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

def validate_result(result,manifest,receipt,exe,manifest_path):
    def finite(value):
        if type(value) is float: assert math.isfinite(value)
        elif isinstance(value,dict):
            for x in value.values(): finite(x)
        elif isinstance(value,list):
            for x in value: finite(x)
    def close(a,b): assert math.isclose(a,b,rel_tol=3e-11,abs_tol=3e-14),(a,b)
    finite(result)
    assert result['input_identities_unchanged'] is True
    assert result['python']=='3.12.14' and result['numpy']=='2.3.5'
    assert Path(result['executable']).resolve()==exe.resolve()
    assert result['prior_scientific_child_seconds']==PRIOR
    assert result['prior_evidence_qualification_seconds']==.9663960000034422
    assert set(result['checks'])=={'frozen_inputs_before','reference_readback','gram_checks','matrix_norms',
        'svd_checks','construction_agreement','fixed_work_accounting','frozen_inputs_after'}
    assert all(type(v) is bool and v for v in result['checks'].values())
    assert result['formal_exclusion'] is False
    assert all(type(result[k]) is int and result[k]==0 for k in ('new_flow_trajectories','gaussian_field_evaluations','gaussian_fits'))
    c=result['counters']
    expected=dict(array_files_decoded=2,arrays_loaded=12,rules_constructed=2,rule_nodes=5,
        reference_integrals=2,reference_node_cell_points=983040,Y_entries_written=983040,corner_cell_points=655360,
        analytic_gram_blocks=1152,quadrature_gram_blocks=1152,cholesky_blocks=1152,cholesky_reconstruction_blocks=1152,
        gram_axis_node_evaluations=2688,basis_matrices=2,weighted_matrices=2,quadrature_matrices=2,
        svd_started=4,svd_completed=4,residual_products=4,orthogonality_products=8,audit_bundles=2,
        gaussian_field_evaluations=0,gaussian_fits=0,new_flow_trajectories=0)
    assert all(type(c[k]) is int and c[k]==v for k,v in expected.items())
    assert set(result['cases'])=={'S256','S128'}
    byte_count=file_count=0; estimates={}; positions={}
    for name,n in (('S256',256),('S128',128)):
        case=result['cases'][name]; reference=case['reference']
        C=reference['vorticity_squared_integral']; saved=reference['saved_vorticity_squared_integral']
        assert C>0 and saved>0; close(C,saved)
        meta=json.loads((ROOT.parent/'t60-full-window-gaussian-screen/local'/f'{name}-snapshot-4.json').read_bytes())
        for key in ('circulation','q_squared_integral','axial_impulse','vorticity_squared_integral'):
            close(reference[key],meta['statistics'][key])
        for a,b in zip(reference['centroid'],meta['statistics']['centroid']):close(a,b)
        for row_a,row_b in zip(reference['covariance'],meta['statistics']['covariance']):
            for a,b in zip(row_a,row_b):close(a,b)
        assert len(reference['centroid'])==2 and len(reference['covariance'])==2
        assert all(len(row)==2 for row in reference['covariance'])
        assert reference['minimum_corner']>=0 and reference['minimum_node']>=0
        assert set(case['gram_checks'])=={'radial','axial'}
        for axis,count in (('radial',n),('axial',2*n)):
            gram=case['gram_checks'][axis]
            assert gram['blocks']==count and gram['minimum_leading_diagonal']>0 and gram['minimum_second_pivot']>0
            assert 0<=gram['maximum_cholesky_relative']<=1e-12 and 0<=gram['maximum_quadrature_relative']<=1e-12
        estimates[name]={};positions[name]={}
        for kind,m in (('F',2*n),('Y',3*n)):
            rec=case[kind];s=rec['singular_values']
            assert rec['shape']==[m,4*n] and len(s)==m
            assert all(v>=0 for v in s) and all(a>=b for a,b in zip(s,s[1:]))
            energy=math.fsum(x*x for x in s);tail=math.fsum(x*x for x in s[1:])
            assert energy>0 and rec['norm_squared']>0
            close(energy,rec['spectral_energy']);close(tail,rec['tail_energy'])
            close(rec['relative_error'],math.sqrt(tail/energy));assert 0<=rec['relative_error']<=1
            close(rec['matrix_norm_relative_difference'],abs(rec['norm_squared']/C-1.))
            close(rec['spectral_norm_relative_difference'],abs(energy/C-1.))
            assert 0<=rec['matrix_norm_relative_difference']<=1e-10
            assert 0<=rec['spectral_norm_relative_difference']<=1e-10
            assert 0<=rec['residual_relative']<=1e-10
            close(rec['residual_relative'],rec['residual_absolute']/math.sqrt(rec['norm_squared']))
            assert rec['residual_absolute']>=0 and 0<=rec['orthogonality_U']<=1e-10 and 0<=rec['orthogonality_Vh']<=1e-10
            assert rec['largest_singular_value']==s[0] and rec['operator_upper_is_certified'] is False
            close(rec['computed_operator_upper'],s[0]*math.sqrt(1+rec['orthogonality_U'])*math.sqrt(1+rec['orthogonality_Vh'])+rec['residual_absolute'])
            estimates[name][kind]=rec['relative_error']
            e=rec['relative_error'];positions[name][kind]='above' if e-.10>1e-8 else 'below' if .10-e>1e-8 else 'near'
        sf=case['F']['singular_values']+[0.]*n;sy=case['Y']['singular_values']
        close(case['spectrum_difference_relative'],math.sqrt(math.fsum((a-b)**2 for a,b in zip(sf,sy)))/math.sqrt(saved))
        close(case['extra_spectrum_relative'],math.sqrt(math.fsum(x*x for x in sy[-n:]))/math.sqrt(saved))
        close(case['error_difference'],abs(estimates[name]['F']-estimates[name]['Y']))
        assert all(0<=case[k]<=1e-10 for k in ('spectrum_difference_relative','extra_spectrum_relative','error_difference'))
        bundle=case['audit_bundle'];assert bundle['path']==f'local/{name}-audit.npz'
        assert identity(ROOT/bundle['path'])=={k:bundle[k] for k in ('bytes','sha256')}
        shapes=dict(F=[2*n,4*n],Y=[3*n,4*n],U_F=[2*n,2*n],s_F=[2*n],Vh_F=[2*n,4*n],
            U_Y=[3*n,3*n],s_Y=[3*n],Vh_Y=[3*n,4*n],C=[n,2,2*n,2],Gr=[n,2,2],Gz=[2*n,2,2],
            Lr=[n,2,2],Lz=[2*n,2,2],r=[n],rc=[n],z=[2*n])
        assert set(bundle['arrays'])==set(shapes)
        for key,shape in shapes.items():
            assert bundle['arrays'][key]==dict(shape=shape,dtype='float64',bytes=8*math.prod(shape))
        assert bundle['array_bytes']==sum(x['bytes'] for x in bundle['arrays'].values())
        byte_count+=bundle['array_bytes'];file_count+=bundle['bytes']
    assert c['audit_array_bytes']==byte_count and c['audit_file_bytes']==c['output_bytes_hashed']==file_count
    a=result['classification'];primary=estimates['S256']['F'];sensitivity=estimates['S128']['F']
    difference=abs(primary-sensitivity);agreement=difference<=.001
    above=all(e-.1>1e-8 for pair in estimates.values() for e in pair.values())
    assert a==dict(primary_error=primary,sensitivity_error=sensitivity,absolute_difference=difference,
        sensitivity_agreement=agreement,all_estimates_above_gate=above,gate=.10,separation_buffer=1e-8,
        sensitivity_tolerance=.001,estimates=estimates,positions=positions)
    assert result['status']==('qualified_numerical_barrier_evidence' if above and agreement else 'qualified_no_separability_exclusion')
    admitted={(REPO/x['path']).resolve():{k:x[k] for k in ('bytes','sha256')} for x in manifest['inputs']}
    admitted[exe.resolve()]=receipt['executable_identity'];admitted[manifest_path.resolve()]=receipt['input_manifest_identity']
    actual={(REPO/x['path']).resolve():{k:x[k] for k in ('bytes','sha256')} for x in result['input_identities']}
    assert len(actual)==len(result['input_identities']) and actual==admitted
    assert c['input_bytes_hashed_before']==c['input_bytes_hashed_after']==sum(x['bytes'] for x in admitted.values())
    assert 0<=result['child_elapsed_before_result_write_seconds']<=receipt['scientific_child_supervised_seconds']

def main():
    start=time.perf_counter()
    local=ROOT/'local'
    manifest_path=ROOT/'input-manifest.json'
    manifest=json.loads(manifest_path.read_bytes())
    assert manifest['schema']=='t65-separability-freeze-v1'
    assert manifest['maximum_scientific_child_invocations']==1
    assert manifest['child_timeout_seconds']==LIMIT and manifest['observed_peak_working_set_limit_bytes']==CAP
    assert manifest['required_available_physical_bytes']==REQUIRED
    assert manifest['expected_svd_calls']==4
    assert manifest['prior_scientific_child_seconds']==PRIOR
    assert all(identity(REPO/x['path'])=={k:x[k] for k in ('bytes','sha256')} for x in manifest['inputs'])
    exe=Path(manifest['executable']['path'])
    assert identity(exe)=={k:manifest['executable'][k] for k in ('bytes','sha256')}
    assert not (ROOT/'result.json').exists() and not (ROOT/'execution.json').exists()
    assert not (local/'execution-started.json').exists()
    preflight=json.loads((ROOT/'preflight.json').read_bytes())
    assert preflight['schema']=='t65-os-preflight-v1' and preflight['passed'] is True
    assert preflight['source']==identity(MEMORY_SOURCE)
    spec=importlib.util.spec_from_file_location('t65_memory',MEMORY_SOURCE)
    memory=importlib.util.module_from_spec(spec);spec.loader.exec_module(memory)
    command=[str(exe),'-I','-B','-u','-X','utf8',str(ROOT/'measure.py')]
    env=dict(os.environ)
    limits={key:'1' for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
    env.update(limits)
    receipt=dict(schema='t65-separability-measurement-execution-v1',started_utc=now(),command=command,cwd=str(REPO),
        child_timeout_seconds=LIMIT,observed_peak_working_set_limit_bytes=CAP,
        required_available_physical_bytes=REQUIRED,memory_sample_interval_seconds=INTERVAL,
        thread_environment_overrides=limits,scientific_child_invocations=0,new_scientific_trajectories=0,
        complete_result_validated=False,separability_verdict='unqualified',formal_exclusion=False,
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
        if p.is_file() and p.name in ('work.jsonl','failure.json','phases.jsonl','partial.json','S256-audit.npz','S128-audit.npz')]
    receipt['result_exists']=(ROOT/'result.json').exists()
    if receipt['result_exists']:
        receipt['result_identity']=identity(ROOT/'result.json')
        try:
            result=json.loads((ROOT/'result.json').read_bytes())
            assert result['schema']=='t65-separability-measurement-v1'
            assert result['status'] in ('qualified_numerical_barrier_evidence','qualified_no_separability_exclusion','qualification_failure')
            assert result['formal_exclusion'] is False
            if receipt['status']=='exited_pending_readback':
                if result['status']=='qualification_failure':
                    assert receipt['returncode']==2
                    receipt['status']='qualification_failure_no_retry'
                else:
                    assert receipt['returncode']==0
                    assert receipt['scientific_child_supervised_seconds']<=LIMIT
                    assert receipt['memory_samples']>0 and receipt['peak_observed_working_set_bytes']<=CAP
                    assert receipt['inputs_unchanged'] and receipt['input_manifest_unchanged'] and receipt['executable_unchanged']
                    validate_result(result,manifest,receipt,exe,manifest_path)
                    receipt.update(status='completed_'+result['status'],complete_result_validated=True,
                        separability_verdict=result['status'],formal_exclusion=False)
        except Exception as exc:
            receipt['result_read_error']=repr(exc)
            if receipt['status']=='exited_pending_readback':receipt['status']='failed_result_validation_no_retry'
    elif receipt['status']=='exited_pending_readback':
        receipt['status']='missing_result_no_retry'
    if not all(receipt[k] for k in ('inputs_unchanged','input_manifest_unchanged','executable_unchanged')):
        receipt.update(status='failed_preservation_no_retry',complete_result_validated=False,separability_verdict='unqualified',formal_exclusion=False)
    receipt['supervisor_elapsed_before_receipt_write_seconds']=time.perf_counter()-start
    receipt['finished_utc']=now()
    write(ROOT/'execution.json',receipt)
    print(json.dumps({k:receipt[k] for k in ('status','scientific_child_invocations','scientific_child_supervised_seconds',
        'separability_verdict','peak_observed_working_set_bytes','inputs_unchanged')},indent=2))

if __name__=='__main__':main()
