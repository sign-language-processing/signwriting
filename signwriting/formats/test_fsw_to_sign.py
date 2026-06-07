import re
import unittest

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.formats.fsw_to_swu import fsw2swu


def legacy_fsw_to_sign(fsw):
    boxes = re.finditer(r'([BLMR])(\d{3})x(\d{3})', fsw)
    box = next(boxes, None)
    box_symbol, x, y = box.groups() if box is not None else ("M", 500, 500)

    symbols = re.findall(r'(S[123][0-9a-f]{2}[0-5][0-9a-f])(\d{3})x(\d{3})', fsw)

    return {
        "box": {
            "symbol": box_symbol,
            "position": (int(x), int(y)),
        },
        "symbols": [{
            "symbol": s[0],
            "position": (int(s[1]), int(s[2])),
        } for s in symbols],
    }


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

    def test_matches_legacy_parser(self):
        cases = [
            '',
            'S10000493x489',
            'M123x456S1f720487x492',
            'AS10011S10019S2e704S2e748M525x535S2e748483x510S10011501x466S2e704510x500S10019476x475',
            'M530x538S37602508x462S15a11493x494S20e00488x510S22f03469x517',
            'M<s><s>M<s>p483',
        ]
        for fsw in cases:
            with self.subTest(fsw=fsw):
                self.assertEqual(fsw_to_sign(fsw), legacy_fsw_to_sign(fsw))

if __name__ == '__main__':
    unittest.main()
