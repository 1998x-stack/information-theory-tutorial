"""Regression checks for the three chapter 28 capstone projects."""
from __future__ import annotations

import math
import unittest
from random import Random

from examples.capstone import (
    arithmetic_decode, arithmetic_encode, bsc_transmit, build_huffman_codebook,
    entropy, hamming74_block_error_probability, hamming74_decode,
    hamming74_encode, huffman_decode, huffman_encode, kl_divergence,
    lzw_decode, lzw_encode, transmission,
)


class EntropyProjectTests(unittest.TestCase):
    def test_entropy_zero_term(self):
        self.assertAlmostEqual(entropy([.5, .5, 0]), 1)

    def test_entropy_probability_guard(self):
        with self.assertRaises(ValueError):
            entropy([.6, .6])

    def test_kl_support_not_fudged(self):
        self.assertEqual(kl_divergence([1, 0], [0, 1]), math.inf)
        self.assertAlmostEqual(kl_divergence([.5, .5], [.5, .5]), 0)


class CodecsProjectTests(unittest.TestCase):
    def test_huffman_expected_small_example(self):
        bits, book = huffman_encode("AAAABBCD")
        self.assertEqual(len(bits), 14)
        self.assertEqual(book, {"A": "0", "B": "10", "C": "110", "D": "111"})
        self.assertEqual(huffman_decode(bits, book), "AAAABBCD")

    def test_huffman_single_symbol_and_empty(self):
        for sample in ("", "AAAAAAA", "你你好你好", "AAAAABBCCDDDE"):
            bits, book = huffman_encode(sample)
            self.assertEqual(huffman_decode(bits, book), sample)

    def test_huffman_truncated_codeword(self):
        with self.assertRaises(ValueError):
            huffman_decode("11", {"A": "0", "B": "10", "C": "110", "D": "111"})

    def test_arithmetic_exact_roundtrip(self):
        for sample in ("", "AAAA", "AAAABBCD", "ABABABA", "ABRACADABRA", "你好世界你好"):
            bits, frequency, length = arithmetic_encode(sample)
            self.assertEqual(arithmetic_decode(bits, frequency, length), sample)

    def test_arithmetic_roundtrip_random(self):
        rng = Random(16)
        for n in range(1, 25):
            sample = "".join(rng.choice("ABCD") for _ in range(n))
            bits, model, length = arithmetic_encode(sample)
            self.assertEqual(arithmetic_decode(bits, model, length), sample)

    def test_lzw_roundtrip_various(self):
        for data in (b"", b"AAAAAA", b"TOBEORNOTTOBEORTOBEORNOT",
                     bytes(range(256)), "数据可复现".encode("utf-8")):
            self.assertEqual(lzw_decode(lzw_encode(data)), data)

    def test_lzw_invalid_first_code(self):
        with self.assertRaises(ValueError):
            lzw_decode([999])


class HammingChannelProjectTests(unittest.TestCase):
    def test_hamming_reference(self):
        self.assertEqual(hamming74_encode("1011"), "0110011")
        decoded, syndrome, recovered = hamming74_decode("0110011")
        self.assertEqual((decoded, syndrome, recovered), ("1011", 0, "0110011"))

    def test_hamming_corrects_every_single_position(self):
        for nibble in ("0000", "1011", "1111", "0101"):
            original = hamming74_encode(nibble)
            for i in range(7):
                received = list(original)
                received[i] = "1" if received[i] == "0" else "0"
                decoded, syndrome, recovered = hamming74_decode("".join(received))
                self.assertEqual(decoded, nibble)
                self.assertEqual(syndrome, i + 1)
                self.assertEqual(recovered, original)

    def test_double_errors_are_not_correctable(self):
        original = hamming74_encode("1011")
        corrupted = list(original)
        for i in (0, 2):
            corrupted[i] = "1" if corrupted[i] == "0" else "0"
        decoded, syndrome, _ = hamming74_decode("".join(corrupted))
        self.assertNotEqual(decoded, "1011")
        self.assertNotEqual(syndrome, 0)

    def test_bsc_deterministic_and_extremes(self):
        bits = "010110"
        self.assertEqual(bsc_transmit(bits, 0, 7)[0], bits)
        self.assertEqual(bsc_transmit(bits, 1, 7)[0], "101001")
        self.assertEqual(bsc_transmit(bits, .4, 17), bsc_transmit(bits, .4, 17))

    def test_hamming_block_error_probability(self):
        self.assertAlmostEqual(hamming74_block_error_probability(0), 0)
        p = .1
        expected = sum(math.comb(7, k) * p**k * (1-p)**(7-k)
                       for k in range(2, 8))
        self.assertAlmostEqual(hamming74_block_error_probability(p), expected)

    def test_noiseless_pipeline(self):
        r = transmission("AAAABBCD", p=0, seed=123)
        self.assertTrue(r["success"])
        self.assertEqual(r["source_bit_length"], 14)
        self.assertEqual(r["pad_bits"], 2)
        self.assertEqual(r["physical_uses"], 28)
        self.assertEqual(r["nonzero_syndromes"], 0)
        self.assertTrue(r["shared_metadata_not_counted"])

    def test_nonzero_noise_is_deterministic(self):
        for p in (.03, .1, .3):
            self.assertEqual(transmission(p=p, seed=5),
                             transmission(p=p, seed=5))

    def test_single_flip_in_each_hamming_block(self):
        source = "AAAABBCD"
        r = transmission(source, p=0)
        bits = list(r["channel_bits"])
        for i in range(0, len(bits), 7):
            bits[i] = "1" if bits[i] == "0" else "0"
        corrected = "".join(hamming74_decode("".join(bits[i:i+7]))[0]
                            for i in range(0, len(bits), 7))
        self.assertEqual(corrected[:r["source_bit_length"]], r["source_bits"])


if __name__ == "__main__":
    unittest.main()
