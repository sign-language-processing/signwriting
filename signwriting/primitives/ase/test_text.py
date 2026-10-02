import unittest

from signwriting.fingerspelling.fingerspelling import spell
from signwriting.primitives.ase.dates import construct_day_of_month, construct_month, construct_year
from signwriting.primitives.ase.numbers import construct_integer
from signwriting.primitives.ase.text import construct_date, construct_number


class TextPrimitiveCase(unittest.TestCase):

    def test_integer_quantities(self):
        for text, value in [("156", 156), ("0", 0), ("1,234", 1234), ("1000000000", 1000000000)]:
            with self.subTest(text=text):
                self.assertEqual(construct_number(text), construct_integer(value))

    def test_decimal_digits_are_exact(self):
        for text, whole, fraction in [("0.0030", 0, "0030"), ("1,234.50", 1234, "50")]:
            self.assertEqual(construct_number(text), " ".join([
                construct_integer(whole), spell(".", language="ase", seed=0),
                spell(fraction, language="ase", vertical=False, seed=0),
            ]))

    def test_unsupported_numbers_abstain(self):
        for text in ["004", "03-04-2026", "12B", "1,5", "12,34", "-5", "1e6", "1/2", "", "１２",
                     "999999999999", "0." + "1" * 100, "9" * 5000]:
            with self.subTest(text=text):
                self.assertIsNone(construct_number(text))

    def test_dates_agree_across_unambiguous_forms(self):
        expected = " ".join([construct_month(3), construct_day_of_month(4), construct_year(2026)])
        for text in ["2026-03-04", "2026 - 03 - 04", "March 4, 2026", "March 4 , 2026", "4 march 2026"]:
            with self.subTest(text=text):
                self.assertEqual(construct_date(text), expected)

    def test_invalid_or_ambiguous_dates_abstain(self):
        for text in ["03-04-2026", "03/04/2026", "2026-02-29", "2026-13-01", "0000-01-01",
                     "March 32, 2026", "April 31, 2026", "next Tuesday", "March 4", "March 4, 2026 at noon"]:
            with self.subTest(text=text):
                self.assertIsNone(construct_date(text))
        self.assertIsNotNone(construct_date("2024-02-29"))
