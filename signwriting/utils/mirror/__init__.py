"""Horizontal mirror for SignWriting symbols and signs.

The Sutton SignWriting symbol set (ISWA) splits into ranges that mirror
differently. This module groups them as:

* **Hands** (S100-S204): each base has 16 rotations - 0-7 are right-hand at
  eight compass directions, 8-15 are the corresponding left-hand variants.
  The mirror is the matching half: ``rotation -> (rotation + 8) % 16``.
* **Movement arrows** (S205-S2f6): each base has up to six fills that encode
  arrow style **and handedness**. Fill pairs ``0/1``, ``3/4`` and ``2/5`` are
  the right/left-hand variants of the same movement. Mirroring swaps the fill
  in its pair and applies the same rotation step as hands (``+8``). The few
  movement bases that only define rotations 0-7 use the face-style reflection
  instead.
* **Everything else** (S2f7+: dynamics, heads, faces, eyes, mouth, trunk,
  ...): only eight rotations exist. Mirroring reflects the direction across
  the vertical axis: ``0`` and ``4`` are fixed, and the diagonals swap
  (``1<->7``, ``2<->6``, ``3<->5``). Some head bases (e.g. asymmetric
  eyebrows) additionally encode handedness in fill ``1`` vs fill ``2``; we
  swap that pair when the partner glyph exists.

The sign-level mirror reflects each symbol's x-position across ``x = 500``
(the box centerline), recomputes the box's right edge, and flips the ``L``
and ``R`` lane markers.

The symbol-level rotation logic is a section-typed reformulation of
signmaker's ``ssw.mirror`` (https://github.com/sutton-signwriting/signmaker).
The movement fill swap is the extension Steve and Amit identified by
inspecting the ``SuttonSignWritingLine`` font's fill-by-rotation grid.
"""
from typing import Tuple

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.formats.sign_to_fsw import sign_to_fsw
from signwriting.visualizer.visualize import get_symbol_size


# ---------------------------------------------------------------------------
# Section dispatch
# ---------------------------------------------------------------------------
_HAND_BASE_MIN, _HAND_BASE_MAX = 0x100, 0x204
_MOVEMENT_BASE_MIN, _MOVEMENT_BASE_MAX = 0x205, 0x2f6


def _section(base: str) -> str:
    base_value = int(base[1:], 16)
    if _HAND_BASE_MIN <= base_value <= _HAND_BASE_MAX:
        return "hand"
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
# Face, head, dynamics, eyes, mouth, ...  (S2f7+)
# ---------------------------------------------------------------------------
_FACE_ROTATION_MIRROR = {0: 0, 1: 7, 2: 6, 3: 5, 4: 4, 5: 3, 6: 2, 7: 1}
_FACE_FILL_MIRROR = {"1": "2", "2": "1"}


def _mirror_face(base: str, fill: str, rotation: int) -> Tuple[str, int]:
    new_rotation = _FACE_ROTATION_MIRROR.get(rotation, rotation)
    swapped_fill = _FACE_FILL_MIRROR.get(fill, fill)
    # Asymmetric head features (e.g. S30a single eyebrow) come as a fill
    # 1 / fill 2 pair. Only swap when the partner glyph exists in the font.
    if swapped_fill != fill and _symbol_exists(f"{base}{swapped_fill}{new_rotation:x}"):
        return swapped_fill, new_rotation
    return fill, new_rotation


# ---------------------------------------------------------------------------
# Movement arrows  (S205-S2f6)
# ---------------------------------------------------------------------------
_MOVEMENT_FILL_MIRROR = {
    "0": "1", "1": "0",
    "2": "5", "5": "2",
    "3": "4", "4": "3",
}


def _movement_has_16_rotations(base: str) -> bool:
    # Probe both common fills - some bases only ship a subset.
    return _symbol_exists(f"{base}08") or _symbol_exists(f"{base}18")


def _mirror_movement(base: str, fill: str, rotation: int) -> Tuple[str, int]:
    if _movement_has_16_rotations(base):
        new_rotation = (rotation + 8) % 16
    else:
        new_rotation = _FACE_ROTATION_MIRROR.get(rotation, rotation)

    swapped_fill = _MOVEMENT_FILL_MIRROR.get(fill, fill)
    # Prefer the handedness-swapped fill, but a few bases have gaps in the
    # font - fall back to the original fill when the swap is missing.
    if swapped_fill != fill and _symbol_exists(f"{base}{swapped_fill}{new_rotation:x}"):
        return swapped_fill, new_rotation
    return fill, new_rotation


# ---------------------------------------------------------------------------
# Symbol mirror
# ---------------------------------------------------------------------------
def mirror_symbol(symbol: str) -> str:
    """Return the horizontal mirror of an FSW symbol key (e.g. ``S2e748``).

    Symbols that don't exist in the font pass through unchanged.
    """
    if not _symbol_exists(symbol):
        return symbol
    base, fill = symbol[:4], symbol[4]
    rotation = int(symbol[5], 16)
    section = _section(base)
    if section == "hand":
        new_fill, new_rotation = _mirror_hand(fill, rotation)
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
