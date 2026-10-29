"""T52: one fixed scalar quadrature check; not a fluid solver."""
import time
START = time.perf_counter()
import datetime
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import numpy as np

ORDERS = (128, 256, 512)
RADIUS = 12.0
TOLERANCE = 1e-9


def ell(radius):
    if radius <= 0.25:
        z = -0.5 * radius * radius
        term = 1.0
        terms = []
        for n in range(12):
            if n:
                term *= z / n
            terms.append(term / (2 * n + 3))
        return 2.0 * math.fsum(terms)
    return 2.0 * (
        math.sqrt(math.pi / 2.0) * math.erf(radius / math.sqrt(2.0))
        - radius * math.exp(-radius * radius / 2.0)
    ) / radius ** 3


def metrics(moments):
    j0, j1, j2 = moments
    best_squared = 1.0 - j1 * j1 / (j0 * j2)
    center_squared = (j2 - (4.0 / 3.0) * j1 + (4.0 / 9.0) * j0) / j2
    assert 0.0 < best_squared < 1.0 and center_squared >= 0.0
    best = math.sqrt(best_squared)
    center = math.sqrt(center_squared)
    kappa_n = math.sqrt(6.0 * j2 / (5.0 * math.sqrt(math.pi)))
    return dict(
        beta_best_over_g0=j1 / j0, beta_center_over_g0=2.0 / 3.0,
        E_best=best, E_center=center, E_zero_derivative_reference=1.0,
        best_to_center_residual_ratio=best / center,
        residual_reduction_fraction=1.0 - best / center,
        kappa_N=kappa_n, kappa_best=kappa_n * best,
        kappa_center=kappa_n * center,
    )


def main():
    out = Path(sys.argv[1])
    assert not out.exists(), out
    closed = [
        15.0 * math.sqrt(math.pi) / 16.0,
        math.sqrt(2.0 * math.pi / 3.0) / 3.0,
        math.sqrt(math.pi) * (
            2.0 * math.atan(1.0 / (2.0 * math.sqrt(2.0)))
            - 5.0 / (6.0 * math.sqrt(2.0))
        ),
    ]
    rules = []
    for order in ORDERS:
        start = time.perf_counter()
        nodes, weights = np.polynomial.legendre.leggauss(order)
        node_seconds = time.perf_counter() - start
        start_eval = time.perf_counter()
        terms = [[], [], []]
        for node, weight in zip(nodes, weights):
            radius = 0.5 * RADIUS * (float(node) + 1.0)
            base = (0.5 * RADIUS * float(weight)) * radius ** 6 * math.exp(-radius * radius)
            value = ell(radius)
            terms[0].append(base)
            terms[1].append(base * value)
            terms[2].append(base * value * value)
        moments = [math.fsum(values) for values in terms]
        eval_seconds = time.perf_counter() - start_eval
        assert all(math.isfinite(value) and value > 0.0 for value in moments)
        assert 0.0 < moments[1] ** 2 < moments[0] * moments[2]
        rules.append(dict(
            nodes=order, moments=moments,
            relative_difference_from_closed=[abs(v - exact) / exact for v, exact in zip(moments, closed)],
            node_generation_seconds=node_seconds, integration_seconds=eval_seconds,
            node_and_integration_seconds=time.perf_counter() - start,
        ))
    adjacent = [
        [abs(a - b) / exact for a, b, exact in zip(left['moments'], right['moments'], closed)]
        for left, right in zip(rules[:-1], rules[1:])
    ]
    consistency = all(
        error <= TOLERANCE
        for errors in [entry['relative_difference_from_closed'] for entry in rules] + adjacent
        for error in errors
    )
    radius = RADIUS
    tail0 = math.exp(-radius * radius) * (
        radius ** 5 / 2.0 + 5.0 * radius ** 3 / 4.0
        + 15.0 * radius / 8.0 + 15.0 / (16.0 * radius)
    )
    source = Path(__file__).read_bytes()
    result = dict(
        schema='t52-scalar-enstrophy-tangent-measurement-v1',
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='consistent' if consistency else 'inconsistent',
        python=platform.python_version(), numpy=np.__version__,
        executable=sys.executable, platform=platform.platform(),
        measurement_script=dict(bytes=len(source),sha256=hashlib.sha256(source).hexdigest()),
        settings=dict(orders=list(ORDERS),radius=RADIUS,tolerance=TOLERANCE,
                      series_threshold=0.25,series_terms=12,total_nodes=sum(ORDERS)),
        closed_moments=closed,rules=rules,adjacent_rule_relative_differences=adjacent,
        real_arithmetic_tail_upper_bounds=[tail0,2.0 * tail0 / 3.0,4.0 * tail0 / 9.0],
        real_arithmetic_series_remainder_upper_bound=2.0 * (1.0 / 32.0) ** 12 / (math.factorial(12) * 27.0),
        closed_metrics=metrics(closed),finest_rule_metrics=metrics(rules[-1]['moments']),
        formal_floating_point_certificate=False,fluid_trajectories=0,new_methods_implemented=0,
        child_elapsed_before_result_write_seconds=time.perf_counter()-START,
    )
    with out.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    print(json.dumps(dict(status=result['status'],metrics=result['closed_metrics'],output=str(out))))
    return 0 if consistency else 2


if __name__ == '__main__':
    raise SystemExit(main())
