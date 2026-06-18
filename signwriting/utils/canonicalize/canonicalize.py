"""Rewrite a single FSW sign with its symbols in a canonical order.

Symbols are sorted by ISWA category, then top-to-bottom and left-to-right
within a category. The category order (faces first, movement last) was
derived empirically from the single_signs corpus - see README.md.

The one wrinkle is overlapping glyphs. When two symbols' inked pixels
overlap, one is drawn on top of the other - but that only matters if the
two paint a shared pixel with different colors (e.g. one symbol's opaque
white fill covering the other's line). So overlapping pairs are rendered
both ways: if the images match, the order is free and we reorder to
canonical; if they differ, the pair keeps its input order. The sort is
therefore a topological one - the canonical order is the target, with
order-sensitive overlaps as hard precedence constraints layered on top.

Finally, the sign's box is recomputed to tightly fit the symbols (the same
calculation ``signwriting_to_image`` performs when ``trust_box`` is off).
"""
import functools
from typing import List

import numpy as np
from PIL import Image, ImageDraw

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.formats.fsw_to_swu import key2id, symbol_fill, symbol_line
from signwriting.formats.sign_to_fsw import sign_to_fsw
from signwriting.types import Sign, SignSymbol
from signwriting.visualizer.visualize import get_font, get_symbol_size, signwriting_box


def _category_rank(symbol: str) -> int:
    base = int(symbol[1:4], 16)
    if 0x2ff <= base <= 0x36c:  # faces
        return 0
    if base >= 0x36d:  # other: head, trunk, limbs, location, punctuation
        return 1
    if base <= 0x204:  # hands
        return 2
    if base <= 0x220:  # contact
        return 3
    return 4  # movement (0x221-0x2fe)


def _sort_key(symbol: SignSymbol):
    x, y = symbol["position"]
    return _category_rank(symbol["symbol"]), y, x


# A sign's center pivot, ported from @sutton-signwriting/font-ttf signNormalize:
# when a sign contains a face it is centered horizontally on the face, when it
# contains a face or trunk it is centered vertically on those, and otherwise it
# falls back to the full bounding box.
_HCENTER_RANGE = (0x2ff, 0x36c)  # head / face
_VCENTER_RANGE = (0x2ff, 0x375)  # head / face + trunk


def _bbox(symbols: List[SignSymbol]):
    left = min(s["position"][0] for s in symbols)
    top = min(s["position"][1] for s in symbols)
    right = max(s["position"][0] + get_symbol_size(s["symbol"])[0] for s in symbols)
    bottom = max(s["position"][1] + get_symbol_size(s["symbol"])[1] for s in symbols)
    return left, top, right, bottom


def _center_offset(symbols: List[SignSymbol]):
    """Offset of the sign's center from (500, 500), using the face/trunk pivot
    when present and the full bounding box otherwise."""
    left, top, right, bottom = _bbox(symbols)
    faces = [s for s in symbols if _HCENTER_RANGE[0] <= int(s["symbol"][1:4], 16) <= _HCENTER_RANGE[1]]
    if faces:
        left, _, right, _ = _bbox(faces)
    bodies = [s for s in symbols if _VCENTER_RANGE[0] <= int(s["symbol"][1:4], 16) <= _VCENTER_RANGE[1]]
    if bodies:
        _, top, _, bottom = _bbox(bodies)
    return int((left + right) / 2) - 500, int((top + bottom) / 2) - 500


@functools.cache
def _symbol_mask(symbol: str) -> np.ndarray:
    """Boolean ink mask (line + fill) of a symbol rendered at the origin."""
    width, height = get_symbol_size(symbol)
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.fontmode = "1"  # 1-bit edges; overlap is a crisp yes/no question
    symbol_id = key2id(symbol)
    draw.text((0, 0), symbol_fill(symbol_id), fill=(0, 0, 0, 255), font=get_font("SuttonSignWritingFill"))
    draw.text((0, 0), symbol_line(symbol_id), fill=(0, 0, 0, 255), font=get_font("SuttonSignWritingLine"))
    return np.asarray(image)[:, :, 3] > 0


def _symbols_share_ink(a: SignSymbol, b: SignSymbol) -> bool:
    """True if two positioned symbols share an inked pixel (a real glyph
    overlap, not merely intersecting bounding boxes)."""
    (ax, ay), (bx, by) = a["position"], b["position"]
    mask_a = _symbol_mask(a["symbol"])
    mask_b = _symbol_mask(b["symbol"])

    left, top = max(ax, bx), max(ay, by)
    right = min(ax + mask_a.shape[1], bx + mask_b.shape[1])
    bottom = min(ay + mask_a.shape[0], by + mask_b.shape[0])
    if left >= right or top >= bottom:
        return False

    region_a = mask_a[top - ay:bottom - ay, left - ax:right - ax]
    region_b = mask_b[top - by:bottom - by, left - bx:right - bx]
    return bool(np.logical_and(region_a, region_b).any())


@functools.cache
def _draw_order_differs(symbol_a: str, symbol_b: str, dx: int, dy: int) -> bool:
    """True if drawing ``symbol_a`` then ``symbol_b`` differs from the reverse,
    with ``symbol_b`` offset from ``symbol_a`` by ``(dx, dy)``. Order only shows
    when the glyphs paint a shared pixel with different colors - e.g. one
    symbol's opaque white fill covering the other's line."""
    a_width, a_height = get_symbol_size(symbol_a)
    b_width, b_height = get_symbol_size(symbol_b)
    min_x, min_y = min(0, dx), min(0, dy)
    size = (max(a_width, dx + b_width) - min_x, max(a_height, dy + b_height) - min_y)

    def render(symbols) -> np.ndarray:
        image = Image.new("RGBA", size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(image, "RGBA")
        draw.fontmode = "1"  # match the non-antialiased render-equivalence guarantee
        for symbol, (x, y) in symbols:
            symbol_id = key2id(symbol)
            draw.text((x, y), symbol_fill(symbol_id), fill=(255, 255, 255, 255), font=get_font("SuttonSignWritingFill"))
            draw.text((x, y), symbol_line(symbol_id), fill=(0, 0, 0, 255), font=get_font("SuttonSignWritingLine"))
        return np.asarray(image)

    a_at = (symbol_a, (-min_x, -min_y))
    b_at = (symbol_b, (dx - min_x, dy - min_y))
    return not np.array_equal(render([a_at, b_at]), render([b_at, a_at]))


def _order_matters(a: SignSymbol, b: SignSymbol) -> bool:
    """True if the draw order of two symbols affects the rendered image.

    Glyphs that don't share ink commute trivially; glyphs that do are rendered
    both ways and only constrain the order when the two images differ."""
    if not _symbols_share_ink(a, b):
        return False
    (ax, ay), (bx, by) = a["position"], b["position"]
    return _draw_order_differs(a["symbol"], b["symbol"], bx - ax, by - ay)


def _canonical_order(symbols: List[SignSymbol]) -> List[SignSymbol]:
    n = len(symbols)
    # Symbols whose draw order is visible must keep their input order: edge
    # i -> j whenever i precedes j in the input and swapping them would change
    # the image. Edges only ever point forward in the input, so it's acyclic.
    successors = [[] for _ in range(n)]
    indegree = [0] * n
    for i in range(n):
        for j in range(i + 1, n):
            if _order_matters(symbols[i], symbols[j]):
                successors[i].append(j)
                indegree[j] += 1

    keys = [_sort_key(s) for s in symbols]
    placed = [False] * n
    order = []
    for _ in range(n):
        # Among symbols whose overlap-predecessors are all placed, take the one
        # earliest in canonical order (input index breaks ties for stability).
        ready = (i for i in range(n) if not placed[i] and indegree[i] == 0)
        chosen = min(ready, key=lambda i: (keys[i], i))
        placed[chosen] = True
        order.append(symbols[chosen])
        for j in successors[chosen]:
            indegree[j] -= 1
    return order


def canonicalize(fsw: str) -> str:
    """Rewrite an FSW sign with its symbols in canonical order, centered, with a
    tight box.

    Symbols are ordered by category (faces, other, hands, contact, movement)
    and within a category top-to-bottom then left-to-right; overlapping symbols
    keep their original relative order so the rendered image is unchanged. The
    sign is then centered on (500, 500) - on its face/trunk when present,
    otherwise on its bounding box - and the box recomputed to fit tightly.

    ``fsw`` must be ASCII Formal SignWriting. For SWU input, convert with
    ``signwriting.formats.swu_to_fsw.swu2fsw`` first.
    """
    if not fsw.isascii():
        raise ValueError("canonicalize expects ASCII FSW; convert SWU input via swu2fsw first")

    sign = fsw_to_sign(fsw)
    if not sign["symbols"]:
        return fsw

    ordered = _canonical_order(sign["symbols"])
    max_x, max_y = signwriting_box(sign)
    offset_x, offset_y = _center_offset(ordered)
    canonical_sign: Sign = {
        "box": {"symbol": sign["box"]["symbol"], "position": (max_x - offset_x, max_y - offset_y)},
        "symbols": [{"symbol": s["symbol"],
                     "position": (s["position"][0] - offset_x, s["position"][1] - offset_y)}
                    for s in ordered],
    }
    return sign_to_fsw(canonical_sign)
