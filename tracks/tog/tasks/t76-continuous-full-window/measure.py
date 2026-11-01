"""T76 explicit T71 worker fork: ordinary polishing, then sealed reference scoring."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
import traceback

START=time.perf_counter()
DEADLINE=time.perf_counter_ns()+180_000_000_000
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
LOCAL=ROOT/'local'
PREVIOUS=ROOT.parent/'t70-causal-projector-qualification'
SCORER=ROOT.parent/'t71-causal-full-window'/'scorer.py'
NAMES=['frozen_identity_runtime','rules_and_startup_regression','complete_causal_paths_and_counts',
       'path_and_checkpoint_evaluator','continuous_polishing_and_fallback','reference_eligibility_and_score_integration',
       'time_comparison_integration_and_moments','complete_work_accounting','final_identity_preservation']
ORDERS=[2,3,6,8,12,16,64,96,128,192,256]
np=None
STREAM=None
C=dict(rule_count=0,rule_nodes=0,rule_eigh_calls=0,root_input_files_hashed_before=0,
       root_input_files_hashed_after=0,root_input_bytes_hashed_before=0,
       root_input_bytes_hashed_after=0,root_journal_events=0,root_journal_bytes=0,
       new_arrays_saved=0)
BEFORE={}
PATHS=[]
SEARCHES=[]
POLISHES=[]
CHECKS=[]
PHASES={}
DETAILS={}
ACTIVE='initialization'
PHYSICS=None
SEALED=False
EXPECTED=dict(field_calls=0,field_points=0,field_component_points=0,field_heat_nodes=0,
              field_heat_points=0,field_ordered_points=0,extra_cross_calls=0,
              extra_cross_pairs=0,extra_cross_nodes=0,search_cross_pairs=0,search_cross_nodes=0)


class Stall(Exception):
    pass


def require(ok,message):
    if not ok: raise ValueError(message)


def clock():
    if time.perf_counter_ns()>=DEADLINE: raise TimeoutError('T76 fixed child deadline')


def charge(key,n=1):
    C[key]=C.get(key,0)+int(n)


def emit(kind,data):
    clock()
    elapsed=time.perf_counter()-START
    event=dict(data)
    event['kind']=kind
    event.setdefault('elapsed_seconds',elapsed)
    event['journal_elapsed_seconds']=elapsed
    line=json.dumps(event,allow_nan=False)+'\n'
    charge('root_journal_events')
    charge('root_journal_bytes',len(line.encode('utf-8')))
    STREAM.write(line)
    STREAM.flush()


@contextmanager
def phase(name):
    global ACTIVE
    ACTIVE=name
    started=time.perf_counter()
    emit('phase_started',dict(name=name))
    try: yield
    finally:
        PHASES[name]=time.perf_counter()-started
        emit('phase_finished',dict(name=name,seconds=PHASES[name]))


def identity(path,suffix):
    require(path.suffix.lower() not in ('.npz','.npy'),'nonarray identity only before seal')
    size=0
    digest=hashlib.sha256()
    with path.open('rb') as f:
        while block:=f.read(1024*1024):
            clock();digest.update(block);size+=len(block)
    charge('root_input_files_hashed_'+suffix)
    charge('root_input_bytes_hashed_'+suffix,size)
    return dict(bytes=size,sha256=digest.hexdigest())


def read_json(path):
    def reject(value): raise ValueError('nonfinite JSON '+value)
    return json.loads(path.read_bytes(),parse_constant=reject)


def write_json(path,value):
    charge('root_json_write_attempts')
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def import_frozen(name,path):
    require(path.resolve() in BEFORE,'unfrozen helper')
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    charge('root_scientific_helpers_loaded')
    return mod


def qualification(name,passed,details):
    require(name in NAMES and name not in [x['name'] for x in CHECKS],'unique category')
    item=dict(name=name,passed=bool(passed),details=details)
    CHECKS.append(item);emit('qualification',item)


class Compare:
    def __init__(self):
        self.calls=0;self.values=0;self.maximum_absolute_difference=0.
        self.maximum_tolerance_ratio=0.;self.worst_label=None;self.failures=[]

    def close(self,a,b,label,score=False,atol=None):
        a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float)
        require(a.shape==b.shape,'shape mismatch '+label)
        self.calls+=1;self.values+=int(a.size)
        require(bool(np.all(np.isfinite(a))) and bool(np.all(np.isfinite(b))),'nonfinite '+label)
        delta=np.abs(a-b)
        limit=atol if atol is not None else 1e-8 if score else 1e-10+1e-9*np.maximum(np.abs(a),np.abs(b))
        absolute=float(np.max(delta));ratio=float(np.max(delta/limit))
        self.maximum_absolute_difference=max(self.maximum_absolute_difference,absolute)
        if ratio>self.maximum_tolerance_ratio:self.maximum_tolerance_ratio,self.worst_label=ratio,label
        if ratio>1:self.failures.append(dict(label=label,absolute=absolute,tolerance_ratio=ratio))

    def condition(self,passed,label):
        self.calls+=1
        if not passed:self.failures.append(dict(label=label))

    def record(self):
        return dict(passed=not self.failures,comparison_calls=self.calls,compared_values=self.values,
            maximum_absolute_difference=self.maximum_absolute_difference,
            maximum_tolerance_ratio=self.maximum_tolerance_ratio,worst_label=self.worst_label,
            failures=self.failures)

    def ensure(self,label):
        require(not self.failures,label+': '+str(self.failures[:3]))


def gram(a,b):
    charge('root_gram_calls')
    return PHYSICS.gram(a,b)


def norm(state):
    a,b=state['geometry'];eta=state['eta']
    return state['Gamma']**2*math.fsum(((1-eta)**2*gram(a,a),
        2*eta*(1-eta)*gram(a,b),eta*eta*gram(b,b)))


def gaussian(g,grid):
    sr,sz,z=g
    charge('root_gaussian_component_calls')
    charge('root_gaussian_component_points',grid['r'].size)
    charge('root_exp_evaluations',grid['r'].size)
    return np.exp(-grid['r']**2/(2*sr*sr)-(grid['z']-z)**2/(2*sz*sz))/(sr*sr*math.sqrt(2*math.pi)*sz)


def integral(array,grid):
    charge('root_direct_reductions')
    charge('root_direct_reduction_points',array.size)
    value=float(np.sum(grid['W']*array))
    require(math.isfinite(value),'nonfinite integral')
    return value


def physical_components(state):
    return int(state['eta']<1)+int(state['eta']>0)


def field(state,grid,order):
    k=physical_components(state);n=int(grid['r'].size)
    EXPECTED['field_calls']+=1;EXPECTED['field_points']+=n
    EXPECTED['field_component_points']+=k*n
    EXPECTED['field_heat_nodes']+=k*order
    EXPECTED['field_heat_points']+=k*n*order
    EXPECTED['field_ordered_points']+=k*k*n
    return PHYSICS.field(state,grid['r'],grid['z'],order)


def cross(state,g,order):
    k=physical_components(state)
    EXPECTED['extra_cross_calls']+=1;EXPECTED['extra_cross_pairs']+=k*k
    EXPECTED['extra_cross_nodes']+=k*k*order
    return PHYSICS.cross(state,g,order)


def moment_record(state,checks,label):
    charge('root_moment_records')
    m=PHYSICS.moments(state)
    checks.condition(state['Gamma']>0 and 0<=state['eta']<=1 and
        all(g[0]>0 and g[1]>0 for g in state['geometry']),label+' positive state')
    checks.close(m['between']['centroid'],m['raw']['centroid'],label+' centroid routes')
    checks.close(m['between']['covariance'],m['raw']['covariance'],label+' covariance routes')
    cov=m['between']['covariance']
    checks.condition(math.isfinite(m['Gamma']) and math.isfinite(m['I_z']) and m['I_z']>0 and
        cov[0][0]>0 and cov[1][1]>0 and cov[0][0]*cov[1][1]-cov[0][1]**2>0,label+' positive moments')
    checks.ensure(label)
    return m


def check_field_sum(f,checks,label):
    pairs=np.zeros_like(f['F'])
    for item in f['ordered_Fij']:pairs+=item['value']
    checks.close(pairs,f['F'],label+' Fij sum')


def target_cache(current,h,grids,checks,label):
    """Three paid current-state routes; reuse only within this Euler target."""
    current_norm=norm(current)
    routes=[];base=None
    for key,order in (('D12-64x128',128),('D12-64x128',256),('D12-96x192',256)):
        grid=grids[key];f=field(current,grid,order)
        tag=label+' '+key+' '+str(order)
        check_field_sum(f,checks,tag)
        qnorm=integral(f['q']**2,grid);Fnorm=integral(f['F']**2,grid)
        checks.close(qnorm,current_norm,tag+' current norm')
        if base is None:base=f
        elif key=='D12-64x128':
            for name in ('q','qr','qz','phi','phi_r','phi_z','ur','uz','F'):
                checks.close(f[name],base[name],tag+' field heat '+name)
        y=f['q']+h*f['F']
        Ctarget=integral(y*y,grid);N0=integral((y-f['q'])**2,grid)
        require(Ctarget>0 and Fnorm>0 and N0>=0,'positive finite Euler target scales')
        routes.append(dict(grid_name=key,order=order,grid=grid,field=f,y=y,C=Ctarget,
            N_unchanged=N0,S=h*h*Fnorm,Fnorm=Fnorm,qnorm=qnorm,current_norm=current_norm))
    for route in routes[1:]:
        for name in ('qnorm','Fnorm','C','N_unchanged'):
            checks.close(route[name],routes[0][name],label+' target spatial/heat '+name)
    checks.ensure(label+' target cache')
    charge('root_target_caches')
    emit('target_cache_prepared',dict(label=label,current_state=current,
        routes=[{k:r[k] for k in ('grid_name','order','C','N_unchanged','S','Fnorm','qnorm','current_norm')} for r in routes]))
    return routes


def step_confirmation(current,selected,search,h,caches,checks,label,role,expected_J=None):
    """Independent seed or proposed-final qualification on the same paid target."""
    current_norm,selected_norm=caches[0]['current_norm'],norm(selected)
    grid=caches[0]['grid']
    probes=[gaussian(g,grid) for g in selected['geometry']]
    model=selected['Gamma']*((1-selected['eta'])*probes[0]+selected['eta']*probes[1])
    qcross=[current['Gamma']*math.fsum(((1-current['eta'])*gram(current['geometry'][0],g),
                                     current['eta']*gram(current['geometry'][1],g)))
            for g in selected['geometry']]
    heat_cross={order:[cross(current,g,order) for g in selected['geometry']] for order in (128,256)}
    for slot in range(2):
        checks.close(heat_cross[128][slot]['total'],heat_cross[256][slot]['total'],label+' cross heat '+str(slot))
    routes=[]
    for cached in caches[:2]:
        order=cached['order'];f=cached['field'];y=cached['y']
        model_norm=integral(model**2,grid)
        checks.close(model_norm,selected_norm,label+' selected norm '+str(order))
        Ctarget,N0=cached['C'],cached['N_unchanged']
        bs=[]
        for slot,probe in enumerate(probes):
            packet=heat_cross[order][slot]
            checks.close(integral(f['F']*probe,grid),packet['total'],label+' F direct '+str((order,slot)))
            require(len(f['ordered_Fij'])==len(packet['ordered_pairs']),'ordered pair count')
            for numeric,analytic in zip(f['ordered_Fij'],packet['ordered_pairs']):
                require((numeric['i'],numeric['j'])==(analytic['i'],analytic['j']),'pair identity')
                checks.close(integral(numeric['value']*probe,grid),analytic['value'],
                             label+' ordered direct '+str((order,slot,numeric['i'],numeric['j'])))
            b=qcross[slot]+h*packet['total'];bs.append(b)
            checks.close(integral(y*probe,grid),b,label+' target cross '+str((order,slot)))
        B=math.fsum(((1-selected['eta'])*bs[0],selected['eta']*bs[1]))
        J=2*selected['Gamma']*B-selected_norm
        if expected_J is not None:
            checks.close(J,expected_J,label+' retained search J '+str(order))
        elif routes:
            checks.close(J,routes[0]['J'],label+' independent final J heat')
        N=integral((y-model)**2,grid)
        require(N>=0,'nonnegative direct candidate residual')
        checks.condition(Ctarget-J>=0 and Ctarget-search['control']['J']>=0,label+' no subtraction clipping')
        checks.close(N,Ctarget-J,label+' C-J '+str(order))
        checks.close(N0,Ctarget-search['control']['J'],label+' unchanged C-J128 '+str(order))
        checks.close(N0-N,J-search['control']['J'],label+' direct improvement '+str(order))
        routes.append(dict(grid=cached['grid_name'],order=order,C=Ctarget,N=N,N_unchanged=N0,J=J,
            S=cached['S'],model_norm=model_norm,
            control_J128=search['control']['J'],relative_target_error=math.sqrt(N/Ctarget),
            unchanged_relative_target_error=math.sqrt(N0/Ctarget)))
    checks.close(routes[0]['relative_target_error'],routes[1]['relative_target_error'],label+' target heat score',score=True)
    high=caches[2];grid=high['grid']
    high_probes=[gaussian(g,grid) for g in selected['geometry']]
    high_model=selected['Gamma']*((1-selected['eta'])*high_probes[0]+selected['eta']*high_probes[1])
    high_norm=integral(high_model**2,grid)
    high_N=integral((high['y']-high_model)**2,grid)
    require(high_N>=0,'nonnegative high-route candidate residual')
    high_score=math.sqrt(high_N/high['C'])
    checks.close(high_norm,selected_norm,label+' high selected full norm')
    checks.close(high_N,routes[0]['N'],label+' high direct residual')
    checks.close(high_score,routes[0]['relative_target_error'],label+' high target score',score=True)
    # This high route is a direct residual control; its J is explicitly C-N,
    # distinct from the two independently reconstructed low-route analytic Js.
    routes.append(dict(grid=high['grid_name'],order=high['order'],C=high['C'],N=high_N,
        N_unchanged=high['N_unchanged'],S=high['S'],model_norm=high_norm,
        J=high['C']-high_N,J_source='direct_C_minus_N',control_J128=search['control']['J'],
        relative_target_error=high_score,unchanged_relative_target_error=math.sqrt(high['N_unchanged']/high['C'])))
    checks.ensure(label)
    packet=dict(role=role,state=selected,routes=routes,selected_cross=heat_cross,
        current_norm=current_norm,selected_norm=selected_norm,
        expected_search_J=expected_J,independent_J128=routes[0]['J'])
    emit('candidate_confirmation',dict(label=label,**packet))
    charge('root_candidate_confirmations');charge('root_'+role+'_confirmations')
    return packet


def select_final(seed,proposed,seed_confirmation,proposed_confirmation,h,label):
    changed=proposed!=seed
    records=[]
    for initial,final in zip(seed_confirmation['routes'],proposed_confirmation['routes']):
        require((initial['grid'],initial['order'])==(final['grid'],final['order']),'selection route identity')
        gain=initial['N']-final['N']
        floor=1e-10*initial['S']+64*np.finfo(float).eps*initial['N']
        require(math.isfinite(gain) and math.isfinite(floor) and floor>=0,'finite selection gain')
        records.append(dict(grid=initial['grid'],order=initial['order'],E_seed=initial['N'],
            E_proposed=final['N'],S=initial['S'],gain=gain,resolution_floor=floor,
            exceeds_floor=bool(gain>floor)))
    gains=[r['gain'] for r in records]
    minimum,maximum=min(gains),max(gains)
    resolved=minimum>10*(maximum-minimum)
    accepted=changed and all(r['exceeds_floor'] for r in records) and resolved
    chosen=proposed if accepted else seed
    confirmation=proposed_confirmation if accepted else seed_confirmation
    selection=dict(proposed_changed=changed,accepted_polish=bool(accepted),
        reason='resolved_strict_gain' if accepted else 'seed_unchanged' if not changed else 'unresolved_or_nonimproving_final_gain',
        route_gains=records,minimum_gain=minimum,maximum_gain=maximum,
        gain_spread=maximum-minimum,resolved_gain=bool(resolved),
        retained_seed_exactly=not accepted,selected_state=chosen,
        selected_J128=confirmation['independent_J128'],final_confirmation_source='proposed' if accepted else 'seed')
    emit('final_selection',dict(label=label,**selection))
    charge('root_final_selections');charge('root_polish_accepted' if accepted else 'root_seed_retained')
    return chosen,confirmation,selection


def validate_candidate(state,bounds):
    charge('root_candidate_state_checks')
    require(isinstance(state,dict) and len(state['geometry'])==2,'candidate mixture structure')
    require(math.isfinite(state['Gamma']) and state['Gamma']>0 and math.isfinite(state['eta'])
        and 0<=state['eta']<=1,'positive finite candidate circulation')
    for g in state['geometry']:
        require(len(g)==3 and all(math.isfinite(x) for x in g),'finite candidate geometry')
        require(g[0]>0 and g[1]>0 and all(lo<=x<=hi for x,(lo,hi) in zip(g,bounds)),
            'candidate respects frozen search bounds')


def initialize(manifest_path):
    manifest=read_json(manifest_path)
    fixed=dict(schema='t76-continuous-full-window-freeze-v1',expected_python='3.12.14',expected_numpy='2.3.5',
        child_timeout_seconds=180,observed_peak_working_set_limit_bytes=536870912,
        maximum_scientific_child_invocations=1,required_available_physical_bytes=1073741824,
        memory_sample_interval_seconds=.25,step_sizes=[.0625,.03125],steps_per_path=[16,32],
        score_times=[0.,.25,.5,.75,1.],expected_rule_orders=ORDERS,expected_rule_nodes=783,
        expected_rule_eigh_calls=11,expected_check_names=NAMES,
        prior_scientific_child_seconds=2018.39971949975)
    require(all(manifest.get(k)==v for k,v in fixed.items()),'frozen contract')
    for item in manifest['inputs']:
        rel=item['path']
        require(isinstance(rel,str) and ':' not in rel and '\\' not in rel and
            not rel.startswith('/') and all(x not in ('','.','..') for x in rel.split('/')),'contained input')
        path=(REPO/rel).resolve()
        require(path.is_relative_to(REPO) and path not in BEFORE and path.suffix not in ('.npz','.npy'),'nonarray unique input')
        BEFORE[path]={k:item[k] for k in ('bytes','sha256')}
    exe=Path(sys.executable).resolve()
    require(exe==Path(manifest['executable']['path']).resolve(),'runtime path')
    BEFORE[exe]={k:manifest['executable'][k] for k in ('bytes','sha256')}
    BEFORE[manifest_path.resolve()]=identity(manifest_path,'before')
    for path,value in BEFORE.items():
        if path!=manifest_path.resolve():require(identity(path,'before')==value,'input changed '+str(path))
    return manifest


def main(manifest_path):
    global np,PHYSICS,SEALED
    with phase('identity_runtime'):
        manifest=initialize(manifest_path)
        thread_environment={key:os.environ.get(key) for key in
            ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
        require(all(value=='1' for value in thread_environment.values()),'four frozen single-thread environment settings')
        import numpy as numerical_library
        np=numerical_library
        runtime=dict(python=platform.python_version(),numpy=np.__version__,executable=str(Path(sys.executable).resolve()),
            thread_environment=thread_environment)
        require(runtime['python']=='3.12.14' and runtime['numpy']=='2.3.5','runtime versions')
        physics=import_frozen('t76_physics',PREVIOUS/'physics.py')
        search=import_frozen('t76_search',PREVIOUS/'search.py')
        scorer=import_frozen('t76_scorer',SCORER)
        polish=import_frozen('t76_polish',ROOT/'polish.py')
        for key in polish.COUNTER_KEYS:C.setdefault(key,0)
        DETAILS['runtime']=runtime
        qualification(NAMES[0],True,dict(runtime=runtime,frozen_nonarray_files=len(BEFORE)))
    rulechecks,pathchecks=Compare(),Compare()
    with phase('rules'):
        rules={};rule_records=[]
        for n in ORDERS:
            clock()
            k=np.arange(1,n,dtype=float);off=k/np.sqrt(4*k*k-1)
            x,vec=np.linalg.eigh(np.diag(off,1)+np.diag(off,-1));w=2*vec[0,:]**2
            charge('rule_count');charge('rule_nodes',n);charge('rule_eigh_calls')
            rulechecks.condition(bool(np.all(np.isfinite(x)) and np.all(np.isfinite(w)) and
                np.all(np.diff(x)>0) and np.all(np.abs(x)<1) and np.all(w>0)),'finite rule '+str(n))
            rulechecks.close(x,-x[::-1],'node symmetry '+str(n),atol=1e-12)
            rulechecks.close(w,w[::-1],'weight symmetry '+str(n),atol=1e-12)
            rulechecks.close(float(np.sum(w)),2.,'weight sum '+str(n),atol=1e-12)
            rules[n]=(x,w)
            record=dict(order=n,weight_sum=float(np.sum(w)),node_symmetry=float(np.max(np.abs(x+x[::-1]))),
                        weight_symmetry=float(np.max(np.abs(w-w[::-1]))))
            rule_records.append(record);emit('rule_constructed',record)
        rulechecks.ensure('rules')
        DETAILS['rules']=rule_records
        PHYSICS=physics.Physics(np,rules,C,emit)
        grids={}
        for radius in (8,12):
            for nr,nz in ((64,128),(96,192)):
                xr,wr=rules[nr];xz,wz=rules[nz]
                rr,zz=np.meshgrid(radius*(xr+1)/2,radius*xz,indexing='ij')
                W=2*math.pi*rr**3*(radius*wr[:,None]/2)*(radius*wz[None,:])
                grids[f'D{radius}-{nr}x{nz}']=dict(r=rr.ravel(),z=zz.ravel(),W=W.ravel())
                charge('root_spatial_grids');charge('root_spatial_grid_points',nr*nz)
    with phase('causal_predictions'):
        for h,nsteps in ((.0625,16),(.03125,32)):
            state=dict(Gamma=1.5*math.sqrt(2*math.pi),eta=0.,geometry=[[1.,1.,0.],[1.,1.,0.]])
            initial_moments=moment_record(state,pathchecks,f'initial {h}')
            path=dict(h=h,completed_steps=0,steps=[dict(step=0,time=0.,state=state,moments=initial_moments)])
            PATHS.append(path)
            emit('path_started',dict(h=h,steps=nsteps,initial_state=state))
            for index in range(1,nsteps+1):
                clock();require(not SEALED,'no search after seal')
                emit('step_started',dict(h=h,step=index,time_before=(index-1)*h,current_state=state))
                found=search.search_one(state,h,PHYSICS,emit,C,DEADLINE)
                SEARCHES.append(dict(path_h=h,step=index,search=found))
                k=len(found['active_components'])
                EXPECTED['search_cross_pairs']+=found['counters']['search_cross_calls']*k*k
                EXPECTED['search_cross_nodes']+=found['counters']['search_cross_calls']*k*k*128
                seed=found['selected_state'];label=f'{h}/{index}'
                if seed is None:
                    emit('bounded_search_stalled',dict(h=h,step=index,selected=None))
                    raise Stall('no positive finite-search seed for ordinary polishing')
                validate_candidate(seed,found['search_bounds'])
                caches=target_cache(state,h,grids,pathchecks,label)
                seed_confirmation=step_confirmation(state,seed,found,h,caches,pathchecks,label+' seed',
                    'seed',expected_J=found['selected_record']['J'])
                seed_moments=moment_record(seed,pathchecks,label+' seed moments')
                primary=caches[0]
                optimizer_cache=dict(primary['grid'],q=primary['field']['q'],F=primary['field']['F'],
                    y=primary['y'],S=primary['S'])
                polished=polish.polish_one(np,state,h,found,optimizer_cache,C,emit,DEADLINE)
                require(polished['seed_state']==seed,'polisher preserved exact seed')
                proposed=polished['selected_state']
                # Preserve returned optimizer work immediately, including a later evaluator failure.
                record=dict(path_h=h,step=index,seed_state=seed,seed_moments=seed_moments,
                    seed_confirmation=seed_confirmation,polish=polished)
                POLISHES.append(record)
                validate_candidate(proposed,found['search_bounds'])
                changed=proposed!=seed
                proposed_confirmation=(step_confirmation(state,proposed,found,h,caches,pathchecks,
                    label+' proposed','proposed') if changed else seed_confirmation)
                pathchecks.close(polished['audit']['seed_objective'],seed_confirmation['routes'][0]['N'],
                    label+' optimizer seed direct objective')
                pathchecks.close(polished['audit']['final_objective'],proposed_confirmation['routes'][0]['N'],
                    label+' optimizer returned direct objective')
                pathchecks.ensure(label+' optimizer objective integration')
                chosen,confirmation,selection=select_final(seed,proposed,seed_confirmation,proposed_confirmation,h,label)
                record.update(proposed_confirmation=proposed_confirmation,selection=selection,
                    final_confirmation=confirmation)
                if confirmation['independent_J128']<=found['control']['J']:
                    emit('bounded_search_stalled',dict(h=h,step=index,selected=chosen,
                        final_selection=selection,unchanged_J128=found['control']['J']))
                    raise Stall('qualified retained ordinary update does not improve unchanged state')
                moments=moment_record(chosen,pathchecks,f'moments {h}/{index}')
                state=chosen
                path['steps'].append(dict(step=index,time=index*h,state=state,moments=moments,
                    confirmation=confirmation,search_summary=found['summary'],selection=selection))
                path['completed_steps']=index
                charge('root_steps_confirmed')
                emit('step_completed',dict(h=h,step=index,time=index*h,state=state,moments=moments,
                    search_counters=found['counters'],polish_counters=polished['counters'],selection=selection))
                # Do not retain current-field arrays across targets.
                del caches,primary,optimizer_cache
            emit('path_completed',dict(h=h,completed_steps=nsteps))
    with phase('checkpoint_evaluator'):
        checkpoint_records=[]
        for path in PATHS:
            for index in range(0,path['completed_steps']+1,path['completed_steps']//4):
                item=path['steps'][index];state=item['state'];expected_norm=norm(state)
                routes=[]
                for key,grid in grids.items():
                    base=None
                    for order in (128,256):
                        f=field(state,grid,order)
                        label=f"checkpoint {path['h']} {item['time']} {key} {order}"
                        check_field_sum(f,pathchecks,label)
                        normq=integral(f['q']**2,grid);normF=integral(f['F']**2,grid)
                        pathchecks.close(normq,expected_norm,label+' full q norm')
                        if base is None:base=f
                        else:
                            for name in ('q','qr','qz','phi','phi_r','phi_z','ur','uz','F'):
                                pathchecks.close(f[name],base[name],label+' heat '+name)
                        routes.append(dict(grid=key,order=order,qnorm=normq,Fnorm=normF))
                        charge('root_checkpoint_routes')
                primary=next(x for x in routes if x['grid']=='D12-64x128' and x['order']==128)
                for route in routes:
                    pathchecks.close(route['Fnorm'],primary['Fnorm'],f'checkpoint F spatial/domain {path["h"]} {item["time"]} {route["grid"]} {route["order"]}')
                pathchecks.ensure('checkpoint field controls')
                packet=dict(h=path['h'],time=item['time'],routes=routes)
                checkpoint_records.append(packet);emit('checkpoint_evaluator',packet)
        DETAILS['checkpoint_evaluator']=checkpoint_records
    with phase('seal_predictions'):
        prediction_path=LOCAL/'predictions.json'
        write_json(prediction_path,dict(schema='t76-continuous-predictions-v1',paths=PATHS,
            completed_projection_steps=48,new_reference_trajectories=0,future_reference_predictor_inputs=False))
        seal=dict(path=prediction_path.relative_to(REPO).as_posix(),**identity(prediction_path,'prediction_seal'))
        SEALED=True
        emit('predictions_sealed',dict(prediction_seal=seal,completed_steps=48,paths=2))
        DETAILS['prediction_seal']=seal
    with phase('startup_regression'):
        saved=read_json(PREVIOUS/'result.json')
        require(saved['numerical_qualified'] and saved['verdict']=='ordinary_current_state_evaluator_and_first_steps_qualified','T70 eligible')
        for path,old in zip(PATHS,saved['steps']):
            require(path['h']==old['h'],'startup h')
            new=next(x for x in POLISHES if x['path_h']==path['h'] and x['step']==1)
            for name in ('Gamma','eta','geometry'):
                rulechecks.close(new['seed_state'][name],old['selected_state'][name],f'T70 seed state {path["h"]} {name}')
            found=next(x['search'] for x in SEARCHES if x['path_h']==path['h'] and x['step']==1)
            rulechecks.close(found['selected_record']['J'],old['selected_record']['J'],f'T70 selected J {path["h"]}')
            rulechecks.close(found['control']['J'],old['control']['J'],f'T70 control J {path["h"]}')
            for route in ('between','raw'):
                for name in ('centroid','covariance'):
                    rulechecks.close(new['seed_moments'][route][name],old['confirmation']['moments']['selected'][route][name],f'T70 seed moments {path["h"]} {route} {name}')
        rulechecks.ensure('startup regression')
        qualification(NAMES[1],True,rulechecks.record())
        complete=(len(PATHS)==2 and [p['completed_steps'] for p in PATHS]==[16,32] and len(SEARCHES)==48
            and all(x['search']['summary']['scheduled_search_completed'] and
                    not x['search']['summary']['early_success_shortcut'] for x in SEARCHES))
        require(complete,'incomplete causal paths')
        qualification(NAMES[2],complete,dict(paths=2,completed_steps=48,stored_states=50,
            future_reference_predictor_inputs=False,prediction_seal=seal))
        qualification(NAMES[3],True,pathchecks.record())
        polish_checks=dict(complete_attempts=len(POLISHES)==48,
            seed_preserved=all(x['seed_state']==x['polish']['seed_state'] for x in POLISHES),
            exact_seed_fallback=all(x['selection']['accepted_polish'] or
                x['selection']['selected_state']==x['seed_state'] for x in POLISHES),
            strict_resolved_accepted_gains=all(not x['selection']['accepted_polish'] or
                (x['selection']['resolved_gain'] and all(y['exceeds_floor'] for y in x['selection']['route_gains']))
                for x in POLISHES))
        require(all(polish_checks.values()),'continuous polishing and fallback qualification')
        qualification(NAMES[4],True,dict(predicates=polish_checks,attempts=len(POLISHES),
            accepted=C.get('root_polish_accepted',0),seed_retained=C.get('root_seed_retained',0)))
    with phase('sealed_reference_scoring'):
        scored=scorer.score_paths(np,rules,PHYSICS,C,emit,PATHS,manifest['reference_records'],
            REPO,manifest,DEADLINE,prediction_seal=seal)
        DETAILS['scoring']=scored
        require(scored['numerical_qualified'],'scorer numerical qualification')
        qualification(NAMES[5],True,dict(scoring_checks=scored['checks']))
        qualification(NAMES[6],True,dict(scoring_checks=scored['checks']))
    with phase('work_accounting'):
        expected=dict(rule_count=11,rule_nodes=783,rule_eigh_calls=11,root_steps_confirmed=48,
            root_checkpoint_routes=80,root_spatial_grids=4,root_spatial_grid_points=53248,
            phys_field_calls=EXPECTED['field_calls'],phys_field_spatial_points=EXPECTED['field_points'],
            phys_field_component_points=EXPECTED['field_component_points'],
            phys_field_heat_nodes=EXPECTED['field_heat_nodes'],
            phys_field_heat_integrand_points=EXPECTED['field_heat_points'],
            phys_field_ordered_pair_points=EXPECTED['field_ordered_points'],
            phys_cross_calls=C['search_cross_calls']+EXPECTED['extra_cross_calls'],
            phys_cross_ordered_pair_integrals=EXPECTED['search_cross_pairs']+EXPECTED['extra_cross_pairs'],
            phys_cross_integrand_points=EXPECTED['search_cross_nodes']+EXPECTED['extra_cross_nodes'],
            phys_moment_calls=C['root_moment_records'],phys_gram_calls=C['root_gram_calls']+C['search_current_gram_calls']+C['search_candidate_gram_calls'],
            root_target_caches=48,root_final_selections=48,root_seed_confirmations=48,
            root_moment_records=98,root_scientific_helpers_loaded=4,
            polish_invocations=48,polish_model_seed_calls=48,polish_model_canonical_calls=48,
            search_invocations=48,phys_instances=1,phys_rule_transforms=3,phys_rule_nodes_transformed=448)
        predicates={key:C.get(key,0)==value for key,value in expected.items()}
        changed=sum(x['polish']['selected_state']!=x['seed_state'] for x in POLISHES)
        confirmations=48+changed
        direct_reductions=736
        direct_points=8814592
        for original,polished_step in zip(SEARCHES,POLISHES):
            k=physical_components(original['search']['original_state'])
            count=1+int(polished_step['polish']['selected_state']!=polished_step['seed_state'])
            direct_reductions+=count*(14+4*k*k)
            direct_points+=count*((12+4*k*k)*8192+2*18432)
        predicates['224_actual_field_calls']=C['phys_field_calls']==224
        predicates['2736128_actual_field_points']=C['phys_field_spatial_points']==2736128
        predicates['candidate_confirmation_counts']=C['root_candidate_confirmations']==confirmations
        predicates['changed_candidate_counts']=C.get('root_proposed_confirmations',0)==changed
        predicates['extra_cross_calls']=EXPECTED['extra_cross_calls']==4*confirmations
        predicates['gaussian_confirmation_calls']=C['root_gaussian_component_calls']==4*confirmations
        predicates['gaussian_confirmation_points']=C['root_gaussian_component_points']==53248*confirmations
        predicates['gaussian_exp_points']=C['root_exp_evaluations']==C['root_gaussian_component_points']
        predicates['root_gram_work']=C['root_gram_calls']==174+7*confirmations
        predicates['direct_reduction_work']=C['root_direct_reductions']==direct_reductions
        predicates['direct_reduction_points']=C['root_direct_reduction_points']==direct_points
        predicates['candidate_state_checks']=C['root_candidate_state_checks']==96
        predicates['selections_partition']=C.get('root_polish_accepted',0)+C.get('root_seed_retained',0)==48
        predicates['437808_weight_control_attempt_cap']=C['search_weight_attempts']+C['search_control_attempts']<=437808
        predicates['all_count_values_nonnegative_integers']=all(type(x) is int and x>=0 for x in C.values())
        for key in search.COUNTER_KEYS:
            predicates['sum_'+key]=C.get(key,0)==sum(x['search']['counters'][key] for x in SEARCHES)
        polish_keys=set().union(*(set(x['polish']['counters']) for x in POLISHES))
        require(polish_keys==set(polish.COUNTER_KEYS),'declared polish counter keys')
        require(all(key.startswith('polish_') for key in polish_keys),'polish counter namespace')
        for key in polish_keys:
            predicates['sum_'+key]=C.get(key,0)==sum(x['polish']['counters'].get(key,0) for x in POLISHES)
        require(polish_keys=={key for key in C if key.startswith('polish_')},'complete polish accounting')
        predicates['polish_model_points']=C['polish_model_points']==8192*C['polish_model_calls']
        predicates['polish_model_component_points']=C['polish_model_component_points']==2*C['polish_model_points']
        predicates['polish_model_exp_values']=C['polish_model_exp_evaluations']==2*C['polish_model_points']
        predicates['polish_jacobian_calls']=C['polish_jacobian_calls']==C['polish_linearizations']
        predicates['polish_jacobian_columns']=C['polish_jacobian_column_values']==8*8192*C['polish_jacobian_calls']
        caps=dict(search_proposals=109440,search_component_evaluations=57552,
            phys_cross_calls=57936,phys_cross_ordered_pair_integrals=231744,
            phys_cross_integrand_points=29761536,phys_field_component_points=5472256,
            phys_field_heat_integrand_points=1163919360,phys_field_ordered_pair_points=10944512,
            phys_field_heat_nodes=92160,polish_linearizations=960,polish_svd_calls=8640,
            polish_trial_attempts=7680,polish_model_calls=7776)
        for key,value in caps.items():predicates['cap_'+key]=C.get(key,0)<=value
        require(all(predicates.values()),'work accounting '+str([k for k,v in predicates.items() if not v]))
        qualification(NAMES[7],True,dict(predicates=predicates,expected=expected,caps=caps,
            changed_candidates=changed,confirmation_count=confirmations,actual_field_and_cross_accounting=EXPECTED))
    with phase('identity_preservation'):
        preserved=True
        for path,value in BEFORE.items():preserved=(identity(path,'after')==value) and preserved
        require(identity(LOCAL/'predictions.json','prediction_after')=={k:seal[k] for k in ('bytes','sha256')},'predictions changed')
        preserved=preserved and C['root_input_files_hashed_before']==C['root_input_files_hashed_after']==len(BEFORE)
        preserved=preserved and C['root_input_bytes_hashed_before']==C['root_input_bytes_hashed_after']
        require(preserved,'frozen identity preservation')
        qualification(NAMES[8],True,dict(preserved=True,predictions_unchanged=True))
    reference_stable=scored['reference_sensitivity']['passed']
    time_stable=scored['time_sensitivity']['passed']
    physical=scored['physical_pass_both_references']
    verdict=('time_or_reference_sensitive_inconclusive' if not(reference_stable and time_stable) else
             'ordinary_full_window_joint_pass' if physical else 'ordinary_full_window_joint_miss')
    return dict(schema='t76-continuous-full-window-result-v1',verdict=verdict,numerical_qualified=True,
        runtime=runtime,checks=CHECKS,counters=C,paths=PATHS,searches=SEARCHES,polishes=POLISHES,details=DETAILS,
        scoring=scored,prediction_seal=seal,phases_seconds=PHASES,inputs_preserved=True,
        input_identities=[dict(path=path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else str(path),**value)
                          for path,value in BEFORE.items()],
        raw_identities=scored['raw_identities'],array_layouts=scored['array_layouts'],
        reference_sensitive=not reference_stable,time_sensitive=not time_stable,physical_pass=physical,
        full_task_validated=bool(physical and reference_stable and time_stable),
        new_method_claim=False,formal_error_certificate=False,formal_family_exclusion=False,
        future_reference_predictor_inputs=False,new_reference_trajectories=0,new_model_trajectories=2,
        prior_scientific_child_seconds=2018.39971949975,
        child_elapsed_before_result_write_seconds=time.perf_counter()-START)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path,default=ROOT/'input-manifest.json')
    args=parser.parse_args()
    LOCAL.mkdir(exist_ok=True)
    with (LOCAL/'journal.jsonl').open('x',encoding='utf-8',newline='\n') as STREAM:
        try: output=main(args.manifest)
        except BaseException as exc:
            output=dict(schema='t76-continuous-full-window-result-v1',
                verdict='stalled_bounded_search_inconclusive' if isinstance(exc,Stall) else 'failed_qualification_no_retry',
                numerical_qualified=False,error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc(),
                active_phase=ACTIVE,checks=CHECKS,counters=C,paths=PATHS,searches=SEARCHES,polishes=POLISHES,details=DETAILS,
                scoring_partial=getattr(exc,'partial_result',None),phases_seconds=PHASES,
                inputs_preserved=False,predictions_sealed=SEALED,
                child_elapsed_before_result_write_seconds=time.perf_counter()-START)
        write_json(LOCAL/'result.json',output)
    sys.exit(0 if output['numerical_qualified'] else 2)
