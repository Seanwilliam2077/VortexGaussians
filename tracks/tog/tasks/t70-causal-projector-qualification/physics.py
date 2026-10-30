"""Ordinary free-space Gaussian heat potentials; no import-time numerical work.

NumPy and already constructed Legendre rules are supplied by the frozen worker.
All quadratures here are empirical binary64 calculations, not certificates.
"""
import math


COUNTER_KEYS = (
    'phys_instances', 'phys_state_validations', 'phys_geometry_validations',
    'phys_component_setups', 'phys_zero_weight_components_skipped',
    'phys_rule_transforms', 'phys_rule_nodes_transformed', 'phys_gram_calls',
    'phys_cross_calls', 'phys_cross_ordered_pair_integrals',
    'phys_cross_integrand_points', 'phys_field_calls',
    'phys_field_spatial_points', 'phys_field_component_points',
    'phys_field_heat_nodes', 'phys_field_heat_integrand_points',
    'phys_field_ordered_pair_points', 'phys_peak_spatial_points',
    'phys_moment_calls', 'phys_initial_exact_calls', 'phys_initial_exact_points',
    'phys_initial_origin_points', 'phys_initial_series_points',
    'phys_initial_series_terms', 'phys_erf_evaluations',
    'phys_exp_evaluations', 'phys_array_exp_calls', 'phys_scalar_exp_calls',
    'phys_sqrt_evaluations', 'phys_fsum_calls', 'phys_fsum_terms',
)


class Physics:
    def __init__(self, np, rules, counters, emit):
        self.np, self.counters, self.emit = np, counters, emit
        for key in COUNTER_KEYS:
            counters.setdefault(key, 0)
        self._count('phys_instances')
        self.sqrt_two = self._sqrt(2.0)
        self.sqrt_two_pi = self._sqrt(2.0 * math.pi)
        self.sqrt_half_pi = self._sqrt(math.pi / 2.0)
        self.heat = {}
        for order in (64, 128, 256):
            x, w = rules[order]
            x, w = np.asarray(x, dtype=float), np.asarray(w, dtype=float)
            if (x.shape != (order,) or w.shape != (order,)
                    or not np.all(np.isfinite(x)) or not np.all(np.isfinite(w))
                    or not np.all((x > -1.0) & (x < 1.0))
                    or not np.all(w > 0.0) or not np.all(np.diff(x) > 0.0)):
                raise ValueError('invalid supplied heat rule')
            s = (x + 1.0) / 2.0
            tau = (s / (1.0 - s)) ** 2
            weights = (w / 2.0) * (2.0 * s / (1.0 - s) ** 3)
            if not np.all(np.isfinite(tau)) or not np.all(np.isfinite(weights)):
                raise ValueError('nonfinite transformed heat rule')
            self.heat[order] = (tau, weights)
            self._count('phys_rule_transforms')
            self._count('phys_rule_nodes_transformed', order)
        if emit is not None:
            emit('physics_setup', {'heat_orders': [64, 128, 256],
                                  'initial_series_terms': 20,
                                  'initial_series_radius': 0.5})

    def _count(self, key, amount=1):
        self.counters[key] += amount

    def _sqrt(self, value):
        self._count('phys_sqrt_evaluations')
        return math.sqrt(value)

    def _sum(self, values):
        values = list(values)
        self._count('phys_fsum_calls')
        self._count('phys_fsum_terms', len(values))
        return math.fsum(values)

    def _exp(self, value):
        self._count('phys_scalar_exp_calls')
        self._count('phys_exp_evaluations')
        return math.exp(value)

    def _array_exp(self, value):
        self._count('phys_array_exp_calls')
        self._count('phys_exp_evaluations', int(value.size))
        return self.np.exp(value)

    def _geometry(self, geometry):
        self._count('phys_geometry_validations')
        if len(geometry) != 3:
            raise ValueError('geometry must be (sr, sz, z0)')
        sr, sz, z0 = map(float, geometry)
        if not all(map(math.isfinite, (sr, sz, z0))) or sr <= 0 or sz <= 0:
            raise ValueError('nonfinite geometry or nonpositive width')
        rho, nu = sr * sr, sz * sz
        norm = rho * self.sqrt_two_pi * sz
        if not all(map(math.isfinite, (rho, nu, norm))) or min(rho, nu, norm) <= 0:
            raise ValueError('unrepresentable positive geometry')
        return {'geometry': (sr, sz, z0), 'sr': sr, 'sz': sz,
                'z0': z0, 'rho': rho, 'nu': nu, 'norm': norm}

    def _components(self, state):
        self._count('phys_state_validations')
        gamma, eta = float(state['Gamma']), float(state['eta'])
        if not math.isfinite(gamma) or gamma < 0 or not math.isfinite(eta) or not 0 <= eta <= 1:
            raise ValueError('invalid circulation or mixture weight')
        if len(state['geometry']) != 2:
            raise ValueError('state must contain exactly two geometries')
        components = []
        for index, (weight, geometry) in enumerate(zip((1.0 - eta, eta), state['geometry'])):
            item = self._geometry(geometry)
            if weight == 0.0:
                self._count('phys_zero_weight_components_skipped')
                continue
            item.update(index=index, weight=weight, A=gamma * weight / item['norm'])
            if not math.isfinite(item['A']):
                raise ValueError('nonfinite component amplitude')
            components.append(item)
            self._count('phys_component_setups')
        return gamma, components

    def _points(self, r, z):
        np = self.np
        r, z = np.asarray(r, dtype=float), np.asarray(z, dtype=float)
        if (r.ndim != 1 or z.shape != r.shape or r.size > 18432
                or not np.all(np.isfinite(r)) or not np.all(np.isfinite(z))
                or not np.all(r >= 0.0)):
            raise ValueError('invalid flat meridional point arrays')
        self.counters['phys_peak_spatial_points'] = max(
            self.counters['phys_peak_spatial_points'], int(r.size))
        return r, z

    def gram(self, g, h):
        """Full-space H Gram of two unit-circulation components."""
        self._count('phys_gram_calls')
        g, h = self._geometry(g), self._geometry(h)
        rho = 1.0 / (1.0 / g['rho'] + 1.0 / h['rho'])
        nu = 1.0 / (1.0 / g['nu'] + 1.0 / h['nu'])
        overlap = self._exp(-0.5 * (g['z0'] - h['z0']) ** 2 / (g['nu'] + h['nu']))
        value = (4.0 * math.pi * rho * rho * self._sqrt(2.0 * math.pi * nu)
                 * overlap / (g['norm'] * h['norm']))
        if not math.isfinite(value) or value < 0.0:
            raise ValueError('invalid Gaussian Gram value')
        return value

    def cross(self, state, g, order):
        """Return <F(q),g> and each ordered current-component contribution."""
        self._count('phys_cross_calls')
        _, components = self._components(state)
        g = self._geometry(g)
        tau, weights = self.heat[order]
        pairs = []
        for ci in components:
            for cj in components:
                self._count('phys_cross_ordered_pair_integrals')
                terms = []
                for heat_time, weight in zip(tau, weights):
                    self._count('phys_cross_integrand_points')
                    Ri = ci['rho'] + 2.0 * float(heat_time)
                    Vi = ci['nu'] + 2.0 * float(heat_time)
                    ki = (ci['rho'] / Ri) ** 2 * self._sqrt(ci['nu'] / Vi)
                    li, lj, ll = 1.0 / Vi, 1.0 / cj['nu'], 1.0 / g['nu']
                    precision = self._sum((li, lj, ll))
                    nu = 1.0 / precision
                    mu = nu * self._sum((li * ci['z0'], lj * cj['z0'], ll * g['z0']))
                    dispersion = self._sum((
                        li * lj * (ci['z0'] - cj['z0']) ** 2,
                        li * ll * (ci['z0'] - g['z0']) ** 2,
                        lj * ll * (cj['z0'] - g['z0']) ** 2,
                    )) / precision
                    rho = 1.0 / (1.0 / Ri + 1.0 / cj['rho'] + 1.0 / g['rho'])
                    R3, R5 = 2.0 * rho ** 2, 8.0 * rho ** 3
                    Z0 = self._sqrt(2.0 * math.pi * nu) * self._exp(-0.5 * dispersion)
                    bracket = self._sum((
                        R5 * (mu - ci['z0']) / (Vi * cj['rho']),
                        (2.0 * R3 - R5 / Ri) * (mu - cj['z0']) / cj['nu'],
                    ))
                    terms.append(float(weight) * ki * Z0 * bracket)
                value = (2.0 * math.pi * ci['A'] * cj['A'] / g['norm']) * self._sum(terms)
                if not math.isfinite(value):
                    raise ValueError('nonfinite ordered heat contraction')
                pairs.append({'i': ci['index'], 'j': cj['index'], 'value': value})
        total = self._sum(p['value'] for p in pairs)
        return {'total': total, 'ordered_pairs': pairs}

    def field(self, state, r, z, order):
        """Evaluate flat fields without a spatial-points by heat-nodes matrix."""
        self._count('phys_field_calls')
        np = self.np
        r, z = self._points(r, z)
        size = int(r.size)
        self._count('phys_field_spatial_points', size)
        _, components = self._components(state)
        tau, weights = self.heat[order]
        fields = {key: np.zeros_like(r) for key in ('q', 'qr', 'qz', 'phi', 'phi_r', 'phi_z')}
        component_fields = []
        r2 = r * r
        for item in components:
            self._count('phys_field_component_points', size)
            dz = z - item['z0']
            q = item['A'] * self._array_exp(-r2 / (2.0 * item['rho']) - dz * dz / (2.0 * item['nu']))
            part = {'index': item['index'], 'geometry': item['geometry'],
                    'weight': item['weight'], 'A': item['A'], 'q': q,
                    'qr': -r * q / item['rho'], 'qz': -dz * q / item['nu'],
                    'phi': np.zeros_like(r), 'phi_r': np.zeros_like(r), 'phi_z': np.zeros_like(r)}
            for heat_time, weight in zip(tau, weights):
                self._count('phys_field_heat_nodes')
                self._count('phys_field_heat_integrand_points', size)
                Ri = item['rho'] + 2.0 * float(heat_time)
                Vi = item['nu'] + 2.0 * float(heat_time)
                ki = (item['rho'] / Ri) ** 2 * self._sqrt(item['nu'] / Vi)
                kernel = (item['A'] * float(weight) * ki
                          * self._array_exp(-r2 / (2.0 * Ri) - dz * dz / (2.0 * Vi)))
                part['phi'] += kernel
                part['phi_r'] += -(r / Ri) * kernel
                part['phi_z'] += -(dz / Vi) * kernel
            for key in fields:
                fields[key] += part[key]
            component_fields.append(part)
        fields['ur'] = -r * fields['phi_z']
        fields['uz'] = 2.0 * fields['phi'] + r * fields['phi_r']
        fields['F'] = -fields['ur'] * fields['qr'] - fields['uz'] * fields['qz']
        pairs = []
        for ci in component_fields:
            for cj in component_fields:
                self._count('phys_field_ordered_pair_points', size)
                value = r * ci['phi_z'] * cj['qr'] - (2.0 * ci['phi'] + r * ci['phi_r']) * cj['qz']
                pairs.append({'i': ci['index'], 'j': cj['index'], 'value': value})
        if any(not np.all(np.isfinite(value)) for value in fields.values()):
            raise ValueError('nonfinite physical field')
        if any(not np.all(np.isfinite(pair['value'])) for pair in pairs):
            raise ValueError('nonfinite ordered physical field')
        fields['components'], fields['ordered_Fij'] = component_fields, pairs
        return fields

    def moments(self, state):
        self._count('phys_moment_calls')
        gamma, components = self._components(state)
        if gamma == 0.0:
            return {'Gamma': 0.0, 'I_z': 0.0, 'between': None, 'raw': None,
                    'undefined_reason': 'zero_circulation'}
        kappa, radial_variance = self.sqrt_half_pi, (4.0 - math.pi) / 2.0
        mr = self._sum(c['weight'] * kappa * c['sr'] for c in components)
        mz = self._sum(c['weight'] * c['z0'] for c in components)
        rr = self._sum(c['weight'] * (radial_variance * c['rho'] + (kappa * c['sr'] - mr) ** 2) for c in components)
        zz = self._sum(c['weight'] * (c['nu'] + (c['z0'] - mz) ** 2) for c in components)
        rz = self._sum(c['weight'] * (kappa * c['sr'] - mr) * (c['z0'] - mz) for c in components)
        Qrr = self._sum(c['weight'] * 2.0 * c['rho'] for c in components)
        Qrz = self._sum(c['weight'] * kappa * c['sr'] * c['z0'] for c in components)
        Qzz = self._sum(c['weight'] * (c['nu'] + c['z0'] ** 2) for c in components)
        impulse = 2.0 * math.pi * gamma * self._sum(c['weight'] * c['rho'] for c in components)
        return {'Gamma': gamma, 'I_z': impulse,
                'between': {'centroid': [mr, mz], 'covariance': [[rr, rz], [rz, zz]]},
                'raw': {'centroid': [mr, mz], 'raw_second': [[Qrr, Qrz], [Qrz, Qzz]],
                        'covariance': [[Qrr - mr * mr, Qrz - mr * mz],
                                       [Qrz - mr * mz, Qzz - mz * mz]]}}

    def initial_exact(self, r, z):
        """Independent initial closed form; fixed 20-term small-radius series."""
        self._count('phys_initial_exact_calls')
        np = self.np
        r, z = self._points(r, z)
        self._count('phys_initial_exact_points', int(r.size))
        self._count('phys_sqrt_evaluations', int(r.size))
        radius = np.hypot(r, z)
        A = 1.5
        exponential = self._array_exp(-0.5 * radius * radius)
        q = A * exponential
        phi, derivative_over_radius = np.empty_like(r), np.empty_like(r)
        for index, raw_radius in enumerate(radius):
            R = float(raw_radius)
            if R == 0.0:
                self._count('phys_initial_origin_points')
                phi[index], derivative_over_radius[index] = A / 3.0, -A / 5.0
            elif R <= 0.5:
                self._count('phys_initial_series_points')
                self._count('phys_initial_series_terms', 20)
                coefficient, power, previous_power = 1.0, 1.0, 1.0
                potential_terms, derivative_terms = [], []
                for n in range(20):
                    potential_terms.append(coefficient * power / (2 * n + 3))
                    if n:
                        derivative_terms.append(coefficient * (2 * n) * previous_power / (2 * n + 3))
                    previous_power, power = power, power * R * R
                    coefficient *= -0.5 / (n + 1)
                phi[index] = A * self._sum(potential_terms)
                derivative_over_radius[index] = A * self._sum(derivative_terms)
            else:
                self._count('phys_erf_evaluations')
                I2 = self.sqrt_half_pi * math.erf(R / self.sqrt_two) - R * float(exponential[index])
                phi[index] = A * I2 / R ** 3
                derivative_over_radius[index] = A * (R ** 3 * float(exponential[index]) - 3.0 * I2) / R ** 5
        phi_r, phi_z = r * derivative_over_radius, z * derivative_over_radius
        fields = {'q': q, 'qr': -r * q, 'qz': -z * q, 'phi': phi,
                  'phi_r': phi_r, 'phi_z': phi_z,
                  'ur': -r * phi_z, 'uz': 2.0 * phi + r * phi_r,
                  'F': 2.0 * z * q * phi}
        if any(not np.all(np.isfinite(value)) for value in fields.values()):
            raise ValueError('nonfinite initial closed-form field')
        return fields
