import random
import unittest

from signwriting.fingerspelling.fingerspelling import get_chars, spell, spell_text, tokenize, variant_signs


class FingerspellingCase(unittest.TestCase):

    def test_successful_spelling(self):
        sign = spell("abc", language='en-us-ase-asl', vertical=True)
        self.assertEqual(sign, "M510x533S1f720487x466S14720493x486S16d20491x513")

    def test_unsuccessful_spelling_throws(self):
        long_word = "abcdefghijklmnopqrstuvwxyz"
        with self.assertRaises(ValueError):
            spell(long_word, language='en-us-ase-asl', vertical=True)

    def test_spell_text_joins_words_with_space(self):
        random.seed(0)
        text_spelling = spell_text("hello world", language='en-us-ase-asl')

        random.seed(0)
        hello = spell("hello", language='en-us-ase-asl')
        world = spell("world", language='en-us-ase-asl')

        self.assertEqual(text_spelling, f"{hello} {world}")

    def test_variant_signs_returns_list_as_is(self):
        self.assertEqual(variant_signs(["a", "b"]), ["a", "b"])

    def test_variant_signs_returns_default_for_dict(self):
        plus = get_chars('en-us-ase-asl')['+']
        self.assertEqual(variant_signs(plus), ["M522x515S10018496x485S10012492x491S20500477x487"])

    def test_variant_signs_prioritizes_requested_variation(self):
        plus = get_chars('en-us-ase-asl')['+']
        self.assertEqual(variant_signs(plus, ["1hand"]), ["M508x507S1fb20493x488"])

    def test_variant_signs_falls_back_to_default_for_unknown_variation(self):
        plus = get_chars('en-us-ase-asl')['+']
        self.assertEqual(variant_signs(plus, ["2hands"]),
                         ["M522x515S10018496x485S10012492x491S20500477x487"])

    def test_spell_uses_requested_variation(self):
        one_hand = spell("+", language='en-us-ase-asl', variants=["1hand"])
        default = spell("+", language='en-us-ase-asl')
        self.assertNotEqual(one_hand, default)
        # the 1-hand "+" glyph is identical to the "t" glyph
        self.assertEqual(one_hand, spell("t", language='en-us-ase-asl'))

    def test_tokenize_splits_words_and_symbols(self):
        self.assertEqual(tokenize("google.com/test+ai"),
                         ["google", ".", "com", "/", "test", "+", "ai"])

    def test_tokenize_drops_whitespace_and_keeps_underscore(self):
        self.assertEqual(tokenize("hello  world_x"), ["hello", "world", "_", "x"])

    def test_spell_text_splits_non_alphanumeric_independently(self):
        random.seed(0)
        text_spelling = spell_text("google.com/test+ai", language='en-us-ase-asl')

        random.seed(0)
        tokens = [spell(token, language='en-us-ase-asl')
                  for token in ["google", ".", "com", "/", "test", "+", "ai"]]

        self.assertEqual(text_spelling, " ".join(tokens))

    def test_spell_text_applies_variants_across_url(self):
        url = "https://test-site.com/?p_n=+1%20800"

        random.seed(0)
        one_hand = spell_text(url, language='en-us-ase-asl', variants=["1hand"])

        random.seed(0)
        expected = " ".join(spell(token, language='en-us-ase-asl', variants=["1hand"])
                             for token in tokenize(url))
        self.assertEqual(one_hand, expected)

        # "+", "_" and "=" have 1-hand variations, so the result differs from the default spelling
        random.seed(0)
        default = spell_text(url, language='en-us-ase-asl')
        self.assertNotEqual(one_hand, default)


if __name__ == '__main__':
    unittest.main()
