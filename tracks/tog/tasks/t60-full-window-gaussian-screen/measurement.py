"""Fixed T60 D8 controls and one unfitted ordinary Gaussian trajectory.

No solver, reference evolution, fitting, array output, or reference verdict lives
here. The caller must qualify all reference checks before calling score_gaussian.
NumPy is obtained from the already loaded base module inside the scientific run.
"""
import hashlib
import json
import math
from pathlib import Path
import time


TIMES = (0., .25, .5, .75, 1.)
PAIRS = (('S64', 'S128', 'space'), ('S128', 'S256', 'space'),
         ('S128', 'T128', 'time'), ('S128', 'D192', 'domain'),
         ('S128', 'Q128', 'angular'))


class MeasurementError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise MeasurementError(message)


def finite_positive(value, label):
    require(math.isfinite(value) and value > 0., label)


def finite_nonnegative(value, label):
    require(math.isfinite(value) and value >= 0., label)


def record_map(records):
    result = {x['name']: x for x in records}
    require(len(result) == len(records), 'duplicate record names')
    for name, record in result.items():
        require(len(record['snapshots']) == 5, name + ': five statistics required')
        require(tuple(x['time'] for x in record['snapshots']) == TIMES,
                name + ': snapshot times')
    return result


def d8_grid(np, h):
    nr, nz = round(8. / h), round(16. / h)
    require(h > 0. and math.isclose(nr * h, 8., abs_tol=1e-12)
            and math.isclose(nz * h, 16., abs_tol=1e-12), 'D8 partition')
    return (np.arange(nr) + .5) * h, -8. + (np.arange(nz) + .5) * h


def partition_check(field, h):
    g = field['g']
    ratio = g['h'] / h
    require(g['R'] >= 8. and math.isclose(ratio, round(ratio), abs_tol=1e-12)
            and math.isclose(g['R'] / h, round(g['R'] / h), abs_tol=1e-12),
            'comparison grid must refine both source partitions')
    require(len(field['snapshots']) == 5, 'five source snapshots required')


def positive_samples(np, values, counters):
    counters['sample_validations'] += int(values.size)
    require(bool(np.all(np.isfinite(values))), 'nonfinite reconstructed q')
    require(float(np.min(values)) >= 0., 'negative reconstructed q')


def full_box_controls(fields, records, base, gauss, check_time):
    """Same 3x2 polynomial rule on the finer partition, second-field norm."""
    started = time.perf_counter()
    np = base.np
    byname = record_map(records)
    require(len(gauss[0][0]) == len(gauss[0][1]) == 3
            and len(gauss[1][0]) == len(gauss[1][1]) == 2, 'fixed 3x2 rule')
    counters = dict(quadrature_node_cell_points=0, reference_reconstruction_points=0,
                    sample_validations=0, comparison_integrals=0, outside_integrals=0,
                    outside_selected_node_cell_points=0)
    comparisons = []
    for a, b, kind in PAIRS:
        h = min(fields[a]['g']['h'], fields[b]['g']['h'])
        partition_check(fields[a], h)
        partition_check(fields[b], h)
        r, z = d8_grid(np, h)
        points = len(r) * len(z)
        for index, saved_time in enumerate(TIMES):
            tick = time.perf_counter()
            terms_num, terms_den = [], []
            for xr, wr in zip(*gauss[0]):
                rn = r + xr * h / 2.
                for xz, wz in zip(*gauss[1]):
                    check_time()
                    zn = z + xz * h / 2.
                    qa = base.evaluate_saved(fields[a], index, rn, zn, 'q')
                    qb = base.evaluate_saved(fields[b], index, rn, zn, 'q')
                    counters['reference_reconstruction_points'] += 2 * points
                    positive_samples(np, qa, counters)
                    positive_samples(np, qb, counters)
                    weight = 2. * math.pi * rn[:, None]**3 * h*h * wr*wz / 4.
                    terms_num.append(float(np.sum(weight * (qa-qb)**2)))
                    terms_den.append(float(np.sum(weight * qb**2)))
                    counters['quadrature_node_cell_points'] += points
                    check_time()
            numerator, denominator = math.fsum(terms_num), math.fsum(terms_den)
            finite_nonnegative(numerator, 'full-box numerator')
            finite_positive(denominator, 'full-box second-field denominator')
            error = math.sqrt(numerator / denominator)
            comparisons.append(dict(a=a, b=b, kind=kind, index=index, time=saved_time,
                domain='D8', h=h, quadrature_orders=[3, 2], numerator=numerator,
                denominator=denominator, vorticity_relative=error, passed=error <= .01,
                quadrature_node_cell_points=6 * points, elapsed_seconds=time.perf_counter()-tick))
            counters['comparison_integrals'] += 1
    reductions = []
    for index in range(1, 5):
        coarse = comparisons[index]['vorticity_relative']
        fine = comparisons[5+index]['vorticity_relative']
        waived = max(coarse, fine) <= 1e-8
        reductions.append(dict(time=TIMES[index], coarse=coarse, fine=fine,
            ratio=coarse/fine if fine > 0. else None, small_error_waiver=waived,
            passed=waived or coarse >= 1.5*fine))

    # D192's D8 boundary lies on its own cell faces; the complement is a union
    # of whole cells. Evaluate one quadrature-node plane at a time on D12.
    g = fields['D192']['g']
    require(g['R'] == 12., 'D192 must retain D12')
    partition_check(fields['D192'], g['h'])
    h, r, z = g['h'], g['r'], g['z']
    mask = (r[:, None] >= 8.) | (np.abs(z[None, :]) >= 8.)
    selected, points = int(np.count_nonzero(mask)), len(r)*len(z)
    outside = []
    for index, saved_time in enumerate(TIMES):
        tick = time.perf_counter()
        gamma_terms, omega_terms = [], []
        for xr, wr in zip(*gauss[0]):
            rn = r + xr*h/2.
            for xz, wz in zip(*gauss[1]):
                check_time()
                zn = z + xz*h/2.
                q = base.evaluate_saved(fields['D192'], index, rn, zn, 'q')
                counters['reference_reconstruction_points'] += points
                positive_samples(np, q, counters)
                weight = rn[:, None] * h*h*wr*wz/4.
                gamma_terms.append(float(np.sum((weight*q)[mask])))
                omega_terms.append(float(np.sum((2.*math.pi*weight*rn[:, None]**2*q**2)[mask])))
                counters['quadrature_node_cell_points'] += points
                counters['outside_selected_node_cell_points'] += selected
                check_time()
        gamma, omega2 = math.fsum(gamma_terms), math.fsum(omega_terms)
        finite_nonnegative(gamma, 'outside circulation')
        finite_nonnegative(omega2, 'outside physical vorticity squared')
        statistic = byname['D192']['snapshots'][index]
        total_gamma, total_omega2 = statistic['circulation'], statistic['vorticity_squared_integral']
        finite_positive(total_gamma, 'D192 full-domain circulation')
        finite_positive(total_omega2, 'D192 full-domain vorticity squared')
        outside.append(dict(time=saved_time, index=index, domain='D12 minus D8',
            circulation=gamma, vorticity_squared_integral=omega2,
            whole_D12_circulation=total_gamma, whole_D12_vorticity_squared_integral=total_omega2,
            circulation_fraction=gamma/total_gamma, vorticity_squared_fraction=omega2/total_omega2,
            quadrature_orders=[3, 2], quadrature_node_cell_points=6*points,
            selected_node_cell_points=6*selected, elapsed_seconds=time.perf_counter()-tick,
            formal_free_space_tail_bound=False))
        counters['outside_integrals'] += 1
    return dict(checks=dict(full_box_vorticity_disagreements=all(x['passed'] for x in comparisons),
        full_box_spatial_reduction=all(x['passed'] for x in reductions)),
        comparisons=comparisons, spatial_reductions=reductions, outside_D8=outside,
        counters=counters, elapsed_seconds=time.perf_counter()-started,
        cost_note='Named evaluated-point counts, not total FLOPs; one node plane at a time.',
        formal_error_certificate=False)


def model_integrals(field, index, saved_time, speed, rule, orders, base, check_time, counters):
    np = base.np
    tick = time.perf_counter()
    h = field['g']['h']
    partition_check(field, h)
    r, z = d8_grid(np, h)
    points = len(r)*len(z)
    numerators, denominators, masses, squared = [], [], [], []
    minimum = math.inf
    for xr, wr in zip(*rule[0]):
        rn = r + xr*h/2.
        for xz, wz in zip(*rule[1]):
            check_time()
            zn = z + xz*h/2.
            q = base.evaluate_saved(field, index, rn, zn, 'q')
            counters['reference_reconstruction_points'] += points
            positive_samples(np, q, counters)
            minimum = min(minimum, float(np.min(q)))
            qg = 1.5*np.exp(-.5*(rn[:, None]**2 + (zn[None, :]-speed*saved_time)**2))
            require(bool(np.all(np.isfinite(qg))), 'nonfinite Gaussian values')
            counters['gaussian_exp_evaluations'] += points
            weight = rn[:, None]*h*h*wr*wz/4.
            physical_weight = 2.*math.pi*rn[:, None]**2*weight
            numerators.append(float(np.sum(physical_weight*(qg-q)**2)))
            denominators.append(float(np.sum(physical_weight*q**2)))
            masses.append(float(np.sum(weight*qg)))
            squared.append(float(np.sum(physical_weight*qg**2)))
            counters['quadrature_node_cell_points'] += points
            check_time()
    numerator, denominator = math.fsum(numerators), math.fsum(denominators)
    gamma, omega2 = math.fsum(masses), math.fsum(squared)
    finite_nonnegative(numerator, 'model numerator')
    finite_positive(denominator, 'model reference denominator')
    finite_positive(gamma, 'numerical Gaussian D8 circulation')
    finite_positive(omega2, 'numerical Gaussian D8 vorticity squared')
    counters['model_rule_integrals'] += 1
    return dict(domain='D8', quadrature_orders=list(orders), h=h,
        numerator=numerator, denominator=denominator,
        vorticity_relative=math.sqrt(numerator/denominator),
        model_D8_circulation=gamma, model_D8_vorticity_squared_integral=omega2,
        model_D8_circulation_fraction_of_analytic_fullspace=gamma/(1.5*math.sqrt(2.*math.pi)),
        model_D8_vorticity_squared_fraction_of_analytic_fullspace=omega2/((9./4.)*math.pi**1.5),
        reference_minimum_sampled_q=minimum, reference_sampled_nonnegative=True,
        reference_sampled_negative_circulation=0., model_analytic_positive=True,
        quadrature_node_cell_points=points*orders[0]*orders[1],
        gaussian_exp_evaluations=points*orders[0]*orders[1],
        elapsed_seconds=time.perf_counter()-tick, mass_values_are_numerical=True)


def score_gaussian(fields, records, base, coefficient_path, check_time):
    """Fixed complete-tangent translation; all outcome qualification is external."""
    started = time.perf_counter()
    np = base.np
    byname = record_map(records)
    counters = dict(quadrature_node_cell_points=0, reference_reconstruction_points=0,
        sample_validations=0, gaussian_exp_evaluations=0, model_rule_integrals=0,
        quadrature_rules_constructed=0, quadrature_rule_nodes=0)
    check_time()
    tick = time.perf_counter()
    path = Path(coefficient_path)
    raw = path.read_bytes()
    coefficient = json.loads(raw)
    require(coefficient['status'] == 'consistent', 'unqualified frozen coefficient')
    beta = float(coefficient['closed_metrics']['beta_best_over_g0'])
    finite_positive(beta, 'fixed coefficient')
    speed = 1.5*beta
    coefficient_identity = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    coefficient_loading_seconds = time.perf_counter()-tick
    check_time()
    tick = time.perf_counter()
    rules = {}
    for order in (8, 6, 16, 12):
        check_time()
        nodes, weights = np.polynomial.legendre.leggauss(order)
        require(len(nodes) == len(weights) == order and bool(np.all(np.isfinite(nodes)))
                and bool(np.all(np.isfinite(weights))) and bool(np.all(weights > 0.)), 'invalid fixed Gauss rule')
        rules[order] = (nodes, weights)
        counters['quadrature_rules_constructed'] += 1
        counters['quadrature_rule_nodes'] += order
    rule_generation_seconds = time.perf_counter()-tick
    analytic_covariance = [[(4.-math.pi)/2., 0.], [0., 1.]]
    initial = byname['S256']['snapshots'][0]
    normalization = float(np.linalg.norm(np.asarray(initial['covariance'], dtype=float)))
    finite_positive(normalization, 'actual initial S256 covariance norm')
    scores = []
    for name in ('S256', 'S128'):
        for index, saved_time in enumerate(TIMES):
            check_time()
            primary = model_integrals(fields[name], index, saved_time, speed,
                (rules[8], rules[6]), (8, 6), base, check_time, counters)
            confirmation = model_integrals(fields[name], index, saved_time, speed,
                (rules[16], rules[12]), (16, 12), base, check_time, counters)
            statistic = byname[name]['snapshots'][index]
            finite_positive(statistic['circulation'], 'reference circulation for model moments')
            require(statistic['negative_cell_mass'] == 0., 'negative reference cell mass')
            mean = [math.sqrt(math.pi/2.), speed*saved_time]
            centroid_error = abs(mean[1]-statistic['centroid'][1])
            covariance_error = float(np.linalg.norm(np.asarray(analytic_covariance)-np.asarray(statistic['covariance'])))
            finite_nonnegative(centroid_error, 'centroid error')
            finite_nonnegative(covariance_error, 'covariance error')
            score_difference = abs(primary['vorticity_relative']-confirmation['vorticity_relative'])
            scores.append(dict(reference=name, index=index, time=saved_time,
                primary_8x6=primary, confirmation_16x12=confirmation,
                score_absolute_difference=score_difference, integration_passed=score_difference <= 1e-6,
                numerical_mass_absolute_differences=dict(
                    circulation=abs(primary['model_D8_circulation']-confirmation['model_D8_circulation']),
                    vorticity_squared_integral=abs(primary['model_D8_vorticity_squared_integral']-confirmation['model_D8_vorticity_squared_integral'])),
                model_fullspace_centroid=mean, model_fullspace_covariance=analytic_covariance,
                reference_own_domain_centroid=statistic['centroid'], reference_own_domain_covariance=statistic['covariance'],
                reference_own_domain_circulation=statistic['circulation'],
                reference_negative_cell_mass=statistic['negative_cell_mass'],
                reference_own_domain_vorticity_squared_integral=statistic['vorticity_squared_integral'],
                axial_centroid_absolute=centroid_error, covariance_frobenius_absolute=covariance_error,
                covariance_relative_to_initial_S256=covariance_error/normalization,
                score_is_primary_regardless_of_confirmation=True))
    primary_scores = [x for x in scores if x['reference'] == 'S256']
    primary_model_checks = dict(vorticity_L2=all(x['primary_8x6']['vorticity_relative'] <= .10 for x in primary_scores),
        axial_centroid=all(x['axial_centroid_absolute'] <= .1 for x in primary_scores),
        covariance=all(x['covariance_relative_to_initial_S256'] <= .1 for x in primary_scores))
    integration_passed = all(x['integration_passed'] for x in scores)
    displacement = byname['S256']['snapshots'][-1]['centroid'][1]-initial['centroid'][1]
    require(math.isfinite(displacement), 'reference axial displacement')
    motion = dict(reference='S256', initial_axial_centroid=initial['centroid'][1],
        final_axial_centroid=byname['S256']['snapshots'][-1]['centroid'][1],
        axial_displacement=displacement, required_initial_widths=.25, initial_width=1., passed=displacement >= .25)
    check_time()
    return dict(integration_qualified=integration_passed, score_integration_qualified=integration_passed,
        meaningful_motion=motion['passed'], motion=motion, primary_model_checks=primary_model_checks,
        model_pass=all(primary_model_checks.values()), model_pass_requires_external_reference_and_integration_qualification=True,
        checks=dict(score_integration=integration_passed, meaningful_motion=motion['passed'], **primary_model_checks),
        scores=scores, coefficient_identity=coefficient_identity, beta_best_over_g0=beta, axial_speed=speed,
        actual_initial_S256_covariance_frobenius_norm=normalization,
        analytic_model=dict(amplitude=1.5, width=1., fullspace_circulation=1.5*math.sqrt(2.*math.pi),
            radial_centroid=math.sqrt(math.pi/2.), axial_centroid_formula='c*t', covariance=analytic_covariance,
            fullspace_vorticity_squared_integral=(9./4.)*math.pi**1.5,
            negative_vorticity_mass=0., positive_for_all_finite_r_z=True),
        coefficient_loading_seconds=coefficient_loading_seconds, rule_generation_seconds=rule_generation_seconds,
        counters=counters, elapsed_seconds=time.perf_counter()-started,
        scope='D8 fields, finite computational reference moments, five saved times; no rigorous whole-space or continuous-time bound',
        cost_note='Named evaluated-point counts, not total FLOPs; setup and both rules are paid; no fitted parameters or stepper.',
        formal_error_certificate=False)
