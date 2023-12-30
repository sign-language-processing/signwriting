import unittest

from signwriting.formats.fsw_to_sign import fsw_to_sign


class ParseSignCase(unittest.TestCase):

    def test_get_box(self):
        fsw = 'M123x456S1f720487x492'
        sign = fsw_to_sign(fsw)
        self.assertEqual(sign["box"]["symbol"], "M")
        self.assertEqual(sign["box"]["position"], (123, 456))


if __name__ == '__main__':
    unittest.main()
