"""T11 fixed analytic qualification. Default path uses only the standard library."""
import argparse
import hashlib
import importlib.util
import json
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
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def sources():
    config = json.loads((HERE / 'config.json').read_text(encoding='utf-8'))
    paths = {name: HERE / name for name in ('runner.py', 'config.json', 'PROTOCOL.md')}
    paths['core.py'] = (HERE / config['core']['path']).resolve()
    pins = {name: {'path': os.path.relpath(path, HERE).replace('\\', '/'), 'sha256': sha(path), 'bytes': path.stat().st_size}
            for name, path in paths.items()}
    if pins['core.py']['sha256'] != config['core']['sha256']:
        raise ValueError('Frozen common core SHA mismatch')
    return config, pins


def authenticate():
    config, pins = sources()
    frozen = json.loads((HERE / 'freeze.json').read_text(encoding='utf-8'))
    if frozen['sources'] != pins:
        raise ValueError('T11 source/config/protocol freeze mismatch')
    return config, pins


def worker(out):
    config, pins = authenticate()
    started = time.perf_counter()
    report = {'schema': 't11-result-v1', 'status': 'starting', 'interpretation': config['interpretation'],
              'sourcesBefore': pins, 'freezeSHA256': sha(HERE / 'freeze.json'), 'stepsCompleted': 0,
              'validity': [], 'observationComparisons': [], 'futureVelocityComparisons': [], 'arrays': {}}
    out.mkdir()
    dll_handle = None
    io_seconds = 0.0
    code = 1

    def publish():
        write_json(out / 'summary.json', report)

    publish()
    try:
        if os.environ.get('MKL_THREADING_LAYER') != 'SEQUENTIAL':
            raise RuntimeError('Worker requires local MKL SEQUENTIAL policy')
        dll_path = Path(sys.executable).parent / 'Library' / 'bin'
        if os.name == 'nt':
            dll_handle = os.add_dll_directory(str(dll_path))
        import torch
        import numpy as np
        torch.set_num_threads(config['execution']['threads'])
        torch.set_num_interop_threads(1)
        if torch.__version__ != config['execution']['expected_torch']:
            raise RuntimeError('Unexpected Torch version')
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA unavailable; no CPU fallback')
        properties = torch.cuda.get_device_properties(0)
        actual_uuid = str(getattr(properties, 'uuid', 'unknown'))
        expected_uuid = config['execution']['expected_gpu_uuid']
        if actual_uuid.removeprefix('GPU-').lower() != expected_uuid.removeprefix('GPU-').lower():
            raise RuntimeError('Unexpected CUDA device UUID')
        report['runtime'] = {'python': sys.version, 'torch': torch.__version__, 'numpy': np.__version__,
                             'cudaBuild': torch.version.cuda, 'device': properties.name, 'uuid': actual_uuid,
                             'dtype': 'float64', 'threads': torch.get_num_threads(), 'dllDirectory': str(dll_path),
                             'MKL_THREADING_LAYER': os.environ['MKL_THREADING_LAYER'],
                             'CUDA_VISIBLE_DEVICES': os.environ.get('CUDA_VISIBLE_DEVICES')}
        spec = importlib.util.spec_from_file_location('t11_pinned_core', HERE / pins['core.py']['path'])
        core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(core)
        model = core.SmokeModel(**config['model'], device='cuda', dtype=torch.float64)
        torch.cuda.reset_peak_memory_stats()
        gates = config['gates']
        to_cpu = lambda value: value.detach().cpu().numpy().copy()
        scalar = lambda value: float(value.detach().item())
        periodic_d = lambda coord, center: (coord - center + 0.5).remainder(1.0) - 0.5

        def initialize(sign):
            ux = sign * config['velocity']['shear_amplitude'] * torch.sin(2.0 * torch.pi * model.faces[0][..., 1])
            velocity = torch.stack((ux, torch.zeros_like(ux), torch.full_like(ux, config['velocity']['constant_z'])))
            density = torch.zeros_like(ux)
            for lobe in config['density_lobes']:
                dy = periodic_d(model.centers[..., 1], lobe['center_yz'][0])
                dz = periodic_d(model.centers[..., 2], lobe['center_yz'][1])
                density = density + lobe['amplitude'] * torch.exp(-dy.square() / (2 * lobe['sigma_yz'][0]**2)
                                                               -dz.square() / (2 * lobe['sigma_yz'][1]**2))
            return velocity, density

        def validity(label, index, velocity, density, alpha):
            finite = all(bool(torch.isfinite(value).all()) for value in (velocity, density, alpha))
            div = model.divergence(velocity)
            finite = finite and bool(torch.isfinite(div).all())
            if not finite:
                raise FloatingPointError('Nonfinite state: ' + label + ':' + str(index))
            row = {'branch': label, 'index': index, 'finite': True, 'divergenceInf': scalar(div.abs().max()),
                   'densityMin': scalar(density.min()), 'densityMax': scalar(density.max()),
                   'alphaMin': scalar(alpha.min()), 'alphaMax': scalar(alpha.max()),
                   'densitySum': scalar(density.sum())}
            row['passed'] = (row['divergenceInf'] <= gates['divergence_inf'] and row['densityMin'] >= gates['density_lower']
                             and row['alphaMin'] >= gates['alpha_lower'] and row['alphaMax'] <= gates['alpha_upper'])
            report['validity'].append(row)

        def save_arrays(name, **arrays):
            nonlocal io_seconds
            tick = time.perf_counter()
            path = out / name
            with path.open('xb') as stream:
                np.savez(stream, **arrays)
            report['arrays'][name] = {'sha256': sha(path), 'bytes': path.stat().st_size, 'arrays': {
                key: {'shape': list(value.shape), 'dtype': value.dtype.str,
                      'rawSHA256': hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()}
                for key, value in arrays.items()}}
            io_seconds += time.perf_counter() - tick

        torch.cuda.synchronize()
        compute_start = time.perf_counter()
        with torch.no_grad():
            states = [initialize(1), initialize(-1)]
            zero_force = torch.zeros_like(states[0][0])
            initial_velocity = np.stack([to_cpu(state[0]) for state in states])
            obs_rho, obs_alpha = [[], []], [[], []]
            for index in range(config['observation_steps'] + 1):
                if index:
                    states = [model.step(v, rho, zero_force) for v, rho in states]
                    report['stepsCompleted'] += 2
                alphas = [model.render(rho) for _, rho in states]
                for arm, ((v, rho), alpha) in enumerate(zip(states, alphas)):
                    validity('observation_' + config['observation_order'][arm], index, v, rho, alpha)
                    obs_rho[arm].append(to_cpu(rho)); obs_alpha[arm].append(to_cpu(alpha))
                density_scale = max(1.0, *(scalar(rho.max()) for _, rho in states))
                rho_error = scalar((states[0][1] - states[1][1]).abs().max())
                alpha_error = scalar((alphas[0] - alphas[1]).abs().max())
                row = {'index': index, 'densityMaxAbsolute': rho_error, 'densityScale': density_scale,
                       'alphaMaxAbsolute': alpha_error,
                       'passed': rho_error <= gates['observation_density_relative_max'] * density_scale
                                 and alpha_error <= gates['observation_alpha_absolute_max']}
                report['observationComparisons'].append(row)
                if index % 5 == 0:
                    print('observation', index, flush=True)
            torch.cuda.synchronize()
            report['observationSecondsIncludingRenderChecksAndReadback'] = time.perf_counter() - compute_start
            save_arrays('observations.npz', density=np.asarray(obs_rho), alpha=np.asarray(obs_alpha),
                        velocity_initial=initial_velocity, velocity_step20=np.stack([to_cpu(v) for v, _ in states]),
                        indices=np.arange(config['observation_steps'] + 1, dtype=np.int64))
            report['status'] = 'observations_saved'; publish()
            source = config['source']
            distance_squared = sum(periodic_d(model.centers[..., j], source['center'][j]).square() for j in range(3))
            q = source['amplitude'] * torch.exp(-distance_squared / (2 * source['sigma']**2))
            q_sum = scalar(q.sum())
            if not q_sum > 0 or not bool(torch.isfinite(q).all()):
                raise ValueError('Invalid source density')
            # Each branch owns its state; all four invoke the full original step.
            branches = []
            for v, rho in states:
                branches.extend([(v.clone(), rho.clone()), (v.clone(), rho + q)])
            right = model.centers[..., 0] >= 0.5
            future_alpha = [[] for _ in branches]
            future_rho = [[] for _ in branches]
            responses, g_right, total_response = [[], []], [[], []], [[], []]
            torch.cuda.synchronize()
            future_start = time.perf_counter()
            for index in range(config['future_steps'] + 1):
                if index:
                    branches = [model.step(v, rho, zero_force) for v, rho in branches]
                    report['stepsCompleted'] += 4
                alphas = [model.render(rho) for _, rho in branches]
                for arm, ((v, rho), alpha) in enumerate(zip(branches, alphas)):
                    validity(config['future_order'][arm], index, v, rho, alpha)
                    future_alpha[arm].append(to_cpu(alpha)); future_rho[arm].append(to_cpu(rho))
                for sign, (unedited, edited) in enumerate(((0, 1), (2, 3))):
                    dv = scalar((branches[edited][0] - branches[unedited][0]).abs().max())
                    report['futureVelocityComparisons'].append({'sign': config['observation_order'][sign], 'index': index,
                        'maxAbsolute': dv, 'passed': dv <= gates['same_sign_future_velocity_max']})
                    delta_rho = branches[edited][1] - branches[unedited][1]
                    g_right[sign].append(scalar(delta_rho[right].sum()) / q_sum)
                    total_response[sign].append(scalar(delta_rho.sum()) / q_sum)
                    responses[sign].append(to_cpu(alphas[edited] - alphas[unedited]))
                if index % 5 == 0:
                    print('future', index, flush=True)
            torch.cuda.synchronize()
            report['futureSecondsIncludingRenderChecksAndReadback'] = time.perf_counter() - future_start
            future_alpha = np.asarray(future_alpha)
            responses = np.asarray(responses)
            save_arrays('future.npz', alpha=future_alpha, density=np.asarray(future_rho), alpha_response=responses,
                        velocity_final=np.stack([to_cpu(v) for v, _ in branches]),
                        density_final=np.stack([to_cpu(rho) for _, rho in branches]), source_q=to_cpu(q),
                        g_R=np.asarray(g_right, dtype=np.float64), response_mass_ratio=np.asarray(total_response, dtype=np.float64),
                        indices=np.arange(config['future_steps'] + 1, dtype=np.int64))
            report['responseDescription'] = {'sourceSum': q_sum, 'g_R': g_right,
                'g_R_plus_minus': [p-m for p, m in zip(*g_right)],
                'responseMassRatio': total_response,
                'alphaResponsePairMaxAbsolute': [float(np.max(np.abs(responses[0, i] - responses[1, i])))
                                                 for i in range(config['future_steps'] + 1)],
                'scope': 'Descriptive values only; no response-size success threshold or confidence interval'}
        report['numericalQualificationPassed'] = (report['stepsCompleted'] == 120
            and all(row['passed'] for row in report['validity'])
            and all(row['passed'] for row in report['observationComparisons'])
            and all(row['passed'] for row in report['futureVelocityComparisons']))
        report['memory'] = {'scope': 'Torch allocator only, not complete process or device peak',
                            'peakAllocatedBytes': torch.cuda.max_memory_allocated(),
                            'peakReservedBytes': torch.cuda.max_memory_reserved()}
        report['status'] = 'completed'
        report['decision'] = 'ANALYTIC_QUALIFICATION_PASSED' if report['numericalQualificationPassed'] else 'ANALYTIC_QUALIFICATION_FAILED'
        code = 0
    except Exception as exc:
        report.update(status='failed', decision='EXECUTION_FAILED', error=repr(exc), traceback=traceback.format_exc(), numericalQualificationPassed=False)
        traceback.print_exc()
    finally:
        try:
            _, after = sources()
            report['sourcesAfter'] = after
            report['sourcesUnchanged'] = after == pins and sha(HERE / 'freeze.json') == report['freezeSHA256']
        except Exception as exc:
            report['sourcesUnchanged'] = False; report['sourceCheckError'] = repr(exc)
        if not report['sourcesUnchanged']:
            report.update(status='failed', decision='SOURCE_IDENTITY_FAILED', numericalQualificationPassed=False)
            code = 1
        report['evidenceSaveSeconds'] = io_seconds
        report['workerWallSeconds'] = time.perf_counter() - started
        publish()
        # dll_handle intentionally remains alive through the full worker.
    return code


def supervise(out, python):
    config, pins = authenticate()
    out = out.resolve()
    if not out.is_relative_to(HERE) or out == HERE:
        raise ValueError('Fresh output must be inside this T11 directory')
    out.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    for key in ('PYTHONPATH', 'PYTHONHOME', 'TI_ARCH'):
        env.pop(key, None)
    env.update(MKL_THREADING_LAYER='SEQUENTIAL', OMP_NUM_THREADS='4', MKL_NUM_THREADS='4',
               OPENBLAS_NUM_THREADS='1', CUDA_VISIBLE_DEVICES=config['execution']['expected_gpu_uuid'],
               PYTHONUTF8='1', PYTHONIOENCODING='utf-8', T11_SUPERVISED_WORKER='1')
    dll_path = python.parent / 'Library' / 'bin'
    env['PATH'] = str(dll_path) + os.pathsep + env.get('PATH', '')
    command = [str(python), '-I', '-B', '-u', '-X', 'utf8', str(Path(__file__).resolve()), '--worker', '--out', str(out / 'worker')]
    record = {'command': command, 'sourcesBefore': pins, 'limitSeconds': config['execution']['total_timeout_seconds'],
              'environmentPolicy': {key: env[key] for key in ('MKL_THREADING_LAYER', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'CUDA_VISIBLE_DEVICES')},
              'dllDirectory': str(dll_path), 'status': 'running'}
    write_json(out / 'supervisor.json', record)
    tick = time.perf_counter()
    with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
        try:
            completed = subprocess.run(command, cwd=out, env=env, stdout=stdout, stderr=stderr,
                                       timeout=config['execution']['total_timeout_seconds'], check=False)
            record.update(returnCode=completed.returncode, status='completed' if completed.returncode == 0 else 'failed')
        except subprocess.TimeoutExpired:
            record.update(returnCode=None, status='timeout')
        except Exception as exc:
            record.update(returnCode=None, status='failed', error=repr(exc))
    record['wallSeconds'] = time.perf_counter() - tick
    try:
        _, after = sources(); record['sourcesAfter'] = after; record['sourcesUnchanged'] = after == pins
    except Exception as exc:
        record['sourcesUnchanged'] = False; record['sourceCheckError'] = repr(exc)
    if not record['sourcesUnchanged']:
        record['status'] = 'failed'
    write_json(out / 'supervisor.json', record)
    print(json.dumps(record, ensure_ascii=False))
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
        raise ValueError('Choose exactly one action, or no action for plan')
    config, pins = sources()
    if args.freeze:
        with (HERE / 'freeze.json').open('x', encoding='utf-8') as stream:
            json.dump({'schema': 't11-freeze-v1', 'sources': pins}, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    if args.worker:
        if os.environ.get('T11_SUPERVISED_WORKER') != '1':
            raise RuntimeError('Worker requires its bounded supervisor')
        return worker(Path(args.out))
    if args.execute:
        return supervise(HERE / args.out, args.python.resolve())
    frozen = (HERE / 'freeze.json').exists()
    if frozen:
        authenticate()
    print(json.dumps({'mode': 'plan', 'sourcesAuthenticated': True, 'freezePresent': frozen, 'config': config,
                      'sources': pins, 'stepsPlanned': 120, 'torchImported': 'torch' in sys.modules,
                      'executeCommand': [str(args.python), '-I', '-B', '-u', str(Path(__file__).resolve()), '--execute', '--out', args.out]},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
