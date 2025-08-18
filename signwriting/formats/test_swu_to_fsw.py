import unittest

from signwriting.formats.swu import swu_add_prefix
from signwriting.formats.swu_to_fsw import swu2fsw


class SWUtoFSWCase(unittest.TestCase):
    def test_conversion(self):
        swu = '𝠀񀀒񀀚񋚥񋛩𝠃𝤟𝤩񋛩𝣵𝤐񀀒𝤇𝣤񋚥𝤐𝤆񀀚𝣮𝣭'
        fsw = swu2fsw(swu)
        self.assertEqual('AS10011S10019S2e704S2e748M525x535S2e748483x510S10011501x466S2e704510x500S10019476x475', fsw)

    def test_swu_add_prefix(self):
        swu = '𝠃𝤛𝤵񍉡𝣴𝣵񆄱𝤌𝤆񈠣𝤉𝤚𝠃𝤟𝤩񋛩𝣵𝤐񀀒𝤇𝣤񋚥𝤐𝤆񀀚𝣮𝣭'
        prediction = swu_add_prefix(swu)
        self.assertEqual('𝠀񍉡񆄱񈠣𝠃𝤛𝤵񍉡𝣴𝣵񆄱𝤌𝤆񈠣𝤉𝤚 𝠀񋛩񀀒񋚥񀀚𝠃𝤟𝤩񋛩𝣵𝤐񀀒𝤇𝣤񋚥𝤐𝤆񀀚𝣮𝣭', prediction)

if __name__ == '__main__':
    unittest.main()
