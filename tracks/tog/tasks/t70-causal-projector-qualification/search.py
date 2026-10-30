"""T70: fixed, current-state-only T69 projection search; no numerical invocation on import.

Physics is supplied by the caller. Geometry order is (sr, sz, z); pair order is
lexicographic (z, sr, sz). Binary64 candidate enumeration is not an exact-real
inner optimum certificate. emit(kind, data_dict) receives all performed work.
"""
import math
import time

SCHEMA = 't70-causal-projection-search-v1'
COUNTER_KEYS = (
    'search_invocations', 'search_initial_proposals', 'search_neighbor_proposals',
    'search_proposals', 'search_rejected_proposals', 'search_pair_cache_hits',
    'search_pair_evaluations', 'search_component_requests', 'search_component_cache_hits',
    'search_component_evaluations', 'search_current_gram_calls', 'search_candidate_gram_calls',
    'search_cross_calls', 'search_weight_attempts', 'search_control_attempts',
    'search_weight_candidates_before_dedup', 'search_duplicate_weight_candidates',
    'search_inner_unresolved_pairs', 'search_poll_count', 'search_strict_moves',
    'search_rank_operations', 'search_ranked_records',
)


def _finite(value, name):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(name + ' must be finite')
    return value


def _geometry(g):
    if len(g) != 3:
        raise ValueError('geometry must have sr, sz, z')
    result = tuple(_finite(x, 'geometry') for x in g)
    if result[0] <= 0 or result[1] <= 0:
        raise ValueError('component widths must be positive')
    return result


def _key(g):
    return (g[2], g[0], g[1])


def _canonical_pair(pair):
    return tuple(sorted(pair, key=_key))


def _rank(record):
    return (-record['J'], tuple(_key(g) for g in record['geometry']), record['eta'])


def _barycentric(eta, b1, b2, m11, m12, m22):
    left = 1.0 - eta
    B = math.fsum((left * b1, eta * b2))
    M = math.fsum((left * left * m11, 2.0 * eta * left * m12, eta * eta * m22))
    if not math.isfinite(B) or not math.isfinite(M) or M <= 0:
        raise ArithmeticError('nonfinite cross product or nonpositive barycentric Gram')
    return B, M


def _weight_value(eta, b1, b2, m11, m12, m22):
    B, M = _barycentric(eta, b1, b2, m11, m12, m22)
    positive = max(0.0, B)
    Gamma = positive / M
    J = positive * Gamma
    if not math.isfinite(Gamma) or not math.isfinite(J):
        raise ArithmeticError('nonfinite projected scale or improvement')
    if positive > 0 and (Gamma <= 0 or J <= 0):
        raise ArithmeticError('positive projection underflowed to zero')
    return dict(eta=eta, B=B, M=M, Gamma=Gamma, J=J, positive_scale=Gamma > 0)


def solve_weights(b1, b2, M11, M12, M22):
    """Enumerate at most four unique rounded eta values; do not invert a Gram matrix.

    The cancellation flag is a reporting diagnostic (32 ulps of the largest
    subtractand), not an acceptance tolerance. It never changes eta, B, M or J.
    Exact ties use ascending eta. No real-arithmetic optimality is certified.
    """
    b1, b2, M11, M12, M22 = (
        _finite(x, 'inner coefficient') for x in (b1, b2, M11, M12, M22))
    if M11 <= 0 or M22 <= 0:
        raise ValueError('Gram diagonal must be positive')
    beta0, beta1 = b1, b2 - b1
    m0 = M11
    m1 = 2.0 * (M12 - M11)
    m2 = math.fsum((M11, -2.0 * M12, M22))
    t00, t01 = 2.0 * beta1 * m0, beta0 * m1
    t10, t11 = beta1 * m1, 2.0 * beta0 * m2
    A0, A1 = math.fsum((t00, -t01)), math.fsum((t10, -t11))
    if not all(math.isfinite(x) for x in (beta1, m1, m2, A0, A1, t00, t01, t10, t11)):
        raise ArithmeticError('nonfinite stationary coefficients')

    def near_cancel(value, first, second):
        scale = max(abs(first), abs(second))
        return scale > 0 and abs(value) <= 32.0 * math.ulp(scale)

    flags = dict(identical_gram_entries=M11 == M12 == M22,
        rounded_B_constant=beta1 == 0.0, rounded_Gram_constant=m1 == 0.0 and m2 == 0.0,
        rounded_Gram_linear=m2 == 0.0 and m1 != 0.0,
        rounded_derivative_constant=A0 == 0.0 and A1 == 0.0,
        rounded_A1_zero=A1 == 0.0,
        near_A0_cancellation=near_cancel(A0, t00, t01),
        near_A1_cancellation=near_cancel(A1, t10, t11),
        nonfinite_stationary_ratio=False, nonfinite_B_boundary_ratio=False)
    proposals = [(0.0, 'eta_zero'), (1.0, 'eta_one')]
    stationary, boundary = None, None
    if A1 != 0.0:
        stationary = -A0 / A1
        if not math.isfinite(stationary):
            flags['nonfinite_stationary_ratio'] = True
            stationary = None
        elif 0.0 < stationary < 1.0:
            proposals.append((stationary, 'stationary'))
    if beta1 != 0.0:
        boundary = -beta0 / beta1
        if not math.isfinite(boundary):
            flags['nonfinite_B_boundary_ratio'] = True
            boundary = None
        elif 0.0 < boundary < 1.0:
            proposals.append((boundary, 'B_zero_boundary'))
    sources = {}
    for eta, source in proposals:
        sources.setdefault(eta, []).append(source)
    candidates = []
    for eta in sorted(sources):
        candidate = _weight_value(eta, b1, b2, M11, M12, M22)
        candidate['sources'] = sources[eta]
        candidates.append(candidate)
    selected = min(candidates, key=lambda x: (-x['J'], x['eta']))
    unresolved = any(flags[k] for k in ('near_A0_cancellation', 'near_A1_cancellation',
        'nonfinite_stationary_ratio', 'nonfinite_B_boundary_ratio'))
    return dict(coefficients=dict(b1=b1, b2=b2, M11=M11, M12=M12, M22=M22,
            beta0=beta0, beta1=beta1, m0=m0, m1=m1, m2=m2, A0=A0, A1=A1),
        stationary_ratio=stationary, B_boundary_ratio=boundary, flags=flags,
        candidates=candidates, selected=dict(selected), attempts=len(candidates),
        candidate_proposals=len(proposals), duplicate_candidates=len(proposals) - len(candidates),
        floating_point_classification_unresolved=unresolved,
        exact_real_inner_optimality_certified=False, cancellation_diagnostic_ulps=32)


def search_one(state, h, physics, emit, counters, deadline_ns):
    """Run one complete fixed bounded search; caller independently qualifies output.

    physics.gram(g1,g2) -> float; physics.cross(state,g,128) -> {total,ordered_pairs}.
    physics owns phys_* numerical-work counters. search_* counts include actual
    API calls separately, without adding them to physics-work totals.
    """
    h = _finite(h, 'h')
    if h <= 0:
        raise ValueError('step must be positive')
    local = dict.fromkeys(COUNTER_KEYS, 0)

    def check_time():
        if time.perf_counter_ns() >= deadline_ns:
            raise TimeoutError('T70 search deadline')

    def charge(key, amount=1, cap=None):
        value = local[key] + amount
        if cap is not None and value > cap:
            raise ArithmeticError(key + ' exceeds fixed T69 work cap')
        local[key] = value
        counters[key] = counters.get(key, 0) + amount

    def event(kind, data):
        check_time()
        emit(kind, data)

    def ranked(records):
        charge('search_rank_operations')
        charge('search_ranked_records', len(records))
        return sorted(records, key=_rank)

    check_time()
    charge('search_invocations')
    Gamma = _finite(state['Gamma'], 'current Gamma')
    eta = _finite(state['eta'], 'current eta')
    if Gamma <= 0 or not 0.0 <= eta <= 1.0 or len(state['geometry']) != 2:
        raise ValueError('current state must be a nonzero positive two-component mixture')
    geometries = tuple(_geometry(g) for g in state['geometry'])
    original = dict(Gamma=Gamma, eta=eta, geometry=[list(g) for g in geometries])
    active = [(geometries[0], 1.0 - eta), (geometries[1], eta)]
    active = [(g, w) for g, w in active if w > 0]
    if len(active) == 2 and active[0][0] == active[1][0]:
        active = [(active[0][0], 1.0)]
    active.sort(key=lambda x: _key(x[0]))
    if len(active) == 1:
        current_pair = (active[0][0], active[0][0])
        current_eta = 0.0
    else:
        current_pair = (active[0][0], active[1][0])
        current_eta = active[1][1]
    current = dict(Gamma=Gamma, eta=current_eta, geometry=[list(g) for g in current_pair])
    a = math.fsum(w * g[2] for g, w in active)
    R = math.sqrt(math.fsum(w * g[0] * g[0] for g, w in active))
    Z = math.sqrt(math.fsum(w * (g[1] * g[1] + (g[2] - a)**2) for g, w in active))
    if not all(math.isfinite(x) for x in (a, R, Z)) or R <= 0 or Z <= 0:
        raise ArithmeticError('invalid current-state search scales')
    bounds = ((min(.5 * R, min(g[0] for g, _ in active)), max(1.5 * R, max(g[0] for g, _ in active))),
        (min(.5 * Z, min(g[1] for g, _ in active)), max(1.5 * Z, max(g[1] for g, _ in active))),
        (min(a - 1.5 * Z, min(g[2] for g, _ in active)), max(a + 1.5 * Z, max(g[2] for g, _ in active))))
    bank_sources = {}
    for radial in (.75, 1.0, 1.25):
        for axial in (.75, 1.0, 1.25):
            for offset in (-1.0, -.5, 0.0, .5, 1.0):
                g = (radial * R, axial * Z, a + offset * Z)
                bank_sources.setdefault(g, []).append('relative_bank')
    for index, (g, _) in enumerate(active):
        bank_sources.setdefault(g, []).append('active_' + str(index))
    bank = sorted(bank_sources, key=_key)
    if not 45 <= len(bank) <= 47:
        raise ArithmeticError('unexpected exact-deduplicated bank size')
    event('search_started', dict(h=h, original_state=original, current_state=current,
        active_components=[dict(geometry=list(g), weight=w) for g, w in active],
        scales=dict(a=a, R=R, Z=Z), bounds=[list(x) for x in bounds],
        bank=[list(g) for g in bank], bank_sources=[bank_sources[g] for g in bank]))
    basis_cache, pair_cache = {}, {}
    records = []

    def basis(g):
        check_time()
        charge('search_component_requests')
        if g in basis_cache:
            charge('search_component_cache_hits')
            return basis_cache[g]
        charge('search_component_evaluations', cap=1199)
        gram_terms = []
        for current_g, weight in active:
            check_time()
            charge('search_current_gram_calls')
            value = _finite(physics.gram(current_g, g), 'current Gram')
            gram_terms.append(dict(geometry=list(current_g), weight=weight, gram=value))
        q_cross = Gamma * math.fsum(t['weight'] * t['gram'] for t in gram_terms)
        charge('search_cross_calls')
        cross = physics.cross(current, g, 128)
        F_cross = _finite(cross['total'], 'F cross')
        if not isinstance(cross['ordered_pairs'], list):
            raise TypeError('physics.cross ordered_pairs must be a list')
        b = math.fsum((q_cross, h * F_cross))
        if not math.isfinite(b):
            raise ArithmeticError('nonfinite target cross product')
        packet = dict(geometry=list(g), q_cross=q_cross, F_cross=F_cross, b=b,
            current_gram_terms=gram_terms, physics_cross=cross)
        basis_cache[g] = packet
        event('search_component_basis', packet)
        return packet

    def pair_coefficients(pair):
        first, second = basis(pair[0]), basis(pair[1])
        values = []
        for left, right in ((pair[0], pair[0]), (pair[0], pair[1]), (pair[1], pair[1])):
            check_time()
            charge('search_candidate_gram_calls')
            values.append(_finite(physics.gram(left, right), 'candidate Gram'))
        return first['b'], second['b'], values[0], values[1], values[2]

    # The unchanged tuple is evaluated at its original scale, never refitted.
    cb1, cb2, cm11, cm12, cm22 = pair_coefficients(current_pair)
    charge('search_control_attempts')
    control_B, control_M = _barycentric(current_eta, cb1, cb2, cm11, cm12, cm22)
    control_J = math.fsum((2.0 * Gamma * control_B, -Gamma * Gamma * control_M))
    if not math.isfinite(control_J):
        raise ArithmeticError('nonfinite unchanged-state control')
    control = dict(original_Gamma=Gamma, original_eta=eta, current_state=current,
        original_state=original, eta=current_eta, Gamma=Gamma, B=control_B, M=control_M,
        J=control_J, scale_refitted=False)
    event('search_unchanged_control', control)

    def propose(pair, source):
        check_time()
        charge('search_proposals', cap=2280)
        charge('search_initial_proposals' if source['phase'] == 'bank' else 'search_neighbor_proposals',
            cap=1128 if source['phase'] == 'bank' else 1152)
        proposal_index = local['search_proposals'] - 1
        pair = _canonical_pair(pair)
        packet = dict(proposal_index=proposal_index, source=source, geometry=[list(g) for g in pair])
        if not all(math.isfinite(g[k]) and bounds[k][0] <= g[k] <= bounds[k][1]
                   for g in pair for k in range(3)):
            charge('search_rejected_proposals')
            event('search_proposal_rejected', packet)
            return None
        if pair in pair_cache:
            charge('search_pair_cache_hits')
            record = pair_cache[pair]
            event('search_pair_cache_hit', dict(packet, evaluation_index=record['evaluation_index']))
            return record
        charge('search_pair_evaluations')
        coefficients = pair_coefficients(pair)
        weights = solve_weights(*coefficients)
        charge('search_weight_attempts', weights['attempts'], cap=9120)
        charge('search_weight_candidates_before_dedup', weights['candidate_proposals'])
        charge('search_duplicate_weight_candidates', weights['duplicate_candidates'])
        if weights['floating_point_classification_unresolved']:
            charge('search_inner_unresolved_pairs')
        chosen = weights['selected']
        record = dict(evaluation_index=len(records), geometry=[list(g) for g in pair],
            eta=chosen['eta'], Gamma=chosen['Gamma'], B=chosen['B'], M=chosen['M'], J=chosen['J'],
            positive_scale=chosen['positive_scale'], weights=weights)
        pair_cache[pair] = record
        records.append(record)
        event('search_pair_evaluated', dict(packet, record=record))
        return record

    for i, first in enumerate(bank):
        for j in range(i, len(bank)):
            propose((first, bank[j]), dict(phase='bank', i=i, j=j))
    expected_bank_proposals = len(bank) * (len(bank) + 1) // 2
    if local['search_initial_proposals'] != expected_bank_proposals:
        raise AssertionError('bank traversal incomplete')
    starts = ranked([x for x in records if x['positive_scale']])[:4]
    start_indices = [x['evaluation_index'] for x in starts]
    event('search_local_starts', dict(evaluation_indices=start_indices))
    polls = []
    for start_index, start in enumerate(starts):
        center = start
        for level, steps in enumerate(((.10 * R, .10 * Z, .20 * Z),
                                      (.05 * R, .05 * Z, .10 * Z),
                                      (.025 * R, .025 * Z, .05 * Z))):
            for poll in range(8):
                check_time()
                before = center
                improvements = []
                for component in range(2):
                    for coordinate in range(3):
                        for direction in (-1, 1):
                            pair = [list(g) for g in before['geometry']]
                            pair[component][coordinate] += direction * steps[coordinate]
                            result = propose(tuple(tuple(g) for g in pair), dict(phase='neighbor',
                                start=start_index, level=level, poll=poll, component=component,
                                coordinate=coordinate, direction=direction, center=before['evaluation_index']))
                            if result is not None and result['positive_scale'] and result['J'] > before['J']:
                                improvements.append(result)
                charge('search_poll_count')
                if improvements:
                    center = ranked(improvements)[0]
                    charge('search_strict_moves')
                packet = dict(start=start_index, level=level, poll=poll, steps=list(steps),
                    center_before=before['evaluation_index'], center_after=center['evaluation_index'],
                    improved=bool(improvements), proposals=12)
                polls.append(packet)
                event('search_poll_completed', packet)
                if not improvements:
                    break
    eligible = ranked([x for x in records if x['positive_scale']])
    selected = eligible[0] if eligible else None
    selected_state = None if selected is None else dict(Gamma=selected['Gamma'], eta=selected['eta'],
        geometry=selected['geometry'])
    if local['search_proposals'] != (local['search_rejected_proposals'] +
            local['search_pair_cache_hits'] + local['search_pair_evaluations']):
        raise AssertionError('proposal accounting mismatch')
    if local['search_weight_attempts'] + local['search_control_attempts'] > 9121:
        raise AssertionError('weight/control accounting exceeds contract')
    summary = dict(bank_size=len(bank), bank_proposals=expected_bank_proposals,
        evaluated_pairs=len(records), eligible_pairs=len(eligible), local_starts=len(starts),
        selected_index=None if selected is None else selected['evaluation_index'],
        scheduled_search_completed=True, early_success_shortcut=False,
        bounded_search_only=True, exact_real_inner_optimality_certified=False,
        global_geometry_optimality_certified=False,
        floating_point_unresolved_pairs=local['search_inner_unresolved_pairs'],
        selected_classification_unresolved=None if selected is None else
            selected['weights']['floating_point_classification_unresolved'])
    result = dict(schema=SCHEMA, status='completed_bounded_search' if selected is not None else 'no_positive_candidate',
        h=h, original_state=original, current_state=current,
        active_components=[dict(geometry=list(g), weight=w) for g, w in active],
        search_scales=dict(a=a, R=R, Z=Z), search_bounds=[list(x) for x in bounds],
        bank=[list(g) for g in bank], bank_sources=[bank_sources[g] for g in bank],
        control=control, selected_state=selected_state, selected_record=selected,
        start_indices=start_indices, polls=polls, counters=dict(local), summary=summary)
    event('search_completed', dict(status=result['status'], selected_state=selected_state,
        summary=summary, counters=dict(local)))
    return result
