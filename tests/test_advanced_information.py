import unittest
from itertools import product
from math import inf
from examples.advanced_information import (
    crc_remainder, crc_encode, crc_burst_detects_all, crc32_iso_hdlc,
    conv_encode, viterbi_decode, otp_encrypt, otp_decrypt, otp_binary_leakage,
    binary_hamming_rate_distortion, gaussian_rate_distortion,
    reverse_water_filling, differential_entropy_uniform,
    differential_entropy_gaussian, differential_entropy_scaled,
    awgn_capacity_real, water_filling,
)

class AdvancedInformationTests(unittest.TestCase):
    def test_crc_examples_and_burst_guarantee(self):
        code=crc_encode("1101","1011")
        self.assertEqual(code,"1101001")
        self.assertEqual(crc_remainder(code,"1011"),"000")
        self.assertTrue(crc_burst_detects_all("1011"))
        for length in range(1,4):
            patterns=("1",) if length==1 else (("11",) if length==2 else
                ("1"+"".join(mid)+"1" for mid in product("01",repeat=length-2)))
            for pattern in patterns:self.assertNotEqual(crc_remainder(pattern,"1011"),"000")
    def test_crc32_standard_check(self):
        self.assertEqual(crc32_iso_hdlc(b"123456789"),0xCBF43926)
        self.assertEqual(crc32_iso_hdlc(b""),0)
    def test_viterbi_known_vector_and_single_flip(self):
        encoded=conv_encode("1011")
        self.assertEqual(encoded,"111000010111")
        self.assertEqual(viterbi_decode(encoded),"1011")
        self.assertEqual(viterbi_decode("111001010111"),"1011")
    def test_viterbi_all_short_messages(self):
        for n in range(1,6):
            for bits in product("01",repeat=n):
                message="".join(bits)
                self.assertEqual(viterbi_decode(conv_encode(message)),message)
    def test_otp_and_leakage(self):
        msg,key="101101","011010"
        self.assertEqual(otp_decrypt(otp_encrypt(msg,key),key),msg)
        self.assertAlmostEqual(otp_binary_leakage(.5),0)
        self.assertAlmostEqual(otp_binary_leakage(.8),.2780719051126377)
        self.assertAlmostEqual(otp_binary_leakage(0),1)
    def test_rate_distortion(self):
        self.assertAlmostEqual(binary_hamming_rate_distortion(.2,.1),.2529325012980811)
        self.assertEqual(binary_hamming_rate_distortion(.2,.2),0)
        self.assertAlmostEqual(gaussian_rate_distortion(1,.25),1)
        self.assertEqual(gaussian_rate_distortion(1,1),0)
        self.assertEqual(gaussian_rate_distortion(1,0),inf)
    def test_reverse_water_filling(self):
        theta,dist,rate=reverse_water_filling((1,4,9),4)
        self.assertAlmostEqual(theta,1.5)
        for a,b in zip(dist,(1,1.5,1.5)):self.assertAlmostEqual(a,b)
        self.assertAlmostEqual(rate,2)
        self.assertAlmostEqual(sum(dist),4)
    def test_differential_entropy(self):
        self.assertAlmostEqual(differential_entropy_uniform(.25),-2)
        self.assertAlmostEqual(differential_entropy_gaussian(1),2.047095585180641)
        self.assertAlmostEqual(differential_entropy_scaled(0,4),2)
    def test_awgn_and_water_filling(self):
        self.assertAlmostEqual(awgn_capacity_real(2,1),.792481250360578)
        powers,level,capacity=water_filling((1,2,4),6)
        for a,b in zip(powers,(10/3,7/3,1/3)):self.assertAlmostEqual(a,b)
        self.assertAlmostEqual(level,13/3)
        self.assertAlmostEqual(capacity,1.6732158261299042)
        self.assertAlmostEqual(sum(powers),6)

if __name__=="__main__":unittest.main()
