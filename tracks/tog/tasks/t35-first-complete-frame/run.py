"""One fixed full-frame invocation; importing this file performs no experiment."""
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
EPS, PRUNE_ERROR, GL_NOMINAL, FP_ALLOWANCE = .001, .00025, .000125, 1e-10
RAW_CAP = 32 * 1024 * 1024
WIDTH, HEIGHT = 256, 192
PROGRESS_HEADER = struct.Struct('<8s4Q')
NO_PIXEL = (1 << 64) - 1
STAGES = {name: i + 1 for i, name in enumerate([
    'initial_source_check', 'module_import', 'decode', 'tree_build', 'camera',
    'evidence_setup', 'ordinary_projection_and_pruning', 'ordinary_solve',
    'independent_projection', 'reference_enclosure', 'qualification',
    'stream_write', 'coverage', 'final_source_check'])}


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
    """Small overwritten checksummed progress record, not a per-pixel journal.

    Stage durations include their progress writes. Complete and failed work are
    accumulated once; the fixed record permits a bounded hard-kill diagnosis.
    """
    def __init__(self):
        self.file = (OUT / 'progress.bin').open('x+b', buffering=0)
        self.sequence = 0
        self.seconds = {}
        self.last = {}
        self.failed = None
        self.stage = None

    def progress(self, name, index, started, state):
        self.sequence += 1
        head = PROGRESS_HEADER.pack(b'T35PRG01', self.sequence,
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
    deadline_ns = tic + 600_000_000_000
    require((OUT / 'attempt.json').exists(), 'Supervisor attempt reservation required')
    save_new(OUT / 'worker-start.json', {
        'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'start_perf_counter_ns': tic, 'computation_deadline_ns': deadline_ns})
    timer = Timings()
    frozen_bytes = (HERE / 'freeze.json').read_bytes()
    freeze = json.loads(frozen_bytes)
    counters, cache = {}, {}
    active = None
    evidence = None
    evidence_module = None
    frame_info = None
    completed = nontrivial_count = mixed_count = 0
    failed = None
    initial_source_check = {'pass': False}
    final_source_check = None
    status = 'failed'

    def check_time():
        if time.perf_counter_ns() >= deadline_ns:
            raise TimeoutError('T35 computation deadline')

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
            adapter = load('t35_adapter', BASE / 'adapter.py')
            ordinary = load('t35_ordinary', BASE / 'ordinary.py')
            reference = load('t35_reference', ROOT / 'tracks/tog/tasks/t34-box-reference-qualification/reference.py')
            kernel = ordinary.load_kernel(ROOT)
            evidence_module = load('t35_evidence', HERE / 'evidence.py')
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
            cmax = [max(p['color'][k] for p in particles) for k in range(3)]
            mass_budget = min([-math.log1p(-PRUNE_ERROR)] +
                              [-math.log1p(-PRUNE_ERROR / c) for c in cmax if c > PRUNE_ERROR])
            check_time()
        with timer.measure('tree_build'):
            tree = adapter.build_bvh(particles, counters)
            check_time()
        with timer.measure('camera'):
            camera = adapter.camera(frame['camera_params'], 0, WIDTH, HEIGHT)
            frame_info = {'schema': 't35-frame-v1', 'frame': 90, 'view': view, 'width': WIDTH,
                          'height': HEIGHT, 'particle_count': n, 'cmax': cmax, 'mass_budget': mass_budget,
                          'camera_params': frame['camera_params'], 'camera': camera,
                          'bvh_node_count': len(tree['nodes']), 'schedule': 'all pixels, row-major top-down',
                          'progress_format': '<8s4Q + sha256(header)', 'progress_stages': STAGES,
                          'progress_states': {'active': 0, 'completed': 1, 'failed': 2},
                          'progress_no_pixel': NO_PIXEL}
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
            with timer.measure('independent_projection', index):
                ref_ray = reference.independent_ray(frame['camera_params'], 0, WIDTH, HEIGHT, i, j)
                ratios = [normalized(a, b) for name in ['origin', 'direction']
                          for a, b in zip(ray[name], ref_ray[name])]
                ratios += [normalized(ray[k], ref_ray[k]) for k in ['a', 'b']]
                ratios.append(normalized(math.fsum(v * v for v in ray['direction']), 1.))
                geometry_ratio = max(ratios)
                require(geometry_ratio <= 1. and ray['a'] < ray['b'], 'Independent ray/clip/unit mismatch')
                allp = reference.project_all(particles, ref_ray, counters)
                mu_ratio = q_ratio = 0.
                for offset, source in enumerate(ids):
                    mu_ratio = max(mu_ratio, normalized(p['mu'][offset], allp['mu'][source]))
                    q_ratio = max(q_ratio, abs(p['weight'][offset] - allp['weight'][source]) /
                                  (1e-12 + 1e-9 * abs(allp['weight'][source])))
                require(mu_ratio <= 1. and q_ratio <= 1., 'Independent projected mean/weight mismatch')
                active.update(reference_ray=ref_ray, geometry_ratio=geometry_ratio,
                              mu_ratio=mu_ratio, q_ratio=q_ratio)
                check_time()
            with timer.measure('reference_enclosure', index):
                ref = reference.enclose(allp, cmax, tuple(answer['rgb']), EPS + FP_ALLOWANCE, counters, deadline_ns)
                active['reference'] = ref
                check_time()
            with timer.measure('qualification', index):
                leaves = ref['leaves']
                if ref['path'] == 'enclosure':
                    require(bool(leaves) and leaves[0][0] == ref_ray['a'] and leaves[-1][1] == ref_ray['b'], 'Reference leaf domain')
                    require(all(cell[0] < cell[1] for cell in leaves) and
                            all(a[1] == b[0] for a, b in zip(leaves, leaves[1:])), 'Reference leaf partition')
                    require(abs(math.fsum(cell[2] for cell in leaves) - ref['retained_alpha']) <= FP_ALLOWANCE, 'Reference absorption accounting')
                else:
                    require(not leaves and ref['path'] in ['empty', 'equal_color'], 'Unexpected analytic reference path')
                low_sum = [math.fsum([ref['analytic_retained_rgb'][k]] + [c[3 + k] for c in leaves]) for k in range(3)]
                high_sum = [math.fsum([ref['analytic_retained_rgb'][k]] + [c[6 + k] for c in leaves]) for k in range(3)]
                require(all(len(c) == 9 and all(math.isfinite(x) for x in c) and c[2] >= 0 and
                            all(-FP_ALLOWANCE <= c[3 + k] <= c[6 + k] + FP_ALLOWANCE and
                                c[6 + k] <= c[2] * cmax[k] + FP_ALLOWANCE for k in range(3)) for c in leaves), 'Reference cell range')
                require(all(abs(ref['lower'][k] - max(0, low_sum[k] - ref['omission_rgb_radius'][k])) <= FP_ALLOWANCE and
                            abs(ref['upper'][k] - (high_sum[k] + ref['omission_rgb_radius'][k])) <= FP_ALLOWANCE for k in range(3)), 'Reference ledger sum mismatch')
                alpha = ref['alpha_full']
                actual_omitted = math.fsum(ref['finite_masses'][source] for source in omitted)
                bound = selection['mass_bound']
                delta = -math.expm1(-bound)
                require(bound <= mass_budget + FP_ALLOWANCE and actual_omitted <= bound + FP_ALLOWANCE, 'BVH omitted mass exceeds charge/budget')
                require(delta <= PRUNE_ERROR + FP_ALLOWANCE and all(c * delta <= PRUNE_ERROR + FP_ALLOWANCE for c in cmax), 'Pruning radiance/alpha budget')
                require(all(math.isfinite(r) and r >= 0 for r in ref['radius']), 'Invalid reference radius')
                endpoint_error = [max(abs(answer['rgb'][k] - ref['lower'][k]), abs(answer['rgb'][k] - ref['upper'][k])) for k in range(3)]
                alpha_error = abs(answer['alpha'] - alpha)
                require(ref['endpoint_errors'] == endpoint_error and ref['stop_reason'] == 'output_endpoint_accepted', 'Reference output decision mismatch')
                require(max(endpoint_error) <= EPS + FP_ALLOWANCE and alpha_error <= EPS + FP_ALLOWANCE, 'Ordinary RGB/alpha exceeds fixed accuracy gate')
                require(0 <= answer['alpha'] <= 1 and all(math.isfinite(x) for x in answer['rgb']), 'Invalid ordinary output')
                require(all(-FP_ALLOWANCE <= answer['rgb'][k] <= cmax[k] * answer['alpha'] + FP_ALLOWANCE for k in range(3)), 'Necessary color/alpha range failed')
                sources = [source for source, mass in enumerate(ref['finite_masses']) if mass >= .0001]
                mixed = len(sources) >= 2 and max(max(particles[s]['color'][k] for s in sources) -
                            min(particles[s]['color'][k] for s in sources) for k in range(3)) > .01
                check_time()
            values = dict(zip(['r', 'g', 'b'], answer['rgb']))
            for prefix, key in [('lower', 'lower'), ('upper', 'upper'), ('analytic', 'analytic_retained_rgb'), ('omission', 'omission_rgb_radius')]:
                values.update({prefix + '_' + channel: ref[key][k] for k, channel in enumerate('rgb')})
            values.update(alpha=answer['alpha'], full_alpha=alpha, retained_alpha=ref['retained_alpha'],
                          mass_bound=bound, actual_omitted_mass=actual_omitted, prune_delta=delta,
                          geometry_ratio=geometry_ratio, mu_ratio=mu_ratio, q_ratio=q_ratio,
                          a=ref_ray['a'], b=ref_ray['b'], retained_count=len(ids),
                          reference_path=evidence_module.REF_PATHS[ref['path']],
                          ordinary_path=evidence_module.ORD_PATHS[answer['path']], gl_order=answer.get('gl_order', 0),
                          mixed=int(mixed), created_cells=ref['created_cells'], partition_ok=int(partition_ok))
            for field, stage in [('preparation_seconds', 'ordinary_projection_and_pruning'), ('ordinary_seconds', 'ordinary_solve'),
                                 ('projection_seconds', 'independent_projection'), ('reference_seconds', 'reference_enclosure'),
                                 ('qualification_seconds', 'qualification')]:
                values[field] = timer.last[stage]
            with timer.measure('stream_write', index):
                check_time()
                evidence.write_pixel(index, values, leaves)
                # Never overwrite an already committed pixel with a failure marker.
                active = None
                completed += 1
                nontrivial_count += int(alpha >= .001)
                mixed_count += int(mixed)
            check_time()
        with timer.measure('coverage'):
            check_time()
            require(completed == WIDTH * HEIGHT and nontrivial_count >= 1 and mixed_count >= 1, 'Full-frame coverage gate')
        status = 'qualified_first_complete_frame_only'
    except Exception as error:
        failed = {'stage': timer.stage, 'code': getattr(error, 'code', type(error).__name__),
                  'error': str(error), 'traceback': traceback.format_exc(), 'ray': active,
                  'failed_stage_timing': timer.failed, 'reference_diagnostics': getattr(error, 'diagnostics', None)}
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
            failed = {'stage': 'computation_deadline', 'code': 'TimeoutError', 'error': 'T35 computation deadline', 'ray': None}
    if failed is not None:
        save_new(OUT / 'failure.json', failed)
    packet = {'schema': 't35-worker-result-v1', 'status': status,
              'scope': 'first authored frame only; binary64 qualification, not a formal floating-point certificate',
              'thresholds': {'rgb_alpha': EPS, 'pruning': PRUNE_ERROR, 'gl_nominal': GL_NOMINAL, 'numerical_allowance': FP_ALLOWANCE},
              'frame_metadata_path': 'frame.json' if frame_info is not None else None,
              'planned_pixels': WIDTH * HEIGHT, 'completed_pixels': completed,
              'nontrivial_pixels': nontrivial_count, 'mixed_pixels': mixed_count,
              'failure_path': 'failure.json' if failed is not None else None,
              'failed_stage': None if failed is None else failed['stage'],
              'failure_code': None if failed is None else failed.get('code'),
              'error': None if failed is None else failed['error'],
              'failed_stage_timing': None if failed is None else failed.get('failed_stage_timing'),
              'counters': counters, 'stage_seconds_including_failed_work': timer.seconds,
              'stage_timing_note': 'Each stage includes its small progress writes; stream writes are separate. Completed-pixel stage sums exclude failed-pixel work.',
              'computation_elapsed_seconds': (scientific_end - tic) / 1e9,
              'initial_source_check': initial_source_check,
              'final_source_check': final_source_check,
              'freeze_sha256': hashlib.sha256(frozen_bytes).hexdigest(),
              'runtime': {'python': sys.version, 'platform': platform.platform()},
              'simulations': 0, 'new_carriers': 0, 'gpu_runs': 0, 'retries': 0,
              'T32_status_preserved': 'failed', 'T33_status_preserved': 'failed',
              'T34_status_preserved': 'qualified_fixed_subset_only',
              'not_a_strong_baseline_or_speedup_trial': True}
    publication_tic = time.perf_counter_ns()
    try:
        require(evidence is not None and frame_info is not None, 'No initialized pixel evidence to package')
        packet['evidence'] = evidence_module.finalize(OUT, frame_info['cmax'], frame_info['particle_count'])
        summary = packet['evidence']['summary']
        require(summary['qualified_pixels'] == completed and summary['nontrivial_pixels'] == nontrivial_count and
                summary['mixed_pixels'] == mixed_count, 'Committed binary counts differ from worker')
        if status == 'qualified_first_complete_frame_only':
            require(summary['all_pixel_records_qualified'] and final_source_check['pass'] and
                    nontrivial_count >= 1 and mixed_count >= 1, 'Final complete-frame conditions')
        packet['publication_status'] = 'packaged'
    except Exception as error:
        packet['status'] = status = 'failed_publication'
        packet['publication_status'] = 'failed'
        packet['publication_error'] = repr(error)
    packet['publication_seconds'] = (time.perf_counter_ns() - publication_tic) / 1e9
    packet['worker_elapsed_before_result_seconds'] = (time.perf_counter_ns() - tic) / 1e9
    existing = sum((OUT / name).stat().st_size for name in ['pixels.bin', 'leaves.bin', 'failure.json', 'frame.json'] if (OUT / name).exists())
    # Include this result's own extent, without a self-referential byte-count field.
    packet['raw_other_numeric_bytes'] = existing
    packet['raw_numeric_cap_bytes'] = RAW_CAP
    if existing + len(encoded(packet)) > RAW_CAP:
        packet['status'] = status = 'failed_publication'
        packet['publication_status'] = 'failed'
        packet['publication_error'] = 'Raw binary + failure + frame metadata + result exceeds 32MiB cap; all partial files preserved'
    save_new(OUT / 'result.json', packet)
    print(json.dumps({'status': status, 'completed_pixels': completed, 'failed_stage': packet['failed_stage'],
                      'publication_status': packet['publication_status'], 'retry_allowed': False}, allow_nan=False))
    return 0 if status == 'qualified_first_complete_frame_only' else 2


if __name__ == '__main__':
    raise SystemExit(main())
