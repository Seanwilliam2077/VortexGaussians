"""Independent saved-array audit. Default is a stdlib-only plan; --execute is CPU only."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
TASK = HERE.parent / 'tog/tasks/t12-ordinary-wind-response-extrema'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(run, stage):
    import numpy as np
    s = json.loads((run / 'summary.json').read_text())
    config = json.loads((TASK / 'config.json').read_text())
    freeze = json.loads((TASK / 'freeze.json').read_text())
    result = {'stage': stage, 'scope': 'CPU saved arrays; no Torch, producer import, simulation, rendering or AD',
              'numpy': np.__version__, 'scriptSHA256': sha(__file__), 'failures': [], 'files': {}, 'recomputed': {}}
    def require(label, condition):
        if not condition:
            result['failures'].append(label)
    def mx(a):
        return float(np.max(np.abs(a)))
    def near(a, b):
        return bool(np.allclose(a, b, atol=1e-11, rtol=1e-12))
    def raw(a):
        return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
    def read(name):
        path = run / name
        pin = s['raw'][name]
        require(name + ' file SHA/bytes', sha(path) == pin['sha256'] and path.stat().st_size == pin['bytes'])
        with np.load(path, allow_pickle=False) as z:
            a = {k: z[k].copy() for k in z.files}
        require(name + ' members', set(a) == set(pin['arrays']))
        for k, v in a.items():
            p = pin['arrays'][k]
            require(name + '/' + k, list(v.shape) == p['shape'] and v.dtype.str == p['dtype']
                    and raw(v) == p['rawSHA256'] and bool(np.isfinite(v).all()))
        result['files'][name] = {'sha256': sha(path), 'bytes': path.stat().st_size, 'arrays': len(a)}
        return a
    for name, pin in freeze['sources'].items():
        p = TASK / pin['path']
        require('source ' + name, sha(p) == pin['sha256'] and p.stat().st_size == pin['bytes']
                and s['sourcesBefore'][name] == pin)
        if stage == 'final':
            require('source after ' + name, s['sourcesAfter'][name] == pin)
    require('freeze SHA', sha(TASK / 'freeze.json') == s['freezeSHA256'])
    result['sourcePins'] = freeze['sources']
    result['freezeSHA256'] = sha(TASK / 'freeze.json')
    ref = read('reference.npz')
    codes = np.floor(255 * ref['observation_alpha'] + .5).clip(0, 255).astype(np.uint8)
    lower, upper = np.maximum((codes.astype(float) - .5) / 255, 0), np.minimum((codes.astype(float) + .5) / 255, 1)
    denominator = float(ref['observation_alpha'][-1].sum())
    require('reference quantization/interval/denominator', np.array_equal(codes, ref['observed_uint8'])
            and near(lower, ref['lower']) and near(upper, ref['upper']) and denominator > 0
            and near(denominator, ref['denominator']))
    n = config['model']['n']
    h = 1 / n
    def div(v):
        return sum((np.roll(v[j], -1, axis=j) - v[j]) / h for j in range(3))
    ijk = np.stack(np.meshgrid(*([np.arange(n)] * 3), indexing='ij'), -1)
    edge = (ijk + np.array([0, 0, .5])) * h
    dist = (edge - np.asarray(config['wind']['potential_center']) + .5) % 1 - .5
    az = dist[..., 1] * np.exp(-np.sum(dist**2, axis=-1) / (2 * config['wind']['sigma']**2))
    unscaled = np.stack(((np.roll(az, -1, axis=1) - az) / h,
                         -(np.roll(az, -1, axis=0) - az) / h, np.zeros_like(az)))
    wind = unscaled * (config['wind']['max_component'] / mx(unscaled))
    require('wind potential/curl/scale', near(az, ref['potential']) and near(wind, ref['wind']))
    require('wind MAC divergence', mx(div(ref['wind'])) <= config['gates']['divergence_inf'])
    result['wind'] = {'potentialMaxError': mx(az - ref['potential']), 'forceMaxError': mx(wind - ref['wind']),
                      'divergenceInf': mx(div(ref['wind'])), 'maxComponent': mx(ref['wind']),
                      'phaseScope': 'Source read: future updates 0..9 force, 10..19 zero. Saved first density/alpha delay checked; no replay.'}
    x0, y0, x1, y1 = config['response']['roi']
    gate = config['gates']
    def values(a, name):
        alpha, v = a['observation_alpha'], a['initial_velocity']
        require(name + ' shapes', alpha.shape == (20, 64, 64) and a['future_alpha'].shape == (2, 20, 64, 64))
        c = np.concatenate((255 * (lower - alpha).ravel(), 255 * (alpha - upper).ravel(),
                            [mx(v) / config['velocity']['initial_max_component'] - 1,
                             float(np.mean(v*v)) / config['velocity']['initial_component_rms']**2 - 1]))
        gs = a['future_alpha'][:, -1, y0:y1, x0:x1].sum(axis=(1, 2)) / denominator
        d = float(gs[1] - gs[0])
        require(name + ' constraints', near(c, a['constraints']) and c.shape == (163842,))
        if 'd' in a:
            require(name + ' d', near(d, a['d']))
        stats = a['state_metrics']
        finite = all(bool(np.isfinite(v).all()) for v in a.values())
        numerical = (finite and stats.shape == (60, 6) and bool(np.all(stats[:, 5] == 1))
                     and float(stats[:, 0].max()) <= gate['divergence_inf']
                     and mx(div(v)) <= gate['divergence_inf']
                     and float(stats[:, 1].min()) >= gate['density_min']
                     and float(stats[:, 3].min()) >= gate['alpha_min'] and float(stats[:, 4].max()) <= gate['alpha_max'])
        violation = np.maximum(np.maximum(lower - alpha, alpha - upper), 0)
        different = np.floor(255 * alpha + .5).clip(0, 255).astype(np.uint8) != codes
        qualified = (numerical and float(violation.max()) <= gate['interval_alpha_tolerance']
                     and mx(v) <= config['velocity']['initial_max_component']
                     and float(np.sqrt(np.mean(v*v))) <= config['velocity']['initial_component_rms'])
        first_rho_error = mx(a['first_future_density'][0] - a['first_future_density'][1])
        first_alpha_error = mx(a['future_alpha'][0, 0] - a['future_alpha'][1, 0])
        require(name + ' first future delay', first_rho_error == 0 and first_alpha_error == 0)
        for velocity in [a['observation_velocity20'], *a['final_velocity']]:
            require(name + ' stored v divergence', mx(div(velocity)) <= gate['divergence_inf'])
        row = {'d': d, 'g': gs.tolist(), 'constraintsMaxDifference': mx(c-a['constraints']),
               'intervalMaxViolation': float(violation.max()), 'intervalBadPixels': int((violation > gate['interval_alpha_tolerance']).sum()),
               'quantizedDifferentPixels': int(different.sum()), 'initialMaxComponent': mx(v),
               'initialComponentRMS': float(np.sqrt(np.mean(v*v))), 'numericalPassed': numerical,
               'qualified': qualified, 'firstFutureDensityMaxDifference': first_rho_error,
               'firstFutureAlphaMaxDifference': first_alpha_error}
        result['recomputed'][name] = row
        return d, c, row
    _, _, rm = values(ref, 'reference')
    require('reference eligible', rm['qualified'])
    analytic = read('qualification/analytic.npz')
    d0, c0, am = values(analytic, 'G0 analytic')
    qc = config['qualification']
    lam = analytic['multipliers']
    require('G0 fixed multipliers', bool(np.all(lam == qc['multiplier'])))
    def objective(d, c):
        p = qc['penalty']
        return config['response']['objective_scale'] * d + float(np.sum(np.maximum(lam+p*c, 0)**2-lam**2)/(2*p))
    loss0 = objective(d0, c0)
    require('G0 scalar', near(loss0, analytic['loss']) and am['numericalPassed'])
    branch = lam + qc['penalty'] * c0
    require('G0 active branches', int((branch > 0).sum()) == s['qualification']['activePHRBranches'])
    result['G0'] = {'d': d0, 'loss': loss0, 'lossReductionDifference': float(loss0-analytic['loss'].item()),
                    'activeBranches': int((branch > 0).sum()), 'minimumAbsoluteBranch': float(np.abs(branch).min()), 'directions': []}
    for i in range(qc['directions']):
        direction = read(f'qualification/direction-{i}.npz')['direction']
        norm = float(np.sqrt(np.sum(direction**2)))
        require('L2 unit direction ' + str(i), abs(norm-1) <= 1e-12)
        dots = {k: float(np.sum(analytic['gradient_'+k]*direction)) for k in ('d', 'loss')}
        row = {'index': i, 'L2Norm': norm, 'dots': dots, 'h': []}
        for hi, step in enumerate(qc['h']):
            calculated = []
            for sign, label in [(1, 'plus'), (-1, 'minus')]:
                name = f'qualification/probe-{i}-{hi}-{label}.npz'
                a = read(name)
                require(name + ' theta perturbation', near(a['theta'], analytic['theta'] + sign*step*direction))
                d, c, metrics = values(a, name)
                loss = objective(d, c)
                require(name + ' numerical/scalar', metrics['numericalPassed'] and near(loss, a['loss']))
                calculated.append({'d': d, 'loss': loss})
            errors = {}
            for k in ('d', 'loss'):
                fd = (calculated[0][k]-calculated[1][k])/(2*step)
                relative = abs(fd-dots[k])/max(abs(dots[k]), qc['denominator_floor'])
                errors[k] = {'fd': fd, 'relativeError': relative}
                require(f'G0 {i}/{step}/{k}', bool(np.isfinite(relative)) and relative <= qc['relative_gate'])
            row['h'].append({'value': step, 'errors': errors})
        result['G0']['directions'].append(row)
    qsum = s['qualification']
    require('G0 recorded count/memory', qsum['evaluations'] == 9 and qsum['backwardCalls'] == 2
            and qsum['memory']['peakAllocatedBytes'] <= qc['peak_allocated_limit_bytes']
            and qsum['memory']['peakReservedBytes'] <= qc['peak_reserved_limit_bytes'])
    result['G0']['memoryReported'] = qsum['memory']
    result['G0']['secondsReported'] = qsum['secondsIncludingIO']
    if stage == 'final':
        require('whole run completed', s['status'] == 'completed' and len(s['extremes']) == 2)
        endpoints = []
        for summary in s['extremes']:
            arm = summary['extreme']
            best = read(arm+'/best-evaluated.npz'); final = read(arm+'/final-verification.npz')
            _, _, bm = values(best, arm+' best'); _, _, fm = values(final, arm+' final')
            require(arm+' endpoint qualification', bm['qualified'] and fm['qualified'] and summary['finalQualified'] == fm['qualified'])
            compare = {k: {'maxAbs': mx(best[k]-final[k]), 'bytesEqual': raw(best[k]) == raw(final[k])} for k in final}
            require(arm+' theta retained', raw(best['theta']) == raw(final['theta']))
            calls = summary['calls']
            require(arm+' actual budget', summary['evaluationsStarted'] == len(calls) <= config['optimizer']['max_evaluations_per_extreme']
                    and summary['evaluationsCompleted'] == sum(bool(v.get('forwardCompleted')) for v in calls)
                    and sum(v['origin']=='seed_initial' for v in calls) == 1
                    and sum(v['origin']=='mandatory_best_verification' for v in calls) == 1)
            require(arm+' final metrics', near(fm['d'], summary['finalMetrics']['d']))
            require(arm+' backward count', summary['backwardCalls'] == sum(bool(v['gradient']) for v in calls))
            require(arm+' acceptance/cache accounting', len(summary['accepted']) == summary['returnedSteps']+1
                    and summary['cacheHits']+summary['cacheMisses'] == summary['returnedSteps'])
            classifications = []
            for call in calls:
                m = call['metrics']
                reasons = []
                if not m['numericalPassed']:
                    reasons.append('numerical')
                if m['intervalMaxAlphaViolation'] > gate['interval_alpha_tolerance']:
                    reasons.append('pixel_interval')
                if m['initialVelocityMaxComponent'] > config['velocity']['initial_max_component']:
                    reasons.append('initial_velocity_max')
                if m['initialVelocityComponentRMS'] > config['velocity']['initial_component_rms']:
                    reasons.append('initial_velocity_rms')
                require(arm+' call eligibility '+str(call['evaluation']), m['qualified'] == (not reasons)
                        and (m['intervalViolatingPixels'] == 0) == (m['intervalMaxAlphaViolation'] <= gate['interval_alpha_tolerance']))
                classifications.append({'evaluation': call['evaluation'], 'origin': call['origin'],
                    'qualified': not reasons, 'failedGates': reasons, 'd': m['d'],
                    'intervalMaxAlphaViolation': m['intervalMaxAlphaViolation'],
                    'intervalViolatingPixels': m['intervalViolatingPixels']})
            invalid = [v for v in classifications if not v['qualified']]
            qualified_ids = [v['evaluation'] for v in classifications if v['qualified']]
            trial_review = {'scope': 'Independent classification of saved per-call metrics, not reconstruction of unsaved trial arrays.',
                'qualifiedEvaluationIDs': qualified_ids, 'invalidCount': len(invalid),
                'failedGateCounts': {k: sum(k in v['failedGates'] for v in invalid) for k in
                    ['numerical', 'pixel_interval', 'initial_velocity_max', 'initial_velocity_rms']},
                'minimumMaximumIntervalViolation': min(invalid, key=lambda v:v['intervalMaxAlphaViolation']) if invalid else None,
                'minimumViolatingPixelCount': min((v['intervalViolatingPixels'] for v in invalid), default=0),
                'calls': classifications, 'bestUpdatesRecorded': summary['bestUpdates'],
                'identityLimit': 'Trial theta arrays were not saved. The first closure is at seed by source order; other failed calls have distinct observations. No claim about the number of distinct parameter vectors.'}
            endpoints.append({'arm': arm, 'metrics': fm, 'bestVsFinal': compare, 'calls': len(calls),
                              'backwardCallsReported': summary['backwardCalls'], 'secondsReported': summary['secondsIncludingFinalAndIO'],
                              'termination': summary['termination'], 'selectedOrigin': summary['selectedOrigin'],
                              'finalThetaEqualsSeedBytes': raw(final['theta']) == raw(ref['seed_theta']),
                              'trialReview': trial_review})
        result['endpoints'] = endpoints
        expected = 10 + sum(x['calls'] for x in endpoints)
        require('aggregate evaluations/steps', s['actualWork']['fullEvaluationsStarted'] == expected
                and s['actualWork']['fullEvaluationsCompleted'] == expected and s['actualWork']['stepsCompleted'] == expected*60)
        require('aggregate backward calls', s['actualWork']['reverseCalls'] == 2+sum(x['backwardCallsReported'] for x in endpoints))
        require('runtime inputs fixed', s['runtimeInputsBefore'] == s['runtimeInputsAfter'])
        result['costsReported'] = {'setup': s['setup']['secondsIncludingIO'], 'G0': qsum['secondsIncludingIO'],
                                  'actualWork': s['actualWork'], 'workerSeconds': s['workerWallSeconds']}
        result['summarySHA256'] = sha(run/'summary.json')
    result['limitations'] = ['Not an independent AD, simulation or renderer run. Saved gradients are checked against independent scalar finite differences.',
        'Trajectory state_metrics and allocator/timing values remain producer observations; only stored state arrays and derived scalar arithmetic are independently checked.',
        'No confidence, safety, global extremum, statistical performance or artistic claim. Finite-budget failure to find a different qualified endpoint is not uniqueness.',
        'CPU reduction ordering can differ from GPU; original FD and eligibility gates are unchanged. Summary comparison tolerance is 1e-11 absolute plus 1e-12 relative.']
    result['passed'] = not result['failures']
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run', type=Path, default=TASK/'runs/run-01/worker')
    p.add_argument('--stage', choices=['qualification', 'final'], default='qualification')
    p.add_argument('--execute', action='store_true')
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    if not args.execute:
        print(json.dumps({'mode': 'plan', 'stage': args.stage, 'run': str(args.run), 'CPUOnly': True,
                          'numpyImported': 'numpy' in sys.modules, 'torchImported': 'torch' in sys.modules}))
        return 0
    result = audit(args.run, args.stage)
    if args.out:
        with args.out.open('x', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps({'passed': result['passed'], 'failures': result['failures'], 'files': len(result['files']),
                      'G0': result['G0'], 'endpoints': result.get('endpoints')}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
