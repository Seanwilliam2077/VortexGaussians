"""Two fixed cheap ordinary arms; no GL or reference evaluations."""
from contextlib import contextmanager
import datetime
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import struct
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = HERE / 'run-01'
BASE = ROOT / 'tracks/tog/tasks/t32-ordinary-volume-entry'
PRIOR = ROOT / 'tracks/tog/tasks/t35-first-complete-frame/run-01'
DELIVERY = ROOT / 'tracks/tog/tasks/t36-ordinary-output-replay/run-01'
EPS, PRUNE_ERROR, FP_ALLOWANCE = .001, .00025, 1e-10
RAW_CAP = 16 * 1024 * 1024
WIDTH, HEIGHT = 256, 192
OLD_RECORD = struct.Struct('<31d10I')
DELIVERY_RECORD = struct.Struct('<13d6I')
ARMS = ('sorted', 'mixture')
PROGRESS_HEADER = struct.Struct('<8s4Q')
NO_PIXEL = (1 << 64) - 1
STAGE_NAMES = ['initial_source_check', 'module_import', 'decode', 'evidence_setup']
for arm in ARMS:
    STAGE_NAMES.extend(arm + '.' + name for name in [
        'tree_build', 'camera', 'preparation', 'output', 'comparison', 'stream_write', 'coverage'])
STAGE_NAMES.append('final_source_check')
STAGES = {name: i + 1 for i, name in enumerate(STAGE_NAMES)}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def encoded(value):
    return (json.dumps(value, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def save_new(path, value):
    data = encoded(value)
    with path.open('xb') as stream:
        require(stream.write(data) == len(data), 'Short JSON write: ' + path.name)
    return len(data)


def normalized(a, b):
    return abs(a - b) / (1e-12 * max(1., abs(a), abs(b)))


class Timings:
    """One overwritten checksummed stage record; no per-pixel JSON journal."""
    def __init__(self):
        self.file = (OUT / 'progress.bin').open('x+b', buffering=0)
        self.sequence = 0
        self.seconds = {}
        self.last = {}
        self.failed = None
        self.stage = None

    def progress(self, name, index, started, state):
        self.sequence += 1
        head = PROGRESS_HEADER.pack(b'T37PRG01', self.sequence,
                                    NO_PIXEL if index is None else index,
                                    STAGES[name] | (state << 32), started)
        payload = head + hashlib.sha256(head).digest()
        self.file.seek(0)
        require(self.file.write(payload) == len(payload), 'Short progress write')

    @contextmanager
    def measure(self, name, index=None):
        self.stage = name
        started = time.perf_counter_ns()
        error = None
        try:
            self.progress(name, index, started, 0)
            yield
        except BaseException as caught:
            error = caught
            raise
        finally:
            try:
                self.progress(name, index, started, 1 if error is None else 2)
            finally:
                seconds = (time.perf_counter_ns() - started) / 1e9
                self.last[name] = seconds
                self.seconds[name] = self.seconds.get(name, 0.) + seconds
                if error is not None:
                    self.failed = {'stage': name, 'pixel_index': index, 'seconds': seconds}


def main():
    tic = time.perf_counter_ns()
    deadline_ns = tic + 60_000_000_000
    require((OUT / 'attempt.json').exists(), 'Supervisor attempt reservation required')
    save_new(OUT / 'worker-start.json', {
        'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'start_perf_counter_ns': tic, 'computation_deadline_ns': deadline_ns})
    timer = Timings()
    frozen_bytes = (HERE / 'freeze.json').read_bytes()
    freeze = json.loads(frozen_bytes)
    active = evidence = evidence_module = frame_info = None
    prior_result = delivery_result = old_raw = delivery_raw = None
    arm_reports = []
    completed = 0
    failed = None
    initial_source_check = {'pass': False}
    final_source_check = None
    status = 'failed'

    def check_time():
        if time.perf_counter_ns() >= deadline_ns:
            raise TimeoutError('T37 computation deadline')

    def verify_sources():
        for item in freeze['artifacts']:
            path = (ROOT / item['path']).resolve()
            require(path.is_relative_to(ROOT), 'Frozen path escapes repository')
            data = path.read_bytes()
            require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'],
                    'Frozen input changed: ' + item['path'])
        require((HERE / 'freeze.json').read_bytes() == frozen_bytes, 'Freeze changed')

    def saved_pixels(directory, result, record_size):
        info = next(item for item in result['evidence']['files'] if item['path'] == 'pixels.bin.gz')
        packed = (directory / 'pixels.bin.gz').read_bytes()
        require(len(packed) == info['bytes'] and hashlib.sha256(packed).hexdigest() == info['sha256'], 'Saved compressed pixel identity')
        raw = gzip.decompress(packed)
        require(len(raw) == WIDTH * HEIGHT * record_size == info['raw_bytes'] and
                hashlib.sha256(raw).hexdigest() == info['raw_sha256'], 'Saved raw pixel identity')
        return raw, info

    try:
        with timer.measure('initial_source_check'):
            verify_sources()
            initial_source_check = {'pass': True}
            check_time()
        with timer.measure('module_import'):
            adapter = load('t37_adapter', BASE / 'adapter.py')
            kernel = load('t37_mass_kernel', ROOT / 'tracks/tog/tasks/t22-prefix-complete-cost/integrators.py')
            methods = load('t37_methods', HERE / 'methods.py')
            evidence_module = load('t37_evidence', HERE / 'evidence.py')
            check_time()
        with timer.measure('decode'):
            packed = (ROOT / 'tracks/tog/tasks/t31-local-carrier/run-01/carrier.json.gz').read_bytes()
            require(len(packed) == 58581 and hashlib.sha256(packed).hexdigest() ==
                    '39f4dc758bb790f3b88bb2bbfa65dbe469c030289d4237476f598e29b823dcf2', 'Carrier compressed identity')
            raw = gzip.decompress(packed)
            require(len(raw) == 167310 and hashlib.sha256(raw).hexdigest() ==
                    'b2a666a4a54b075e11e0e841a02b5d4768f399c715ea6cad1e331209185e62d1', 'Carrier raw identity')
            carrier = json.loads(raw)
            require(carrier['width'] == WIDTH and carrier['height'] == HEIGHT and
                    [f['frame'] for f in carrier['frames']] == [90, 180], 'Unexpected carrier geometry')
            require(carrier['views'] == [{'id': 'front', 'yaw': 0}, {'id': 'oblique', 'yaw': .7},
                                        {'id': 'side', 'yaw': 1.4}], 'Unexpected views')
            frame, view = carrier['frames'][0], carrier['views'][0]
            particles = frame['primitives']
            n = len(particles)
            require(frame['frame'] == 90 and n == 270 and view == {'id': 'front', 'yaw': 0}, 'Fixed first frame changed')
            prior_frame = json.loads((PRIOR / 'frame.json').read_bytes())
            prior_result = json.loads((PRIOR / 'result.json').read_bytes())
            delivery_frame = json.loads((DELIVERY / 'frame.json').read_bytes())
            delivery_result = json.loads((DELIVERY / 'result.json').read_bytes())
            runtime = {'python': sys.version, 'platform': platform.platform()}
            require(prior_result['runtime'] == delivery_result['runtime'] == runtime, 'Runtime identity differs')
            require(delivery_result['status'] == 'qualified_ordinary_replay_only' and
                    delivery_result['evidence']['summary']['saved_validation_pass'], 'T36 delivery is not qualified')
            old_raw, prior_file = saved_pixels(PRIOR, prior_result, OLD_RECORD.size)
            delivery_raw, delivery_file = saved_pixels(DELIVERY, delivery_result, DELIVERY_RECORD.size)
            for metadata in [prior_frame, delivery_frame]:
                require(metadata['frame'] == 90 and metadata['view'] == view and
                        metadata['width'] == WIDTH and metadata['height'] == HEIGHT and
                        metadata['particle_count'] == n and metadata['camera_params'] == frame['camera_params'], 'Prior frame contract differs')
            require(prior_frame['cmax'] == delivery_frame['cmax'] and
                    prior_frame['mass_budget'] == delivery_frame['mass_budget'], 'Saved field/pruning metadata differs')
            # These metadata are for validation/publication only. Each delivery
            # arm below recomputes its own maxima, budget, tree and camera.
            frame_info = {'schema': 't37-frame-v1', 'frame': 90, 'view': view, 'width': WIDTH,
                          'height': HEIGHT, 'particle_count': n, 'cmax': prior_frame['cmax'],
                          'mass_budget': prior_frame['mass_budget'], 'camera_params': frame['camera_params'],
                          'camera': prior_frame['camera'], 'arms': list(ARMS),
                          'schedule': 'sorted then mixture; every original pixel row-major in each arm',
                          'prior_raw_pixels_sha256': prior_file['raw_sha256'],
                          't36_raw_pixels_sha256': delivery_file['raw_sha256'],
                          'progress_format': '<8s4Q + sha256(header)', 'progress_stages': STAGES,
                          'progress_states': {'active': 0, 'completed': 1, 'failed': 2}, 'progress_no_pixel': NO_PIXEL}
            check_time()
        with timer.measure('evidence_setup'):
            save_new(OUT / 'frame.json', frame_info)
            evidence = evidence_module.Evidence(OUT)
            check_time()
        for arm_id, arm in enumerate(ARMS):
            counters = {}
            report = {'arm': arm, 'arm_id': arm_id, 'status': 'started', 'completed_pixels': 0,
                      'counters': counters, 'inherited_nontrivial_pixels': 0, 'inherited_mixed_pixels': 0,
                      'rgb_classes': {'1': 0, '2': 0, '3': 0}, 'alpha_classes': {'1': 0, '2': 0}}
            arm_reports.append(report)
            with timer.measure(arm + '.tree_build'):
                check_time()
                cmax = [max(p['color'][k] for p in particles) for k in range(3)]
                mass_budget = min([-math.log1p(-PRUNE_ERROR)] +
                                  [-math.log1p(-PRUNE_ERROR / c) for c in cmax if c > PRUNE_ERROR])
                tree = adapter.build_bvh(particles, counters)
                require(cmax == prior_frame['cmax'] and mass_budget == prior_frame['mass_budget'] and
                        len(tree['nodes']) == prior_frame['bvh_node_count'], 'Arm field/tree/pruning metadata differs')
                report.update(cmax=cmax, mass_budget=mass_budget, bvh_node_count=len(tree['nodes']))
                check_time()
            with timer.measure(arm + '.camera'):
                camera = adapter.camera(frame['camera_params'], 0, WIDTH, HEIGHT)
                require(camera == prior_frame['camera'] == delivery_frame['camera'], 'Arm ordinary camera differs')
                check_time()
            for pixel in range(WIDTH * HEIGHT):
                index = arm_id * WIDTH * HEIGHT + pixel
                i, j = pixel % WIDTH, pixel // WIDTH
                active = {'record_index': index, 'pixel_index': pixel, 'arm': arm, 'arm_id': arm_id,
                          'frame': 90, 'view_id': 'front', 'i': i, 'j': j}
                with timer.measure(arm + '.preparation', index):
                    check_time()
                    ray = adapter.make_ray(camera, i, j)
                    require(normalized(math.fsum(v * v for v in ray['direction']), 1.) <= 1. and
                            math.isfinite(ray['a']) and math.isfinite(ray['b']) and 0 <= ray['a'] < ray['b'], 'Ordinary unit/domain gate')
                    selection = adapter.query(tree, ray, mass_budget, counters)
                    ids, omitted = selection['kept_ids'], selection['omitted_ids']
                    partition_ok = len(ids) + len(omitted) == n and sorted(ids + omitted) == list(range(n))
                    require(partition_ok, 'BVH partition not complete/disjoint')
                    prepared = adapter.project(particles, ids, ray, counters)
                    active.update(ray=ray, selection=selection)
                with timer.measure(arm + '.output', index):
                    answer = methods.solve(prepared, arm, counters, deadline_ns, kernel)
                    active['output'] = answer
                    check_time()
                with timer.measure(arm + '.comparison', index):
                    # Neither saved output nor reference endpoints reach solve.
                    old = OLD_RECORD.unpack_from(old_raw, pixel * OLD_RECORD.size)
                    delivered = DELIVERY_RECORD.unpack_from(delivery_raw, pixel * DELIVERY_RECORD.size)
                    require(old[31] == 1 and old[40] == 1 and delivered[13] == 1 and
                            delivered[17] == 1 and delivered[18] == 1, 'Prior accepted/partition flags')
                    require(all(math.isfinite(old[q]) and 0 <= old[q] <= 1. for q in [21, 22, 23]), 'Prior geometry/projection residual gate')
                    bound = selection['mass_bound']
                    delta = -math.expm1(-bound)
                    require(answer['alpha'] == old[3] == delivered[3] and len(ids) == old[32] == delivered[14] and
                            bound == old[18] == delivered[6] and delta == old[20] == delivered[7], 'Alpha/retention/pruning reproduction mismatch')
                    require(ray['a'] == delivered[4] and ray['b'] == delivered[5] and
                            normalized(ray['a'], old[24]) <= 1. and normalized(ray['b'], old[25]) <= 1., 'Clip reproduction mismatch')
                    require(math.isfinite(old[19]) and 0 <= old[19] <= bound + FP_ALLOWANCE and
                            bound <= mass_budget + FP_ALLOWANCE, 'Inherited omitted mass exceeds charge/budget')
                    require(delta <= PRUNE_ERROR + FP_ALLOWANCE and all(c * delta <= PRUNE_ERROR + FP_ALLOWANCE for c in cmax), 'Pruning radiance/alpha budget')
                    require(len(answer['rgb']) == 3 and 0 <= answer['alpha'] <= 1 and
                            math.isfinite(answer['tau']) and answer['tau'] >= 0 and
                            all(math.isfinite(x) for x in answer['rgb']), 'Invalid cheap output')
                    require(answer['alpha'] == -math.expm1(-answer['tau']), 'Optical mass/alpha consistency')
                    require(all(-FP_ALLOWANCE <= answer['rgb'][k] <= cmax[k] * answer['alpha'] + FP_ALLOWANCE for k in range(3)), 'Necessary color/alpha range failed')
                    require(all(math.isfinite(old[q]) for q in range(4, 11)) and
                            all(0 <= old[4 + k] <= old[7 + k] for k in range(3)) and 0 <= old[10] <= 1., 'Invalid saved reference interval')
                    upper_distance = [max(abs(answer['rgb'][k] - old[4 + k]), abs(answer['rgb'][k] - old[7 + k])) for k in range(3)]
                    lower_distance = [max(old[4 + k] - answer['rgb'][k], 0., answer['rgb'][k] - old[7 + k]) for k in range(3)]
                    rgb_class = 1 if max(upper_distance) <= EPS + FP_ALLOWANCE else 2 if max(lower_distance) > EPS + FP_ALLOWANCE else 3
                    alpha_error = abs(answer['alpha'] - old[10])
                    alpha_class = 1 if alpha_error <= EPS + FP_ALLOWANCE else 2
                    require(old[38] in [0, 1], 'Prior mixed flag')
                    active['comparison'] = {'upper_distance': upper_distance, 'lower_distance': lower_distance,
                                            'alpha_error': alpha_error, 'rgb_class': rgb_class, 'alpha_class': alpha_class,
                                            'inherited_actual_omitted_mass': old[19]}
                    check_time()
                values = {'rgb_r': answer['rgb'][0], 'rgb_g': answer['rgb'][1], 'rgb_b': answer['rgb'][2],
                          'alpha': answer['alpha'], 'tau': answer['tau'], 'ray_near': ray['a'], 'ray_far': ray['b'],
                          'mass_bound': bound, 'prune_delta': delta,
                          'preparation_seconds': timer.last[arm + '.preparation'],
                          'output_seconds': timer.last[arm + '.output'], 'comparison_seconds': timer.last[arm + '.comparison'],
                          'retained_count': len(ids), 'arm_id': arm_id, 'rgb_class': rgb_class,
                          'alpha_class': alpha_class, 'partition_ok': int(partition_ok)}
                with timer.measure(arm + '.stream_write', index):
                    check_time()
                    evidence.write_pixel(index, values)
                    active = None
                    completed += 1
                    report['completed_pixels'] += 1
                    report['inherited_nontrivial_pixels'] += int(old[10] >= .001)
                    report['inherited_mixed_pixels'] += old[38]
                    report['rgb_classes'][str(rgb_class)] += 1
                    report['alpha_classes'][str(alpha_class)] += 1
                check_time()
            with timer.measure(arm + '.coverage'):
                check_time()
                require(report['completed_pixels'] == WIDTH * HEIGHT and
                        report['inherited_nontrivial_pixels'] == 986 and report['inherited_mixed_pixels'] >= 1, 'Arm coverage gate')
                require(not any(key.startswith('gl_') or key == 'integration_evaluations' for key in counters), 'Unexpected quadrature work')
            report['status'] = 'completed_all_pixels_accuracy_classified'
        status = 'screen_computed_pending_saved_validation'
    except Exception as error:
        failed = {'stage': timer.stage, 'code': getattr(error, 'code', type(error).__name__),
                  'error': str(error), 'traceback': traceback.format_exc(), 'ray': active,
                  'failed_stage_timing': timer.failed}
        if active is not None and evidence is not None:
            try:
                evidence.mark_failed(active['record_index'])
            except Exception as marker_error:
                failed['marker_error'] = repr(marker_error)
    finally:
        with timer.measure('final_source_check'):
            try:
                verify_sources()
                final_source_check = {'pass': True}
            except Exception as error:
                final_source_check = {'pass': False, 'error': str(error)}
                if failed is None:
                    failed = {'stage': 'final_source_check', 'code': type(error).__name__, 'error': str(error), 'ray': active}
                status = 'failed'
        if evidence is not None:
            evidence.close()
        timer.file.close()
    scientific_end = time.perf_counter_ns()
    if scientific_end >= deadline_ns:
        status = 'failed'
        if failed is None:
            failed = {'stage': 'computation_deadline', 'code': 'TimeoutError', 'error': 'T37 computation deadline', 'ray': None}
    if failed is not None:
        save_new(OUT / 'failure.json', failed)
    packet = {'schema': 't37-worker-result-v1', 'status': status,
              'scope': 'two ordinary approximations classified against intact saved T35 intervals; completion is not accuracy success',
              'thresholds': {'rgb_alpha': EPS, 'pruning': PRUNE_ERROR, 'numerical_allowance': FP_ALLOWANCE},
              'frame_metadata_path': 'frame.json' if frame_info is not None else None,
              'planned_records': len(ARMS) * WIDTH * HEIGHT, 'completed_records': completed, 'arms': arm_reports,
              'failure_path': 'failure.json' if failed is not None else None,
              'failed_stage': None if failed is None else failed['stage'],
              'failure_code': None if failed is None else failed.get('code'),
              'error': None if failed is None else failed['error'],
              'failed_stage_timing': None if failed is None else failed.get('failed_stage_timing'),
              'stage_seconds_including_failed_work': timer.seconds,
              'stage_timing_note': 'Each stage includes small progress writes. Every arm pays independent preparation/output; comparisons are outside delivery.',
              'computation_elapsed_seconds': (scientific_end - tic) / 1e9,
              'initial_source_check': initial_source_check, 'final_source_check': final_source_check,
              'freeze_sha256': hashlib.sha256(frozen_bytes).hexdigest(),
              'runtime': {'python': sys.version, 'platform': platform.platform()},
              'prior_paid_costs': {name: None if result is None else {
                  'computation_seconds': result['computation_elapsed_seconds'],
                  'publication_seconds': result['publication_seconds'],
                  'stages_seconds': result['stage_seconds_including_failed_work']}
                  for name, result in [('T35', prior_result), ('T36', delivery_result)]},
              'scientific_invocations_in_T37': 1, 'reference_invocations_in_T37': 0, 'GL_invocations_in_T37': 0,
              'simulations': 0, 'new_carriers': 0, 'gpu_runs': 0, 'retries': 0,
              'T35_delivery_status_preserved': 'failed_saved_blue_alias',
              'T36_status_preserved': 'qualified_ordinary_replay_only',
              'not_a_new_method_or_optimized_baseline_speedup_trial': True}
    publication_tic = time.perf_counter_ns()
    try:
        require(evidence is not None and frame_info is not None and old_raw is not None and delivery_raw is not None,
                'No initialized pixel evidence to package')
        packet['evidence'] = evidence_module.finalize(OUT, frame_info['cmax'], frame_info['particle_count'],
                                                     old_raw, delivery_raw, frame_info['mass_budget'])
        summary = packet['evidence']['summary']
        require(summary['saved_validation_pass'] and summary['invalid_saved_records'] == 0, 'Saved output validation failed')
        require(summary['committed_records'] == completed and summary['valid_records'] == completed,
                'Decoded record count differs from worker')
        if status == 'screen_computed_pending_saved_validation':
            require(summary['all_records_valid'] and summary['reference_foreground_pixels'] == 986 and
                    final_source_check['pass'] and completed == len(ARMS) * WIDTH * HEIGHT,
                    'Final complete-screen conditions')
            packet['status'] = status = 'completed_cheap_screen'
        packet['publication_status'] = 'packaged'
    except Exception as error:
        packet['status'] = status = 'failed_saved_delivery'
        packet['publication_status'] = 'failed'
        packet['publication_error'] = repr(error)
    packet['publication_seconds'] = (time.perf_counter_ns() - publication_tic) / 1e9
    packet['worker_elapsed_before_result_seconds'] = (time.perf_counter_ns() - tic) / 1e9
    existing = sum((OUT / name).stat().st_size for name in ['pixels.bin', 'failure.json', 'frame.json'] if (OUT / name).exists())
    packet['raw_other_numeric_bytes'] = existing
    packet['raw_numeric_cap_bytes'] = RAW_CAP
    if existing + len(encoded(packet)) > RAW_CAP:
        packet['status'] = status = 'failed_saved_delivery'
        packet['publication_status'] = 'failed'
        packet['publication_error'] = 'Raw binary + failure + frame metadata + result exceeds 16MiB cap; partial files preserved'
    save_new(OUT / 'result.json', packet)
    print(json.dumps({'status': status, 'completed_records': completed, 'failed_stage': packet['failed_stage'],
                      'publication_status': packet['publication_status'], 'retry_allowed': False}, allow_nan=False))
    return 0 if status == 'completed_cheap_screen' else 2


if __name__ == '__main__':
    raise SystemExit(main())
