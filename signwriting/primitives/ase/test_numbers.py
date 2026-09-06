import unittest

from signwriting.primitives.ase.numbers import _generate_float, _generate_integer


class NumberFormattingCase(unittest.TestCase):

    def test_english_grouping_does_not_depend_on_system_locale(self):
        self.assertEqual(list(_generate_integer(1549))[1], "1,549")
        self.assertEqual(list(_generate_float(1549.5))[1], "1,549.500000")


if __name__ == "__main__":
    unittest.main()
