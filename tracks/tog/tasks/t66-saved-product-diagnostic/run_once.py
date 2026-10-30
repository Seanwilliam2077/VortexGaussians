"""One T66 scientific child with fixed OS memory/time observation; no NumPy."""
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
PRIOR=1979.5974398998078
CAP=512*1024*1024
REQUIRED=1024*1024*1024
LIMIT=60.
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

QUALIFIED_STATUSES = {
    'broader_separable_endpoint_witness': 'broader_separable_endpoint_witness',
    'qualified_candidate_miss': 'candidate_miss',
    'qualified_reference_sensitive_inconclusive': 'reference_sensitive_inconclusive',
}
EXPECTED_COUNTS = dict(input_npz_files=3,input_arrays=19,triangular_blocks=768,
    polynomial_cell_moment_evaluations=3328,polynomial_factor_integrals=9,
    factor_endpoint_checks=1536,factor_jump_checks=766,boundary_product_checks=3,
    reference_corner_cell_points=655360,candidate_node_cell_points=786432,
    reference_node_cell_points=1572864,rules_constructed=2,rule_nodes=5,
    reference_integrals=2,candidate_quadrature_integrals=1,output_bundles=1,
    svd_calls=0,eigensolver_calls=0,gaussian_field_evaluations=0,gaussian_fits=0,new_flow_trajectories=0)
CHECK_KEYS = {'frozen_inputs_before','input_shapes_coordinates','triangular_recovery',
    'reference_readback','polynomial_quadrature_agreement','saved_field_score_agreement',
    'fixed_work_accounting','frozen_inputs_after'}


def validate_result(result,manifest,receipt,exe,manifest_path):
    # Scalar/identity readback only: no numerical modules or array decoding.
    def finite(value):
        if type(value) is float: assert math.isfinite(value)
        elif isinstance(value,dict):
            for x in value.values(): finite(x)
        elif isinstance(value,list):
            for x in value: finite(x)
    def number(value):
        assert type(value) in (int,float) and math.isfinite(value)
        return value
    def close(a,b):
        assert math.isclose(number(a),number(b),rel_tol=3e-11,abs_tol=3e-14),(a,b)
    def same(a,b):
        if a is None or b is None: assert a is None and b is None
        elif isinstance(a,list) or isinstance(b,list):
            assert isinstance(a,list) and isinstance(b,list) and len(a)==len(b)
            for x,y in zip(a,b): same(x,y)
        else: close(a,b)
    def stats(x):
        raw=x['raw_moments']; assert isinstance(raw,list) and len(raw)==9
        for v in raw: number(v)
        assert x['circulation']==raw[0] and x['positive_circulation'] is (raw[0]>0.)
        assert x['q_squared_integral']==raw[6] and x['axial_impulse']==raw[7]
        assert x['vorticity_squared_integral']==raw[8] and raw[6]>=0. and raw[8]>=0.
        assert (x['centroid'] is None)==(x['covariance'] is None)
        if x['centroid'] is None:
            assert x['undefined_reason'] in {'zero_circulation','nonfinite_normalized_moments','nonfinite_separable_ratios'}
            if raw[0]==0.: assert x['undefined_reason']=='zero_circulation'
        else:
            assert x['undefined_reason'] is None and raw[0]!=0.
            assert len(x['centroid'])==2 and len(x['covariance'])==2
            assert all(len(row)==2 for row in x['covariance'])
            mean=[raw[1]/raw[0],raw[2]/raw[0]]
            cov=[[raw[3]/raw[0]-mean[0]*mean[0],raw[4]/raw[0]-mean[0]*mean[1]],
                 [raw[4]/raw[0]-mean[0]*mean[1],raw[5]/raw[0]-mean[1]*mean[1]]]
            same(x['centroid'],mean);same(x['covariance'],cov)
    def compare_stats(a,b):
        for key in ('circulation','q_squared_integral','axial_impulse','vorticity_squared_integral','centroid','covariance'):
            same(a[key],b[key])
    def layout(item,shapes):
        assert set(item)==set(shapes)
        for key,shape in shapes.items():
            assert item[key]==dict(shape=shape,dtype='float64',bytes=8*math.prod(shape))

    finite(result)
    assert result['schema']=='t66-saved-product-diagnostic-v1'
    assert result['status'] in QUALIFIED_STATUSES
    assert result['numerical_qualified'] is True and result['input_identities_unchanged'] is True
    assert result['python']==manifest['expected_python']=='3.12.14'
    assert result['numpy']==manifest['expected_numpy']=='2.3.5'
    assert Path(result['executable']).resolve()==exe.resolve()
    assert result['prior_scientific_child_seconds']==PRIOR
    assert result['prior_evidence_qualification_seconds']==.9663960000034422
    assert set(result['checks'])==CHECK_KEYS and all(type(v) is bool and v for v in result['checks'].values())
    assert result['formal_exclusion'] is result['gaussian_witness'] is result['causal_dynamics_claim'] is False
    assert type(result['new_flow_trajectories']) is int and result['new_flow_trajectories']==0
    c=result['counters']
    dynamic={'input_bytes_hashed_before','input_bytes_hashed_after','output_bytes_hashed','output_array_bytes','output_file_bytes'}
    assert set(c)==set(EXPECTED_COUNTS)|dynamic
    assert all(type(c[k]) is int and c[k]==v for k,v in EXPECTED_COUNTS.items())
    assert all(type(c[k]) is int and c[k]>=0 for k in dynamic)
    admitted={(REPO/x['path']).resolve():{k:x[k] for k in ('bytes','sha256')} for x in manifest['inputs']}
    admitted[exe.resolve()]=receipt['executable_identity'];admitted[manifest_path.resolve()]=receipt['input_manifest_identity']
    actual={(REPO/x['path']).resolve():{k:x[k] for k in ('bytes','sha256')} for x in result['input_identities']}
    assert len(actual)==len(result['input_identities']) and actual==admitted
    assert c['input_bytes_hashed_before']==c['input_bytes_hashed_after']==sum(x['bytes'] for x in admitted.values())
    def read_frozen(path):
        assert path.resolve() in admitted
        return json.loads(path.read_bytes())

    saved=read_frozen(ROOT.parent/'t65-separability-measurement/result.json')
    t63=read_frozen(ROOT.parent/'t63-endpoint-capacity/result.json')
    assert saved['status']=='qualified_no_separability_exclusion' and saved['input_identities_unchanged'] is True
    assert t63['status']=='search_inconclusive' and t63['input_identities_unchanged'] is True
    D0=t63['region']['D0']; assert D0==1.0882203729522952
    records=result['input_arrays']; assert len(records)==3
    byrole={x['role']:x for x in records}; assert set(byrole)=={'S256','S128','S256_saved_factors'}
    assert len(byrole)==len(records)
    for name,n in (('S256',256),('S128',128)):
        item=byrole[name]
        target=ROOT.parent/'t60-full-window-gaussian-screen/local'/f'{name}-snapshot-4.npz'
        assert item['path']==target.relative_to(REPO).as_posix()
        assert {k:item[k] for k in ('bytes','sha256')}==admitted[target.resolve()]
        shapes={k:[n,2*n] for k in ('q','qr','qz')};shapes.update(r=[n],rc=[n],z=[2*n])
        layout(item['arrays'],shapes)
    item=byrole['S256_saved_factors']; target=ROOT.parent/'t65-separability-measurement/local/S256-audit.npz'
    assert item['path']==target.relative_to(REPO).as_posix()
    assert {k:item[k] for k in ('bytes','sha256')}==admitted[target.resolve()]
    layout(item['arrays'],dict(U_F=[512,512],s_F=[512],Vh_F=[512,1024],Lr=[256,2,2],Lz=[512,2,2],r=[256],z=[512]))
    assert sum(len(x['arrays']) for x in records)==19
    recovery=result['recovery'];assert set(recovery)=={'leading_singular_value','radial','axial'}
    assert recovery['leading_singular_value']==saved['cases']['S256']['F']['singular_values'][0]>0.
    for axis,n in (('radial',256),('axial',512)):
        q=recovery[axis]; assert q['blocks']==n and number(q['target_frobenius'])>0.
        assert 0.<=number(q['relative_residual'])<=1e-10
    orientation=result['orientation'];before=number(orientation['radial_integral_before'])
    assert before!=0. and orientation['common_sign_flipped'] is (before<0.)

    diagnostics=result['factor_diagnostics']
    for axis,n in (('radial',256),('axial',512)):
        q=diagnostics[axis];minimum=number(q['minimum_endpoint']);maximum=number(q['maximum_endpoint'])
        assert minimum<=maximum and q['nonnegative'] is (minimum>=0.)
        negatives=q['negative_endpoints'];assert isinstance(negatives,list)
        assert len({(x['segment'],x['side']) for x in negatives})==len(negatives)
        for x in negatives:
            assert type(x['segment']) is int and 0<=x['segment']<n
            assert type(x['side']) is int and x['side'] in (0,1)
            assert minimum<=number(x['value'])<0.
        assert bool(negatives)==(minimum<0.)
        if negatives: assert min(x['value'] for x in negatives)==minimum
        jump=number(q['maximum_absolute_piece_jump']);count=q['nonzero_piece_jumps']
        assert jump>=0. and type(count) is int and 0<=count<n and (count==0)==(jump==0.)
    nonnegative=diagnostics['radial']['nonnegative'] and diagnostics['axial']['nonnegative']
    assert diagnostics['nonnegative_factors'] is nonnegative
    assert diagnostics['domain']==dict(r=[0.,8.],z=[-8.,8.],outside='explicit_zero_extension')
    boundary=diagnostics['boundary_product_suprema'];assert set(boundary)=={'r8','z_minus8','z_plus8'}
    assert all(number(v)>=0. for v in boundary.values())
    assert diagnostics['extension_discontinuous'] is any(v!=0. for v in boundary.values())
    assert diagnostics['internal_piece_discontinuity'] is any(diagnostics[k]['nonzero_piece_jumps']>0 for k in ('radial','axial'))

    candidate=result['candidate_statistics'];poly=result['polynomial_statistics'];stats(candidate);stats(poly)
    same(candidate['raw_moments'],poly['raw_moments']);compare_stats(candidate,poly)
    R=poly['R'];Z=poly['Z'];Rs=poly['radial_squared_moments'];Zs=poly['axial_squared_moment']
    assert len(R)==len(Z)==3 and len(Rs)==2 and all(number(x)>=0. for x in Rs) and number(Zs)>=0.
    assert R[0]==abs(before)>0.
    raw=[R[0]*Z[0],R[1]*Z[0],R[0]*Z[1],R[2]*Z[0],R[1]*Z[1],R[0]*Z[2],
         2.*math.pi*Rs[0]*Zs,math.pi*R[2]*Z[0],2.*math.pi*Rs[1]*Zs]
    same(poly['raw_moments'],raw)
    if poly['covariance'] is not None: assert poly['covariance'][0][1]==poly['covariance'][1][0]==0.
    refs=result['references'];scores=result['scores'];assert set(refs)==set(scores)=={'S256','S128'}
    all_gates=True
    for name in ('S256','S128'):
        ref=refs[name];stats(ref)
        meta=read_frozen(ROOT.parent/'t60-full-window-gaussian-screen/local'/f'{name}-snapshot-4.json')
        compare_stats(ref,meta['statistics']);compare_stats(ref,saved['cases'][name]['reference'])
        compare_stats(ref,t63['reference_checks'][name])
        assert ref['positive_circulation'] is True and ref['centroid'] is not None
        assert ref['minimum_node']>=0. and ref['minimum_corner']>=0.
        score=scores[name];C=number(score['reference_norm_squared']);numerator=number(score['error_numerator'])
        assert C==ref['vorticity_squared_integral'] and C>0. and numerator>=0.
        error=math.sqrt(numerator/C);close(score['relative_field_error'],error)
        defined=candidate['centroid'] is not None and candidate['covariance'] is not None
        axial=abs(candidate['centroid'][1]-ref['centroid'][1]) if defined else None
        covariance=math.sqrt(math.fsum((candidate['covariance'][i][j]-ref['covariance'][i][j])**2
                    for i in (0,1) for j in (0,1)))/D0 if defined else None
        same(score['axial_centroid_error'],axial);same(score['normalized_covariance_error'],covariance)
        assert score['covariance_denominator']==D0 and score['undefined_reason']==candidate['undefined_reason']
        gates=dict(field=score['relative_field_error']<=.10,
            axial_centroid=score['axial_centroid_error'] is not None and score['axial_centroid_error']<=.10,
            covariance=score['normalized_covariance_error'] is not None and score['normalized_covariance_error']<=.10)
        assert score['gates']==gates and all(type(x) is bool for x in score['gates'].values())
        all_gates=all_gates and all(gates.values())
        close(score['circulation_difference'],candidate['circulation']-ref['circulation'])
        close(score['axial_impulse_difference'],candidate['axial_impulse']-ref['axial_impulse'])
    calibration=abs(scores['S256']['relative_field_error']-saved['cases']['S256']['F']['relative_error'])
    close(result['score_calibration_absolute'],calibration);assert calibration<=1e-10
    difference=abs(scores['S256']['relative_field_error']-scores['S128']['relative_field_error'])
    sensitivity=result['sensitivity'];assert set(sensitivity)=={'absolute_difference','tolerance','passed'}
    close(sensitivity['absolute_difference'],difference)
    assert sensitivity['tolerance']==.001 and sensitivity['passed'] is (difference<=.001)
    physical=dict(nonnegative_factors=nonnegative,positive_circulation=candidate['circulation']>0.,
        defined_moments=candidate['centroid'] is not None and candidate['covariance'] is not None,
        both_reference_gates=all_gates)
    assert result['physical_checks']==physical and all(type(x) is bool for x in result['physical_checks'].values())
    witness=all(physical.values()) and sensitivity['passed']
    verdict='broader_separable_endpoint_witness' if witness else ('reference_sensitive_inconclusive' if not sensitivity['passed'] else 'candidate_miss')
    assert result['capacity_witness'] is witness and result['candidate_verdict']==verdict
    assert QUALIFIED_STATUSES[result['status']]==verdict

    bundle=result['output_bundle'];assert bundle['path']=='local/recovered-factors.npz'
    assert identity(ROOT/bundle['path'])=={k:bundle[k] for k in ('bytes','sha256')}
    layout(bundle['arrays'],dict(a=[256,2],b=[512,2],r=[256],z=[512]))
    assert bundle['array_bytes']==sum(x['bytes'] for x in bundle['arrays'].values())==18432
    assert c['output_array_bytes']==bundle['array_bytes'] and c['output_file_bytes']==c['output_bytes_hashed']==bundle['bytes']
    assert 0<=result['child_elapsed_before_result_write_seconds']<=receipt['scientific_child_supervised_seconds']
    assert result['phases_seconds'] and all(number(v)>=0. for v in result['phases_seconds'].values())
    # Journal inspection checks saved completion/phase accounting, without recomputing any field.
    events=[json.loads(line) for line in (ROOT/'local/work.jsonl').read_text(encoding='utf-8').splitlines()]
    terminal=[x for x in events if x['kind']=='terminal']
    assert len(terminal)==1 and terminal[0]['status']==result['status'] and events[-1]==terminal[0]
    starts=[x['name'] for x in events if x['kind']=='phase_started']
    ends=[x for x in events if x['kind']=='phase_finished']
    assert len(starts)==len(set(starts))==len(ends)==len(result['phases_seconds'])
    assert set(starts)=={x['name'] for x in ends}==set(result['phases_seconds'])
    for x in ends: assert x['seconds']==result['phases_seconds'][x['name']]
    assert sum(x['kind']=='arrays_loaded' for x in events)==3
    assert sum(x['kind']=='factors_saved' for x in events)==1

def main():
    start=time.perf_counter()
    local=ROOT/'local'
    manifest_path=ROOT/'input-manifest.json'
    manifest=json.loads(manifest_path.read_bytes())
    assert manifest['schema']=='t66-saved-product-freeze-v1'
    assert manifest['maximum_scientific_child_invocations']==1
    assert manifest['child_timeout_seconds']==LIMIT and manifest['observed_peak_working_set_limit_bytes']==CAP
    assert manifest['required_available_physical_bytes']==REQUIRED
    assert manifest['expected_python']=='3.12.14' and manifest['expected_numpy']=='2.3.5'
    assert manifest['expected_rule_orders']==[3,2] and manifest['expected_rule_nodes']==5
    assert len(manifest['inputs'])==len({x['path'] for x in manifest['inputs']})==47
    fixed=manifest['expected_fixed_counts']
    required_counts={'input_npz_files','input_arrays','rule_nodes','reference_node_cell_points',
        'candidate_node_cell_points','triangular_blocks','polynomial_cell_moment_evaluations',
        'factor_endpoint_checks','factor_jump_checks','reference_corner_cell_points'}
    assert required_counts<=set(fixed)<=set(EXPECTED_COUNTS)
    assert all(type(v) is int and v==EXPECTED_COUNTS[k] for k,v in fixed.items())
    assert manifest['prior_scientific_child_seconds']==PRIOR
    assert all(identity(REPO/x['path'])=={k:x[k] for k in ('bytes','sha256')} for x in manifest['inputs'])
    exe=Path(manifest['executable']['path'])
    assert identity(exe)=={k:manifest['executable'][k] for k in ('bytes','sha256')}
    assert not (ROOT/'result.json').exists() and not (ROOT/'execution.json').exists()
    assert not (local/'execution-started.json').exists()
    preflight=json.loads((ROOT/'preflight.json').read_bytes())
    assert preflight['schema']=='t66-os-preflight-v1' and preflight['passed'] is True
    assert preflight['source']==identity(MEMORY_SOURCE)
    spec=importlib.util.spec_from_file_location('t66_memory',MEMORY_SOURCE)
    memory=importlib.util.module_from_spec(spec);spec.loader.exec_module(memory)
    command=[str(exe),'-I','-B','-u','-X','utf8',str(ROOT/'measure.py')]
    env=dict(os.environ)
    limits={key:'1' for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
    env.update(limits)
    receipt=dict(schema='t66-saved-product-diagnostic-execution-v1',started_utc=now(),command=command,cwd=str(REPO),
        child_timeout_seconds=LIMIT,observed_peak_working_set_limit_bytes=CAP,
        required_available_physical_bytes=REQUIRED,memory_sample_interval_seconds=INTERVAL,
        thread_environment_overrides=limits,scientific_child_invocations=0,new_scientific_trajectories=0,
        complete_result_validated=False,numerical_qualified=False,candidate_verdict=None,capacity_witness=None,formal_exclusion=False,
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
        if p.is_file() and p.name in ('work.jsonl','failure.json','recovered-factors.npz')]
    receipt['result_exists']=(ROOT/'result.json').exists()
    if receipt['result_exists']:
        receipt['result_identity']=identity(ROOT/'result.json')
        try:
            result=json.loads((ROOT/'result.json').read_bytes())
            assert result['schema']=='t66-saved-product-diagnostic-v1'
            assert result['status'] in set(QUALIFIED_STATUSES)|{'qualification_failure'}
            assert result['formal_exclusion'] is False
            if receipt['status']=='exited_pending_readback':
                if result['status']=='qualification_failure':
                    assert receipt['returncode']==2 and result['numerical_qualified'] is False
                    assert result['candidate_verdict'] is None and result['capacity_witness'] is None
                    receipt['status']='qualification_failure_no_retry'
                else:
                    assert receipt['returncode']==0
                    assert receipt['scientific_child_supervised_seconds']<=LIMIT
                    assert receipt['memory_samples']>0 and receipt['peak_observed_working_set_bytes']<=CAP
                    assert receipt['inputs_unchanged'] and receipt['input_manifest_unchanged'] and receipt['executable_unchanged']
                    validate_result(result,manifest,receipt,exe,manifest_path)
                    receipt.update(status='completed_'+result['status'],complete_result_validated=True,numerical_qualified=True,
                        candidate_verdict=result['candidate_verdict'],capacity_witness=result['capacity_witness'],formal_exclusion=False)
        except Exception as exc:
            receipt['result_read_error']=repr(exc)
            if receipt['status']=='exited_pending_readback':receipt['status']='failed_result_validation_no_retry'
    elif receipt['status']=='exited_pending_readback':
        receipt['status']='missing_result_no_retry'
    if not all(receipt[k] for k in ('inputs_unchanged','input_manifest_unchanged','executable_unchanged')):
        receipt.update(status='failed_preservation_no_retry',complete_result_validated=False,numerical_qualified=False,
            candidate_verdict=None,capacity_witness=None,formal_exclusion=False)
    receipt['supervisor_elapsed_before_receipt_write_seconds']=time.perf_counter()-start
    receipt['finished_utc']=now()
    write(ROOT/'execution.json',receipt)
    print(json.dumps({k:receipt[k] for k in ('status','scientific_child_invocations','scientific_child_supervised_seconds',
        'candidate_verdict','peak_observed_working_set_bytes','inputs_unchanged')},indent=2))

if __name__=='__main__':main()
