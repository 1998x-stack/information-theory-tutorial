"""Reproducible teaching models for information theory chapters 16–20.

CRC generic strings are MSB-first with init/xorout zero; CRC-32/ISO-HDLC is
implemented separately. Convolutional state is (previous, older) and generators
are (7,5)_8. Viterbi uses hard-decision Hamming metrics. AWGN capacities are
per real channel use; parallel subchannels are independent.
"""
from __future__ import annotations
from itertools import product
from math import inf, log2, pi, e


def _bits(value: str, allow_empty: bool = False) -> list[int]:
    if not isinstance(value, str) or (not value and not allow_empty) or set(value) - {"0", "1"}:
        raise ValueError("expected a binary string")
    return [int(ch) for ch in value]


def crc_remainder(bits: str, generator: str) -> str:
    """MSB-first polynomial remainder over GF(2), padded to degree(G) bits."""
    work, g = _bits(bits, True), _bits(generator)
    if len(g) < 2 or g[0] != 1 or g[-1] != 1:
        raise ValueError("generator must have positive degree and nonzero constant term")
    degree = len(g) - 1
    if len(work) >= len(g):
        for i in range(len(work) - len(g) + 1):
            if work[i]:
                for j, bit in enumerate(g):
                    work[i + j] ^= bit
    return "".join(map(str, work[-degree:] if degree <= len(work) else work)).rjust(degree, "0")


def crc_encode(message: str, generator: str) -> str:
    _bits(message)
    degree = len(generator) - 1
    if degree < 1:
        raise ValueError("generator degree must be positive")
    return message + crc_remainder(message + "0" * degree, generator)


def crc_burst_detects_all(generator: str) -> bool:
    """Exhaustively check every burst shape of length <= degree(G)."""
    g = _bits(generator)
    if len(g) < 2 or g[0] != 1 or g[-1] != 1:
        raise ValueError("generator must have positive degree and constant term 1")
    degree = len(g) - 1
    for length in range(1, degree + 1):
        if length == 1:
            patterns = ("1",)
        elif length == 2:
            patterns = ("11",)
        else:
            patterns = ("1" + "".join(mid) + "1" for mid in product("01", repeat=length - 2))
        for pattern in patterns:
            if set(crc_remainder(pattern, generator)) == {"0"}:
                return False
    return True


def crc32_iso_hdlc(data: bytes) -> int:
    """CRC-32/ISO-HDLC: poly=04C11DB7, init/xorout=FFFFFFFF, refin/refout."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be bytes-like")
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0xEDB88320 if crc & 1 else 0)
    return crc ^ 0xFFFFFFFF


def conv_encode(message: str, terminate: bool = True) -> str:
    """Rate-1/2 K=3 encoder (7,5)_8; state=(u[t-1],u[t-2])."""
    bits = _bits(message)
    state, output = 0, []
    for bit in bits + ([0, 0] if terminate else []):
        previous, older = (state >> 1) & 1, state & 1
        output.extend((bit ^ previous ^ older, bit ^ older))
        state = (bit << 1) | previous
    return "".join(map(str, output))


def viterbi_decode(received: str, terminate: bool = True) -> str:
    """Hard-decision Viterbi; terminated mode forces final state 00 and strips two tails."""
    bits = _bits(received)
    if len(bits) % 2:
        raise ValueError("rate-1/2 stream must contain bit pairs")
    if terminate and len(bits) < 4:
        raise ValueError("terminated frame must contain at least two trellis steps")
    pairs = [bits[i:i + 2] for i in range(0, len(bits), 2)]
    metrics, backpointers = [0, inf, inf, inf], []
    for pair in pairs:
        nxt, pred = [inf] * 4, [None] * 4
        for state in range(4):
            if metrics[state] == inf:
                continue
            previous, older = (state >> 1) & 1, state & 1
            for bit in (0, 1):
                output = (bit ^ previous ^ older, bit ^ older)
                new_state = (bit << 1) | previous
                branch = int(pair[0] != output[0]) + int(pair[1] != output[1])
                candidate = metrics[state] + branch
                if candidate < nxt[new_state]:
                    nxt[new_state], pred[new_state] = candidate, (state, bit)
        metrics = nxt
        backpointers.append(pred)
    state = 0 if terminate else min(range(4), key=lambda s: metrics[s])
    if metrics[state] == inf:
        raise ValueError("no valid trellis path")
    decoded = []
    for pred in reversed(backpointers):
        item = pred[state]
        if item is None:
            raise ValueError("incomplete survivor path")
        state, bit = item
        decoded.append(str(bit))
    decoded.reverse()
    if terminate:
        if decoded[-2:] != ["0", "0"]:
            raise ValueError("terminated path does not end with two zero tail bits")
        decoded = decoded[:-2]
    return "".join(decoded)


def otp_encrypt(plaintext: str, key: str) -> str:
    p, k = _bits(plaintext), _bits(key)
    if len(p) != len(k):
        raise ValueError("one-time pad key must match message length")
    return "".join(str(a ^ b) for a, b in zip(p, k))


def otp_decrypt(ciphertext: str, key: str) -> str:
    return otp_encrypt(ciphertext, key)


def binary_entropy(p: float) -> float:
    if not 0 <= p <= 1:
        raise ValueError("probability must lie in [0,1]")
    return 0.0 if p in (0, 1) else -p * log2(p) - (1-p) * log2(1-p)


def otp_binary_leakage(key_one_probability: float) -> float:
    """I(M;C) for uniform independent M and Bernoulli(q) XOR key K."""
    return 1.0 - binary_entropy(key_one_probability)


def binary_hamming_rate_distortion(p: float, distortion: float) -> float:
    if not 0 <= p <= 1 or distortion < 0:
        raise ValueError("invalid source probability or distortion")
    if distortion >= min(p, 1-p):
        return 0.0
    return binary_entropy(p) - binary_entropy(distortion)


def gaussian_rate_distortion(variance: float, distortion: float) -> float:
    if variance <= 0 or distortion < 0:
        raise ValueError("positive variance and nonnegative distortion required")
    if distortion == 0:
        return inf
    if distortion >= variance:
        return 0.0
    return 0.5 * log2(variance / distortion)


def reverse_water_filling(variances, total_distortion: float):
    """Independent Gaussian components: D_i=min(theta, variance_i)."""
    values = tuple(float(v) for v in variances)
    if not values or any(v <= 0 for v in values) or total_distortion < 0:
        raise ValueError("positive variances and nonnegative distortion required")
    if total_distortion == 0:
        return 0.0, tuple(0.0 for _ in values), inf
    if total_distortion >= sum(values):
        return max(values), values, 0.0
    lo, hi = 0.0, max(values)
    for _ in range(100):
        mid = (lo + hi) / 2
        if sum(min(mid, v) for v in values) > total_distortion:
            hi = mid
        else:
            lo = mid
    theta = (lo + hi) / 2
    distortions = tuple(min(theta, v) for v in values)
    rate = 0.5 * sum(log2(v / d) for v, d in zip(values, distortions) if d < v)
    return theta, distortions, rate


def differential_entropy_uniform(width: float) -> float:
    if width <= 0:
        raise ValueError("uniform interval width must be positive")
    return log2(width)


def differential_entropy_gaussian(variance: float) -> float:
    if variance <= 0:
        raise ValueError("variance must be positive")
    return 0.5 * log2(2 * pi * e * variance)


def differential_entropy_scaled(entropy: float, scale: float) -> float:
    if scale == 0:
        raise ValueError("scale must be nonzero")
    return entropy + log2(abs(scale))


def awgn_capacity_real(power: float, noise_variance: float) -> float:
    """Capacity in bits per real scalar channel use."""
    if power < 0 or noise_variance <= 0:
        raise ValueError("nonnegative power and positive noise variance required")
    return 0.5 * log2(1 + power / noise_variance)


def water_filling(noise_variances, total_power: float):
    """Optimal powers, water level and sum capacity for independent real AWGN channels."""
    noise = tuple(float(v) for v in noise_variances)
    if not noise or any(v <= 0 for v in noise) or total_power < 0:
        raise ValueError("positive noise variances and nonnegative power required")
    if total_power == 0:
        return tuple(0.0 for _ in noise), min(noise), 0.0
    lo, hi = min(noise), max(noise) + total_power
    for _ in range(100):
        level = (lo + hi) / 2
        if sum(max(level - n, 0.0) for n in noise) > total_power:
            hi = level
        else:
            lo = level
    level = (lo + hi) / 2
    powers = tuple(max(level - n, 0.0) for n in noise)
    capacity = sum(0.5 * log2(1 + p / n) for p, n in zip(powers, noise))
    return powers, level, capacity
