import math
from fractions import Fraction as F
from itertools import product
import unittest

from examples.coding import (
    entropy, kraft_sum, shannon_lengths, huffman_codebook, decode_prefix,
    arithmetic_interval, arithmetic_decode, dyadic_prefix, typical_mass, adaptive_interval, adaptive_decode,
    gaussian_rate_distortion, bernoulli_rate_distortion
)

class CodingTests(unittest.TestCase):
    def test_rate_distortion(self):
        self.assertEqual(gaussian_rate_distortion(0.25), 1.0)
        self.assertEqual(gaussian_rate_distortion(0.0625), 2.0)
        self.assertEqual(gaussian_rate_distortion(1.0), 0.0)
        self.assertEqual(round(bernoulli_rate_distortion(0.1), 3), 0.531)
        self.assertEqual(round(bernoulli_rate_distortion(0.25), 3), 0.189)
        with self.assertRaises(ValueError):
            gaussian_rate_distortion(0.0)
        with self.assertRaises(ValueError):
            bernoulli_rate_distortion(0.6)
    def test_entropy_and_kraft(self):
        p=[.4,.3,.2,.1]
        self.assertAlmostEqual(entropy(p),1.8464393446710154)
        self.assertAlmostEqual(kraft_sum([1,2,3,3]),1.)
        self.assertGreater(kraft_sum([1,2,2,3]),1.)
        self.assertEqual(shannon_lengths(p),(2,2,3,4))
        with self.assertRaises(ValueError):
            kraft_sum([0,2])
        with self.assertRaises(ValueError):
            entropy([.3,.4])
    def test_huffman_optimal_sample(self):
        p={"A":.4,"B":.3,"C":.2,"D":.1}
        codes=huffman_codebook(p)
        self.assertEqual(set(codes),set(p))
        self.assertEqual({k:len(codes[k]) for k in p},{"A":1,"B":2,"C":3,"D":3})
        self.assertAlmostEqual(sum(p[k]*len(codes[k]) for k in p),1.9)
        for a,b in product(codes.values(),repeat=2):
            if a!=b: self.assertFalse(b.startswith(a))
        for message in ["","A","ABCD","DCCBBAA"]:
            self.assertEqual(decode_prefix("".join(codes[s] for s in message),codes),message)
        with self.assertRaises(ValueError):
            decode_prefix("0",{"A":"0","B":"01"})
    def test_arithmetic_exact_interval(self):
        p={"A":F(3,5),"B":F(2,5)}
        lo,hi=arithmetic_interval("ABA",p)
        self.assertEqual((lo,hi),(F(9,25),F(63,125)))
        self.assertEqual(dyadic_prefix(lo,hi),"011")
        self.assertEqual(arithmetic_decode(F(3,8),3,p),"ABA")
    def test_roundtrip_short_messages_all(self):
        p={"A":F(3,5),"B":F(2,5)}
        for n in range(1,7):
            for seq in product("AB",repeat=n):
                msg="".join(seq)
                lo,hi=arithmetic_interval(msg,p)
                prefix=dyadic_prefix(lo,hi)
                val=F(int(prefix,2),1<<len(prefix))
                self.assertGreaterEqual(val,lo)
                self.assertLessEqual(val+F(1,1<<len(prefix)),hi)
                self.assertEqual(arithmetic_decode(val,n,p),msg)
    def test_adaptive_roundtrip(self):
        self.assertEqual(adaptive_interval("ABA"),(F(1,3),F(5,12)))
        self.assertEqual(adaptive_decode(F(3,8),3),"ABA")
        for n in range(1,6):
            for seq in product("AB",repeat=n):
                message="".join(seq)
                lo,hi=adaptive_interval(message)
                bits=dyadic_prefix(lo,hi)
                v=F(int(bits,2),1<<len(bits))
                self.assertEqual(adaptive_decode(v,n),message)
        with self.assertRaises(ValueError):
            adaptive_interval("AX")

    def test_reject_invalid_model(self):
        with self.assertRaises(ValueError):
            arithmetic_interval("A",{"A":F(1,2)})
        with self.assertRaises(ValueError):
            arithmetic_interval("C",{"A":F(1,2),"B":F(1,2)})
        with self.assertRaises(ValueError):
            arithmetic_decode(F(1,1),1,{"A":F(1,1)})
    def test_aep_finite_n(self):
        self.assertAlmostEqual(typical_mass(8),.31146240234375)
        self.assertAlmostEqual(typical_mass(40),.8005436824591012)
        self.assertAlmostEqual(typical_mass(80),.948398039264617)
        self.assertAlmostEqual(typical_mass(160),.9954390793796618)
        with self.assertRaises(ValueError):
            typical_mass(0)

if __name__=="__main__":
    unittest.main()
