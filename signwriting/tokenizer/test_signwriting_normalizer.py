import unittest

from signwriting.tokenizer import normalize_signwriting


class NormalizeCase(unittest.TestCase):

    def test_normalizer_same_sign(self):
        fsw = 'M123x456S1f720487x492S1f720487x492'
        normalized = normalize_signwriting(fsw)
        self.assertEqual(fsw, normalized)

    def test_normalizer_removes_a(self):
        a_info = 'AS16d10S22b03S20500S15a28S31400'
        m_info = 'M536x550S15a28485x523S16d10519x484S22b03507x508S20500498x532S31400482x482'
        normalized = normalize_signwriting(a_info + m_info)
        self.assertEqual(m_info, normalized)

    def test_normalizer_creates_space(self):
        fsw_1 = 'M536x550S15a28485x523S16d10519x484S22b03507x508S20500498x532S31400482x482'
        fsw_2 = 'M123x456S15a28485x523S16d10519x484S22b03507x508S20500498x532S31400482x482'

        normalized = normalize_signwriting(fsw_1 + fsw_2)
        self.assertEqual(f"{fsw_1} {fsw_2}", normalized)

    def test_normalization_is_identity_regression_4(self):
        # https://github.com/sign-language-processing/signwriting/issues/4
        fsw_1 = "M511x510S2c734490x490"
        fsw_2 = "M510x518S2c105490x483"
        self.assertEqual(fsw_1, normalize_signwriting(fsw_1))
        self.assertEqual(fsw_2, normalize_signwriting(fsw_2))


if __name__ == '__main__':
    unittest.main()
