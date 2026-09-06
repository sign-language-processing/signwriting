import unittest

from signwriting.primitives.ase.punctuation import PUNCTUATION, construct_punctuation, generate_punctuation


class PunctuationCase(unittest.TestCase):

    def test_punctuation(self):
        expected = ((",", "S38700463x496"), (".", "S38800464x496"), (";", "S38900464x496"),
                    (":", "S38a00464x496"), ("(", "S38b00464x496"), (")", "S38b04464x496"))
        self.assertEqual(PUNCTUATION, dict(generate_punctuation()))
        for character, fsw in expected:
            with self.subTest(character=character):
                self.assertEqual(fsw, construct_punctuation(character))

    def test_unsupported_punctuation(self):
        with self.assertRaisesRegex(ValueError, "Unsupported punctuation"):
            construct_punctuation("!")


if __name__ == "__main__":
    unittest.main()
