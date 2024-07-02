import unittest

from signwriting.utils.join_signs import join_signs_vertical


class JoinSignsCase(unittest.TestCase):

    def test_join_two_characters(self):
        char_a = 'M507x507S1f720487x492'
        char_b = 'M507x507S14720493x485'
        result_sign = join_signs_vertical(char_a, char_b)
        self.assertEqual('M510x518S1f720487x481S14720493x496', result_sign)

    def test_join_alphabet_characters(self):
        chars = [
            "M510x508S1f720490x493", "M507x511S14720493x489", "M509x510S16d20492x490", "M508x515S10120492x485",
            "M508x508S14a20493x493", "M511x515S1ce20489x485", "M515x508S1f000486x493", "M515x508S11502485x493",
            "M511x510S19220490x491", "M519x518S19220498x499S2a20c482x483"
        ]
        result_sign = join_signs_vertical(*chars, spacing=10)
        # pylint: disable=line-too-long
        self.assertEqual(
            'M518x653S1f720490x347S14720493x372S16d20492x404S10120492x434S14a20493x474S1ce20489x499S1f000486x539S11502485x564S19220490x589S19220498x634S2a20c482x618',
            result_sign
        )

    def test_join_empty_sign(self):
        char_a = 'M507x507S1f720487x492'
        char_b = 'M507x507'
        result_sign = join_signs_vertical(char_a, char_b)
        self.assertEqual('M510x507S1f720487x492', result_sign)

if __name__ == '__main__':
    unittest.main()
