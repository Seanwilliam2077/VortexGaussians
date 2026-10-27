"""Ordinary T13 Phase-I. Explicit narrow fork of frozen T12. No Torch import on plan/freeze paths."""
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
    paths = {name: HERE / name for name in ('runner.py', 'config.json', 'PROTOCOL.md', 'prepare_inputs.py', 'inputs.npz', 'inputs-manifest.json')}
    for name, row in config['sources'].items():
        paths[name] = (HERE / row['path']).resolve()
        if sha(paths[name]) != row['sha256']:
            raise ValueError('Common source SHA mismatch: ' + name)
    if sha(HERE / config['input_pack']['path']) != config['input_pack']['sha256'] or sha(HERE / config['input_pack']['manifest']) != config['input_pack']['manifest_sha256']:
        raise ValueError('Portable input SHA mismatch')
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


class CandidateFound(Exception):
    pass


def worker(out):
    config, pins = authenticate()
    out.mkdir()
    started = time.perf_counter()
    report = {'schema': 't13-result-v1', 'status': 'starting', 'scope': config['scope'], 'sourcesBefore': pins,
              'freezeSHA256': sha(HERE / 'freeze.json'), 'raw': {}, 'qualification': {'status': 'not_started'}, 'search': {'status': 'not_started'}}
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
        core = load_module('t13_pinned_core', HERE / pins['core.py']['path'])
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

        # Portable inputs are selected bytes of the original authenticated NPZs.
        input_load_start = time.perf_counter()
        manifest = json.loads((HERE / config['input_pack']['manifest']).read_text(encoding='utf-8'))
        if manifest['status'] != 'prepared' or not manifest['sourcesUnchangedAfter']:
            raise ValueError('Input-copy provenance invalid')
        with np.load(HERE / config['input_pack']['path'], allow_pickle=False) as archive:
            if set(archive.files) != set(manifest['arrays']):
                raise ValueError('Input keys differ from manifest')
            loaded = {}
            for key in archive.files:
                value = np.ascontiguousarray(archive[key])
                expected = manifest['arrays'][key]
                if (list(value.shape) != expected['shape'] or value.dtype.str != expected['dtype']
                        or hashlib.sha256(value.tobytes()).hexdigest() != expected['rawSHA256']
                        or value.dtype.hasobject or not np.isfinite(value).all()):
                    raise ValueError('Input array mismatch: ' + key)
                loaded[key] = torch.from_numpy(value.copy()).to('cuda')
        sync()
        input_load_seconds = time.perf_counter() - input_load_start
        original_config = json.loads((HERE / pins['t12_config']['path']).read_text(encoding='utf-8'))
        for key in ('model', 'dtype', 'observation_steps', 'future_steps', 'theta_shape', 'velocity', 'wind', 'gates', 'qualification'):
            if config[key] != original_config[key]:
                raise ValueError('Frozen numerical contract changed: ' + key)
        for key in ('roi', 'roi_order', 'future_index', 'denominator'):
            if config['response'][key] != original_config['response'][key]:
                raise ValueError('Response contract changed')
        for key in ('outer_iterations', 'returned_steps_per_outer', 'initial_multiplier', 'initial_penalty',
                    'penalty_growth', 'penalty_max', 'violation_reduction_factor', 'lbfgs'):
            if config['optimizer'][key] != original_config['optimizer'][key]:
                raise ValueError('Optimizer contract changed: ' + key)

        class Engine:
            def __init__(self):
                self.observations_started = self.observations_completed = 0
                self.full_started = self.full_completed = 0
                self.steps_completed = self.backward_calls = 0
                self.rho0 = loaded['rho0']
                self.seed = loaded['seed_theta']
                self.seed_velocity = loaded['seed_velocity']
                self.start = loaded['start_theta']
                self.wind = loaded['wind']
                self.potential = loaded['potential']
                self.zero = torch.zeros_like(self.wind)
                self.observed, self.lower, self.upper = (loaded[key] for key in ('observed_uint8', 'lower', 'upper'))
                self.denominator = loaded['denominator'].reshape(())

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

            def observe(self, theta, count=True):
                if count:
                    self.observations_started += 1
                v0 = self.initial_velocity(theta)
                v, rho = v0, self.rho0
                frames, diagnostics = [], []
                for _ in range(config['observation_steps']):
                    v, rho = self.advance(v, rho, self.zero)
                    alpha = model.render(rho)
                    frames.append(alpha); diagnostics.append(self.diagnostics(v, rho, alpha))
                if count:
                    self.observations_completed += 1
                return {'observation_alpha': torch.stack(frames), 'initial_velocity': v0,
                        'observation_velocity20': v, 'observation_density20': rho,
                        'state_metrics': torch.stack(diagnostics)}

            def complete(self, theta):
                self.full_started += 1
                output = self.observe(theta, count=False)
                v20, rho20 = output['observation_velocity20'], output['observation_density20']
                diagnostics = list(output['state_metrics'].unbind(0))
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
                self.full_completed += 1
                output.update(future_alpha=torch.stack(futures), final_velocity=torch.stack(velocities),
                              final_density=torch.stack(densities), first_future_density=torch.stack(first_densities),
                              state_metrics=torch.stack(diagnostics))
                return output

            def constraints(self, output):
                alpha = output['observation_alpha']
                v0 = output['initial_velocity']
                constraints = torch.cat((255 * (self.lower - alpha).reshape(-1),
                                         255 * (alpha - self.upper).reshape(-1),
                                         (v0.abs().max() / config['velocity']['initial_max_component'] - 1).reshape(1),
                                         (v0.square().mean() / config['velocity']['initial_component_rms']**2 - 1).reshape(1)))
                return constraints

            def response(self, output):
                x0, y0, x1, y1 = config['response']['roi']
                gs = output['future_alpha'][:, -1, y0:y1, x0:x1].sum((-2, -1)) / self.denominator
                return gs[1] - gs[0], gs

            def assess(self, output, constraints):
                with torch.no_grad():
                    stats = output['state_metrics']
                    alpha = output['observation_alpha']
                    finite = all(bool(torch.isfinite(value).all()) for value in output.values())
                    finite = finite and bool(torch.isfinite(constraints).all())
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
                    row = {'finite': finite, 'numericalPassed': numerical,
                           'intervalMaxAlphaViolation': scalar(interval.max()),
                           'intervalViolatingPixels': int((interval > gate['interval_alpha_tolerance']).sum().item()),
                           'quantizedByteExact': bool((code_delta == 0).all()),
                           'quantizedDifferentPixels': int((code_delta != 0).sum().item()),
                           'quantizedMaxCodeDifference': int(code_delta.max().item()),
                           'initialVelocityMaxComponent': vmax, 'initialVelocityComponentRMS': vrms,
                           'initialDivergenceInf': div0, 'trajectoryDivergenceInf': scalar(stats[:, 0].max()),
                           'densityMin': scalar(stats[:, 1].min()), 'alphaMin': scalar(stats[:, 3].min()),
                           'alphaMax': scalar(stats[:, 4].max()), 'maxPositiveConstraint': scalar(constraints.clamp_min(0).max())}
                    row['qualified'] = (numerical and row['intervalViolatingPixels'] == 0
                                        and vmax <= config['velocity']['initial_max_component']
                                        and vrms <= config['velocity']['initial_component_rms'])
                    difference = output['initial_velocity'] - self.seed_velocity
                    row['seedVelocityDifferenceMax'] = scalar(difference.abs().max())
                    row['seedVelocityDifferenceRelativeL2'] = scalar(difference.square().sum().sqrt() / self.seed_velocity.square().sum().sqrt())
                    row['nonseed'] = row['seedVelocityDifferenceMax'] > config['nonseed_velocity_max_absolute_threshold']
                    row['eligible'] = row['qualified'] and row['nonseed']
                    row['intervalViolatingPixelsPerFrame'] = [int(v) for v in (interval > gate['interval_alpha_tolerance']).sum((-2, -1)).cpu().tolist()]
                    row['intervalMaxAlphaViolationPerFrame'] = [float(v) for v in interval.amax((-2, -1)).cpu().tolist()]
                    row['positiveConstraintSquareSum'] = scalar(constraints.clamp_min(0).square().sum())
                    return row

            def fixed_tensors(self):
                return loaded

            def identity(self):
                return tuple((key, id(value), value._version, tuple(value.shape), str(value.dtype), str(value.device))
                             for key, value in sorted(self.fixed_tensors().items()))

        def phr(constraints, multipliers, penalty):
            return ((multipliers + penalty * constraints).clamp_min(0).square() - multipliers.square()).sum() / (2 * penalty)

        setup_start = time.perf_counter()
        engine = Engine()
        qc = config['qualification']
        generator = torch.Generator(device='cpu').manual_seed(qc['x_seed'])
        perturb = (2 * torch.randint(0, 2, config['theta_shape'], generator=generator, dtype=torch.int64) - 1).to(torch.float64).to('cuda')
        if not torch.equal(engine.start, engine.seed + qc['x_perturbation'] * perturb):
            raise ValueError('Loaded starting theta does not match original G0 recipe')
        generator = torch.Generator(device='cpu').manual_seed(qc['direction_seed'])
        for index in range(qc['directions']):
            direction = (2 * torch.randint(0, 2, config['theta_shape'], generator=generator, dtype=torch.int64) - 1).to(torch.float64).to('cuda')
            direction = direction / direction.square().sum().sqrt()
            if not torch.equal(direction, loaded[f'direction{index}']):
                raise ValueError('Loaded qualification direction differs from original recipe')
        with torch.no_grad():
            values = engine.observed.to(torch.float64)
            if (not torch.equal(engine.lower, ((values - .5) / 255).clamp_min(0))
                    or not torch.equal(engine.upper, ((values + .5) / 255).clamp_max(1))
                    or not scalar(engine.denominator) > 0):
                raise ValueError('Loaded observation interval/denominator invalid')
            seed_v = engine.initial_velocity(engine.seed)
            seed_velocity_check = {'maxAbsolute': scalar((seed_v - engine.seed_velocity).abs().max()),
                                   'numericEqual': bool(torch.equal(seed_v, engine.seed_velocity))}
            if not seed_velocity_check['numericEqual']:
                raise ValueError('Loaded seed velocity differs from original parameterization')
            wind_div = scalar(model.divergence(engine.wind).abs().max())
            if wind_div > config['gates']['divergence_inf']:
                raise ValueError('Loaded fixed wind violates divergence gate')
        sync()
        report['setup'] = {'source': 'Authenticated portable byte-copy of T12 reference and G0 inputs',
                           'evaluations': 0, 'steps': 0, 'secondsIncludingIO': time.perf_counter() - setup_start,
                           'inputReadVerifyAndUploadSeconds': input_load_seconds,
                           'seedVelocityCheck': seed_velocity_check, 'windDivergenceInf': wind_div,
                           'windMaxComponent': scalar(engine.wind.abs().max()), 'startRecipeExact': True,
                           'directionRecipesExact': True,
                           'futureBranchOrder': ['unedited', 'wind'],
                           'stateMetricColumns': ['divInf', 'rhoMin', 'rhoMax', 'alphaMin', 'alphaMax', 'finiteFlag'],
                           'originalInputPreparationSeconds': manifest['secondsCPUCopyIncludingIO']}
        report['runtimeInputsBefore'] = tensor_hashes(engine.fixed_tensors())
        input_identity = engine.identity()
        report['status'] = 'inputs_ready'; publish()
        del perturb, direction, values, seed_v

        # New PHR-only G0: nine 20-step observations and one reverse call.
        qreport = report['qualification'] = {'status': 'running', 'observationEvaluations': 0,
                                            'fullEvaluations': 0, 'backwardCalls': 0, 'directions': []}
        qt = time.perf_counter()
        analytic_theta = engine.start.detach().clone().requires_grad_(True)
        torch.cuda.reset_peak_memory_stats()
        output = engine.observe(analytic_theta); qreport['observationEvaluations'] += 1
        c = engine.constraints(output)
        lam = torch.full_like(c, qc['multiplier'])
        loss = phr(c, lam, qc['penalty'])
        engine.backward_calls += 1; qreport['backwardCalls'] += 1
        gradient = torch.autograd.grad(loss, analytic_theta)[0]
        sync()
        branch = lam + qc['penalty'] * c.detach()
        qreport.update(analyticLoss=scalar(loss), activePHRBranches=int((branch > 0).sum().item()),
                       minimumAbsolutePHRBranch=scalar(branch.abs().min()),
                       finiteAnalytic=all(bool(torch.isfinite(v).all()) for v in (gradient, loss, c)),
                       analyticMetrics=engine.assess(output, c), probeMetrics=[])
        raw_save('qualification/analytic.npz', theta=analytic_theta, gradient_loss=gradient,
                 constraints=c, multipliers=lam, loss=loss, **output)
        detached_gradient = gradient.detach().clone()
        del output, c, loss, analytic_theta, gradient, branch
        for direction_index in range(qc['directions']):
            direction = loaded[f'direction{direction_index}']
            dot = scalar((detached_gradient * direction).sum())
            item = {'index': direction_index, 'euclideanNorm': scalar(direction.square().sum().sqrt()),
                    'gradientDotDirection': dot, 'finiteDifferences': []}
            raw_save(f'qualification/direction-{direction_index}.npz', direction=direction)
            for h_index, h in enumerate(qc['h']):
                values = []
                for sign, name in ((1, 'plus'), (-1, 'minus')):
                    theta_probe = engine.start + sign * h * direction
                    with torch.no_grad():
                        output = engine.observe(theta_probe); qreport['observationEvaluations'] += 1
                        c = engine.constraints(output)
                        loss = phr(c, lam, qc['penalty'])
                        values.append(scalar(loss))
                        qreport['probeMetrics'].append({'direction': direction_index, 'h': h, 'sign': name,
                                                        'metrics': engine.assess(output, c)})
                        raw_save(f'qualification/probe-{direction_index}-{h_index}-{name}.npz',
                                 theta=theta_probe, constraints=c, loss=loss, **output)
                    del output, c, loss
                fd = (values[0] - values[1]) / (2 * h)
                error = abs(fd - dot) / max(abs(dot), qc['denominator_floor'])
                item['finiteDifferences'].append({'h': h, 'plus': values[0], 'minus': values[1],
                                                  'fd': fd, 'relativeError': error,
                                                  'passed': math.isfinite(error) and error <= qc['relative_gate']})
            qreport['directions'].append(item)
            publish()
        sync()
        qreport['memory'] = {'scope': 'Torch allocator; not full process/device peak',
                            'peakAllocatedBytes': torch.cuda.max_memory_allocated(),
                            'peakReservedBytes': torch.cuda.max_memory_reserved()}
        qreport['memoryPassed'] = (qreport['memory']['peakAllocatedBytes'] <= qc['peak_allocated_limit_bytes']
                                   and qreport['memory']['peakReservedBytes'] <= qc['peak_reserved_limit_bytes'])
        qreport['numericalPassed'] = (qreport['analyticMetrics']['numericalPassed']
                                      and all(row['metrics']['numericalPassed'] for row in qreport['probeMetrics']))
        qreport['passed'] = (qreport['finiteAnalytic'] and qreport['observationEvaluations'] == 9
                            and qreport['backwardCalls'] == 1 and qreport['memoryPassed'] and qreport['numericalPassed']
                            and all(row['passed'] for item in qreport['directions'] for row in item['finiteDifferences']))
        qreport.update(status='completed', steps=180, secondsIncludingIO=time.perf_counter() - qt)
        del detached_gradient, direction, lam, theta_probe
        publish()
        if not qreport['passed']:
            report.update(status='completed', decision='STOP_NEW_PHR_G0_OR_MEMORY_QUALIFICATION')
            code = 0
        else:
            opt = config['optimizer']
            tick = time.perf_counter()
            theta = torch.nn.Parameter(engine.start.detach().clone())
            multipliers = torch.zeros(2 * 20 * 64 * 64 + 2, dtype=torch.float64, device='cuda')
            penalty = opt['initial_penalty']
            row = report['search'] = {'status': 'running', 'evaluationsStarted': 0, 'evaluationsCompleted': 0,
                                     'observationEvaluationsStarted': 0, 'observationEvaluationsCompleted': 0,
                                     'fullEvaluationsStarted': 0, 'fullEvaluationsCompleted': 0,
                                     'backwardCalls': 0, 'returnedSteps': 0, 'cacheHits': 0, 'cacheMisses': 0,
                                     'calls': [], 'accepted': [], 'outerUpdates': [], 'leastViolatingUpdates': [],
                                     'budget': opt['max_evaluations'], 'start': 'original_T12_G0_perturbation',
                                     'candidateMayBeLineSearchEvaluated': True, 'seedFallbackAllowed': False}
            cache = candidate = least = None
            last_theta = last_output = last_c = last_evaluation = None

            def check_search_budget(reserve):
                if row['evaluationsStarted'] >= row['budget'] - reserve:
                    raise SearchBudget('evaluation_budget')
                if time.perf_counter() - tick >= opt['soft_seconds']:
                    raise SearchBudget('soft_time_limit')

            def consider(x, output, constraints, metrics, call):
                nonlocal candidate, least
                if metrics['eligible']:
                    if candidate is not None:
                        raise RuntimeError('Attempt to overwrite the first feasible candidate')
                    candidate = {'theta': x.detach().clone(), 'output': detached(output),
                                 'constraints': constraints.detach().clone(), 'metrics': dict(metrics),
                                 'evaluation': call['evaluation'], 'origin': call['origin']}
                    raw_save('search/first-feasible.npz', theta=candidate['theta'], constraints=candidate['constraints'],
                             **candidate['output'])
                    row['firstCandidate'] = {key: candidate[key] for key in ('evaluation', 'origin', 'metrics')}
                    call['status'] = 'candidate_found_before_backward'
                    publish()
                    raise CandidateFound('first_nonseed_feasible_evaluation')
                if metrics['numericalPassed']:
                    score = (metrics['maxPositiveConstraint'], metrics['positiveConstraintSquareSum'])
                    if least is None or score < least['score']:
                        least = {'theta': x.detach().clone(), 'output': detached(output),
                                 'constraints': constraints.detach().clone(), 'metrics': dict(metrics), 'score': score,
                                 'evaluation': call['evaluation'], 'origin': call['origin']}
                        row['leastViolatingUpdates'].append({'evaluation': call['evaluation'], 'score': list(score)})
                        row['leastViolating'] = {key: least[key] for key in ('evaluation', 'origin', 'metrics')}
                        raw_save('search/least-violating.npz', theta=least['theta'], constraints=least['constraints'],
                                 **least['output'])

            def evaluate(x, origin, gradient=False, final=False):
                nonlocal cache
                if final:
                    if row['evaluationsStarted'] >= row['budget'] or row['fullEvaluationsStarted'] != 0:
                        raise RuntimeError('Mandatory single final evaluation slot missing/already used')
                else:
                    check_search_budget(2 if gradient else 1)
                if engine.identity() != input_identity:
                    raise RuntimeError('Fixed input identity/version changed')
                row['evaluationsStarted'] += 1
                kind = 'full' if final else 'observation'
                row[kind + 'EvaluationsStarted'] += 1
                call = {'evaluation': row['evaluationsStarted'], 'origin': origin, 'gradientRequested': gradient,
                        'kind': kind, 'stepsPlanned': 60 if final else 20, 'status': 'started', 'backwardCalled': False}
                row['calls'].append(call)
                sync(); start = time.perf_counter()
                try:
                    with torch.set_grad_enabled(gradient):
                        output = engine.complete(x) if final else engine.observe(x)
                        row['evaluationsCompleted'] += 1
                        row[kind + 'EvaluationsCompleted'] += 1
                        call['forwardCompleted'] = True
                        constraints = engine.constraints(output)
                        loss = phr(constraints, multipliers, penalty)
                        metrics = engine.assess(output, constraints)
                        clean_output, clean_c = detached(output), constraints.detach().clone()
                        call.update(metrics=metrics, penalty=penalty, maxMultiplier=scalar(multipliers.max()),
                                    loss=scalar(loss), status='forward_completed_before_backward')
                        # This is deliberately before backward and before optimizer return.
                        if not final:
                            consider(x, clean_output, clean_c, metrics, call)
                        if not metrics['numericalPassed'] and not final:
                            raise InvalidTrial('Numerically invalid evaluated observation')
                        if gradient:
                            if not bool(torch.isfinite(loss)):
                                raise InvalidTrial('Nonfinite closure')
                            row['backwardCalls'] += 1; engine.backward_calls += 1
                            call['backwardCalled'] = True
                            loss.backward()
                            if x.grad is None or not bool(torch.isfinite(x.grad).all()):
                                raise InvalidTrial('Nonfinite gradient')
                    call['status'] = 'completed'
                    if gradient:
                        cache = {'theta': x.detach().clone(), 'output': clean_output, 'constraints': clean_c,
                                 'metrics': metrics, 'evaluation': call['evaluation'], 'identity': input_identity}
                    return loss, clean_output, clean_c, metrics, call['evaluation']
                except CandidateFound:
                    raise
                except Exception as exc:
                    call.update(status='failed_after_forward' if call.get('forwardCompleted') else 'failed_in_forward',
                                error=repr(exc))
                    raise
                finally:
                    sync(); call['seconds'] = time.perf_counter() - start

            def accept(reason, initial=False):
                nonlocal last_theta, last_output, last_c, last_evaluation
                hit = (not initial and cache is not None and cache['identity'] == engine.identity()
                       and torch.equal(cache['theta'], theta.detach()))
                if hit:
                    row['cacheHits'] += 1
                    output, constraints, metrics, evaluation = cache['output'], cache['constraints'], cache['metrics'], cache['evaluation']
                else:
                    if not initial:
                        row['cacheMisses'] += 1
                    _, output, constraints, metrics, evaluation = evaluate(theta, 'perturbed_initial' if initial else 'acceptance_miss')
                last_theta = theta.detach().clone()
                last_output, last_c, last_evaluation = output, constraints, evaluation
                merit = phr(engine.constraints(output), multipliers, penalty)
                row['accepted'].append({'returnedStep': row['returnedSteps'], 'reason': reason, 'evaluation': evaluation,
                                        'cacheHit': hit, 'metrics': metrics, 'ALObjective': scalar(merit), 'penalty': penalty})

            termination = 'fixed_returned_step_budget'
            try:
                accept('initial', initial=True)
                for outer in range(opt['outer_iterations']):
                    violation_before = scalar(last_c.clamp_min(0).max())
                    optimizer = torch.optim.LBFGS([theta], **opt['lbfgs'])
                    for iteration in range(opt['returned_steps_per_outer']):
                        check_search_budget(2)

                        def closure():
                            optimizer.zero_grad(set_to_none=True)
                            loss, _, _, _, _ = evaluate(theta, 'line_search_or_closure', gradient=True)
                            return loss

                        optimizer.step(closure)
                        row['returnedSteps'] += 1
                        accept('optimizer_returned')
                        publish()
                    del optimizer
                    if outer + 1 == opt['outer_iterations']:
                        break
                    violation_after = scalar(last_c.clamp_min(0).max())
                    multipliers = (multipliers + penalty * last_c).clamp_min(0).detach()
                    old_penalty = penalty
                    if violation_after > opt['violation_reduction_factor'] * violation_before:
                        penalty = min(opt['penalty_max'], penalty * opt['penalty_growth'])
                    row['outerUpdates'].append({'outer': outer, 'violationBefore': violation_before, 'violationAfter': violation_after,
                                                'oldPenalty': old_penalty, 'newPenalty': penalty,
                                                'maxMultiplier': scalar(multipliers.max()), 'historyReset': True})
                    raw_save(f'search/outer-update-{outer}.npz', theta=last_theta, constraints=last_c,
                             multipliers=multipliers, penalty=penalty)
                    cache = None
            except CandidateFound as exc:
                termination = str(exc)
                cache = None
                # Do not restore theta into candidate or overwrite its saved evaluation.
            except (SearchBudget, InvalidTrial) as exc:
                termination = str(exc)
                if last_theta is not None:
                    with torch.no_grad():
                        theta.copy_(last_theta)
                cache = None
                row['rollback'] = {'reason': str(exc), 'restoredEvaluation': last_evaluation,
                                   'trialWasNotAccepted': True}
            row.update(termination=termination, searchSecondsBeforeFinal=time.perf_counter() - tick)
            if candidate is None:
                row.update(status='completed', finalPerformed=False, nonseedWitnessFound=False,
                           leastViolatingIsWitness=False, secondsIncludingFinalAndIO=time.perf_counter() - tick)
                report.update(status='completed', decision='NO_NONSEED_FEASIBLE_POINT_FOUND_WITHIN_FIXED_SEARCH')
            else:
                print('first feasible evaluation; one complete final verification', flush=True)
                _, verified, verified_c, metrics, final_id = evaluate(candidate['theta'], 'mandatory_first_candidate_verification', final=True)
                d, gs = engine.response(verified)
                metrics.update(d=scalar(d), g_unedited=scalar(gs[0]), g_wind=scalar(gs[1]),
                               firstFutureAlphaWindDifferenceMax=scalar((verified['future_alpha'][0, 0] - verified['future_alpha'][1, 0]).abs().max()),
                               firstFutureDensityWindDifferenceMax=scalar((verified['first_future_density'][0] - verified['first_future_density'][1]).abs().max()))
                metrics['responseFinite'] = bool(torch.isfinite(d)) and bool(torch.isfinite(gs).all())
                metrics['qualified'] = metrics['qualified'] and metrics['responseFinite']
                metrics['eligible'] = metrics['qualified'] and metrics['nonseed']
                comparison = {}
                for key, previous in candidate['output'].items():
                    current = verified[key][:20] if key == 'state_metrics' else verified[key]
                    comparison[key] = {'maxAbsolute': scalar((current - previous).abs().max()),
                                       'numericEqual': bool(torch.equal(current, previous)),
                                       'byteEqual': cpu(current).tobytes() == cpu(previous).tobytes()}
                raw_save('search/final-verification.npz', theta=candidate['theta'], constraints=verified_c, d=d, gs=gs, **verified)
                row.update(status='completed', finalPerformed=True, nonseedWitnessFound=metrics['eligible'],
                           finalQualified=metrics['qualified'], finalNonseed=metrics['nonseed'], finalMetrics=metrics,
                           selectedEvaluation=candidate['evaluation'], selectedOrigin=candidate['origin'],
                           selectedWasOptimizerReturned=any(item['evaluation'] == candidate['evaluation'] for item in row['accepted'][1:]),
                           finalVerificationEvaluation=final_id, verificationComparisons=comparison,
                           secondsIncludingFinalAndIO=time.perf_counter() - tick)
                report.update(status='completed', decision='ORDINARY_NONSEED_FEASIBILITY_FOUND' if metrics['eligible']
                              else 'FIRST_CANDIDATE_FINAL_VERIFICATION_FAILED')
            row['softLimitExceededIncludingFinal'] = time.perf_counter() - tick > opt['soft_seconds']
            publish()
            code = 0
    except Exception as exc:
        report.update(status='failed', decision='EXECUTION_FAILED', error=repr(exc), traceback=traceback.format_exc())
        traceback.print_exc()
    finally:
        if engine is not None:
            report['actualWork'] = {'observationEvaluationsStarted': engine.observations_started,
                                    'observationEvaluationsCompleted': engine.observations_completed,
                                    'fullEvaluationsStarted': engine.full_started, 'fullEvaluationsCompleted': engine.full_completed,
                                    'stepsCompleted': engine.steps_completed, 'reverseCalls': engine.backward_calls,
                                    'scope': 'New G0, one observation-only search and at most one paid complete final verification; no reference simulation'}
            try:
                if 'runtimeInputsBefore' in report:
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
        raise ValueError('Output must be a fresh child directory of T13')
    out.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    for key in ('PYTHONPATH', 'PYTHONHOME', 'TI_ARCH'):
        env.pop(key, None)
    env.update(MKL_THREADING_LAYER='SEQUENTIAL', OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', OPENBLAS_NUM_THREADS='1',
               CUDA_VISIBLE_DEVICES=config['execution']['expected_gpu_uuid'], PYTHONUTF8='1', PYTHONIOENCODING='utf-8', T13_SUPERVISED_WORKER='1')
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
            json.dump({'schema': 't13-freeze-v1', 'sources': pins}, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    if args.worker:
        if os.environ.get('T13_SUPERVISED_WORKER') != '1':
            raise RuntimeError('Worker must be launched by its bounded supervisor')
        return worker(Path(args.out))
    if args.execute:
        return supervise(HERE / args.out, args.python.resolve())
    if (HERE / 'freeze.json').exists():
        authenticate()
    print(json.dumps({'mode': 'plan', 'config': config, 'sources': pins, 'freezePresent': (HERE / 'freeze.json').exists(),
                      'torchImported': 'torch' in sys.modules, 'qualificationObservationEvaluations': 9, 'maximumSearchAndFinalEvaluations': config['optimizer']['max_evaluations'],
                      'maximumFullFinalEvaluations': 1, 'maximumSteps': 9 * 20 + (config['optimizer']['max_evaluations'] - 1) * 20 + 60,
                      'note': 'Plan only. No automatic freeze or execution.'}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
