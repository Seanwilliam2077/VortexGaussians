"""Recover T81 suffix ignition times from saved fuel clocks and score prefix previews."""
import gzip
import hashlib
import json
import struct
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PUBLIC = HERE.parent / 't81-firewoods-capacity-causality' / 'public'
RECIPE = HERE.parent / 't42-firewoods-sequential-workflow' / 'recipe.json'
OUTPUT = HERE / 'CLOCK.json'
START, END = 180, 360
CUTS = (0, 60, 90, 120, 150)
POINTS = 34687
COLUMNS = ['id', 'fuelInitial', 'fuel', 'heat', 'char', 'glow', 'state']
POLICIES = ('per-layer', 'global')


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source(name, manifest):
    record = manifest[name]
    packed = (PUBLIC / name).read_bytes()
    require(len(packed) == record['bytes'] and digest(packed) == record['sha256'], name + ' packed')
    decoded = gzip.decompress(packed)
    require(len(decoded) == record['decoded_bytes'] and digest(decoded) == record['decoded_sha256'], name + ' decoded')
    return decoded


def f32(number):
    return struct.unpack('<f', struct.pack('<f', number))[0]


def clocks(initial, decrement):
    result = {initial: 0}
    fuel = initial
    for ticks in range(1, END - START + 1):
        fuel = max(0.0, f32(fuel - decrement))
        require(fuel not in result, 'non-unique fuel clock')
        result[fuel] = ticks
    return result


def material(state, label):
    require(state['material_columns'] == COLUMNS, label + ' columns')
    values = {}
    for row in state['material_rows']:
        idx = int(row[0].removeprefix('ply:'))
        require(row[0] == f'ply:{idx}' and idx not in values, label + ' invalid or duplicate ID')
        require(row[1] == 1 and 0 < row[2] <= 1 and row[6] in (0, 1), f'{label} unsupported fuel or state {idx}')
        values[idx] = (row[2], row[6])
    require(set(values) == set(range(POINTS)), label + ' incomplete material IDs')
    frontier = state['frontier']
    burning = {idx for idx, (_, phase) in values.items() if phase == 1}
    require(len(frontier) == len(burning) and set(frontier) == burning, label + ' invalid frontier')
    return values


def reconstruct(arm, manifest, recipe):
    def checkpoint(tag):
        return json.loads(source(f'{arm}-{tag}.dynamic.json.gz', manifest))

    prefix = checkpoint('prefix')
    after = checkpoint('after-intervention')
    end = checkpoint('endpoint')
    require((prefix['frame'], after['frame'], end['frame']) == (START, START, END), arm + ' frame labels')
    before_rows = material(prefix, arm + ' prefix')
    initial = material(after, arm + ' intervention')
    final = material(end, arm + ' endpoint')
    direct = set(after['newly_B_indices'])
    require(len(direct) == len(after['newly_B_indices']) and len(direct) == (288 if arm.endswith('-AB') else 0), arm + ' direct IDs')
    require(all((before_rows[i][0], int(bool(before_rows[i][1] or i in direct))) == initial[i] for i in initial), arm + ' zero-time intervention fields')
    require(set(after['frontier']) - set(prefix['frontier']) == direct, arm + ' direct intervention')
    frontier = list(after['frontier'])
    require(frontier[:len(prefix['frontier'])] == prefix['frontier'], arm + ' preserved prefix ordering')
    decrement = recipe['dt'] / recipe['params']['spreadBurnT']
    clock_luts = {}
    starts = defaultdict(list)
    for idx, (fuel, phase) in initial.items():
        last_fuel, last_phase = final[idx]
        require(last_phase >= phase, f'{arm} invalid state transition {idx}')
        if last_phase == 0:
            require(fuel == last_fuel == 1, f'{arm} unexpected unburned consumption {idx}')
            continue
        if fuel not in clock_luts:
            clock_luts[fuel] = clocks(fuel, decrement)
        ticks = clock_luts[fuel].get(last_fuel)
        require(ticks is not None and ticks > 0, f'{arm} fuel outside attainable clock values {idx}')
        if phase == 1:
            require(ticks == END - START, f'{arm} existing burner clock {idx}')
        else:
            require(fuel == 1, f'{arm} unsupported starting fuel {idx}')
            starts[END - ticks + 1].append(idx)

    rows = [json.loads(line) for line in source(arm + '-steps.jsonl.gz', manifest).splitlines()]
    require([row['frame'] for row in rows] == list(range(1, END + 1)), arm + ' step labels')
    previous_clock = rows[START - 1]['counters']['clockProcessed']
    require(previous_clock == after['counters']['clockProcessed'], arm + ' starting clock total')
    cursor = after['emit_cursor']
    require(prefix['emit_cursor'] == cursor, arm + ' starting emitter cursor')
    masks = {0: set(frontier)}
    timeline = [len(frontier)]
    checked_offers = 0
    endpoint_order = end['frontier']
    initial_order = list(frontier)
    require(endpoint_order[:len(initial_order)] == initial_order, arm + ' endpoint prefix versus zero-time frontier')
    graph_cap = recipe['params']['spreadFrontierCap']
    graph_prefix_stable = len(initial_order) >= graph_cap
    step_render_ms = [0.0]
    last_graph_calls = rows[START - 1]['counters']['frontierProcessed']
    for row in rows[START:]:
        frame = row['frame']
        clock = row['counters']['clockProcessed']
        # The independent clock count tells where the endpoint's append-only frontier
        # ended on this frame. Its slice should reproduce every fuel-derived ID.
        observed_count = clock - previous_clock
        require(len(frontier) <= observed_count <= len(endpoint_order), f'{arm} {frame}: nonmonotone frontier length')
        observed_births = endpoint_order[len(frontier):observed_count]
        require(observed_births == sorted(starts.get(frame, [])), f'{arm} {frame}: frontier vs fuel event IDs/order')
        frontier.extend(observed_births)
        require(clock - previous_clock == len(frontier), f'{arm} {frame}: clock delta differs from active count')
        previous_clock = clock
        graph_calls = row['counters']['frontierProcessed']
        require(graph_calls - last_graph_calls == min(len(frontier), graph_cap), f'{arm} {frame}: graph service count')
        last_graph_calls = graph_calls
        step_render_ms.append(step_render_ms[-1] + row['timing']['step_plus_render_ms'])
        expected_offers = min(len(frontier), recipe['params']['spreadFeedCap'])
        offers = row['offers']
        require(len(offers) == expected_offers, f'{arm} {frame}: offer count')
        for offer in offers:
            cursor = (cursor + 1) % len(frontier)
            require(offer[0] == frontier[cursor], f'{arm} {frame}: emitter differs at saved index {cursor}')
        checked_offers += len(offers)
        timeline.append(len(frontier))
        if frame - START in CUTS:
            masks[frame - START] = set(frontier)
    require(frontier == end['frontier'] and cursor == end['emit_cursor'], arm + ' final frontier or emitter cursor')
    onset = {idx: frame for frame, ids in starts.items() for idx in ids}
    onset.update(dict.fromkeys(direct, START))
    return {'direct': direct, 'endpoint': set(frontier), 'masks': masks,
            'prefix_burning': set(prefix['frontier']), 'onset': onset,
            'graph_sources': initial_order[:graph_cap], 'ms': step_render_ms,
            'checks': {'n_material_ids': len(final), 'clock_deltas_verified': END - START,
                       'offer_source_ids_reproduced': checked_offers, 'endpoint_order_and_cursor_verified': True,
                       'frontier_slice_equals_fuel_birth_ids_all_frames': True,
                       'graph_service_first_ids_unchanged': graph_prefix_stable,
                       'active_counts_frames_180_through_360': timeline}}


def compare(predicted, observed):
    tp = len(predicted & observed)
    fp = len(predicted - observed)
    fn = len(observed - predicted)
    return {'tp': tp, 'fp': fp, 'fn': fn,
            'precision': tp / (tp + fp) if tp + fp else None,
            'recall': tp / (tp + fn) if tp + fn else None,
            'iou': tp / (tp + fp + fn) if tp + fp + fn else None}


def score(pred, edited, original, direct):
    def by_direction(universe):
        return {'gains': compare((pred - original) & universe, (edited - original) & universe),
                'losses': compare((original - pred) & universe, (original - edited) & universe)}
    all_ids = set(range(POINTS))
    return {'signed_all': by_direction(all_ids), 'signed_outside_direct_B': by_direction(all_ids - direct),
            'absolute_AB_burning': compare(pred, edited)}


def onset_comparison(a, ab):
    require(a['prefix_burning'] == ab['prefix_burning'], 'different pre-edit burning IDs')
    shared = set(a['onset']) & set(ab['onset']) - ab['direct']
    shifts = sorted(ab['onset'][idx] - a['onset'][idx] for idx in shared)

    def quantile(q):
        if not shifts:
            return None
        rank = (len(shifts) - 1) * q
        low = int(rank)
        high = min(low + 1, len(shifts) - 1)
        return shifts[low] + (shifts[high] - shifts[low]) * (rank - low)

    def bins(onset):
        by_frame = defaultdict(list)
        for idx, frame in onset.items():
            by_frame[frame].append(idx)
        return by_frame

    new_a, new_ab = bins(a['onset']), bins(ab['onset'])
    burning_a = set(a['prefix_burning'])
    burning_ab = set(ab['prefix_burning'])
    timeline = []
    for frame in range(START, END + 1):
        burning_a.update(new_a[frame])
        burning_ab.update(new_ab[frame])
        gained = burning_ab - burning_a
        lost = burning_a - burning_ab
        timeline.append([frame, len(gained), len(lost), len(gained - ab['direct']), len(lost - ab['direct'])])
    require(burning_a == a['endpoint'] and burning_ab == ab['endpoint'], 'timeline endpoint differs')
    return {'timeline_columns': ['frame', 'gained', 'lost', 'gained_outside_B', 'lost_outside_B'], 'timeline': timeline,
            'pre_edit_left_censored': len(a['prefix_burning']), 'immediate_direct_B': len(ab['direct']),
            'only_AB_by_360_outside_B': len((burning_ab - burning_a) - ab['direct']),
            'only_A_by_360_outside_B': len((burning_a - burning_ab) - ab['direct']),
            'paired_finite_new_onsets_excluding_direct_B': len(shifts),
            'shift_AB_minus_A_frames': {'earlier': sum(s < 0 for s in shifts), 'same': shifts.count(0),
                                        'later': sum(s > 0 for s in shifts),
                                        'linear_quantiles_min_p25_median_p75_max': [quantile(q) for q in [0, .25, .5, .75, 1]]},
            'censoring': 'Absent endpoint means onset later than frame 360 or absent. Common pre-edit sites are left-censored at frame 180.'}


def run():
    meta = (PUBLIC / 'MANIFEST.json').read_bytes()
    manifest = {row['file']: row for row in json.loads(meta)['files']}
    recipe_bytes = RECIPE.read_bytes()
    recipe = json.loads(recipe_bytes)
    p = recipe['params']
    require(p['spreadClockMode'] == 'elapsed' and p['spreadMeasureMode'] == 'legacy' and recipe['dt'] == 1/60
            and p['spreadBurnT'] == 6 and p['spreadFeedCap'] == 48, 'frozen model assumptions')
    result = {'schema': 't84-fuel-clock-preview-v1', 'manifest_sha256': digest(meta), 'recipe_sha256': digest(recipe_bytes),
              'cuts_suffix_steps': list(CUTS), 'arms': {}, 'scores': {}, 'onsets': {}, 'matched_graph_service': {}}
    for policy in POLICIES:
        a = reconstruct(policy + '-A', manifest, recipe)
        ab = reconstruct(policy + '-AB', manifest, recipe)
        for name, data in [('A', a), ('AB', ab)]:
            result['arms'][policy + '-' + name] = data['checks']
        result['onsets'][policy] = onset_comparison(a, ab)
        result['matched_graph_service'][policy] = {'same_first_1400_all_suffix_frames':
            len(a['graph_sources']) == 1400 and a['graph_sources'] == ab['graph_sources']}
        result['scores'][policy] = {}
        for cut in CUTS:
            held = ab['masks'][cut]
            scored = {}
            for method, pred in [('hold_observed_AB', held), ('union_cached_A_endpoint', held | a['endpoint'])]:
                scored[method] = score(pred, ab['endpoint'], a['endpoint'], ab['direct'])
            scored['charged_execution'] = {'AB_native_steps': cut, 'suffix_fraction': cut / (END - START),
                'measured_AB_step_plus_render_ms': ab['ms'][cut], 'measured_full_AB_suffix_step_plus_render_ms': ab['ms'][-1],
                'measured_A_suffix_step_plus_render_ms_for_cache': a['ms'][-1]}
            result['scores'][policy][str(cut)] = scored
    result['qualification'] = 'decoded_existing_records_and_reproduced_clock_counts_frontier_and_offers'
    result['scope'] = ('Partial-take active sets inferred retrospectively using endpoint fuel clocks. Online predictors use only the identified prefix masks and the stated existing A cache. Times and savings of a deployed preview were not measured.')
    return result


def main():
    try:
        result = run()
    except (KeyError, ValueError, OSError, TypeError, IndexError) as exc:
        result = {'schema': 't84-fuel-clock-preview-v1', 'qualification': 'failed', 'error': str(exc)}
    payload = (json.dumps(result, indent=2, allow_nan=False) + '\n').encode()
    if OUTPUT.exists():
        require(OUTPUT.read_bytes() == payload, 'recorded CLOCK.json differs')
    else:
        with OUTPUT.open('xb') as handle:
            handle.write(payload)
    print(result['qualification'])
    return int(result['qualification'] == 'failed')


if __name__ == '__main__':
    raise SystemExit(main())

