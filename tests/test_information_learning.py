import math
import random
import unittest

from examples.information_learning import (
    gaussian_mac_capacity_region, relay_rate_bounds, butterfly_network_code,
    fisher_information_normal_mean, cramer_rao_normal_mean, aic_bic,
    softmax, softmax_cross_entropy, softmax_cross_entropy_gradient,
    label_smoothing, brier_score, vae_elbo,
    information_bottleneck_objective, variational_ib_loss,
    empirical_entropy, miller_madow_entropy, empirical_mutual_information,
    gaussian_mutual_information, ksg_mutual_information,
    mine_dv_empirical_bound, info_nce_empirical_bound,
)


class NetworkInformationTests(unittest.TestCase):
    def test_gaussian_mac_capacity_region(self):
        r = gaussian_mac_capacity_region(2.0, 1.5, 1.0)
        self.assertAlmostEqual(r["c1"], 0.792481250360578)
        self.assertAlmostEqual(r["c2"], 0.6609640474436812)
        self.assertAlmostEqual(r["sum"], 1.084962500721156)
        self.assertEqual(len(r["vertices"]), 5)
        self.assertAlmostEqual(r["vertices"][2][1], r["sum"] - r["c1"])
        self.assertAlmostEqual(r["vertices"][3][0], r["sum"] - r["c2"])

    def test_relay_bounds_are_not_collapsed(self):
        b = relay_rate_bounds(1.2, 1.5, .8, 1.1)
        self.assertAlmostEqual(b["cut_set_upper"], 1.2)
        self.assertAlmostEqual(b["decode_forward_lower"], .8)

    def test_butterfly_network_coding(self):
        for a, b in ((0, 0), (0, 1), (1, 0), (1, 1)):
            result = butterfly_network_code(a, b)
            self.assertEqual(result["destination_a_recovers_b"], b)
            self.assertEqual(result["destination_b_recovers_a"], a)


class StatisticalInferenceTests(unittest.TestCase):
    def test_fisher_information_and_crlb(self):
        self.assertAlmostEqual(fisher_information_normal_mean(100, 4), 25)
        self.assertAlmostEqual(cramer_rao_normal_mean(100, 4), .04)

    def test_aic_bic_use_natural_log(self):
        r = aic_bic(-50, 3, 100)
        self.assertAlmostEqual(r["aic"], 106)
        self.assertAlmostEqual(r["bic"], 113.81551055796427)


class CrossEntropyTests(unittest.TestCase):
    def test_softmax_normalizes_and_ce_gradient_is_q_minus_y(self):
        logits, target = (2.0, 0.0, -1.0), (0.0, 1.0, 0.0)
        p = softmax(logits)
        grad = softmax_cross_entropy_gradient(logits, target)
        self.assertAlmostEqual(sum(p), 1)
        self.assertAlmostEqual(sum(grad), 0)
        for a, b in zip(grad, (p[0], p[1] - 1, p[2])):
            self.assertAlmostEqual(a, b)
        self.assertAlmostEqual(softmax_cross_entropy(logits, target), 2.1698460195562856)

    def test_gradient_matches_finite_difference(self):
        z, y, eps = [1.2, -.4, .1], [0, 1, 0], 1e-6
        grad = softmax_cross_entropy_gradient(z, y)
        for i in range(3):
            plus, minus = z[:], z[:]
            plus[i] += eps
            minus[i] -= eps
            numeric = (softmax_cross_entropy(plus, y) - softmax_cross_entropy(minus, y)) / (2 * eps)
            self.assertAlmostEqual(grad[i], numeric, places=6)

    def test_label_smoothing_and_brier_are_normalized(self):
        target = label_smoothing(1, 4, .1)
        self.assertAlmostEqual(sum(target), 1)
        self.assertAlmostEqual(target[1], .925)
        self.assertAlmostEqual(brier_score((.1, .8, .1), (0, 1, 0)), .06)

    def test_vae_and_ib_objectives_keep_conventions_explicit(self):
        self.assertAlmostEqual(vae_elbo(-2, .5, 2), -3)
        self.assertAlmostEqual(information_bottleneck_objective(1.5, .8, 2), -.1)
        self.assertAlmostEqual(variational_ib_loss(.3, .8, .1), .38)


class MutualInformationEstimationTests(unittest.TestCase):
    def test_plugin_entropy_and_miller_madow(self):
        samples = [0, 0, 0, 1]
        self.assertAlmostEqual(empirical_entropy(samples), .8112781244591328)
        self.assertGreater(miller_madow_entropy(samples), empirical_entropy(samples))

    def test_empirical_mutual_information(self):
        x, y = [0, 0, 1, 1], [0, 0, 1, 1]
        self.assertAlmostEqual(empirical_mutual_information(x, y), 1)
        self.assertAlmostEqual(empirical_mutual_information(x, [0, 1, 0, 1]), 0)

    def test_gaussian_mutual_information(self):
        self.assertAlmostEqual(gaussian_mutual_information(.7), .48571542390161454)

    def test_ksg_correlated_exceeds_independent_baseline(self):
        rng = random.Random(2026)
        n, rho = 300, .65
        x, correlated, independent = [], [], []
        for _ in range(n):
            a, b, c = rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)
            x.append(a)
            correlated.append(rho * a + math.sqrt(1 - rho * rho) * b)
            independent.append(c)
        truth = gaussian_mutual_information(rho)
        estimate = ksg_mutual_information(x, correlated, k=4)
        null_estimate = ksg_mutual_information(x, independent, k=4)
        self.assertLess(abs(estimate - truth), .18)
        self.assertLess(abs(null_estimate), .18)
        self.assertGreater(estimate, null_estimate + .2)

    def test_neural_bounds_are_reported_as_objectives(self):
        mine = mine_dv_empirical_bound([1.0, 1.0], [0.0, 0.0])
        self.assertAlmostEqual(mine, 1 / math.log(2))
        nce = info_nce_empirical_bound([[3, 0, 0], [3, 0, 0], [3, 0, 0]])
        self.assertGreater(nce, .5)
        self.assertLessEqual(nce, math.log2(3) + 1e-12)


if __name__ == "__main__":
    unittest.main()
