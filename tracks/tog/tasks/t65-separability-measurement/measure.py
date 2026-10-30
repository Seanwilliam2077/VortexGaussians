"""One frozen weighted-separability diagnostic; no historical module execution."""
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
np = None
STREAM = None
BEFORE = {}
CHECKS = {}
PHASES = {}
CASES = {}
ACTIVE = 'initialization'
COUNTERS = dict(input_bytes_hashed_before=0,input_bytes_hashed_after=0,output_bytes_hashed=0,
    array_files_decoded=0,arrays_loaded=0,rules_constructed=0,rule_nodes=0,
    reference_integrals=0,reference_node_cell_points=0,Y_entries_written=0,corner_cell_points=0,
    analytic_gram_blocks=0,quadrature_gram_blocks=0,cholesky_blocks=0,
    cholesky_reconstruction_blocks=0,gram_axis_node_evaluations=0,
    basis_matrices=0,weighted_matrices=0,quadrature_matrices=0,
    svd_started=0,svd_completed=0,residual_products=0,orthogonality_products=0,
    audit_bundles=0,audit_array_bytes=0,audit_file_bytes=0,
    gaussian_field_evaluations=0,gaussian_fits=0,new_flow_trajectories=0)


def require(ok, message):
    if not ok: raise ValueError(message)


def clock():
    require(time.perf_counter()-START<120., 'fixed 120-second child budget exhausted')


def event(kind, **values):
    if STREAM is not None:
        STREAM.write(json.dumps(dict(kind=kind,elapsed_seconds=time.perf_counter()-START,
                                     **values),allow_nan=False)+'\n')
        STREAM.flush()


@contextmanager
def phase(name):
    global ACTIVE
    ACTIVE=name; begin=time.perf_counter()
    event('phase_started',name=name)
    try:
        clock()
        yield
    finally:
        seconds=time.perf_counter()-begin
        PHASES[name]=PHASES.get(name,0.)+seconds
        event('phase_finished',name=name,seconds=seconds)


def identity(path, counter=None):
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
    require(path.resolve() in BEFORE, 'unfrozen JSON: '+str(path))
    def invalid(text): raise ValueError('invalid JSON constant: '+text)
    return json.loads(path.read_text(encoding='utf-8'),parse_constant=invalid)


def close(actual,expected,label):
    a=np.asarray(actual); b=np.asarray(expected)
    require(a.shape==b.shape and bool(np.all(np.isfinite(a))) and
            bool(np.allclose(a,b,rtol=3e-11,atol=3e-14)),label)


def frobenius(value):
    return math.sqrt(float(np.sum(value*value)))


def freeze():
    path=ROOT/'input-manifest.json'; raw=path.read_bytes(); manifest=json.loads(raw)
    fixed=dict(schema='t65-separability-freeze-v1',expected_python='3.12.14',expected_numpy='2.3.5',
        maximum_scientific_child_invocations=1,child_timeout_seconds=120,
        observed_peak_working_set_limit_bytes=536870912,required_available_physical_bytes=1073741824,
        expected_svd_calls=4,expected_rule_orders=[3,2],expected_rule_nodes=5,
        expected_reference_node_cell_points=983040,expected_corner_cell_points=655360)
    require(all(manifest.get(k)==v for k,v in fixed.items()),'fixed execution contract')
    admitted={}
    for item in manifest['inputs']:
        value=item['path']
        require(isinstance(value,str) and value and '\\' not in value and ':' not in value
                and not value.startswith('/') and all(x not in ('','.','..') for x in value.split('/')),
                'invalid frozen repository path')
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


def rules():
    out={}
    for n in (3,2):
        clock(); x,w=np.polynomial.legendre.leggauss(n)
        require(x.shape==w.shape==(n,) and bool(np.all(np.isfinite(x))) and
                bool(np.all(np.diff(x)>0.)) and bool(np.all(w>0.)) and
                abs(float(np.sum(w))-2.)<=3e-14,'Gaussian rule construction')
        out[n]=(x,w); COUNTERS['rules_constructed']+=1; COUNTERS['rule_nodes']+=n
    return out


def load_field(name,n):
    metadata=read_json(OLD/'local'/f'{name}-snapshot-4.json')
    require((metadata['name'],metadata['index'],metadata['time'],metadata['nr'],metadata['nz'],metadata['R'])
            ==(name,4,1.,n,2*n,8.),'endpoint metadata')
    h=metadata['h']; require(h==8./n,'grid spacing')
    require(metadata['raw']['path']==f'{name}-snapshot-4.npz','raw basename')
    path=OLD/'local'/metadata['raw']['path']
    require(BEFORE[path.resolve()]=={k:metadata['raw'][k] for k in ('bytes','sha256')},'snapshot identity')
    with np.load(path,allow_pickle=False) as archive:
        f={key:archive[key] for key in ('q','qr','qz','r','rc','z')}
    COUNTERS['array_files_decoded']+=1; COUNTERS['arrays_loaded']+=6
    for key,value in f.items():
        shape=(n,2*n) if key in ('q','qr','qz') else ((2*n,) if key=='z' else (n,))
        require(value.shape==shape and value.dtype==np.dtype('float64') and
                bool(np.all(np.isfinite(value))),'array shape/type/finite: '+key)
    rf=np.arange(n+1)*h; zf=-8.+np.arange(2*n+1)*h; area=(rf[1:]**2-rf[:-1]**2)/2.
    expected=dict(r=(rf[:-1]+rf[1:])/2.,z=(zf[:-1]+zf[1:])/2.,
                  rc=(rf[1:]**3-rf[:-1]**3)/(3.*area))
    for key,value in expected.items():
        require(np.array_equal(f[key],value) and bool(np.all(np.diff(f[key])>0.)),'saved coordinates: '+key)
    require(bool(np.all(f['q']>=0.)),'negative cell average')
    minimum=math.inf
    for radial in (rf[:-1],rf[1:]):
        for axial in (-h/2.,h/2.):
            clock(); corner=f['q']+f['qr']*(radial-f['rc'])[:,None]+f['qz']*axial
            COUNTERS['corner_cell_points']+=n*2*n
            minimum=min(minimum,float(np.min(corner)))
            require(bool(np.all(np.isfinite(corner))) and bool(np.all(corner>=0.)),'PL corner positivity')
    f.update(name=name,n=n,h=h,statistics=metadata['statistics'],minimum_corner=minimum)
    return f


def block_relative(actual,expected):
    return np.sqrt(np.sum((actual-expected)**2,axis=(1,2)))/np.sqrt(np.sum(expected**2,axis=(1,2)))


def gram_and_basis(f,rule):
    n=f['n']; h=f['h']; m=f['r']; C=np.zeros((n,2,2*n,2))
    C[:,0,:,0]=f['q']+f['qr']*(m-f['rc'])[:,None]
    C[:,0,:,1]=h*f['qz']; C[:,1,:,0]=h*f['qr']
    require(bool(np.all(np.isfinite(C))),'nonfinite scaled coefficients')
    COUNTERS['basis_matrices']+=1
    Gr=np.empty((n,2,2)); Gz=np.zeros((2*n,2,2))
    Gr[:,0,0]=2.*math.pi*h*(m**3+m*h*h/4.)
    Gr[:,0,1]=Gr[:,1,0]=2.*math.pi*h*(m*m*h/4.+h**3/80.)
    Gr[:,1,1]=2.*math.pi*h*(m**3/12.+3.*m*h*h/80.)
    Gz[:,0,0]=h; Gz[:,1,1]=h/12.
    COUNTERS['analytic_gram_blocks']+=3*n
    quadrature_r=np.zeros_like(Gr); quadrature_z=np.zeros_like(Gz)
    for x,w in zip(*rule[3]):
        r=m+x*h/2.; basis=np.array([1.,x/2.])
        quadrature_r+=(2.*math.pi*w*h/2.*r**3)[:,None,None]*np.outer(basis,basis)
        COUNTERS['gram_axis_node_evaluations']+=n
    for x,w in zip(*rule[2]):
        basis=np.array([1.,x/2.])
        quadrature_z+=w*h/2.*np.outer(basis,basis)[None,:,:]
        COUNTERS['gram_axis_node_evaluations']+=2*n
    COUNTERS['quadrature_gram_blocks']+=3*n
    factors=[]; diagnostic={}
    for axis,G,Q in (('radial',Gr,quadrature_r),('axial',Gz,quadrature_z)):
        require(bool(np.all(np.isfinite(G))) and bool(np.all(G[:,0,0]>0.)),'invalid analytic Gram')
        L=np.zeros_like(G); L[:,0,0]=np.sqrt(G[:,0,0]); L[:,1,0]=G[:,1,0]/L[:,0,0]
        pivot=G[:,1,1]-L[:,1,0]**2
        require(bool(np.all(np.isfinite(pivot))) and bool(np.all(pivot>0.)),'Gram not positive definite')
        L[:,1,1]=np.sqrt(pivot)
        COUNTERS['cholesky_blocks']+=len(G)
        reconstructed=L@np.swapaxes(L,1,2); COUNTERS['cholesky_reconstruction_blocks']+=len(G)
        reconstruction=block_relative(reconstructed,G); quadrature=block_relative(Q,G)
        require(bool(np.all(np.isfinite(reconstruction))) and bool(np.all(np.isfinite(quadrature)))
                and bool(np.all(reconstruction<=1e-12)) and bool(np.all(quadrature<=1e-12)),'Gram consistency')
        diagnostic[axis]=dict(blocks=len(G),minimum_leading_diagonal=float(np.min(G[:,0,0])),
            minimum_second_pivot=float(np.min(pivot)),maximum_cholesky_relative=float(np.max(reconstruction)),
            maximum_quadrature_relative=float(np.max(quadrature)))
        factors.append(L)
    return C,Gr,Gz,factors[0],factors[1],diagnostic


def quadrature_and_statistics(f,rule,prior):
    n=f['n']; h=f['h']; Y=np.empty((3*n,4*n)); totals=np.zeros(9); minimum=math.inf
    for ir,(xr,wr) in enumerate(zip(*rule[3])):
        for iz,(xz,wz) in enumerate(zip(*rule[2])):
            clock(); rn=f['r']+xr*h/2.; zn=f['z']+xz*h/2.
            # Independent original annular-centered reconstruction: never C or F.
            q=f['q']+f['qr']*(rn-f['rc'])[:,None]+f['qz']*(zn-f['z'])[None,:]
            require(bool(np.all(np.isfinite(q))) and bool(np.all(q>=0.)),'node positivity')
            minimum=min(minimum,float(np.min(q)))
            Y[ir::3,iz::2]=np.sqrt(2.*math.pi*wr*h/2.*rn**3)[:,None]*q*math.sqrt(wz*h/2.)
            r=rn[:,None]; z=zn[None,:]; w=wr*wz*h*h/4.*r; density=w*q
            totals+=np.array([np.sum(density),np.sum(density*r),np.sum(density*z),
                np.sum(density*r*r),np.sum(density*r*z),np.sum(density*z*z),
                2.*math.pi*np.sum(w*q*q),math.pi*np.sum(density*r*r),
                2.*math.pi*np.sum(w*r*r*q*q)])
            COUNTERS['reference_node_cell_points']+=n*2*n; COUNTERS['Y_entries_written']+=n*2*n
    require(bool(np.all(np.isfinite(Y))) and totals[0]>0. and totals[8]>0.,'reference norms/assembly')
    mean=totals[1:3]/totals[0]
    cov=np.array([[totals[3],totals[4]],[totals[4],totals[5]]])/totals[0]-np.outer(mean,mean)
    record=dict(circulation=float(totals[0]),centroid=mean.tolist(),covariance=cov.tolist(),
        q_squared_integral=float(totals[6]),axial_impulse=float(totals[7]),
        vorticity_squared_integral=float(totals[8]),minimum_node=minimum,minimum_corner=f['minimum_corner'],
        saved_vorticity_squared_integral=f['statistics']['vorticity_squared_integral'])
    for key in ('circulation','centroid','covariance','q_squared_integral','axial_impulse','vorticity_squared_integral'):
        close(record[key],f['statistics'][key],'original reference statistics: '+key)
        close(record[key],prior[key],'T63 reference readback: '+key)
    COUNTERS['reference_integrals']+=1; COUNTERS['quadrature_matrices']+=1
    return Y,record


def decompose(X,label,C):
    clock(); norm_squared=float(np.sum(X*X)); norm=math.sqrt(norm_squared)
    require(math.isfinite(norm_squared) and norm_squared>0. and abs(norm_squared/C-1.)<=1e-10,'matrix norm')
    with phase(label+'/svd'):
        require(COUNTERS['svd_started']<4,'SVD cap'); COUNTERS['svd_started']+=1
        event('svd_invocation',label=label,shape=list(X.shape),ordinal=COUNTERS['svd_started'])
        U,s,Vh=np.linalg.svd(X,full_matrices=False)
        COUNTERS['svd_completed']+=1
    with phase(label+'/decomposition_checks'):
        k=min(X.shape)
        require(U.shape==(X.shape[0],k) and s.shape==(k,) and Vh.shape==(k,X.shape[1]),'SVD factor shapes')
        require(all(bool(np.all(np.isfinite(a))) for a in (U,s,Vh)) and bool(np.all(s>=0.))
                and bool(np.all(np.diff(s)<=0.)),'SVD finite/ordered spectrum')
        energy=math.fsum(float(value)**2 for value in s)
        tail=math.fsum(float(value)**2 for value in s[1:])
        require(energy>0. and abs(energy/C-1.)<=1e-10,'spectral energy')
        reconstruction=(U*s[None,:])@Vh; COUNTERS['residual_products']+=1
        residual=frobenius(X-reconstruction)
        left=U.T@U-np.eye(k); right=Vh@Vh.T-np.eye(k)
        COUNTERS['orthogonality_products']+=2
        eU=frobenius(left); eV=frobenius(right)
        require(residual/norm<=1e-10 and eU<=1e-10 and eV<=1e-10,'SVD residual/orthogonality')
        record=dict(shape=list(X.shape),singular_values=s.tolist(),norm_squared=norm_squared,
            spectral_energy=energy,tail_energy=tail,relative_error=math.sqrt(tail/energy),
            matrix_norm_relative_difference=abs(norm_squared/C-1.),spectral_norm_relative_difference=abs(energy/C-1.),
            residual_absolute=residual,residual_relative=residual/norm,orthogonality_U=eU,orthogonality_Vh=eV,
            largest_singular_value=float(s[0]),
            computed_operator_upper=float(s[0])*math.sqrt(1.+eU)*math.sqrt(1.+eV)+residual,
            operator_upper_is_certified=False)
        require(all(math.isfinite(v) for v in record.values() if type(v) is float),'nonfinite SVD diagnostic')
        event('decomposition_qualified',label=label,**record)
    return (U,s,Vh),record


def process(name,n,rule,prior):
    with phase(name+'/input_and_corners'):
        f=load_field(name,n)
    with phase(name+'/basis_and_grams'):
        C,Gr,Gz,Lr,Lz,grams=gram_and_basis(f,rule)
        event('grams_qualified',reference=name,checks=grams)
    with phase(name+'/independent_Y_and_statistics'):
        Y,reference=quadrature_and_statistics(f,rule,prior)
        event('reference_qualified',reference=name,statistics=reference,Y_shape=list(Y.shape))
    with phase(name+'/weighted_F_assembly'):
        # Lr[i,p,a] C[i,p,j,q] Lz[j,q,b] implements Lr.T @ C @ Lz.
        F=np.einsum('ipa,ipjq,jqb->iajb',Lr,C,Lz,optimize=True).reshape(2*n,4*n)
        require(F.shape==(2*n,4*n) and bool(np.all(np.isfinite(F))),'weighted matrix assembly')
        COUNTERS['weighted_matrices']+=1; event('weighted_matrix',reference=name,shape=list(F.shape))
    factors_F,record_F=decompose(F,name+'/F',reference['vorticity_squared_integral'])
    factors_Y,record_Y=decompose(Y,name+'/Y',reference['vorticity_squared_integral'])
    with phase(name+'/construction_agreement'):
        sF=factors_F[1]; sY=factors_Y[1]; scale=math.sqrt(reference['saved_vorticity_squared_integral'])
        difference=frobenius(sY-np.pad(sF,(0,n)))/scale
        extra=frobenius(sY[-n:])/scale
        error_difference=abs(record_F['relative_error']-record_Y['relative_error'])
        require(difference<=1e-10 and extra<=1e-10 and error_difference<=1e-10,'independent construction spectra')
        record=dict(reference=reference,gram_checks=grams,F=record_F,Y=record_Y,
            spectrum_difference_relative=difference,error_difference=error_difference,extra_spectrum_relative=extra)
        event('construction_agreement',reference=name,spectrum_difference_relative=difference,
              error_difference=error_difference,extra_spectrum_relative=extra)
    with phase(name+'/audit_bundle_write'):
        arrays=dict(F=F,Y=Y,U_F=factors_F[0],s_F=factors_F[1],Vh_F=factors_F[2],
            U_Y=factors_Y[0],s_Y=factors_Y[1],Vh_Y=factors_Y[2],C=C,Gr=Gr,Gz=Gz,Lr=Lr,Lz=Lz,
            r=f['r'],rc=f['rc'],z=f['z'])
        layout={key:dict(shape=list(value.shape),dtype=str(value.dtype),bytes=value.nbytes) for key,value in arrays.items()}
        array_bytes=sum(x['bytes'] for x in layout.values())
        path=LOCAL/f'{name}-audit.npz'
        event('audit_write_started',reference=name,path=path.relative_to(ROOT).as_posix(),array_bytes=array_bytes,arrays=layout)
        with path.open('xb') as stream:
            np.savez(stream,**arrays); stream.flush()
        artifact=dict(path=path.relative_to(ROOT).as_posix(),**identity(path,'output_bytes_hashed'),
                      array_bytes=array_bytes,arrays=layout)
        COUNTERS['audit_bundles']+=1; COUNTERS['audit_array_bytes']+=array_bytes
        COUNTERS['audit_file_bytes']+=artifact['bytes']
        record['audit_bundle']=artifact; event('audit_written',reference=name,artifact=artifact)
    return record


def measure():
    global np
    with phase('imports_and_input_hashes'):
        require(platform.python_version()=='3.12.14','Python version')
        import numpy as numpy
        np=numpy; require(np.__version__=='2.3.5','NumPy version')
        freeze(); CHECKS['frozen_inputs_before']=True
        t61=read_json(ROOT.parent/'t61-saved-output-qualification'/'result.json')
        require(t61['accepted_saved_evidence'] is True and t61['reference_qualified_full_window'] is True,'T61 qualification')
        t63=read_json(ROOT.parent/'t63-endpoint-capacity'/'result.json')
        require(t63['status']=='search_inconclusive' and t63['input_identities_unchanged'] is True
                and all(t63['checks'].values()),'T63 qualified input evidence')
    with phase('rules'):
        rule=rules()
    for name,n in (('S256',256),('S128',128)):
        CASES[name]=process(name,n,rule,t63['reference_checks'][name])
        event('case_completed',reference=name)
    CHECKS.update(reference_readback=True,gram_checks=True,matrix_norms=True,
                  svd_checks=True,construction_agreement=True)
    expected=dict(array_files_decoded=2,arrays_loaded=12,rules_constructed=2,rule_nodes=5,
        reference_integrals=2,reference_node_cell_points=983040,Y_entries_written=983040,corner_cell_points=655360,
        analytic_gram_blocks=1152,quadrature_gram_blocks=1152,cholesky_blocks=1152,
        cholesky_reconstruction_blocks=1152,gram_axis_node_evaluations=2688,
        basis_matrices=2,weighted_matrices=2,quadrature_matrices=2,svd_started=4,svd_completed=4,
        residual_products=4,orthogonality_products=8,audit_bundles=2,
        gaussian_field_evaluations=0,gaussian_fits=0,new_flow_trajectories=0)
    require(all(COUNTERS[k]==v for k,v in expected.items()),'fixed work accounting')
    CHECKS['fixed_work_accounting']=True
    primary=CASES['S256']['F']['relative_error']; sensitivity=CASES['S128']['F']['relative_error']
    difference=abs(primary-sensitivity); agreement=difference<=.001
    estimates={name:{kind:CASES[name][kind]['relative_error'] for kind in ('F','Y')} for name in CASES}
    above=all(value-.10>1e-8 for case in estimates.values() for value in case.values())
    classification=dict(primary_error=primary,sensitivity_error=sensitivity,absolute_difference=difference,
        sensitivity_agreement=agreement,all_estimates_above_gate=above,gate=.10,separation_buffer=1e-8,
        sensitivity_tolerance=.001,estimates=estimates,
        positions={name:{kind:('above' if value-.10>1e-8 else 'below' if .10-value>1e-8 else 'near')
                         for kind,value in case.items()} for name,case in estimates.items()})
    return dict(status='qualified_numerical_barrier_evidence' if above and agreement else 'qualified_no_separability_exclusion',
                classification=classification)


def main():
    global STREAM
    LOCAL.mkdir(exist_ok=True); failure=None; result=None
    with (LOCAL/'work.jsonl').open('x',encoding='utf-8',newline='\n') as STREAM:
        try:
            result=measure()
        except Exception as error:
            failure=dict(error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc(),active=ACTIVE)
        try:
            with phase('input_hashes_after'):
                for path,expected in BEFORE.items():
                    require(identity(path,'input_bytes_hashed_after')==expected,'input changed: '+str(path))
            CHECKS['frozen_inputs_after']=True
        except Exception as error:
            CHECKS['frozen_inputs_after']=False
            failure=dict(error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc(),
                         active=ACTIVE,previous_failure=failure)
        if failure:
            result=dict(status='qualification_failure',classification=None,failure=failure)
        result.update(schema='t65-separability-measurement-v1',cases=CASES,checks=CHECKS,counters=COUNTERS,
            phases_seconds=PHASES,formal_exclusion=False,new_flow_trajectories=0,
            gaussian_field_evaluations=0,gaussian_fits=0,
            prior_scientific_child_seconds=1978.636870399816,prior_evidence_qualification_seconds=.9663960000034422,
            input_identities_unchanged=CHECKS.get('frozen_inputs_before',False) and CHECKS.get('frozen_inputs_after',False),
            input_identities=[dict(path=path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else str(path),**value)
                              for path,value in BEFORE.items()],
            python=platform.python_version(),numpy=np.__version__ if np is not None else None,
            executable=str(Path(sys.executable).resolve()),
            created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            child_elapsed_before_result_write_seconds=time.perf_counter()-START)
        if failure: write_json(LOCAL/'failure.json',result)
        event('terminal',status=result['status'])
        write_json(ROOT/'result.json',result)
    STREAM=None
    print(json.dumps(dict(status=result['status'],formal_exclusion=False)),flush=True)
    return 2 if failure else 0


if __name__=='__main__':
    raise SystemExit(main())
