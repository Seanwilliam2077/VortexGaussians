"""Small contract tests; the separate auditor supplies formal reference evidence."""
import copy
import math
import unittest

import numpy as np
import core
import run


def one(temperature=450.0, sigma=.07):
    return [{"id": "s0", "anchorId": "s0", "position": [0., 0., 0.], "volume": .001,
             "Gamma": [0., 0., .001], "sigma": sigma, "temperature": temperature, "capacityPerVolume": 3.}]


class CoreContracts(unittest.TestCase):
    def test_radial_series_switch_against_positive_quadrature(self):
        # Independent radial-integral identity, not a copy of erf or the series.
        z, w = np.polynomial.legendre.leggauss(64)
        t, weight = (z+1)/2, w/2
        for q in [0., 1e-8, .01, .25, math.nextafter(.5, 0.), .5, math.nextafter(.5, math.inf), 1.]:
            F, D, _, _ = core.gaussian_factors(q, 1.)
            ref_f = math.sqrt(2/math.pi)*np.dot(weight, t**2*np.exp(-.5*q*q*t*t))
            ref_d = -math.sqrt(2/math.pi)*np.dot(weight, t**4*np.exp(-.5*q*q*t*t))
            self.assertLess(abs(float(F)-ref_f), 2e-14)
            self.assertLess(abs(float(D)-ref_d), 2e-13)
        self.assertTrue(bool(core.gaussian_factors(math.nextafter(.5, 0.), 1.)[3]))
        self.assertFalse(bool(core.gaussian_factors(.5, 1.)[3]))

    def test_kernel_origin_nonzero_jacobian_and_self_stretch_zero(self):
        p = core.make_parcels(one())
        u, J = core.velocity_jacobian(p, [[0., 0., 0.]])
        np.testing.assert_array_equal(u, 0.)
        self.assertGreater(np.max(np.abs(J)), 0.)
        np.testing.assert_array_equal(J[0]@p["Gamma"][0], 0.)
        self.assertEqual(np.trace(J[0]), 0.)
        self.assertGreater(J[0, 1, 0], 0.)

    def test_complete_jacobian_by_difference_and_solenoidal_trace(self):
        p = core.make_parcels(run.base_sources())
        x = np.array([[.023, .814, -.031]])
        _, J = core.velocity_jacobian(p, x)
        numerical = np.zeros((3, 3))
        for axis in range(3):
            delta = np.zeros((1, 3)); delta[0, axis] = 1e-6
            numerical[:, axis] = (core.velocity_jacobian(p, x+delta)[0][0] - core.velocity_jacobian(p, x-delta)[0][0]) / 2e-6
        np.testing.assert_allclose(J[0], numerical, rtol=1e-7, atol=1e-8)
        self.assertLess(abs(np.trace(J[0])), 1e-12)

    def test_split_preserves_all_fields_and_energy(self):
        records = run.base_sources()
        p = core.make_parcels(records)
        split = core.make_parcels(run.split_sources(records, [2]*8))
        x = [[.02, .81, -.03]]
        for a, b in zip(core.velocity_jacobian(p, x), core.velocity_jacobian(split, x)):
            np.testing.assert_allclose(a, b, rtol=1e-13, atol=1e-13)
        a, b = core.thermal_samples(p, x), core.thermal_samples(split, x)
        for key in ("temperature", "gradient", "numerator", "denominator"):
            np.testing.assert_allclose(a[key], b[key], rtol=1e-13, atol=1e-10)
        self.assertEqual(core.energy(p), core.energy(split))

    def test_constant_temperature_exact_and_far_rescaled_support(self):
        p = core.make_parcels(one(sigma=1.))
        samples = core.thermal_samples(p, [[0., 0., 0.], [40., 0., 0.]])
        self.assertEqual(samples["temperature"], [450., 450.])
        np.testing.assert_array_equal(samples["gradient"], 0.)
        self.assertEqual(samples["supported"], [True, True])
        self.assertTrue(samples["denominatorUnderflow"][1])
        self.assertLess(samples["logDenominator"][1], -745.)

    def test_physical_numerator_can_survive_denominator_underflow(self):
        p = core.make_parcels(one(temperature=1e300, sigma=1.))
        sample = core.thermal_samples(p, [[40., 0., 0.]])
        self.assertEqual(sample["denominator"][0], 0.)
        self.assertGreater(sample["numerator"][0], 0.)
        self.assertFalse(sample["numeratorUnderflow"][0])
        self.assertTrue(math.isfinite(sample["temperature"][0]))

    def test_centering_does_not_erase_small_dominant_temperature(self):
        sources = one(temperature=1e16, sigma=1.) + one(temperature=1., sigma=1.)
        sources[0]["volume"] = 1e-20
        sources[1]["volume"] = 1.
        sources[1]["id"] = "s1"; sources[1]["anchorId"] = "s1"
        sample = core.thermal_samples(core.make_parcels(sources), [[0., 0., 0.]])
        self.assertAlmostEqual(sample["temperature"][0], 1.0001, places=14)
        reverse = core.thermal_samples(core.make_parcels(list(reversed(sources))), [[0., 0., 0.]])
        self.assertEqual(reverse["temperature"], sample["temperature"])

    def test_shepard_gradient_is_its_own_quotient_derivative(self):
        p = core.make_parcels(run.base_sources())
        x = np.array([[.02, .81, -.03]])
        sample = core.thermal_samples(p, x)
        numerical = []
        for axis in range(3):
            delta = np.zeros((1, 3)); delta[0, axis] = 1e-6
            plus = core.thermal_samples(p, x+delta)["temperature"][0]
            minus = core.thermal_samples(p, x-delta)["temperature"][0]
            numerical.append((plus-minus)/2e-6)
        np.testing.assert_allclose(sample["gradient"][0], numerical, rtol=1e-7, atol=1e-7)

    def test_empty_field_has_no_invented_thermal_support(self):
        p = core.make_parcels([])
        u, J = core.velocity_jacobian(p, [[1., 2., 3.]])
        np.testing.assert_array_equal(u, 0.); np.testing.assert_array_equal(J, 0.)
        sample = core.thermal_samples(p, [[1., 2., 3.]])
        self.assertEqual(sample["supported"], [False])
        self.assertEqual(sample["temperature"], [None])
        self.assertEqual(sample["gradient"], [None])
        self.assertEqual(core.energy(p), 0.)

    def test_buoyancy_source_units_sign_and_split(self):
        p = core.make_parcels(one())
        p["Gamma"][:] = 0.
        rhs = core.inviscid_rhs(p, np.zeros((1, 3, 3)), [[40., -25., 30.]], .5, 100.)
        np.testing.assert_allclose(rhs[0], .001*.5*np.array([-30., 0., 40.])/100., atol=0., rtol=1e-15)
        self.assertEqual(float(rhs[0, 1]), 0.)

    def test_euler_is_synchronous_and_does_not_mutate(self):
        p = core.make_parcels(one())
        original = run.encoded(core.source_records(p))
        updated, mean = core.mean_mode_euler(p, [0., 0., 0.], [0., .25, 0.], .01)
        np.testing.assert_array_equal(updated["x"], p["x"])
        np.testing.assert_allclose(mean, [0., .0025, 0.], rtol=0., atol=0.)
        self.assertEqual(run.encoded(core.source_records(p)), original)
        updated["T"][0] = 0.
        self.assertEqual(p["T"][0], 450.)

    def test_reject_malformed_and_nonfinite_inputs(self):
        for field, value in [("volume", 0.), ("sigma", -1.), ("temperature", -1.), ("capacityPerVolume", math.inf),
                             ("position", [[0., 0., 0.]]), ("Gamma", [0., math.nan, 0.])]:
            records = one(); records[0][field] = value
            with self.assertRaises((ValueError, FloatingPointError)):
                core.make_parcels(records)
        with self.assertRaises(ValueError):
            core.make_parcels(one()+one())
        with self.assertRaises(ValueError):
            core.velocity_jacobian(core.make_parcels(one()), [0., 0., 0.])
        with self.assertRaises(ValueError):
            core.thermal_samples(core.make_parcels(one()), [[[0., 0., 0.]]])

    def test_overflow_cannot_escape_mean_update(self):
        p = core.make_parcels(one())
        with self.assertRaises((ValueError, FloatingPointError, OverflowError)):
            core.mean_mode_euler(p, [0., 0., 0.], [0., 1e308, 0.], 10.)

    def test_fixture_coverage_and_switch_actual_branches(self):
        self.assertEqual(len(run.STATIC_IDS), 12)
        self.assertEqual(len(run.DYNAMIC_IDS), 9)
        kernel = run.kernel_case()
        self.assertEqual(len(kernel["queries"]), 31)
        self.assertEqual([p["branch"] for p in kernel["radialProbes"]][2:5], ["series", "regular", "regular"])
        self.assertEqual(len(run.split_sources(run.base_sources(), [1, 2]*4)), 12)


if __name__ == "__main__":
    unittest.main(verbosity=2)
