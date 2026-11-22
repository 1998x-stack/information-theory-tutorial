import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from foundations import entropy, surprisal, kl, cross_entropy, bayes_positive, bsc_information, otp_encrypt, otp_decrypt, otp_reuse_xor, min_entropy

class FoundationTests(unittest.TestCase):
    def test_otp_and_min_entropy(self):
        m, k = [1,0,1,1], [0,1,1,0]
        c = otp_encrypt(m, k)
        self.assertEqual(c, [1,1,0,1])
        self.assertEqual(otp_decrypt(c, k), m)
        self.assertEqual(otp_reuse_xor([0,1],[1,1]), [1,0])
        self.assertEqual(min_entropy([0.5,0.25,0.25]), 1.0)
        with self.assertRaises(ValueError):
            otp_encrypt([1,0,1],[0,1])
    def test_entropy(self):
        self.assertAlmostEqual(entropy([.5,.25,.125,.125]), 1.75)
        self.assertAlmostEqual(entropy([.5,.5]), 1.0)
        self.assertEqual(entropy([1,0]), 0)
    def test_surprisal(self):
        self.assertEqual(surprisal(.125), 3)
        with self.assertRaises(ValueError): surprisal(0)
    def test_bayes(self):
        self.assertAlmostEqual(bayes_positive(.01,.9,.05), 90/585)
    def test_kl(self):
        p, q = (.75,.25),(.5,.5)
        self.assertAlmostEqual(entropy(p)+kl(p,q),cross_entropy(p,q))
        self.assertAlmostEqual(kl(p,q), .18872187554086717)
        self.assertNotAlmostEqual(kl(p,q),kl(q,p))
        self.assertEqual(kl([1,0],[0,1]),math.inf)
    def test_bsc(self):
        self.assertAlmostEqual(bsc_information(.1),.5310044064107188)
        self.assertAlmostEqual(bsc_information(.5),0)
    def test_bad_distribution(self):
        with self.assertRaises(ValueError): entropy([.3,.3])
        with self.assertRaises(ValueError): kl([.5,.5],[1])
if __name__ == "__main__":
    unittest.main()
