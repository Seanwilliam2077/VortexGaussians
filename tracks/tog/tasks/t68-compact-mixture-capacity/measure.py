"""Single frozen T68 ordinary mixture experiment; no historical scientific imports."""
import datetime
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import platform
import sys
import time
import traceback
from contextlib import contextmanager

START = time.perf_counter()
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
LOCAL = ROOT / 'local'
OLD = ROOT.parent / 't60-full-window-gaussian-screen'
np = None
solve_weights = None
STREAM = None
BEFORE = {}
CHECKS = {}
PHASES = {}
PARTIAL = {}
ACTIVE = 'initialization'
CAPS = {}
COUNTERS = dict(input_bytes_hashed_before=0, input_bytes_hashed_after=0,
    input_npz_files=0, input_arrays=0, rule_count=0, rule_nodes=0, rule_eigh_calls=0,
    polynomial_integrals=0, reference_polynomial_node_cells=0, reference_corner_cells=0,
    control_primary_contractions=0, control_additional_axis_exponentials=0,
    control_additional_diagonal_gram_axis_products=0, control_additional_three_term_cell_visits=0,
    initial_geometry_proposals=0, neighbor_geometry_proposals=0, geometry_proposals=0,
    geometry_evaluations=0, geometry_cache_hits=0, rejected_geometry_proposals=0,
    distinct_S256_components=0, component_basis_cache_hits=0,
    search_component_axis_exponentials=0, search_three_term_reference_cell_visits=0,
    search_diagonal_gram_axis_products=0, search_cross_gram_axis_products=0,
    exact_polynomial_long_divisions=0, root_isolation_nodes=0, rational_operations=0,
    weight_attempts=0, search_original_moment_checks=0,
    fixed_control_selected_moment_routes=0, fixed_model_reference_route_gate_comparisons=0,
    direct_control_integrals=0, direct_selected_integrals=0,
    direct_integrals_started=0, direct_integrals_completed=0,
    direct_reference_model_node_cells=0, direct_component_point_evaluations=0,
    direct_diagnostic_reductions=0)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def clock():
    if time.perf_counter() - START >= 120.:
        raise TimeoutError('fixed child deadline exhausted')


def charge(key, amount=1):
    COUNTERS[key] = COUNTERS.get(key, 0) + amount
    limit = CAPS.get(key + '_max', CAPS.get(key))
    if limit is not None:
        require(COUNTERS[key] <= limit, 'work cap exceeded: ' + key)


def event(kind, **values):
    if STREAM is not None:
        STREAM.write(json.dumps(dict(kind=kind, elapsed_seconds=time.perf_counter()-START,
                                     **values), allow_nan=False) + '\n')
        STREAM.flush()


@contextmanager
def phase(name):
    global ACTIVE
    ACTIVE = name
    begin = time.perf_counter()
    event('phase_started', name=name, counters=dict(COUNTERS))
    try:
        clock()
        yield
    finally:
        elapsed = time.perf_counter() - begin
        PHASES[name] = PHASES.get(name, 0.) + elapsed
        event('phase_finished', name=name, seconds=elapsed, counters=dict(COUNTERS))


def identity(path, counter=None):
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            clock()
            digest.update(block)
            size += len(block)
    if counter:
        charge(counter, size)
    return dict(bytes=size, sha256=digest.hexdigest())


def read_json(path):
    require(path.resolve() in BEFORE, 'JSON is not frozen: ' + str(path))
    def invalid(value):
        raise ValueError('nonfinite JSON: ' + value)
    return json.loads(path.read_text(encoding='utf-8'), parse_constant=invalid)


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def close(actual, expected, label):
    a, b = np.asarray(actual), np.asarray(expected)
    require(a.shape == b.shape and bool(np.all(np.isfinite(a)))
            and bool(np.all(np.isfinite(b)))
            and bool(np.allclose(a, b, rtol=3e-11, atol=3e-14)), label)


def freeze():
    path = ROOT / 'input-manifest.json'
    raw = path.read_bytes()
    manifest = json.loads(raw)
    require(manifest['schema'] == 't68-compact-mixture-capacity-freeze-v1', 'freeze schema')
    fixed = dict(expected_python='3.12.14', expected_numpy='2.3.5',
        maximum_scientific_child_invocations=1, child_timeout_seconds=120,
        observed_peak_working_set_limit_bytes=536870912,
        required_available_physical_bytes=1073741824, memory_sample_interval_seconds=.25,
        expected_input_npz_files=2, expected_input_arrays=12,
        prior_scientific_child_seconds=1980.2512354997452,
        preparation_scientific_invocations=0, T60_history_reclassified=False)
    require(all(manifest.get(k) == v for k, v in fixed.items()), 'fixed manifest limits')
    admitted = {}
    for item in manifest['inputs']:
        value = item['path']
        require(isinstance(value, str) and value and '\\' not in value and ':' not in value
                and not value.startswith('/')
                and all(x not in ('', '.', '..') for x in value.split('/')), 'invalid input path')
        target = (REPO / value).resolve()
        require(target.is_relative_to(REPO) and target not in admitted, 'duplicate or escaping input')
        admitted[target] = {k: item[k] for k in ('bytes', 'sha256')}
    raw_paths = {p for p in admitted if p.suffix.lower() in ('.npz', '.npy')}
    require(raw_paths == {(OLD / 'local' / (n + '-snapshot-4.npz')).resolve()
                          for n in ('S256', 'S128')}, 'exact two-array-file input whitelist')
    executable = Path(manifest['executable']['path']).resolve()
    require(executable == Path(sys.executable).resolve(), 'runtime executable')
    admitted[executable] = {k: manifest['executable'][k] for k in ('bytes', 'sha256')}
    for target, expected in admitted.items():
        actual = identity(target, 'input_bytes_hashed_before')
        require(actual == expected, 'frozen input mismatch: ' + str(target))
        BEFORE[target] = actual
    BEFORE[path.resolve()] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    charge('input_bytes_hashed_before', len(raw))
    return manifest


def rules():
    result = {}
    for n in (3, 2, 8, 6, 16, 12):
        clock()
        k = np.arange(1, n, dtype=np.float64)
        off = k / np.sqrt(4. * k * k - 1.)
        jacobi = np.diag(off, 1) + np.diag(off, -1)
        event('rule_eigh_started', order=n)
        x, vectors = np.linalg.eigh(jacobi)
        charge('rule_eigh_calls')
        w = 2. * vectors[0, :] ** 2
        require(x.shape == w.shape == (n,) and bool(np.all(np.isfinite(x)))
                and bool(np.all(np.isfinite(w))) and bool(np.all(np.diff(x) > 0.))
                and bool(np.all(np.abs(x) < 1.)) and bool(np.all(w > 0.))
                and abs(float(np.sum(w)) - 2.) <= 1e-13
                and bool(np.all(np.abs(x + x[::-1]) <= 1e-13))
                and bool(np.all(np.abs(w - w[::-1]) <= 1e-13)), 'quadrature qualification')
        result[n] = x, w
        charge('rule_count')
        charge('rule_nodes', n)
        event('rule_constructed', order=n, nodes=x.tolist(), weights=w.tolist(),
              eigensolver='numpy.linalg.eigh', symmetric_matrix_order=n)
    return result


def load_field(name, n):
    metadata = read_json(OLD / 'local' / f'{name}-snapshot-4.json')
    require((metadata['name'], metadata['index'], metadata['time'], metadata['nr'],
             metadata['nz'], metadata['R']) == (name, 4, 1., n, 2*n, 8.), 'endpoint metadata')
    h = metadata['h']
    require(h == 8./n and metadata['raw']['path'] == f'{name}-snapshot-4.npz', 'grid/path identity')
    path = OLD / 'local' / metadata['raw']['path']
    require(BEFORE[path.resolve()] == {k: metadata['raw'][k] for k in ('bytes', 'sha256')},
            'snapshot identity')
    f = {}
    with np.load(path, allow_pickle=False) as archive:
        charge('input_npz_files')
        for key in ('q', 'qr', 'qz', 'r', 'rc', 'z'):
            value = archive[key]
            charge('input_arrays')
            shape = (n, 2*n) if key in ('q', 'qr', 'qz') else ((2*n,) if key == 'z' else (n,))
            require(value.shape == shape and value.dtype == np.dtype('float64')
                    and bool(np.all(np.isfinite(value))), 'array type/layout: ' + key)
            f[key] = value
            event('array_decoded', reference=name, key=key, shape=list(value.shape), bytes=value.nbytes)
    rf = np.arange(n+1) * h
    zf = -8. + np.arange(2*n+1) * h
    area = (rf[1:]**2 - rf[:-1]**2)/2.
    expected = dict(r=(rf[:-1]+rf[1:])/2., z=(zf[:-1]+zf[1:])/2.,
                    rc=(rf[1:]**3-rf[:-1]**3)/(3.*area))
    for key, value in expected.items():
        require(bool(np.all(np.diff(f[key]) > 0.)) and np.array_equal(f[key], value),
                'coordinate identity: ' + key)
    require(bool(np.all(f['q'] >= 0.)), 'negative cell average')
    minimum = math.inf
    for radial in (rf[:-1], rf[1:]):
        for axial in (-h/2., h/2.):
            clock()
            corner = f['q'] + f['qr']*(radial-f['rc'])[:, None] + f['qz']*axial
            charge('reference_corner_cells', n*2*n)
            minimum = min(minimum, float(np.min(corner)))
            require(bool(np.all(np.isfinite(corner))) and bool(np.all(corner >= 0.)), 'PL corner positivity')
    f.update(name=name, n=n, h=h, statistics=metadata['statistics'], minimum_corner=minimum)
    return f


def samples(f, xr, xz):
    h = f['h']
    rn, zn = f['r'] + xr*h/2., f['z'] + xz*h/2.
    q = f['q'] + f['qr']*(rn-f['rc'])[:, None] + f['qz']*(zn-f['z'])[None, :]
    require(bool(np.all(np.isfinite(q))) and bool(np.all(q >= 0.)), 'PL node positivity')
    return rn, zn, q


def polynomial(f, rule):
    totals = np.zeros(9)
    for xr, wr in zip(*rule[3]):
        for xz, wz in zip(*rule[2]):
            clock()
            rn, zn, q = samples(f, xr, xz)
            r, z = rn[:, None], zn[None, :]
            w = wr*wz*f['h']**2/4.*r
            density = w*q
            totals += np.array([np.sum(density), np.sum(density*r), np.sum(density*z),
                np.sum(density*r*r), np.sum(density*r*z), np.sum(density*z*z),
                2.*math.pi*np.sum(w*q*q), math.pi*np.sum(density*r*r),
                2.*math.pi*np.sum(w*r*r*q*q)])
            charge('reference_polynomial_node_cells', f['q'].size)
    gamma = float(totals[0])
    require(gamma > 0. and totals[8] > 0., 'positive polynomial norms')
    mean = totals[1:3]/gamma
    cov = np.array([[totals[3], totals[4]], [totals[4], totals[5]]])/gamma - np.outer(mean, mean)
    record = dict(circulation=gamma, centroid=mean.tolist(), covariance=cov.tolist(),
        q_squared_integral=float(totals[6]), axial_impulse=float(totals[7]),
        vorticity_squared_integral=float(totals[8]), minimum_corner=f['minimum_corner'])
    for key in ('circulation', 'centroid', 'covariance', 'q_squared_integral',
                'axial_impulse', 'vorticity_squared_integral'):
        close(record[key], f['statistics'][key], 'reference readback: '+f['name']+'/'+key)
    f['C'] = record['vorticity_squared_integral']
    charge('polynomial_integrals')
    event('reference_qualified', reference=f['name'], statistics=record)
    return record


def component_key(g):
    return g[2], g[0], g[1]


def canonical(pair):
    return tuple(sorted((tuple(pair[0]), tuple(pair[1])), key=component_key))


def pair_key(pair):
    return tuple(component_key(g) for g in pair)


def component_moments(g):
    sr, sz, z = g
    mean = (math.sqrt(math.pi/2.)*sr, z)
    cov = (((4.-math.pi)/2.*sr*sr, 0.), (0., sz*sz))
    raw = ((2.*sr*sr, mean[0]*z), (mean[0]*z, sz*sz+z*z))
    return mean, cov, raw


def model_moments(pair, eta, route='between'):
    m1, c1, q1 = component_moments(pair[0])
    m2, c2, q2 = component_moments(pair[1])
    d = tuple(m2[i]-m1[i] for i in range(2))
    mean = [m1[i]+eta*d[i] for i in range(2)]
    if route == 'between':
        cov = [[math.fsum(((1.-eta)*c1[i][j], eta*c2[i][j],
                          eta*(1.-eta)*d[i]*d[j])) for j in range(2)] for i in range(2)]
    else:
        require(route == 'raw', 'moment route')
        cov = [[math.fsum(((1.-eta)*q1[i][j], eta*q2[i][j], -mean[i]*mean[j]))
                for j in range(2)] for i in range(2)]
    require(all(math.isfinite(v) for v in mean + [v for row in cov for v in row]), 'finite mixture moments')
    return dict(centroid=mean, covariance=cov)


def moment_gates(moments, reference, D0):
    axial = abs(moments['centroid'][1] - reference['centroid'][1])
    cov = math.sqrt(math.fsum((moments['covariance'][i][j]-reference['covariance'][i][j])**2
                              for i in range(2) for j in range(2)))/D0
    return dict(axial_centroid_error=axial, normalized_covariance_error=cov,
        axial_centroid_pass=axial <= .1, covariance_pass=cov <= .1,
        joint_moment_pass=axial <= .1 and cov <= .1)


def covariance_polynomial(pair, reference, D0):
    m1, c1, _ = component_moments(pair[0])
    m2, c2, _ = component_moments(pair[1])
    d = [m2[i]-m1[i] for i in range(2)]
    h0 = [c1[i][j]-reference['covariance'][i][j] for i in range(2) for j in range(2)]
    h1 = [c2[i][j]-c1[i][j]+d[i]*d[j] for i in range(2) for j in range(2)]
    h2 = [-d[i]*d[j] for i in range(2) for j in range(2)]
    def dot(a, b):
        return math.fsum(x*y for x, y in zip(a, b))
    coeff = [dot(h0, h0)-(.1*D0)**2, 2.*dot(h0, h1),
             dot(h1, h1)+2.*dot(h0, h2), 2.*dot(h1, h2), dot(h2, h2)]
    require(all(math.isfinite(v) for v in coeff), 'finite covariance polynomial')
    return coeff, dict(H0=h0, H1=h1, H2=h2)


def primary_grid(f, rule):
    xr, wr = rule[8]
    xz, wz = rule[6]
    r = f['r'][:, None]+xr[None, :]*f['h']/2.
    z = f['z'][:, None]+xz[None, :]*f['h']/2.
    return dict(r=r, z=z, rw=wr[None, :]*f['h']/2.*r**3,
                zw=wz[None, :]*f['h']/2.)


def basis(f, g, scope, cache):
    g = tuple(g)
    if g in cache:
        charge('component_basis_cache_hits')
        return cache[g]
    clock()
    grid = f['primary_grid']
    sr, sz, z0 = g
    fr = np.exp(-.5*(grid['r']/sr)**2)/(sr*sr)
    fz = np.exp(-.5*((grid['z']-z0)/sz)**2)/(math.sqrt(2.*math.pi)*sz)
    axis_count = 8*f['n']+6*2*f['n']
    expkey = 'control_additional_axis_exponentials' if scope == 'control' else 'search_component_axis_exponentials'
    cellkey = 'control_additional_three_term_cell_visits' if scope == 'control' else 'search_three_term_reference_cell_visits'
    gramkey = 'control_additional_diagonal_gram_axis_products' if scope == 'control' else 'search_diagonal_gram_axis_products'
    charge(expkey, axis_count)
    require(bool(np.all(np.isfinite(fr))) and bool(np.all(np.isfinite(fz)))
            and bool(np.all(fr > 0.)) and bool(np.all(fz > 0.)), 'positive component axis values')
    R3 = np.sum(grid['rw']*fr, axis=1)
    Rc = np.sum(grid['rw']*(grid['r']-f['rc'][:, None])*fr, axis=1)
    Z0 = np.sum(grid['zw']*fz, axis=1)
    Zc = np.sum(grid['zw']*(grid['z']-f['z'][:, None])*fz, axis=1)
    b = 2.*math.pi*math.fsum((float(R3@(f['q']@Z0)), float(Rc@(f['qr']@Z0)),
                             float(R3@(f['qz']@Zc))))
    charge(cellkey, 3*f['n']*2*f['n'])
    M = 2.*math.pi*float(np.sum(grid['rw']*fr*fr))*float(np.sum(grid['zw']*fz*fz))
    charge(gramkey, axis_count)
    require(all(math.isfinite(v) and v > 0. for v in (b, M)), 'positive component b/M')
    record = dict(fr=fr, fz=fz, b=b, M=M, origin=scope)
    cache[g] = record
    if f['name'] == 'S256':
        charge('distinct_S256_components')
    event('component_basis', reference=f['name'], geometry=list(g), origin=scope,
          b=b, M=M, axis_points=axis_count, three_term_cell_visits=3*f['q'].size)
    return record


def cross_gram(f, a, b):
    grid = f['primary_grid']
    value = 2.*math.pi*float(np.sum(grid['rw']*a['fr']*b['fr']))*float(np.sum(grid['zw']*a['fz']*b['fz']))
    charge('search_cross_gram_axis_products', 8*f['n']+6*2*f['n'])
    require(math.isfinite(value) and value > 0., 'positive cross Gram')
    require(value*value <= (1.+1e-12)*a['M']*b['M'], 'pair Cauchy arithmetic check')
    return value


def direct(f, params, orders, rule, label):
    clock()
    require(COUNTERS['direct_integrals_started'] < 8, 'direct integral cap')
    charge('direct_integrals_started')
    begin = time.perf_counter()
    sums = [[], [], [], []]
    pair, eta, gamma = params['geometry'], params['eta'], params['Gamma']
    pieces = [(pair[0], 1.-eta), (pair[1], eta)]
    if pair[0] == pair[1]:
        pieces = [(pair[0], 1.)]
    pieces = [(g, w) for g, w in pieces if w != 0.]
    for xr, wr in zip(*rule[orders[0]]):
        for xz, wz in zip(*rule[orders[1]]):
            clock()
            rn, zn, q = samples(f, xr, xz)
            model = np.zeros_like(q)
            for (sr, sz, z0), mixture_weight in pieces:
                N = sr*sr*math.sqrt(2.*math.pi)*sz
                component = np.exp(-.5*((rn[:, None]/sr)**2+((zn[None, :]-z0)/sz)**2))/N
                charge('direct_component_point_evaluations', q.size)
                require(bool(np.all(np.isfinite(component))) and bool(np.all(component > 0.)),
                        'positive direct component')
                model += gamma*mixture_weight*component
            require(bool(np.all(np.isfinite(model))) and bool(np.all(model > 0.)), 'positive direct model')
            weight = rn[:, None]*f['h']**2*wr*wz/4.
            physical = 2.*math.pi*rn[:, None]**2*weight
            sums[0].append(float(np.sum(physical*(model-q)**2)))
            sums[1].append(float(np.sum(physical*q*q)))
            sums[2].append(float(np.sum(weight*model)))
            sums[3].append(float(np.sum(math.pi*rn[:, None]**2*weight*model)))
            charge('direct_diagnostic_reductions', 2)
            charge('direct_reference_model_node_cells', q.size)
    numerator, denominator, circulation, impulse = (math.fsum(v) for v in sums)
    require(all(math.isfinite(v) for v in (numerator, denominator, circulation, impulse))
            and numerator >= 0. and denominator > 0., 'direct finite positive norms')
    close(denominator, f['C'], 'direct reference denominator')
    charge('direct_integrals_completed')
    charge('direct_control_integrals' if label == 'control' else 'direct_selected_integrals')
    record = dict(reference=f['name'], label=label, orders=list(orders), numerator=numerator,
        denominator=denominator, relative_error=math.sqrt(numerator/denominator),
        D8_circulation=circulation, D8_axial_impulse=impulse,
        node_cell_points=q.size*orders[0]*orders[1], seconds=time.perf_counter()-begin)
    event('direct_score', **record)
    return record


def score_pair(f, params, rule, label):
    primary = direct(f, params, (8, 6), rule, label)
    confirmation = direct(f, params, (16, 12), rule, label)
    difference = abs(primary['relative_error']-confirmation['relative_error'])
    require(difference <= 1e-9, label+' direct rule disagreement')
    for key in ('D8_circulation', 'D8_axial_impulse'):
        close(primary[key], confirmation[key], label+' diagnostic rule agreement: '+key)
    return dict(primary_8x6=primary, confirmation_16x12=confirmation, rule_difference=difference)


def fixed_moment_routes(params, fields, D0, label):
    routes = {}
    for route in ('between', 'raw'):
        routes[route] = model_moments(params['geometry'], params['eta'], route)
        charge('fixed_control_selected_moment_routes')
    for key in ('centroid', 'covariance'):
        close(routes['between'][key], routes['raw'][key], label+' independent moment route: '+key)
    gates = {}
    for name, f in fields.items():
        gates[name] = {}
        for route, value in routes.items():
            gates[name][route] = moment_gates(value, f['statistics'], D0)
            charge('fixed_model_reference_route_gate_comparisons')
    gamma, eta, pair = params['Gamma'], params['eta'], params['geometry']
    impulse = 2.*math.pi*gamma*math.fsum(((1.-eta)*pair[0][0]**2, eta*pair[1][0]**2))
    diagnostics = {name: dict(circulation_difference=gamma-f['statistics']['circulation'],
        axial_impulse_difference=impulse-f['statistics']['axial_impulse']) for name, f in fields.items()}
    return dict(routes=routes, gates=gates, fullspace_circulation=gamma,
        fullspace_axial_impulse=impulse, diagnostics=diagnostics)


def add_solver_counts(result):
    counts = result['counters']
    for target, source in (('exact_polynomial_long_divisions', 'polynomial_long_divisions'),
                           ('root_isolation_nodes', 'isolation_nodes'),
                           ('rational_operations', 'rational_operations'),
                           ('weight_attempts', 'weight_attempts')):
        require(type(counts[source]) is int and counts[source] >= 0, 'solver counter: '+source)
        charge(target, counts[source])
    for key in ('max_depth', 'max_rational_bits', 'max_sturm_chain_length'):
        value = counts[key]
        require(type(value) is int and value >= 0, 'solver maximum: '+key)
        target = 'root_' + key
        COUNTERS[target] = max(COUNTERS.get(target, 0), value)


def search(f, selected_control, D0, cache):
    evaluated = {}
    proposed_count = 0
    field_statistics = f['statistics']

    def candidate_key(record):
        candidate = record['best_candidate']
        return -candidate['J'], pair_key(record['geometry']), candidate['parameters']['eta']

    def evaluate(proposed, origin, initial=False):
        nonlocal proposed_count
        clock()
        proposed_count += 1
        charge('geometry_proposals')
        charge('initial_geometry_proposals' if initial else 'neighbor_geometry_proposals')
        pair = canonical(proposed)
        shell = dict(proposal_index=proposed_count-1, proposed_geometry=proposed,
                     canonical_geometry=pair, component_order_swapped=tuple(proposed) != pair, origin=origin)
        if any(not (.5 <= sr <= 1.5 and .5 <= sz <= 1.5 and -.5 <= z <= 1.5)
               for sr, sz, z in pair):
            charge('rejected_geometry_proposals')
            event('geometry_rejected', **shell, reason='outside_frozen_box')
            return None
        if pair in evaluated:
            charge('geometry_cache_hits')
            event('geometry_cache_hit', **shell, evaluation_index=evaluated[pair]['index'])
            return evaluated[pair] if evaluated[pair]['best_candidate'] is not None else None
        charge('geometry_evaluations')
        index = len(evaluated)
        event('geometry_started', **shell, evaluation_index=index)
        a, b = basis(f, pair[0], 'search', cache), basis(f, pair[1], 'search', cache)
        M12 = cross_gram(f, a, b)
        primary = dict(b1=a['b'], b2=b['b'], M11=a['M'], M12=M12, M22=b['M'])
        coefficients, h_entries = covariance_polynomial(pair, field_statistics, D0)
        try:
            inner = solve_weights(coefficients,
                dict(z1=pair[0][2], z2=pair[1][2], mu_z=field_statistics['centroid'][1], tolerance=.1),
                primary, deadline_ns=int((START+120.)*1_000_000_000))
        except TimeoutError as exc:
            partial = getattr(exc, 'partial_result', None)
            if partial is not None:
                add_solver_counts(partial)
                event('geometry_deadline_partial', **shell, evaluation_index=index,
                      primary=primary, coefficients=coefficients, inner=partial)
            raise
        add_solver_counts(inner)
        checked = []
        best = None
        accepted_eta = set()
        discrepancies = []
        numerical_unresolved = []
        for point in inner['candidates']:
            clock()
            eta = point['eta']
            require(type(eta) is float and math.isfinite(eta) and 0. <= eta <= 1., 'solver candidate domain')
            moments = model_moments(pair, eta)
            charge('search_original_moment_checks')
            gates = moment_gates(moments, field_statistics, D0)
            record = dict(eta=eta, rounded_feasible=point['rounded_feasible'],
                          sources=point['sources'], moments=moments, gates=gates, objective=None)
            if gates['joint_moment_pass'] != point['rounded_feasible']:
                discrepancies.append(dict(eta=eta, rounded_feasible=point['rounded_feasible'],
                                          original_feasible=gates['joint_moment_pass']))
            if gates['joint_moment_pass']:
                w0, w1 = 1.-eta, eta
                B = math.fsum((w0*a['b'], w1*b['b']))
                M = math.fsum((w0*w0*a['M'], 2.*w0*w1*M12, w1*w1*b['M']))
                if not all(math.isfinite(v) and v > 0. for v in (B, M)):
                    record['unresolved_reason'] = 'nonpositive_or_nonfinite_B_M'
                    numerical_unresolved.append(record['unresolved_reason'])
                else:
                    gamma = B/M
                    J = B*B/M
                    numerator = f['C']-J
                    if not all(math.isfinite(v) for v in (gamma, J, numerator)) or gamma <= 0. or numerator < 0.:
                        record['unresolved_reason'] = 'nonfinite_or_negative_projected_residual'
                        numerical_unresolved.append(record['unresolved_reason'])
                    else:
                        objective = dict(J=J, B=B, M=M, C=f['C'], numerator=numerator,
                            relative_error=math.sqrt(numerator/f['C']),
                            parameters=dict(geometry=pair, eta=eta, Gamma=gamma),
                            moments=moments, gates=gates,
                            identical_components=pair[0] == pair[1], zero_weight=eta in (0., 1.))
                        record['objective'] = {k: objective[k] for k in ('J', 'B', 'M', 'C', 'numerator', 'relative_error')}
                        accepted_eta.add(eta)
                        if best is None or (-J, eta) < (-best['J'], best['parameters']['eta']):
                            best = objective
            checked.append(record)
        # The helper supplies explicit candidate groups for feasible boundaries,
        # isolated points and open intervals; no group is silently discarded.
        uncovered = []
        for group in inner['coverage_groups']:
            if not any(eta in accepted_eta for eta in group['candidate_etas']):
                uncovered.append(group['id'])
        complete = (inner['representable_candidate_construction_complete']
                    and not discrepancies and not numerical_unresolved and not uncovered)
        record = dict(index=index, geometry=pair, primary=primary,
            covariance_polynomial=coefficients, covariance_H=h_entries,
            inner=inner, original_candidates=checked, best_candidate=best,
            rounded_original_discrepancies=discrepancies, uncovered_feasible_groups=uncovered,
            numerical_unresolved_reasons=numerical_unresolved,
            root_isolation_complete_for_rounded_polynomial=inner['root_isolation_complete_for_rounded_polynomial'],
            representable_candidate_construction_complete=bool(complete))
        evaluated[pair] = record
        event('geometry_evaluated', **shell, record=record)
        return record if best is not None else None

    bank = list(itertools.product((.75, 1., 1.25), (.75, 1., 1.25), (-.5, 0., .5, 1., 1.5)))
    bank.append(tuple(selected_control[k] for k in ('sr', 'sz', 'z0')))
    require(len(bank) == len(set(bank)) == 46, 'fixed distinct initial bank')
    bank_records = {}
    for i in range(len(bank)):
        for j in range(i, len(bank)):
            result = evaluate((bank[i], bank[j]), dict(stage='bank', i=i, j=j), initial=True)
            if result is not None:
                bank_records[result['geometry']] = result
    require(COUNTERS['initial_geometry_proposals'] == 1081, 'complete bank enumeration')
    starts = sorted(bank_records.values(), key=candidate_key)[:4]
    event('local_starts', evaluation_indices=[x['index'] for x in starts],
          geometries=[x['geometry'] for x in starts])
    polls = []
    for start_index, start in enumerate(starts):
        current = start
        for level, (width_step, z_step) in enumerate(((.10, .20), (.05, .10), (.025, .05))):
            for poll in range(8):
                clock()
                center = current
                neighbors = []
                for axis in range(6):
                    for sign in (-1, 1):
                        proposed = [list(g) for g in center['geometry']]
                        proposed[axis//3][axis % 3] += sign*(z_step if axis % 3 == 2 else width_step)
                        result = evaluate(tuple(tuple(g) for g in proposed),
                            dict(stage='neighbor', start=start_index, level=level, poll=poll,
                                 axis=axis, sign=sign, center_index=center['index']))
                        if result is not None:
                            neighbors.append(result)
                neighbor = min(neighbors, key=candidate_key) if neighbors else None
                improved = neighbor is not None and neighbor['best_candidate']['J'] > center['best_candidate']['J']
                if improved:
                    current = neighbor
                log = dict(start=start_index, level=level, poll=poll, width_step=width_step,
                    axial_step=z_step, center_before=center['index'], center_after=current['index'],
                    improved=improved)
                polls.append(log)
                event('poll_completed', **log)
                if not improved:
                    break
    eligible = [x for x in evaluated.values() if x['best_candidate'] is not None]
    winner = min(eligible, key=candidate_key) if eligible else None
    selected = None if winner is None else dict(evaluation_index=winner['index'],
        geometry=winner['geometry'], **winner['best_candidate'],
        root_isolation_complete_for_rounded_polynomial=winner['root_isolation_complete_for_rounded_polynomial'],
        representable_candidate_construction_complete=winner['representable_candidate_construction_complete'])
    procedural = dict(evaluated_geometries=len(evaluated),
        root_isolation_complete_for_rounded_polynomial=all(x['root_isolation_complete_for_rounded_polynomial'] for x in evaluated.values()),
        representable_candidate_construction_complete=all(x['representable_candidate_construction_complete'] for x in evaluated.values()),
        root_unresolved_geometries=sum(not x['root_isolation_complete_for_rounded_polynomial'] for x in evaluated.values()),
        candidate_construction_incomplete_geometries=sum(not x['representable_candidate_construction_complete'] for x in evaluated.values()),
        rounded_original_discrepancy_geometries=sum(bool(x['rounded_original_discrepancies']) for x in evaluated.values()),
        numerical_unresolved_geometries=sum(bool(x['numerical_unresolved_reasons']) for x in evaluated.values()),
        rounded_empty_geometries=sum(bool(x['inner']['rounded_feasible_set_empty']) for x in evaluated.values()))
    summary = dict(initial_components=bank, initial_pairs=1081, proposals=COUNTERS['geometry_proposals'],
        local_start_indices=[x['index'] for x in starts], polls=polls,
        eligible_geometry_count=len(eligible), selected_index=None if winner is None else winner['index'],
        early_success_shortcut=False, global_geometry_optimality_certified=False,
        continuous_inner_optimality_certified=False)
    event('search_completed', summary=summary, procedural=procedural, selected=selected)
    return selected, summary, procedural


def check_counts(has_selected):
    fixed = dict(input_npz_files=2, input_arrays=12, rule_count=6, rule_nodes=47,
        rule_eigh_calls=6, polynomial_integrals=2, reference_polynomial_node_cells=983040,
        reference_corner_cells=655360, control_primary_contractions=2,
        initial_geometry_proposals=1081, direct_control_integrals=4,
        direct_selected_integrals=4 if has_selected else 0,
        fixed_control_selected_moment_routes=4 if has_selected else 2,
        fixed_model_reference_route_gate_comparisons=8 if has_selected else 4,
        direct_integrals_started=8 if has_selected else 4,
        direct_integrals_completed=8 if has_selected else 4,
        direct_reference_model_node_cells=78643200 if has_selected else 39321600)
    for key, expected in fixed.items():
        require(COUNTERS[key] == expected, 'fixed completed count: '+key)
    for key, value in CAPS.items():
        name = key[:-4] if key.endswith('_max') else key
        require(name in COUNTERS and COUNTERS[name] <= value, 'budget count: '+name)
    require(COUNTERS['geometry_proposals'] == COUNTERS['initial_geometry_proposals']+COUNTERS['neighbor_geometry_proposals'],
            'proposal partition')
    require(COUNTERS['geometry_proposals'] == COUNTERS['geometry_evaluations']+COUNTERS['geometry_cache_hits']+COUNTERS['rejected_geometry_proposals'],
            'evaluated/cache/rejected partition')
    require(COUNTERS['root_max_depth'] <= 64 and COUNTERS['root_max_rational_bits'] <= 8192
            and COUNTERS['root_max_sturm_chain_length'] <= 5, 'root retained-state caps')


def measure():
    global np, solve_weights
    with phase('imports_and_input_hashes'):
        require(platform.python_version() == '3.12.14', 'Python version')
        import numpy as numpy
        np = numpy
        require(np.__version__ == '2.3.5', 'NumPy version')
        manifest = freeze()
        contract = read_json(ROOT.parent / 't67-compact-mixture-contract' / 'evidence.json')
        require(manifest['count_caps'] == contract['future_measurement']['count_caps'], 'unchanged work caps')
        require(manifest['root_contract'] == contract['future_measurement']['root_contract'], 'unchanged root caps')
        CAPS.update(manifest['count_caps'])
        spec = importlib.util.spec_from_file_location('t68_weight_solver', ROOT / 'weight_solver.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        solve_weights = module.solve_weights
        qualification = read_json(ROOT.parent / 't61-saved-output-qualification' / 'result.json')
        require(qualification['accepted_saved_evidence'] is True and qualification['reference_qualified_full_window'] is True,
                'T61 separate reference qualification')
        old = read_json(OLD / 'result.json')
        require({k: qualification['original_numerical_result'][k] for k in ('bytes', 'sha256')}
                == BEFORE[(OLD / 'result.json').resolve()], 'T61 accepted original result identity')
        previous = read_json(ROOT.parent / 't63-endpoint-capacity' / 'result.json')
        require(previous['status'] == 'search_inconclusive' and previous['capacity_witness'] is False,
                'unchanged T63 historical meaning')
        selected_control = previous['selected']['parameters']
        CHECKS['frozen_inputs_and_prior_reference_qualification'] = True
    with phase('rules_and_reference_qualification'):
        rule = rules()
        fields = {name: load_field(name, n) for name, n in (('S256', 256), ('S128', 128))}
        references = {name: polynomial(f, rule) for name, f in fields.items()}
        initial = read_json(OLD / 'local' / 'S256.json')['snapshots'][0]['covariance']
        D0 = old['ordinary_model_screen']['actual_initial_S256_covariance_frobenius_norm']
        require(D0 == manifest['initial_S256_covariance_norm'] == 1.0882203729522952, 'original D0')
        close(math.sqrt(math.fsum(x*x for row in initial for x in row)), D0, 'initial covariance norm')
        for name, f in fields.items():
            for key in ('circulation', 'centroid', 'covariance', 'q_squared_integral', 'axial_impulse', 'vorticity_squared_integral'):
                close(references[name][key], previous['reference_checks'][name][key], 'T63 reference readback')
            f['primary_grid'] = primary_grid(f, rule)
        CHECKS['rules_and_original_reference_statistics'] = True
        PARTIAL['references'] = references
    cache = {name: {} for name in fields}
    with phase('fixed_T63_control'):
        g = tuple(selected_control[k] for k in ('sr', 'sz', 'z0'))
        gamma = selected_control['A']*g[0]**2*math.sqrt(2.*math.pi)*g[1]
        control = dict(geometry=(g, g), eta=0., Gamma=gamma)
        control_moments = fixed_moment_routes(control, fields, D0, 'control')
        control_scores = {}
        for name, f in fields.items():
            bas = basis(f, g, 'control', cache[name])
            numerator = math.fsum((f['C'], -2.*gamma*bas['b'], gamma*gamma*bas['M']))
            charge('control_primary_contractions')
            require(math.isfinite(numerator) and numerator >= 0., 'fixed control projected numerator')
            contraction = dict(B=bas['b'], M=bas['M'], C=f['C'], Gamma=gamma,
                numerator=numerator, relative_error=math.sqrt(numerator/f['C']), amplitude_refitted=False)
            scores = score_pair(f, control, rule, 'control')
            for name_rule in ('primary_8x6', 'confirmation_16x12'):
                require(abs(scores[name_rule]['relative_error']-previous['selected_scores'][name][name_rule]['relative_error']) <= 1e-9,
                        'fixed T63 selected field calibration')
            for route in ('between', 'raw'):
                for key in ('centroid', 'covariance'):
                    close(control_moments['routes'][route][key], previous['selected_scores'][name]['moments'][key],
                          'fixed T63 moment calibration')
            discrepancy = abs(contraction['relative_error']-scores['primary_8x6']['relative_error'])
            require(discrepancy <= 1e-9, 'fixed control contraction/direct agreement')
            scores.update(contraction=contraction, contraction_direct_difference=discrepancy)
            control_scores[name] = scores
        CHECKS['unchanged_T63_control_and_primary_contractions'] = True
        PARTIAL.update(control=control, control_scores=control_scores, control_moments=control_moments)
    with phase('fixed_geometry_and_weight_search'):
        selected, summary, procedural = search(fields['S256'], selected_control, D0, cache['S256'])
        CHECKS['prescribed_search_completed'] = True
        PARTIAL.update(selected=selected, search_summary=summary, geometry_procedural_summary=procedural)
    selected_scores, selected_moments, sensitivity = {}, None, None
    selected_contraction_difference = None
    with phase('fixed_selected_confirmation'):
        if selected is not None:
            params = selected['parameters']
            selected_moments = fixed_moment_routes(params, fields, D0, 'selected')
            for name, f in fields.items():
                scores = score_pair(f, params, rule, 'selected')
                gates = selected_moments['gates'][name]
                both_field_pass = all(scores[k]['relative_error'] <= .1 for k in ('primary_8x6', 'confirmation_16x12'))
                scores['physical_gates'] = dict(field_both_rules=both_field_pass,
                    axial_both_routes=all(gates[k]['axial_centroid_pass'] for k in ('between', 'raw')),
                    covariance_both_routes=all(gates[k]['covariance_pass'] for k in ('between', 'raw')))
                scores['joint_pass'] = all(scores['physical_gates'].values())
                selected_scores[name] = scores
            selected_contraction_difference = abs(selected['relative_error']-selected_scores['S256']['primary_8x6']['relative_error'])
            require(selected_contraction_difference <= 1e-9, 'selected S256 contraction/direct agreement')
            difference = abs(selected_scores['S256']['primary_8x6']['relative_error']-selected_scores['S128']['primary_8x6']['relative_error'])
            sensitivity = dict(absolute_difference=difference, tolerance=.001, passed=difference <= .001,
                selected_parameters_identical=True, selection_reference='S256')
        CHECKS['selected_direct_confirmation_or_explicit_no_candidate'] = True
        PARTIAL.update(selected_scores=selected_scores, selected_moments=selected_moments, sensitivity=sensitivity)
    with phase('counts_verdict_and_final_hashes'):
        check_counts(selected is not None)
        CHECKS['complete_work_counts'] = True
        for path, expected in BEFORE.items():
            require(identity(path, 'input_bytes_hashed_after') == expected, 'input changed: '+str(path))
        CHECKS['frozen_inputs_after'] = True
        require(COUNTERS['input_bytes_hashed_before'] == COUNTERS['input_bytes_hashed_after'], 'hash byte coverage')
        if selected is not None and sensitivity['passed'] and all(x['joint_pass'] for x in selected_scores.values()):
            status = 'ordinary_two_gaussian_endpoint_witness'
        elif selected is not None and not sensitivity['passed']:
            status = 'reference_sensitive_inconclusive'
        else:
            status = 'bounded_search_inconclusive'
        event('outcome', status=status, selected=selected, sensitivity=sensitivity, counters=COUNTERS)
    clock()
    return dict(schema='t68-compact-mixture-capacity-v1', status=status, candidate_verdict=status,
        numerical_qualified=True, capacity_witness=status == 'ordinary_two_gaussian_endpoint_witness',
        references=references, control_parameters=control, original_T63_control_parameters=selected_control,
        control_scores=control_scores, control_moments=control_moments,
        selected=selected, selected_scores=selected_scores, selected_moments=selected_moments,
        selected_contraction_direct_difference=selected_contraction_difference,
        search_summary=summary, geometry_procedural_summary=procedural, sensitivity=sensitivity,
        checks=CHECKS, counters=COUNTERS, phases_seconds=PHASES,
        input_identities=[dict(path=str(p.relative_to(REPO)).replace('\\', '/') if p.is_relative_to(REPO) else str(p), **v)
                          for p, v in BEFORE.items()],
        python=platform.python_version(), numpy=np.__version__,
        formal_exclusion=False, formal_error_certificate=False, continuous_inner_optimality_certified=False,
        global_geometry_optimality_certified=False, causal_dynamics_claim=False,
        new_flow_trajectories=0, prior_scientific_child_seconds=1980.2512354997452,
        scientific_series_scope=manifest['prior_scientific_series_scope'],
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        child_elapsed_before_result_write_seconds=time.perf_counter()-START)


def main():
    global STREAM
    with (LOCAL / 'work.jsonl').open('x', encoding='utf-8', newline='\n') as stream:
        STREAM = stream
        try:
            result = measure()
            write_json(ROOT / 'result.json', result)
            print(json.dumps(dict(status=result['status'], capacity_witness=result['capacity_witness'],
                                 counters=COUNTERS), allow_nan=False), flush=True)
        except BaseException as exc:
            failure = dict(schema='t68-compact-mixture-capacity-failure-v1', status='numerical_failure',
                numerical_qualified=False, capacity_witness=False, active_phase=ACTIVE,
                error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc(),
                counters=COUNTERS, checks=CHECKS, phases_seconds=PHASES, partial=PARTIAL,
                elapsed_seconds=time.perf_counter()-START)
            event('worker_failure', **failure)
            write_json(LOCAL / 'worker-failure.json', failure)
            raise


if __name__ == '__main__':
    main()
