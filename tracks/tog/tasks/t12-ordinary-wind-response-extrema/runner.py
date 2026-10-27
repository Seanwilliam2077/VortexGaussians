"""Ordinary T12 finite-budget search. No Torch import on plan/freeze paths."""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def safe_json(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: safe_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe_json(item) for item in value]
    return value


def write_json(path, value):
    path.write_text(json.dumps(safe_json(value), ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def sources():
    config = json.loads((HERE / 'config.json').read_text(encoding='utf-8'))
    paths = {name: HERE / name for name in ('runner.py', 'config.json', 'PROTOCOL.md')}
    for name, row in config['sources'].items():
        paths[name] = (HERE / row['path']).resolve()
        if sha(paths[name]) != row['sha256']:
            raise ValueError('Common source SHA mismatch: ' + name)
    pins = {name: {'path': os.path.relpath(path, HERE).replace('\\', '/'), 'sha256': sha(path), 'bytes': path.stat().st_size}
            for name, path in paths.items()}
    return config, pins


def authenticate():
    config, pins = sources()
    frozen = json.loads((HERE / 'freeze.json').read_text(encoding='utf-8'))
    if frozen['sources'] != pins:
        raise ValueError('Frozen source/config/protocol changed')
    return config, pins


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SearchBudget(Exception):
    pass


class InvalidTrial(Exception):
    pass


def worker(out):
    config, pins = authenticate()
    out.mkdir()
    started = time.perf_counter()
    report = {'schema': 't12-result-v1', 'status': 'starting', 'scope': config['scope'], 'sourcesBefore': pins,
              'freezeSHA256': sha(HERE / 'freeze.json'), 'raw': {}, 'qualification': {'status': 'not_started'}, 'extremes': []}
    engine = None
    code = 1
    save_seconds = 0.0
    dll_handle = None

    def publish():
        write_json(out / 'summary.json', report)

    publish()
    try:
        if os.environ.get('MKL_THREADING_LAYER') != 'SEQUENTIAL':
            raise RuntimeError('Missing child-local MKL SEQUENTIAL policy')
        dll_path = Path(sys.executable).parent / 'Library' / 'bin'
        if os.name == 'nt':
            dll_handle = os.add_dll_directory(str(dll_path))
        import torch
        import numpy as np
        torch.set_num_threads(config['execution']['threads'])
        torch.set_num_interop_threads(1)
        if torch.__version__ != config['execution']['expected_torch'] or not torch.cuda.is_available():
            raise RuntimeError('Expected CUDA Torch runtime unavailable; no fallback')
        props = torch.cuda.get_device_properties(0)
        actual_uuid = str(getattr(props, 'uuid', 'unknown'))
        if actual_uuid.removeprefix('GPU-').lower() != config['execution']['expected_gpu_uuid'].removeprefix('GPU-').lower():
            raise RuntimeError('Unexpected GPU UUID')
        report['runtime'] = {'python': sys.version, 'torch': torch.__version__, 'numpy': np.__version__,
                             'cudaBuild': torch.version.cuda, 'gpuName': props.name, 'uuid': actual_uuid,
                             'dtype': 'float64', 'threads': torch.get_num_threads(), 'dllDirectory': str(dll_path),
                             'MKL_THREADING_LAYER': os.environ['MKL_THREADING_LAYER']}
        core = load_module('t12_pinned_core', HERE / pins['core.py']['path'])
        scene = load_module('t12_pinned_scene', HERE / pins['scene.py']['path'])
        model = core.SmokeModel(**config['model'], device='cuda', dtype=torch.float64)
        scalar = lambda value: float(value.detach().item())
        sync = torch.cuda.synchronize

        def cpu(value):
            return value.detach().cpu().numpy().copy() if isinstance(value, torch.Tensor) else np.asarray(value)

        def raw_save(name, **arrays):
            nonlocal save_seconds
            tick = time.perf_counter()
            path = out / name
            path.parent.mkdir(parents=True, exist_ok=True)
            packed = {key: np.ascontiguousarray(cpu(value)) for key, value in arrays.items()}
            temporary = path.with_suffix(path.suffix + '.tmp')
            with temporary.open('wb') as stream:
                np.savez(stream, **packed)
            os.replace(temporary, path)
            report['raw'][name] = {'sha256': sha(path), 'bytes': path.stat().st_size, 'arrays': {
                key: {'shape': list(value.shape), 'dtype': value.dtype.str,
                      'rawSHA256': hashlib.sha256(value.tobytes()).hexdigest()} for key, value in packed.items()}}
            save_seconds += time.perf_counter() - tick

        def detached(output):
            return {key: value.detach().clone() for key, value in output.items()}

        def tensor_hashes(tensors):
            return {key: {'shape': list(value.shape), 'dtype': str(value.dtype),
                          'rawSHA256': hashlib.sha256(cpu(value).tobytes()).hexdigest()}
                    for key, value in tensors.items()}

        class Engine:
            def __init__(self):
                self.evaluations_started = 0
                self.evaluations_completed = 0
                self.steps_completed = 0
                self.backward_calls = 0
                _, self.rho0 = scene.initial_state(model)
                self.rho0 = self.rho0.detach()
                coarse_axis = torch.arange(8, dtype=torch.float64, device='cuda')
                ijk = torch.stack(torch.meshgrid(coarse_axis, coarse_axis, coarse_axis, indexing='ij'), -1)
                coarse_faces = [(ijk + model._constant(offset)) / 8 for offset in model.FACE_OFFSETS]
                amps = config['reference_theta_amplitudes']
                self.seed = torch.stack((amps[0] * torch.sin(2 * torch.pi * coarse_faces[0][..., 1]),
                                         amps[1] * torch.sin(2 * torch.pi * coarse_faces[1][..., 2]),
                                         amps[2] * torch.sin(2 * torch.pi * coarse_faces[2][..., 0]))).detach()
                axis = torch.arange(model.n, dtype=torch.float64, device='cuda')
                ijk = torch.stack(torch.meshgrid(axis, axis, axis, indexing='ij'), -1)
                edge = (ijk + model._constant((0.0, 0.0, 0.5))) * model.h
                center = model._constant(config['wind']['potential_center'])
                difference = (edge - center + 0.5).remainder(1.0) - 0.5
                az = difference[..., 1] * torch.exp(-difference.square().sum(-1) / (2 * config['wind']['sigma']**2))
                force = torch.stack(((torch.roll(az, -1, dims=1) - az) / model.h,
                                     -(torch.roll(az, -1, dims=0) - az) / model.h, torch.zeros_like(az)))
                self.wind_scale = scalar(config['wind']['max_component'] / force.abs().max())
                self.wind_raw_stats = {'maxComponent': scalar(force.abs().max()),
                                       'componentRMS': scalar(force.square().mean().sqrt()),
                                       'euclideanNorm': scalar(force.square().sum().sqrt()),
                                       'scale': self.wind_scale}
                self.wind = (force * self.wind_scale).detach()
                self.potential = az.detach()
                self.zero = torch.zeros_like(self.wind)
                self.observed = self.lower = self.upper = self.denominator = None

            def initial_velocity(self, theta):
                coarse = config['velocity']['coarse_scale'] * torch.tanh(theta)
                expanded = torch.stack([model.sample(coarse[j], model.faces[j], model.FACE_OFFSETS[j]) for j in range(3)])
                base = model._constant(config['velocity']['base']).reshape(3, 1, 1, 1)
                return model.project(expanded) + base

            def diagnostics(self, v, rho, alpha):
                with torch.no_grad():
                    div = model.divergence(v.detach())
                    finite = torch.stack([torch.isfinite(item.detach()).all() for item in (v, rho, alpha, div)]).all()
                    return torch.stack((div.abs().max(), rho.detach().min(), rho.detach().max(),
                                        alpha.detach().min(), alpha.detach().max(), finite.to(torch.float64)))

            def advance(self, v, rho, force):
                v, rho = model.step(v, rho, force)
                self.steps_completed += 1
                return v, rho

            def evaluate(self, theta):
                self.evaluations_started += 1
                v0 = self.initial_velocity(theta)
                v, rho = v0, self.rho0
                frames, diagnostics = [], []
                for _ in range(config['observation_steps']):
                    v, rho = self.advance(v, rho, self.zero)
                    alpha = model.render(rho)
                    frames.append(alpha); diagnostics.append(self.diagnostics(v, rho, alpha))
                v20, rho20 = v, rho
                futures, velocities, densities, first_densities = [], [], [], []
                for wind_enabled in (False, True):
                    v, rho = v20, rho20
                    branch = []
                    for index in range(config['future_steps']):
                        force = self.wind if wind_enabled and index < config['wind']['active_updates'] else self.zero
                        v, rho = self.advance(v, rho, force)
                        if index == 0:
                            first_densities.append(rho)
                        alpha = model.render(rho)
                        branch.append(alpha); diagnostics.append(self.diagnostics(v, rho, alpha))
                    futures.append(torch.stack(branch)); velocities.append(v); densities.append(rho)
                self.evaluations_completed += 1
                return {'observation_alpha': torch.stack(frames), 'future_alpha': torch.stack(futures),
                        'initial_velocity': v0, 'observation_velocity20': v20, 'observation_density20': rho20,
                        'final_velocity': torch.stack(velocities), 'final_density': torch.stack(densities),
                        'first_future_density': torch.stack(first_densities),
                        'state_metrics': torch.stack(diagnostics)}

            def terms(self, output):
                alpha = output['observation_alpha']
                v0 = output['initial_velocity']
                constraints = torch.cat((255 * (self.lower - alpha).reshape(-1),
                                         255 * (alpha - self.upper).reshape(-1),
                                         (v0.abs().max() / config['velocity']['initial_max_component'] - 1).reshape(1),
                                         (v0.square().mean() / config['velocity']['initial_component_rms']**2 - 1).reshape(1)))
                x0, y0, x1, y1 = config['response']['roi']
                gs = output['future_alpha'][:, -1, y0:y1, x0:x1].sum((-2, -1)) / self.denominator
                return gs[1] - gs[0], constraints, gs

            def assess(self, output, d, constraints, gs):
                with torch.no_grad():
                    stats = output['state_metrics']
                    alpha = output['observation_alpha']
                    finite = all(bool(torch.isfinite(value).all()) for value in output.values())
                    finite = finite and bool(torch.isfinite(constraints).all()) and bool(torch.isfinite(d))
                    interval = torch.maximum(self.lower - alpha, alpha - self.upper).clamp_min(0)
                    vmax = scalar(output['initial_velocity'].abs().max())
                    vrms = scalar(output['initial_velocity'].square().mean().sqrt())
                    div0 = scalar(model.divergence(output['initial_velocity']).abs().max())
                    observed_codes = torch.floor(255 * alpha + 0.5).clamp(0, 255).to(torch.uint8)
                    code_delta = (observed_codes.to(torch.int16) - self.observed.to(torch.int16)).abs()
                    gate = config['gates']
                    numerical = (finite and bool((stats[:, 5] == 1).all())
                                 and scalar(stats[:, 0].max()) <= gate['divergence_inf']
                                 and div0 <= gate['divergence_inf']
                                 and scalar(stats[:, 1].min()) >= gate['density_min']
                                 and scalar(stats[:, 3].min()) >= gate['alpha_min']
                                 and scalar(stats[:, 4].max()) <= gate['alpha_max'])
                    row = {'d': scalar(d), 'g_unedited': scalar(gs[0]), 'g_wind': scalar(gs[1]),
                           'finite': finite, 'numericalPassed': numerical,
                           'intervalMaxAlphaViolation': scalar(interval.max()),
                           'intervalViolatingPixels': int((interval > gate['interval_alpha_tolerance']).sum().item()),
                           'quantizedByteExact': bool((code_delta == 0).all()),
                           'quantizedDifferentPixels': int((code_delta != 0).sum().item()),
                           'quantizedMaxCodeDifference': int(code_delta.max().item()),
                           'initialVelocityMaxComponent': vmax, 'initialVelocityComponentRMS': vrms,
                           'initialDivergenceInf': div0, 'trajectoryDivergenceInf': scalar(stats[:, 0].max()),
                           'densityMin': scalar(stats[:, 1].min()), 'alphaMin': scalar(stats[:, 3].min()),
                           'alphaMax': scalar(stats[:, 4].max()), 'maxPositiveConstraint': scalar(constraints.clamp_min(0).max()),
                           'firstFutureAlphaWindDifferenceMax': scalar((output['future_alpha'][0, 0] - output['future_alpha'][1, 0]).abs().max()),
                           'firstFutureDensityWindDifferenceMax': scalar((output['first_future_density'][0] - output['first_future_density'][1]).abs().max())}
                    row['qualified'] = (numerical and row['intervalViolatingPixels'] == 0
                                        and vmax <= config['velocity']['initial_max_component']
                                        and vrms <= config['velocity']['initial_component_rms'])
                    return row

            def fixed_tensors(self):
                return {'rho0': self.rho0, 'seed_theta': self.seed, 'wind': self.wind, 'potential': self.potential,
                        'observed_uint8': self.observed, 'lower': self.lower, 'upper': self.upper, 'denominator': self.denominator}

            def identity(self):
                tensors = self.fixed_tensors()
                return tuple((key, id(value), value._version, tuple(value.shape), str(value.dtype), str(value.device))
                             for key, value in sorted(tensors.items()))

        def phr(constraints, multipliers, penalty):
            return ((multipliers + penalty * constraints).clamp_min(0).square() - multipliers.square()).sum() / (2 * penalty)

        setup_start = time.perf_counter()
        engine = Engine()
        with torch.no_grad():
            reference = engine.evaluate(engine.seed)
            engine.observed = torch.floor(255 * reference['observation_alpha'] + 0.5).clamp(0, 255).to(torch.uint8)
            values = engine.observed.to(torch.float64)
            engine.lower = ((values - 0.5) / 255).clamp_min(0)
            engine.upper = ((values + 0.5) / 255).clamp_max(1)
            engine.denominator = reference['observation_alpha'][-1].sum().detach()
            if not scalar(engine.denominator) > 0:
                raise RuntimeError('Reference response denominator is not positive')
            d, c, gs = engine.terms(reference)
            reference_metrics = engine.assess(reference, d, c, gs)
            wind_div = scalar(model.divergence(engine.wind).abs().max())
            projection_change = scalar((model.project(engine.wind) - engine.wind).abs().max())
            if wind_div > config['gates']['divergence_inf'] or not reference_metrics['qualified']:
                raise RuntimeError('Reference or fixed wind failed preconditions')
            raw_save('reference.npz', theta=engine.seed, **reference, constraints=c, d=d, **engine.fixed_tensors())
        sync()
        report['setup'] = {'evaluations': 1, 'steps': 60, 'secondsIncludingIO': time.perf_counter() - setup_start,
                           'referenceMetrics': reference_metrics, 'windDivergenceInf': wind_div,
                           'windProjectionChangeMax': projection_change, 'windMaxComponent': scalar(engine.wind.abs().max()),
                           'windBeforeScaling': engine.wind_raw_stats,
                           'knownDensitySource': 'Pinned scene.initial_state; its returned velocity is discarded',
                           'futureBranchOrder': ['unedited', 'wind'], 'stateMetricsOrder': ['observation1..20', 'unedited21..40', 'wind21..40'],
                           'stateMetricColumns': ['divInf', 'rhoMin', 'rhoMax', 'alphaMin', 'alphaMax', 'finiteFlag']}
        report['runtimeInputsBefore'] = tensor_hashes(engine.fixed_tensors())
        input_identity = engine.identity()
        report['status'] = 'reference_ready'; publish()
        del reference, c, d, gs

        # New complete-objective G0: nine physical evaluations, two reverse calls.
        qc = config['qualification']
        qreport = report['qualification'] = {'status': 'running', 'evaluations': 0, 'backwardCalls': 0, 'directions': []}
        qt = time.perf_counter()
        generator = torch.Generator(device='cpu').manual_seed(qc['x_seed'])
        perturb = (2 * torch.randint(0, 2, config['theta_shape'], generator=generator, dtype=torch.int64) - 1).to(torch.float64).to('cuda')
        analytic_theta = (engine.seed + qc['x_perturbation'] * perturb).detach().requires_grad_(True)
        torch.cuda.reset_peak_memory_stats()
        output = engine.evaluate(analytic_theta); qreport['evaluations'] += 1
        d, c, gs = engine.terms(output)
        lam = torch.full_like(c, qc['multiplier'])
        loss = config['response']['objective_scale'] * d + phr(c, lam, qc['penalty'])
        engine.backward_calls += 1; qreport['backwardCalls'] += 1
        gd = torch.autograd.grad(d, analytic_theta, retain_graph=True)[0]
        engine.backward_calls += 1; qreport['backwardCalls'] += 1
        gl = torch.autograd.grad(loss, analytic_theta)[0]
        sync()
        branch = lam + qc['penalty'] * c.detach()
        qreport.update(analyticD=scalar(d), analyticLoss=scalar(loss),
                       activePHRBranches=int((branch > 0).sum().item()),
                       minimumAbsolutePHRBranch=scalar(branch.abs().min()),
                       finiteAnalytic=all(bool(torch.isfinite(v).all()) for v in (gd, gl, d, loss, c)),
                       analyticMetrics=engine.assess(output, d, c, gs), probeMetrics=[])
        raw_save('qualification/analytic.npz', theta=analytic_theta, gradient_d=gd, gradient_loss=gl,
                 constraints=c, multipliers=lam, d=d, loss=loss, **output)
        detached_gd, detached_gl = gd.detach(), gl.detach()
        detached_theta = analytic_theta.detach()
        del output, d, c, gs, loss, analytic_theta, gd, gl, perturb, branch
        generator = torch.Generator(device='cpu').manual_seed(qc['direction_seed'])
        for direction_index in range(qc['directions']):
            direction = (2 * torch.randint(0, 2, config['theta_shape'], generator=generator, dtype=torch.int64) - 1).to(torch.float64).to('cuda')
            direction = direction / direction.square().sum().sqrt()
            dots = {'d': scalar((detached_gd * direction).sum()), 'loss': scalar((detached_gl * direction).sum())}
            direction_record = {'index': direction_index, 'euclideanNorm': scalar(direction.square().sum().sqrt()), 'gradientDotDirection': dots, 'finiteDifferences': []}
            raw_save(f'qualification/direction-{direction_index}.npz', direction=direction)
            for h_index, h in enumerate(qc['h']):
                values = []
                for sign, name in ((1, 'plus'), (-1, 'minus')):
                    theta = detached_theta + sign * h * direction
                    with torch.no_grad():
                        output = engine.evaluate(theta); qreport['evaluations'] += 1
                        d, c, gs = engine.terms(output)
                        loss = config['response']['objective_scale'] * d + phr(c, lam, qc['penalty'])
                        values.append({'d': scalar(d), 'loss': scalar(loss)})
                        qreport['probeMetrics'].append({'direction': direction_index, 'h': h, 'sign': name,
                                                        'metrics': engine.assess(output, d, c, gs)})
                        raw_save(f'qualification/probe-{direction_index}-{h_index}-{name}.npz', theta=theta, constraints=c, d=d, loss=loss, **output)
                    del output, d, c, gs, loss
                row = {'h': h, 'plus': values[0], 'minus': values[1], 'errors': {}}
                for key in ('d', 'loss'):
                    fd = (values[0][key] - values[1][key]) / (2 * h)
                    error = abs(fd - dots[key]) / max(abs(dots[key]), qc['denominator_floor'])
                    row['errors'][key] = {'fd': fd, 'relativeError': error, 'passed': math.isfinite(error) and error <= qc['relative_gate']}
                direction_record['finiteDifferences'].append(row)
            qreport['directions'].append(direction_record)
            publish()
        sync()
        qreport['memory'] = {'scope': 'Torch allocator; not full process/device peak', 'peakAllocatedBytes': torch.cuda.max_memory_allocated(), 'peakReservedBytes': torch.cuda.max_memory_reserved()}
        qreport['memoryPassed'] = (qreport['memory']['peakAllocatedBytes'] <= qc['peak_allocated_limit_bytes']
                                   and qreport['memory']['peakReservedBytes'] <= qc['peak_reserved_limit_bytes'])
        qreport['numericalPassed'] = (qreport['analyticMetrics']['numericalPassed']
                                      and all(row['metrics']['numericalPassed'] for row in qreport['probeMetrics']))
        qreport['passed'] = (qreport['finiteAnalytic'] and qreport['evaluations'] == 9 and qreport['backwardCalls'] == 2
                            and qreport['memoryPassed'] and qreport['numericalPassed']
                            and all(e['passed'] for item in qreport['directions'] for row in item['finiteDifferences'] for e in row['errors'].values()))
        qreport.update(status='completed', secondsIncludingIO=time.perf_counter() - qt)
        del detached_gd, detached_gl, detached_theta, direction, lam, theta
        publish()
        if not qreport['passed']:
            report.update(status='completed', decision='STOP_NEW_G0_OR_MEMORY_QUALIFICATION')
            code = 0
        else:
            def solve(extreme):
                opt = config['optimizer']
                sign = 1.0 if extreme == 'min' else -1.0
                tick = time.perf_counter()
                theta = torch.nn.Parameter(engine.seed.detach().clone())
                multipliers = torch.zeros(2 * 20 * 64 * 64 + 2, dtype=torch.float64, device='cuda')
                penalty = opt['initial_penalty']
                row = {'extreme': extreme, 'status': 'running', 'evaluationsStarted': 0, 'evaluationsCompleted': 0,
                       'backwardCalls': 0, 'returnedSteps': 0, 'cacheHits': 0, 'cacheMisses': 0,
                       'calls': [], 'accepted': [], 'outerUpdates': [], 'bestUpdates': [], 'budget': opt['max_evaluations_per_extreme'],
                       'start': 'same_public_reference_seed', 'bestMayBeLineSearchEvaluated': True}
                report['extremes'].append(row)
                cache = None
                best = None
                last_theta = None
                last_output = None
                last_c = None
                last_evaluation = None

                def check_search_budget(reserve):
                    if row['evaluationsStarted'] >= row['budget'] - reserve:
                        raise SearchBudget('evaluation_budget')
                    if time.perf_counter() - tick >= opt['soft_seconds_per_extreme']:
                        raise SearchBudget('soft_time_limit')

                def consider(x, output, constraints, metrics, call):
                    nonlocal best
                    if metrics['qualified'] and (best is None or sign * metrics['d'] < sign * best['metrics']['d']):
                        best = {'theta': x.detach().clone(), 'output': detached(output), 'constraints': constraints.detach().clone(),
                                'metrics': dict(metrics), 'evaluation': call['evaluation'], 'origin': call['origin']}
                        row['bestUpdates'].append({'evaluation': call['evaluation'], 'origin': call['origin'], 'd': metrics['d']})
                        raw_save(f'{extreme}/best-evaluated.npz', theta=best['theta'], constraints=best['constraints'], **best['output'])
                        row['bestEvaluated'] = {'evaluation': best['evaluation'], 'origin': best['origin'], 'metrics': best['metrics']}

                def evaluate(x, origin, gradient=False, final=False):
                    nonlocal cache
                    if final:
                        if row['evaluationsStarted'] >= row['budget']:
                            raise RuntimeError('Mandatory final evaluation slot missing')
                    else:
                        check_search_budget(2 if gradient else 1)
                    if engine.identity() != input_identity:
                        raise RuntimeError('Fixed input identity/version changed')
                    row['evaluationsStarted'] += 1
                    call = {'evaluation': row['evaluationsStarted'], 'origin': origin, 'gradient': gradient, 'status': 'started'}
                    row['calls'].append(call)
                    sync(); start = time.perf_counter()
                    with torch.set_grad_enabled(gradient):
                        output = engine.evaluate(x)
                        row['evaluationsCompleted'] += 1
                        call['forwardCompleted'] = True
                        d, constraints, gs = engine.terms(output)
                        loss = sign * config['response']['objective_scale'] * d + phr(constraints, multipliers, penalty)
                        metrics = engine.assess(output, d, constraints, gs)
                        clean_output = detached(output)
                        clean_c = constraints.detach().clone()
                        call.update(metrics=metrics, penalty=penalty, maxMultiplier=scalar(multipliers.max()))
                        # Eligibility depends on the evaluated physical output, not
                        # on a later gradient/line-search acceptance decision.
                        if not final:
                            consider(x, clean_output, clean_c, metrics, call)
                        if not metrics['finite'] and not final:
                            raise InvalidTrial('Nonfinite evaluated state')
                        if gradient:
                            if not bool(torch.isfinite(loss)):
                                raise InvalidTrial('Nonfinite closure')
                            row['backwardCalls'] += 1; engine.backward_calls += 1
                            loss.backward()
                            if x.grad is None or not bool(torch.isfinite(x.grad).all()):
                                raise InvalidTrial('Nonfinite gradient')
                    sync()
                    call.update(status='completed', seconds=time.perf_counter() - start, loss=scalar(loss),
                                metrics=metrics, penalty=penalty, maxMultiplier=scalar(multipliers.max()))
                    if gradient:
                        cache = {'theta': x.detach().clone(), 'output': clean_output, 'constraints': clean_c,
                                 'metrics': metrics, 'evaluation': call['evaluation'], 'identity': input_identity}
                    return loss, clean_output, clean_c, metrics, call['evaluation']

                def accept(reason, required_initial=False):
                    nonlocal last_theta, last_output, last_c, last_evaluation
                    hit = (not required_initial and cache is not None and cache['identity'] == engine.identity()
                           and torch.equal(cache['theta'], theta.detach()))
                    if hit:
                        row['cacheHits'] += 1
                        output, constraints, metrics, evaluation = cache['output'], cache['constraints'], cache['metrics'], cache['evaluation']
                    else:
                        if not required_initial:
                            row['cacheMisses'] += 1
                        _, output, constraints, metrics, evaluation = evaluate(theta, 'seed_initial' if required_initial else 'acceptance_miss')
                    last_theta = theta.detach().clone()
                    last_output, last_c, last_evaluation = output, constraints, evaluation
                    d, current_c, _ = engine.terms(output)
                    merit = sign * config['response']['objective_scale'] * d + phr(current_c, multipliers, penalty)
                    row['accepted'].append({'returnedStep': row['returnedSteps'], 'reason': reason, 'evaluation': evaluation,
                                            'cacheHit': hit, 'metrics': metrics, 'ALObjective': scalar(merit), 'penalty': penalty})

                accept('initial', required_initial=True)
                if best is None:
                    raise RuntimeError('Public seed failed repeated qualification')
                termination = 'fixed_returned_step_budget'
                stop = False
                for outer in range(opt['outer_iterations']):
                    violation_before = scalar(last_c.clamp_min(0).max())
                    optimizer = torch.optim.LBFGS([theta], **opt['lbfgs'])
                    for iteration in range(opt['returned_steps_per_outer']):
                        try:
                            check_search_budget(2)

                            def closure():
                                optimizer.zero_grad(set_to_none=True)
                                loss, _, _, _, _ = evaluate(theta, 'line_search_or_closure', gradient=True)
                                return loss

                            optimizer.step(closure)
                            row['returnedSteps'] += 1
                            accept('optimizer_returned')
                        except (SearchBudget, InvalidTrial) as exc:
                            with torch.no_grad():
                                theta.copy_(last_theta)
                            cache = None
                            termination = str(exc)
                            row['rollback'] = {'reason': str(exc), 'restoredEvaluation': last_evaluation,
                                               'bestEvaluatedStillEligible': best['evaluation']}
                            stop = True
                            break
                        publish()
                    del optimizer
                    if stop or outer + 1 == opt['outer_iterations']:
                        break
                    violation_after = scalar(last_c.clamp_min(0).max())
                    multipliers = (multipliers + penalty * last_c).clamp_min(0).detach()
                    old_penalty = penalty
                    if violation_after > opt['violation_reduction_factor'] * violation_before:
                        penalty = min(opt['penalty_max'], penalty * opt['penalty_growth'])
                    row['outerUpdates'].append({'outer': outer, 'violationBefore': violation_before, 'violationAfter': violation_after,
                                               'oldPenalty': old_penalty, 'newPenalty': penalty, 'maxMultiplier': scalar(multipliers.max()),
                                               'historyReset': True})
                    cache = None
                row['termination'] = termination
                row['searchSecondsBeforeFinal'] = time.perf_counter() - tick
                _, verified, verified_c, verified_metrics, final_id = evaluate(best['theta'], 'mandatory_best_verification', final=True)
                comparison = {key: {'maxAbsolute': scalar((verified[key] - best['output'][key]).abs().max()),
                                    'numericEqual': bool(torch.equal(verified[key], best['output'][key]))}
                              for key in verified}
                raw_save(f'{extreme}/final-verification.npz', theta=best['theta'], constraints=verified_c, **verified)
                row.update(status='completed', finalQualified=verified_metrics['qualified'], finalMetrics=verified_metrics,
                           selectedEvaluation=best['evaluation'], selectedOrigin=best['origin'], finalVerificationEvaluation=final_id,
                           verificationComparisons=comparison, secondsIncludingFinalAndIO=time.perf_counter() - tick,
                           softLimitExceeded=time.perf_counter() - tick > opt['soft_seconds_per_extreme'])
                row['selectedWasOptimizerReturned'] = any(item['evaluation'] == best['evaluation'] for item in row['accepted'][1:])
                row['selectedWasInitialSeed'] = best['origin'] == 'seed_initial'
                publish()

            for extreme in config['response']['order']:
                print('solve', extreme, flush=True)
                solve(extreme)
            report.update(status='completed', decision='FINITE_BUDGET_WITNESSES_RECORDED',
                          allFinalWitnessesQualified=all(row['finalQualified'] for row in report['extremes']))
            if not report['allFinalWitnessesQualified']:
                report['decision'] = 'FINAL_WITNESS_VERIFICATION_FAILED'
            code = 0
    except Exception as exc:
        report.update(status='failed', decision='EXECUTION_FAILED', error=repr(exc), traceback=traceback.format_exc())
        traceback.print_exc()
    finally:
        if engine is not None:
            report['actualWork'] = {'fullEvaluationsStarted': engine.evaluations_started, 'fullEvaluationsCompleted': engine.evaluations_completed,
                                    'stepsCompleted': engine.steps_completed, 'reverseCalls': engine.backward_calls,
                                    'scope': 'Includes reference setup, new G0, both searches and paid final verification'}
            try:
                if engine.observed is not None and 'runtimeInputsBefore' in report:
                    report['runtimeInputsAfter'] = tensor_hashes(engine.fixed_tensors())
                    report['runtimeInputsUnchanged'] = report['runtimeInputsBefore'] == report['runtimeInputsAfter']
            except Exception as exc:
                report['runtimeInputsUnchanged'] = False; report['inputCheckError'] = repr(exc)
        try:
            _, after = sources(); report['sourcesAfter'] = after
            report['sourcesUnchanged'] = after == pins and sha(HERE / 'freeze.json') == report['freezeSHA256']
        except Exception as exc:
            report['sourcesUnchanged'] = False; report['sourceCheckError'] = repr(exc)
        if not report['sourcesUnchanged'] or report.get('runtimeInputsUnchanged') is False:
            report.update(status='failed', decision='INPUT_OR_SOURCE_IDENTITY_FAILED'); code = 1
        report['evidenceSaveSeconds'] = save_seconds
        report['workerWallSeconds'] = time.perf_counter() - started
        publish()
    return code


def supervise(out, python):
    config, pins = authenticate()
    out = out.resolve()
    if not out.is_relative_to(HERE) or out == HERE:
        raise ValueError('Output must be a fresh child directory of T12')
    out.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    for key in ('PYTHONPATH', 'PYTHONHOME', 'TI_ARCH'):
        env.pop(key, None)
    env.update(MKL_THREADING_LAYER='SEQUENTIAL', OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', OPENBLAS_NUM_THREADS='1',
               CUDA_VISIBLE_DEVICES=config['execution']['expected_gpu_uuid'], PYTHONUTF8='1', PYTHONIOENCODING='utf-8', T12_SUPERVISED_WORKER='1')
    dll = python.parent / 'Library' / 'bin'
    env['PATH'] = str(dll) + os.pathsep + env.get('PATH', '')
    command = [str(python), '-I', '-B', '-u', '-X', 'utf8', str(Path(__file__).resolve()), '--worker', '--out', str(out / 'worker')]
    record = {'command': command, 'sourcesBefore': pins, 'hardLimitSeconds': config['execution']['hard_timeout_seconds'],
              'environmentPolicy': {key: env[key] for key in ('MKL_THREADING_LAYER', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'CUDA_VISIBLE_DEVICES')},
              'dllDirectory': str(dll), 'status': 'running'}
    write_json(out / 'supervisor.json', record)
    tick = time.perf_counter()
    with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
        try:
            completed = subprocess.run(command, cwd=out, env=env, stdout=stdout, stderr=stderr,
                                       timeout=config['execution']['hard_timeout_seconds'], check=False)
            record.update(returnCode=completed.returncode, status='completed' if completed.returncode == 0 else 'failed')
        except subprocess.TimeoutExpired:
            record.update(returnCode=None, status='timeout')
        except Exception as exc:
            record.update(returnCode=None, status='failed', error=repr(exc))
    record['wallSeconds'] = time.perf_counter() - tick
    try:
        _, after = sources(); record['sourcesAfter'] = after; record['sourcesUnchanged'] = pins == after
    except Exception as exc:
        record['sourcesUnchanged'] = False; record['sourceCheckError'] = repr(exc)
    if not record['sourcesUnchanged']:
        record['status'] = 'failed'
    write_json(out / 'supervisor.json', record)
    print(json.dumps(safe_json(record), ensure_ascii=False))
    return 0 if record['status'] == 'completed' else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--out', default='runs/run-01')
    parser.add_argument('--python', type=Path, default=Path.home() / 'miniconda3/envs/gs-sph-3d/python.exe')
    args = parser.parse_args()
    if sum((args.freeze, args.execute, args.worker)) > 1:
        raise ValueError('Choose one action, or no action for plan')
    config, pins = sources()
    if args.freeze:
        with (HERE / 'freeze.json').open('x', encoding='utf-8') as stream:
            json.dump({'schema': 't12-freeze-v1', 'sources': pins}, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    if args.worker:
        if os.environ.get('T12_SUPERVISED_WORKER') != '1':
            raise RuntimeError('Worker must be launched by its bounded supervisor')
        return worker(Path(args.out))
    if args.execute:
        return supervise(HERE / args.out, args.python.resolve())
    if (HERE / 'freeze.json').exists():
        authenticate()
    print(json.dumps({'mode': 'plan', 'config': config, 'sources': pins, 'freezePresent': (HERE / 'freeze.json').exists(),
                      'torchImported': 'torch' in sys.modules, 'maximumFullEvaluations': 1 + 9 + 2 * config['optimizer']['max_evaluations_per_extreme'],
                      'maximumSteps': 60 * (1 + 9 + 2 * config['optimizer']['max_evaluations_per_extreme']),
                      'note': 'Plan only. No automatic freeze or execution.'}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
