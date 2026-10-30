"""One frozen offline endpoint capacity measurement; no historical code import."""
import datetime
import hashlib
import itertools
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
LOCAL = ROOT / 'local'
OLD = ROOT.parent / 't60-full-window-gaussian-screen'
np = None
STREAM = None
BEFORE = {}
CHECKS = {}
PHASES = {}
PARTIAL = {}
ACTIVE = 'initialization'
COUNTERS = dict(input_bytes_hashed_before=0, input_bytes_hashed_after=0,
    array_files_decoded=0, arrays_loaded=0, rules_constructed=0, rule_nodes=0,
    polynomial_integrals=0, polynomial_node_cell_points=0, corner_cell_points=0,
    calibration_contractions=0, geometry_evaluations=0, contraction_calls=0,
    contraction_axis_exponent_evaluations=0, contraction_coefficient_cell_visits=0,
    rejected_coordinates=0, search_attempts=0, direct_integrals_started=0,
    direct_integrals_completed=0, direct_node_cell_points=0,
    direct_reference_reconstruction_points=0, direct_gaussian_field_points=0)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def clock():
    require(time.perf_counter()-START < 120., 'fixed child deadline exhausted')


def event(kind, **values):
    if STREAM is not None:
        STREAM.write(json.dumps(dict(kind=kind, elapsed_seconds=time.perf_counter()-START,
                                     **values), allow_nan=False)+'\n')
        STREAM.flush()


@contextmanager
def phase(name):
    global ACTIVE
    ACTIVE = name
    begin = time.perf_counter()
    try:
        clock()
        yield
    finally:
        elapsed = time.perf_counter()-begin
        PHASES[name] = PHASES.get(name, 0.)+elapsed
        event('phase', name=name, seconds=elapsed)


def identity(path, counter=None):
    h = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        while block := stream.read(1024*1024):
            clock(); size += len(block); h.update(block)
    if counter: COUNTERS[counter] += size
    return dict(bytes=size, sha256=h.hexdigest())


def read_json(path):
    require(path.resolve() in BEFORE, 'JSON is not frozen: '+str(path))
    def invalid(value): raise ValueError('nonfinite JSON: '+value)
    return json.loads(path.read_text(encoding='utf-8'), parse_constant=invalid)


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def close(actual, expected, label):
    a = np.asarray(actual); b = np.asarray(expected)
    require(a.shape == b.shape and bool(np.all(np.isfinite(a))) and
            bool(np.allclose(a, b, rtol=3e-11, atol=3e-14)), label)


def freeze():
    path = ROOT/'input-manifest.json'
    raw = path.read_bytes(); manifest = json.loads(raw)
    require(manifest['schema']=='t63-endpoint-capacity-freeze-v1', 'freeze schema')
    fixed=dict(expected_python='3.12.14',expected_numpy='2.3.5',
        maximum_scientific_child_invocations=1,child_timeout_seconds=120,
        observed_peak_working_set_limit_bytes=536870912,required_available_physical_bytes=1073741824,
        memory_sample_interval_seconds=.25,maximum_primary_geometry_evaluations=606,
        maximum_calibration_contractions=2,maximum_full_gaussian_rule_integrals=8,
        maximum_full_gaussian_node_cell_points=78643200,reference_polynomial_node_cell_points=983040,
        expected_1D_rule_orders=[3,2,8,6,16,12],expected_rule_nodes=47,
        prior_scientific_child_seconds=1976.6796338998247,T61_qualification_seconds=.9663960000034422,
        new_scientific_trajectories_permitted=0,preparation_scientific_invocations=0,T60_history_reclassified=False)
    require(all(manifest.get(key)==value for key,value in fixed.items()), 'fixed budget/scope contract')
    admitted = {}
    for item in manifest['inputs']:
        value = item['path']
        require(isinstance(value, str) and value and '\\' not in value and ':' not in value
                and not value.startswith('/') and all(x not in ('', '.', '..') for x in value.split('/')),
                'invalid frozen relative path')
        target = (REPO/value).resolve()
        require(target.is_relative_to(REPO) and target not in admitted, 'duplicate/escaping input')
        admitted[target] = {k:item[k] for k in ('bytes','sha256')}
    executable = Path(manifest['executable']['path']).resolve()
    require(executable==Path(sys.executable).resolve(), 'runtime executable')
    admitted[executable] = {k:manifest['executable'][k] for k in ('bytes','sha256')}
    for target, expected in admitted.items():
        actual = identity(target, 'input_bytes_hashed_before')
        require(actual==expected, 'frozen input mismatch: '+str(target)); BEFORE[target] = actual
    BEFORE[path.resolve()] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    COUNTERS['input_bytes_hashed_before'] += len(raw)
    return manifest


def rules():
    out = {}
    for n in (3,2,8,6,16,12):
        clock(); x,w = np.polynomial.legendre.leggauss(n)
        require(x.shape==w.shape==(n,) and bool(np.all(np.isfinite(x)))
                and bool(np.all(np.diff(x)>0.)) and bool(np.all(w>0.))
                and abs(float(np.sum(w))-2.)<=3e-14, 'Gaussian rule construction')
        out[n] = (x,w); COUNTERS['rules_constructed'] += 1; COUNTERS['rule_nodes'] += n
    return out


def load_field(name, n):
    metadata = read_json(OLD/'local'/f'{name}-snapshot-4.json')
    require((metadata['name'],metadata['index'],metadata['time'],metadata['nr'],metadata['nz'],metadata['R'])
            ==(name,4,1.,n,2*n,8.), 'endpoint metadata')
    h = metadata['h']; require(h==8./n, 'grid spacing')
    require(metadata['raw']['path']==f'{name}-snapshot-4.npz', 'exact snapshot basename')
    path = OLD/'local'/metadata['raw']['path']
    require(BEFORE[path.resolve()]==
            {k:metadata['raw'][k] for k in ('bytes','sha256')}, 'snapshot identity')
    with np.load(path, allow_pickle=False) as archive:
        f = {key:archive[key] for key in ('q','qr','qz','r','rc','z')}
    COUNTERS['array_files_decoded'] += 1; COUNTERS['arrays_loaded'] += 6
    for key,value in f.items():
        shape = (n,2*n) if key in ('q','qr','qz') else ((2*n,) if key=='z' else (n,))
        require(value.shape==shape and value.dtype==np.dtype('float64')
                and bool(np.all(np.isfinite(value))), 'array shape/type/finite: '+key)
    rf=np.arange(n+1)*h; zf=-8.+np.arange(2*n+1)*h
    area=(rf[1:]**2-rf[:-1]**2)/2.
    expected=dict(r=(rf[:-1]+rf[1:])/2.,z=(zf[:-1]+zf[1:])/2.,
                  rc=(rf[1:]**3-rf[:-1]**3)/(3.*area))
    for key,value in expected.items():
        require(bool(np.all(np.diff(f[key])>0.)) and np.array_equal(f[key],value), 'coordinate identity: '+key)
    require(bool(np.all(f['q']>=0.)), 'negative cell average')
    minimum = math.inf
    for radial in (rf[:-1],rf[1:]):
        for axial in (-h/2.,h/2.):
            clock(); corner=f['q']+f['qr']*(radial-f['rc'])[:,None]+f['qz']*axial
            COUNTERS['corner_cell_points'] += n*2*n
            minimum=min(minimum,float(np.min(corner)))
            require(bool(np.all(np.isfinite(corner))) and bool(np.all(corner>=0.)), 'PL corner positivity')
    f.update(name=name,n=n,h=h,statistics=metadata['statistics'],minimum_corner=minimum)
    return f


def samples(f, xr, xz):
    h=f['h']; rn=f['r']+xr*h/2.; zn=f['z']+xz*h/2.
    q=f['q']+f['qr']*(rn-f['rc'])[:,None]+f['qz']*(zn-f['z'])[None,:]
    require(bool(np.all(np.isfinite(q))) and bool(np.all(q>=0.)), 'PL node positivity')
    return rn,zn,q


def polynomial(f, rule):
    totals=np.zeros(9); points=f['q'].size
    for xr,wr in zip(*rule[3]):
        for xz,wz in zip(*rule[2]):
            clock(); rn,zn,q=samples(f,xr,xz)
            r=rn[:,None]; z=zn[None,:]; w=wr*wz*f['h']**2/4.*r; density=w*q
            totals+=np.array([np.sum(density),np.sum(density*r),np.sum(density*z),
                np.sum(density*r*r),np.sum(density*r*z),np.sum(density*z*z),
                2.*math.pi*np.sum(w*q*q),math.pi*np.sum(density*r*r),
                2.*math.pi*np.sum(w*r*r*q*q)])
            COUNTERS['polynomial_node_cell_points'] += points
    gamma=float(totals[0]); require(gamma>0. and totals[8]>0., 'positive polynomial norms')
    mean=totals[1:3]/gamma
    cov=np.array([[totals[3],totals[4]],[totals[4],totals[5]]])/gamma-np.outer(mean,mean)
    record=dict(circulation=gamma,centroid=mean.tolist(),covariance=cov.tolist(),
        q_squared_integral=float(totals[6]),axial_impulse=float(totals[7]),
        vorticity_squared_integral=float(totals[8]),minimum_corner=f['minimum_corner'])
    for key in ('circulation','centroid','covariance','q_squared_integral','axial_impulse','vorticity_squared_integral'):
        close(record[key],f['statistics'][key], 'polynomial readback: '+f['name']+'/'+key)
    f['C']=record['vorticity_squared_integral']
    COUNTERS['polynomial_integrals'] += 1
    event('reference_qualified', name=f['name'], statistics=record)
    return record


def moment_metrics(params, statistics, D0):
    sr,sz,z0=params['sr'],params['sz'],params['z0']
    mean=[math.sqrt(math.pi/2.)*sr,z0]; covariance=[[(4.-math.pi)/2.*sr*sr,0.],[0.,sz*sz]]
    shape=math.sqrt(math.fsum((covariance[i][j]-statistics['covariance'][i][j])**2
                             for i in range(2) for j in range(2)))/D0
    axial=abs(z0-statistics['centroid'][1])
    return dict(centroid=mean,covariance=covariance,axial_centroid_absolute=axial,
                covariance_relative=shape,axial_centroid_pass=axial<=.1,covariance_pass=shape<=.1)


def contraction(f, params, rule, fixed_amplitude=None, calibration=False):
    clock(); tick=time.perf_counter(); nr=f['n']; nz=2*nr; h=f['h']
    if calibration: COUNTERS['calibration_contractions'] += 1
    else:
        require(COUNTERS['geometry_evaluations']<606, 'geometry cap')
        COUNTERS['geometry_evaluations'] += 1
    COUNTERS['contraction_calls'] += 1
    xr,wr=rule[8]; xz,wz=rule[6]
    r=f['r'][:,None]+xr[None,:]*h/2.; z=f['z'][:,None]+xz[None,:]*h/2.
    fr=np.exp(-.5*(r/params['sr'])**2); fz=np.exp(-.5*((z-params['z0'])/params['sz'])**2)
    COUNTERS['contraction_axis_exponent_evaluations'] += 8*nr+6*nz
    rw=wr[None,:]*h/2.*r**3; zw=wz[None,:]*h/2.
    R3=np.sum(rw*fr,axis=1); Rc=np.sum(rw*(r-f['rc'][:,None])*fr,axis=1)
    Z0=np.sum(zw*fz,axis=1); Zc=np.sum(zw*(z-f['z'][:,None])*fz,axis=1)
    B=2.*math.pi*math.fsum((float(R3@(f['q']@Z0)),float(Rc@(f['qr']@Z0)),float(R3@(f['qz']@Zc))))
    M=2.*math.pi*float(np.sum(rw*fr*fr))*float(np.sum(zw*fz*fz)); C=f['C']
    COUNTERS['contraction_coefficient_cell_visits'] += 3*nr*nz
    require(all(math.isfinite(v) and v>0. for v in (B,M,C)), 'invalid contraction B/M/C')
    A=B/M if fixed_amplitude is None else fixed_amplitude
    numerator=C-B*B/M if fixed_amplitude is None else math.fsum((C,-2.*A*B,A*A*M))
    require(math.isfinite(A) and A>0. and math.isfinite(numerator) and numerator>=0., 'negative/invalid contracted residual')
    return dict(B=B,M=M,C=C,A=A,numerator=numerator,error_squared=numerator/C,
                relative_error=math.sqrt(numerator/C),seconds=time.perf_counter()-tick)


def direct(f, params, orders, rule, label):
    clock(); require(COUNTERS['direct_integrals_started']<8, 'direct integral cap')
    COUNTERS['direct_integrals_started'] += 1
    begin=time.perf_counter(); sums=[[],[],[],[]]; points=f['q'].size
    for xr,wr in zip(*rule[orders[0]]):
        for xz,wz in zip(*rule[orders[1]]):
            clock(); rn,zn,q=samples(f,xr,xz)
            COUNTERS['direct_reference_reconstruction_points'] += points
            qg=params['A']*np.exp(-.5*((rn[:,None]/params['sr'])**2+((zn[None,:]-params['z0'])/params['sz'])**2))
            COUNTERS['direct_gaussian_field_points'] += points
            require(bool(np.all(np.isfinite(qg))) and bool(np.all(qg>0.)), 'invalid Gaussian samples')
            weight=rn[:,None]*f['h']**2*wr*wz/4.; physical=2.*math.pi*rn[:,None]**2*weight
            sums[0].append(float(np.sum(physical*(qg-q)**2))); sums[1].append(float(np.sum(physical*q*q)))
            sums[2].append(float(np.sum(weight*qg))); sums[3].append(float(np.sum(physical*qg*qg)))
            COUNTERS['direct_node_cell_points'] += points
    numerator,denominator,gamma,omega2=(math.fsum(x) for x in sums)
    require(numerator>=0. and denominator>0., 'invalid direct norm')
    close(denominator,f['C'],'direct denominator')
    COUNTERS['direct_integrals_completed'] += 1
    record=dict(reference=f['name'],label=label,orders=list(orders),numerator=numerator,denominator=denominator,
        relative_error=math.sqrt(numerator/denominator),D8_circulation=gamma,D8_vorticity_squared=omega2,
        node_cell_points=points*orders[0]*orders[1],seconds=time.perf_counter()-begin)
    event('direct_score', **record)
    return record


def score_pair(f, params, rule, label):
    primary=direct(f,params,(8,6),rule,label); confirm=direct(f,params,(16,12),rule,label)
    difference=abs(primary['relative_error']-confirm['relative_error'])
    require(difference<=1e-6, label+' fixed rule disagreement')
    return dict(primary_8x6=primary,confirmation_16x12=confirm,rule_difference=difference)


def search(f, region, D0, rule):
    evaluated=[]; rejected=0
    def evaluate(coordinates, origin):
        nonlocal rejected
        clock(); COUNTERS['search_attempts'] += 1
        u,v,w=coordinates
        reason=None
        if u*u+v*v>1. or abs(w)>1.: reason='outside_normalized_domain'
        params=None; moments=None
        if reason is None:
            params=dict(sr=math.sqrt((region['a']+region['rho']*u)/region['gamma']),
                        sz=math.sqrt(region['d']+region['rho']*v),z0=region['mu_z']+.1*w)
            require(all(math.isfinite(x) for x in params.values()) and params['sr']>0. and params['sz']>0., 'invalid geometry')
            moments=moment_metrics(params,f['statistics'],D0)
            if not moments['axial_centroid_pass'] or not moments['covariance_pass']: reason='rounded_original_moment_gate'
        if reason:
            rejected+=1; COUNTERS['rejected_coordinates']+=1
            event('rejected_geometry',coordinates=list(coordinates),origin=origin,reason=reason,parameters=params,moments=moments)
            return None
        objective=contraction(f,params,rule); params['A']=objective['A']
        record=dict(index=len(evaluated),coordinates=list(coordinates),origin=origin,parameters=params,
                    moments=moments,contraction=objective)
        evaluated.append(record); event('geometry',**record)
        return record
    def key(record):
        return (record['contraction']['error_squared'],*record['coordinates'])
    center=evaluate((0.,0.,0.),'moment_center'); require(center is not None,'moment center ineligible')
    if center['contraction']['relative_error']<=.10:
        return center,dict(route='moment_center_shortcut',evaluated=len(evaluated),rejected=rejected,local_starts=[],cycles=[])
    grid=[]
    for u,v,w in itertools.product((-1.,-.5,0.,.5,1.),repeat=3):
        if u*u+v*v<=1.:
            record=evaluate((u,v,w),'grid')
            if record is not None: grid.append(record)
    require(len(grid)>=3,'fewer than three eligible grid starts')
    starts=sorted(grid,key=key)[:3]; cycles=[]
    for start_index,start in enumerate(starts):
        current=start; step=.25
        for cycle in range(30):
            if step<=2.**-10: break
            neighbors=[]
            for axis,sign in ((0,1),(0,-1),(1,1),(1,-1),(2,1),(2,-1)):
                coordinates=list(current['coordinates']); coordinates[axis]+=sign*step
                candidate=evaluate(tuple(coordinates),f'poll/{start_index}/{cycle}/{axis}/{sign}')
                if candidate is not None: neighbors.append(candidate)
            best=min(neighbors,key=key) if neighbors else None
            improved=best is not None and best['contraction']['error_squared']<current['contraction']['error_squared']
            used_step=step
            if improved: current=best
            else: step/=2.
            record=dict(start=start_index,cycle=cycle,step=used_step,next_step=step,improved=improved,current_index=current['index'])
            cycles.append(record); event('poll_cycle',**record)
    selected=min(evaluated,key=key)
    return selected,dict(route='fixed_grid_pattern',evaluated=len(evaluated),rejected=rejected,
        local_starts=[x['coordinates'] for x in starts],cycles=cycles)


def measure():
    global np
    with phase('imports_and_input_hashes'):
        require(platform.python_version()=='3.12.14','Python version')
        import numpy as numpy
        np=numpy; require(np.__version__=='2.3.5','NumPy version')
        manifest=freeze(); CHECKS['frozen_inputs_before']=True
        qualification=read_json(ROOT.parent/'t61-saved-output-qualification'/'result.json')
        require(qualification['accepted_saved_evidence'] is True and qualification['reference_qualified_full_window'] is True,
                'T61 reference qualification')
        old=read_json(OLD/'result.json')
        require({key:qualification['original_numerical_result'][key] for key in ('bytes','sha256')}
                ==BEFORE[(OLD/'result.json').resolve()], 'T61 accepted numerical-result identity')
        coefficient=read_json(ROOT.parent/'t54-scalar-verification'/'result.json')
        require(coefficient['status']=='consistent','T54 coefficient qualification')
        require(old['coefficient_input']==BEFORE[(ROOT.parent/'t54-scalar-verification'/'result.json').resolve()],
                'frozen original coefficient')
        speed=1.5*coefficient['closed_metrics']['beta_best_over_g0']
    with phase('rules_and_reference_qualification'):
        rule=rules(); fields={name:load_field(name,n) for name,n in (('S256',256),('S128',128))}
        reference={name:polynomial(f,rule) for name,f in fields.items()}
        initial=read_json(OLD/'local'/'S256.json')['snapshots'][0]['covariance']
        D0=old['ordinary_model_screen']['actual_initial_S256_covariance_frobenius_norm']
        require(math.isfinite(D0) and D0>0., 'original shape normalization')
        close(math.sqrt(math.fsum(x*x for row in initial for x in row)),D0,'initial covariance normalization')
        cov=fields['S256']['statistics']['covariance']; a,b,d=cov[0][0],cov[0][1],cov[1][1]
        rho2=(.1*D0)**2-2.*b*b; require(rho2>0. and a>.1*D0 and d>.1*D0,'compact positive geometry region')
        region=dict(a=a,b=b,d=d,D0=D0,rho=math.sqrt(rho2),gamma=(4.-math.pi)/2.,
                    mu_z=fields['S256']['statistics']['centroid'][1])
        PARTIAL.update(reference_checks=reference,region=region); CHECKS['reference_readback']=True
    with phase('calibration'):
        baseline=dict(A=1.5,sr=1.,sz=1.,z0=speed); calibration={}
        for name,f in fields.items():
            contracted=contraction(f,baseline,rule,fixed_amplitude=1.5,calibration=True)
            event('calibration_contraction',reference=name,parameters=baseline,contraction=contracted)
            scored=score_pair(f,baseline,rule,'calibration')
            stored=next(x for x in old['ordinary_model_screen']['scores'] if x['reference']==name and x['index']==4)
            for label in ('primary_8x6','confirmation_16x12'):
                require(abs(scored[label]['relative_error']-stored[label]['vorticity_relative'])<=1e-9, 'saved baseline score')
            require(abs(contracted['relative_error']-scored['primary_8x6']['relative_error'])<=1e-9,'calibration contraction disagreement')
            calibration[name]=dict(contraction=contracted,**scored); PARTIAL['calibration']=calibration
        CHECKS['calibration']=True
    with phase('selection'):
        selected,summary=search(fields['S256'],region,D0,rule)
        PARTIAL.update(selected=selected,search_summary=summary)
    with phase('selected_confirmation'):
        scores={}; params=selected['parameters']
        for name,f in fields.items():
            scored=score_pair(f,params,rule,'selected'); moments=moment_metrics(params,f['statistics'],D0)
            gamma=params['A']*params['sr']**2*math.sqrt(2.*math.pi)*params['sz']
            impulse=2.*math.pi*params['sr']**2*gamma
            physical=dict(vorticity_L2=scored['primary_8x6']['relative_error']<=.10,
                axial_centroid=moments['axial_centroid_pass'],covariance=moments['covariance_pass'])
            scores[name]=dict(**scored,moments=moments,physical_gates=physical,
                joint_pass=all(physical.values()),fullspace_circulation=gamma,fullspace_axial_impulse=impulse,
                circulation_relative_difference=gamma/f['statistics']['circulation']-1.,
                impulse_relative_difference=impulse/f['statistics']['axial_impulse']-1.,
                fullspace_vorticity_squared=math.pi**1.5*params['A']**2*params['sr']**4*params['sz'])
            PARTIAL['selected_scores']=scores
        difference=abs(selected['contraction']['relative_error']-scores['S256']['primary_8x6']['relative_error'])
        require(difference<=1e-9,'selected contraction disagreement')
        CHECKS['selected_score_qualification']=True
    geometries=COUNTERS['geometry_evaluations']
    require(1<=geometries<=606 and COUNTERS['calibration_contractions']==2
            and COUNTERS['array_files_decoded']==2 and COUNTERS['arrays_loaded']==12
            and COUNTERS['rules_constructed']==6 and COUNTERS['rule_nodes']==47
            and COUNTERS['polynomial_integrals']==2 and COUNTERS['polynomial_node_cell_points']==983040
            and COUNTERS['corner_cell_points']==655360
            and COUNTERS['contraction_calls']==geometries+2
            and COUNTERS['contraction_axis_exponent_evaluations']==5120*geometries+7680
            and COUNTERS['contraction_coefficient_cell_visits']==3*(131072*geometries+163840)
            and COUNTERS['search_attempts']==geometries+COUNTERS['rejected_coordinates']
            and COUNTERS['direct_integrals_started']==COUNTERS['direct_integrals_completed']==8
            and COUNTERS['direct_node_cell_points']==COUNTERS['direct_reference_reconstruction_points']
                ==COUNTERS['direct_gaussian_field_points']==78643200,
            'fixed work accounting')
    CHECKS['fixed_work_accounting']=True
    witness=scores['S256']['joint_pass']
    return dict(status='qualified_endpoint_witness' if witness else 'search_inconclusive',capacity_witness=witness,
        **PARTIAL,selected_contraction_direct_difference=difference,calibration_parameters=baseline,
        sensitivity_parameters_identical=True,prior_scientific_child_seconds=1976.6796338998247,
        prior_evidence_qualification_seconds=.9663960000034422,coefficient_refitted=False,new_flow_trajectories=0,
        offline_oracle=True,global_optimality_certified=False,formal_error_certificate=False,
        earlier_four_witnesses_reused_as_saved_observations=True)


def main():
    global STREAM
    LOCAL.mkdir(exist_ok=True)
    result=None; failure=None
    with (LOCAL/'search.jsonl').open('x',encoding='utf-8',newline='\n') as STREAM:
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
            failure=dict(error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc(),active=ACTIVE,
                         previous_failure=failure)
        if failure:
            result=dict(status='qualification_failure',capacity_witness=None,**PARTIAL,failure=failure,
                        prior_scientific_child_seconds=1976.6796338998247)
            write_json(LOCAL/'failure.json',dict(**result,counters=COUNTERS,phases_seconds=PHASES))
        result.update(schema='t63-endpoint-capacity-v1',checks=CHECKS,counters=COUNTERS,phases_seconds=PHASES,
            input_identities_unchanged=CHECKS.get('frozen_inputs_before',False) and CHECKS.get('frozen_inputs_after',False),
            python=platform.python_version(),
            numpy=np.__version__ if np is not None else None,executable=str(Path(sys.executable).resolve()),
            input_identities=[dict(path=path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else str(path),**value)
                              for path,value in BEFORE.items()],
            created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            child_elapsed_before_result_write_seconds=time.perf_counter()-START)
        event('terminal',status=result['status'],capacity_witness=result['capacity_witness'])
        write_json(ROOT/'result.json',result)
    STREAM=None
    print(json.dumps(dict(status=result['status'],capacity_witness=result['capacity_witness'])),flush=True)
    return 2 if failure else 0


if __name__=='__main__':
    raise SystemExit(main())
