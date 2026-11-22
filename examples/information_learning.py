"""Reproducible teaching models for information theory chapters 21–25.

Conventions:
- Gaussian channel capacities are per real scalar channel use (hence 1/2).
- AIC/BIC use natural-log likelihoods.
- KSG-1 returns bits; the digamma expression is naturally in nats.
- InfoNCE and DV functions return empirical objectives, not unbiased MI estimates.
"""
from __future__ import annotations

from collections import Counter
from itertools import product
from math import exp, inf, isfinite, log, log2, pi, sqrt
from typing import Iterable, Sequence


def gaussian_mac_capacity_region(power1: float, power2: float, noise_variance: float):
    """Two-user real Gaussian MAC region for independent Gaussian codebooks."""
    if power1 < 0 or power2 < 0 or noise_variance <= 0:
        raise ValueError("powers must be nonnegative and noise variance positive")
    c1 = 0.5 * log2(1 + power1 / noise_variance)
    c2 = 0.5 * log2(1 + power2 / noise_variance)
    total = 0.5 * log2(1 + (power1 + power2) / noise_variance)
    return {
        "c1": c1,
        "c2": c2,
        "sum": total,
        "vertices": (
            (0.0, 0.0),
            (c1, 0.0),
            (c1, total - c1),
            (total - c2, c2),
            (0.0, c2),
        ),
    }


def relay_rate_bounds(cut_destination: float, cut_relay: float,
                      decode_relay: float, decode_destination: float):
    """Return generic cut-set upper bound and decode-forward achievable bound.

    Inputs are already evaluated mutual informations for one fixed input law;
    optimization over admissible input distributions is deliberately separate.
    """
    values = (cut_destination, cut_relay, decode_relay, decode_destination)
    if any(v < 0 or not isfinite(v) for v in values):
        raise ValueError("mutual-information terms must be finite and nonnegative")
    return {
        "cut_set_upper": min(cut_destination, cut_relay),
        "decode_forward_lower": min(decode_relay, decode_destination),
    }


def butterfly_network_code(bit_a: int, bit_b: int):
    """Return the XOR packet sent over the butterfly network bottleneck."""
    if bit_a not in (0, 1) or bit_b not in (0, 1):
        raise ValueError("network-code inputs must be bits")
    coded = bit_a ^ bit_b
    return {"coded": coded, "destination_a_recovers_b": coded ^ bit_a,
            "destination_b_recovers_a": coded ^ bit_b}


def fisher_information_normal_mean(sample_size: int, variance: float) -> float:
    """Fisher information in n iid N(mu, variance) observations, variance known."""
    if sample_size < 1 or variance <= 0:
        raise ValueError("sample size must be positive and variance > 0")
    return sample_size / variance


def cramer_rao_normal_mean(sample_size: int, variance: float) -> float:
    """CRLB for any unbiased estimator of the mean of iid known-variance normals."""
    return 1.0 / fisher_information_normal_mean(sample_size, variance)


def aic_bic(log_likelihood: float, num_parameters: int, sample_size: int):
    """AIC and BIC from a maximized natural-log likelihood."""
    if not isfinite(log_likelihood) or num_parameters < 0 or sample_size < 1:
        raise ValueError("finite log likelihood, k >= 0 and n >= 1 required")
    return {
        "aic": -2.0 * log_likelihood + 2.0 * num_parameters,
        "bic": -2.0 * log_likelihood + num_parameters * log(sample_size),
    }


def softmax(logits: Sequence[float]) -> tuple[float, ...]:
    if not logits or any(not isfinite(float(z)) for z in logits):
        raise ValueError("logits must be a nonempty finite sequence")
    maximum = max(logits)
    exps = [exp(float(z) - maximum) for z in logits]
    total = sum(exps)
    return tuple(value / total for value in exps)


def softmax_cross_entropy(logits: Sequence[float], target: Sequence[float]) -> float:
    """Stable cross-entropy for normalized categorical target probabilities."""
    if len(logits) != len(target) or not logits:
        raise ValueError("logits and target must have the same nonzero length")
    if any(float(y) < 0 or not isfinite(float(y)) for y in target):
        raise ValueError("target probabilities must be finite and nonnegative")
    if abs(sum(target) - 1.0) > 1e-9:
        raise ValueError("target probabilities must sum to one")
    maximum = max(logits)
    log_partition = maximum + log(sum(exp(float(z) - maximum) for z in logits))
    return log_partition - sum(float(y) * float(z) for y, z in zip(target, logits))


def softmax_cross_entropy_gradient(logits: Sequence[float],
                                   target: Sequence[float]) -> tuple[float, ...]:
    if len(logits) != len(target) or abs(sum(target) - 1.0) > 1e-9:
        raise ValueError("target must match logits and sum to one")
    return tuple(p - float(y) for p, y in zip(softmax(logits), target))


def label_smoothing(target_index: int, num_classes: int,
                    epsilon: float) -> tuple[float, ...]:
    """PyTorch-style mixture (1-epsilon)*one_hot + epsilon*uniform."""
    if num_classes < 2 or not 0 <= target_index < num_classes:
        raise ValueError("invalid target index or class count")
    if not 0 <= epsilon <= 1:
        raise ValueError("epsilon must lie in [0,1]")
    base = epsilon / num_classes
    return tuple(base + (1.0 - epsilon if i == target_index else 0.0)
                 for i in range(num_classes))


def brier_score(probabilities: Sequence[float], target: Sequence[float]) -> float:
    if len(probabilities) != len(target) or not probabilities:
        raise ValueError("probability and target vectors must have equal nonzero length")
    if any(p < 0 or not isfinite(p) for p in probabilities):
        raise ValueError("probabilities must be finite and nonnegative")
    if abs(sum(probabilities) - 1.0) > 1e-9 or abs(sum(target) - 1.0) > 1e-9:
        raise ValueError("both vectors must be normalized")
    return sum((float(p) - float(y)) ** 2
               for p, y in zip(probabilities, target))


def vae_elbo(reconstruction_log_likelihood: float, kl_divergence: float,
             beta: float = 1.0) -> float:
    """Return beta-ELBO; larger is better."""
    if kl_divergence < 0 or beta < 0:
        raise ValueError("KL and beta must be nonnegative")
    return reconstruction_log_likelihood - beta * kl_divergence


def information_bottleneck_objective(i_x_t: float, i_t_y: float,
                                     beta: float) -> float:
    """Classical minimization convention: I(X;T) - beta*I(T;Y)."""
    if min(i_x_t, i_t_y, beta) < 0:
        raise ValueError("information quantities and beta must be nonnegative")
    return i_x_t - beta * i_t_y


def variational_ib_loss(task_nll: float, kl_to_prior: float,
                        beta: float) -> float:
    """Common VIB minimization convention: task NLL + beta * KL."""
    if task_nll < 0 or kl_to_prior < 0 or beta < 0:
        raise ValueError("loss terms and beta must be nonnegative")
    return task_nll + beta * kl_to_prior


def _counts(values: Iterable):
    values = list(values)
    if not values:
        raise ValueError("samples must be nonempty")
    return Counter(values), len(values)


def empirical_entropy(samples: Iterable) -> float:
    counts, n = _counts(samples)
    return -sum((c / n) * log2(c / n) for c in counts.values())


def miller_madow_entropy(samples: Iterable) -> float:
    """First-order Miller–Madow correction for a fixed finite alphabet."""
    counts, n = _counts(samples)
    plugin = -sum((c / n) * log2(c / n) for c in counts.values())
    return plugin + (len(counts) - 1) / (2.0 * n * log(2.0))


def empirical_mutual_information(x: Iterable, y: Iterable) -> float:
    xs, ys = list(x), list(y)
    if not xs or len(xs) != len(ys):
        raise ValueError("x and y must have equal nonzero lengths")
    n = len(xs)
    cx, cy, cxy = Counter(xs), Counter(ys), Counter(zip(xs, ys))
    result = 0.0
    for (a, b), count in cxy.items():
        pxy = count / n
        result += pxy * log2(pxy / ((cx[a] / n) * (cy[b] / n)))
    return result


def gaussian_mutual_information(correlation: float) -> float:
    """MI in bits for a nondegenerate bivariate Gaussian pair."""
    if not -1 < correlation < 1:
        raise ValueError("correlation must lie strictly between -1 and 1")
    return -0.5 * log2(1.0 - correlation * correlation)


def _as_points(values: Sequence):
    values = list(values)
    if not values:
        raise ValueError("sample arrays must be nonempty")
    if isinstance(values[0], (int, float)):
        points = [(float(v),) for v in values]
    else:
        points = [tuple(float(v) for v in row) for row in values]
    width = len(points[0])
    if width == 0 or any(len(row) != width for row in points):
        raise ValueError("all observations must have the same positive dimension")
    if any(not isfinite(v) for row in points for v in row):
        raise ValueError("samples must be finite")
    return points


def _chebyshev(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


def _digamma_integer(n: int) -> float:
    if n < 1:
        raise ValueError("digamma integer argument must be positive")
    return sum(1.0 / j for j in range(1, n)) - 0.5772156649015329


def ksg_mutual_information(x: Sequence, y: Sequence, k: int = 4) -> float:
    """KSG-1 MI estimator in bits using the joint Chebyshev metric.

    Assumes iid samples from a continuous joint distribution with few/no ties.
    A negative finite-sample estimate is possible and should not be clipped.
    Complexity is O(N^2 log N); intended for small reproducible teaching samples.
    """
    xp, yp = _as_points(x), _as_points(y)
    if len(xp) != len(yp) or len(xp) <= k or k < 1:
        raise ValueError("x,y must have equal length N > k >= 1")
    n = len(xp)
    terms = []
    for i in range(n):
        joint_distances = sorted(
            max(_chebyshev(xp[i], xp[j]), _chebyshev(yp[i], yp[j]))
            for j in range(n) if j != i
        )
        epsilon = joint_distances[k - 1]
        nx = sum(_chebyshev(xp[i], xp[j]) < epsilon
                 for j in range(n) if j != i)
        ny = sum(_chebyshev(yp[i], yp[j]) < epsilon
                 for j in range(n) if j != i)
        terms.append(_digamma_integer(nx + 1) + _digamma_integer(ny + 1))
    estimate_nats = (_digamma_integer(k) + _digamma_integer(n)
                     - sum(terms) / n)
    return estimate_nats / log(2.0)


def mine_dv_empirical_bound(joint_scores: Sequence[float],
                            marginal_scores: Sequence[float]) -> float:
    """Empirical DV objective in bits; not an unbiased finite-sample MI estimate."""
    if not joint_scores or not marginal_scores:
        raise ValueError("joint and marginal score samples must be nonempty")
    if any(not isfinite(v) for v in list(joint_scores) + list(marginal_scores)):
        raise ValueError("critic scores must be finite")
    maximum = max(marginal_scores)
    log_mean_exp = maximum + log(
        sum(exp(v - maximum) for v in marginal_scores) / len(marginal_scores)
    )
    return (sum(joint_scores) / len(joint_scores) - log_mean_exp) / log(2.0)


def info_nce_empirical_bound(score_rows: Sequence[Sequence[float]]) -> float:
    """InfoNCE lower-bound objective in bits; column zero is the positive pair.

    Each row contains one positive score followed by marginal-negative scores.
    The population lower-bound interpretation requires the appropriate sampling
    assumptions; the finite-sample objective is a training statistic.
    """
    rows = [tuple(float(v) for v in row) for row in score_rows]
    if not rows or len(rows[0]) < 2 or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("score matrix must be nonempty and rectangular with K >= 2")
    if any(not isfinite(v) for row in rows for v in row):
        raise ValueError("scores must be finite")
    k = len(rows[0])
    losses = []
    for row in rows:
        maximum = max(row)
        log_partition = maximum + log(sum(exp(v - maximum) for v in row))
        losses.append(log_partition - row[0])
    bound_nats = log(k) - sum(losses) / len(losses)
    return bound_nats / log(2.0)
