"""Post-seal T71 scoring; no predictor calls, fitting, or scientific module imports."""
import hashlib
import json
import math
from pathlib import Path
import time

D0 = 1.0882203729522952
TIMES = (0., .25, .5, .75, 1.)
KEYS = ('q', 'qr', 'qz', 'r', 'rc', 'z')
ELIGIBILITY = 'tracks/tog/tasks/t61-saved-output-qualification/result.json'
EXPECTED = {
    'input_npz_files': 10, 'input_arrays': 60, 'input_array_bytes': 19722240,
    'raw_hashes': 20, 'reference_corner_cells': 3276800,
    'reference_polynomial_integrals': 10, 'reference_polynomial_node_cells': 4915200,
    'reference_polynomial_scalar_reductions': 540,
    'direct_scores': 40, 'reference_score_node_cells': 393216000,
    'reference_component_node_products': 786432000, 'reference_axis_exp_values': 460800,
    'reference_score_scalar_reductions': 24000, 'checkpoint_scores': 20,
    'reference_sensitivity_records': 10, 'time_routes': 68,
    'time_spatial_points': 905216, 'time_component_node_products': 3620864,
    'time_axis_exp_values': 65280, 'time_scalar_reductions': 136,
    'time_sensitivity_records': 17, 'moment_route_checks': 50,
}


class ScoringFailure(RuntimeError):
    pass


class _Scorer:
    def __init__(self, np, rules, counters, emit, repo, manifest, deadline_ns):
        self.np, self.rules, self.counters, self.emit = np, rules, counters, emit
        self.repo, self.manifest, self.deadline_ns = Path(repo).resolve(), manifest, deadline_ns
        self.start = time.perf_counter()
        self.local = {}
        self.result = dict(schema='t71-postprediction-score-v1', numerical_qualified=False,
            direct_scores=[], checkpoint_scores=[], reference_statistics=[],
            reference_sensitivity={'records': []}, time_sensitivity={'records': [], 'routes': []},
            raw_identities=[], array_layouts=[], checks={})

    def clock(self):
        if time.perf_counter_ns() >= self.deadline_ns:
            raise TimeoutError('T71 post-prediction scoring deadline')

    def require(self, condition, message):
        if not condition:
            raise ScoringFailure(message)

    def count(self, key, value=1):
        self.local[key] = self.local.get(key, 0) + value
        name = 'scorer_' + key
        self.counters[name] = self.counters.get(name, 0) + value

    def close(self, a, b, label):
        np = self.np
        x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        self.require(x.shape == y.shape and bool(np.all(np.isfinite(x)))
                     and bool(np.all(np.isfinite(y)))
                     and bool(np.all(np.abs(x-y) <= 1e-10 + 1e-9*np.maximum(np.abs(x), np.abs(y)))), label)

    def path(self, value):
        self.require(isinstance(value, str) and value and '\\' not in value,
                     'expected nonempty POSIX repository-relative path')
        p = Path(value)
        self.require(not p.is_absolute() and ':' not in value and '..' not in p.parts,
                     'unsafe evidence path')
        target = (self.repo / p).resolve()
        self.require(target.is_relative_to(self.repo), 'evidence escaped repository')
        return target

    def identity(self, record, raw=False):
        self.clock()
        digest, size = hashlib.sha256(), 0
        with self.path(record['path']).open('rb') as handle:
            while block := handle.read(1024*1024):
                self.clock()
                digest.update(block)
                size += len(block)
        actual = {'bytes': size, 'sha256': digest.hexdigest()}
        self.require(actual == {key: record[key] for key in actual}, 'evidence identity: '+record['path'])
        self.count('raw_hashes' if raw else 'nonarray_hashes')
        self.count('raw_hashed_bytes' if raw else 'nonarray_hashed_bytes', size)
        return actual

    def frozen_json(self, record):
        self.identity(record)
        return json.loads(self.path(record['path']).read_text(encoding='utf-8'))

    def seal(self, paths, prediction_seal, reference_records):
        self.clock()
        saved = self.frozen_json(prediction_seal)
        # JSON roundtrip changes tuples to lists only; no scalar adjustment is allowed.
        canonical = json.loads(json.dumps(paths, allow_nan=False))
        self.require(saved['paths'] == canonical, 'supplied paths differ from prediction seal')
        self.require(len(paths) == 2, 'two complete causal paths required')
        for path, steps in zip(paths, (16, 32)):
            self.require(path['h'] == 1./steps and path['completed_steps'] == steps
                         and len(path['steps']) == steps+1, 'path schedule')
            for i, record in enumerate(path['steps']):
                self.require(record['step'] == i and record['time'] == i/steps, 'path time/index')
                self.state(record['state'])
                self.moments(record['state'], record['moments'])
        self.result['prediction_seal'] = prediction_seal
        inputs = {item['path']: item for item in self.manifest['inputs']}
        raw_inputs = {item['path']: item for item in self.manifest['raw_inputs']}
        self.require(len(raw_inputs) == len(self.manifest['raw_inputs']) == 10, 'raw allowlist size')
        self.require(len(reference_records) == 10 and
                     {(r['name'], r['index']) for r in reference_records} ==
                     {(name, i) for name in ('S256', 'S128') for i in range(5)}, 'reference schedule')
        self.require({r['raw']['path'] for r in reference_records} == set(raw_inputs), 'raw allowlist mismatch')
        for record in reference_records:
            self.require(record['time'] == TIMES[record['index']], 'reference time')
            self.require(record['raw'] == raw_inputs[record['raw']['path']], 'frozen raw identity tuple')
            self.require(record['metadata'] == inputs[record['metadata']['path']], 'frozen metadata tuple')
        eligible = self.frozen_json(inputs[ELIGIBILITY])
        self.require(eligible['schema'] == 't61-saved-output-qualification-v1'
                     and eligible['accepted_saved_evidence'] is True
                     and eligible['reference_qualified_full_window'] is True
                     and eligible['meaningful_motion'] is True
                     and eligible['T60_history_reclassified'] is False, 'T61 saved reference eligibility')
        self.result['reference_eligibility'] = inputs[ELIGIBILITY]
        self.result['checks']['prediction_sealed_before_reference'] = True
        self.result['checks']['saved_reference_eligibility'] = True
        self.emit('scorer_prediction_seal_verified', {'prediction_seal': prediction_seal})

    def state(self, state):
        gamma, eta, geometry = state['Gamma'], state['eta'], state['geometry']
        self.require(math.isfinite(gamma) and gamma > 0. and math.isfinite(eta)
                     and 0. <= eta <= 1. and len(geometry) == 2, 'positive finite mixture state')
        for g in geometry:
            self.require(len(g) == 3 and all(math.isfinite(x) for x in g)
                         and g[0] > 0. and g[1] > 0., 'positive finite geometry')

    def moments(self, state, moments):
        self.clock()
        self.close(moments['Gamma'], state['Gamma'], 'stored circulation and state')
        a, b = moments['between'], moments['raw']
        self.close(a['centroid'], b['centroid'], 'moment centroid routes')
        self.close(a['covariance'], b['covariance'], 'moment covariance routes')
        mean = b['centroid']
        recovered = [[b['raw_second'][i][j]-mean[i]*mean[j] for j in range(2)] for i in range(2)]
        self.close(recovered, b['covariance'], 'raw second-moment reconstruction')
        covariance = a['covariance']
        self.require(covariance[0][0] > 0. and covariance[1][1] > 0.
                     and covariance[0][0]*covariance[1][1] > covariance[0][1]**2
                     and math.isfinite(moments['I_z']) and moments['I_z'] > 0., 'positive model moments')
        self.close(covariance[0][1], covariance[1][0], 'symmetric model covariance')
        self.count('moment_route_checks')

    def load(self, record):
        self.clock()
        raw, meta_record = record['raw'], record['metadata']
        metadata = self.frozen_json(meta_record)
        n, index = int(record['name'][1:]), record['index']
        self.require((metadata['name'], metadata['index'], metadata['time'], metadata['nr'],
                      metadata['nz'], metadata['R'], metadata['h']) ==
                     (record['name'], index, TIMES[index], n, 2*n, 8., 8./n), 'reference metadata grid')
        self.require(metadata['whole_task_qualified'] is False, 'preserve original checkpoint status')
        self.require(metadata['raw']['path'] == Path(raw['path']).name and
                     {k: metadata['raw'][k] for k in ('bytes','sha256')} ==
                     {k: raw[k] for k in ('bytes','sha256')}, 'snapshot raw identity chain')
        if not self.result['raw_identities']:
            self.emit('first_raw_hash', {'path': raw['path'], 'prediction_seal': self.result['prediction_seal']})
        before = self.identity(raw, raw=True)
        self.result['raw_identities'].append({'path': raw['path'], 'before': before, 'after': None})
        np, data = self.np, {}
        with np.load(self.path(raw['path']), allow_pickle=False) as archive:
            self.count('input_npz_files')
            for key in KEYS:
                self.clock()
                value = archive[key]
                shape = (n, 2*n) if key in KEYS[:3] else ((2*n,) if key == 'z' else (n,))
                self.require(value.shape == shape and value.dtype == np.dtype('float64')
                             and bool(np.all(np.isfinite(value))), 'reference array layout: '+key)
                data[key] = value
                self.count('input_arrays')
                self.count('input_array_bytes', int(value.nbytes))
                layout = dict(path=raw['path'], name=record['name'], index=index,
                              key=key, shape=list(value.shape), dtype=str(value.dtype), bytes=int(value.nbytes))
                self.result['array_layouts'].append(layout)
                self.emit('reference_array_decoded', layout)
        h = 8./n
        rf, zf = np.arange(n+1)*h, -8.+np.arange(2*n+1)*h
        area = (rf[1:]**2-rf[:-1]**2)/2.
        expected = dict(r=(rf[:-1]+rf[1:])/2., z=(zf[:-1]+zf[1:])/2.,
                        rc=(rf[1:]**3-rf[:-1]**3)/(3.*area))
        for key, expected_value in expected.items():
            self.require(bool(np.all(np.diff(data[key]) > 0.)) and np.array_equal(data[key], expected_value),
                         'reference coordinate identity: '+key)
        self.require(bool(np.all(data['q'] >= 0.)), 'reference negative cell average')
        minimum = math.inf
        for radial in (rf[:-1], rf[1:]):
            for axial in (-h/2., h/2.):
                self.clock()
                corner = data['q']+data['qr']*(radial-data['rc'])[:,None]+data['qz']*axial
                self.count('reference_corner_cells', int(corner.size))
                self.require(bool(np.all(np.isfinite(corner))) and bool(np.all(corner >= 0.)), 'PL corner positivity')
                minimum = min(minimum, float(np.min(corner)))
        data.update(h=h, n=n, metadata=metadata, minimum_corner=minimum)
        return data

    def sample(self, f, xr, xz):
        rn, zn = f['r']+xr*f['h']/2., f['z']+xz*f['h']/2.
        q = f['q']+f['qr']*(rn-f['rc'])[:,None]+f['qz']*(zn-f['z'])[None,:]
        self.require(bool(self.np.all(self.np.isfinite(q))) and bool(self.np.all(q >= 0.)), 'PL node positivity')
        return rn, zn, q

    def statistics(self, f):
        np, terms = self.np, [[] for _ in range(9)]
        for xr, wr in zip(*self.rules[3]):
            for xz, wz in zip(*self.rules[2]):
                self.clock()
                rn, zn, q = self.sample(f, xr, xz)
                r, z = rn[:,None], zn[None,:]
                w = wr*wz*f['h']**2/4.*r
                density = w*q
                values = (np.sum(density), np.sum(density*r), np.sum(density*z),
                          np.sum(density*r*r), np.sum(density*r*z), np.sum(density*z*z),
                          2.*math.pi*np.sum(w*q*q), math.pi*np.sum(density*r*r),
                          2.*math.pi*np.sum(w*r*r*q*q))
                for target, value in zip(terms, values):
                    target.append(float(value))
                self.count('reference_polynomial_node_cells', int(q.size))
                self.count('reference_polynomial_scalar_reductions', 9)
        t = [math.fsum(x) for x in terms]
        self.require(all(math.isfinite(x) for x in t) and t[0] > 0. and t[8] > 0., 'positive reference norms')
        mean = [t[1]/t[0], t[2]/t[0]]
        cov = [[t[3]/t[0]-mean[0]**2, t[4]/t[0]-mean[0]*mean[1]],
               [t[4]/t[0]-mean[0]*mean[1], t[5]/t[0]-mean[1]**2]]
        record = dict(circulation=t[0], centroid=mean, covariance=cov, q_squared_integral=t[6],
                      axial_impulse=t[7], vorticity_squared_integral=t[8])
        for key, value in record.items():
            self.close(value, f['metadata']['statistics'][key], 'reference statistics: '+key)
        if f['metadata']['name'] == 'S256' and f['metadata']['index'] == 0:
            self.close(math.sqrt(math.fsum(x*x for row in cov for x in row)), D0, 'fixed initial S256 denominator')
        self.count('reference_polynomial_integrals')
        return record

    def factors(self, state, radial, axial, prefix):
        np, factors = self.np, []
        for sr, sz, z0 in state['geometry']:
            fr = np.exp(-.5*(radial/sr)**2)/(sr*sr)
            fz = np.exp(-.5*((axial-z0)/sz)**2)/(math.sqrt(2.*math.pi)*sz)
            self.count(prefix+'_axis_exp_values', int(radial.size+axial.size))
            self.require(bool(np.all(np.isfinite(fr))) and bool(np.all(np.isfinite(fz)))
                         and bool(np.all(fr >= 0.)) and bool(np.all(fz >= 0.)), 'finite nonnegative Gaussian factors')
            self.count(prefix+'_axis_underflow_zeros', int(np.count_nonzero(fr == 0.)+np.count_nonzero(fz == 0.)))
            factors.append((fr, fz))
        return factors

    def direct(self, f, state, orders, reference_norm):
        np, (nr, nz), started = self.np, orders, time.perf_counter()
        xr, wr = self.rules[nr]
        xz, wz = self.rules[nz]
        radial = f['r'][None,:]+xr[:,None]*f['h']/2.
        axial = f['z'][None,:]+xz[:,None]*f['h']/2.
        factors = self.factors(state, radial, axial, 'reference')
        terms = [[] for _ in range(5)]
        for i in range(nr):
            for j in range(nz):
                self.clock()
                rn, _, reference = self.sample(f, xr[i], xz[j])
                model = state['Gamma']*((1.-state['eta'])*factors[0][0][i,:,None]*factors[0][1][j,None,:]
                                       + state['eta']*factors[1][0][i,:,None]*factors[1][1][j,None,:])
                w = wr[i]*wz[j]*f['h']**2/4.*rn[:,None]
                physical = 2.*math.pi*rn[:,None]**2*w
                values = (np.sum(physical*(model-reference)**2), np.sum(physical*reference**2),
                          np.sum(w*model), math.pi*np.sum(w*rn[:,None]**2*model), np.sum(physical*model**2))
                for target, value in zip(terms, values):
                    target.append(float(value))
                self.count('reference_score_node_cells', int(reference.size))
                self.count('reference_component_node_products', int(reference.size)*2)
                self.count('reference_score_scalar_reductions', 5)
        N, D, gamma, impulse, norm = [math.fsum(x) for x in terms]
        self.require(all(math.isfinite(x) and x >= 0. for x in (N,D,gamma,impulse,norm)) and D > 0., 'direct score values')
        self.close(D, reference_norm, 'direct denominator versus polynomial reference norm')
        self.count('direct_scores')
        return dict(orders=list(orders), numerator=N, denominator=D, relative_error=math.sqrt(N/D),
                    model_D8_circulation=gamma, model_D8_impulse=impulse, model_D8_vorticity_squared=norm,
                    elapsed_seconds=time.perf_counter()-started)

    def moment_errors(self, model, reference):
        mean, cov = model['between']['centroid'], model['between']['covariance']
        mean_delta = [mean[i]-reference['centroid'][i] for i in range(2)]
        cov_delta = [[cov[i][j]-reference['covariance'][i][j] for j in range(2)] for i in range(2)]
        return dict(axial_centroid_error=abs(mean_delta[1]),
                    normalized_covariance_error=math.sqrt(math.fsum(x*x for row in cov_delta for x in row))/D0,
                    signed_centroid_difference=mean_delta, signed_covariance_difference=cov_delta,
                    circulation_difference=model['Gamma']-reference['circulation'],
                    impulse_difference=model['I_z']-reference['axial_impulse'])

    def references(self, paths, records):
        for record in sorted(records, key=lambda x: (0 if x['name']=='S256' else 1, x['index'])):
            started = time.perf_counter()
            f = self.load(record)
            stats = self.statistics(f)
            self.result['reference_statistics'].append(dict(name=record['name'], index=record['index'],
                time=record['time'], statistics=stats, minimum_corner=f['minimum_corner']))
            for path_index, path in enumerate(paths):
                step = record['index']*(4 if path_index == 0 else 8)
                predicted = path['steps'][step]
                scores = []
                for orders in ((8,6), (16,12)):
                    score = self.direct(f, predicted['state'], orders, stats['vorticity_squared_integral'])
                    score.update(path_index=path_index, h=path['h'], name=record['name'], index=record['index'], time=record['time'])
                    scores.append(score)
                    self.result['direct_scores'].append(score)
                    self.emit('reference_direct_score', score)
                for key in ('numerator','denominator','model_D8_circulation','model_D8_impulse','model_D8_vorticity_squared'):
                    self.close(scores[0][key], scores[1][key], 'direct scoring rule agreement: '+key)
                self.require(abs(scores[0]['relative_error']-scores[1]['relative_error']) <= 1e-8, 'direct scoring dimensionless agreement')
                errors = self.moment_errors(predicted['moments'], stats)
                gates = dict(field=scores[0]['relative_error'] <= .1,
                             centroid=errors['axial_centroid_error'] <= .1,
                             covariance=errors['normalized_covariance_error'] <= .1)
                packet = dict(path_index=path_index, h=path['h'], name=record['name'], index=record['index'], time=record['time'],
                              primary=scores[0], confirmation=scores[1], moment_errors=errors,
                              model_moments=predicted['moments'], gates=gates, passed=all(gates.values()))
                self.result['checkpoint_scores'].append(packet)
                self.count('checkpoint_scores')
            del f
            after = self.identity(record['raw'], raw=True)
            self.result['raw_identities'][-1]['after'] = after
            self.emit('reference_snapshot_scored', dict(name=record['name'], index=record['index'],
                raw_identity=self.result['raw_identities'][-1], elapsed_seconds=time.perf_counter()-started))
        for path_index in range(2):
            for index in range(5):
                pair = [next(s for s in self.result['checkpoint_scores'] if
                             (s['path_index'],s['index'],s['name']) == (path_index,index,name)) for name in ('S256','S128')]
                a, b = pair
                delta = dict(field=abs(a['primary']['relative_error']-b['primary']['relative_error']),
                    centroid=abs(a['moment_errors']['axial_centroid_error']-b['moment_errors']['axial_centroid_error']),
                    covariance=abs(a['moment_errors']['normalized_covariance_error']-b['moment_errors']['normalized_covariance_error']))
                entry = dict(path_index=path_index, time=TIMES[index], differences=delta,
                             passed=all(v <= .01 for v in delta.values()))
                self.result['reference_sensitivity']['records'].append(entry)
                self.count('reference_sensitivity_records')
        self.result['reference_sensitivity']['passed'] = all(x['passed'] for x in self.result['reference_sensitivity']['records'])
        motion = []
        for name in ('S256','S128'):
            endpoints = [next(x['statistics']['centroid'][1] for x in self.result['reference_statistics']
                              if (x['name'],x['index']) == (name,index)) for index in (0,4)]
            displacement = endpoints[1]-endpoints[0]
            motion.append(dict(name=name, initial_axial_centroid=endpoints[0],
                final_axial_centroid=endpoints[1], axial_displacement=displacement, passed=displacement >= .25))
        self.result['reference_motion'] = {'records':motion, 'passed':all(x['passed'] for x in motion)}
        self.require(self.result['reference_motion']['passed'], 'saved reference meaningful axial displacement')
        self.result['meaningful_motion'] = True

    def time_scores(self, paths):
        np, grids = self.np, []
        for R in (8.,12.):
            for nr,nz in ((64,128),(96,192)):
                xr,wr = self.rules[nr]
                xz,wz = self.rules[nz]
                r,z = R*(xr+1.)/2., R*xz
                w = 2.*math.pi*r[:,None]**3*(R*wr[:,None]/2.)*(R*wz[None,:])
                grids.append((R,nr,nz,r,z,w))
        for k in range(17):
            a,b = paths[0]['steps'][k], paths[1]['steps'][2*k]
            routes = []
            for R,nr,nz,r,z,w in grids:
                self.clock()
                models = []
                for predicted in (a,b):
                    state = predicted['state']
                    f = self.factors(state, r, z, 'time')
                    model = state['Gamma']*((1.-state['eta'])*f[0][0][:,None]*f[0][1][None,:]
                                           +state['eta']*f[1][0][:,None]*f[1][1][None,:])
                    models.append(model)
                N,D = float(np.sum(w*(models[0]-models[1])**2)), float(np.sum(w*models[1]**2))
                self.require(math.isfinite(N) and N >= 0. and math.isfinite(D) and D > 0., 'time direct nonnegative norms')
                route = dict(time=k/16., R=R, orders=[nr,nz], numerator=N, denominator=D, relative_error=math.sqrt(N/D))
                routes.append(route)
                self.result['time_sensitivity']['routes'].append(route)
                self.count('time_routes')
                self.count('time_spatial_points', nr*nz)
                self.count('time_component_node_products', 4*nr*nz)
                self.count('time_scalar_reductions', 2)
            self.require(all(abs(x['relative_error']-routes[0]['relative_error']) <= 1e-8 for x in routes), 'time spatial/domain score agreement')
            ma,mb = a['moments']['between'], b['moments']['between']
            dz = abs(ma['centroid'][1]-mb['centroid'][1])
            covariance = [[ma['covariance'][i][j]-mb['covariance'][i][j] for j in range(2)] for i in range(2)]
            dc = math.sqrt(math.fsum(x*x for row in covariance for x in row))/D0
            gates = dict(field=routes[0]['relative_error'] <= .01, centroid=dz <= .01, covariance=dc <= .01)
            entry = dict(time=k/16., primary=routes[0], axial_centroid_difference=dz,
                         normalized_covariance_difference=dc, gates=gates, passed=all(gates.values()))
            self.result['time_sensitivity']['records'].append(entry)
            self.count('time_sensitivity_records')
            self.emit('time_sensitivity_scored', entry)
        self.result['time_sensitivity']['passed'] = all(x['passed'] for x in self.result['time_sensitivity']['records'])

    def finish(self):
        self.clock()
        for key,value in EXPECTED.items():
            self.require(self.local.get(key,0) == value, 'fixed scorer work count: '+key)
        self.require(all(x['before'] == x['after'] for x in self.result['raw_identities']), 'raw preservation')
        self.result['checks'].update(reference_layout_and_polynomial_readback=True,
            reference_score_integration=True, time_comparison_integration=True,
            stored_moment_routes=True, fixed_work_accounting=True, raw_identity_preservation=True)
        self.result['physical_pass_primary'] = all(x['passed'] for x in self.result['checkpoint_scores'] if x['name']=='S256')
        self.result['physical_pass_sensitivity_reference'] = all(x['passed'] for x in self.result['checkpoint_scores'] if x['name']=='S128')
        self.result['physical_pass_both_references'] = all(x['passed'] for x in self.result['checkpoint_scores'])
        self.result.update(numerical_qualified=True, covariance_denominator=D0,
                           counters=dict(self.local), elapsed_seconds=time.perf_counter()-self.start)
        return self.result


def score_paths(np, rules, physics, counters, emit, paths, reference_records, repo, manifest,
                deadline_ns, *, prediction_seal):
    """Score fixed sealed paths; physics is passed for API symmetry but never called."""
    scorer = _Scorer(np,rules,counters,emit,repo,manifest,deadline_ns)
    try:
        scorer.seal(paths,prediction_seal,reference_records)
        scorer.references(paths,reference_records)
        scorer.time_scores(paths)
        return scorer.finish()
    except Exception as error:
        scorer.result.update(counters=dict(scorer.local), elapsed_seconds=time.perf_counter()-scorer.start,
                             failure={'type':type(error).__name__, 'message':str(error)})
        error.partial_result = scorer.result
        raise
