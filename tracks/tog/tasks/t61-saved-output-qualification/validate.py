"""Independent standard-library qualification of frozen T60 saved evidence.

No numerical arrays or old program are loaded. NPZ files are streamed only for
hashes; all arithmetic below concerns recorded scalar measurements and gates.
"""
import datetime
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time
import traceback

START = time.perf_counter()
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
OLD = ROOT.parent / 't60-full-window-gaussian-screen'
LOCAL = OLD / 'local'
sys.path.insert(0, str(ROOT))
from path_contract import resolve_evidence

NAMES = ('S64', 'S128', 'S256', 'T128', 'D192', 'Q128')
TIMES = (0., .25, .5, .75, 1.)
CONFIGS = ((8.,64,.0025,32),(8.,128,.0025,32),(8.,256,.0025,32),
           (8.,128,.00125,32),(12.,192,.0025,32),(8.,128,.0025,64))
PAIRS = (('S64','S128','space'),('S128','S256','space'),('S128','T128','time'),
         ('S128','D192','domain'),('S128','Q128','angular'))
COUNTS = dict(elliptic_attempts=5630, elliptic_completed=5630, transport_stages=5600,
              completed_steps=2800, snapshots=30, completed_cases=6, new_CG_solves=0)
PHASES = ('rhs_seconds','forward_transform_seconds','factor_seconds','triangular_seconds',
          'inverse_transform_seconds','original_rhs_assembly_seconds','original_residual_seconds',
          'checked_solve_seconds')
ADMITTED = {}
BEFORE = {}
READ_PATHS = set()
NORMALIZED = []


def require(condition, message):
    if not condition:
        raise ValueError(message)


def deadline():
    require(time.perf_counter()-START < 60., 'fixed 60-second qualification budget exhausted')


def identity(path):
    digest = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        while block := stream.read(1024*1024):
            deadline(); digest.update(block); size += len(block)
    return dict(bytes=size, sha256=digest.hexdigest())


def ident_fields(value):
    require(type(value['bytes']) is int and value['bytes'] >= 0, 'invalid byte count')
    require(isinstance(value['sha256'],str) and len(value['sha256']) == 64
            and all(x in '0123456789abcdef' for x in value['sha256']), 'invalid SHA256')
    return {k:value[k] for k in ('bytes','sha256')}


def strict_json(raw):
    def unique(pairs):
        out = {}
        for key,value in pairs:
            require(key not in out, 'duplicate JSON key: '+key); out[key] = value
        return out
    def finite(text):
        x = float(text); require(math.isfinite(x), 'nonfinite JSON number'); return x
    def invalid(text):
        raise ValueError('invalid JSON constant: '+text)
    value = json.loads(raw, object_pairs_hook=unique, parse_float=finite, parse_constant=invalid)
    require(isinstance(value,dict), 'JSON record must be an object')
    return value


def checked(path):
    path = Path(path).resolve()
    require(path in ADMITTED, 'file absent from the T61 freeze: '+str(path))
    if path not in BEFORE:
        BEFORE[path] = identity(path)
        require(BEFORE[path] == ADMITTED[path], 'frozen identity mismatch: '+str(path))
    READ_PATHS.add(path)
    return BEFORE[path]


def document(path):
    expected = checked(path); raw = Path(path).read_bytes()
    require(dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) == expected, 'JSON changed during read')
    return strict_json(raw)


def lines(path):
    checked(path)
    with Path(path).open('rb') as stream:
        for raw in stream:
            deadline(); require(raw.strip(), 'blank JSONL record'); yield strict_json(raw)


def match(path, record):
    require(checked(path) == ident_fields(record), 'artifact linkage mismatch: '+str(path))


def close(a,b,label):
    require(type(a) in (int,float) and type(b) in (int,float)
            and math.isfinite(a) and math.isfinite(b), label+': invalid scalar')
    require(math.isclose(a,b,rel_tol=3e-11,abs_tol=3e-14), label+': scalar readback mismatch')


def norm(matrix):
    return math.sqrt(math.fsum(x*x for row in matrix for x in row))


def covariance_difference(a,b):
    return norm([[a[i][j]-b[i][j] for j in range(2)] for i in range(2)])


def evidence(record, logical):
    path = resolve_evidence(OLD,record['path'],logical)
    match(path,record)
    NORMALIZED.append(dict(supplied=record['path'],logical=logical,identity=checked(path)))
    return path


def relative_input(value):
    require(isinstance(value,str) and value and '\\' not in value and ':' not in value,
            'freeze input must be an unambiguous repository-relative POSIX path')
    require(not value.startswith('/') and all(x not in ('','..','.') for x in value.split('/')),
            'invalid freeze input path')
    path = (REPO/value).resolve()
    require(path.is_relative_to(REPO), 'freeze input escapes repository')
    return path


def reductions(comparisons, stored):
    require(len(stored) == 4, 'four nonzero-time reductions required')
    outcomes = []
    for i,record in enumerate(stored,1):
        coarse = comparisons[i]['vorticity_relative']; fine = comparisons[5+i]['vorticity_relative']
        require(record['time'] == TIMES[i], 'reduction time')
        close(record['coarse'],coarse,'coarse reduction'); close(record['fine'],fine,'fine reduction')
        waived = max(coarse,fine) <= 1e-8
        passed = waived or coarse >= 1.5*fine
        require(record['small_error_waiver'] is waived and record['passed'] is passed,'reduction predicate')
        if fine > 0.: close(record['ratio'],coarse/fine,'reduction ratio')
        else: require(record['ratio'] is None,'zero fine denominator')
        outcomes.append(passed)
    return all(outcomes)


def case_records(result):
    cases = result['cases']; require([x['name'] for x in cases] == list(NAMES),'case order')
    aggregates = dict(solves=0,stages=0,steps=0,snapshots=0)
    all_checkpoints = []; all_solves = []; summaries = []
    expected_raw = set()
    for case,config in zip(cases,CONFIGS):
        deadline(); name=case['name']; R,nr,dt,angular=config; steps=800 if name=='T128' else 400
        require(case == document(LOCAL/(name+'.json')), 'case metadata equality')
        require((case['R'],case['Z'],case['radial_cells'],case['axial_cells'],case['dt'],case['angular_order'])
                == (R,R,nr,2*nr,dt,angular), 'case configuration')
        close(case['h'],R/nr,'grid spacing')
        require(case['steps']==steps and case['transport_stages']==2*steps
                and case['elliptic_solves']==2*steps+5, 'case counts')
        require(case['method']==case['elliptic_method']=='ordinary_FFT_sine_Thomas','direct method')
        require(case['green_released_before_final_array_save'] is True,'Green lifetime declaration')
        for key,suffix in (('raw','.npz'),('log','-steps.jsonl')):
            require(case[key]['path']==name+suffix,'case basename'); match(LOCAL/(name+suffix),case[key])
        expected_raw.add(name+'.npz')
        statistics=case['snapshots']; require(len(statistics)==5 and len(case['checkpoint_records'])==5,'five snapshots')
        for i,(stat,cp) in enumerate(zip(statistics,case['checkpoint_records'])):
            step=i*(steps//4); stem=f'{name}-snapshot-{i}'
            require((stat['step'],stat['time'])==(step,TIMES[i]),'snapshot statistic time')
            require((cp['name'],cp['index'],cp['step'],cp['time'])==(name,i,step,TIMES[i]),'checkpoint tuple')
            require(cp['path']==stem+'.json' and cp['raw']['path']==stem+'.npz','checkpoint basename')
            match(LOCAL/cp['path'],cp); match(LOCAL/cp['raw']['path'],cp['raw'])
            saved=document(LOCAL/cp['path'])
            require(saved['schema']=='t60-partial-snapshot-v1' and saved['whole_task_qualified'] is False,'checkpoint semantics')
            require((saved['name'],saved['index'],saved['step'],saved['time'])==(name,i,step,TIMES[i]),'checkpoint metadata tuple')
            require((saved['R'],saved['nr'],saved['nz'],saved['dt'],saved['angular_order'])
                    ==(R,nr,2*nr,dt,angular),'checkpoint grid configuration')
            close(saved['h'],R/nr,'checkpoint spacing')
            require(saved['raw']==cp['raw'] and saved['statistics']==stat,'checkpoint statistics linkage')
            require(stat['circulation']>0. and stat['min_q']>=0. and stat['negative_cell_mass']==0.,'saved positivity')
            all_checkpoints.append(cp); expected_raw.add(stem+'.npz')
        logged=list(lines(LOCAL/case['log']['path']))
        expected=[('snapshot',0,None)]
        for step in range(steps):
            expected.extend((('stage',step,0),('stage',step,1),('step',step+1,None)))
            if (step+1) % (steps//4)==0: expected.append(('snapshot',step+1,None))
        require([(x['kind'],x['step'],x.get('stage')) for x in logged]==expected,'complete ordered stage schedule')
        solves=[x for x in logged if x['kind'] in ('stage','snapshot')]
        stages=[x for x in logged if x['kind']=='stage']; updates=[x for x in logged if x['kind']=='step']
        snapshots=[x for x in logged if x['kind']=='snapshot']
        for i,cp in enumerate(case['checkpoint_records']):
            saved=document(LOCAL/cp['path'])
            require(saved['current']=={k:v for k,v in snapshots[i].items() if k not in ('kind','step')},'snapshot flow log linkage')
        for flow in solves:
            solver=flow['solver']
            require(solver['method']=='ordinary_FFT_sine_Thomas' and solver['shape']==[nr,2*nr]
                    and solver['factor_reuse'] is False,'logged direct contract')
            require(solver['minimum_pivot']>0. and solver['minimum_eigenvalue']>0.,'positive direct factors')
            require(0.<=solver['true_weighted_relative_residual']<=1e-10
                    and 0.<=flow['max_volume_divergence']<=1e-10,'logged elliptic/flux gate')
            require(all(solver[k]>=0. for k in PHASES),'negative solver cost')
        require(all(0.<=x['outgoing_CFL']<=.5 and x['minimum_face_q']>=0. for x in stages),'CFL/face gate')
        require(all(x['minimum_q']>=0. and x['minimum_Euler_stage_q']>=0.
                    and 0.<=x['circulation_ledger_relative']<=1e-10 for x in updates),'stage/ledger gate')
        values=dict(max_CFL=max(x['outgoing_CFL'] for x in stages),
            max_volume_divergence=max(x['max_volume_divergence'] for x in solves),
            max_solver_true_residual=max(x['solver']['true_weighted_relative_residual'] for x in solves),
            max_circulation_ledger_relative=max(x['circulation_ledger_relative'] for x in updates),
            minimum_Euler_stage_q=min(x['minimum_Euler_stage_q'] for x in updates))
        for key,value in values.items(): close(case[key],value,key)
        for key in PHASES: close(case['direct_solver_phase_seconds'][key],math.fsum(x['solver'][key] for x in solves),key)
        require(set(case['direct_solver_counts'])=={'solves','rhs_assemblies','forward_transforms','factorizations',
                'triangular_solves','inverse_transforms','original_rhs_assemblies','original_residual_checks',
                'factor_reuses','new_CG_solves'},'direct count categories')
        for key,value in case['direct_solver_counts'].items():
            require(value==(0 if key in ('factor_reuses','new_CG_solves') else len(solves)),'direct phase count')
        require(set(case['phase_seconds'])=={'boundary_seconds','linear_solve_seconds','reconstruction_seconds','transport_seconds'},'case cost categories')
        for key,value in case['phase_seconds'].items(): close(value,math.fsum(x.get(key,0.) for x in logged),key)
        gamma0=statistics[0]['circulation']; predicted=gamma0
        for step in range(steps):
            predicted-=dt/2.*(stages[2*step]['boundary_circulation_outflow']+stages[2*step+1]['boundary_circulation_outflow'])
            if (step+1) % (steps//4)==0:
                stat=statistics[(step+1)//(steps//4)]
                require(abs(stat['circulation']-predicted)/gamma0<=1e-10,'snapshot outflow ledger')
        qdrift=[abs(x['q_squared_integral']/statistics[0]['q_squared_integral']-1.) for x in statistics]
        idrift=[abs(x['axial_impulse']/statistics[0]['axial_impulse']-1.) for x in statistics]
        for saved,recomputed in ((case['q_squared_relative_drift'],qdrift),(case['impulse_relative_drift'],idrift)):
            require(len(saved)==5,'drift length')
            for a,b in zip(saved,recomputed): close(a,b,'drift')
        require(set(case['initial_analytic_errors'])=={'u','J'},'initial metric categories')
        initial=all(0.<=case['initial_analytic_errors'][k]<=(.01 if name=='S64' else .005) for k in ('u','J'))
        summaries.append(dict(name=name,initial=initial,stage=True,ledger=max(values['max_circulation_ledger_relative'],0.)<=1e-10,
                              q_drift=max(qdrift)<=.02,impulse_drift=max(idrift)<=.01))
        aggregates['solves']+=len(solves); aggregates['stages']+=len(stages)
        aggregates['steps']+=len(updates); aggregates['snapshots']+=len(snapshots); all_solves.extend(solves)
    require(expected_raw=={p.name for p in LOCAL.glob('*.npz')} and len(expected_raw)==36,'exact 36 raw files')
    require(aggregates==dict(solves=5630,stages=5600,steps=2800,snapshots=30),'aggregate schedule counts')
    require(result['runtime_counts']==COUNTS and result['checkpoint_records']==all_checkpoints,'result counts/checkpoints')
    for key in PHASES: close(result['direct_solver_phase_seconds'][key],math.fsum(x['solver'][key] for x in all_solves),'total '+key)
    close(result['direct_solver_phase_seconds']['failed_checked_solve_seconds'],0.,'failed solver cost')
    return cases,summaries,aggregates


def reference_gates(result,cases,summaries):
    byname={x['name']:x for x in cases}; core=result['comparisons']; full=result['full_box_controls']
    expected=[(a,b,kind,i,t) for a,b,kind in PAIRS for i,t in enumerate(TIMES)]
    require(len(core)==len(full['comparisons'])==25,'25 comparisons per domain')
    shape_norm=math.sqrt(1.+((4.-math.pi)/2.)**2)
    for k,(a,b,kind,i,t) in enumerate(expected):
        row=core[k]; wide=full['comparisons'][k]
        require((row['a'],row['b'],row['kind'],row['time'])==(a,b,kind,t),'core comparison schedule')
        require((wide['a'],wide['b'],wide['kind'],wide['index'],wide['time'])==(a,b,kind,i,t),'D8 comparison schedule')
        require(wide['domain']=='D8' and wide['quadrature_orders']==[3,2],'fixed full-box rule')
        require(wide['numerator']>=0. and wide['denominator']>0.,'D8 norm signs')
        close(wide['vorticity_relative'],math.sqrt(wide['numerator']/wide['denominator']),'D8 score')
        require(wide['passed'] is (wide['vorticity_relative']<=.01),'D8 gate')
        sa=byname[a]['snapshots'][i]; sb=byname[b]['snapshots'][i]
        close(row['axial_centroid_absolute'],abs(sa['centroid'][1]-sb['centroid'][1]),'reference centroid')
        close(row['covariance_relative'],covariance_difference(sa['covariance'],sb['covariance'])/shape_norm,'reference covariance')
        require(row['vorticity_relative']>=0. and row['velocity_relative']>=0.,'core scalar signs')
    checks=dict(initial_analytic=all(x['initial'] for x in summaries),all_stage_invariants=all(x['stage'] for x in summaries),
        vorticity_disagreements=all(x['vorticity_relative']<=.01 for x in core),
        velocity_disagreements=all(x['velocity_relative']<=(.02 if x['kind']=='space' else .01) for x in core),
        centroid_disagreements=all(x['axial_centroid_absolute']<=.01 for x in core),
        covariance_disagreements=all(x['covariance_relative']<=.01 for x in core),
        spatial_reduction=reductions(core,result['spatial_reductions']),
        circulation_ledger=all(x['ledger'] for x in summaries),q_squared_drift=all(x['q_drift'] for x in summaries),
        axial_impulse_drift=all(x['impulse_drift'] for x in summaries),
        full_box_vorticity_disagreements=all(x['vorticity_relative']<=.01 for x in full['comparisons']),
        full_box_spatial_reduction=reductions(full['comparisons'],full['spatial_reductions']))
    require(result['reference_checks']==checks and result['reference_qualified_full_window'] is all(checks.values()),'12 reference predicates')
    require(full['checks']=={k:checks[k] for k in ('full_box_vorticity_disagreements','full_box_spatial_reduction')},'D8 predicates')
    require(result['initial_checks']=={x['name']:x['initial'] for x in summaries},'initial predicates')
    require(len(full['outside_D8'])==5,'outside diagnostics count')
    for i,row in enumerate(full['outside_D8']):
        stat=byname['D192']['snapshots'][i]
        require((row['index'],row['time'],row['quadrature_orders'])==(i,TIMES[i],[3,2]),'outside schedule')
        for value,total,recorded,fraction in (('circulation','circulation','whole_D12_circulation','circulation_fraction'),
                ('vorticity_squared_integral','vorticity_squared_integral','whole_D12_vorticity_squared_integral','vorticity_squared_fraction')):
            require(row[value]>=0.,'outside sign'); close(row[recorded],stat[total],'outside full total')
            close(row[fraction],row[value]/stat[total],'outside fraction')
        require(row['formal_free_space_tail_bound'] is False,'outside scope')
    return checks


def model_gates(result,cases):
    screen=result['ordinary_model_screen']; require(isinstance(screen,dict),'required qualified-reference scoring')
    coefficient_path=ROOT.parent/'t54-scalar-verification'/'result.json'; coefficient=document(coefficient_path)
    match(coefficient_path,result['coefficient_input']); match(coefficient_path,screen['coefficient_identity'])
    require(coefficient['status']=='consistent' and result['coefficient_refitted'] is False,'fixed coefficient')
    beta=coefficient['closed_metrics']['beta_best_over_g0']; speed=1.5*beta
    close(screen['beta_best_over_g0'],beta,'beta'); close(screen['axial_speed'],speed,'speed')
    byname={x['name']:x for x in cases}; covariance=[[(4.-math.pi)/2.,0.],[0.,1.]]
    initial=byname['S256']['snapshots'][0]; normalization=norm(initial['covariance'])
    close(screen['actual_initial_S256_covariance_frobenius_norm'],normalization,'actual shape denominator')
    gamma=1.5*math.sqrt(2.*math.pi); omega2=(9./4.)*math.pi**1.5
    analytic=screen['analytic_model']
    require(analytic['amplitude']==1.5 and analytic['width']==1. and analytic['negative_vorticity_mass']==0.,'fixed model parameters')
    require(analytic['covariance']==covariance and analytic['positive_for_all_finite_r_z'] is True,'analytic model shape')
    close(analytic['fullspace_circulation'],gamma,'analytic Gamma'); close(analytic['fullspace_vorticity_squared_integral'],omega2,'analytic omega2')
    close(analytic['radial_centroid'],math.sqrt(math.pi/2.),'analytic radial mean')
    expected=[(name,i,t) for name in ('S256','S128') for i,t in enumerate(TIMES)]
    require([(x['reference'],x['index'],x['time']) for x in screen['scores']]==expected,'ten score tuples')
    integration=[]; points=0
    for row,(name,i,t) in zip(screen['scores'],expected):
        stat=byname[name]['snapshots'][i]; primary=row['primary_8x6']; confirm=row['confirmation_16x12']
        for record,orders in ((primary,[8,6]),(confirm,[16,12])):
            require(record['domain']=='D8' and record['quadrature_orders']==orders,'fixed model rule')
            require(record['numerator']>=0. and record['denominator']>0.,'model norm signs')
            close(record['vorticity_relative'],math.sqrt(record['numerator']/record['denominator']),'model score arithmetic')
            close(record['denominator'],stat['vorticity_squared_integral'],'reference score denominator')
            for key,total in (('circulation',gamma),('vorticity_squared_integral',omega2)):
                value=record['model_D8_'+key]; require(value>0.,'numerical model mass')
                fraction='model_D8_'+('circulation' if key=='circulation' else 'vorticity_squared')+'_fraction_of_analytic_fullspace'
                close(record[fraction],value/total,'model mass fraction')
            count=byname[name]['radial_cells']*byname[name]['axial_cells']*orders[0]*orders[1]
            require(record['quadrature_node_cell_points']==record['gaussian_exp_evaluations']==count,'rule point count'); points+=count
            require(record['mass_values_are_numerical'] is True and record['reference_sampled_nonnegative'] is True
                    and record['reference_minimum_sampled_q']>=0. and record['reference_sampled_negative_circulation']==0.,'score positivity/mass label')
        difference=abs(primary['vorticity_relative']-confirm['vorticity_relative'])
        close(row['score_absolute_difference'],difference,'rule difference')
        passed=difference<=1e-6; require(row['integration_passed'] is passed,'integration gate'); integration.append(passed)
        for key in ('circulation','vorticity_squared_integral'):
            close(row['numerical_mass_absolute_differences'][key],abs(primary['model_D8_'+key]-confirm['model_D8_'+key]),'mass difference')
        mean=[math.sqrt(math.pi/2.),speed*t]
        require(row['model_fullspace_centroid']==mean and row['model_fullspace_covariance']==covariance,'model moments')
        require(row['reference_own_domain_centroid']==stat['centroid'] and row['reference_own_domain_covariance']==stat['covariance'],'reference moments')
        close(row['reference_own_domain_circulation'],stat['circulation'],'reference Gamma')
        close(row['reference_own_domain_vorticity_squared_integral'],stat['vorticity_squared_integral'],'reference omega2')
        require(row['reference_negative_cell_mass']==0. and row['score_is_primary_regardless_of_confirmation'] is True,'score semantics')
        close(row['axial_centroid_absolute'],abs(speed*t-stat['centroid'][1]),'model centroid error')
        difference=covariance_difference(covariance,stat['covariance'])
        close(row['covariance_frobenius_absolute'],difference,'model shape error')
        close(row['covariance_relative_to_initial_S256'],difference/normalization,'normalized model shape')
    primary=screen['scores'][:5]
    checks=dict(vorticity_L2=all(x['primary_8x6']['vorticity_relative']<=.10 for x in primary),
                axial_centroid=all(x['axial_centroid_absolute']<=.1 for x in primary),
                covariance=all(x['covariance_relative_to_initial_S256']<=.1 for x in primary))
    displacement=byname['S256']['snapshots'][-1]['centroid'][1]-initial['centroid'][1]
    close(screen['motion']['axial_displacement'],displacement,'motion')
    require(screen['motion']['reference']=='S256' and screen['motion']['required_initial_widths']==.25
            and screen['motion']['initial_width']==1.,'motion definition')
    close(screen['motion']['initial_axial_centroid'],initial['centroid'][1],'motion initial mean')
    close(screen['motion']['final_axial_centroid'],byname['S256']['snapshots'][-1]['centroid'][1],'motion final mean')
    motion=displacement>=.25; qualified=all(integration); model_pass=all(checks.values())
    require(screen['primary_model_checks']==checks and screen['model_pass'] is model_pass,'three model gates')
    require(screen['integration_qualified'] is qualified and screen['score_integration_qualified'] is qualified,'ten integration gates')
    require(screen['motion']['passed'] is motion and screen['meaningful_motion'] is motion,'motion gate')
    require(result['score_integration_qualified'] is qualified and result['meaningful_motion'] is motion,'result qualification links')
    require(screen['checks']==dict(score_integration=qualified,meaningful_motion=motion,**checks),'screen predicates')
    counters=screen['counters']
    require(all(counters[k]==points for k in ('quadrature_node_cell_points','reference_reconstruction_points','sample_validations','gaussian_exp_evaluations')),'model work counts')
    require(counters['model_rule_integrals']==20 and counters['quadrature_rules_constructed']==4 and counters['quadrature_rule_nodes']==42,'model setup counts')
    return checks,qualified,motion,model_pass


def qualify():
    require(platform.python_version()=='3.12.13','bookkeeping Python version')
    manifest_path=ROOT/'input-manifest.json'; manifest_raw=manifest_path.read_bytes(); manifest=strict_json(manifest_raw)
    manifest_id=dict(bytes=len(manifest_raw),sha256=hashlib.sha256(manifest_raw).hexdigest())
    require(manifest['schema']=='t61-saved-output-freeze-v1','new freeze schema')
    for item in manifest['inputs']:
        path=relative_input(item['path']); require(path not in ADMITTED,'duplicate freeze input'); ADMITTED[path]=ident_fields(item)
    for item in manifest.get('external_inputs',[]):
        require(Path(item['path']).is_absolute(),'external input must be absolute')
        path=Path(item['path']).resolve(); require(path not in ADMITTED,'duplicate external input'); ADMITTED[path]=ident_fields(item)
    executable=Path(manifest['executable']['path']).resolve(); require(Path(sys.executable).resolve()==executable,'bookkeeping executable')
    ADMITTED[executable]=ident_fields(manifest['executable'])
    for path in ADMITTED: checked(path)
    oldfreeze=document(OLD/'input-manifest.json'); require(len(oldfreeze['inputs'])==49,'original 49-input freeze')
    fixed=dict(schema='t60-full-window-gaussian-freeze-v1',expected_python='3.12.14',expected_numpy='2.3.5',
        maximum_scientific_child_invocations=1,child_timeout_seconds=600,maximum_new_reference_trajectories=6,
        reused_reference_trajectories=0,new_CG_solves_permitted=0,candidate_trajectories_permitted=0,
        ordinary_model_trajectories_permitted=1,case_names=list(NAMES),maximum_steps=2800,
        maximum_transport_stages=5600,maximum_direct_solves=5630,maximum_completed_checkpoints=30,time_end=1.,
        scientific_children_before_freeze_this_task=0,peak_working_set_stop_bytes=2*1024**3,
        minimum_available_host_bytes=3*1024**3,memory_sample_interval_seconds=.25)
    require(all(oldfreeze[k]==v for k,v in fixed.items()),'original fixed budget/scope metadata')
    require(len({x['path'] for x in oldfreeze['inputs']})==49,'original unique input paths')
    for item in oldfreeze['inputs']: match(relative_input(item['path']),item)
    match(Path(oldfreeze['executable']['path']),oldfreeze['executable'])
    result=document(OLD/'result.json'); receipt=document(OLD/'execution.json')
    require(receipt['status']=='failed_result_validation_no_retry' and receipt['result_read_error']=='AssertionError()'
            and receipt['complete_result_validated'] is False and receipt['ordinary_model_verdict']=='unqualified','preserve failed T60 history')
    require(receipt['returncode']==0 and receipt['scientific_child_invocations']==1,'original single child')
    require(receipt['schema']=='t60-full-window-gaussian-execution-v1'
            and receipt['maximum_new_reference_trajectories']==6 and receipt['reused_reference_trajectories']==0,
            'original execution scope')
    require(0.<receipt['child_supervised_seconds']<=600. and receipt['child_timeout_seconds']==600,'original runtime')
    require(receipt['host_before_launch']['available_physical_bytes']>=3*1024**3
            and receipt['peak_working_set_stop_bytes']==2*1024**3,'original resource contract')
    require(all(receipt[k] is True for k in ('frozen_inputs_unchanged','executable_unchanged','input_manifest_unchanged')),'original preservation receipt')
    match(OLD/'input-manifest.json',receipt['input_manifest_identity']); match(OLD/'result.json',receipt['result_identity'])
    match(OLD/'reference.py',receipt['code_identity']); match(OLD/'run_once.py',receipt['supervisor_identity'])
    match(Path(oldfreeze['executable']['path']),receipt['executable_identity'])
    expected_categories={
        'case_metadata_files':{f'local/{name}.json' for name in NAMES},
        'completed_case_records':{f'local/{name}.json' for name in NAMES},
        'step_logs':{f'local/{name}-steps.jsonl' for name in NAMES},
        'raw_files':{f'local/{name}.npz' for name in NAMES}|{f'local/{name}-snapshot-{i}.npz' for name in NAMES for i in range(5)},
        'checkpoint_metadata_files':{f'local/{name}-snapshot-{i}.json' for name in NAMES for i in range(5)},
        'validated_checkpoint_records':{f'local/{name}-snapshot-{i}.json' for name in NAMES for i in range(5)},
        'checkpoint_ledger':{'local/checkpoints.jsonl'},
        'partial_evaluation_files':{'local/reference-evaluation.json','local/ordinary-model-screen.json'},
        'logs':{'local/stdout.txt','local/stderr.txt','local/memory.jsonl'}}
    for key,expected in expected_categories.items():
        items=receipt[key]
        require(len(items)==len(expected) and {x['path'] for x in items}==expected,'receipt inventory: '+key)
        for item in items: match(OLD/item['path'],item)
    require(receipt['completed_case_count']==6 and receipt['validated_checkpoint_count']==30
            and receipt['case_validation_errors']==receipt['checkpoint_validation_errors']==receipt['failure_records']==[],
            'original completed artifact validation')
    for item in receipt['logs']:
        require(item['path'] in ('local/stdout.txt','local/stderr.txt','local/memory.jsonl'),'log destination'); match(OLD/item['path'],item)
    memory=list(lines(LOCAL/'memory.jsonl'))
    require(len(memory)==receipt['memory_samples'] and len(memory)>0,'memory sample count')
    require(all(0.<=x['working_set_bytes']<=x['peak_working_set_bytes']<=2*1024**3 for x in memory),'observed memory cap')
    require(all(x['elapsed_seconds']>=0. and x['private_usage_bytes']>=0.
                and x['peak_pagefile_usage_bytes']>=0. for x in memory),'resource record signs')
    require(all(memory[i]['elapsed_seconds']<memory[i+1]['elapsed_seconds'] for i in range(len(memory)-1)),'memory sample order')
    require(memory[-1]['elapsed_seconds']<=receipt['child_supervised_seconds'],'memory runtime')
    require(max(x['peak_working_set_bytes'] for x in memory)==receipt['observed_peak_working_set_bytes'],'memory peak')
    require(result['schema']=='t60-full-window-gaussian-screen-v1' and result['python']=='3.12.14' and result['numpy']=='2.3.5','scientific metadata')
    require(Path(result['executable']).resolve()==Path(oldfreeze['executable']['path']).resolve(),'original runtime identity')
    for key,path in {'code':OLD/'reference.py','measurement_code':OLD/'measurement.py',
            'base_code':ROOT.parent/'t56-coupled-reference'/'reference.py',
            'spatial_code':ROOT.parent/'t55-axisymmetric-reference'/'reference.py',
            'solver_code':ROOT.parent/'t58-separable-solver-qualification'/'solver.py'}.items():
        match(path,result[key]); require(result['source_identities_after'][key]==result[key],'scientific source preservation')
    require(result['source_identities_unchanged'] is True and result['coefficient_input']==result['coefficient_input_after'],'source/data preservation')
    require(result['completed_trajectories']==result['new_completed_trajectories']==6 and result['reused_trajectories']==0
            and result['time_end']==1. and result['candidate_trajectories']==result['new_CG_solves']==0,'trajectory scope')
    require(result['ordinary_model_trajectories']==1 and result['formal_error_certificate'] is False,'model scope')
    require(result['prior_T56_status']=='failed_checks' and result['prior_T57_status']=='timeout_no_retry'
            and result['prior_T59_status']=='qualified_short_reference_only','earlier history')
    cases,summaries,counts=case_records(result)
    checkpoints=evidence(result['checkpoint_index'],'local/checkpoints.jsonl')
    checkpoint_rows=list(lines(checkpoints)); saved=[x for x in checkpoint_rows if x['kind']=='snapshot_saved']
    require(len(saved)==30 and [{k:v for k,v in x.items() if k!='kind'} for x in saved]==result['checkpoint_records'],'checkpoint ledger')
    evaluation=document(evidence(result['reference_evidence'],'local/reference-evaluation.json'))
    require(evaluation['schema']=='t60-reference-evaluation-v1'
            and evaluation['reference_qualified_full_window'] is True
            and evaluation['runtime_counts']==result['runtime_counts']
            and evaluation['initial_checks']==result['initial_checks'],'reference artifact semantics')
    require(evaluation['reference_checks']==result['reference_checks'] and evaluation['comparisons']==result['comparisons']
            and evaluation['spatial_reductions']==result['spatial_reductions'] and evaluation['full_box_controls']==result['full_box_controls'],'reference artifact equality')
    checks=reference_gates(result,cases,summaries); require(all(checks.values()),'reference qualifications did not all pass')
    scorefile=document(evidence(result['ordinary_model_evidence'],'local/ordinary-model-screen.json'))
    require(scorefile['schema']=='t60-ordinary-screen-evidence-v1','model artifact schema')
    require(scorefile['ordinary_model_screen']==result['ordinary_model_screen'],'model artifact equality')
    for key in ('status','ordinary_model_verdict','score_integration_qualified','meaningful_motion','full_t1_task_pass'):
        require(scorefile[key]==result[key],'model artifact status linkage')
    model_checks,integration,motion,model_pass=model_gates(result,cases)
    require(integration and motion,'score integration or meaningful motion unqualified')
    verdict='pass' if model_pass else 'fail'
    require(result['ordinary_model_verdict']==verdict and result['full_t1_task_pass'] is model_pass
            and result['status']=='qualified_reference_ordinary_model_'+verdict,'original worker outcome')
    close(result['prior_child_seconds'],1560.418468699907,'prior scientific cost')
    close(receipt['cumulative_T56_T57_T58_T59_T60_supervised_seconds'],1976.6796338998247,'scientific history cost')
    close(receipt['prior_T56_T57_T58_T59_supervised_seconds']+receipt['child_supervised_seconds'],1976.6796338998247,'scientific cost addition')
    require(0.<=result['child_elapsed_before_result_write_seconds']<=receipt['child_supervised_seconds'],'child timing')
    close(result['prior_plus_child_elapsed_before_result_write_seconds'],result['prior_child_seconds']+result['child_elapsed_before_result_write_seconds'],'reported child subtotal')
    close(result['full_box_comparison_seconds'],result['full_box_controls']['elapsed_seconds'],'full-box cost')
    close(result['ordinary_model_measurement_seconds'],result['ordinary_model_screen']['elapsed_seconds'],'model cost')
    for case in cases:
        disjoint=case['kernel']['build_seconds']+sum(case['phase_seconds'].values())+case['checkpoint_save_seconds']+case['final_array_save_seconds']
        require(0.<=disjoint<=case['case_elapsed_before_record_write_seconds']+1e-9,'case nonoverlapping costs')
    review=REPO/'tracks/validation/t60-full-window-review.md'; checked(review)
    require(identity(manifest_path)==manifest_id,'T61 manifest changed')
    for path,expected in BEFORE.items(): require(identity(path)==expected,'input changed during qualification: '+str(path))
    deadline()
    return dict(schema='t61-saved-output-qualification-v1',status='qualified_saved_reference_ordinary_model_'+verdict,
        accepted_saved_evidence=True,reference_qualified_full_window=True,ordinary_model_verdict=verdict,
        full_t1_task_pass=model_pass,T60_history_reclassified=False,new_scientific_trajectories=0,new_scientific_invocations=0,
        reference_checks=checks,model_checks=model_checks,score_integration_qualified=integration,meaningful_motion=motion,
        counts=counts,raw_files_hashed_not_loaded=36,normalized_evidence_paths=NORMALIZED,
        original_failed_receipt=dict(path=(OLD/'execution.json').relative_to(REPO).as_posix(),**checked(OLD/'execution.json')),
        original_numerical_result=dict(path=(OLD/'result.json').relative_to(REPO).as_posix(),**checked(OLD/'result.json')),
        saved_array_review=dict(path=review.relative_to(REPO).as_posix(),**checked(review),
            attribution='Prior t48_review saved-array/log reduction; not repeated by this metadata-only child.'),
        limitations=['No array decoding or new integration; core field measurements are saved scalars.',
            'Unsaved intermediate face upper bounds rely on frozen producer assertions; logged minimum/solver/CFL conditions are rechecked.',
            'D8, five sampled times, empirical reference and rule agreement; no formal whole-space or continuous-time certificate.'],
        scalar_readback_tolerance=dict(relative=3e-11,absolute=3e-14,scientific_thresholds_changed=False),
        input_manifest=manifest_id,input_count=len(manifest['inputs']),external_input_count=len(manifest.get('external_inputs',[])),
        all_input_identities_unchanged=True,files_read_or_hashed=len(READ_PATHS),
        python=platform.python_version(),executable=str(Path(sys.executable).resolve()),
        code=checked(Path(__file__)),path_contract=checked(ROOT/'path_contract.py'),
        original_scientific_history_seconds=1976.6796338998247,
        qualification_child_elapsed_before_result_write_seconds=time.perf_counter()-START)


def main():
    try:
        result=qualify(); exit_code=0
    except Exception as error:
        result=dict(schema='t61-saved-output-qualification-v1',status='qualification_failed',
            accepted_saved_evidence=False,reference_qualified_full_window=False,ordinary_model_verdict='unqualified',
            full_t1_task_pass=None,T60_history_reclassified=False,new_scientific_trajectories=0,new_scientific_invocations=0,
            error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc(),
            qualification_child_elapsed_before_result_write_seconds=time.perf_counter()-START)
        exit_code=2
    result['created_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (ROOT/'result.json').open('x',encoding='utf8',newline='\n') as stream:
        json.dump(result,stream,indent=2,allow_nan=False); stream.write('\n')
    print(json.dumps(dict(status=result['status'],accepted_saved_evidence=result['accepted_saved_evidence'],
                          ordinary_model_verdict=result['ordinary_model_verdict'])),flush=True)
    return exit_code


if __name__=='__main__':
    raise SystemExit(main())
