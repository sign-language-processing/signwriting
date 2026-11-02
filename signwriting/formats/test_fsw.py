import unittest

from signwriting.formats.fsw import is_fsw


class FSWCase(unittest.TestCase):
    def test_complete_signs_and_punctuation(self):
        for text in [
            "M518x529S14c20481x471S27106503x489",
            "AS14c20S27106M518x529S14c20481x471S27106503x489",
            "B500x500S10000000x999",
            "L500x500S10000480x480 R500x500S10000480x480",
            "M510x509S19220492x490 S38800464x496",
            "S38700500x500 S38800500x500 S38900500x500 S38a00500x500 S38b00500x500",
            " \tM518x529S14c20481x471\nS38800464x496\r\n",
        ]:
            with self.subTest(text=text):
                self.assertTrue(is_fsw(text))

    def test_empty_incomplete_and_styled_text(self):
        for text in [
            "", " \t\n", "Hello", "𝠃𝤟𝤩񋛩𝣵𝤐",
            "M500x500", "M500x500S15d39", "AS10000M500x500",
            "AM500x500S10000480x480", "AS10000",
            "M500x500S10000480x480 M500x500S15d39",
            "M500x500S10000480x480-C", "junkM500x500S10000480x480",
            "M500x500S10000480x480junk",
            "M50x500S10000480x480", "M500x500S10000480x4800",
            "M٥٠٠x٥٠٠S10000480x480", "M500x500S40000480x480",
            "M500x500S10060480x480", "M500x500S1000g480x480",
            "S10000480x480", "S38800", "S38600480x480",
        ]:
            with self.subTest(text=text):
                self.assertFalse(is_fsw(text))


if __name__ == '__main__':
    unittest.main()
