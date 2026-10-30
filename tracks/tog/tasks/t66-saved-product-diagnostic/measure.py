"""One frozen saved-product diagnostic; no decomposition, fit, or flow."""
import datetime
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time
import traceback
from contextlib import contextmanager

START = time.perf_counter()
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
LOCAL = ROOT/'local'
OLD = ROOT.parent/'t60-full-window-gaussian-screen'
SAVED = ROOT.parent/'t65-separability-measurement'
np = None
STREAM = None
BEFORE = {}
PHASES = {}
PARTIAL = {}
INPUT_ARRAYS = []
ACTIVE = 'initialization'
CHECKS = dict.fromkeys(('frozen_inputs_before','input_shapes_coordinates','triangular_recovery',
    'reference_readback','polynomial_quadrature_agreement','saved_field_score_agreement',
    'fixed_work_accounting','frozen_inputs_after'),False)
COUNTERS = dict(input_bytes_hashed_before=0,input_bytes_hashed_after=0,output_bytes_hashed=0,
    input_npz_files=0,input_arrays=0,triangular_blocks=0,polynomial_cell_moment_evaluations=0,
    polynomial_factor_integrals=0,factor_endpoint_checks=0,factor_jump_checks=0,
    boundary_product_checks=0,reference_corner_cell_points=0,candidate_node_cell_points=0,
    reference_node_cell_points=0,rules_constructed=0,rule_nodes=0,
    reference_integrals=0,candidate_quadrature_integrals=0,output_bundles=0,
    output_array_bytes=0,output_file_bytes=0,svd_calls=0,eigensolver_calls=0,
    gaussian_field_evaluations=0,gaussian_fits=0,new_flow_trajectories=0)


def require(ok,message):
    if not ok: raise ValueError(message)


def clock():
    require(time.perf_counter()-START<60.,'fixed 60-second child budget exhausted')


def event(kind,**values):
    if STREAM is not None:
        STREAM.write(json.dumps(dict(kind=kind,elapsed_seconds=time.perf_counter()-START,**values),allow_nan=False)+'\n')
        STREAM.flush()


@contextmanager
def phase(name):
    global ACTIVE
    ACTIVE=name; begin=time.perf_counter(); event('phase_started',name=name)
    try:
        clock(); yield
    finally:
        seconds=time.perf_counter()-begin; PHASES[name]=PHASES.get(name,0.)+seconds
        event('phase_finished',name=name,seconds=seconds)


def identity(path,counter=None):
    digest=hashlib.sha256(); size=0
    with path.open('rb') as stream:
        while block:=stream.read(1024*1024):
            clock(); digest.update(block); size+=len(block)
    if counter: COUNTERS[counter]+=size
    return dict(bytes=size,sha256=digest.hexdigest())


def write_json(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,allow_nan=False); stream.write('\n')


def read_json(path):
    require(path.resolve() in BEFORE,'unfrozen JSON: '+str(path))
    def invalid(text): raise ValueError('invalid JSON constant: '+text)
    return json.loads(path.read_text(encoding='utf-8'),parse_constant=invalid)


def close(actual,expected,label):
    a=np.asarray(actual); b=np.asarray(expected)
    require(a.shape==b.shape and bool(np.all(np.isfinite(a))) and bool(np.all(np.isfinite(b)))
            and bool(np.allclose(a,b,rtol=3e-11,atol=3e-14)),label)


def freeze():
    path=ROOT/'input-manifest.json'; raw=path.read_bytes(); manifest=json.loads(raw)
    fixed=dict(schema='t66-saved-product-freeze-v1',expected_python='3.12.14',expected_numpy='2.3.5',
        maximum_scientific_child_invocations=1,child_timeout_seconds=60,
        observed_peak_working_set_limit_bytes=536870912,required_available_physical_bytes=1073741824,
        expected_rule_orders=[3,2],expected_rule_nodes=5,expected_input_npz_files=3,expected_input_arrays=19,
        expected_triangular_blocks=768,expected_candidate_node_cell_points=786432,
        expected_reference_node_cell_points=1572864,expected_reference_corner_cell_points=655360,
        expected_polynomial_cell_moment_evaluations=3328,expected_factor_endpoint_checks=1536,
        expected_factor_jump_checks=766,prior_scientific_child_seconds=1979.5974398998078)
    require(all(manifest.get(k)==v for k,v in fixed.items()),'fixed execution contract')
    admitted={}
    for item in manifest['inputs']:
        value=item['path']
        require(isinstance(value,str) and value and '\\' not in value and ':' not in value
                and not value.startswith('/') and all(x not in ('','.','..') for x in value.split('/')),
                'invalid repository input path')
        target=(REPO/value).resolve()
        require(target.is_relative_to(REPO) and target not in admitted,'duplicate/escaping input')
        admitted[target]={k:item[k] for k in ('bytes','sha256')}
    executable=Path(manifest['executable']['path']).resolve()
    require(executable==Path(sys.executable).resolve(),'runtime executable')
    admitted[executable]={k:manifest['executable'][k] for k in ('bytes','sha256')}
    for target,expected in admitted.items():
        actual=identity(target,'input_bytes_hashed_before')
        require(actual==expected,'frozen input mismatch: '+str(target)); BEFORE[target]=actual
    BEFORE[path.resolve()]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    COUNTERS['input_bytes_hashed_before']+=len(raw)


def decode(path,shapes,role):
    require(path.resolve() in BEFORE,'unfrozen numerical input')
    with np.load(path,allow_pickle=False) as archive:
        arrays={key:archive[key] for key in shapes}
    COUNTERS['input_npz_files']+=1; COUNTERS['input_arrays']+=len(arrays)
    for key,value in arrays.items():
        require(value.shape==shapes[key] and value.dtype==np.dtype('float64')
                and bool(np.all(np.isfinite(value))),'array shape/type/finite: '+role+'/'+key)
    INPUT_ARRAYS.append(dict(role=role,path=path.relative_to(REPO).as_posix(),**BEFORE[path.resolve()],
        arrays={k:dict(shape=list(v.shape),dtype=str(v.dtype),bytes=v.nbytes) for k,v in arrays.items()}))
    event('arrays_loaded',record=INPUT_ARRAYS[-1])
    return arrays


def load_field(name,n):
    meta=read_json(OLD/'local'/f'{name}-snapshot-4.json')
    require((meta['name'],meta['index'],meta['time'],meta['nr'],meta['nz'],meta['R'])
            ==(name,4,1.,n,2*n,8.),'endpoint metadata')
    h=meta['h']; require(h==8./n and meta['raw']['path']==f'{name}-snapshot-4.npz','grid/raw identity')
    path=OLD/'local'/meta['raw']['path']
    require(BEFORE[path.resolve()]=={k:meta['raw'][k] for k in ('bytes','sha256')},'snapshot identity')
    shapes={k:(n,2*n) for k in ('q','qr','qz')}; shapes.update(r=(n,),rc=(n,),z=(2*n,))
    f=decode(path,shapes,name)
    rf=np.arange(n+1)*h; zf=-8.+np.arange(2*n+1)*h; area=(rf[1:]**2-rf[:-1]**2)/2.
    expected=dict(r=(rf[:-1]+rf[1:])/2.,z=(zf[:-1]+zf[1:])/2.,rc=(rf[1:]**3-rf[:-1]**3)/(3.*area))
    for key,value in expected.items():
        require(np.array_equal(f[key],value) and bool(np.all(np.diff(f[key])>0.)),'saved coordinates: '+key)
    require(bool(np.all(f['q']>=0.)),'negative cell average'); minimum=math.inf
    for radial in (rf[:-1],rf[1:]):
        for axial in (-h/2.,h/2.):
            clock(); corner=f['q']+f['qr']*(radial-f['rc'])[:,None]+f['qz']*axial
            COUNTERS['reference_corner_cell_points']+=n*2*n
            require(bool(np.all(np.isfinite(corner))) and bool(np.all(corner>=0.)),'PL corner positivity')
            minimum=min(minimum,float(np.min(corner)))
    f.update(n=n,h=h,statistics=meta['statistics'],minimum_corner=minimum)
    return f


def recover(saved,fine):
    path=SAVED/'local'/'S256-audit.npz'; artifact=saved['cases']['S256']['audit_bundle']
    require(artifact['path']=='local/S256-audit.npz' and BEFORE[path.resolve()]
            =={k:artifact[k] for k in ('bytes','sha256')},'audit bundle identity')
    shapes=dict(U_F=(512,512),s_F=(512,),Vh_F=(512,1024),Lr=(256,2,2),Lz=(512,2,2),r=(256,),z=(512,))
    data=decode(path,shapes,'S256_saved_factors')
    require(np.array_equal(data['r'],fine['r']) and np.array_equal(data['z'],fine['z']),'audit coordinates')
    s0=float(data['s_F'][0]); require(s0>0. and s0==saved['cases']['S256']['F']['singular_values'][0],'leading value')
    root=math.sqrt(s0); output=[]; diagnostics={}
    for axis,L,target in (('radial',data['Lr'],data['U_F'][:,0].reshape(256,2)*root),
                          ('axial',data['Lz'],data['Vh_F'][0,:].reshape(512,2)*root)):
        require(bool(np.all(L[:,0,1]==0.)) and bool(np.all(L[:,0,0]>0.))
                and bool(np.all(L[:,1,1]>0.)),'triangular factor structure')
        c=np.empty_like(target); c[:,1]=target[:,1]/L[:,1,1]
        c[:,0]=(target[:,0]-L[:,1,0]*c[:,1])/L[:,0,0]
        reconstructed=np.column_stack((L[:,0,0]*c[:,0]+L[:,1,0]*c[:,1],L[:,1,1]*c[:,1]))
        denominator=math.sqrt(float(np.sum(target*target)))
        residual=math.sqrt(float(np.sum((reconstructed-target)**2)))/denominator
        require(bool(np.all(np.isfinite(c))) and math.isfinite(residual) and residual<=1e-10,'triangular recovery')
        COUNTERS['triangular_blocks']+=len(c)
        diagnostics[axis]=dict(blocks=len(c),relative_residual=residual,target_frobenius=denominator)
        output.append(c)
    PARTIAL['recovery']=dict(leading_singular_value=s0,**diagnostics)
    CHECKS['triangular_recovery']=True
    return output


def polynomial_integral(centers,coeff,h,p,squared=False):
    # Analytic monomial antiderivatives on [-1/2,1/2], independent of GL nodes.
    def moment(k): return 0. if k%2 else 1./((k+1)*2**k)
    cells=[]
    for m,c in zip(centers,coeff):
        c0=float(c[0]); c1=float(c[1]); m=float(m); terms=[]
        for j in range(p+1):
            factor=math.comb(p,j)*m**(p-j)*h**j
            inner=(c0*c0*moment(j)+2.*c0*c1*moment(j+1)+c1*c1*moment(j+2)) if squared else (c0*moment(j)+c1*moment(j+1))
            terms.append(factor*inner)
        cells.append(h*math.fsum(terms))
    COUNTERS['polynomial_cell_moment_evaluations']+=len(cells); COUNTERS['polynomial_factor_integrals']+=1
    answer=math.fsum(cells); require(math.isfinite(answer),'nonfinite polynomial moment'); return answer


def statistics(totals):
    raw=[float(x) for x in totals]; require(all(math.isfinite(x) for x in raw),'nonfinite raw moments')
    gamma=raw[0]; reason=None; mean=None; cov=None
    if gamma==0.: reason='zero_circulation'
    else:
        m=np.asarray(raw[1:3])/gamma
        c=np.array([[raw[3],raw[4]],[raw[4],raw[5]]])/gamma-np.outer(m,m)
        if bool(np.all(np.isfinite(m))) and bool(np.all(np.isfinite(c))): mean=m.tolist(); cov=c.tolist()
        else: reason='nonfinite_normalized_moments'
    return dict(raw_moments=raw,circulation=gamma,centroid=mean,covariance=cov,undefined_reason=reason,
        positive_circulation=gamma>0.,q_squared_integral=raw[6],axial_impulse=raw[7],vorticity_squared_integral=raw[8])


def factor_moments(a,b,fine):
    h=fine['h']; R=[polynomial_integral(fine['r'],a,h,k+1) for k in range(3)]
    Z=[polynomial_integral(fine['z'],b,h,k) for k in range(3)]
    Rs=[polynomial_integral(fine['r'],a,h,k,True) for k in (1,3)]
    Zs=polynomial_integral(fine['z'],b,h,0,True)
    PARTIAL['orientation']=dict(radial_integral_before=R[0],common_sign_flipped=R[0]<0.)
    require(R[0]!=0.,'candidate_definition_zero_radial_integral')
    if R[0]<0.:
        a*=-1.; b*=-1.; R=[-x for x in R]; Z=[-x for x in Z]
    raw=[R[0]*Z[0],R[1]*Z[0],R[0]*Z[1],R[2]*Z[0],R[1]*Z[1],R[0]*Z[2],
         2.*math.pi*Rs[0]*Zs,math.pi*R[2]*Z[0],2.*math.pi*Rs[1]*Zs]
    record=statistics(raw)
    # Use the independently separable ratios, rather than the quadrature's total-mass ratios.
    if Z[0]!=0.:
        mr=R[1]/R[0]; mz=Z[1]/Z[0]; vr=R[2]/R[0]-mr*mr; vz=Z[2]/Z[0]-mz*mz
        if all(math.isfinite(x) for x in (mr,mz,vr,vz)):
            record.update(centroid=[mr,mz],covariance=[[vr,0.],[0.,vz]],undefined_reason=None)
        else: record.update(centroid=None,covariance=None,undefined_reason='nonfinite_separable_ratios')
    record.update(R=R,Z=Z,radial_squared_moments=Rs,axial_squared_moment=Zs)
    return record


def factor_diagnostics(a,b):
    endpoints={}; records={}
    for axis,c in (('radial',a),('axial',b)):
        e=np.column_stack((c[:,0]-c[:,1]/2.,c[:,0]+c[:,1]/2.))
        require(bool(np.all(np.isfinite(e))),'nonfinite factor endpoints')
        COUNTERS['factor_endpoint_checks']+=e.size
        jumps=e[1:,0]-e[:-1,1]; COUNTERS['factor_jump_checks']+=len(jumps)
        negative=np.argwhere(e<0.)
        records[axis]=dict(minimum_endpoint=float(np.min(e)),maximum_endpoint=float(np.max(e)),
            nonnegative=bool(np.all(e>=0.)),negative_endpoints=[dict(segment=int(i),side=int(j),value=float(e[i,j])) for i,j in negative],
            maximum_absolute_piece_jump=float(np.max(np.abs(jumps))),nonzero_piece_jumps=int(np.count_nonzero(jumps)))
        endpoints[axis]=e
    er=endpoints['radial']; ez=endpoints['axial']
    boundaries=dict(r8=abs(float(er[-1,1]))*float(np.max(np.abs(ez))),
        z_minus8=abs(float(ez[0,0]))*float(np.max(np.abs(er))),
        z_plus8=abs(float(ez[-1,1]))*float(np.max(np.abs(er))))
    COUNTERS['boundary_product_checks']+=3
    require(all(math.isfinite(x) for x in boundaries.values()),'nonfinite boundary product')
    return dict(**records,nonnegative_factors=records['radial']['nonnegative'] and records['axial']['nonnegative'],
        domain=dict(r=[0.,8.],z=[-8.,8.],outside='explicit_zero_extension'),boundary_product_suprema=boundaries,
        extension_discontinuous=any(x!=0. for x in boundaries.values()),
        internal_piece_discontinuity=any(x['nonzero_piece_jumps']>0 for x in records.values()))


def add_totals(totals,q,r,z,w):
    density=w*q
    totals+=np.array([np.sum(density),np.sum(density*r),np.sum(density*z),np.sum(density*r*r),
        np.sum(density*r*z),np.sum(density*z*z),2.*math.pi*np.sum(w*q*q),
        math.pi*np.sum(density*r*r),2.*math.pi*np.sum(w*r*r*q*q)])


def quadrature(a,b,fields):
    fine=fields['S256']; h=fine['h']; totals=np.zeros(9); ref={k:np.zeros(9) for k in fields}
    errors=dict.fromkeys(fields,0.); minima=dict.fromkeys(fields,math.inf)
    # Closed-form fixed rules avoid a hidden eigensolver inside rule generation.
    x3=math.sqrt(3./5.); x2=1./math.sqrt(3.)
    rules={3:([-x3,0.,x3],[5./9.,8./9.,5./9.]),2:([-x2,x2],[1.,1.])}
    COUNTERS['rules_constructed']=2; COUNTERS['rule_nodes']=5
    for xr,wr in zip(*rules[3]):
        for xz,wz in zip(*rules[2]):
            clock(); rn=fine['r']+xr*h/2.; zn=fine['z']+xz*h/2.
            r=rn[:,None]; z=zn[None,:]; w=wr*wz*h*h/4.*r
            qstar=(a[:,0]+a[:,1]*xr/2.)[:,None]*(b[:,0]+b[:,1]*xz/2.)[None,:]
            require(bool(np.all(np.isfinite(qstar))),'nonfinite product node')
            add_totals(totals,qstar,r,z,w); COUNTERS['candidate_node_cell_points']+=qstar.size
            for name,f in fields.items():
                ir=np.arange(256)//(256//f['n']); iz=np.arange(512)//(256//f['n'])
                require(bool(np.all(rn>f['r'][ir]-f['h']/2.)) and bool(np.all(rn<f['r'][ir]+f['h']/2.))
                        and bool(np.all(zn>f['z'][iz]-f['h']/2.)) and bool(np.all(zn<f['z'][iz]+f['h']/2.)),
                        'containing coarse cells')
                index=np.ix_(ir,iz)
                q=f['q'][index]+f['qr'][index]*(rn-f['rc'][ir])[:,None]+f['qz'][index]*(zn-f['z'][iz])[None,:]
                require(bool(np.all(np.isfinite(q))) and bool(np.all(q>=0.)),'reference node positivity')
                add_totals(ref[name],q,r,z,w); minima[name]=min(minima[name],float(np.min(q)))
                errors[name]+=2.*math.pi*float(np.sum(w*r*r*(q-qstar)**2))
                COUNTERS['reference_node_cell_points']+=q.size
    COUNTERS['candidate_quadrature_integrals']+=1; COUNTERS['reference_integrals']+=2
    records={name:dict(**statistics(t),minimum_node=minima[name],minimum_corner=fields[name]['minimum_corner']) for name,t in ref.items()}
    return statistics(totals),records,errors


def compare_statistics(actual,expected,label):
    for key in ('circulation','q_squared_integral','axial_impulse','vorticity_squared_integral'):
        close(actual[key],expected[key],label+'/'+key)
    for key in ('centroid','covariance'):
        if actual[key] is None or expected[key] is None:
            require(actual[key] is None and expected[key] is None,label+'/'+key+' definedness')
        else: close(actual[key],expected[key],label+'/'+key)


def save_factors(a,b,fine):
    arrays=dict(a=a,b=b,r=fine['r'],z=fine['z']); path=LOCAL/'recovered-factors.npz'
    layout={k:dict(shape=list(v.shape),dtype=str(v.dtype),bytes=v.nbytes) for k,v in arrays.items()}
    with path.open('xb') as stream: np.savez(stream,**arrays); stream.flush()
    artifact=dict(path=path.relative_to(ROOT).as_posix(),**identity(path,'output_bytes_hashed'),arrays=layout,
                  array_bytes=sum(x['bytes'] for x in layout.values()))
    COUNTERS['output_bundles']+=1; COUNTERS['output_array_bytes']+=artifact['array_bytes']
    COUNTERS['output_file_bytes']+=artifact['bytes']; PARTIAL['output_bundle']=artifact
    event('factors_saved',artifact=artifact)


def measure():
    global np
    with phase('imports_and_input_hashes'):
        require(platform.python_version()=='3.12.14','Python version')
        import numpy as numpy
        np=numpy; require(np.__version__=='2.3.5','NumPy version'); freeze(); CHECKS['frozen_inputs_before']=True
        saved=read_json(SAVED/'result.json'); t63=read_json(ROOT.parent/'t63-endpoint-capacity'/'result.json')
        t61=read_json(ROOT.parent/'t61-saved-output-qualification'/'result.json')
        require(t61['accepted_saved_evidence'] is True and t61['reference_qualified_full_window'] is True,'T61 qualification')
        require(saved['status']=='qualified_no_separability_exclusion' and saved['input_identities_unchanged'] is True
                and saved['checks'] and all(v is True for v in saved['checks'].values()),'T65 qualification')
        require(t63['status']=='search_inconclusive' and t63['input_identities_unchanged'] is True
                and t63['checks'] and all(v is True for v in t63['checks'].values()),'T63 qualification')
        D0=t63['region']['D0']; require(D0==1.0882203729522952,'original covariance denominator')
    with phase('input_arrays_and_recovery'):
        fields={name:load_field(name,n) for name,n in (('S256',256),('S128',128))}
        a,b=recover(saved,fields['S256']); CHECKS['input_shapes_coordinates']=True
    with phase('independent_polynomial_moments_and_sign'):
        polynomial=factor_moments(a,b,fields['S256']); PARTIAL['polynomial_statistics']=polynomial
        PARTIAL['factor_diagnostics']=factor_diagnostics(a,b)
    with phase('recovered_factor_artifact'):
        save_factors(a,b,fields['S256'])
    with phase('fixed_quadrature'):
        candidate,references,errors=quadrature(a,b,fields)
        PARTIAL.update(candidate_statistics=candidate,references=references)
        for name in fields:
            compare_statistics(references[name],fields[name]['statistics'],name+'/original metadata')
            compare_statistics(references[name],saved['cases'][name]['reference'],name+'/T65 metadata')
            compare_statistics(references[name],t63['reference_checks'][name],name+'/T63 metadata')
        CHECKS['reference_readback']=True
        close(candidate['raw_moments'],polynomial['raw_moments'],'independent raw candidate moments')
        compare_statistics(candidate,polynomial,'independent normalized candidate moments')
        CHECKS['polynomial_quadrature_agreement']=True
    with phase('scores_and_verdict'):
        scores={}
        for name,ref in references.items():
            C=ref['vorticity_squared_integral']; numerator=errors[name]
            require(C>0. and math.isfinite(numerator) and numerator>=0.,'field error integrals')
            error=math.sqrt(numerator/C); defined=candidate['centroid'] is not None and candidate['covariance'] is not None
            axial=abs(candidate['centroid'][1]-ref['centroid'][1]) if defined else None
            cov=math.sqrt(float(np.sum((np.asarray(candidate['covariance'])-np.asarray(ref['covariance']))**2)))/D0 if defined else None
            gates=dict(field=error<=.10,axial_centroid=axial is not None and axial<=.10,covariance=cov is not None and cov<=.10)
            scores[name]=dict(error_numerator=numerator,reference_norm_squared=C,relative_field_error=error,
                axial_centroid_error=axial,normalized_covariance_error=cov,covariance_denominator=D0,gates=gates,
                undefined_reason=candidate['undefined_reason'],circulation_difference=candidate['circulation']-ref['circulation'],
                axial_impulse_difference=candidate['axial_impulse']-ref['axial_impulse'])
        calibration=abs(scores['S256']['relative_field_error']-saved['cases']['S256']['F']['relative_error'])
        require(calibration<=1e-10,'saved leading-product field score')
        CHECKS['saved_field_score_agreement']=True
        difference=abs(scores['S256']['relative_field_error']-scores['S128']['relative_field_error'])
        sensitivity=dict(absolute_difference=difference,tolerance=.001,passed=difference<=.001)
        physical=dict(nonnegative_factors=PARTIAL['factor_diagnostics']['nonnegative_factors'],
            positive_circulation=candidate['circulation']>0.,defined_moments=candidate['centroid'] is not None and candidate['covariance'] is not None,
            both_reference_gates=all(all(s['gates'].values()) for s in scores.values()))
        witness=all(physical.values()) and sensitivity['passed']
        verdict='broader_separable_endpoint_witness' if witness else ('reference_sensitive_inconclusive' if not sensitivity['passed'] else 'candidate_miss')
        status={'broader_separable_endpoint_witness':'broader_separable_endpoint_witness',
            'reference_sensitive_inconclusive':'qualified_reference_sensitive_inconclusive','candidate_miss':'qualified_candidate_miss'}[verdict]
        PARTIAL.update(scores=scores,physical_checks=physical,sensitivity=sensitivity,score_calibration_absolute=calibration)
    expected=dict(input_npz_files=3,input_arrays=19,triangular_blocks=768,polynomial_cell_moment_evaluations=3328,
        polynomial_factor_integrals=9,factor_endpoint_checks=1536,factor_jump_checks=766,boundary_product_checks=3,
        reference_corner_cell_points=655360,candidate_node_cell_points=786432,reference_node_cell_points=1572864,
        rules_constructed=2,rule_nodes=5,reference_integrals=2,candidate_quadrature_integrals=1,output_bundles=1,
        svd_calls=0,eigensolver_calls=0,gaussian_field_evaluations=0,gaussian_fits=0,new_flow_trajectories=0)
    require(all(COUNTERS[k]==v for k,v in expected.items()),'fixed work accounting'); CHECKS['fixed_work_accounting']=True
    return dict(status=status,candidate_verdict=verdict,capacity_witness=witness)


def main():
    global STREAM
    LOCAL.mkdir(exist_ok=True); failure=None; result=None
    with (LOCAL/'work.jsonl').open('x',encoding='utf-8',newline='\n') as STREAM:
        try: result=measure()
        except Exception as error:
            failure=dict(error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc(),active=ACTIVE)
        try:
            with phase('input_hashes_after'):
                for path,expected in BEFORE.items():
                    require(identity(path,'input_bytes_hashed_after')==expected,'input changed: '+str(path))
            CHECKS['frozen_inputs_after']=True
        except Exception as error:
            CHECKS['frozen_inputs_after']=False
            failure=dict(error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc(),active=ACTIVE,previous_failure=failure)
        if failure: result=dict(status='qualification_failure',candidate_verdict=None,capacity_witness=None,failure=failure)
        result.update(schema='t66-saved-product-diagnostic-v1',**PARTIAL,checks=CHECKS,counters=COUNTERS,
            numerical_qualified=failure is None and all(CHECKS.values()),input_arrays=INPUT_ARRAYS,phases_seconds=PHASES,
            formal_exclusion=False,gaussian_witness=False,causal_dynamics_claim=False,new_flow_trajectories=0,
            prior_scientific_child_seconds=1979.5974398998078,prior_evidence_qualification_seconds=.9663960000034422,
            input_identities_unchanged=CHECKS['frozen_inputs_before'] and CHECKS['frozen_inputs_after'],
            input_identities=[dict(path=p.relative_to(REPO).as_posix() if p.is_relative_to(REPO) else str(p),**v) for p,v in BEFORE.items()],
            python=platform.python_version(),numpy=np.__version__ if np is not None else None,executable=str(Path(sys.executable).resolve()),
            created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),child_elapsed_before_result_write_seconds=time.perf_counter()-START)
        if failure: write_json(LOCAL/'failure.json',result)
        event('terminal',status=result['status']); clock(); write_json(ROOT/'result.json',result)
    STREAM=None
    print(json.dumps(dict(status=result['status'],candidate_verdict=result['candidate_verdict'])),flush=True)
    return 2 if failure else 0


if __name__=='__main__':
    raise SystemExit(main())
