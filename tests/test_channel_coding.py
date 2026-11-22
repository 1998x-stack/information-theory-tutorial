import unittest
from itertools import product
from math import isclose
from examples.channel_coding import (
    lz77_tokens,lz77_decode,lz78_tokens,lz78_decode,
    bsc_matrix,bec_matrix,cascade_bsc,mutual_information,
    binary_entropy,blahut_arimoto,repetition_error_probability,
    exact_bsc_block_error,hamming74_encode,hamming74_correct,
    hamming74_syndrome,hamming74_extract,
    crc32_reflected,crc32_msb,
)

class ChannelCodingTests(unittest.TestCase):
    def test_lz77_overlap(self):
        tokens=lz77_tokens("ABCABCABC",window=16,min_match=3)
        self.assertEqual(tokens,[("lit","A"),("lit","B"),("lit","C"),("ref",3,6)])
        self.assertEqual(lz77_decode(tokens),"ABCABCABC")
        self.assertEqual(lz77_decode([("lit","A"),("ref",1,9)]),"A"*10)
        with self.assertRaises(ValueError):
            lz77_decode([("ref",4,2)])
    def test_lz78_phrases(self):
        self.assertEqual(lz78_tokens("ABABABA"),[(0,"A"),(0,"B"),(1,"B"),(3,"A")])
        self.assertEqual(lz78_decode(lz78_tokens("ABABABA")),"ABABABA")
    def test_lz_finite_exhaustive(self):
        for n in range(9):
            for seq in product("AB",repeat=n):
                text="".join(seq)
                self.assertEqual(lz77_decode(lz77_tokens(text,window=9,min_match=3)),text)
                self.assertEqual(lz78_decode(lz78_tokens(text)),text)
    def test_channels_and_cascade(self):
        self.assertEqual(bsc_matrix(.1),((.9,.1),(.1,.9)))
        self.assertEqual(bec_matrix(.25),((.75,0.,.25),(0.,.75,.25)))
        self.assertAlmostEqual(cascade_bsc(.1,.2),.26)
        self.assertAlmostEqual(mutual_information((.5,.5),bsc_matrix(.1)),1-binary_entropy(.1))
        self.assertAlmostEqual(mutual_information((.5,.5),bec_matrix(.25)),.75)
        self.assertAlmostEqual(mutual_information((.95,.05),bsc_matrix(.1)),
                               binary_entropy(.1+.05*.8)-binary_entropy(.1))
        with self.assertRaises(ValueError):
            mutual_information((.5,.5),((.9,.2),(.2,.8)))
    def test_capacity_numerics(self):
        cap,dist=blahut_arimoto(bsc_matrix(.1))
        self.assertAlmostEqual(cap,1-binary_entropy(.1),places=9)
        self.assertAlmostEqual(dist[0],.5,places=9)
        c2,p2=blahut_arimoto(((1.,0.),(.2,.8)))
        self.assertTrue(.6182<c2<.6183)
        self.assertTrue(.43<p2[1]<.44)
        c3,p3=blahut_arimoto(((1,0),(1,0)))
        self.assertAlmostEqual(c3,0)
        self.assertAlmostEqual(sum(p3),1.)
    def test_repetition_majority(self):
        self.assertAlmostEqual(repetition_error_probability(3,.1),.028)
        self.assertAlmostEqual(repetition_error_probability(5,.1),.00856)
        with self.assertRaises(ValueError):
            repetition_error_probability(4,.1)
    def test_finite_ml_error(self):
        book=("00000000","11110000","00001111","11111111")
        result=exact_bsc_block_error(book,.1)
        self.assertTrue(0<result<.5)
        self.assertEqual(exact_bsc_block_error(book,0),0)
        self.assertAlmostEqual(exact_bsc_block_error(("0","1"),.1),.1)
    def test_hamming_all_messages_all_one_flip(self):
        words=set()
        for bits in product("01",repeat=4):
            message="".join(bits)
            word=hamming74_encode(message)
            self.assertEqual(hamming74_syndrome(word),0)
            self.assertEqual(hamming74_extract(word),message)
            words.add(word)
            for i in range(7):
                corrupted=word[:i]+str(1-int(word[i]))+word[i+1:]
                self.assertEqual(hamming74_syndrome(corrupted),i+1)
                self.assertEqual(hamming74_correct(corrupted),word)
        self.assertEqual(len(words),16)
    def test_hamming_example(self):
        self.assertEqual(hamming74_encode("1011"),"0110011")
        self.assertEqual(hamming74_syndrome("0110111"),5)
        self.assertEqual(hamming74_correct("0110111"),"0110011")
        self.assertEqual(hamming74_extract("0110011"),"1011")
    def test_crc32_check_values(self):
        self.assertEqual(crc32_reflected(b"123456789"),0xCBF43926)
        self.assertEqual(crc32_reflected(b""),0x00000000)
        self.assertEqual(crc32_msb(b"123456789"),0xFC891918)
        # CRC is linear: a single-bit flip changes the remainder
        self.assertNotEqual(crc32_reflected(b"payload"),crc32_reflected(b"payloae"))
        with self.assertRaises(ValueError):
            crc32_reflected("not bytes")

if __name__=="__main__":
    unittest.main()
