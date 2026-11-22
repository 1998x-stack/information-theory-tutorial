"""Small deterministic discrete information-theory calculations.

Finite alphabets; probabilities must be normalized; logarithms use base two.
"""
from math import log2, isclose

def checked(ps):
    values = tuple(float(p) for p in ps)
    if not values or any(p < 0 or p > 1 for p in values) or not isclose(sum(values), 1.0, rel_tol=0, abs_tol=1e-10):
        raise ValueError("probabilities must be nonnegative and sum to one")
    return values

def entropy(ps):
    return -sum(p * log2(p) for p in checked(ps) if p)

def surprisal(p):
    if p <= 0 or p > 1:
        raise ValueError("event probability must lie in (0, 1]")
    return -log2(p)

def cross_entropy(ps, qs):
    p, q = checked(ps), checked(qs)
    if len(p) != len(q):
        raise ValueError("support lengths differ")
    if any(a > 0 and b == 0 for a, b in zip(p, q)):
        return float("inf")
    return -sum(a * log2(b) for a,b in zip(p,q) if a)

def kl(ps, qs):
    p, q = checked(ps), checked(qs)
    return cross_entropy(p, q) - entropy(p)

def bayes_positive(prior, sensitivity, false_positive):
    if not all(0 <= x <= 1 for x in (prior, sensitivity, false_positive)):
        raise ValueError("all inputs must be probabilities")
    num = sensitivity * prior
    den = num + false_positive * (1-prior)
    if den == 0:
        raise ValueError("positive test event has zero probability")
    return num / den

def bsc_information(error_probability):
    if not 0 <= error_probability <= 1:
        raise ValueError("crossover probability outside [0, 1]")
    return 1 - entropy((error_probability, 1-error_probability))

def _bits(seq, n):
    if len(seq) != n or not all(b in (0, 1) for b in seq):
        raise ValueError(f"expected {n} bits")
    return list(seq)

def otp_encrypt(message, key):
    """One-time pad: message XOR key on equal-length bit lists."""
    message, key = _bits(message, len(message)), _bits(key, len(message))
    return [m ^ k for m, k in zip(message, key)]

def otp_decrypt(ciphertext, key):
    return otp_encrypt(ciphertext, key)

def otp_reuse_xor(first, second):
    """XOR of two equal-length plaintexts: the reused key cancels out."""
    first, second = _bits(first, len(first)), _bits(second, len(first))
    return [a ^ b for a, b in zip(first, second)]

def min_entropy(probabilities):
    """H_inf = -log2(max p): worst-case unpredictability for guessing attacks."""
    from math import log2
    ps = checked(probabilities)
    return -log2(max(ps))

def awgn_capacity(snr):
    """Per-symbol AWGN capacity C=0.5*log2(1+snr) bits; snr is the linear P/sigma^2."""
    if snr < 0:
        raise ValueError("signal-to-noise ratio must be nonnegative")
    from math import log2
    return 0.5 * log2(1 + snr)


def water_filling(noise_variances, total_power, tolerance=1e-9):
    """Optimal parallel-Gaussian power allocation P_i=max(mu-sigma_i^2,0)."""
    noise = list(noise_variances)
    if not noise or total_power < 0 or any(n < 0 for n in noise):
        raise ValueError("need nonnegative variances and power")
    lo, hi = min(noise), max(noise) + total_power
    while hi - lo > tolerance:
        mid = (lo + hi) / 2
        if sum(max(mid - n, 0.0) for n in noise) < total_power:
            lo = mid
        else:
            hi = mid
    mu = (lo + hi) / 2
    return mu, [max(mu - n, 0.0) for n in noise]


if __name__ == "__main__":
    p, q = (.75,.25), (.5,.5)
    print("H(p)",entropy(p),"H(p,q)",cross_entropy(p,q),"KL",kl(p,q))
    print("Bayes test posterior",bayes_positive(.01,.9,.05))
