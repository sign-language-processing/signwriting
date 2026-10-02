import unittest

from signwriting.hamnosys.handshapes.map import (HAND_BASES, hamnosys_to_sw, hand_symbols, handshapes,
                                                 key_to_symid, mappings, orientation, sw_to_hamnosys)


class MapCase(unittest.TestCase):
    def test_every_hand_base_has_a_mapping_entry(self):
        self.assertEqual(261, len(HAND_BASES))
        self.assertEqual(HAND_BASES, list(mappings().keys()))

    def test_mapped_values_are_hamnosys_character_lists(self):
        for key, spellings in mappings().items():
            self.assertIsInstance(spellings, list, key)
            for spelling in spellings:
                self.assertTrue(all(0xE000 <= ord(char) <= 0xE0F1 for char in spelling), key)

    def test_key_to_symid(self):
        self.assertEqual("01-01-001-01-01-01", key_to_symid("S10000"))
        self.assertEqual("01-10-015-01-03-06", key_to_symid("S20325"))

    def test_hand_symbols(self):
        self.assertEqual(["S100"], hand_symbols("M518x518S10011482x483"))
        # non-hand symbols (movement, face) are ignored
        self.assertEqual(["S203", "S15a"], hand_symbols("M528x528S20300500x500S15a20510x510S2ff00490x490"))

    def test_orientation(self):
        hamextfingeru, hamextfingerr, hamextfingero = "\ue020", "\ue022", "\ue029"
        hampalmu, hampalmd, hampalml = "\ue038", "\ue03c", "\ue03e"
        self.assertEqual(hamextfingeru + hampalmd, orientation(0, 0))  # wall plane, palm to signer
        self.assertEqual(hamextfingeru + hampalml, orientation(1, 0))  # side view
        self.assertEqual(hamextfingero + hampalmu, orientation(3, 0))  # floor plane, palm up
        self.assertEqual(hamextfingerr + hampalmd, orientation(0, 10))  # left hand mirrors rotation

    def test_sw_to_hamnosys(self):
        index = "\ue002\ue00d"  # hamfinger2 hamthumbacrossmod
        self.assertEqual(index, sw_to_hamnosys("S100"))
        self.assertEqual(index + orientation(0, 0), sw_to_hamnosys("S10000"))
        unmapped = next(key for key, spellings in mappings().items() if not spellings)
        self.assertIsNone(sw_to_hamnosys(unmapped + "00"))

    def test_hamnosys_to_sw(self):
        self.assertEqual("S100", hamnosys_to_sw("\ue002\ue00d"))
        self.assertIsNone(hamnosys_to_sw("\ue0f1"))

    def test_handshapes_tokenizer(self):
        # hamsymmlr hamflathand hamfingerbendmod hamthumboutmod hamextfingero hampalmu ...
        self.assertEqual(["\ue001\ue011\ue00c"], handshapes("\ue0e9\ue001\ue011\ue00c\ue029\ue038"))
        # thumb-between-fingers keeps hambetween; a trailing hambetween is a location relation
        self.assertEqual(["\ue000\ue071\ue0e6\ue072"], handshapes("\ue000\ue071\ue0e6\ue072"))
        self.assertEqual(["\ue001"], handshapes("\ue001\ue0e6\ue052"))
        # two hands, two tokens
        self.assertEqual(["\ue002\ue00d", "\ue001"], handshapes("\ue002\ue00d\ue020\ue001\ue038"))


if __name__ == "__main__":
    unittest.main()
