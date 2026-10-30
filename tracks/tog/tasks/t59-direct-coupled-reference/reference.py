"""T59: unchanged T56 coupled physics with the ordinary T58 direct solve.

No old module is edited. The sole numerical binding change is its Poisson
function; the new case wrapper adds checkpoint/output lifetime accounting.
"""
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

START = time.perf_counter()
import numpy as np

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT / 'local'
BASE_PATH = ROOT.parent / 't56-coupled-reference' / 'reference.py'
SPATIAL_PATH = ROOT.parent / 't55-axisymmetric-reference' / 'reference.py'
SOLVER_PATH = ROOT.parent / 't58-separable-solver-qualification' / 'solver.py'
OLD_LOCAL = BASE_PATH.parent / 'local'
CASES = [('S64', 8., 64, .0025, 32), ('S128', 8., 128, .0025, 32),
         ('S256', 8., 256, .0025, 32), ('T128', 8., 128, .00125, 32),
         ('D192', 12., 192, .0025, 32), ('Q128', 8., 128, .0025, 64)]
TIMES = (0., .125, .25)
PRIOR_CHILD_SECONDS = 1317.5624378999928
SOLVER_PHASES = ('rhs_seconds', 'forward_transform_seconds', 'factor_seconds',
                 'triangular_seconds', 'inverse_transform_seconds',
                 'original_rhs_assembly_seconds', 'original_residual_seconds')
RUNTIME_COUNTS = dict(elliptic_attempts=0, elliptic_completed=0,
                      transport_stages=0, completed_steps=0,
                      snapshots=0, completed_cases=0, new_CG_solves=0)
SOLVER_SECONDS = {key: 0. for key in SOLVER_PHASES}
SOLVER_SECONDS['checked_solve_seconds'] = 0.
SOLVER_SECONDS['failed_checked_solve_seconds'] = 0.
CHECKPOINTS = []
CASE_RECORDS = []
ACTIVE = dict(case=None, step=None, stage=None, phase='initialization')
CHECKPOINT_STREAM = None


def identity(path):
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
            size += len(block)
    return dict(bytes=size, sha256=digest.hexdigest())


def write_json(path, value):
    with path.open('x', encoding='utf8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()


def check_time():
    if time.perf_counter() - START >= 600.:
        raise RuntimeError('fixed 600-second child budget exhausted; no retry')


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE_PATHS = dict(code=Path(__file__), spatial_code=SPATIAL_PATH,
                    base_code=BASE_PATH, solver_code=SOLVER_PATH)
SOURCE_BEFORE = {key: identity(path) for key, path in SOURCE_PATHS.items()}
frozen = json.loads((ROOT / 'input-manifest.json').read_text(encoding='utf8'))
frozen_inputs = {str((ROOT.parents[3] / item['path']).resolve()): item
                 for item in frozen['inputs']}
for key, path in SOURCE_PATHS.items():
    expected_identity = frozen_inputs[str(path.resolve())]
    assert SOURCE_BEFORE[key] == {field: expected_identity[field]
                                 for field in ('bytes', 'sha256')}
base = load_module('t59_unchanged_t56', BASE_PATH)
direct = load_module('t59_unchanged_t58', SOLVER_PATH)
spatial = base.spatial


def checked_direct_poisson(q, h, r, gR, gminus, gplus):
    """Same signature; independently check T55's original weighted FV system."""
    begin = time.perf_counter()
    RUNTIME_COUNTS['elliptic_attempts'] += 1
    try:
        check_time()
        phi, record = direct.solve(q, h, gR, gminus, gplus)
        assert record['method'] == 'ordinary_FFT_sine_Thomas'
        assert record['factor_reuse'] is False
        # Independently assembled original T55 RHS/operator, not transformed RHS.
        tick = time.perf_counter()
        nr, nz = q.shape
        faces = np.arange(nr + 1) * h
        volumes = (faces[1:]**4 - faces[:-1]**4) / 4.
        left = faces[:-1]**3 / (volumes * h)
        right = faces[1:]**3 / (volumes * h)
        diag = np.broadcast_to((left + right + 2. / h**2)[:, None], q.shape).copy()
        diag[-1, :] += right[-1]
        diag[:, 0] += 1. / h**2
        diag[:, -1] += 1. / h**2
        original_rhs = q.copy()
        original_rhs[-1, :] += 2. * right[-1] * gR
        original_rhs[:, 0] += 2. * gminus / h**2
        original_rhs[:, -1] += 2. * gplus / h**2
        record['original_rhs_assembly_seconds'] = time.perf_counter() - tick
        tick = time.perf_counter()
        applied = diag * phi
        applied[1:, :] -= left[1:, None] * phi[:-1, :]
        applied[:-1, :] -= right[:-1, None] * phi[1:, :]
        applied[:, 1:] -= phi[:, :-1] / h**2
        applied[:, :-1] -= phi[:, 1:] / h**2
        residual = original_rhs - applied
        denominator = math.sqrt(float(np.sum(volumes[:, None] * original_rhs * original_rhs)))
        assert math.isfinite(denominator) and denominator > 0.
        relative = math.sqrt(float(np.sum(volumes[:, None] * residual * residual))) / denominator
        assert math.isfinite(relative) and relative <= 1e-10
        record['true_weighted_relative_residual'] = relative
        record['original_residual_seconds'] = time.perf_counter() - tick
        record['checked_solve_seconds'] = time.perf_counter() - begin
        RUNTIME_COUNTS['elliptic_completed'] += 1
        for key in SOLVER_PHASES:
            SOLVER_SECONDS[key] += record[key]
        SOLVER_SECONDS['checked_solve_seconds'] += record['checked_solve_seconds']
        return phi, record
    except Exception:
        SOLVER_SECONDS['failed_checked_solve_seconds'] += time.perf_counter() - begin
        raise


# This changes only an in-memory binding. T56 current, rhs and all transport,
# initialization, reconstruction and comparison functions remain their originals.
spatial.poisson = checked_direct_poisson


def checkpoint_event(record):
    CHECKPOINT_STREAM.write(json.dumps(record, allow_nan=False) + '\n')
    CHECKPOINT_STREAM.flush()


def save_npz(path, **arrays):
    with path.open('xb') as stream:
        np.savez(stream, **arrays)
        stream.flush()


def solve_case(config, gauss):
    """T56 step equations verbatim in meaning; only solver/output wrapper differs."""
    name, R, nr, dt, order = config
    begin = time.perf_counter()
    ACTIVE.update(case=name, step=0, stage=None, phase='geometry_and_kernel')
    check_time()
    checkpoint_event(dict(kind='case_started', name=name,
                          child_elapsed_seconds=time.perf_counter() - START))
    g = base.geometry(R, nr)
    q = base.initial(g)
    mat, tr, tz, krecord = base.kernel(g, order)
    checkpoint_event(dict(kind='kernel_ready', name=name, kernel=krecord,
                          child_elapsed_seconds=time.perf_counter() - START))
    check_time()
    steps = int(round(.25 / dt))
    assert math.isclose(steps * dt, .25)
    snapshots, stats, records, ledger, checkpoint_records = [], [], [], [], []
    gamma0 = float(np.sum(q * g['V']))
    expected = gamma0
    checkpoint_seconds = 0.
    path = LOCAL / (name + '-steps.jsonl')

    def log(record):
        records.append(record)
        logstream.write(json.dumps(record, allow_nan=False) + '\n')
        logstream.flush()

    def snapshot(step):
        nonlocal checkpoint_seconds
        ACTIVE.update(step=step, stage=None, phase='snapshot')
        check_time()
        flow = base.current(q, g, mat)
        log(dict(kind='snapshot', step=step, **flow['record']))
        qr, qz = base.slopes(q, g)
        ur, uz = base.velocity_slopes(flow['u'], g)
        saved = dict(q=q.copy(), qr=qr, qz=qz, u=flow['u'], ur=ur, uz=uz,
                     phi=flow['phi'], boundary=flow['boundary'])
        statistic = dict(step=step, time=step * dt,
                         **base.statistics(q, qr, qz, g, gauss))
        index = len(snapshots)
        assert index < 3 and math.isclose(step * dt, TIMES[index], abs_tol=1e-15)
        tick = time.perf_counter()
        raw = LOCAL / f'{name}-snapshot-{index}.npz'
        save_npz(raw, **saved, J=flow['J'], r=g['r'], rc=g['rc'], z=g['z'],
                 boundary_r=tr, boundary_z=tz)
        raw_record = dict(path=raw.name, **identity(raw))
        metadata = LOCAL / f'{name}-snapshot-{index}.json'
        write_json(metadata, dict(schema='t59-partial-snapshot-v1', name=name,
                   index=index, step=step, time=step * dt, R=R, nr=nr, nz=g['nz'],
                   h=g['h'], dt=dt, angular_order=order,
                   whole_task_qualified=False, statistics=statistic,
                   current=flow['record'], raw=raw_record,
                   child_elapsed_before_metadata_seconds=time.perf_counter() - START))
        cp = dict(name=name, index=index, step=step, time=step * dt,
                  raw=raw_record, path=metadata.name, **identity(metadata))
        checkpoint_event(dict(kind='snapshot_saved', **cp))
        checkpoint_seconds += time.perf_counter() - tick
        checkpoint_records.append(cp)
        CHECKPOINTS.append(cp)
        snapshots.append(saved)
        stats.append(statistic)
        RUNTIME_COUNTS['snapshots'] += 1
        check_time()
        return flow

    try:
        with path.open('x', encoding='utf8', newline='\n') as logstream:
            flow0 = snapshot(0)
            initial_error, exact_u, exact_J = base.analytic_initial(flow0, g)
            for step in range(steps):
                ACTIVE.update(step=step, stage=0, phase='transport')
                check_time()
                f0 = base.current(q, g, mat)
                l0, a0 = base.rhs(q, g, f0, dt)
                RUNTIME_COUNTS['transport_stages'] += 1
                log(dict(kind='stage', step=step, stage=0, **f0['record'], **a0))
                q1 = q + dt * l0
                assert np.all(np.isfinite(q1)) and np.min(q1) >= 0.
                ACTIVE.update(stage=1)
                check_time()
                f1 = base.current(q1, g, mat)
                l1, a1 = base.rhs(q1, g, f1, dt)
                RUNTIME_COUNTS['transport_stages'] += 1
                log(dict(kind='stage', step=step, stage=1, **f1['record'], **a1))
                q2 = q1 + dt * l1
                assert np.all(np.isfinite(q2)) and np.min(q2) >= 0.
                q = .5 * q + .5 * q2
                assert np.all(np.isfinite(q)) and np.min(q) >= 0.
                expected -= dt / 2. * (a0['boundary_circulation_outflow'] + a1['boundary_circulation_outflow'])
                error = abs(float(np.sum(q * g['V'])) - expected) / gamma0
                ledger.append(error)
                RUNTIME_COUNTS['completed_steps'] += 1
                log(dict(kind='step', step=step + 1, minimum_q=float(q.min()),
                         minimum_Euler_stage_q=min(float(q1.min()), float(q2.min())),
                         circulation_ledger_relative=error))
                if step + 1 in (steps // 2, steps):
                    snapshot(step + 1)
                if (step + 1) % 25 == 0:
                    print(json.dumps(dict(case=name, completed_steps=step + 1, steps=steps)), flush=True)
    finally:
        # All current-q boundary/velocity/flux calls are over for this case.
        # No returned object retains mat; release it before stack/save/next case.
        del mat
    ACTIVE.update(stage=None, phase='final_case_save')
    check_time()
    tick = time.perf_counter()
    raw = LOCAL / (name + '.npz')
    arrays = {key: np.stack([s[key] for s in snapshots]) for key in snapshots[0]}
    save_npz(raw, **arrays, r=g['r'], rc=g['rc'], z=g['z'], J0=flow0['J'],
             exact_u0=exact_u, exact_J0=exact_J, boundary_r=tr, boundary_z=tz)
    del arrays
    raw_record = dict(path=raw.name, **identity(raw))
    final_array_save_seconds = time.perf_counter() - tick
    solves = [x for x in records if x['kind'] in ('stage', 'snapshot')]
    stages = [x for x in records if x['kind'] == 'stage']
    assert len(solves) == 2 * steps + 3 and len(stages) == 2 * steps
    direct_counts = dict(solves=len(solves), rhs_assemblies=len(solves),
                         forward_transforms=len(solves), factorizations=len(solves),
                         triangular_solves=len(solves), inverse_transforms=len(solves),
                         original_rhs_assemblies=len(solves), original_residual_checks=len(solves),
                         factor_reuses=0, new_CG_solves=0)
    record = dict(name=name, R=R, Z=R, radial_cells=nr, axial_cells=g['nz'], h=g['h'],
        dt=dt, steps=steps, angular_order=order, kernel=krecord,
        method='ordinary_FFT_sine_Thomas', elliptic_method='ordinary_FFT_sine_Thomas', elliptic_solves=len(solves),
        transport_stages=len(stages), initial_analytic_errors=initial_error, snapshots=stats,
        checkpoint_records=checkpoint_records, direct_solver_counts=direct_counts,
        direct_solver_phase_seconds={key: sum(x['solver'][key] for x in solves)
                                     for key in SOLVER_PHASES + ('checked_solve_seconds',)},
        max_CFL=max(x['outgoing_CFL'] for x in stages),
        max_volume_divergence=max(x['max_volume_divergence'] for x in solves),
        max_solver_true_residual=max(x['solver']['true_weighted_relative_residual'] for x in solves),
        max_circulation_ledger_relative=max(ledger),
        minimum_Euler_stage_q=min(x['minimum_Euler_stage_q'] for x in records if x['kind'] == 'step'),
        q_squared_relative_drift=[abs(s['q_squared_integral'] / stats[0]['q_squared_integral'] - 1.) for s in stats],
        impulse_relative_drift=[abs(s['axial_impulse'] / stats[0]['axial_impulse'] - 1.) for s in stats],
        phase_seconds={key: sum(x.get(key, 0.) for x in records) for key in
                       ('boundary_seconds', 'linear_solve_seconds', 'reconstruction_seconds', 'transport_seconds')},
        checkpoint_save_seconds=checkpoint_seconds, final_array_save_seconds=final_array_save_seconds,
        green_released_before_final_array_save=True,
        log=dict(path=path.name, **identity(path)), raw=raw_record,
        case_elapsed_before_record_write_seconds=time.perf_counter() - begin)
    write_json(LOCAL / (name + '.json'), record)
    checkpoint_event(dict(kind='case_completed', name=name,
                          record=dict(path=name + '.json', **identity(LOCAL / (name + '.json')))))
    RUNTIME_COUNTS['completed_cases'] += 1
    print(json.dumps(dict(case=name, completed=True,
                          seconds=record['case_elapsed_before_record_write_seconds'])), flush=True)
    return record, dict(g=g, snapshots=snapshots)


def load_old_field(name, expected_config):
    path = OLD_LOCAL / (name + '.npz')
    metadata_path = OLD_LOCAL / (name + '.json')
    metadata = json.loads(metadata_path.read_text(encoding='utf8'))
    _, R, nr, dt, order = expected_config
    assert metadata['name'] == name and metadata['R'] == R
    assert metadata['radial_cells'] == nr and metadata['axial_cells'] == 2 * nr
    assert metadata['dt'] == dt and metadata['angular_order'] == order
    assert [s['time'] for s in metadata['snapshots']] == list(TIMES)
    assert identity(path) == {key: metadata['raw'][key] for key in ('bytes', 'sha256')}
    snapshots = []
    with np.load(path, allow_pickle=False) as saved:
        for index in range(3):
            snapshots.append({key: saved[key][index].copy()
                              for key in ('q', 'qr', 'qz', 'u', 'ur', 'uz')})
    return dict(g=base.geometry(R, nr), snapshots=snapshots), dict(
        name=name, raw=dict(path=str(path), **identity(path)),
        metadata=dict(path=str(metadata_path), **identity(metadata_path)))


def main():
    global CHECKPOINT_STREAM
    assert LOCAL.is_dir()
    assert platform.python_version() == '3.12.14'
    assert np.__version__ == '2.3.5'
    check_time()
    # Same T56 quadrature and unchanged base.compare/evaluate_saved functions.
    gauss = (np.polynomial.legendre.leggauss(3), np.polynomial.legendre.leggauss(2))
    fields = {}
    checkpoint_path = LOCAL / 'checkpoints.jsonl'
    with checkpoint_path.open('x', encoding='utf8', newline='\n') as CHECKPOINT_STREAM:
        checkpoint_event(dict(kind='started', schema='t59-partial-checkpoints-v1',
                              source_identities=SOURCE_BEFORE, whole_task_qualified=False))
        for config in CASES:
            record, field = solve_case(config, gauss)
            CASE_RECORDS.append(record)
            fields[record['name']] = field
        ACTIVE.update(case=None, step=None, stage=None, phase='comparisons')
        check_time()
        byname = {c['name']: c for c in CASE_RECORDS}
        comparisons = []
        tick = time.perf_counter()
        for a, b, kind in [('S64', 'S128', 'space'), ('S128', 'S256', 'space'),
                           ('S128', 'T128', 'time'), ('S128', 'D192', 'domain'),
                           ('S128', 'Q128', 'angular')]:
            for index, t in enumerate(TIMES):
                check_time()
                metrics = base.compare(fields[a], fields[b], index, gauss)
                sa = byname[a]['snapshots'][index]
                sb = byname[b]['snapshots'][index]
                metrics.update(axial_centroid_absolute=abs(sa['centroid'][1] - sb['centroid'][1]),
                    covariance_relative=float(np.linalg.norm(np.array(sa['covariance']) -
                                                             np.array(sb['covariance'])) / base.SHAPE_NORM))
                comparisons.append(dict(a=a, b=b, kind=kind, time=t, **metrics))
        comparison_seconds = time.perf_counter() - tick
        port_regressions, old_inputs = [], []
        tick = time.perf_counter()
        for config in CASES[:2]:
            name = config[0]
            old, input_record = load_old_field(name, config)
            old_inputs.append(input_record)
            for index, t in enumerate(TIMES):
                check_time()
                # Second argument supplies the OLD physical-norm denominator.
                metrics = base.compare(fields[name], old, index, gauss)
                port_regressions.append(dict(name=name, time=t, index=index,
                    denominator='old_T56', **metrics,
                    passed=metrics['vorticity_relative'] <= 1e-7 and metrics['velocity_relative'] <= 1e-7))
            del old
        port_regression_seconds = time.perf_counter() - tick
        ratios = []
        for index in (1, 2):
            coarse = comparisons[index]['vorticity_relative']
            fine = comparisons[3 + index]['vorticity_relative']
            ratios.append(dict(time=TIMES[index], coarse=coarse, fine=fine,
                ratio=coarse / fine if fine > 0. else None,
                small_error_waiver=max(coarse, fine) <= 1e-8,
                passed=max(coarse, fine) <= 1e-8 or coarse >= 1.5 * fine))
        initial_checks = {c['name']: max(c['initial_analytic_errors'].values()) <=
                          (.01 if c['name'] == 'S64' else .005) for c in CASE_RECORDS}
        checks = dict(initial_analytic=all(initial_checks.values()),
            all_stage_invariants=all(c['max_CFL'] <= .5 and c['max_volume_divergence'] <= 1e-10 and
                c['minimum_Euler_stage_q'] >= 0. and c['max_solver_true_residual'] <= 1e-10 for c in CASE_RECORDS),
            vorticity_disagreements=all(c['vorticity_relative'] <= .01 for c in comparisons),
            velocity_disagreements=all(c['velocity_relative'] <= (.02 if c['kind'] == 'space' else .01) for c in comparisons),
            centroid_disagreements=all(c['axial_centroid_absolute'] <= .01 for c in comparisons),
            covariance_disagreements=all(c['covariance_relative'] <= .01 for c in comparisons),
            spatial_reduction=all(c['passed'] for c in ratios),
            circulation_ledger=all(c['max_circulation_ledger_relative'] <= 1e-10 for c in CASE_RECORDS),
            q_squared_drift=all(max(c['q_squared_relative_drift']) <= .02 for c in CASE_RECORDS),
            axial_impulse_drift=all(max(c['impulse_relative_drift']) <= .01 for c in CASE_RECORDS),
            solver_port_regression=all(c['passed'] for c in port_regressions))
        assert RUNTIME_COUNTS == dict(elliptic_attempts=1418, elliptic_completed=1418,
            transport_stages=1400, completed_steps=700, snapshots=18,
            completed_cases=6, new_CG_solves=0)
        source_after = {key: identity(path) for key, path in SOURCE_PATHS.items()}
        assert SOURCE_BEFORE == source_after
        checkpoint_event(dict(kind='schedule_and_comparisons_completed', checks=checks,
                              runtime_counts=RUNTIME_COUNTS, whole_task_qualified=False))
    CHECKPOINT_STREAM = None
    check_time()
    elapsed = time.perf_counter() - START
    result = dict(schema='t59-direct-coupled-reference-v1',
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='qualified_short_reference_only' if all(checks.values()) else 'failed_checks',
        python=platform.python_version(), numpy=np.__version__, executable=sys.executable,
        **SOURCE_BEFORE, source_identities_after=source_after, source_identities_unchanged=True,
        cases=CASE_RECORDS, comparisons=comparisons, port_regressions=port_regressions,
        old_regression_inputs=old_inputs, spatial_reductions=ratios,
        initial_checks=initial_checks, checks=checks, runtime_counts=RUNTIME_COUNTS,
        direct_solver_phase_seconds=SOLVER_SECONDS,
        phase_timing_note='Case phases and direct subphases overlap; do not add them twice. Child wall time includes all work.',
        comparison_seconds=comparison_seconds, port_regression_seconds=port_regression_seconds,
        checkpoint_records=CHECKPOINTS,
        checkpoint_index=dict(path=str(checkpoint_path.relative_to(ROOT)), **identity(checkpoint_path)),
        completed_trajectories=6, new_completed_trajectories=6, reused_trajectories=0,
        time_end=.25, candidate_trajectories=0, new_CG_solves=0,
        full_t1_task_pass=None, formal_error_certificate=False,
        prior_T56_status='failed_checks', prior_T57_status='timeout_no_retry',
        prior_child_seconds=PRIOR_CHILD_SECONDS,
        prior_plus_child_elapsed_before_result_write_seconds=PRIOR_CHILD_SECONDS + elapsed,
        child_elapsed_before_result_write_seconds=elapsed)
    write_json(ROOT / 'result.json', result)
    check_time()
    print(json.dumps(dict(status=result['status'], checks=checks)), flush=True)
    return 0 if all(checks.values()) else 2


def run_terminal():
    try:
        return main()
    except Exception as error:
        # Completed NPZ/JSON/checkpoint/log files remain untouched. No retry,
        # fallback, resume, numerical repair or post-failure scientific work.
        failure = dict(schema='t59-terminal-failure-v1', status='execution_failed_partial',
            error_type=type(error).__name__, error=str(error), active=ACTIVE.copy(),
            traceback=traceback.format_exc(), runtime_counts=RUNTIME_COUNTS.copy(),
            direct_solver_phase_seconds=SOLVER_SECONDS.copy(),
            completed_case_records=CASE_RECORDS, checkpoint_records=CHECKPOINTS,
            whole_task_qualified=False, retry_allowed=False,
            child_elapsed_before_failure_write_seconds=time.perf_counter() - START)
        if LOCAL.is_dir():
            write_json(LOCAL / 'failure.json', failure)
        print(json.dumps(dict(status=failure['status'], error=failure['error'], active=ACTIVE)), flush=True)
        return 3


if __name__ == '__main__':
    raise SystemExit(run_terminal())
