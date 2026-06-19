import re
import unittest

import numpy as np

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.utils.canonicalize import canonicalize
from signwriting.utils.canonicalize.canonicalize import _order_matters, _symbols_share_ink
from signwriting.visualizer.visualize import get_symbol_size, signwriting_to_image

# Real signs from the single_signs corpus, spanning a range of symbol counts
# and categories. Canonicalization must never change the rendered image.
CORPUS_SIGNS = [
    "M534x515S14420491x484S10020519x485S14420465x484",
    "M518x574S34400482x483S20300494x526S26c06496x547",
    "M517x539S15d2a483x460S19c50483x500S2f900492x534S26a14490x483S2f700498x473",
    "M566x520S36d00479x480S20500477x486S20500489x486S27100526x502S14c56492x496",
    "M524x520S15a11501x497S15a19476x497S20600487x479",
    "M535x530S30004482x483S15d10495x464S26504521x495S15d10494x503S20500509x507",
    "M538x523S1ea50514x478S1ea58462x479S26904522x503S26914462x505",
    "M511x527S1f902492x474S2e309488x504",
    "M530x514S15d48469x487S11552500x497S20600492x487",
    "M538x531S36500482x483S20500495x495S1ea10515x510S26507523x493",
    "M598x558S2f800490x441S2f801431x450S2f800454x441S2f800526x441S2f801410x473"
    "S2f802402x491S2f803412x527S2f804437x547S2f804473x547S2f804510x547S2f805547x522"
    "S2f805566x497S2f806587x461S2f800549x450",
    # Overlapping pairs: the first two reorder (harmless overlap), the last
    # keeps order (the right hand's fill covers the left hand's lines).
    "M544x527S11511503x500S33100482x482S20600522x495",
    "M518x529S10000469x499S30a00482x482",
    "M515x516S10010500x486S15d59485x484",
]


class CanonicalizeOverlapCase(unittest.TestCase):
    """A face glyph (S331) overlapping a hand glyph (S203). When they overlap,
    relative order is preserved; when they don't, the canonical category order
    (faces before hands) applies."""

    def test_overlapping_hand_then_face_preserved(self):
        self.assertEqual(
            "M521x518S20310506x499S33100482x482",
            canonicalize("M521x547S20310506x500S33100482x483"),
        )

    def test_overlapping_face_then_hand_preserved(self):
        self.assertEqual(
            "M521x518S33100482x482S20310506x499",
            canonicalize("M521x547S33100482x483S20310506x500"),
        )

    def test_non_overlapping_reorders_to_category_order(self):
        # Moving the face up (y 483 -> 443) breaks the overlap, so the canonical
        # order kicks in and the face is written before the hand.
        self.assertEqual(
            "M521x554S33100482x482S20310506x539",
            canonicalize("M521x547S20310506x500S33100482x443"),
        )

    def test_overlap_detection_is_glyph_not_box(self):
        face = {"symbol": "S33100", "position": (482, 483)}
        hand_touching = {"symbol": "S20310", "position": (506, 500)}
        hand_clear = {"symbol": "S20310", "position": (506, 460)}
        self.assertTrue(_symbols_share_ink(face, hand_touching))
        self.assertFalse(_symbols_share_ink(face, hand_clear))

    def test_order_matters_only_when_render_differs(self):
        face = {"symbol": "S33100", "position": (482, 482)}
        # S20310's white fill covers part of the face line, so order is visible.
        hand_opaque = {"symbol": "S20310", "position": (506, 500)}
        self.assertTrue(_order_matters(face, hand_opaque))
        # S11511 overlaps the face but renders identically either way.
        hand_transparent = {"symbol": "S11511", "position": (503, 500)}
        self.assertTrue(_symbols_share_ink(face, hand_transparent))
        self.assertFalse(_order_matters(face, hand_transparent))

    def test_overlap_reordered_when_render_unaffected(self):
        # S11511 (hand) overlaps S33100 (face) but order doesn't change the
        # image, so the face is moved ahead of the hand into canonical order.
        self.assertEqual(
            "M544x527S33100482x482S11511503x500S20600522x495",
            canonicalize("M544x527S11511503x500S33100482x482S20600522x495"),
        )


class CanonicalizeCategoryOrderCase(unittest.TestCase):
    """Non-overlapping symbols sort by category (faces, other, hands, contact,
    movement), then top-to-bottom, left-to-right."""

    def test_category_order(self):
        # One symbol per category, placed far apart so none overlap. Input is
        # in reverse-canonical order; output must be face, other, hand,
        # contact, movement.
        fsw = "M750x750S26500250x250S20500300x300S10000350x350S37000400x400S33000450x450"
        self.assertEqual(
            "M525x544S33000476x507S37000426x457S10000376x407S20500326x357S26500276x307",
            canonicalize(fsw),
        )

    def test_top_to_bottom_then_left_to_right_within_category(self):
        # Three non-overlapping hands; canonical order is by y, then x.
        fsw = "M540x540S10000510x510S10000260x510S10000510x260"
        positions = [s["position"] for s in fsw_to_sign(canonicalize(fsw))["symbols"]]
        self.assertEqual(sorted(positions, key=lambda p: (p[1], p[0])), positions)


class CanonicalizeBoxCase(unittest.TestCase):

    def test_box_is_tightened(self):
        # The input box (547) is looser than the symbols require; it is
        # recomputed to the tight bottom-right corner (and the sign centered).
        out = canonicalize("M521x547S20310506x500S33100482x483")
        self.assertTrue(out.startswith("M521x518"))

    def test_box_marker_preserved(self):
        self.assertTrue(canonicalize("L521x547S20310506x500S33100482x483").startswith("L"))
        self.assertTrue(canonicalize("R521x547S20310506x500S33100482x483").startswith("R"))


class CanonicalizeCenterCase(unittest.TestCase):
    """Centering ported from @sutton-signwriting/font-ttf signNormalize: a sign
    is moved so its center sits on (500, 500), pivoting on the face/trunk when
    present and the full bounding box otherwise."""

    def test_centers_horizontally_on_face(self):
        # Face plus a hand far to the right. Horizontal centering pivots on the
        # face (S2ff-S36c), so the face's midpoint lands on 500 - independent of
        # where the hand sits.
        out = canonicalize("M620x540S33000482x460S10000600x500")
        face = next(s for s in fsw_to_sign(out)["symbols"] if s["symbol"] == "S33000")
        left = face["position"][0]
        right = left + get_symbol_size("S33000")[0]
        self.assertEqual(500, int((left + right) / 2))

    def test_normalizes_translation(self):
        # The same sign shifted by a constant offset normalizes to one form.
        base = "M544x527S11511503x500S33100482x482S20600522x495"
        shifted = "M564x547S11511523x520S33100502x502S20600542x515"
        self.assertEqual(canonicalize(base), canonicalize(shifted))


class CanonicalizeContractCase(unittest.TestCase):

    def test_empty_sign_passes_through(self):
        self.assertEqual("M500x500", canonicalize("M500x500"))

    def test_rejects_non_ascii(self):
        with self.assertRaises(ValueError):
            canonicalize("𝠃𝤛𝤵񍉡𝣴𝣵")

    def test_is_idempotent(self):
        for fsw in CORPUS_SIGNS:
            with self.subTest(fsw=fsw):
                once = canonicalize(fsw)
                self.assertEqual(once, canonicalize(once))


class CanonicalizeMultiSignCase(unittest.TestCase):
    """``fsw_to_sign`` absorbs every symbol into the first box, so a whitespace-
    separated multi-sign string must be canonicalized one sign at a time rather
    than merged into a single box."""

    def test_each_sign_canonicalized_independently(self):
        first = "M532x585S30004482x483S1ce02487x518S1ce0a477x533S20500522x508S2eb34512x543S2eb10472x553"
        second = "M522x527S20300497x512S20320507x507S21400479x514S28a02484x474S20e00494x494"
        out = canonicalize(f"{first} {second}")
        self.assertEqual(f"{canonicalize(first)} {canonicalize(second)}", out)

    def test_signs_are_not_merged(self):
        first = "M532x585S30004482x483S1ce02487x518S1ce0a477x533S20500522x508S2eb34512x543S2eb10472x553"
        second = "M522x527S20300497x512S20320507x507S21400479x514S28a02484x474S20e00494x494"
        out = canonicalize(f"{first} {second}")
        self.assertEqual(2, len(out.split()))
        self.assertEqual(2, len(re.findall(r"[MLRB]\d{3}x\d{3}", out)))

    def test_whitespace_only_is_empty(self):
        self.assertEqual("", canonicalize("   "))


class CanonicalizeRenderEquivalenceCase(unittest.TestCase):
    """Reordering only swaps symbols whose draw order is invisible, and
    centering is a uniform translation, so the rendered image (cropped to its
    content) is pixel-identical to the original."""

    @staticmethod
    def _render(fsw: str):
        return np.array(signwriting_to_image(fsw, antialiasing=False, trust_box=False))

    def test_render_unchanged(self):
        for fsw in CORPUS_SIGNS:
            with self.subTest(fsw=fsw):
                original = self._render(fsw)
                canonical = self._render(canonicalize(fsw))
                self.assertEqual(original.shape, canonical.shape)
                self.assertTrue(np.array_equal(original, canonical))


if __name__ == "__main__":
    unittest.main()
