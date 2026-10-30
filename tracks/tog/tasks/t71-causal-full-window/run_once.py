"""One T71 scientific child, observed OS resources and saved-result readback; stdlib only."""
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
PRIOR = 1991.4691072998103
LIMIT, CAP, REQUIRED, INTERVAL = 120.0, 536870912, 1073741824, .25
CHECKS = ('frozen_identity_runtime', 'rules_and_startup_regression',
    'complete_causal_paths_and_counts', 'path_and_checkpoint_evaluator',
    'reference_eligibility_and_score_integration', 'time_comparison_integration_and_moments',
    'complete_work_accounting', 'final_identity_preservation')
ACCEPTED = {'ordinary_full_window_joint_pass', 'ordinary_full_window_joint_miss',
    'time_or_reference_sensitive_inconclusive'}
BASE = HERE.parent / 't70-causal-projector-qualification'


def identity(path):
    path = Path(path)
    if path.suffix.lower() in {'.npz', '.npy'}:
        raise ValueError('T71 must not open/hash raw arrays')
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
    tree = ast.parse((BASE / name).read_text(encoding='utf-8'))
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
    # Reconstruct saved scalar traversal only; no Gram/field/optimizer invocation.
    assert step['schema'] == 't70-causal-projection-search-v1'
    local, summary = step['counters'], step['summary']
    assert set(local) == set(keys) and all(type(x) is int and x >= 0 for x in local.values())
    initial = step['original_state']
    validate_state(initial)
    active = [(tuple(initial['geometry'][0]),1-initial['eta']),
              (tuple(initial['geometry'][1]),initial['eta'])]
    active = [(g,w) for g,w in active if w>0]
    if len(active)==2 and active[0][0]==active[1][0]: active=[(active[0][0],1.0)]
    active.sort(key=lambda x:(x[0][2],x[0][0],x[0][1]))
    current=dict(Gamma=initial['Gamma'],eta=0.0 if len(active)==1 else active[1][1],
        geometry=[list(active[0][0]),list(active[-1][0])])
    assert step['current_state']==current
    assert step['active_components']==[dict(geometry=list(g),weight=w) for g,w in active]
    a=math.fsum(w*g[2] for g,w in active)
    R=math.sqrt(math.fsum(w*g[0]*g[0] for g,w in active))
    Z=math.sqrt(math.fsum(w*(g[1]*g[1]+(g[2]-a)**2) for g,w in active))
    assert step['search_scales']==dict(a=a,R=R,Z=Z)
    bounds=[[min(.5*R,min(g[0] for g,w in active)),max(1.5*R,max(g[0] for g,w in active))],
        [min(.5*Z,min(g[1] for g,w in active)),max(1.5*Z,max(g[1] for g,w in active))],
        [min(a-1.5*Z,min(g[2] for g,w in active)),max(a+1.5*Z,max(g[2] for g,w in active))]]
    assert step['search_bounds']==bounds
    sources={}
    for sr in (.75,1.,1.25):
        for sz in (.75,1.,1.25):
            for z in (-1.,-.5,0.,.5,1.): sources.setdefault((sr*R,sz*Z,a+z*Z),[]).append('relative_bank')
    for i,(g,w) in enumerate(active): sources.setdefault(g,[]).append('active_'+str(i))
    bank=[list(g) for g in sorted(sources,key=lambda g:(g[2],g[0],g[1]))]
    bank_count=len(bank); pair_count=bank_count*(bank_count+1)//2
    assert 45<=bank_count<=47 and step['bank']==bank
    assert step['bank_sources']==[sources[tuple(g)] for g in bank]
    assert events[0]['kind'] == 'search_started' and events[-1]['kind'] == 'search_completed'
    assert events[0]['h'] == step['h'] and events[0]['current_state'] == current and events[0]['original_state'] == initial
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
    assert local['search_proposals'] == pair_count + local['search_neighbor_proposals'] <= 2280
    assert local['search_initial_proposals'] == pair_count and local['search_neighbor_proposals'] <= 1152
    bank_proposals = [x for x in proposals if x['source']['phase'] == 'bank']
    expected_pairs = [(i, j) for i in range(bank_count) for j in range(i, bank_count)]
    assert len(bank_proposals) == pair_count
    for packet, (i, j) in zip(bank_proposals, expected_pairs):
        assert packet['source'] == dict(phase='bank', i=i, j=j)
        assert packet['geometry'] == [bank[i], bank[j]] and packet['kind'] == 'search_pair_evaluated'
    for record in records:
        assert pair_key(record['geometry']) == tuple(sorted(pair_key(record['geometry'])))
        assert all(bounds[k][0]<=g[k]<=bounds[k][1] for g in record['geometry'] for k in range(3))
        validate_weights(record['weights'])
        for name in ('eta', 'Gamma', 'B', 'M', 'J', 'positive_scale'):
            assert record[name] == record['weights']['selected'][name]
    for packet in proposals:
        if packet['kind'] == 'search_pair_cache_hit':
            assert packet['geometry'] == records[packet['evaluation_index']]['geometry']
    basis = [x for x in events if x['kind'] == 'search_component_basis']
    assert len(basis) == local['search_component_evaluations'] <= 1199
    assert len({tuple(x['geometry']) for x in basis}) == len(basis)
    assert local['search_cross_calls'] == len(basis) and local['search_current_gram_calls']==len(active)*len(basis)
    assert local['search_component_requests'] == 2 * (len(records) + 1)
    assert local['search_component_cache_hits'] == local['search_component_requests'] - len(basis)
    assert local['search_candidate_gram_calls'] == 3 * (len(records) + 1)
    for packet in basis:
        assert len(packet['current_gram_terms']) == len(active)
        assert len(packet['physics_cross']['ordered_pairs']) == len(active)**2
        close(packet['q_cross'],initial['Gamma']*math.fsum(t['weight']*t['gram'] for t in packet['current_gram_terms']))
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
    assert {k: v for k, v in controls[0].items() if k not in ('kind', 'elapsed_seconds', 'journal_elapsed_seconds')} == step['control']
    control = step['control']
    assert control['original_state'] == initial and control['current_state']==current
    assert control['original_Gamma'] == control['Gamma'] == initial['Gamma']
    assert control['original_eta'] == initial['eta'] and control['eta'] == current['eta'] and control['scale_refitted'] is False
    close(control['J'], math.fsum((2 * control['Gamma'] * control['B'], -control['Gamma']**2 * control['M'])))
    starts = sorted([x for x in records[:pair_count] if x['positive_scale']], key=rank)[:4]
    assert step['start_indices'] == [x['evaluation_index'] for x in starts]
    polls = step['polls']
    journal_polls = [{k: v for k, v in x.items() if k not in ('kind', 'elapsed_seconds', 'journal_elapsed_seconds')}
        for x in events if x['kind'] == 'search_poll_completed']
    assert journal_polls == polls and local['search_poll_count'] == len(polls)
    assert local['search_neighbor_proposals'] == 12 * len(polls)
    assert local['search_strict_moves'] == sum(x['improved'] for x in polls)
    position = 0
    for si, start in enumerate(starts):
        center = start
        for level, delta in enumerate(((.1*R,.1*Z,.2*Z),(.05*R,.05*Z,.1*Z),(.025*R,.025*Z,.05*Z))):
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
                    inside = all(bounds[k][0]<=g[k]<=bounds[k][1] for g in geometry for k in range(3))
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
    assert summary['bank_size'] == bank_count and summary['bank_proposals'] == pair_count
    assert summary['evaluated_pairs'] == len(records) and summary['eligible_pairs'] == len(eligible)
    assert summary['floating_point_unresolved_pairs'] == local['search_inner_unresolved_pairs']
    if selected is not None:
        assert selected['J'] + 1e-10 + 1e-9 * max(abs(selected['J']), abs(control['J'])) >= control['J']


def close_tree(a, b):
    if isinstance(a, list):
        assert isinstance(b, list) and len(a) == len(b)
        for x, y in zip(a, b): close_tree(x, y)
    else:
        close(a, b)


def validate_state(state):
    assert set(state) == {'Gamma', 'eta', 'geometry'}
    assert nonnegative_number(state['Gamma']) and state['Gamma'] > 0
    assert nonnegative_number(state['eta']) and state['eta'] <= 1
    assert len(state['geometry']) == 2
    for g in state['geometry']:
        assert len(g) == 3 and all(type(x) in (int, float) and math.isfinite(x) for x in g)
        assert g[0] > 0 and g[1] > 0


def validate_moments(state, moments):
    close(moments['Gamma'], state['Gamma'])
    assert nonnegative_number(moments['I_z']) and moments['I_z'] > 0
    a, b = moments['between'], moments['raw']
    close_tree(a['centroid'], b['centroid']); close_tree(a['covariance'], b['covariance'])
    cov = a['covariance']
    assert len(cov) == 2 and all(len(row) == 2 for row in cov)
    assert cov[0][0] > 0 and cov[1][1] > 0 and cov[0][0]*cov[1][1] > cov[0][1]**2
    close(cov[0][1], cov[1][0])
    for i in range(2):
        for j in range(2): close(b['covariance'][i][j], b['raw_second'][i][j]-b['centroid'][i]*b['centroid'][j])


def active_count(state):
    return int(state['eta'] < 1) + int(state['eta'] > 0)


def validate_confirmation(packet, search, current):
    assert [x['order'] for x in packet['routes']] == [128, 256]
    close(packet['current_norm'], current['Gamma']**2*search['control']['M'])
    close(packet['selected_norm'], search['selected_state']['Gamma']**2*search['selected_record']['M'])
    k = active_count(current)
    assert set(packet['selected_cross']) == {'128', '256'}
    for order in ('128', '256'):
        cross = packet['selected_cross'][order]
        assert len(cross) == 2
        for item in cross:
            pairs = item['ordered_pairs']
            # Physics retains nonzero original slot indices, including slot 1 when eta=1.
            indices = [i for i, w in enumerate((1-current['eta'], current['eta'])) if w > 0]
            assert [(x['i'], x['j']) for x in pairs] == [(i, j) for i in indices for j in indices]
            assert len(pairs) == k*k
            close(item['total'], math.fsum(x['value'] for x in pairs))
    for i in range(2): close(packet['selected_cross']['128'][i]['total'], packet['selected_cross']['256'][i]['total'])
    for route in packet['routes']:
        assert route['C'] > 0 and route['N'] >= 0 and route['N_unchanged'] >= 0
        close(route['J'], search['selected_record']['J']); close(route['control_J128'], search['control']['J'])
        assert route['C']-route['J'] >= 0 and route['C']-route['control_J128'] >= 0
        close(route['N'], route['C']-route['J'])
        close(route['N_unchanged'], route['C']-route['control_J128'])
        close(route['N_unchanged']-route['N'], route['J']-route['control_J128'])
        close(route['relative_target_error'], math.sqrt(route['N']/route['C']), score=True)
        close(route['unchanged_relative_target_error'], math.sqrt(route['N_unchanged']/route['C']), score=True)
    close(packet['routes'][0]['relative_target_error'], packet['routes'][1]['relative_target_error'], score=True)


def validate_paths(result):
    paths, searches = result['paths'], result['searches']
    assert len(paths) == 2 and len(searches) == 48
    initial = dict(Gamma=1.5*math.sqrt(2*math.pi), eta=0., geometry=[[1., 1., 0.]]*2)
    pos = 0
    for path, n in zip(paths, (16, 32)):
        assert path['h'] == 1/n and path['completed_steps'] == n and len(path['steps']) == n+1
        assert path['steps'][0]['state'] == initial
        for index, item in enumerate(path['steps']):
            assert item['step'] == index and item['time'] == index/n
            validate_state(item['state']); validate_moments(item['state'], item['moments'])
            if not index: continue
            saved = searches[pos]; pos += 1
            assert saved['path_h'] == path['h'] and saved['step'] == index
            search = saved['search']
            assert search['h'] == path['h'] and search['original_state'] == path['steps'][index-1]['state']
            assert search['selected_state'] == item['state'] and search['summary'] == item['search_summary']
            assert search['selected_record']['J'] > search['control']['J']
            validate_confirmation(item['confirmation'], search, path['steps'][index-1]['state'])
    old = read_json(BASE/'result.json')
    assert old['numerical_qualified'] is True and old['verdict'] == 'ordinary_current_state_evaluator_and_first_steps_qualified'
    for path, prior in zip(paths, old['steps']):
        item = path['steps'][1]
        for key in ('Gamma', 'eta', 'geometry'): close_tree(item['state'][key], prior['selected_state'][key])
        search = next(x['search'] for x in searches if x['path_h'] == path['h'] and x['step'] == 1)
        close(search['selected_record']['J'], prior['selected_record']['J']); close(search['control']['J'], prior['control']['J'])
        for route in ('between', 'raw'):
            for key in ('centroid', 'covariance'):
                close_tree(item['moments'][route][key], prior['confirmation']['moments']['selected'][route][key])


def validate_scoring(result, manifest):
    scored, paths, c = result['scoring'], result['paths'], result['counters']
    assert scored == result['details']['scoring']
    assert scored['schema'] == 't71-postprediction-score-v1' and scored['numerical_qualified'] is True
    names = {'prediction_sealed_before_reference', 'saved_reference_eligibility',
        'reference_layout_and_polynomial_readback', 'reference_score_integration',
        'time_comparison_integration', 'stored_moment_routes', 'fixed_work_accounting', 'raw_identity_preservation'}
    assert set(scored['checks']) == names and all(x is True for x in scored['checks'].values())
    assert scored['prediction_seal'] == result['prediction_seal']
    assert scored['covariance_denominator'] == 1.0882203729522952
    d0 = scored['covariance_denominator']
    eligible_path = 'tracks/tog/tasks/t61-saved-output-qualification/result.json'
    assert scored['reference_eligibility'] == next(x for x in manifest['inputs'] if x['path'] == eligible_path)
    eligibility = read_json(REPO/eligible_path)
    assert eligibility['accepted_saved_evidence'] is eligibility['reference_qualified_full_window'] is eligibility['meaningful_motion'] is True
    assert eligibility['T60_history_reclassified'] is False
    records = manifest['reference_records']
    assert result['raw_identities'] == scored['raw_identities'] and result['array_layouts'] == scored['array_layouts']
    assert len(scored['raw_identities']) == 10 and len(scored['array_layouts']) == 60
    for item, record in zip(scored['raw_identities'], records):
        assert item['path'] == record['raw']['path']
        assert item['before'] == item['after'] == {k: record['raw'][k] for k in ('bytes', 'sha256')}
    wanted_layouts = []
    for record in records:
        n = int(record['name'][1:])
        for key in ('q', 'qr', 'qz', 'r', 'rc', 'z'):
            shape = [n, 2*n] if key in ('q', 'qr', 'qz') else [2*n] if key == 'z' else [n]
            wanted_layouts.append(dict(path=record['raw']['path'], name=record['name'], index=record['index'],
                key=key, shape=shape, dtype='float64', bytes=8*math.prod(shape)))
    assert scored['array_layouts'] == wanted_layouts
    stats = scored['reference_statistics']
    assert len(stats) == 10
    for item, record in zip(stats, records):
        assert (item['name'], item['index'], item['time']) == (record['name'], record['index'], record['time'])
        metadata = read_json(REPO/record['metadata']['path'])
        assert metadata['whole_task_qualified'] is False
        for key, value in item['statistics'].items(): close_tree(value, metadata['statistics'][key])
        assert item['minimum_corner'] >= 0
    statmap = {(x['name'], x['index']): x['statistics'] for x in stats}
    motion = scored['reference_motion']
    assert scored['meaningful_motion'] is motion['passed'] is True and len(motion['records']) == 2
    for item, name in zip(motion['records'], ('S256', 'S128')):
        assert item['name'] == name
        before, after = statmap[name, 0]['centroid'][1], statmap[name, 4]['centroid'][1]
        close(item['initial_axial_centroid'], before); close(item['final_axial_centroid'], after)
        close(item['axial_displacement'], after-before)
        assert item['passed'] is (after-before >= .25) and item['passed']
    initial_cov = statmap['S256', 0]['covariance']
    close(math.sqrt(math.fsum(x*x for row in initial_cov for x in row)), d0)
    direct, checkpoints = scored['direct_scores'], scored['checkpoint_scores']
    assert len(direct) == 40 and len(checkpoints) == 20
    schedule = [(name, i, p) for name in ('S256', 'S128') for i in range(5) for p in range(2)]
    for packet, (name, index, pi) in zip(checkpoints, schedule):
        path = paths[pi]; predicted = path['steps'][index*(4 if pi == 0 else 8)]
        assert (packet['name'], packet['index'], packet['path_index'], packet['time'], packet['h']) == (name, index, pi, index/4, path['h'])
        assert packet['model_moments'] == predicted['moments']
        scores = [packet['primary'], packet['confirmation']]
        for score, orders in zip(scores, ([8, 6], [16, 12])):
            assert score['orders'] == orders
            assert (score['name'], score['index'], score['path_index'], score['time'], score['h']) == (name, index, pi, index/4, path['h'])
            assert score['numerator'] >= 0 and score['denominator'] > 0
            close(score['relative_error'], math.sqrt(score['numerator']/score['denominator']), score=True)
            close(score['denominator'], statmap[name, index]['vorticity_squared_integral'])
            for key in ('model_D8_circulation', 'model_D8_impulse', 'model_D8_vorticity_squared', 'elapsed_seconds'):
                assert nonnegative_number(score[key])
        for key in ('numerator', 'denominator', 'model_D8_circulation', 'model_D8_impulse', 'model_D8_vorticity_squared'):
            close(scores[0][key], scores[1][key])
        close(scores[0]['relative_error'], scores[1]['relative_error'], score=True)
        ref, model = statmap[name, index], predicted['moments']
        dz = [model['between']['centroid'][i]-ref['centroid'][i] for i in range(2)]
        dc = [[model['between']['covariance'][i][j]-ref['covariance'][i][j] for j in range(2)] for i in range(2)]
        errors = packet['moment_errors']
        close_tree(errors['signed_centroid_difference'], dz); close_tree(errors['signed_covariance_difference'], dc)
        close(errors['axial_centroid_error'], abs(dz[1]))
        close(errors['normalized_covariance_error'], math.sqrt(math.fsum(x*x for row in dc for x in row))/d0)
        close(errors['circulation_difference'], model['Gamma']-ref['circulation'])
        close(errors['impulse_difference'], model['I_z']-ref['axial_impulse'])
        gates = dict(field=scores[0]['relative_error'] <= .1, centroid=errors['axial_centroid_error'] <= .1,
            covariance=errors['normalized_covariance_error'] <= .1)
        assert packet['gates'] == gates and packet['passed'] is all(gates.values())
    assert direct == [s for p in checkpoints for s in (p['primary'], p['confirmation'])]
    lookup = {(x['path_index'], x['index'], x['name']): x for x in checkpoints}
    sensitivity = scored['reference_sensitivity']
    assert len(sensitivity['records']) == 10
    for packet, (pi, index) in zip(sensitivity['records'], [(p, i) for p in range(2) for i in range(5)]):
        a, b = lookup[pi, index, 'S256'], lookup[pi, index, 'S128']
        delta = dict(field=abs(a['primary']['relative_error']-b['primary']['relative_error']),
            centroid=abs(a['moment_errors']['axial_centroid_error']-b['moment_errors']['axial_centroid_error']),
            covariance=abs(a['moment_errors']['normalized_covariance_error']-b['moment_errors']['normalized_covariance_error']))
        assert packet['path_index'] == pi and packet['time'] == index/4
        assert packet['differences'] == delta and packet['passed'] is all(x <= .01 for x in delta.values())
    assert sensitivity['passed'] is all(x['passed'] for x in sensitivity['records'])
    times = scored['time_sensitivity']
    assert len(times['records']) == 17 and len(times['routes']) == 68
    for index, packet in enumerate(times['records']):
        routes = times['routes'][4*index:4*index+4]
        assert [(x['R'], x['orders']) for x in routes] == [(r, o) for r in (8., 12.) for o in ([64, 128], [96, 192])]
        for route in routes:
            assert route['time'] == index/16 and route['numerator'] >= 0 and route['denominator'] > 0
            close(route['relative_error'], math.sqrt(route['numerator']/route['denominator']), score=True)
            close(route['relative_error'], routes[0]['relative_error'], score=True)
        assert packet['time'] == index/16 and packet['primary'] == routes[0]
        ma, mb = paths[0]['steps'][index]['moments']['between'], paths[1]['steps'][2*index]['moments']['between']
        dz = abs(ma['centroid'][1]-mb['centroid'][1])
        dc = math.sqrt(math.fsum((ma['covariance'][i][j]-mb['covariance'][i][j])**2 for i in range(2) for j in range(2)))/d0
        close(packet['axial_centroid_difference'], dz); close(packet['normalized_covariance_difference'], dc)
        gates = dict(field=routes[0]['relative_error'] <= .01, centroid=dz <= .01, covariance=dc <= .01)
        assert packet['gates'] == gates and packet['passed'] is all(gates.values())
    assert times['passed'] is all(x['passed'] for x in times['records'])
    for field, subset in [('physical_pass_primary', [x for x in checkpoints if x['name'] == 'S256']),
        ('physical_pass_sensitivity_reference', [x for x in checkpoints if x['name'] == 'S128']),
        ('physical_pass_both_references', checkpoints)]:
        assert scored[field] is all(x['passed'] for x in subset)
    expected = ast.literal_eval(next(n.value for n in ast.parse((HERE/'scorer.py').read_text(encoding='utf-8')).body
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'EXPECTED' for t in n.targets)))
    assert expected and all(scored['counters'].get(k, 0) == v for k, v in expected.items())
    assert all(type(v) is int and v >= 0 and c['scorer_'+k] == v for k, v in scored['counters'].items())
    assert scored['counters']['raw_hashed_bytes'] == 2*sum(x['bytes'] for x in manifest['raw_inputs'])
    assert scored['counters']['nonarray_hashes'] == 12
    nonarray_bytes = result['prediction_seal']['bytes'] + scored['reference_eligibility']['bytes'] + sum(x['metadata']['bytes'] for x in records)
    assert scored['counters']['nonarray_hashed_bytes'] == nonarray_bytes
    assert result['reference_sensitive'] is (not sensitivity['passed']) and result['time_sensitive'] is (not times['passed'])
    assert result['physical_pass'] is scored['physical_pass_both_references']
    stable = sensitivity['passed'] and times['passed']
    assert result['full_task_validated'] is bool(stable and result['physical_pass'])
    expected_verdict = ('time_or_reference_sensitive_inconclusive' if not stable else
        'ordinary_full_window_joint_pass' if result['physical_pass'] else 'ordinary_full_window_joint_miss')
    assert result['verdict'] == expected_verdict


def validate_journal(result):
    # At most one search's proposal/weight records are retained; no full journal load.
    c, keys, searches = result['counters'], counter_keys('search.py'), result['searches']
    counts, misc, pending = {}, [], None
    completed, lines, byte_count, previous_time = 0, 0, 0, -1.
    sealed = scorer_sealed = first_raw = False
    with (HERE/'local/journal.jsonl').open('rb') as stream:
        for raw in stream:
            packet = json.loads(raw); finite_tree(packet)
            kind = packet['kind']; assert isinstance(kind, str)
            elapsed = packet['journal_elapsed_seconds']; assert nonnegative_number(elapsed) and elapsed >= previous_time
            previous_time = elapsed; lines += 1; byte_count += len(raw)
            counts[kind] = counts.get(kind, 0)+1
            if kind == 'search_started':
                assert pending is None and not sealed and completed < 48
                pending = []
            if pending is not None:
                pending.append(packet)
                if kind == 'search_completed':
                    validate_search(searches[completed]['search'], pending, keys)
                    completed += 1; pending = None
                continue
            if kind in ('step_started', 'step_confirmation', 'step_completed', 'path_started', 'path_completed', 'checkpoint_evaluator'):
                assert not sealed
            if kind == 'predictions_sealed':
                assert not sealed and completed == 48
                assert packet['prediction_seal'] == result['prediction_seal'] and packet['completed_steps'] == 48 and packet['paths'] == 2
                sealed = True
            if kind == 'scorer_prediction_seal_verified':
                assert sealed and not scorer_sealed
                assert packet['prediction_seal'] == result['prediction_seal']; scorer_sealed = True
            if kind == 'first_raw_hash':
                assert scorer_sealed and not first_raw
                assert packet['prediction_seal'] == result['prediction_seal']; first_raw = True
            if kind in ('reference_array_decoded', 'reference_direct_score', 'reference_snapshot_scored', 'time_sensitivity_scored'):
                assert first_raw
            misc.append(packet)
    assert pending is None and completed == 48 and sealed and scorer_sealed and first_raw
    assert lines == c['root_journal_events'] and byte_count == c['root_journal_bytes']
    phases = ['identity_runtime', 'rules', 'causal_predictions', 'checkpoint_evaluator', 'seal_predictions',
        'startup_regression', 'sealed_reference_scoring', 'work_accounting', 'identity_preservation']
    assert [x['name'] for x in misc if x['kind'] == 'phase_started'] == phases
    finished = [x for x in misc if x['kind'] == 'phase_finished']
    assert [x['name'] for x in finished] == phases and set(result['phases_seconds']) == set(phases)
    for item in finished:
        assert item['seconds'] == result['phases_seconds'][item['name']] and nonnegative_number(item['seconds'])
    assert misc[-1]['kind'] == 'phase_finished'
    def payload(item): return {k: v for k, v in item.items() if k not in ('kind', 'elapsed_seconds', 'journal_elapsed_seconds')}
    assert [payload(x) for x in misc if x['kind'] == 'qualification'] == result['checks']
    assert [payload(x) for x in misc if x['kind'] == 'rule_constructed'] == result['details']['rules']
    assert [payload(x) for x in misc if x['kind'] == 'checkpoint_evaluator'] == result['details']['checkpoint_evaluator']
    assert [payload(x) for x in misc if x['kind'] == 'reference_array_decoded'] == result['array_layouts']
    assert [payload(x) for x in misc if x['kind'] == 'time_sensitivity_scored'] == result['scoring']['time_sensitivity']['records']
    # Payload elapsed_seconds is phase-local; the independent journal clock is preserved above.
    direct_events = [x for x in misc if x['kind'] == 'reference_direct_score']
    assert [{k: v for k, v in x.items() if k not in ('kind', 'journal_elapsed_seconds')} for x in direct_events] == result['scoring']['direct_scores']
    snapshots = [x for x in misc if x['kind'] == 'reference_snapshot_scored']
    assert len(snapshots) == 10
    for event, raw, stats in zip(snapshots, result['raw_identities'], result['scoring']['reference_statistics']):
        assert (event['name'], event['index']) == (stats['name'], stats['index'])
        assert event['raw_identity'] == raw and nonnegative_number(event['elapsed_seconds'])
    first = next(x for x in misc if x['kind'] == 'first_raw_hash')
    assert first['path'] == result['raw_identities'][0]['path']
    begun = [x for x in misc if x['kind'] == 'path_started']
    done = [x for x in misc if x['kind'] == 'path_completed']
    assert len(begun) == len(done) == 2
    for path, begin, end in zip(result['paths'], begun, done):
        assert begin['h'] == end['h'] == path['h']
        assert begin['steps'] == end['completed_steps'] == path['completed_steps']
        assert begin['initial_state'] == path['steps'][0]['state']
    steps = [(p, i) for p in result['paths'] for i in range(1, p['completed_steps']+1)]
    starts = [x for x in misc if x['kind'] == 'step_started']
    ends = [x for x in misc if x['kind'] == 'step_completed']
    confirms = [x for x in misc if x['kind'] == 'step_confirmation']
    assert len(starts) == len(ends) == len(confirms) == 48
    for (path, index), start, end, confirm in zip(steps, starts, ends, confirms):
        current, chosen = path['steps'][index-1], path['steps'][index]
        assert (start['h'], start['step'], start['time_before'], start['current_state']) == (path['h'], index, current['time'], current['state'])
        assert (end['h'], end['step'], end['time'], end['state'], end['moments']) == (path['h'], index, chosen['time'], chosen['state'], chosen['moments'])
        saved = next(x['search'] for x in searches if x['path_h'] == path['h'] and x['step'] == index)
        assert end['search_counters'] == saved['counters']
        assert {k: v for k, v in payload(confirm).items() if k != 'label'} == chosen['confirmation']
    fixed_events = dict(search_started=48, search_completed=48, path_started=2, path_completed=2,
        step_started=48, step_completed=48, step_confirmation=48, checkpoint_evaluator=10,
        predictions_sealed=1, scorer_prediction_seal_verified=1, first_raw_hash=1,
        reference_array_decoded=60, reference_direct_score=40, reference_snapshot_scored=10,
        time_sensitivity_scored=17, qualification=8, rule_constructed=11)
    assert all(counts.get(k, 0) == v for k, v in fixed_events.items())
    return dict(events=lines, bytes=byte_count, complete_searches=completed, event_counts=counts,
        streaming_one_search_at_a_time=True, predictions_precede_all_raw_events=True)


def validate_work(result, manifest, admitted):
    c, searches, paths = result['counters'], result['searches'], result['paths']
    assert c and all(type(x) is int and x >= 0 for x in c.values())
    assert c['new_arrays_saved'] == 0
    assert c['root_input_files_hashed_before'] == c['root_input_files_hashed_after'] == len(admitted) == 42
    assert c['root_input_bytes_hashed_before'] == c['root_input_bytes_hashed_after'] == sum(x['bytes'] for x in admitted.values())
    for phase in ('prediction_seal', 'prediction_after'):
        assert c['root_input_files_hashed_'+phase] == 1 and c['root_input_bytes_hashed_'+phase] == result['prediction_seal']['bytes']
    for key in counter_keys('search.py'): assert c.get(key, 0) == sum(x['search']['counters'][key] for x in searches)
    for key in counter_keys('physics.py'): assert key in c
    fixed = dict(rule_count=11, rule_nodes=783, rule_eigh_calls=11, root_steps_confirmed=48,
        root_checkpoint_routes=80, root_spatial_grids=4, root_spatial_grid_points=53248,
        search_invocations=48, phys_instances=1, phys_rule_transforms=3, phys_rule_nodes_transformed=448,
        phys_moment_calls=50, root_scientific_helpers_loaded=3, root_json_write_attempts=2,
        root_gaussian_component_calls=96, root_gaussian_component_points=786432,
        root_exp_evaluations=786432, root_gram_calls=510, phys_field_calls=176, phys_field_spatial_points=1851392)
    totals = dict(component_points=0, heat_nodes=0, heat_points=0, ordered_points=0,
        cross_pairs=0, cross_nodes=0, reductions=160, reduction_points=40*53248)
    for saved in searches:
        search = saved['search']; k = active_count(search['original_state'])
        canonical_k = len(search['active_components']); bases = search['counters']['search_cross_calls']
        totals['cross_pairs'] += canonical_k**2*bases + 4*k*k
        totals['cross_nodes'] += canonical_k**2*bases*128 + 2*k*k*(128+256)
        totals['component_points'] += 2*k*8192
        totals['heat_nodes'] += k*(128+256); totals['heat_points'] += k*8192*(128+256)
        totals['ordered_points'] += 2*k*k*8192
        totals['reductions'] += 18+4*k*k; totals['reduction_points'] += (18+4*k*k)*8192
    for path in paths:
        for i in range(0, path['completed_steps']+1, path['completed_steps']//4):
            k = active_count(path['steps'][i]['state'])
            totals['component_points'] += 2*k*53248
            totals['heat_nodes'] += 4*k*(128+256); totals['heat_points'] += k*53248*(128+256)
            totals['ordered_points'] += 2*k*k*53248
    fixed.update(phys_cross_calls=c['search_cross_calls']+192,
        phys_cross_ordered_pair_integrals=totals['cross_pairs'], phys_cross_integrand_points=totals['cross_nodes'],
        phys_field_component_points=totals['component_points'], phys_field_heat_nodes=totals['heat_nodes'],
        phys_field_heat_integrand_points=totals['heat_points'], phys_field_ordered_pair_points=totals['ordered_points'],
        phys_gram_calls=510+c['search_current_gram_calls']+c['search_candidate_gram_calls'],
        root_direct_reductions=totals['reductions'], root_direct_reduction_points=totals['reduction_points'])
    for key, value in fixed.items(): assert c.get(key, 0) == value, (key, c.get(key), value)
    assert c['phys_peak_spatial_points'] <= 18432
    caps = dict(search_proposals=109440, search_component_evaluations=57552,
        phys_cross_calls=57744, phys_cross_ordered_pair_integrals=230976, phys_cross_integrand_points=29614080,
        phys_field_component_points=3702784, phys_field_heat_integrand_points=710934528,
        phys_field_ordered_pair_points=7405568, phys_field_heat_nodes=67584)
    assert all(c[k] <= v for k, v in caps.items())
    assert c['search_weight_attempts']+c['search_control_attempts'] <= 437808
    account = result['checks'][6]['details']
    assert account['predicates'] and all(x is True for x in account['predicates'].values())
    assert account['caps'] == caps
    assert account['expected'] and all(c.get(k, 0) == v for k, v in account['expected'].items())


def validate_result(result, manifest, receipt, manifest_path):
    finite_tree(result)
    assert result['numerical_qualified'] is result['inputs_preserved'] is True
    assert result['runtime']['python'] == manifest['expected_python'] and result['runtime']['numpy'] == manifest['expected_numpy']
    assert Path(result['runtime']['executable']).resolve() == Path(manifest['executable']['path']).resolve()
    assert len(result['checks']) == 8 and [x['name'] for x in result['checks']] == list(CHECKS)
    assert all(x['passed'] is True and isinstance(x['details'], dict) for x in result['checks'])
    for key in ('new_method_claim', 'formal_error_certificate', 'formal_family_exclusion', 'future_reference_predictor_inputs'):
        assert result[key] is False
    assert result['new_reference_trajectories'] == 0 and result['new_model_trajectories'] == 2
    assert result['prior_scientific_child_seconds'] == PRIOR
    assert 0 <= result['child_elapsed_before_result_write_seconds'] <= receipt['scientific_child_supervised_seconds']
    admitted = {(REPO/x['path']).resolve(): {k: x[k] for k in ('bytes', 'sha256')} for x in manifest['inputs']}
    admitted[Path(manifest['executable']['path']).resolve()] = receipt['executable_identity']
    admitted[manifest_path] = receipt['input_manifest_identity']
    observed = {(REPO/x['path']).resolve(): {k: x[k] for k in ('bytes', 'sha256')} for x in result['input_identities']}
    assert len(observed) == len(result['input_identities']) and observed == admitted
    seal = result['prediction_seal']
    assert seal['path'] == (HERE/'local/predictions.json').relative_to(REPO).as_posix()
    assert {k: seal[k] for k in ('bytes', 'sha256')} == receipt['predictions_identity']
    predictions = read_json(HERE/'local/predictions.json')
    assert predictions['schema'] == 't71-causal-predictions-v1' and predictions['paths'] == result['paths']
    assert predictions['completed_projection_steps'] == 48 and predictions['new_reference_trajectories'] == 0
    assert predictions['future_reference_predictor_inputs'] is False and result['details']['prediction_seal'] == seal
    validate_paths(result)
    rules = result['details']['rules']
    assert [x['order'] for x in rules] == manifest['expected_rule_orders']
    for rule in rules:
        assert abs(rule['weight_sum']-2) <= 1e-12 and 0 <= rule['node_symmetry'] <= 1e-12 and 0 <= rule['weight_symmetry'] <= 1e-12
    for index in (1, 3):
        check = result['checks'][index]['details']
        assert check['passed'] is True and check['failures'] == [] and check['comparison_calls'] > 0 and check['compared_values'] > 0
        assert 0 <= check['maximum_tolerance_ratio'] <= 1
    checkpoints = result['details']['checkpoint_evaluator']
    assert len(checkpoints) == 10
    for packet, (h, t) in zip(checkpoints, [(h, i/4) for h in (.0625, .03125) for i in range(5)]):
        assert packet['h'] == h and packet['time'] == t and len(packet['routes']) == 8
        expected = [(f'D{r}-{nr}x{nz}', order) for r in (8, 12) for nr, nz in ((64, 128), (96, 192)) for order in (128, 256)]
        assert [(x['grid'], x['order']) for x in packet['routes']] == expected
        primary = next(x for x in packet['routes'] if x['grid'] == 'D12-64x128' and x['order'] == 128)
        for route in packet['routes']:
            assert route['qnorm'] > 0 and route['Fnorm'] >= 0
            close(route['qnorm'], primary['qnorm']); close(route['Fnorm'], primary['Fnorm'])
    validate_scoring(result, manifest)
    validate_work(result, manifest, admitted)
    receipt['saved_readback'] = validate_journal(result)
    receipt['saved_readback'].update(raw_arrays_opened_by_supervisor=0, raw_identities_verified_from_child_and_frozen_metadata=10,
        physical_pass=result['physical_pass'], reference_sensitive=result['reference_sensitive'], time_sensitive=result['time_sensitive'],
        full_task_validated=result['full_task_validated'], scientific_methods_reexecuted=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, default=HERE / 'input-manifest.json')
    args = parser.parse_args()
    started = time.perf_counter()
    manifest_path = args.manifest.resolve()
    assert manifest_path == HERE / 'input-manifest.json'
    manifest = read_json(manifest_path)
    assert manifest['schema'] == 't71-causal-full-window-freeze-v1'
    assert manifest['maximum_scientific_child_invocations'] == 1
    assert manifest['child_timeout_seconds'] == LIMIT and manifest['observed_peak_working_set_limit_bytes'] == CAP
    assert manifest['required_available_physical_bytes'] == REQUIRED and manifest['memory_sample_interval_seconds'] == INTERVAL
    assert manifest['expected_python'] == '3.12.14' and manifest['expected_numpy'] == '2.3.5'
    assert manifest['expected_rule_orders'] == [2, 3, 6, 8, 12, 16, 64, 96, 128, 192, 256]
    assert manifest['expected_rule_nodes'] == 783 and manifest['expected_rule_eigh_calls'] == 11
    assert manifest['heat_orders'] == [64, 128, 256] and manifest['step_sizes'] == [.0625, .03125]
    assert manifest['expected_check_names'] == list(CHECKS)
    assert manifest['prior_scientific_child_seconds'] == PRIOR
    inputs = manifest['inputs']
    assert len(inputs) == len({x['path'] for x in inputs}) == 40
    for item in inputs:
        path = Path(item['path'])
        assert not path.is_absolute() and '..' not in path.parts
        assert path.suffix.lower() not in {'.npz', '.npy'}
        assert identity(REPO / path) == {k: item[k] for k in ('bytes', 'sha256')}
    raw_inputs = manifest['raw_inputs']
    assert len(raw_inputs) == len({x['path'] for x in raw_inputs}) == 10
    assert len(manifest['reference_records']) == 10
    for record in manifest['reference_records']:
        assert record['raw'] in raw_inputs and record['metadata'] in inputs
        assert record['name'] in ('S256', 'S128') and record['index'] in range(5)
        assert record['time'] == [0.0, .25, .5, .75, 1.0][record['index']]
        expected = 'tracks/tog/tasks/t60-full-window-gaussian-screen/local/' + record['name'] + '-snapshot-' + str(record['index'])
        assert record['raw']['path'] == expected + '.npz'
        assert record['metadata']['path'] == expected + '.json'
    assert {(x['name'], x['index']) for x in manifest['reference_records']} == {(name, i) for name in ('S256', 'S128') for i in range(5)}
    # Raw identities are inherited metadata here: no raw file open/hash/stat.
    exe = Path(manifest['executable']['path'])
    assert identity(exe) == {k: manifest['executable'][k] for k in ('bytes', 'sha256')}
    memory_record = next(x for x in inputs if (REPO / x['path']).resolve() == MEMORY)
    assert identity(MEMORY) == {k: memory_record[k] for k in ('bytes', 'sha256')}
    local = HERE / 'local'
    local.mkdir(exist_ok=True)
    for name in ('execution-started.json', 'result.json', 'predictions.json', 'journal.jsonl', 'failure.json',
                 'stdout.txt', 'stderr.txt', 'memory.jsonl'):
        assert not (local / name).exists(), name
    assert not (HERE / 'execution.json').exists()
    preflight = read_json(HERE / 'preflight.json')
    assert preflight['schema'] == 't71-os-preflight-v1' and preflight['passed'] is True
    assert preflight['source'] == identity(MEMORY)
    spec = importlib.util.spec_from_file_location('t71_memory_supervisor', MEMORY)
    observer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(observer)
    command = [str(exe), '-I', '-B', '-u', '-X', 'utf8', str(HERE / 'measure.py'), '--manifest', str(manifest_path)]
    overrides = {k: '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')}
    environment = dict(os.environ)
    environment.update(overrides)
    receipt = dict(schema='t71-causal-full-window-execution-v1', started_utc=now(), command=command, cwd=str(REPO),
        child_timeout_seconds=LIMIT, observed_peak_working_set_limit_bytes=CAP,
        required_available_physical_bytes=REQUIRED, memory_sample_interval_seconds=INTERVAL,
        thread_environment_overrides=overrides, scientific_child_invocations=0,
        new_reference_trajectories=0, maximum_ordinary_causal_paths=2, complete_result_validated=False, numerical_qualified=False,
        verdict=None, prior_scientific_child_seconds=PRIOR, T61_qualification_seconds=.9663960000034422,
        prior_scientific_series_scope=manifest['prior_scientific_series_scope'], scientific_series_is_total_project_cost=False,
        input_manifest_identity=identity(manifest_path), supervisor_identity=identity(Path(__file__)),
        worker_identity=identity(HERE / 'measure.py'), physics_identity=identity(BASE / 'physics.py'),
        search_identity=identity(BASE / 'search.py'), scorer_identity=identity(HERE / 'scorer.py'),
        raw_inputs_previously_recorded=raw_inputs, supervisor_raw_arrays_opened=0, memory_observer_identity=identity(MEMORY), executable_identity=identity(exe),
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
    receipt['predictions_exists'] = (local / 'predictions.json').exists()
    if receipt['predictions_exists']:
        receipt['predictions_identity'] = identity(local / 'predictions.json')
    receipt['result_exists'] = (local / 'result.json').exists()
    if receipt['result_exists']:
        receipt['result_identity'] = identity(local / 'result.json')
        try:
            result = read_json(local / 'result.json')
            assert result['schema'] == 't71-causal-full-window-result-v1'
            assert result['verdict'] in ACCEPTED | {'failed_qualification_no_retry', 'stalled_bounded_search_inconclusive'}
            receipt['retained_worker_verdict'] = result['verdict']
            if receipt['status'] == 'exited_pending_readback':
                if result['verdict'] in {'failed_qualification_no_retry', 'stalled_bounded_search_inconclusive'}:
                    assert result['numerical_qualified'] is False
                    receipt['status'] = result['verdict']
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
