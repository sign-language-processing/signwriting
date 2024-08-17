import unittest

from signwriting.fingerspelling.fingerspelling import spell


class FingerspellingCase(unittest.TestCase):

    def test_successful_spelling(self):
        sign = spell("abc", language='en-us-ase-asl', vertical=True)
        self.assertEqual(sign, "M510x533S1f720487x466S14720493x486S16d20491x513")

    def test_unsuccessful_spelling_throws(self):
        long_word = "abcdefghijklmnopqrstuvwxyz"
        with self.assertRaises(ValueError):
            spell(long_word, language='en-us-ase-asl', vertical=True)


if __name__ == '__main__':
    unittest.main()
