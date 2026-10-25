import unittest

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.formats.sign_to_fsw import sign_to_fsw


class SignToFswCase(unittest.TestCase):
    out_of_range = {"box": {"symbol": "M", "position": (1100, 900)},
                    "symbols": [{"symbol": "S10000", "position": (100, 500)},
                                {"symbol": "S20000", "position": (600, 700)}]}

    def test_out_of_range_is_clamped(self):
        sign = fsw_to_sign(sign_to_fsw(self.out_of_range))
        points = [sign["box"]["position"]] + [s["position"] for s in sign["symbols"]]
        self.assertTrue(all(250 <= v <= 750 for p in points for v in p))
        self.assertEqual(points, [(749, 749), (250, 500), (600, 700)])

    def test_out_of_range_raises_without_fix(self):
        with self.assertRaises(ValueError):
            sign_to_fsw(self.out_of_range, fix_out_of_range=False)


if __name__ == '__main__':
    unittest.main()
