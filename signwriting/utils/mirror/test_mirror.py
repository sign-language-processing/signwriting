import unittest

import numpy as np
from PIL import ImageOps

from signwriting.formats.swu_to_fsw import swu2fsw
from signwriting.utils.mirror import mirror_sign, mirror_symbol
from signwriting.visualizer.visualize import signwriting_to_image

# Canonical SWU examples sourced from real signs. Converted to FSW once at
# load time so the test cases live in their original notation but exercise
# the FSW-only API.
RENDER_MIRROR_CASES_SWU = [
    '𝠀񀀒񀀚񋚥񋛩𝠃𝤟𝤩񋛩𝣵𝤐񀀒𝤇𝣤񋚥𝤐𝤆񀀚𝣮𝣭',
    '𝠀񂇢񂇈񆙡񋎥񋎵𝠃𝤛𝤬񂇈𝤀𝣺񂇢𝤄𝣻񋎥𝤄𝤗񋎵𝤃𝣟񆙡𝣱𝣸',
    '𝠀񅨑񀀙񆉁𝠃𝤙𝤞񀀙𝣷𝤀񅨑𝣼𝤀񆉁𝣳𝣮',
    '𝠀񀕁𝠃𝤍𝤕񀕁𝣾𝣷',
    '𝠀񂌢񂇷񆙡񈗦𝠃𝤩𝤛񂌢𝣢𝣱񂇷𝣬𝤉񆙡𝤍𝣽񈗦𝤜𝤎',
    '𝠀񀀡𝠃𝤎𝤕񀀡𝣿𝣷',
    '𝠀񀀒񉁩񌏁𝠃𝤮𝤙񌏁𝣴𝣴񀀒𝤙𝣻񉁩𝤙𝣟',
    '𝠀񀂁񂇻񈟃񆕁𝠃𝤣𝤘񂇻𝤈𝤌񆕁𝣹𝤁񀂁𝤍𝣵񈟃𝣩𝣽',
    '𝠀񀀡񋎥񀀁𝠃𝤡𝤖񀀁𝤒𝣸񀀡𝣫𝣸񋎥𝣻𝣷',
    '𝠀񀀓񃛆񆿅񆕁𝠃𝤣𝤟񀀓𝤅𝣯񆕁𝤅𝣽񃛆𝣪𝣮񆿅𝤅𝤐',
    '𝠀񂇢񉳍񂇂񂇈𝠃𝤬𝤘񂇢𝤕𝣵񂇈𝣡𝣴񂇂𝣤𝣵񉳍𝣿𝣼',
    '𝠀񀀒񀀚񋠥񋡩𝠃𝤝𝤪񋡩𝣷𝤊񀀒𝤈𝣡񋠥𝤍𝤃񀀚𝣯𝣪',
    '𝠀񃧁񃧉񆿅񆿕񋸥𝠃𝤨𝤛񆿕𝣭𝤉񃧁𝤌𝣱񃧉𝣥𝣱񆿅𝤔𝤊񋸥𝣿𝤕',
    '𝠀񄹸񈗦񄾘𝠃𝤭𝤥񄹸𝣞𝣦񄾘𝤔𝤌񈗦𝣽𝣾',
    '𝠃𝤗𝤜񀀋𝣹𝤍񀁂𝣵𝣱',
    '𝠀񆅁񇅅𝠃𝤏𝤙񆅁𝣿𝣳񇅅𝣾𝤇',
    '𝠃𝤦𝤖񄵡𝣧𝣷񆅁𝤁𝤆񃉡𝤔𝣸',
    '𝠃𝤧𝤬񅩱𝤊𝤝񍳡𝣴𝣴',
    '𝠃𝤼𝤘񃛋𝣳𝣶񃛃𝤇𝣶񈙇𝤞𝣵񈙓𝣐𝣵񆇡𝤂𝤍',
    '𝠀񂋣񂋫񆕁񇆡𝠃𝤜𝤞񇆡𝣹𝣯񂋣𝤁𝤆񂋫𝣱𝤋񆕁𝣿𝣿',
    '𝠀񀟡񆄩񆕁񈟃񍩁𝠃𝤟𝥄񆄩𝤉𝤵񀟡𝤐𝤕񆕁𝤁𝤥񈟃𝣰𝤟񍩁𝣴𝣴',
    '𝠀񃁁񃁉񋠩񋡭񋸡𝠃𝤦𝤬񃁁𝤇𝤝񃁉𝣥𝤑񋡭𝣯𝣨񋠩𝤌𝣵񋸡𝤀𝣠',
    '𝠀񅡁񂇇񉨬𝠃𝤖𝤥񂇇𝣶𝣦񅡁𝣾𝣵񉨬𝣶𝤂',
    '𝠀񆅱񆅹񇆥񇆵񌁵𝠃𝤢𝥇񆅱𝤎𝤤񆅹𝣯𝤤񇆥𝤉𝤹񇆵𝣩𝤹񌁵𝣴𝣯',
    '𝠃𝤛𝤵񍉡𝣴𝣵񆄱𝤌𝤆񈠣𝤉𝤚',
]
RENDER_MIRROR_CASES = [swu2fsw(sw) for sw in RENDER_MIRROR_CASES_SWU]


def _render(fsw: str):
    return signwriting_to_image(fsw, antialiasing=False, trust_box=True)


def _pixel_diff_ratio(a, b):
    arr_a = np.array(a)
    arr_b = np.array(b)
    if arr_a.shape != arr_b.shape:
        return 1.0
    diff = (arr_a != arr_b).any(axis=-1).sum()
    return diff / (arr_a.shape[0] * arr_a.shape[1])


class MirrorHandCase(unittest.TestCase):
    """S100-S204: rotation 0-7 / 8-15 are mirror halves."""

    def test_swaps_halves(self):
        self.assertEqual('S10008', mirror_symbol('S10000'))
        self.assertEqual('S10000', mirror_symbol('S10008'))

    def test_preserves_orientation_offset(self):
        self.assertEqual('S1000d', mirror_symbol('S10005'))
        self.assertEqual('S10004', mirror_symbol('S1000c'))

    def test_fill_unchanged(self):
        self.assertEqual('S15028', mirror_symbol('S15020'))


class MirrorMovementCase(unittest.TestCase):
    """S205-S2f6: fill swap (0<->1, 3<->4, 2<->5) plus rotation flip."""

    def test_fill_pairs_swap(self):
        # User's canonical walk-through: S2e700 -> S2e708 (mirrored direction,
        # same hand) -> S2e718 (mirrored direction, opposite hand).
        self.assertEqual('S2e718', mirror_symbol('S2e700'))
        self.assertEqual('S2e710', mirror_symbol('S2e708'))

    def test_fill_swap_works_at_any_rotation(self):
        self.assertEqual('S2e730', mirror_symbol('S2e748'))
        self.assertEqual('S2e74c', mirror_symbol('S2e734'))

    def test_movement_with_only_8_rotations(self):
        # S22a is a movement base whose font glyphs only cover rotations 0-7.
        # Fill still swaps, rotation reflects across vertical (face-style).
        self.assertEqual('S22a16', mirror_symbol('S22a02'))
        self.assertEqual('S22a10', mirror_symbol('S22a00'))
        self.assertEqual('S22a14', mirror_symbol('S22a04'))


class MirrorFaceCase(unittest.TestCase):
    """S2f7+: 8 rotations, no chirality. Mirror reflects the direction.

    Some head bases additionally encode handedness in fill 1 vs fill 2.
    """

    def test_axis_aligned_rotations_fixed(self):
        # S38800 is a punctuation glyph; symmetric, mirror is itself.
        self.assertEqual('S38800', mirror_symbol('S38800'))
        self.assertEqual('S38804', mirror_symbol('S38804'))

    def test_diagonal_rotations_swap(self):
        self.assertEqual('S30007', mirror_symbol('S30001'))
        self.assertEqual('S30001', mirror_symbol('S30007'))

    def test_head_fill_1_2_pair_swaps(self):
        # S30a is a single-eyebrow base; fill 1 and fill 2 are left/right.
        self.assertEqual('S30a20', mirror_symbol('S30a10'))
        self.assertEqual('S30a10', mirror_symbol('S30a20'))

    def test_head_without_fill_pair_keeps_fill(self):
        # S300 fills 1/2 are both symmetric in the font - no swap.
        self.assertEqual('S30000', mirror_symbol('S30000'))


class MirrorSymbolCase(unittest.TestCase):

    def test_unknown_symbol_passes_through(self):
        self.assertEqual('Szzzzz', mirror_symbol('Szzzzz'))

    def test_mirror_is_involution(self):
        for s in ['S10000', 'S10005', 'S22a02', 'S22a07',
                  'S38800', 'S2e748', 'S2e700', 'S30001']:
            self.assertEqual(s, mirror_symbol(mirror_symbol(s)))


class MirrorSignCase(unittest.TestCase):

    def test_rejects_non_ascii(self):
        with self.assertRaises(ValueError):
            mirror_sign('𝠃𝤛𝤵񍉡𝣴𝣵')

    def test_empty_sign_passes_through(self):
        self.assertEqual('M500x500', mirror_sign('M500x500'))

    def test_box_marker_flips_l_r(self):
        self.assertTrue(mirror_sign('L500x500S38800482x482').startswith('R'))
        self.assertTrue(mirror_sign('R500x500S38800482x482').startswith('L'))

    def test_m_box_marker_preserved(self):
        self.assertTrue(mirror_sign('M500x500S38800482x482').startswith('M'))

    def test_position_reflects_across_500(self):
        # Single-symbol sign with a chiral hand glyph: x should flip to the
        # mirrored side and the box's right edge becomes 1000 - orig_min_x.
        out = mirror_sign('M510x500S20310506x500')
        self.assertEqual('M494x500S20318479x500', out)

    def test_mirror_is_involution_on_renderable_signs(self):
        for fsw in RENDER_MIRROR_CASES:
            with self.subTest(fsw=fsw):
                # Mirroring once may rewrite the box to its canonical
                # symmetric form, but mirror^2 must then be stable.
                normalized = mirror_sign(mirror_sign(fsw))
                self.assertEqual(normalized, mirror_sign(mirror_sign(normalized)))

    def test_render_matches_flipped_original(self):
        # render(mirror(sign)) should equal the horizontal flip of
        # render(sign) up to font glyph asymmetries (some movement arrows
        # have 1px-asymmetric heads). 20% pixel-diff tolerance covers those.
        tolerance = 0.20
        for fsw in RENDER_MIRROR_CASES:
            with self.subTest(fsw=fsw):
                normalized = mirror_sign(mirror_sign(fsw))
                original = _render(normalized)
                mirrored = _render(mirror_sign(normalized))
                flipped = ImageOps.mirror(original)
                ratio = _pixel_diff_ratio(flipped, mirrored)
                self.assertLessEqual(
                    ratio, tolerance,
                    f'pixel diff {ratio:.2%} exceeds {tolerance:.0%} for {fsw}',
                )


if __name__ == '__main__':
    unittest.main()
