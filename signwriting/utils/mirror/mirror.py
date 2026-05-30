"""Horizontal mirror for SignWriting symbols and signs.

The Sutton SignWriting symbol set (ISWA) splits into ranges that mirror
differently. This module groups them as:

* **Hands** (S100-S204): each base has 16 rotations - 0-7 are right-hand at
  eight compass directions, 8-15 are the corresponding left-hand variants.
  The mirror is the matching half: ``rotation -> (rotation + 8) % 16``.
* **Contact** (S205-S216: touch, grasp, strike, brush, rub, surface,
  squeeze): fills encode visual variants (e.g. two vs three asterisks), not
  handedness, so the fill is preserved. Rotations cover ``n`` evenly-spaced
  angles around the circle (``n`` is 1, 4, or 8 depending on the base), and
  horizontal mirror reflects ``rotation -> (n - rotation) % n``.
* **Movement arrows** (S217-S2f6): fills encode arrow style (e.g. small vs
  large arrowhead, hollow vs filled), not handedness, so the fill is
  preserved. Bases that ship all 16 rotations use the hand convention
  ``rotation -> (rotation + 8) % 16`` (rotations 0-7 are one chirality at
  eight compass directions; 8-15 are the corresponding mirrored variants).
  Bases that ship fewer rotations use the contact convention
  ``rotation -> (n - rotation) % n``.
* **Everything else** (S2f7+: dynamics, heads, faces, eyes, mouth, trunk,
  ...): only eight rotations exist. Mirroring reflects the direction across
  the vertical axis: ``0`` and ``4`` are fixed, and the diagonals swap
  (``1<->7``, ``2<->6``, ``3<->5``). Some head bases (e.g. asymmetric
  eyebrows) additionally encode handedness in fill ``1`` vs fill ``2``; we
  swap that pair when the partner glyph exists.

The four sections above describe the *default* rule for each range. Many
individual bases deviate (the same compass direction can encode chirality
in the rotation, the fill, or neither depending on the glyph family), so
the bulk of this module is a set of per-base override tables - the
``_*_BASES`` frozensets and ``_*_OVERRIDES`` / ``_*_MAPS`` dicts below.
Each table names the bases it covers and the rule it applies; the
dispatchers (`_mirror_movement`, `_mirror_face`) consult them before
falling back to the section default. The tables were calibrated against a
corpus of human-confirmed mirror pairs (see ``test_mirror.py``), and every
existing ISWA symbol satisfies ``mirror(mirror(s)) == s``.

The sign-level mirror reflects each symbol's x-position across ``x = 500``
(the box centerline), recomputes the box's right edge, and flips the ``L``
and ``R`` lane markers.

The symbol-level rotation logic started as a section-typed reformulation of
signmaker's ``ssw.mirror`` (https://github.com/sutton-signwriting/signmaker)
and was extended with the per-base tables described above.
"""
import warnings
from functools import lru_cache
from typing import Tuple

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.formats.sign_to_fsw import sign_to_fsw
from signwriting.visualizer.visualize import get_symbol_size

# Symbols whose horizontal mirror is not representable as another ISWA
# symbol in the font. ``mirror_symbol`` returns them unchanged and emits a
# warning so callers know the result is approximate.
_NO_MIRROR_SYMBOLS = frozenset({
    "S2ef24", "S2ef25",
    "S2f024", "S2f025",
})

# One-off per-symbol overrides for cases that don't fit any base-level
# rule. mirror_symbol consults this (and its inverse) first, which both
# produces the mapping AND short-circuits the section dispatch - so a
# self-entry like S32630->S32630 is meaningful: it pins those symbols as
# self-mirror, overriding the _FACE_WITH_0_4_SWAP_* rule the rest of S326
# follows.
_SPECIAL_MIRROR_OVERRIDES = {
    "S32320": "S32324",
    "S32630": "S32630",
    "S32634": "S32634",
}
# Pre-computed inverse for an O(1) reverse lookup in mirror_symbol. Exclude
# self-pairs: they're already served by the forward dict, and a self-entry
# in the reverse dict would be redundant.
_SPECIAL_MIRROR_REVERSE = {
    dst: src for src, dst in _SPECIAL_MIRROR_OVERRIDES.items() if dst != src
}

# Shared fill-mirror dicts used across multiple "face/dynamics" bases.
_FILL_0_1_SWAP = {"0": "1", "1": "0"}
_FILL_23_SWAP = {"2": "3", "3": "2"}
_FILL_45_SWAP = {"4": "5", "5": "4"}
_FILL_01_23_SWAP = {**_FILL_0_1_SWAP, **_FILL_23_SWAP}
_FILL_01_23_45_SWAP = {**_FILL_01_23_SWAP, **_FILL_45_SWAP}
_FILL_12_34_SWAP = {"1": "2", "2": "1", "3": "4", "4": "3"}
_FILL_12_45_SWAP = {"1": "2", "2": "1", **_FILL_45_SWAP}


# ---------------------------------------------------------------------------
# Section dispatch
# ---------------------------------------------------------------------------
_HAND_BASE_MIN, _HAND_BASE_MAX = 0x100, 0x204
_CONTACT_BASE_MIN, _CONTACT_BASE_MAX = 0x205, 0x216
_MOVEMENT_BASE_MIN, _MOVEMENT_BASE_MAX = 0x217, 0x2f6


def _section(base: str) -> str:
    base_value = int(base[1:], 16)
    if _HAND_BASE_MIN <= base_value <= _HAND_BASE_MAX:
        return "hand"
    if _CONTACT_BASE_MIN <= base_value <= _CONTACT_BASE_MAX:
        return "contact"
    if _MOVEMENT_BASE_MIN <= base_value <= _MOVEMENT_BASE_MAX:
        return "movement"
    return "other"


def _symbol_exists(symbol: str) -> bool:
    try:
        width, height = get_symbol_size(symbol)
    except (ValueError, OverflowError):
        return False
    return width > 0 and height > 0


# ---------------------------------------------------------------------------
# Hands  (S100-S204)
# ---------------------------------------------------------------------------
def _mirror_hand(fill: str, rotation: int) -> Tuple[str, int]:
    return fill, (rotation + 8) % 16


# ---------------------------------------------------------------------------
# Contact  (S205-S216)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=None)
def _contact_rotation_count(base: str, fill: str) -> int:
    # Number of contiguous rotations (from 0) the font defines for this
    # base+fill. Probes the font, so cache the (base, fill) -> n result.
    n = 0
    for r in range(16):
        if _symbol_exists(f"{base}{fill}{r:x}"):
            n = r + 1
        else:
            break
    return n


def _mirror_contact(base: str, fill: str, rotation: int) -> Tuple[str, int]:
    # Rotations span 0..n-1 at evenly-spaced angles, so horizontal mirror is
    # rotation -> (n - rotation) % n.
    n = _contact_rotation_count(base, fill)
    if n == 0:
        return fill, rotation
    return fill, (n - rotation) % n


# ---------------------------------------------------------------------------
# Face, head, dynamics, eyes, mouth, ...  (S2f7+)
# ---------------------------------------------------------------------------
_FACE_ROTATION_MIRROR = {0: 0, 1: 7, 2: 6, 3: 5, 4: 4, 5: 3, 6: 2, 7: 1}
_FACE_FILL_MIRROR = {"1": "2", "2": "1"}

# 16-rotation "other" bases that follow the hand-style +8 convention
# instead of the 8-rotation face reflection. Mostly body/movement glyphs
# that aren't really "faces":
#   S308 Face Direction Positions, Nose Up or Down
#   S309 Face Direction Positions, Nose Up or Down Tilting
#   S327 Eyegaze Curved Wall Plane
#   S36f Shoulder Hip Move Wall Plane
#   S370 Shoulder Hip Move Floor Plane
#   S371 Shoulder Tilts (from Waist)
#   S37e Fingers
_OTHER_16_ROTATION_BASES = frozenset({
    "S308", "S309", "S327", "S36f", "S370", "S371", "S37e",
})

# Limb Length 1..7 (S377-S37d): rotation 0 (vertical down) and rotation 8
# (vertical up) are axis-aligned and self-mirror; all other rotations
# follow the +8 chirality swap. (S376 Limb Combinations uses a slightly
# different map - see _OTHER_BASE_ROTATION_MAPS.)
_LIMB_BASES = frozenset({
    "S377", "S378", "S379", "S37a", "S37b", "S37c", "S37d",
})


def _mirror_limb_rotation(rotation: int) -> int:
    if rotation in (0, 8):
        return rotation
    return (rotation + 8) % 16

# Per-base fill chirality pairs. The default rule is fill 1 <-> fill 2 (the
# "asymmetric head feature" rule that applies to single-eyebrow S30a etc.).
# These bases override that default:
#   S329 Eyegaze Circles Wall   - fill never swaps; rotation uses XOR 4
#   S32c Cheeks Sucked          - both 1/2 and 3/4 swap
#   S330 Ears                   - both 1/2 and 3/4 swap
#   S33a Breath Inhale          - fills 0/1, 2/3, 4/5 all pair
#   S357 Mouth Wrinkles Single  - fills 4/5 swap
#   S358 Mouth Wrinkles Double  - fills 4/5 swap
#   S361 Teeth                  - fills are independent variants, no swap
#   S368 Jaw Move Wall Plane    - no fill swap, only face-style rotation
#   S369 Jaw Move Floor Plane   - no fill swap
#   S36f-S371 (shoulders)       - no fill swap; rotation uses +8
#   S386 Location Limbs Digits  - no fill swap; rotation uses XOR 4
# Bases in the "other" section whose fills are independent variants - no
# fill swap on mirror. (Rotation handling varies; that's in the other
# rotation sets below.)
_NO_FILL_SWAP_BASES = frozenset({
    "S302", "S304", "S305", "S306", "S307", "S308", "S309",
    "S321", "S322", "S323", "S324", "S325", "S326", "S327", "S328", "S329",
    "S361", "S368", "S369", "S36f", "S370", "S371",
    "S372", "S373", "S374", "S376", "S37e", "S382", "S386", "S387",
})
_FACE_FILL_OVERRIDES = {
    # Eyebrow-shape fill swap (1<->2 and 4<->5).
    "S30a": _FILL_12_45_SWAP, "S30b": _FILL_12_45_SWAP,
    "S30c": _FILL_12_45_SWAP, "S30d": _FILL_12_45_SWAP,
    "S30e": _FILL_12_45_SWAP, "S30f": _FILL_12_45_SWAP,
    "S310": _FILL_12_45_SWAP,
    "S335": _FILL_12_45_SWAP,  # Air Blowing Out.
    "S336": _FILL_12_45_SWAP,  # Air Sucking In.
    "S356": _FILL_12_45_SWAP,  # Mouth Corners.
    # 1<->2 AND 3<->4 swap.
    "S317": _FILL_12_34_SWAP,  # Eye Blink Single (other S314-S320 use default).
    "S32b": _FILL_12_34_SWAP,  # Cheeks Neutral.
    "S32c": _FILL_12_34_SWAP,  # Cheeks Sucked.
    "S330": _FILL_12_34_SWAP,  # Ears.
    # 4<->5 swap only.
    "S357": _FILL_45_SWAP,
    "S358": _FILL_45_SWAP,
    "S365": _FILL_45_SWAP,
    # 2<->3 swap only.
    "S36b": _FILL_23_SWAP,  # Hair.
    "S36c": _FILL_23_SWAP,  # Excitement.
    # Fast / Tense / Relaxed - fills 0<->1 and 2<->3.
    "S2f7": _FILL_01_23_SWAP,
    "S2f9": _FILL_01_23_SWAP,
    "S2fa": _FILL_01_23_SWAP,
    # Breath Exhale / Breath Inhale - fills 0<->1, 2<->3, 4<->5.
    "S339": _FILL_01_23_45_SWAP,
    "S33a": _FILL_01_23_45_SWAP,
}

# Bases where rotation k mirrors to rotation k XOR 4 (rather than the
# default face-style 8-rotation reflection). Works for both 8- and
# 16-rotation bases:
#   S328 Eyegaze Curved Floor Plane                                  8 rot
#   S329 Eyegaze Circles Wall Plane                                  8 rot
#   S386 Location Limbs Digits                                      16 rot
#       (XOR 4 keeps the lower and upper halves distinct)
_OTHER_XOR_4_BASES = frozenset({
    "S328",
    "S329",
    "S386",
})

# Bases where rotation k mirrors to rotation k XOR 2 (4-rotation set).
#   S304 Head Movement Curves Wall Plane
#   S305 Head Movement Curves Floor Plane
#   S372 Torso Straight Stretch Wall
#   S373 Torso Curved Bend Wall
#   S374 Torso Twist Floor Plane
_OTHER_XOR_2_BASES = frozenset({
    "S304", "S305", "S372", "S373", "S374",
})

# Per-base rotation override maps for "other" range bases that don't fit
# any of the simpler rules.
#   S382 Location Width (9 rotations): 0 self, (1,2), (3,4), (5,6), (7,8).
#   S376 Limb Combinations (16 rotations): 0/8 self; 1<->9, 2<->a, 3<->b,
#   4<->c (lower half +8), 5<->e, 6<->f, 7<->d (upper half differs).
_OTHER_BASE_ROTATION_MAPS = {
    "S382": {0: 0, 1: 2, 2: 1, 3: 4, 4: 3, 5: 6, 6: 5, 7: 8, 8: 7},
    "S376": {
        0: 0, 1: 9, 2: 10, 3: 11, 4: 12, 5: 14, 6: 15, 7: 13,
        8: 8, 9: 1, 10: 2, 11: 3, 12: 4, 13: 7, 14: 5, 15: 6,
    },
}

# Bases where rotation k mirrors to rotation k XOR 1 (2-rotation set).
#   S302 Head Movement Tilts Wall Plane
_OTHER_XOR_1_BASES = frozenset({
    "S302",  # Head Movement Tilts Wall Plane (2 rotations)
    "S306",  # Head Movement Circles (4 rotations: 0<->1, 2<->3)
    "S307",  # Face Direction Positions, Nose Forward Tilting (2 rotations)
})

# (S321-S326 Eyegaze Straight use plain face-style rotation reflection
# with no fill swap - see _FACE_FILL_OVERRIDES.)

# Bases that use a face-style rotation reflection with rotations 0 and 4
# swapped (instead of being self-mirror). The 0/4 axis-aligned positions
# encode chirality rather than being symmetric.
#   S326 Eyegaze Straight Floor Alternate
#   S387 Comma
_FACE_WITH_0_4_SWAP_BASES = frozenset({
    "S326", "S387",
})
_FACE_WITH_0_4_SWAP_ROTATION = {0: 4, 1: 7, 2: 6, 3: 5, 4: 0, 5: 3, 6: 2, 7: 1}

# Per-(base, fill) rotation override maps. Used for bases where the rotation
# rule depends on which fill we're at - e.g. Shoulder Hip Positions (S36e),
# where fill 0 is the only one with rotation 0 as self.
_PER_FILL_ROTATION_MAPS = {
    # Shoulder Hip Positions (S36e). 5 fills x 6 rotations.
    # Fill 0:        0 self, 1<->5, 2<->4, 3 self.
    # Fills 1,2,3:   0<->3, 1<->5, 2<->4.
    # Fill 4:        0<->1, 2 self, 3 self, 4<->5.
    "S36e": {
        "0": {0: 0, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1},
        "1": {0: 3, 1: 5, 2: 4, 3: 0, 4: 2, 5: 1},
        "2": {0: 3, 1: 5, 2: 4, 3: 0, 4: 2, 5: 1},
        "3": {0: 3, 1: 5, 2: 4, 3: 0, 4: 2, 5: 1},
        "4": {0: 1, 1: 0, 2: 2, 3: 3, 4: 5, 5: 4},
    },
    # Torso Straight Stretch Wall (S372): default is XOR-2, but fill 2 has
    # rotations 0 and 2 as self (with 1<->3 still pairing via XOR-2).
    "S372": {
        "2": {0: 0, 1: 3, 2: 2, 3: 1},
    },
}


def _face_rotation(base: str, rotation: int) -> int:
    """Resolve the rotation rule for an "other" base."""
    if base in _LIMB_BASES:
        return _mirror_limb_rotation(rotation)
    if base in _OTHER_16_ROTATION_BASES:
        return (rotation + 8) % 16
    if base in _OTHER_XOR_4_BASES:
        return rotation ^ 4
    if base in _OTHER_XOR_2_BASES:
        return rotation ^ 2
    if base in _OTHER_XOR_1_BASES:
        return rotation ^ 1
    if base in _FACE_WITH_0_4_SWAP_BASES:
        return _FACE_WITH_0_4_SWAP_ROTATION.get(rotation, rotation)
    return _FACE_ROTATION_MIRROR.get(rotation, rotation)


def _mirror_face(base: str, fill: str, rotation: int) -> Tuple[str, int]:
    # Per-(base, fill) override takes precedence and bypasses fill swapping.
    if base in _PER_FILL_ROTATION_MAPS:
        rotation_map = _PER_FILL_ROTATION_MAPS[base].get(fill)
        if rotation_map is not None:
            return fill, rotation_map.get(rotation, rotation)
    if base == "S383":  # Location Depth - every symbol is self-mirror.
        return fill, rotation
    if base in _OTHER_BASE_ROTATION_MAPS:
        rotation_map = _OTHER_BASE_ROTATION_MAPS[base]
        return fill, rotation_map.get(rotation, rotation)
    if base == "S36d":  # Shoulder Hip Spine - contact-style rotation.
        return _mirror_contact(base, fill, rotation)
    new_rotation = _face_rotation(base, rotation)
    if base in _NO_FILL_SWAP_BASES:
        return fill, new_rotation
    fill_map = _FACE_FILL_OVERRIDES.get(base, _FACE_FILL_MIRROR)
    swapped_fill = fill_map.get(fill, fill)
    # Asymmetric head features (e.g. S30a single eyebrow) come as a fill
    # 1 / fill 2 pair. Only swap when the partner glyph exists in the font.
    if swapped_fill != fill and _symbol_exists(f"{base}{swapped_fill}{new_rotation:x}"):
        return swapped_fill, new_rotation
    return fill, new_rotation


# ---------------------------------------------------------------------------
# Movement arrows  (S217-S2f6)
# ---------------------------------------------------------------------------
# Rotation k mirrors to rotation k XOR 1 - the lowest bit encodes chirality
# at each direction. Covers the "Hits Front Wall / Chest / Ceiling / Floor"
# arrow families (Curve, Hump, Loop, Wave, Rotation). The fill 0<->1 swap
# encodes handedness; the rotation XOR 1 pairs adjacent directions.
# (See ISWA base names for the full taxonomy.)
_XOR_PAIRED_BASES = frozenset({
    # S2a6-S2ab: Curve / Hump / Loop / Wave Hits Front Wall
    "S2a6", "S2a7", "S2a8", "S2a9", "S2aa", "S2ab",
    # S2ad-S2b2: Curve / Hump / Loop / Wave Hits Chest
    "S2ad", "S2ae", "S2af", "S2b0", "S2b1", "S2b2",
    # S2ba-S2c2: Hump / Loop / Wave / Rotation Hits Ceiling
    # (S2b7, S2b8, S2c3, S2c5 use the dual-axis pair rule - see
    # _CEILING_HITS_*; S2b9, S2bb use the _FLOOR_HITS_* fill 0/1 swap.)
    "S2ba", "S2bc", "S2bd", "S2be", "S2bf",
    "S2c0", "S2c1", "S2c2",
})

# "Rotation Alternating" arrows (S2ac Hits Front Wall, S2b3 Hits Chest):
# fill 0<->1 swap, but the 4 rotations reflect via 3 - rotation
# (0<->3, 1<->2) rather than the XOR-1 pairing of their neighbours.
_ALTERNATING_ROTATION_BASES = frozenset({"S2ac", "S2b3"})

# Rotation 0<->1, 2<->7, 3<->6, 4<->5 - "axis-fold" reflection. Shared by
# the _FLOOR_HITS_* and _CEILING_HITS_* families (the dicts used to be
# duplicated).
_AXIS_FOLD_ROTATION = {0: 1, 1: 0, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2}

# "Dual-axis pair" bases - fills 0<->1 and 3<->4 swap (fills 2/5 stay);
# rotation uses _AXIS_FOLD_ROTATION.
#   S2b7, S2b8 Curve Hits Ceiling Small/Large
#   S2c3, S2c4, S2c5 Rotation Single/Double/Alternating Hits Ceiling
#   S2c6, S2c7 Curve Hits Floor Small/Large
#   S2d2, S2d3 Rotation Single/Double Hits Floor
_CEILING_HITS_BASES = frozenset({
    "S2b7", "S2b8", "S2c3", "S2c4", "S2c5", "S2c6", "S2c7", "S2d2", "S2d3",
})

# Rotation Alternating Hits Floor (S2d4): rotation 0<->4, 1<->5, 2<->7,
# 3<->6 (fill handled by the general movement-fill rule).
_S2D4_ROTATION = {0: 4, 4: 0, 1: 5, 5: 1, 2: 7, 7: 2, 3: 6, 6: 3}

# 16-rotation arrows (rotation +8) - Rotation Single/Double/Alternate Wall
# Plane (S2a2-S2a4), Rotation Floor Plane (S2df-S2e1), Arm Circle Hits Wall
# (S2e7-S2ec). Fill is handled by the general movement-fill rule.
_PLUS_8_ROTATION_BASES = frozenset({
    "S2a2", "S2a3", "S2a4",
    "S2df", "S2e0", "S2e1",
    "S2e7", "S2e8", "S2e9", "S2ea", "S2eb", "S2ec",
})

# ---------------------------------------------------------------------------
# Movement fill (handedness) - general rule
# ---------------------------------------------------------------------------
# For movement bases S22a-S2f6, the fill swap depends only on how many fills
# the base ships (handedness lives in the fill-0/1 pair, and for 6-fill bases
# also the 3/4 pair):
#   <3 fills          : keep fill (no handedness encoded)
#   3, 4, 5 fills      : swap 0<->1; keep 2/3/4
#   6 fills            : swap 0<->1 and 3<->4; keep 2/5
# Bases below S22a (Squeeze/Flick/Hinge/Contact/Single-straight) keep their
# fill, as do the two Arrowhead bases which carry no handedness.
_MOVEMENT_FILL_RANGE_START = 0x22a
_MOVEMENT_KEEP_ALL_FILL_BASES = frozenset({"S2f5", "S2f6"})
_FILL_34_SWAP = {"3": "4", "4": "3"}


@lru_cache(maxsize=None)
def _movement_fill_count(base: str) -> int:
    n = 0
    for f in range(6):
        if _symbol_exists(f"{base}{f}0"):
            n = f + 1
        else:
            break
    return n


def _movement_fill(base: str, fill: str) -> str:
    if int(base[1:], 16) < _MOVEMENT_FILL_RANGE_START:
        return fill
    if base in _MOVEMENT_KEEP_ALL_FILL_BASES:
        return fill
    count = _movement_fill_count(base)
    if count < 3:
        return fill
    if fill in _FILL_0_1_SWAP:
        return _FILL_0_1_SWAP[fill]
    if count == 6:
        return _FILL_34_SWAP.get(fill, fill)
    return fill

# Wrist Circle Hits Wall - Single (S2ef) / Double (S2f0): fills 0 and 1 are
# chirality pairs at the same rotation (S2ef0r <-> S2ef1r). Fill 2 (an arrow
# variant) uses XOR-1 on rotation.
_FILL_0_1_PAIRED_BASES = frozenset({"S2ef", "S2f0"})

# Diagonal movements and Floor-plane straight movements (S255-S26b): fill
# 0 <-> 1, fills 2/3/4 stay, rotation uses face-style 8-rotation reflection.
# Covers both the 6-rotation non-contiguous bases (S255-S264) and the
# 8-rotation contiguous bases (S265-S26b).
_DIAGONAL_AND_FLOOR_STRAIGHT_BASES = frozenset({
    # S255-S264: Diagonal Away/Towards/Between Away/Between Towards
    "S255", "S256", "S257", "S258",
    "S259", "S25a", "S25b", "S25c",
    "S25d", "S25e", "S25f", "S260",
    "S261", "S262", "S263", "S264",
    # S265-S26b: Single/Double/Triple Straight Movement & Wrist Flex,
    # Floor Plane (various sizes)
    "S265", "S266", "S267", "S268", "S269", "S26a", "S26b",
})

# Rotation 0<->1, 2<->7, 3<->6, 4<->5 (= _AXIS_FOLD_ROTATION); fill 0<->1.
#   S2b9, S2bb Hump Hits Ceiling 2/3 Humps Small
#   S2c8-S2d1 Hump / Loop / Wave Hits Floor (and Loop Hits Floor Small).
_FLOOR_HITS_BASES = frozenset({
    "S2b9", "S2bb",
    "S2c8", "S2c9", "S2ca", "S2cb", "S2cc", "S2cd", "S2ce", "S2cf",
    "S2d0", "S2d1",
})

# Finger Circles Hits Wall Single (S2f3) / Double (S2f4): fill stays;
# rotation uses a mixed pairing - 0<->2, 1<->3 (XOR-2 on the lower nibble),
# 4<->5, 6<->7 (XOR-1 on the upper nibble).
_FINGER_CIRCLES_BASES = frozenset({"S2f3", "S2f4"})
_FINGER_CIRCLES_ROTATION = {0: 2, 2: 0, 1: 3, 3: 1, 4: 5, 5: 4, 6: 7, 7: 6}


@lru_cache(maxsize=None)
def _movement_has_16_rotations(base: str) -> bool:
    # Probe both common fills - some bases only ship a subset.
    return _symbol_exists(f"{base}08") or _symbol_exists(f"{base}18")


def _movement_rotation(base: str, fill: str, rotation: int) -> int:
    """The per-base rotation rule for a movement symbol (fill-independent
    except for the Wrist-Circle bases)."""
    if base in _FLOOR_HITS_BASES or base in _CEILING_HITS_BASES:
        return _AXIS_FOLD_ROTATION.get(rotation, rotation)
    if base == "S2d4":  # Rotation Alternating Hits Floor.
        return _S2D4_ROTATION.get(rotation, rotation)
    if base in _PLUS_8_ROTATION_BASES:
        return (rotation + 8) % 16
    if base == "S2f2":  # Finger Circles Wall Double.
        return rotation ^ 4
    if base in _ALTERNATING_ROTATION_BASES:
        return 3 - rotation
    if base in _XOR_PAIRED_BASES:
        return rotation ^ 1
    if base in _FILL_0_1_PAIRED_BASES:
        # Fills 0/1 keep their rotation; fill 2 (an arrow variant) uses XOR-1.
        return rotation if fill in _FILL_0_1_SWAP else rotation ^ 1
    if base in _FINGER_CIRCLES_BASES:
        return _FINGER_CIRCLES_ROTATION.get(rotation, rotation)
    if base in _DIAGONAL_AND_FLOOR_STRAIGHT_BASES:
        return _FACE_ROTATION_MIRROR.get(rotation, rotation)
    if _movement_has_16_rotations(base):
        return (rotation + 8) % 16
    # Contact-style fallback: rotation (n - r) mod n.
    _, new_rotation = _mirror_contact(base, fill, rotation)
    return new_rotation


def _mirror_movement(base: str, fill: str, rotation: int) -> Tuple[str, int]:
    return _movement_fill(base, fill), _movement_rotation(base, fill, rotation)


# ---------------------------------------------------------------------------
# Symbol mirror
# ---------------------------------------------------------------------------
def mirror_symbol(symbol: str) -> str:
    """Return the horizontal mirror of an FSW symbol key (e.g. ``S2e748``).

    Symbols that don't exist in the font pass through unchanged. Symbols
    listed in :data:`_NO_MIRROR_SYMBOLS` also pass through unchanged because
    no other ISWA symbol represents their horizontal mirror; a warning is
    emitted so callers know the result is approximate.
    """
    if symbol in _SPECIAL_MIRROR_OVERRIDES:
        return _SPECIAL_MIRROR_OVERRIDES[symbol]
    if symbol in _SPECIAL_MIRROR_REVERSE:
        return _SPECIAL_MIRROR_REVERSE[symbol]
    if symbol in _NO_MIRROR_SYMBOLS:
        warnings.warn(
            f"{symbol} has no representable horizontal mirror in ISWA; "
            f"returning the original symbol unchanged.",
            stacklevel=2,
        )
        return symbol
    if not _symbol_exists(symbol):
        return symbol
    base, fill = symbol[:4], symbol[4]
    rotation = int(symbol[5], 16)
    section = _section(base)
    if section == "hand":
        new_fill, new_rotation = _mirror_hand(fill, rotation)
    elif section == "contact":
        new_fill, new_rotation = _mirror_contact(base, fill, rotation)
    elif section == "movement":
        new_fill, new_rotation = _mirror_movement(base, fill, rotation)
    else:
        new_fill, new_rotation = _mirror_face(base, fill, rotation)
    candidate = f"{base}{new_fill}{format(new_rotation, 'x')}"
    return candidate if _symbol_exists(candidate) else symbol


# ---------------------------------------------------------------------------
# Position flip
# ---------------------------------------------------------------------------
# Signs live on the [250, 750] x [250, 750] plane with the box centered on
# (500, 500). Horizontal mirror sends ``x -> 1000 - x``. We mirror each
# symbol's visual center so width drift between an original glyph and its
# (possibly slightly different) mirror glyph distributes symmetrically around
# the original position.
_AXIS = 1000
_BOX_MIRROR = {"L": "R", "R": "L"}


def _mirror_x(x: int, orig_width: int, new_width: int) -> int:
    center = x + orig_width / 2
    return round(_AXIS - center - new_width / 2)


def mirror_sign(fsw: str) -> str:
    """Return the horizontal mirror of an FSW sign.

    ``fsw`` must be ASCII Formal SignWriting. For SWU input, convert with
    ``signwriting.formats.swu_to_fsw.swu2fsw`` first.
    """
    if not fsw.isascii():
        raise ValueError(
            "mirror_sign expects ASCII FSW; convert SWU input via swu2fsw first"
        )

    sign = fsw_to_sign(fsw)
    if not sign["symbols"]:
        return fsw

    box_marker = _BOX_MIRROR.get(sign["box"]["symbol"], sign["box"]["symbol"])
    box_y = sign["box"]["position"][1]
    orig_min_x = min(s["position"][0] for s in sign["symbols"])

    mirrored_symbols = []
    for entry in sign["symbols"]:
        original = entry["symbol"]
        mirrored = mirror_symbol(original)
        orig_width, _ = get_symbol_size(original)
        new_width, _ = get_symbol_size(mirrored)
        x, y = entry["position"]
        mirrored_symbols.append({
            "symbol": mirrored,
            "position": (_mirror_x(x, orig_width, new_width), y),
        })

    mirrored_sign = {
        "box": {"symbol": box_marker, "position": (_AXIS - orig_min_x, box_y)},
        "symbols": mirrored_symbols,
    }
    return sign_to_fsw(mirrored_sign)
