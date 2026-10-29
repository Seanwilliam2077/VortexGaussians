"""One ordinary-only replay against frozen T35 interval evidence; no reference imports."""
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
EPS, PRUNE_ERROR, GL_NOMINAL, FP_ALLOWANCE = .001, .00025, .000125, 1e-10
RAW_CAP = 32 * 1024 * 1024
WIDTH, HEIGHT = 256, 192
OLD_RECORD = struct.Struct('<31d10I')
PROGRESS_HEADER = struct.Struct('<8s4Q')
NO_PIXEL = (1 << 64) - 1
STAGES = {name: i + 1 for i, name in enumerate([
    'initial_source_check', 'module_import', 'decode', 'tree_build', 'camera',
    'evidence_setup', 'ordinary_projection_and_pruning', 'ordinary_solve',
    'saved_evidence_comparison', 'stream_write', 'coverage', 'final_source_check'])}


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
        head = PROGRESS_HEADER.pack(b'T36PRG01', self.sequence,
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
    deadline_ns = tic + 300_000_000_000
    require((OUT / 'attempt.json').exists(), 'Supervisor attempt reservation required')
    save_new(OUT / 'worker-start.json', {
        'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'start_perf_counter_ns': tic, 'computation_deadline_ns': deadline_ns})
    timer = Timings()
    frozen_bytes = (HERE / 'freeze.json').read_bytes()
    freeze = json.loads(frozen_bytes)
    counters, cache = {}, {}  # One initially empty ordinary rule cache.
    active = evidence = evidence_module = frame_info = prior_result = None
    old_raw = None
    completed = nontrivial_count = mixed_count = 0
    failed = None
    initial_source_check = {'pass': False}
    final_source_check = None
    status = 'failed'

    def check_time():
        if time.perf_counter_ns() >= deadline_ns:
            raise TimeoutError('T36 computation deadline')

    def verify_sources():
        for item in freeze['artifacts']:
            path = (ROOT / item['path']).resolve()
            require(path.is_relative_to(ROOT), 'Frozen path escapes repository')
            data = path.read_bytes()
            require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'],
                    'Frozen input changed: ' + item['path'])
        require((HERE / 'freeze.json').read_bytes() == frozen_bytes, 'Freeze changed')

    try:
        with timer.measure('initial_source_check'):
            verify_sources()
            initial_source_check = {'pass': True}
            check_time()
        with timer.measure('module_import'):
            adapter = load('t36_adapter', BASE / 'adapter.py')
            ordinary = load('t36_ordinary', BASE / 'ordinary.py')
            kernel = ordinary.load_kernel(ROOT)
            evidence_module = load('t36_evidence', HERE / 'evidence.py')
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
            require(prior_result['runtime'] == {'python': sys.version, 'platform': platform.platform()}, 'Replay runtime identity differs')
            require(prior_result['thresholds'] == {'rgb_alpha': EPS, 'pruning': PRUNE_ERROR,
                    'gl_nominal': GL_NOMINAL, 'numerical_allowance': FP_ALLOWANCE}, 'Prior thresholds differ')
            prior_file = next(item for item in prior_result['evidence']['files'] if item['path'] == 'pixels.bin.gz')
            packed_pixels = (PRIOR / 'pixels.bin.gz').read_bytes()
            require(len(packed_pixels) == prior_file['bytes'] and hashlib.sha256(packed_pixels).hexdigest() == prior_file['sha256'], 'Prior compressed pixel identity')
            old_raw = gzip.decompress(packed_pixels)
            require(len(old_raw) == WIDTH * HEIGHT * OLD_RECORD.size == prior_file['raw_bytes'] and
                    hashlib.sha256(old_raw).hexdigest() == prior_file['raw_sha256'], 'Prior raw pixel identity')
            # T35's duplicate b names are never used for decoding. Slot 2 is
            # corrupted blue and is deliberately never read as RGB evidence.
            cmax = [max(p['color'][k] for p in particles) for k in range(3)]
            mass_budget = min([-math.log1p(-PRUNE_ERROR)] +
                              [-math.log1p(-PRUNE_ERROR / c) for c in cmax if c > PRUNE_ERROR])
            require(prior_frame['frame'] == 90 and prior_frame['view'] == view and
                    prior_frame['width'] == WIDTH and prior_frame['height'] == HEIGHT and
                    prior_frame['particle_count'] == n and prior_frame['camera_params'] == frame['camera_params'] and
                    prior_frame['cmax'] == cmax and prior_frame['mass_budget'] == mass_budget, 'Prior frame contract differs')
            check_time()
        with timer.measure('tree_build'):
            tree = adapter.build_bvh(particles, counters)
            require(len(tree['nodes']) == prior_frame['bvh_node_count'], 'BVH build extent differs')
            check_time()
        with timer.measure('camera'):
            camera = adapter.camera(frame['camera_params'], 0, WIDTH, HEIGHT)
            require(camera == prior_frame['camera'], 'Ordinary camera differs from frozen prior')
            frame_info = {'schema': 't36-frame-v1', 'frame': 90, 'view': view, 'width': WIDTH,
                          'height': HEIGHT, 'particle_count': n, 'cmax': cmax, 'mass_budget': mass_budget,
                          'camera_params': frame['camera_params'], 'camera': camera,
                          'bvh_node_count': len(tree['nodes']), 'schedule': 'all pixels, row-major top-down',
                          'prior_raw_pixels_sha256': prior_file['raw_sha256'],
                          'prior_reference': 'T35 intact saved positional endpoints; no reference reevaluation',
                          'progress_format': '<8s4Q + sha256(header)', 'progress_stages': STAGES,
                          'progress_states': {'active': 0, 'completed': 1, 'failed': 2}, 'progress_no_pixel': NO_PIXEL}
            check_time()
        with timer.measure('evidence_setup'):
            save_new(OUT / 'frame.json', frame_info)
            evidence = evidence_module.Evidence(OUT, WIDTH, HEIGHT)
            check_time()
        for index in range(WIDTH * HEIGHT):
            i, j = index % WIDTH, index // WIDTH
            active = {'pixel_index': index, 'frame': 90, 'view_id': 'front', 'i': i, 'j': j}
            with timer.measure('ordinary_projection_and_pruning', index):
                check_time()
                ray = adapter.make_ray(camera, i, j)
                require(normalized(math.fsum(v * v for v in ray['direction']), 1.) <= 1. and
                        math.isfinite(ray['a']) and math.isfinite(ray['b']) and 0 <= ray['a'] < ray['b'], 'Ordinary unit/domain gate')
                selection = adapter.query(tree, ray, mass_budget, counters)
                ids, omitted = selection['kept_ids'], selection['omitted_ids']
                partition_ok = len(ids) + len(omitted) == n and sorted(ids + omitted) == list(range(n))
                require(partition_ok, 'BVH partition not complete/disjoint')
                p = adapter.project(particles, ids, ray, counters)
                active.update(ray=ray, selection=selection)
            with timer.measure('ordinary_solve', index):
                answer = ordinary.solve(p, GL_NOMINAL, counters, deadline_ns, cache, kernel)
                active['ordinary'] = answer
                check_time()
            with timer.measure('saved_evidence_comparison', index):
                # The saved interval is accessed only after the ordinary solve.
                old = OLD_RECORD.unpack_from(old_raw, index * OLD_RECORD.size)
                require(old[31] == 1 and old[40] == 1, 'Prior accepted/partition flags')
                require(all(math.isfinite(old[q]) and 0 <= old[q] <= 1. for q in [21, 22, 23]), 'Prior geometry/projection residual gate')
                code = {'computed_zero_mass': 1, 'ordinary_color_box': 2, 'gl_no_fallback': 3}[answer['path']]
                order = answer.get('gl_order', 0)
                bound = selection['mass_bound']
                delta = -math.expm1(-bound)
                replay_match = (answer['rgb'][0] == old[0] and answer['rgb'][1] == old[1] and
                                answer['alpha'] == old[3] and len(ids) == old[32] and code == old[34] and
                                order == old[35] and bound == old[18] and delta == old[20])
                require(replay_match, 'Exact intact ordinary replay mismatch')
                require(normalized(ray['a'], old[24]) <= 1. and normalized(ray['b'], old[25]) <= 1., 'Replay vs saved independent clip mismatch')
                require(math.isfinite(old[19]) and 0 <= old[19] <= bound + FP_ALLOWANCE and
                        bound <= mass_budget + FP_ALLOWANCE, 'Inherited omitted mass exceeds charge/budget')
                require(delta <= PRUNE_ERROR + FP_ALLOWANCE and all(c * delta <= PRUNE_ERROR + FP_ALLOWANCE for c in cmax), 'Pruning radiance/alpha budget')
                require(0 <= answer['alpha'] <= 1 and all(math.isfinite(x) for x in answer['rgb']), 'Invalid ordinary output')
                require(all(-FP_ALLOWANCE <= answer['rgb'][k] <= cmax[k] * answer['alpha'] + FP_ALLOWANCE for k in range(3)), 'Necessary color/alpha range failed')
                require(all(math.isfinite(old[q]) for q in range(4, 11)) and
                        all(old[4 + k] <= old[7 + k] for k in range(3)), 'Invalid saved reference interval')
                endpoint_error = [max(abs(answer['rgb'][k] - old[4 + k]), abs(answer['rgb'][k] - old[7 + k])) for k in range(3)]
                alpha_error = abs(answer['alpha'] - old[10])
                require(max(endpoint_error) <= EPS + FP_ALLOWANCE and alpha_error <= EPS + FP_ALLOWANCE, 'New RGB/alpha exceeds frozen reference gate')
                require(old[38] in [0, 1], 'Prior mixed flag')
                active['comparison'] = {'endpoint_error': endpoint_error, 'alpha_error': alpha_error,
                                        'inherited_actual_omitted_mass': old[19], 'replay_match': replay_match}
                check_time()
            values = {'rgb_r': answer['rgb'][0], 'rgb_g': answer['rgb'][1], 'rgb_b': answer['rgb'][2],
                      'alpha': answer['alpha'], 'ray_near': ray['a'], 'ray_far': ray['b'],
                      'mass_bound': bound, 'prune_delta': delta,
                      'preparation_seconds': timer.last['ordinary_projection_and_pruning'],
                      'ordinary_seconds': timer.last['ordinary_solve'],
                      'comparison_seconds': timer.last['saved_evidence_comparison'],
                      'max_endpoint_error': max(endpoint_error), 'alpha_error': alpha_error,
                      'retained_count': len(ids), 'ordinary_path': code, 'gl_order': order,
                      'partition_ok': int(partition_ok), 'replay_match': int(replay_match)}
            with timer.measure('stream_write', index):
                check_time()
                evidence.write_pixel(index, values)
                active = None  # The successful committed record must not be overwritten.
                completed += 1
                nontrivial_count += int(old[10] >= .001)
                mixed_count += old[38]
            check_time()
        with timer.measure('coverage'):
            check_time()
            require(completed == WIDTH * HEIGHT and nontrivial_count >= 1 and mixed_count >= 1, 'Full-frame inherited coverage gate')
        status = 'ordinary_replay_computed_pending_saved_validation'
    except Exception as error:
        failed = {'stage': timer.stage, 'code': getattr(error, 'code', type(error).__name__),
                  'error': str(error), 'traceback': traceback.format_exc(), 'ray': active,
                  'failed_stage_timing': timer.failed}
        if active is not None and evidence is not None:
            try:
                evidence.mark_failed(active['pixel_index'])
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
            failed = {'stage': 'computation_deadline', 'code': 'TimeoutError', 'error': 'T36 computation deadline', 'ray': None}
    if failed is not None:
        save_new(OUT / 'failure.json', failed)
    packet = {'schema': 't36-worker-result-v1', 'status': status,
              'scope': 'ordinary-only replay against intact T35 saved intervals; not new reference or source-level independent validation',
              'thresholds': {'rgb_alpha': EPS, 'pruning': PRUNE_ERROR, 'gl_nominal': GL_NOMINAL, 'numerical_allowance': FP_ALLOWANCE},
              'frame_metadata_path': 'frame.json' if frame_info is not None else None,
              'planned_pixels': WIDTH * HEIGHT, 'completed_pixels': completed,
              'inherited_nontrivial_pixels': nontrivial_count, 'inherited_mixed_pixels': mixed_count,
              'failure_path': 'failure.json' if failed is not None else None,
              'failed_stage': None if failed is None else failed['stage'],
              'failure_code': None if failed is None else failed.get('code'),
              'error': None if failed is None else failed['error'],
              'failed_stage_timing': None if failed is None else failed.get('failed_stage_timing'),
              'counters': counters, 'stage_seconds_including_failed_work': timer.seconds,
              'stage_timing_note': 'Each stage includes small progress writes; completed-pixel sums exclude failed work. Reference endpoints are read only during comparison.',
              'computation_elapsed_seconds': (scientific_end - tic) / 1e9,
              'initial_source_check': initial_source_check, 'final_source_check': final_source_check,
              'freeze_sha256': hashlib.sha256(frozen_bytes).hexdigest(),
              'runtime': {'python': sys.version, 'platform': platform.platform()},
              'prior_T35_paid_cost': None if prior_result is None else {
                  'computation_seconds': prior_result['computation_elapsed_seconds'],
                  'publication_seconds': prior_result['publication_seconds'],
                  'stages_seconds': prior_result['stage_seconds_including_failed_work']},
              'scientific_invocations_in_T35_T36': 2, 'reference_invocations_in_T36': 0,
              'simulations': 0, 'new_carriers': 0, 'gpu_runs': 0, 'retries': 0,
              'T35_delivery_status_preserved': 'failed_saved_blue_alias',
              'not_a_fresh_renderer_reference_cost_or_speedup_trial': True}
    publication_tic = time.perf_counter_ns()
    try:
        require(evidence is not None and frame_info is not None and old_raw is not None, 'No initialized pixel evidence to package')
        packet['evidence'] = evidence_module.finalize(OUT, frame_info['cmax'], frame_info['particle_count'],
                                                     old_raw, frame_info['mass_budget'], WIDTH, HEIGHT)
        summary = packet['evidence']['summary']
        require(summary['qualified_pixels'] == completed and summary['nontrivial_pixels'] == nontrivial_count and
                summary['mixed_pixels'] == mixed_count, 'Decoded counts differ from worker')
        require(summary['saved_validation_pass'] and summary['invalid_saved_pixels'] == 0, 'Saved output validation failed')
        if status == 'ordinary_replay_computed_pending_saved_validation':
            require(summary['all_pixel_records_qualified'] and final_source_check['pass'] and
                    completed == WIDTH * HEIGHT and nontrivial_count >= 1 and mixed_count >= 1, 'Final complete replay conditions')
            packet['status'] = status = 'qualified_ordinary_replay_only'
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
        packet['publication_error'] = 'Raw binary + failure + frame metadata + result exceeds 32MiB cap; partial files preserved'
    save_new(OUT / 'result.json', packet)
    print(json.dumps({'status': status, 'completed_pixels': completed, 'failed_stage': packet['failed_stage'],
                      'publication_status': packet['publication_status'], 'retry_allowed': False}, allow_nan=False))
    return 0 if status == 'qualified_ordinary_replay_only' else 2


if __name__ == '__main__':
    raise SystemExit(main())

