import unittest

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.formats.fsw_to_swu import fsw2swu


class ParseSignCase(unittest.TestCase):

    def test_get_box(self):
        fsw = 'M123x456S1f720487x492'
        sign = fsw_to_sign(fsw)
        self.assertEqual(sign["box"]["symbol"], "M")
        self.assertEqual(sign["box"]["position"], (123, 456))

    def test_conversion(self):
        fsw = 'AS10011S10019S2e704S2e748M525x535S2e748483x510S10011501x466S2e704510x500S10019476x475'
        swu = fsw2swu(fsw)
        self.assertEqual(swu, '𝠀񀀒񀀚񋚥񋛩𝠃𝤟𝤩񋛩𝣵𝤐񀀒𝤇𝣤񋚥𝤐𝤆񀀚𝣮𝣭')

if __name__ == '__main__':
    unittest.main()
