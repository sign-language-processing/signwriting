"""Mapping between SignWriting hand symbols and HamNoSys handshape notations.

A SignWriting hand symbol key ``SXXXFR`` factors into a base handshape ``XXX``
(261 bases, S100-S204), a fill ``F`` (0-5) and a rotation ``R`` (0-15).
Each base maps to a list of equivalent HamNoSys handshape spellings
(``mappings.json``, first entry is canonical) - real corpora spell the
same shape several ways.
Fill and rotation map to HamNoSys orientation symbols (extended finger
direction + palm orientation).
"""

import json
import re
from functools import cache
from pathlib import Path

HERE = Path(__file__).parent
MAPPINGS_FILE = HERE / "mappings.json"

# ISWA 2010 category 01 (hands) groups: (first base, number of bases),
# derived from @sutton-signwriting/core's symidArr.
GROUPS = [(0x100, 14), (0x10E, 16), (0x11E, 38), (0x144, 8), (0x14C, 58),
          (0x186, 30), (0x1A4, 22), (0x1BA, 19), (0x1CD, 40), (0x1F5, 16)]
HAND_BASES = [f"S{base:03x}" for start, count in GROUPS for base in range(start, start + count)]
HAND_BASES_SET = frozenset(HAND_BASES)

# Rotation 0 points up (wall plane) / away (floor plane); right-hand rotations
# (0-7) step counterclockwise, left-hand rotations (8-15) are mirrored.
WALL_DIRECTIONS = ["u", "ul", "l", "dl", "d", "dr", "r", "ur"]
FLOOR_DIRECTIONS = ["o", "ol", "l", "il", "i", "ir", "r", "or"]


@cache
def symbol_chars() -> dict[str, str]:
    """HamNoSys symbol name -> character, from the package's symbols.json."""
    with open(HERE.parent / "symbols.json", encoding="utf-8") as f:
        return {symbol["name"]: symbol["char"] for symbol in json.load(f)}


def parse_key(key: str) -> tuple[str, int, int]:
    """Split a symbol key 'SXXXFR' (or a bare base 'SXXX') into (base, fill, rotation)."""
    if len(key) not in (4, 6) or key[0] != "S":
        raise ValueError(f"invalid symbol key {key!r}")
    return key[1:4].lower(), int(key[4], 16) if len(key) == 6 else 0, int(key[5], 16) if len(key) == 6 else 0


def key_to_symid(key: str) -> str:
    """Convert a hand symbol key to its ISWA 2010 symid, e.g. 'S10000' -> '01-01-001-01-01-01'."""
    base, fill, rotation = parse_key(key)
    index = HAND_BASES.index(f"S{base}")
    for group, (_start, count) in enumerate(GROUPS, start=1):
        if index < count:
            return f"01-{group:02d}-{index + 1:03d}-01-{fill + 1:02d}-{rotation + 1:02d}"
        index -= count
    raise ValueError(f"S{base} is not a hand symbol")


def orientation(fill: int, rotation: int) -> str:
    """HamNoSys orientation (extended finger direction + palm orientation) for
    a SignWriting fill and rotation.

    Convention: SignWriting's unfilled symbol shows the palm from the writer's
    viewpoint - facing the body in the wall plane (hampalmd), facing up in the
    floor plane (hampalmu) - and the filled symbol shows the back of the hand.
    HamNoSys palm orientation is relative to the extended finger direction, so
    the palm symbol does not vary with rotation.
    """
    directions = WALL_DIRECTIONS if fill < 3 else FLOOR_DIRECTIONS
    right_hand = rotation < 8
    direction = directions[rotation % 8]
    if not right_hand:
        direction = mirror(direction)
    side = "l" if right_hand else "r"
    palm = ("d", side, "u", "u", side, "d")[fill]
    return symbol_chars()[f"hamextfinger{direction}"] + symbol_chars()[f"hampalm{palm}"]


def mirror(direction: str) -> str:
    return direction.replace("l", "R").replace("r", "l").replace("R", "r")


@cache
def mappings() -> dict[str, list[str]]:
    with open(MAPPINGS_FILE, encoding="utf-8") as f:
        return json.load(f)


def sw_to_hamnosys(key: str) -> str | None:
    """Full HamNoSys for a SignWriting hand symbol: handshape + orientation.

    Uses the canonical (first) handshape spelling; returns None when the base
    has no mapping yet. A bare base key ('S100') returns just the handshape.
    """
    base, fill, rotation = parse_key(key)
    spellings = mappings().get(f"S{base}") or []
    if not spellings:
        return None
    return spellings[0] + orientation(fill, rotation) if len(key) == 6 else spellings[0]


def hamnosys_to_sw(hamnosys: str) -> str | None:
    """SignWriting base key for an exact HamNoSys handshape spelling,
    e.g. hamfinger2 hamthumbacrossmod -> 'S100'."""
    for key, spellings in mappings().items():
        if hamnosys in spellings:
            return key
    return None


# HamNoSys handshape token grammar: a base form, then thumb / bending /
# finger-selection modifiers. hambetween joins a handshape only in the
# thumb-between-fingers pattern (selector, between, selector) - elsewhere
# it is a location relation.
HNS_BASE_FORMS = frozenset(range(0xE000, 0xE00C))
HNS_SELECTORS = frozenset(range(0xE070, 0xE075))
HNS_MODIFIERS = frozenset(range(0xE00C, 0xE015)) | frozenset(range(0xE070, 0xE07C))
HNS_BETWEEN = 0xE0E6


def handshapes(hamnosys: str) -> list[str]:
    """Extract the handshape tokens from a full HamNoSys transcription."""
    shapes: list[str] = []
    current = None
    for i, char in enumerate(hamnosys):
        codepoint = ord(char)
        if codepoint in HNS_BASE_FORMS:
            if current:
                shapes.append(current)
            current = char
        elif current and codepoint in HNS_MODIFIERS:
            current += char
        elif current and codepoint == HNS_BETWEEN \
                and ord(current[-1]) in HNS_SELECTORS \
                and i + 1 < len(hamnosys) and ord(hamnosys[i + 1]) in HNS_SELECTORS:  # pylint: disable=unsubscriptable-object
            current += char
        else:
            if current:
                shapes.append(current)
            current = None
    if current:
        shapes.append(current)
    return shapes


def hand_symbols(fsw: str) -> list[str]:
    """SignWriting hand base keys in an FSW sign - the counterpart of
    handshapes() for mining parallel corpora, e.g. 'M518x518S10011482x483' -> ['S100']."""
    return [f"S{base}" for base in re.findall(r"S([0-9a-f]{3})[0-5][0-9a-f]", fsw)
            if f"S{base}" in HAND_BASES_SET]
