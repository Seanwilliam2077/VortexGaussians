"""One T70 scientific child, observed OS resources and saved-result readback; stdlib only."""
import argparse
import ast
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
MEMORY = REPO / 'tracks/tog/tasks/t57-finer-short-reference/memory.py'
PRIOR = 1990.3707298998488
LIMIT, CAP, REQUIRED, INTERVAL = 120.0, 536870912, 1073741824, .25
CHECKS = ('frozen_identity_runtime', 'rule_initial_operator', 'full_self_cross_evaluator',
    'independent_weight_controls', 'complete_prescribed_searches',
    'selected_direct_confirmation_moments', 'complete_work_accounting', 'final_identity_preservation')
ACCEPTED = {'ordinary_current_state_evaluator_and_first_steps_qualified', 'qualified_no_positive_startup'}


def identity(path):
    path = Path(path)
    if path.suffix.lower() in {'.npz', '.npy'}:
        raise ValueError('T70 must not open/hash raw arrays')
    digest, size = hashlib.sha256(), 0
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
            size += len(block)
    return dict(bytes=size, sha256=digest.hexdigest())


def read_json(path):
    def reject(value):
        raise ValueError('nonfinite JSON token: ' + value)
    return json.loads(path.read_bytes(), parse_constant=reject)


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def nonnegative_number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def close(actual, expected, score=False):
    assert type(actual) in (int, float) and type(expected) in (int, float)
    assert math.isfinite(actual) and math.isfinite(expected)
    tolerance = 1e-8 if score else 1e-10 + 1e-9 * max(abs(actual), abs(expected))
    assert abs(actual - expected) <= tolerance, (actual, expected, tolerance)


def finite_tree(value):
    if type(value) is float:
        assert math.isfinite(value)
    elif isinstance(value, dict):
        for item in value.values():
            finite_tree(item)
    elif isinstance(value, list):
        for item in value:
            finite_tree(item)


def counter_keys(name):
    tree = ast.parse((HERE / name).read_text(encoding='utf-8'))
    found = [node for node in tree.body if isinstance(node, ast.Assign) and
        any(isinstance(target, ast.Name) and target.id == 'COUNTER_KEYS' for target in node.targets)]
    assert len(found) == 1
    keys = ast.literal_eval(found[0].value)
    assert isinstance(keys, tuple) and len(keys) == len(set(keys))
    return keys


def pair_key(pair):
    return tuple((g[2], g[0], g[1]) for g in pair)


def rank(record):
    return (-record['J'], pair_key(record['geometry']), record['eta'])


def validate_weights(weights):
    assert weights['exact_real_inner_optimality_certified'] is False
    assert type(weights['floating_point_classification_unresolved']) is bool
    candidates = weights['candidates']
    assert 2 <= len(candidates) <= 4 and weights['attempts'] == len(candidates)
    assert [x['eta'] for x in candidates] == sorted({x['eta'] for x in candidates})
    assert candidates[0]['eta'] == 0 and candidates[-1]['eta'] == 1
    assert weights['candidate_proposals'] == len(candidates) + weights['duplicate_candidates'] <= 4
    coefficients = weights['coefficients']
    for candidate in candidates:
        eta = candidate['eta']
        assert 0 <= eta <= 1 and candidate['sources']
        B = math.fsum(((1 - eta) * coefficients['b1'], eta * coefficients['b2']))
        M = math.fsum(((1 - eta)**2 * coefficients['M11'],
            2 * eta * (1 - eta) * coefficients['M12'], eta**2 * coefficients['M22']))
        assert M > 0
        close(candidate['B'], B); close(candidate['M'], M)
        scale = max(0.0, B) / M
        close(candidate['Gamma'], scale); close(candidate['J'], max(0.0, B) * scale)
        assert candidate['positive_scale'] is (candidate['Gamma'] > 0)
    assert weights['selected'] == min(candidates, key=lambda x: (-x['J'], x['eta']))


def validate_search(step, events, keys):
    assert step['schema'] == 't70-causal-projection-search-v1'
    local, summary = step['counters'], step['summary']
    assert set(local) == set(keys) and all(type(x) is int and x >= 0 for x in local.values())
    initial = dict(Gamma=1.5 * math.sqrt(2 * math.pi), eta=0.0, geometry=[[1.0, 1.0, 0.0]] * 2)
    assert step['current_state'] == step['original_state'] == initial
    assert step['active_components'] == [dict(geometry=[1.0, 1.0, 0.0], weight=1.0)]
    assert step['search_scales'] == dict(a=0.0, R=1.0, Z=1.0)
    assert step['search_bounds'] == [[.5, 1.5], [.5, 1.5], [-1.5, 1.5]]
    bank = sorted([[sr, sz, z] for sr in (.75, 1.0, 1.25) for sz in (.75, 1.0, 1.25)
        for z in (-1.0, -.5, 0.0, .5, 1.0)], key=lambda g: (g[2], g[0], g[1]))
    assert step['bank'] == bank and len(step['bank_sources']) == 45
    assert events[0]['kind'] == 'search_started' and events[-1]['kind'] == 'search_completed'
    assert events[0]['h'] == step['h'] and events[0]['current_state'] == initial
    assert events[-1]['selected_state'] == step['selected_state']
    assert events[-1]['summary'] == summary and events[-1]['counters'] == local
    proposals = [x for x in events if x['kind'] in
        {'search_pair_evaluated', 'search_pair_cache_hit', 'search_proposal_rejected'}]
    assert [x['proposal_index'] for x in proposals] == list(range(local['search_proposals']))
    evaluated = [x for x in proposals if x['kind'] == 'search_pair_evaluated']
    records = [x['record'] for x in evaluated]
    assert [x['evaluation_index'] for x in records] == list(range(len(records)))
    assert len(records) == local['search_pair_evaluations']
    assert len({pair_key(x['geometry']) for x in records}) == len(records)
    assert sum(x['kind'] == 'search_pair_cache_hit' for x in proposals) == local['search_pair_cache_hits']
    assert sum(x['kind'] == 'search_proposal_rejected' for x in proposals) == local['search_rejected_proposals']
    assert local['search_proposals'] == sum(local[k] for k in
        ('search_pair_evaluations', 'search_pair_cache_hits', 'search_rejected_proposals'))
    assert local['search_proposals'] == 1035 + local['search_neighbor_proposals'] <= 2280
    assert local['search_initial_proposals'] == 1035 and local['search_neighbor_proposals'] <= 1152
    bank_proposals = [x for x in proposals if x['source']['phase'] == 'bank']
    expected_pairs = [(i, j) for i in range(45) for j in range(i, 45)]
    assert len(bank_proposals) == 1035
    for packet, (i, j) in zip(bank_proposals, expected_pairs):
        assert packet['source'] == dict(phase='bank', i=i, j=j)
        assert packet['geometry'] == [bank[i], bank[j]] and packet['kind'] == 'search_pair_evaluated'
    for record in records:
        assert pair_key(record['geometry']) == tuple(sorted(pair_key(record['geometry'])))
        assert all(.5 <= g[0] <= 1.5 and .5 <= g[1] <= 1.5 and -1.5 <= g[2] <= 1.5 for g in record['geometry'])
        validate_weights(record['weights'])
        for name in ('eta', 'Gamma', 'B', 'M', 'J', 'positive_scale'):
            assert record[name] == record['weights']['selected'][name]
    for packet in proposals:
        if packet['kind'] == 'search_pair_cache_hit':
            assert packet['geometry'] == records[packet['evaluation_index']]['geometry']
    basis = [x for x in events if x['kind'] == 'search_component_basis']
    assert len(basis) == local['search_component_evaluations'] <= 1199
    assert len({tuple(x['geometry']) for x in basis}) == len(basis)
    assert local['search_cross_calls'] == local['search_current_gram_calls'] == len(basis)
    assert local['search_component_requests'] == 2 * (len(records) + 1)
    assert local['search_component_cache_hits'] == local['search_component_requests'] - len(basis)
    assert local['search_candidate_gram_calls'] == 3 * (len(records) + 1)
    for packet in basis:
        assert len(packet['current_gram_terms']) == len(packet['physics_cross']['ordered_pairs']) == 1
        close(packet['F_cross'], packet['physics_cross']['total'])
        close(packet['b'], math.fsum((packet['q_cross'], step['h'] * packet['F_cross'])))
    assert local['search_weight_attempts'] == sum(x['weights']['attempts'] for x in records)
    assert local['search_weight_candidates_before_dedup'] == sum(x['weights']['candidate_proposals'] for x in records)
    assert local['search_duplicate_weight_candidates'] == sum(x['weights']['duplicate_candidates'] for x in records)
    assert local['search_inner_unresolved_pairs'] == sum(x['weights']['floating_point_classification_unresolved'] for x in records)
    assert local['search_control_attempts'] == local['search_invocations'] == 1
    assert local['search_weight_attempts'] + 1 <= 9121
    controls = [x for x in events if x['kind'] == 'search_unchanged_control']
    assert len(controls) == 1
    assert {k: v for k, v in controls[0].items() if k not in ('kind', 'elapsed_seconds')} == step['control']
    control = step['control']
    assert control['original_state'] == control['current_state'] == initial
    assert control['original_Gamma'] == control['Gamma'] == initial['Gamma']
    assert control['original_eta'] == control['eta'] == 0 and control['scale_refitted'] is False
    close(control['J'], math.fsum((2 * control['Gamma'] * control['B'], -control['Gamma']**2 * control['M'])))
    starts = sorted([x for x in records[:1035] if x['positive_scale']], key=rank)[:4]
    assert step['start_indices'] == [x['evaluation_index'] for x in starts]
    polls = step['polls']
    journal_polls = [{k: v for k, v in x.items() if k not in ('kind', 'elapsed_seconds')}
        for x in events if x['kind'] == 'search_poll_completed']
    assert journal_polls == polls and local['search_poll_count'] == len(polls)
    assert local['search_neighbor_proposals'] == 12 * len(polls)
    assert local['search_strict_moves'] == sum(x['improved'] for x in polls)
    position = 0
    for si, start in enumerate(starts):
        center = start
        for level, delta in enumerate(((.1, .1, .2), (.05, .05, .1), (.025, .025, .05))):
            for poll_index in range(8):
                packet = polls[position]; position += 1
                assert (packet['start'], packet['level'], packet['poll']) == (si, level, poll_index)
                assert packet['center_before'] == center['evaluation_index'] and packet['steps'] == list(delta)
                neighbors = [x for x in proposals if x['source'].get('phase') == 'neighbor' and
                    (x['source']['start'], x['source']['level'], x['source']['poll']) == (si, level, poll_index)]
                assert len(neighbors) == 12
                improvements = []
                traversal = [(component, coordinate, direction) for component in range(2)
                    for coordinate in range(3) for direction in (-1, 1)]
                for neighbor, (component, coordinate, direction) in zip(neighbors, traversal):
                    source = neighbor['source']
                    assert (source['component'], source['coordinate'], source['direction']) == (component, coordinate, direction)
                    assert source['center'] == center['evaluation_index']
                    geometry = [list(g) for g in center['geometry']]
                    geometry[component][coordinate] += direction * delta[coordinate]
                    geometry.sort(key=lambda g: (g[2], g[0], g[1]))
                    assert neighbor['geometry'] == geometry
                    inside = all(.5 <= g[0] <= 1.5 and .5 <= g[1] <= 1.5 and -1.5 <= g[2] <= 1.5 for g in geometry)
                    assert (neighbor['kind'] != 'search_proposal_rejected') is inside
                    if inside:
                        record = neighbor['record'] if neighbor['kind'] == 'search_pair_evaluated' else records[neighbor['evaluation_index']]
                        if record['positive_scale'] and record['J'] > center['J']:
                            improvements.append(record)
                best = min(improvements, key=rank) if improvements else center
                assert packet['center_after'] == best['evaluation_index'] and packet['improved'] is bool(improvements)
                center = best
                if not improvements:
                    break
    assert position == len(polls)
    eligible = sorted([x for x in records if x['positive_scale']], key=rank)
    selected = eligible[0] if eligible else None
    assert step['selected_record'] == selected
    assert step['selected_state'] == (None if selected is None else
        dict(Gamma=selected['Gamma'], eta=selected['eta'], geometry=selected['geometry']))
    assert step['status'] == ('no_positive_candidate' if selected is None else 'completed_bounded_search')
    assert summary['scheduled_search_completed'] is True and summary['early_success_shortcut'] is False
    assert summary['global_geometry_optimality_certified'] is summary['exact_real_inner_optimality_certified'] is False
    assert summary['bank_size'] == 45 and summary['bank_proposals'] == 1035
    assert summary['evaluated_pairs'] == len(records) and summary['eligible_pairs'] == len(eligible)
    assert summary['floating_point_unresolved_pairs'] == local['search_inner_unresolved_pairs']
    if selected is not None:
        assert selected['J'] + 1e-10 + 1e-9 * max(abs(selected['J']), abs(control['J'])) >= control['J']


def validate_result(result, manifest, receipt, manifest_path):
    finite_tree(result)
    assert result['numerical_qualified'] is True and result['inputs_preserved'] is True
    assert result['runtime']['python'] == manifest['expected_python'] and result['runtime']['numpy'] == manifest['expected_numpy']
    assert Path(result['runtime']['executable']).resolve() == Path(manifest['executable']['path']).resolve()
    checks = result['checks']
    assert len(checks) == 8 and [x['name'] for x in checks] == list(CHECKS)
    assert all(type(x['passed']) is bool and x['passed'] and isinstance(x['details'], dict) for x in checks)
    for key in ('full_task_validated', 'new_method_claim', 'formal_error_certificate',
                'global_geometry_optimality_certified', 'exact_real_inner_optimality_certified'):
        assert result[key] is False
    assert result['new_flow_trajectories'] == result['reference_arrays_loaded'] == 0
    assert result['selected_tuples_unchanged_during_confirmation'] is True
    assert result['prior_scientific_child_seconds'] == PRIOR
    assert nonnegative_number(result['child_elapsed_before_result_write_seconds'])
    assert result['child_elapsed_before_result_write_seconds'] <= receipt['scientific_child_supervised_seconds']
    admitted = {(REPO / x['path']).resolve(): {k: x[k] for k in ('bytes', 'sha256')} for x in manifest['inputs']}
    admitted[Path(manifest['executable']['path']).resolve()] = receipt['executable_identity']
    admitted[manifest_path] = receipt['input_manifest_identity']
    observed = {(REPO / x['path']).resolve(): {k: x[k] for k in ('bytes', 'sha256')} for x in result['input_identities']}
    assert len(observed) == len(result['input_identities']) and observed == admitted
    c = result['counters']
    assert c and all(type(x) is int and x >= 0 for x in c.values())
    assert c['input_arrays_read'] == c['input_arrays_saved'] == 0
    assert c['root_input_files_hashed_before'] == c['root_input_files_hashed_after'] == len(admitted)
    assert c['root_input_bytes_hashed_before'] == c['root_input_bytes_hashed_after'] == sum(x['bytes'] for x in admitted.values())
    for key, value in manifest['fixed_work'].items():
        assert c[key] == value, key
    for key, cap in manifest['total_work_caps'].items():
        assert c[key] <= cap, key
    for key in counter_keys('physics.py'):
        assert key in c
    details = result['details']
    assert [x['order'] for x in details['rules']] == manifest['expected_rule_orders']
    for rule in details['rules']:
        assert abs(rule['weight_sum'] - 2) <= 1e-12
        assert 0 <= rule['node_symmetry'] <= 1e-12 and 0 <= rule['weight_symmetry'] <= 1e-12
    controls = details['scalar_controls']
    names = ['identical_positive', 'identical_negative', 'identical_zero', 'first_component',
        'second_component', 'interior_mixture', 'signed_difference']
    assert [x['name'] for x in controls] == names
    for packet in controls:
        validate_weights(packet['solver'])
        chosen = packet['solver']['selected']
        actual = [chosen['Gamma'] * (1 - chosen['eta']), chosen['Gamma'] * chosen['eta']]
        assert packet['actual_coefficients'] == actual
        for value, expected in zip(actual, packet['expected_coefficients']):
            close(value, expected)
        if packet['name'].startswith('identical'):
            close(chosen['eta'], 0)
    assert c['root_scalar_control_weight_attempts'] == sum(x['solver']['attempts'] for x in controls) <= 28
    assert len(details['initial_calibration']) == 12
    t54 = read_json(REPO / manifest['scientific_input_paths'][0])['closed_metrics']
    for packet in details['initial_calibration']:
        close(packet['c'], 1.5 * t54['beta_best_over_g0'], score=True)
        close(packet['E_best'], t54['E_best'], score=True)
    steps = result['steps']
    assert len(steps) == 2 and [x['h'] for x in steps] == manifest['step_sizes']
    positive = sum(x['selected_state'] is not None for x in steps)
    assert result['verdict'] == ('ordinary_current_state_evaluator_and_first_steps_qualified'
        if positive == 2 else 'qualified_no_positive_startup')
    keys = counter_keys('search.py')
    for key in keys:
        assert c.get(key, 0) == sum(x['counters'][key] for x in steps)
    expected = dict(phys_instances=1, phys_rule_transforms=3, phys_rule_nodes_transformed=448,
        search_invocations=2, root_confirmation_routes=24, root_spatial_grids=4, root_spatial_grid_points=53248,
        phys_cross_calls=c['search_cross_calls'] + 24 + 6 * positive,
        phys_cross_ordered_pair_integrals=c['search_cross_calls'] + 51 + 6 * positive,
        phys_cross_integrand_points=c['search_cross_calls'] * 128 + (17 + 2 * positive) * 448,
        phys_moment_calls=4 + positive,
        phys_gram_calls=c['search_current_gram_calls'] + c['search_candidate_gram_calls'] + 36 + 5 * positive,
        root_gaussian_component_calls=44 + 8 * positive,
        root_gaussian_component_points=(11 + 2 * positive) * 53248,
        root_direct_reductions=612 + 60 * positive,
        root_direct_reduction_points=(87 + 66 + 15 * positive) * 53248)
    for key, value in expected.items():
        assert c[key] == value, (key, c.get(key), value)
    assert c['root_exp_evaluations'] == c['root_gaussian_component_points']
    assert c['root_array_exp_calls'] == c['root_gaussian_component_calls']
    assert c['phys_peak_spatial_points'] <= 18432
    events = []
    with (HERE / 'local/journal.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            packet = json.loads(line)
            finite_tree(packet)
            assert isinstance(packet['kind'], str) and nonnegative_number(packet['elapsed_seconds'])
            if events:
                assert packet['elapsed_seconds'] >= events[-1]['elapsed_seconds']
            events.append(packet)
    assert len(events) == c['root_journal_events'] and events[-1]['kind'] == 'phase_finished'
    phases = ['identity_runtime', 'rules_and_point_controls', 'direct_evaluator_controls',
        'independent_weight_controls', 'two_independent_searches', 'unchanged_selected_confirmation',
        'work_accounting', 'identity_preservation']
    assert [x['name'] for x in events if x['kind'] == 'phase_started'] == phases
    finished = [x for x in events if x['kind'] == 'phase_finished']
    assert [x['name'] for x in finished] == phases and set(result['phases_seconds']) == set(phases)
    for packet in finished:
        assert packet['seconds'] == result['phases_seconds'][packet['name']] and nonnegative_number(packet['seconds'])
    qualifications = [{k: v for k, v in x.items() if k not in ('kind', 'elapsed_seconds')}
        for x in events if x['kind'] == 'qualification']
    assert qualifications == checks
    for kind, count in dict(rule_constructed=5, evaluator_cross=18, field_control=24,
            scalar_control=7, confirmation_route=24, search_started=2, search_completed=2).items():
        assert sum(x['kind'] == kind for x in events) == count, kind
    starts = [i for i, x in enumerate(events) if x['kind'] == 'search_started']
    ends = [i for i, x in enumerate(events) if x['kind'] == 'search_completed']
    assert starts[0] < ends[0] < starts[1] < ends[1]
    for step, begin, end in zip(steps, starts, ends):
        validate_search(step, events[begin:end + 1], keys)
        confirmation = step['confirmation']
        models = {'unchanged', 'translation'} | ({'selected'} if step['selected_state'] is not None else set())
        routes = confirmation['routes']
        expected_routes = {(grid, order) for grid in ('D8-64x128', 'D8-96x192', 'D12-64x128', 'D12-96x192')
            for order in (64, 128, 256)}
        assert len(routes) == 12 and {(x['grid'], x['heat_order']) for x in routes} == expected_routes
        primary = next(x for x in routes if x['grid'] == 'D12-64x128' and x['heat_order'] == 128)
        assert confirmation['primary'] == primary
        logged = [{k: v for k, v in x.items() if k not in ('kind', 'elapsed_seconds', 'h')}
            for x in events if x['kind'] == 'confirmation_route' and x['h'] == step['h']]
        assert logged == routes
        for route in routes:
            assert route['C'] > 0 and set(route['models']) == models
            for name, packet in route['models'].items():
                assert packet['N'] >= 0 and packet['subtraction'] >= 0
                close(packet['subtraction'], route['C'] - packet['J'])
                close(packet['N'], packet['subtraction'])
                close(packet['relative_error'], math.sqrt(packet['N'] / route['C']), score=True)
                close(packet['relative_error'], primary['models'][name]['relative_error'], score=True)
            close(route['models']['unchanged']['J'], step['control']['J'])
            if 'selected' in models:
                close(route['models']['selected']['J'], step['selected_record']['J'])
                close(route['models']['unchanged']['N'] - route['models']['selected']['N'],
                    route['models']['selected']['J'] - route['models']['unchanged']['J'])
        assert set(confirmation['moments']) == models
        for name, moment in confirmation['moments'].items():
            assert moment['Gamma'] > 0 and moment['I_z'] > 0
            for i in range(2):
                close(moment['between']['centroid'][i], moment['raw']['centroid'][i])
                for j in range(2):
                    close(moment['between']['covariance'][i][j], moment['raw']['covariance'][i][j])
            cov = moment['between']['covariance']
            assert cov[0][0] > 0 and cov[1][1] > 0 and cov[0][0] * cov[1][1] - cov[0][1]**2 > 0
        if 'selected' in models:
            assert confirmation['components_distinct'] is (step['selected_state']['geometry'][0] != step['selected_state']['geometry'][1])
            assert confirmation['selected_improves_unchanged'] is (primary['models']['selected']['N'] < primary['models']['unchanged']['N'])
            assert confirmation['selected_improves_translation'] is (primary['models']['selected']['N'] < primary['models']['translation']['N'])
        else:
            assert confirmation['selected_cross'] is None
            assert all(confirmation[k] is None for k in
                ('components_distinct', 'selected_improves_unchanged', 'selected_improves_translation'))
    receipt['saved_result_validation'] = dict(check_count=8, step_count=2, journal_events=len(events),
        positive_startups=positive, mathematical_reexecution=False, scalar_readback=True,
        raw_arrays_read=0, source_imports=0, full_task_validated=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, default=HERE / 'input-manifest.json')
    args = parser.parse_args()
    started = time.perf_counter()
    manifest_path = args.manifest.resolve()
    assert manifest_path == HERE / 'input-manifest.json'
    manifest = read_json(manifest_path)
    assert manifest['schema'] == 't70-causal-projector-freeze-v1'
    assert manifest['maximum_scientific_child_invocations'] == 1
    assert manifest['child_timeout_seconds'] == LIMIT and manifest['observed_peak_working_set_limit_bytes'] == CAP
    assert manifest['required_available_physical_bytes'] == REQUIRED and manifest['memory_sample_interval_seconds'] == INTERVAL
    assert manifest['expected_python'] == '3.12.14' and manifest['expected_numpy'] == '2.3.5'
    assert manifest['expected_rule_orders'] == [64, 96, 128, 192, 256]
    assert manifest['expected_rule_nodes'] == 736 and manifest['expected_rule_eigh_calls'] == 5
    assert manifest['heat_orders'] == [64, 128, 256] and manifest['step_sizes'] == [.0625, .03125]
    assert manifest['expected_check_names'] == list(CHECKS)
    assert manifest['prior_scientific_child_seconds'] == PRIOR
    inputs = manifest['inputs']
    assert len(inputs) == len({x['path'] for x in inputs}) == 18
    for item in inputs:
        path = Path(item['path'])
        assert not path.is_absolute() and '..' not in path.parts
        assert path.suffix.lower() not in {'.npz', '.npy'}
        assert identity(REPO / path) == {k: item[k] for k in ('bytes', 'sha256')}
    exe = Path(manifest['executable']['path'])
    assert identity(exe) == {k: manifest['executable'][k] for k in ('bytes', 'sha256')}
    memory_record = next(x for x in inputs if (REPO / x['path']).resolve() == MEMORY)
    assert identity(MEMORY) == {k: memory_record[k] for k in ('bytes', 'sha256')}
    local = HERE / 'local'
    local.mkdir(exist_ok=True)
    for name in ('execution-started.json', 'result.json', 'journal.jsonl', 'failure.json',
                 'stdout.txt', 'stderr.txt', 'memory.jsonl'):
        assert not (local / name).exists(), name
    assert not (HERE / 'execution.json').exists()
    preflight = read_json(HERE / 'preflight.json')
    assert preflight['schema'] == 't70-os-preflight-v1' and preflight['passed'] is True
    assert preflight['source'] == identity(MEMORY)
    spec = importlib.util.spec_from_file_location('t70_memory_supervisor', MEMORY)
    observer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(observer)
    command = [str(exe), '-I', '-B', '-u', '-X', 'utf8', str(HERE / 'measure.py'), '--manifest', str(manifest_path)]
    overrides = {k: '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')}
    environment = dict(os.environ)
    environment.update(overrides)
    receipt = dict(schema='t70-causal-projector-execution-v1', started_utc=now(), command=command, cwd=str(REPO),
        child_timeout_seconds=LIMIT, observed_peak_working_set_limit_bytes=CAP,
        required_available_physical_bytes=REQUIRED, memory_sample_interval_seconds=INTERVAL,
        thread_environment_overrides=overrides, scientific_child_invocations=0,
        new_scientific_trajectories=0, complete_result_validated=False, numerical_qualified=False,
        verdict=None, prior_scientific_child_seconds=PRIOR, T61_qualification_seconds=.9663960000034422,
        prior_scientific_series_scope=manifest['prior_scientific_series_scope'], scientific_series_is_total_project_cost=False,
        input_manifest_identity=identity(manifest_path), supervisor_identity=identity(Path(__file__)),
        worker_identity=identity(HERE / 'measure.py'), physics_identity=identity(HERE / 'physics.py'),
        search_identity=identity(HERE / 'search.py'), memory_observer_identity=identity(MEMORY), executable_identity=identity(exe),
        memory_samples=0, peak_observed_working_set_bytes=0, max_observed_private_bytes=0,
        max_observed_peak_pagefile_bytes=0, T60_history_reclassified=False)
    receipt['launch_memory'] = observer.host_memory()
    write(local / 'execution-started.json', receipt)
    child, handle, begin = None, None, None
    with (local / 'stdout.txt').open('xb') as stdout, (local / 'stderr.txt').open('xb') as stderr, \
            (local / 'memory.jsonl').open('x', encoding='utf-8', newline='\n') as memory_log:
        def sample(final=False):
            values = observer.process_memory(handle)
            elapsed = time.perf_counter() - begin
            memory_log.write(json.dumps(dict(elapsed_seconds=elapsed, final=final, **values), allow_nan=False) + '\n')
            memory_log.flush()
            receipt['memory_samples'] += 1
            receipt['peak_observed_working_set_bytes'] = max(receipt['peak_observed_working_set_bytes'], values['peak_working_set_bytes'])
            receipt['max_observed_private_bytes'] = max(receipt['max_observed_private_bytes'], values['private_usage_bytes'])
            receipt['max_observed_peak_pagefile_bytes'] = max(receipt['max_observed_peak_pagefile_bytes'], values['peak_pagefile_usage_bytes'])
            receipt['last_memory_sample_elapsed_seconds'] = elapsed
            return values['peak_working_set_bytes'] <= CAP
        if receipt['launch_memory']['available_physical_bytes'] < REQUIRED:
            receipt['status'] = 'insufficient_launch_memory_no_invocation'
        else:
            begin = time.perf_counter()
            receipt['scientific_child_invocations'] = 1
            try:
                child = subprocess.Popen(command, cwd=REPO, env=environment, stdout=stdout, stderr=stderr,
                    creationflags=subprocess.CREATE_NO_WINDOW)
                receipt['child_pid'] = child.pid
                handle = observer.open_process(child.pid)
                while True:
                    code = child.poll()
                    if code is not None:
                        receipt.update(returncode=code, status='exited_pending_readback')
                        try:
                            if not sample(final=True):
                                receipt['status'] = 'memory_limit_no_retry'
                        except Exception as exc:
                            receipt['final_memory_query_unavailable'] = repr(exc)
                        break
                    if time.perf_counter() - begin >= LIMIT:
                        receipt['status'] = 'timeout_no_retry'
                        break
                    try:
                        if not sample():
                            receipt['status'] = 'memory_limit_no_retry'
                            break
                    except Exception as exc:
                        if child.poll() is not None:
                            receipt.update(returncode=child.returncode, status='exited_pending_readback',
                                final_memory_query_unavailable=repr(exc))
                        else:
                            receipt.update(status='live_memory_observer_error_no_retry', observer_error=repr(exc))
                        break
                    try:
                        child.wait(timeout=min(INTERVAL, max(.001, LIMIT - (time.perf_counter() - begin))))
                    except subprocess.TimeoutExpired:
                        pass
            except Exception as exc:
                receipt.update(status='launch_or_observer_setup_error_no_retry', error=repr(exc))
            finally:
                if child is not None:
                    if child.poll() is None:
                        try:
                            child.kill()
                        except Exception as exc:
                            receipt['termination_error'] = repr(exc)
                    try:
                        receipt['returncode'] = child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        receipt.update(status='termination_failed_requires_cleanup', child_still_live=True)
                if handle is not None:
                    observer.kernel.CloseHandle(handle)
    receipt['scientific_child_supervised_seconds'] = time.perf_counter() - begin if begin is not None else 0.0
    receipt['cumulative_scientific_child_seconds'] = PRIOR + receipt['scientific_child_supervised_seconds']
    receipt['child_still_live'] = child is not None and child.poll() is None
    receipt['inputs_unchanged'] = all(identity(REPO / x['path']) == {k: x[k] for k in ('bytes', 'sha256')} for x in inputs)
    receipt['input_manifest_unchanged'] = identity(manifest_path) == receipt['input_manifest_identity']
    receipt['executable_unchanged'] = identity(exe) == receipt['executable_identity']
    receipt['logs'] = [dict(path='local/' + name, **identity(local / name))
        for name in ('stdout.txt', 'stderr.txt', 'memory.jsonl')]
    receipt['partial_artifacts'] = [dict(path='local/' + name, **identity(local / name))
        for name in ('journal.jsonl', 'failure.json') if (local / name).exists()]
    receipt['forbidden_array_outputs'] = [x.relative_to(HERE).as_posix() for x in local.rglob('*')
        if x.is_file() and x.suffix.lower() in {'.npz', '.npy'}]
    receipt['worker_failure_exists'] = (local / 'failure.json').exists()
    if receipt['worker_failure_exists'] and receipt['status'] == 'exited_pending_readback':
        receipt['status'] = 'worker_failure_no_retry'
    receipt['result_exists'] = (local / 'result.json').exists()
    if receipt['result_exists']:
        receipt['result_identity'] = identity(local / 'result.json')
        try:
            result = read_json(local / 'result.json')
            assert result['schema'] == 't70-causal-projector-result-v1'
            assert result['verdict'] in ACCEPTED | {'failed_qualification_no_retry'}
            receipt['retained_worker_verdict'] = result['verdict']
            if receipt['status'] == 'exited_pending_readback':
                if result['verdict'] == 'failed_qualification_no_retry':
                    assert result['numerical_qualified'] is False
                    receipt['status'] = 'failed_qualification_no_retry'
                else:
                    assert receipt['returncode'] == 0 and not receipt['child_still_live']
                    assert receipt['scientific_child_supervised_seconds'] <= LIMIT
                    assert receipt['memory_samples'] > 0 and receipt['peak_observed_working_set_bytes'] <= CAP
                    assert not receipt['worker_failure_exists'] and not receipt['forbidden_array_outputs']
                    assert all(receipt[k] for k in ('inputs_unchanged', 'input_manifest_unchanged', 'executable_unchanged'))
                    validate_result(result, manifest, receipt, manifest_path)
                    receipt.update(status='completed_' + result['verdict'], complete_result_validated=True,
                        numerical_qualified=True, verdict=result['verdict'])
        except Exception as exc:
            receipt['result_read_error'] = repr(exc)
            if receipt['status'] == 'exited_pending_readback':
                receipt['status'] = 'failed_result_validation_no_retry'
    elif receipt['status'] == 'exited_pending_readback':
        receipt['status'] = 'missing_result_no_retry'
    if not all(receipt[k] for k in ('inputs_unchanged', 'input_manifest_unchanged', 'executable_unchanged')):
        receipt.update(status='failed_preservation_no_retry', complete_result_validated=False,
            numerical_qualified=False, verdict=None)
    if receipt['forbidden_array_outputs']:
        receipt.update(status='forbidden_array_output_no_retry', complete_result_validated=False,
            numerical_qualified=False, verdict=None)
    receipt['supervisor_elapsed_before_receipt_write_seconds'] = time.perf_counter() - started
    receipt['finished_utc'] = now()
    write(HERE / 'execution.json', receipt)
    print(json.dumps({k: receipt[k] for k in ('status', 'scientific_child_invocations',
        'scientific_child_supervised_seconds', 'verdict', 'peak_observed_working_set_bytes', 'inputs_unchanged')}, indent=2))
    return 0 if receipt['complete_result_validated'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
