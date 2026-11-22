"""Executable capstone for information theory chapter 28.

Standard library only. The demonstration uses a pre-shared Huffman codebook and
payload bit length, not a self-describing compressed file format. Do not quote
its symbol-only bit counts as complete wire-format compression ratios.

Run: python3 -m examples.capstone
"""
from __future__ import annotations

import heapq
import json
import math
import random
from collections import Counter
from fractions import Fraction
from itertools import count


def entropy(probs):
    """Entropy in bits for a normalized finite discrete distribution."""
    p = tuple(float(v) for v in probs)
    if not p or any(not math.isfinite(x) or x < 0 for x in p):
        raise ValueError("probabilities must be nonnegative and finite")
    if abs(sum(p) - 1) > 1e-9:
        raise ValueError("probabilities must sum to one")
    return -sum(x * math.log2(x) for x in p if x)


def kl_divergence(p, q):
    """KL divergence in bits, with positive-over-zero support returning infinity."""
    p, q = tuple(p), tuple(q)
    entropy(p)
    entropy(q)
    if len(p) != len(q):
        raise ValueError("distributions must have equal support length")
    if any(a > 0 and b == 0 for a, b in zip(p, q)):
        return math.inf
    return sum(a * math.log2(a / b) for a, b in zip(p, q) if a)


def build_huffman_codebook(text):
    """Deterministic binary prefix tree; symbols are Unicode code points."""
    if not text:
        return {}
    frequency = Counter(text)
    ticket = count()
    heap = [(frequency[s], next(ticket), ("leaf", s)) for s in sorted(frequency)]
    heapq.heapify(heap)
    while len(heap) > 1:
        w1, _, left = heapq.heappop(heap)
        w2, _, right = heapq.heappop(heap)
        heapq.heappush(heap, (w1 + w2, next(ticket), ("branch", left, right)))
    root = heap[0][2]
    result = {}

    def visit(node, prefix):
        if node[0] == "leaf":
            result[node[1]] = prefix or "0"
        else:
            visit(node[1], prefix + "0")
            visit(node[2], prefix + "1")

    visit(root, "")
    return result


def huffman_encode(text, codebook=None):
    """Return (payload_bitstring, shared_codebook); header is not counted."""
    codes = build_huffman_codebook(text) if codebook is None else dict(codebook)
    try:
        return "".join(codes[s] for s in text), codes
    except KeyError as e:
        raise ValueError("unknown symbol in shared codebook") from e


def huffman_decode(bits, codebook):
    """Decode complete prefix codewords; reject invalid or incomplete bitstrings."""
    if not codebook:
        if bits:
            raise ValueError("nonempty payload requires codebook")
        return ""
    inverse = {}
    prefixes = set()
    for symbol, word in codebook.items():
        if not word or any(c not in "01" for c in word):
            raise ValueError("codebook must use nonempty binary codewords")
        if word in inverse:
            raise ValueError("duplicate codeword")
        inverse[word] = symbol
        prefixes.update(word[:i] for i in range(1, len(word)))
    if any(word in prefixes for word in inverse):
        raise ValueError("codebook is not prefix-free")
    acc = ""
    out = []
    for bit in bits:
        acc += bit
        if acc in inverse:
            out.append(inverse[acc])
            acc = ""
        elif acc not in prefixes:
            raise ValueError("invalid Huffman bitstream")
    if acc:
        raise ValueError("truncated Huffman codeword")
    return "".join(out)


def _ceil_fraction_product(fraction, scale):
    n = fraction.numerator * scale
    return (n + fraction.denominator - 1) // fraction.denominator


def arithmetic_encode(text):
    """Exact rational arithmetic coding with a dyadic *contained* interval.

    Returns (bits, frequencies, symbol_count). It is a pedagogical finite
    message coder, not a streaming finite-precision codec or on-wire protocol;
    the frequency table and original length must be transmitted separately.
    """
    if not text:
        return "", {}, 0
    if len(text) > 64:
        raise ValueError("exact Fraction arithmetic demonstration capped at 64 symbols")
    frequency = Counter(text)
    total = sum(frequency.values())
    cum = {}
    offset = Fraction(0)
    for symbol in sorted(frequency):
        portion = Fraction(frequency[symbol], total)
        cum[symbol] = (offset, offset + portion)
        offset += portion
    lo, hi = Fraction(0), Fraction(1)
    for symbol in text:
        span = hi - lo
        a, b = cum[symbol]
        old_lo = lo
        lo = old_lo + span * a
        hi = old_lo + span * b
    for n in range(0, 2049):
        scale = 1 << n
        k = _ceil_fraction_product(lo, scale)
        if Fraction(k + 1, scale) <= hi:
            return format(k, f"0{n}b") if n else "", dict(frequency), len(text)
    raise ArithmeticError("no finite dyadic interval found")


def arithmetic_decode(bits, frequencies, symbol_count):
    if symbol_count < 0 or any(bit not in "01" for bit in bits):
        raise ValueError("invalid encoded input")
    if symbol_count == 0:
        if bits or frequencies:
            raise ValueError("empty message must have empty metadata")
        return ""
    if sum(frequencies.values()) != symbol_count:
        raise ValueError("frequency metadata must match symbol count")
    if any(c < 1 for c in frequencies.values()):
        raise ValueError("frequency counts must be positive")
    if not frequencies:
        raise ValueError("missing arithmetic frequency model")
    scale = 1 << len(bits)
    numerator = int(bits or "0", 2)
    number = Fraction(2 * numerator + 1, 2 * scale)
    lo, hi = Fraction(0), Fraction(1)
    model = []
    c = Fraction(0)
    for symbol in sorted(frequencies):
        start = c
        c += Fraction(frequencies[symbol], symbol_count)
        model.append((symbol, start, c))
    out = []
    for _ in range(symbol_count):
        width = hi - lo
        relative = (number - lo) / width
        for symbol, a, b in model:
            if a <= relative < b:
                old_lo = lo
                lo = old_lo + width * a
                hi = old_lo + width * b
                out.append(symbol)
                break
        else:
            raise ValueError("dyadic point outside arithmetic interval")
    return "".join(out)


def lzw_encode(data):
    """Encode bytes as an unframed sequence of integer dictionary indices."""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("LZW tutorial accepts bytes")
    d = {bytes((i,)): i for i in range(256)}
    nxt = 256
    w = b""
    out = []
    for byte in data:
        c = bytes((byte,))
        wc = w + c
        if wc in d:
            w = wc
        else:
            out.append(d[w])
            d[wc] = nxt
            nxt += 1
            w = c
    if w:
        out.append(d[w])
    return out


def lzw_decode(codes):
    """Decode LZW code indices, including the KwKwK dictionary case."""
    codes = list(codes)
    if not codes:
        return b""
    d = {i: bytes((i,)) for i in range(256)}
    nxt = 256
    first = codes[0]
    if first not in d:
        raise ValueError("invalid initial LZW code")
    w = d[first]
    result = bytearray(w)
    for k in codes[1:]:
        if k in d:
            entry = d[k]
        elif k == nxt:
            entry = w + w[:1]
        else:
            raise ValueError("invalid LZW code")
        result.extend(entry)
        d[nxt] = w + entry[:1]
        nxt += 1
        w = entry
    return bytes(result)


def _binary(bits, *, length=None):
    if not isinstance(bits, str) or any(bit not in "01" for bit in bits):
        raise ValueError("expected a binary string")
    if length is not None and len(bits) != length:
        raise ValueError("unexpected bit length")
    return bits


def hamming74_encode(nibble):
    """Even-parity (7,4), parity at positions 1,2,4 and data at 3,5,6,7."""
    _binary(nibble, length=4)
    d1, d2, d3, d4 = map(int, nibble)
    p1, p2, p4 = d1 ^ d2 ^ d4, d1 ^ d3 ^ d4, d2 ^ d3 ^ d4
    return "".join(str(v) for v in (p1, p2, d1, p4, d2, d3, d4))


def hamming74_decode(word):
    """Return (decoded nibble, syndrome, corrected_codeword).

    Syndrome 0 means no parity-check failure, NOT 'the block is error-free'.
    For >=2 bit errors the single-error decoder may silently miscorrect.
    """
    _binary(word, length=7)
    values = list(map(int, word))
    syndrome = 0
    for index, value in enumerate(values, start=1):
        if value:
            syndrome ^= index
    if syndrome:
        values[syndrome - 1] ^= 1
    decoded = "".join(str(values[i]) for i in (2, 4, 5, 6))
    return decoded, syndrome, "".join(map(str, values))


def hamming74_block_error_probability(p):
    """BSC decoder block error for hard-decision SEC Hamming(7,4)."""
    if not 0 <= p <= 1:
        raise ValueError("p must lie in [0,1]")
    return 1 - (1 - p) ** 7 - 7 * p * (1 - p) ** 6


def bsc_transmit(bits, flip_probability, seed):
    _binary(bits)
    if not 0 <= flip_probability <= 1:
        raise ValueError("flip probability must lie in [0,1]")
    randomizer = random.Random(seed)
    received = []
    flips = []
    for position, bit in enumerate(bits):
        flipped = randomizer.random() < flip_probability
        received.append(str(1 - int(bit)) if flipped else bit)
        if flipped:
            flips.append(position)
    return "".join(received), tuple(flips)


def transmission(text="AAAABBCD", p=0.05, seed=2026):
    """Source coding → pad → Hamming(7,4) → BSC → syndrome decode → decode text.

    The codebook and original payload length are assumed shared out of band.
    """
    if not text:
        raise ValueError("capstone transmission requires nonempty text")
    source_bits, codebook = huffman_encode(text)
    payload_length = len(source_bits)
    pad_length = (-payload_length) % 4
    padded_bits = source_bits + "0" * pad_length
    channel_bits = "".join(hamming74_encode(padded_bits[i:i + 4])
                           for i in range(0, len(padded_bits), 4))
    observed_bits, flips = bsc_transmit(channel_bits, p, seed)
    decoded_blocks = [
        hamming74_decode(observed_bits[i:i + 7])
        for i in range(0, len(observed_bits), 7)
    ]
    received_payload = "".join(block[0] for block in decoded_blocks)[:payload_length]
    residual_errors = sum(a != b for a, b in zip(source_bits, received_payload))
    try:
        recovered = huffman_decode(received_payload, codebook)
    except ValueError:
        recovered = None
    return {
        "input": text, "codebook": codebook,
        "source_bits": source_bits,
        "source_bit_length": payload_length,
        "pad_bits": pad_length,
        "channel_bits": channel_bits,
        "physical_uses": len(channel_bits),
        "received_bits": observed_bits,
        "flipped_positions": flips,
        "channel_error_count": len(flips),
        "nonzero_syndromes": sum(bool(block[1]) for block in decoded_blocks),
        "received_payload": received_payload,
        "residual_payload_errors": residual_errors,
        "recovered": recovered,
        "success": recovered == text,
        "noise_probability": p, "seed": seed,
        "shared_metadata_not_counted": True,
    }


def main():
    example = "AAAABBCD"
    hbits, book = huffman_encode(example)
    abits, freq, n = arithmetic_encode(example)
    lzw = lzw_encode(example.encode("utf-8"))
    assert huffman_decode(hbits, book) == example
    assert arithmetic_decode(abits, freq, n) == example
    assert lzw_decode(lzw) == example.encode("utf-8")
    print("Project 1: H([0.5,0.5]) =", entropy([0.5, 0.5]), "bit")
    print("Project 2: sample =", example)
    print("  Huffman payload:", len(hbits), "bits; codebook off-band", book)
    print("  Exact arithmetic dyadic payload:", len(abits), "bits; model & length off-band")
    print("  LZW indices:", len(lzw), "; no packed bit-length claim")
    for probability in (0.0, 0.05, 0.1, 0.2):
        r = transmission(example, p=probability, seed=2026)
        print(f"Project 3: p={probability:.2f}, "
              f"physical={r['physical_uses']} bits, "
              f"channel_flips={r['channel_error_count']}, "
              f"residual_errors={r['residual_payload_errors']}, "
              f"success={r['success']}, "
              f"Hamming_BLER={hamming74_block_error_probability(probability):.4f}")
    print("NOTE: tiny toy; codebook, header, framing and model costs omitted.")


if __name__ == "__main__":
    main()
