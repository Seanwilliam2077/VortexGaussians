"""One frozen T70 numerical child. No reference arrays or future states."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
import time
import traceback
from contextlib import contextmanager

START = time.perf_counter()
DEADLINE = time.perf_counter_ns() + 120_000_000_000
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
LOCAL = ROOT / 'local'
CHECK_NAMES = [
    'frozen_identity_runtime', 'rule_initial_operator', 'full_self_cross_evaluator',
    'independent_weight_controls', 'complete_prescribed_searches',
    'selected_direct_confirmation_moments', 'complete_work_accounting',
    'final_identity_preservation',
]
np = None
STREAM = None
COUNTERS = dict(input_arrays_read=0, input_arrays_saved=0, rule_count=0,
    rule_nodes=0, rule_eigh_calls=0, root_input_bytes_hashed_before=0,
    root_input_bytes_hashed_after=0, root_input_files_hashed_before=0,
    root_input_files_hashed_after=0)
CHECKS, PHASES, STEPS = [], {}, []
BEFORE = {}
DETAILS = {}
ACTIVE = 'initialization'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def clock():
    if time.perf_counter_ns() >= DEADLINE:
        raise TimeoutError('T70 fixed child deadline')


def charge(key, amount=1):
    COUNTERS[key] = COUNTERS.get(key, 0) + int(amount)


def emit(kind, data):
    clock()
    charge('root_journal_events')
    STREAM.write(json.dumps(dict(kind=kind, elapsed_seconds=time.perf_counter()-START,
                                 **data), allow_nan=False) + '\n')
    STREAM.flush()


@contextmanager
def phase(name):
    global ACTIVE
    ACTIVE = name
    begin = time.perf_counter()
    emit('phase_started', dict(name=name))
    try:
        yield
    finally:
        PHASES[name] = time.perf_counter() - begin
        emit('phase_finished', dict(name=name, seconds=PHASES[name]))


def identity(path, suffix):
    digest, size = hashlib.sha256(), 0
    with path.open('rb') as stream:
        while block := stream.read(1024*1024):
            clock()
            digest.update(block)
            size += len(block)
    charge('root_input_bytes_hashed_' + suffix, size)
    charge('root_input_files_hashed_' + suffix)
    return dict(bytes=size, sha256=digest.hexdigest())


def strict_json(path):
    def reject(value):
        raise ValueError('nonfinite JSON constant: ' + value)
    return json.loads(path.read_text(encoding='utf-8'), parse_constant=reject)


def import_source(name, path):
    require(path.resolve() in BEFORE, 'unfrozen Python helper')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    charge('root_scientific_helpers_loaded')
    return module


def check(name, passed, details):
    require(name in CHECK_NAMES and name not in [x['name'] for x in CHECKS], 'duplicate check')
    packet = dict(name=name, passed=bool(passed), details=details)
    CHECKS.append(packet)
    emit('qualification', packet)


class Comparisons:
    def __init__(self):
        self.count, self.values = 0, 0
        self.maximum_absolute_difference, self.maximum_tolerance_ratio = 0., 0.
        self.worst_label, self.failures = None, []

    def compare(self, actual, expected, label, score=False, atol=None):
        a, b = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
        require(a.shape == b.shape, 'comparison shapes: ' + label)
        self.count += 1
        self.values += int(a.size)
        finite = bool(np.all(np.isfinite(a)) and np.all(np.isfinite(b)))
        if not finite:
            self.failures.append(dict(label=label, reason='nonfinite'))
            return
        delta = np.abs(a-b)
        limit = (float(atol) if atol is not None else
                 1e-8 if score else 1e-10 + 1e-9*np.maximum(np.abs(a), np.abs(b)))
        absolute = float(np.max(delta))
        ratio = float(np.max(delta / limit))
        self.maximum_absolute_difference = max(self.maximum_absolute_difference, absolute)
        if ratio > self.maximum_tolerance_ratio:
            self.maximum_tolerance_ratio, self.worst_label = ratio, label
        if ratio > 1:
            self.failures.append(dict(label=label, maximum_difference=absolute,
                                      maximum_tolerance_ratio=ratio))

    def condition(self, passed, label, values=None):
        self.count += 1
        if not passed:
            self.failures.append(dict(label=label, values=values))

    def record(self):
        return dict(passed=not self.failures, comparison_calls=self.count,
                    compared_values=self.values,
                    maximum_absolute_difference=self.maximum_absolute_difference,
                    maximum_tolerance_ratio=self.maximum_tolerance_ratio,
                    worst_label=self.worst_label, failures=self.failures)


def integral(values, grid):
    clock()
    charge('root_direct_reductions')
    charge('root_direct_reduction_points', int(values.size))
    result = float(np.sum(grid['W'] * values))
    require(math.isfinite(result), 'nonfinite direct integral')
    return result


def gaussian(g, grid):
    sr, sz, z0 = g
    require(sr > 0 and sz > 0, 'nonpositive Gaussian width')
    charge('root_gaussian_component_calls')
    charge('root_gaussian_component_points', int(grid['r'].size))
    charge('root_exp_evaluations', int(grid['r'].size))
    charge('root_array_exp_calls')
    return np.exp(-grid['r']**2/(2*sr*sr) -
                  (grid['z']-z0)**2/(2*sz*sz))/(sr*sr*math.sqrt(2*math.pi)*sz)


def model_values(state, grid):
    # Both slots are charged, including zero-weight and identical geometry.
    left, right = [gaussian(g, grid) for g in state['geometry']]
    return state['Gamma']*((1-state['eta'])*left + state['eta']*right), (left, right)


def model_norm(state, physics):
    g1, g2 = state['geometry']
    m11, m12, m22 = physics.gram(g1,g1), physics.gram(g1,g2), physics.gram(g2,g2)
    eta = state['eta']
    return state['Gamma']**2*math.fsum(((1-eta)**2*m11, 2*eta*(1-eta)*m12, eta*eta*m22))


def frozen_identity(manifest_path):
    manifest = strict_json(manifest_path)
    expected = dict(schema='t70-causal-projector-freeze-v1',
        expected_python='3.12.14', expected_numpy='2.3.5',
        maximum_scientific_child_invocations=1, child_timeout_seconds=120,
        observed_peak_working_set_limit_bytes=536870912,
        required_available_physical_bytes=1073741824, memory_sample_interval_seconds=.25,
        expected_rule_orders=[64,96,128,192,256], expected_rule_nodes=736,
        expected_rule_eigh_calls=5, heat_orders=[64,128,256],
        step_sizes=[.0625,.03125], expected_check_names=CHECK_NAMES,
        prior_scientific_child_seconds=1990.3707298998488)
    require(all(manifest.get(k)==v for k,v in expected.items()), 'manifest fixed contract')
    for item in manifest['inputs']:
        path = item['path']
        require(isinstance(path,str) and path and ':' not in path and '\\' not in path
                and not path.startswith('/') and
                all(x not in ('','.','..') for x in path.split('/')), 'input path')
        target = (REPO/path).resolve()
        require(target.is_relative_to(REPO) and target not in BEFORE and
                target.suffix not in ('.npz','.npy'), 'nonarray contained unique input')
        BEFORE[target] = {k:item[k] for k in ('bytes','sha256')}
    exe = Path(sys.executable).resolve()
    require(exe == Path(manifest['executable']['path']).resolve(), 'scientific interpreter')
    BEFORE[exe] = {k:manifest['executable'][k] for k in ('bytes','sha256')}
    BEFORE[manifest_path.resolve()] = identity(manifest_path, 'before')
    for path, expected_identity in BEFORE.items():
        if path != manifest_path.resolve():
            require(identity(path,'before') == expected_identity, 'input changed: '+str(path))
    t54path = (ROOT.parent/'t54-scalar-verification/result.json').resolve()
    require(t54path in BEFORE, 'T54 scalar not frozen')
    t54 = strict_json(t54path)
    require(t54['status']=='consistent', 'T54 scalar qualification')
    closed = t54['closed_metrics']
    require(closed['beta_best_over_g0']==.29030989544096925 and
            closed['E_best']==.3551693233816372, 'T54 fixed scalars')
    return manifest, closed


def main(manifest_path):
    global np
    with phase('identity_runtime'):
        manifest, closed = frozen_identity(manifest_path)
        import numpy as numerical_library
        np = numerical_library
        runtime = dict(python=platform.python_version(), numpy=np.__version__,
                       executable=str(Path(sys.executable).resolve()))
        require(runtime['python']=='3.12.14' and runtime['numpy']=='2.3.5', 'runtime versions')
        physics_module = import_source('t70_physics',ROOT/'physics.py')
        search_module = import_source('t70_search',ROOT/'search.py')
        check(CHECK_NAMES[0], True, dict(runtime=runtime, frozen_inputs=len(BEFORE)))
        DETAILS['runtime'] = runtime

    initial, evaluator, scalar, searchchecks, confirmation = [Comparisons() for _ in range(5)]
    with phase('rules_and_point_controls'):
        rules, rule_records = {}, []
        for n in (64,96,128,192,256):
            clock()
            k = np.arange(1,n,dtype=float)
            off = k/np.sqrt(4*k*k-1)
            x, vec = np.linalg.eigh(np.diag(off,1)+np.diag(off,-1))
            w = 2*vec[0,:]**2
            charge('rule_count'); charge('rule_nodes',n); charge('rule_eigh_calls')
            initial.condition(bool(np.all(np.isfinite(x)) and np.all(np.isfinite(w)) and
                                   np.all(np.diff(x)>0) and np.all(np.abs(x)<1) and
                                   np.all(w>0)), 'positive ordered finite rule '+str(n))
            initial.compare(x,-x[::-1], 'node symmetry '+str(n), atol=1e-12)
            initial.compare(w,w[::-1], 'weight symmetry '+str(n), atol=1e-12)
            initial.compare(float(np.sum(w)),2., 'weight sum '+str(n), atol=1e-12)
            rules[n] = (x,w)
            packet = dict(order=n, weight_sum=float(np.sum(w)),
                          node_symmetry=float(np.max(np.abs(x+x[::-1]))),
                          weight_symmetry=float(np.max(np.abs(w-w[::-1]))))
            rule_records.append(packet); emit('rule_constructed',packet)
        physics = physics_module.Physics(np,rules,COUNTERS,emit)
        gamma = 1.5*math.sqrt(2*math.pi)
        g0 = (1.,1.,0.)
        fixture_geometry = ((.9,1.05,-.2),(1.1,.85,.4))
        q0 = dict(Gamma=gamma,eta=0.,geometry=[g0,g0])
        duplicate = dict(Gamma=gamma,eta=1/3,geometry=[g0,g0])
        fixture = dict(Gamma=gamma,eta=1/3,geometry=fixture_geometry)
        states = dict(q0=q0,fixture=fixture)
        probes = [g0,*fixture_geometry]
        pts = np.array([(0,0),(0,.25),(0,1),(0,2),(.25,0),(.25,.5),(.5,-.5),
                        (1,0),(1,1),(2,-1),(3,2),(4,0),(0,4)],dtype=float)
        exact = physics.initial_exact(pts[:,0],pts[:,1])
        for order in (64,128,256):
            standard = physics.field(q0,pts[:,0],pts[:,1],order)
            doubled = physics.field(duplicate,pts[:,0],pts[:,1],order)
            for key in ('q','qr','qz','phi','phi_r','phi_z','ur','uz','F'):
                initial.compare(standard[key],exact[key],f'point oracle {order} {key}')
                initial.compare(doubled[key],standard[key],f'duplicate representation {order} {key}')
            initial.compare(standard['F'],2*pts[:,1]*standard['phi']*standard['q'],
                            f'independent initial F {order}')
        DETAILS['rules'] = rule_records

    with phase('direct_evaluator_controls'):
        grids = {}
        for radius in (8,12):
            for nr,nz in ((64,128),(96,192)):
                xr,wr = rules[nr]; xz,wz = rules[nz]
                rr,zz = np.meshgrid(radius*(xr+1)/2, radius*xz,indexing='ij')
                ww = 2*math.pi*rr**3*(radius*wr[:,None]/2)*(radius*wz[None,:])
                key = f'D{radius}-{nr}x{nz}'
                grids[key] = dict(r=rr.ravel(),z=zz.ravel(),W=ww.ravel())
                charge('root_spatial_grids'); charge('root_spatial_grid_points',nr*nz)
        probe_values = {key:[gaussian(g,grid) for g in probes] for key,grid in grids.items()}
        grams = {(i,j):physics.gram(probes[i],probes[j]) for i in range(3) for j in range(i,3)}
        for key,grid in grids.items():
            for (i,j),value in grams.items():
                evaluator.compare(integral(probe_values[key][i]*probe_values[key][j],grid),
                                  value,f'fullspace probe Gram {key} {i} {j}')
        crosses = {}
        for name,state in states.items():
            for p,g in enumerate(probes):
                for order in (64,128,256):
                    packet = physics.cross(state,g,order)
                    crosses[name,p,order] = packet
                    emit('evaluator_cross',dict(state=name,probe=p,order=order,**packet))
                for order in (64,256):
                    for a,b in zip(crosses[name,p,order]['ordered_pairs'],
                                   crosses[name,p,128]['ordered_pairs']):
                        evaluator.compare(a['value'],b['value'],f'cross heat {name} {p} {order} {a["i"]}{a["j"]}')
                    evaluator.compare(crosses[name,p,order]['total'],crosses[name,p,128]['total'],
                                      f'total cross heat {name} {p} {order}')
        cache, calibration, direct_cross = {}, [], {}
        c = 1.5*closed['beta_best_over_g0']
        for name,state in states.items():
            qnorm = model_norm(state,physics)
            for key,grid in grids.items():
                for order in (64,128,256):
                    clock()
                    field = physics.field(state,grid['r'],grid['z'],order)
                    pair_sum = np.zeros_like(field['F'])
                    for pair in field['ordered_Fij']:
                        pair_sum += pair['value']
                    evaluator.compare(pair_sum,field['F'],f'ordered F sum {name} {key} {order}')
                    evaluator.compare(integral(field['q']**2,grid),qnorm,f'qnorm {name} {key} {order}')
                    for p,probe in enumerate(probe_values[key]):
                        numeric = crosses[name,p,order]
                        actual = integral(field['F']*probe,grid)
                        evaluator.compare(actual,numeric['total'],f'total cross direct {name} {key} {order} {p}')
                        pair_values = []
                        for pair,expected in zip(field['ordered_Fij'],numeric['ordered_pairs']):
                            require((pair['i'],pair['j'])==(expected['i'],expected['j']), 'pair order')
                            value = integral(pair['value']*probe,grid)
                            pair_values.append(value)
                            evaluator.compare(value,expected['value'],
                                f'pair cross direct {name} {key} {order} {p} {pair["i"]}{pair["j"]}')
                        direct_cross[name,key,order,p] = [actual,*pair_values]
                    if name=='q0':
                        zq = grid['z']*field['q']
                        den, fnorm = integral(zq*zq,grid),integral(field['F']**2,grid)
                        require(den>0 and fnorm>0,'positive initial derivative norms')
                        coefficient = integral(field['F']*zq,grid)/den
                        residual = math.sqrt(integral((field['F']-c*zq)**2,grid)/fnorm)
                        initial.compare(coefficient,c,f'initial c {key} {order}',score=True)
                        initial.compare(residual,closed['E_best'],f'initial Ebest {key} {order}',score=True)
                        calibration.append(dict(grid=key,order=order,c=coefficient,E_best=residual))
                        cache[key,order] = dict(q=field['q'],F=field['F'])
                    emit('field_control',dict(state=name,grid=key,order=order,points=int(grid['r'].size)))
        for (name,key,order,p),actual in direct_cross.items():
            evaluator.compare(actual,direct_cross[name,'D12-64x128',128,p],
                              f'fixed direct routes {name} {key} {order} {p}')
        DETAILS['initial_calibration'] = calibration
        check(CHECK_NAMES[1], initial.record()['passed'], initial.record())
        check(CHECK_NAMES[2], evaluator.record()['passed'], evaluator.record())

    with phase('independent_weight_controls'):
        same = physics.gram(g0,g0)
        m11,m12,m22 = (physics.gram(fixture_geometry[0],fixture_geometry[0]),
                      physics.gram(fixture_geometry[0],fixture_geometry[1]),
                      physics.gram(fixture_geometry[1],fixture_geometry[1]))
        cases = [
            ('identical_positive',(same,same,same),(1.,0.),(1.,0.)),
            ('identical_negative',(same,same,same),(-1.,0.),(0.,0.)),
            ('identical_zero',(same,same,same),(0.,0.),(0.,0.)),
            ('first_component',(m11,m12,m22),(1.,0.),(1.,0.)),
            ('second_component',(m11,m12,m22),(0.,1.),(0.,1.)),
            ('interior_mixture',(m11,m12,m22),(2/3,1/3),(2/3,1/3)),
            ('signed_difference',(m11,m12,m22),(1.,-1.),(max(0.,(m11-m12)/m11),0.)),
        ]
        control_records = []
        for name,(a,b,d),(target1,target2),expected in cases:
            b1,b2 = target1*a+target2*b,target1*b+target2*d
            solved = search_module.solve_weights(b1,b2,a,b,d)
            charge('root_scalar_control_calls')
            charge('root_scalar_control_weight_attempts',solved['attempts'])
            pick = solved['selected']
            actual = [pick['Gamma']*(1-pick['eta']),pick['Gamma']*pick['eta']]
            scalar.compare(actual,expected,'independent coefficients '+name)
            if name.startswith('identical'):
                scalar.compare(pick['eta'],0.,'identical tie '+name)
            packet = dict(name=name,expected_coefficients=expected,actual_coefficients=actual,solver=solved)
            control_records.append(packet); emit('scalar_control',packet)
        DETAILS['scalar_controls'] = control_records
        check(CHECK_NAMES[3],scalar.record()['passed'],scalar.record())

    with phase('two_independent_searches'):
        for h in (.0625,.03125):
            result = search_module.search_one(q0,h,physics,emit,COUNTERS,DEADLINE)
            local = result['counters']
            searchchecks.condition(result['summary']['scheduled_search_completed'] and
                not result['summary']['early_success_shortcut'],f'complete search {h}')
            searchchecks.condition(local['search_initial_proposals']==1035 and
                result['summary']['bank_size']==45 and local['search_proposals']<=2280 and
                local['search_component_evaluations']<=1199 and
                local['search_weight_attempts']+local['search_control_attempts']<=9121,
                f'search budget {h}')
            if result['selected_record'] is not None:
                chosen,control = result['selected_record'],result['control']
                searchchecks.condition(chosen['J']+1e-10+1e-9*max(abs(chosen['J']),abs(control['J'])) >= control['J'],
                                       f'unchanged control retained {h}')
            STEPS.append(result)
        check(CHECK_NAMES[4],searchchecks.record()['passed'],searchchecks.record())

    with phase('unchanged_selected_confirmation'):
        for step in STEPS:
            h,selected = step['h'],step['selected_state']
            translated = dict(Gamma=gamma,eta=0.,geometry=[(1.,1.,c*h),(1.,1.,c*h)])
            translation_cross = {order:physics.cross(q0,translated['geometry'][0],order)
                                 for order in (64,128,256)}
            selected_cross = None if selected is None else {
                order:[physics.cross(q0,g,order) for g in selected['geometry']]
                for order in (64,128,256)}
            target_states = dict(unchanged=q0,translation=translated)
            if selected is not None:
                target_states['selected'] = selected
            norms = {name:model_norm(state,physics) for name,state in target_states.items()}
            q_cross = {name:[gamma*physics.gram(g0,g) for g in state['geometry']]
                       for name,state in target_states.items()}
            cross_by_model = dict(unchanged={order:[crosses['q0',0,order]]*2 for order in (64,128,256)},
                                 translation={order:[translation_cross[order]]*2 for order in (64,128,256)})
            if selected is not None:
                cross_by_model['selected'] = selected_cross
            scores = {}
            direct_models = {key:{name:model_values(state,grid) for name,state in target_states.items()}
                             for key,grid in grids.items()}
            for order in (64,128,256):
                for name,state in target_states.items():
                    for slot in range(2):
                        confirmation.compare(cross_by_model[name][order][slot]['total'],
                            cross_by_model[name][128][slot]['total'],f'confirmation heat {h} {name} {slot} {order}')
                Js = {}
                bs = {}
                for name,state in target_states.items():
                    bs[name] = [q_cross[name][slot]+h*cross_by_model[name][order][slot]['total']
                                for slot in range(2)]
                    B = math.fsum(((1-state['eta'])*bs[name][0],state['eta']*bs[name][1]))
                    Js[name] = 2*state['Gamma']*B-norms[name]
                confirmation.compare(Js['unchanged'],step['control']['J'],f'unchanged J {h} {order}')
                if selected is not None:
                    confirmation.compare(Js['selected'],step['selected_record']['J'],f'selected J {h} {order}')
                for key,grid in grids.items():
                    field = cache[key,order]
                    y = field['q']+h*field['F']
                    C = integral(y*y,grid)
                    require(C>0,'positive target norm')
                    route = dict(grid=key,heat_order=order,C=C,models={})
                    charge('root_confirmation_routes')
                    for name,state in target_states.items():
                        values,components = direct_models[key][name]
                        for slot,gvalues in enumerate(components):
                            confirmation.compare(integral(field['F']*gvalues,grid),
                                cross_by_model[name][order][slot]['total'],
                                f'confirmation direct F {h} {key} {order} {name} {slot}')
                            confirmation.compare(integral(y*gvalues,grid),bs[name][slot],
                                f'confirmation direct b {h} {key} {order} {name} {slot}')
                        N = integral((y-values)**2,grid)
                        require(N>=0,'negative direct square integral')
                        subtraction = C-Js[name]
                        confirmation.condition(subtraction>=0,f'unclipped subtraction {h} {key} {order} {name}',
                                               dict(C=C,J=Js[name],subtraction=subtraction))
                        confirmation.compare(N,subtraction,f'direct residual {h} {key} {order} {name}')
                        route['models'][name] = dict(N=N,J=Js[name],subtraction=subtraction,relative_error=math.sqrt(N/C))
                    if selected is not None:
                        delta = route['models']['unchanged']['N']-route['models']['selected']['N']
                        confirmation.compare(delta,Js['selected']-Js['unchanged'],
                                             f'direct improvement {h} {key} {order}')
                    scores[key,order] = route
                    emit('confirmation_route',dict(h=h,**route))
            primary = scores['D12-64x128',128]
            for (key,order),route in scores.items():
                for name in target_states:
                    confirmation.compare(route['models'][name]['relative_error'],
                        primary['models'][name]['relative_error'],f'score routes {h} {key} {order} {name}',score=True)
            moment_records = {}
            for name,state in target_states.items():
                moments = physics.moments(state)
                moment_records[name] = moments
                confirmation.condition(state['Gamma']>0 and 0<=state['eta']<=1 and
                    all(g[0]>0 and g[1]>0 for g in state['geometry']),f'positive state {h} {name}')
                confirmation.compare(moments['between']['centroid'],moments['raw']['centroid'],f'moment centroid {h} {name}')
                confirmation.compare(moments['between']['covariance'],moments['raw']['covariance'],f'moment covariance {h} {name}')
                covariance = moments['between']['covariance']
                confirmation.condition(math.isfinite(moments['I_z']) and moments['I_z']>0 and
                    covariance[0][0]>0 and covariance[1][1]>0 and
                    covariance[0][0]*covariance[1][1]-covariance[0][1]**2>0,f'finite positive moments {h} {name}')
            step['confirmation'] = dict(primary=primary, routes=list(scores.values()),moments=moment_records,
                selected_cross=selected_cross,translation_cross=translation_cross,
                components_distinct=None if selected is None else selected['geometry'][0]!=selected['geometry'][1],
                active_component_count=0 if selected is None else (2 if 0<selected['eta']<1 and
                    selected['geometry'][0]!=selected['geometry'][1] else 1),
                genuine_two_active_components=False if selected is None else (0<selected['eta']<1 and
                    selected['geometry'][0]!=selected['geometry'][1]),
                selected_improves_unchanged=None if selected is None else
                    primary['models']['selected']['N'] < primary['models']['unchanged']['N'],
                selected_improves_translation=None if selected is None else
                    primary['models']['selected']['N'] < primary['models']['translation']['N'])
        check(CHECK_NAMES[5],confirmation.record()['passed'],confirmation.record())

    with phase('work_accounting'):
        expected = dict(rule_count=5,rule_nodes=736,rule_eigh_calls=5,
            input_arrays_read=0,input_arrays_saved=0,phys_instances=1,
            phys_rule_transforms=3,phys_rule_nodes_transformed=448,
            phys_field_calls=30,phys_field_spatial_points=319566,
            phys_field_component_points=479349,phys_field_heat_integrand_points=71582784,
            phys_field_ordered_pair_points=798915,phys_initial_exact_calls=1,
            phys_initial_exact_points=13,root_scalar_control_calls=7,search_invocations=2,
            root_confirmation_routes=24,root_spatial_grids=4,root_spatial_grid_points=53248)
        positive = sum(step['selected_state'] is not None for step in STEPS)
        expected.update(phys_cross_calls=COUNTERS['search_cross_calls']+18+6+6*positive,
            phys_cross_ordered_pair_integrals=COUNTERS['search_cross_calls']+45+6+6*positive,
            phys_cross_integrand_points=COUNTERS['search_cross_calls']*128+15*448+2*448+2*positive*448,
            phys_moment_calls=4+positive)
        checks = {key:COUNTERS.get(key)==value for key,value in expected.items()}
        for key in search_module.COUNTER_KEYS:
            checks['sum_'+key] = COUNTERS.get(key,0)==sum(step['counters'][key] for step in STEPS)
        caps = dict(search_proposals=4560,search_component_evaluations=2398,
                    phys_cross_calls=2434,phys_cross_ordered_pair_integrals=2461,
                    phys_cross_integrand_points=316352,phys_peak_spatial_points=18432,
                    root_scalar_control_weight_attempts=28)
        for key,value in caps.items():
            checks['cap_'+key] = COUNTERS.get(key,0)<=value
        checks['all_nonnegative_integer_counts'] = all(type(v) is int and v>=0 for v in COUNTERS.values())
        check(CHECK_NAMES[6],all(checks.values()),dict(predicates=checks,expected=expected,caps=caps))

    with phase('identity_preservation'):
        preserved = True
        for path,expected_identity in BEFORE.items():
            preserved = (identity(path,'after')==expected_identity) and preserved
        hash_ok = (COUNTERS['root_input_files_hashed_before']==COUNTERS['root_input_files_hashed_after']==len(BEFORE)
                   and COUNTERS['root_input_bytes_hashed_before']==COUNTERS['root_input_bytes_hashed_after'])
        check(CHECK_NAMES[7],preserved and hash_ok,dict(preserved=preserved,hash_accounting=hash_ok))
    qualified = all(x['passed'] for x in CHECKS) and len(CHECKS)==8
    verdict = ('ordinary_current_state_evaluator_and_first_steps_qualified' if positive==2 else
               'qualified_no_positive_startup') if qualified else 'failed_qualification_no_retry'
    return dict(schema='t70-causal-projector-result-v1', verdict=verdict,
        numerical_qualified=qualified,runtime=DETAILS['runtime'],checks=CHECKS,counters=COUNTERS,
        steps=STEPS,details=DETAILS,phases_seconds=PHASES,inputs_preserved=preserved,
        input_identities=[dict(path=str(path.relative_to(REPO).as_posix()) if path.is_relative_to(REPO)
                               else str(path),**value) for path,value in BEFORE.items()],
        prior_scientific_child_seconds=1990.3707298998488,
        new_flow_trajectories=0,reference_arrays_loaded=0,full_task_validated=False,
        new_method_claim=False,formal_error_certificate=False,global_geometry_optimality_certified=False,
        exact_real_inner_optimality_certified=False,selected_tuples_unchanged_during_confirmation=True,
        child_elapsed_before_result_write_seconds=time.perf_counter()-START)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path,default=ROOT/'input-manifest.json')
    args = parser.parse_args()
    LOCAL.mkdir(exist_ok=True)
    with (LOCAL/'journal.jsonl').open('x',encoding='utf-8',newline='\n') as STREAM:
        try:
            output = main(args.manifest)
        except BaseException as exc:
            output = dict(schema='t70-causal-projector-result-v1',verdict='failed_qualification_no_retry',
                numerical_qualified=False,error_type=type(exc).__name__,error=str(exc),
                traceback=traceback.format_exc(),active_phase=ACTIVE,checks=CHECKS,
                counters=COUNTERS,steps=STEPS,details=DETAILS,phases_seconds=PHASES,
                inputs_preserved=False,child_elapsed_before_result_write_seconds=time.perf_counter()-START)
        with (LOCAL/'result.json').open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(output,stream,indent=2,allow_nan=False)
            stream.write('\n')
    sys.exit(0 if output['numerical_qualified'] else 2)

