import unittest

from signwriting.formats.swu import is_swu


class SWUtoFSWCase(unittest.TestCase):
    def test_signwriting_with_prefix_is_swu(self):
        text = '𝠀񀀒񀀚񋚥񋛩𝠃𝤟𝤩񋛩𝣵𝤐񀀒𝤇𝣤񋚥𝤐𝤆񀀚𝣮𝣭'
        self.assertTrue(is_swu(text))

    def test_signwriting_without_prefix_is_swu(self):
        text = '𝠃𝤟𝤩񋛩𝣵𝤐񀀒𝤇𝣤񋚥𝤐𝤆񀀚𝣮𝣭'
        self.assertTrue(is_swu(text))

    def test_signwriting_with_whitespace_is_swu(self):
        text = '𝠃𝤟𝤩񋛩𝣵𝤐񀀒𝤇𝣤񋚥𝤐𝤆񀀚𝣮𝣭 '
        self.assertTrue(is_swu(text))

    def test_fsw_is_not_swu(self):
        text = 'AS10011S10019S2e704S2e748M525x535S2e748483x510S10011501x466S2e704510x500S10019476x475'
        self.assertFalse(is_swu(text))

    def test_ascii_is_not_swu(self):
        text = 'Hello, world!'
        self.assertFalse(is_swu(text))

    def test_unicode_is_not_swu(self):
        text = 'שלום'
        self.assertFalse(is_swu(text))


if __name__ == '__main__':
    unittest.main()
