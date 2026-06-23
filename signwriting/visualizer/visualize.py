import os
from functools import lru_cache
from pathlib import Path
from typing import Tuple, List, Union

from PIL import Image, ImageDraw, ImageFont

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.formats.fsw_to_swu import key2id, symbol_line, symbol_fill
from signwriting.formats.swu import is_swu
from signwriting.formats.swu_to_fsw import swu2fsw
from signwriting.types import Sign

# Type alias representing a tuple of four integers: Red, Green, Blue, Alpha
RGBA = Tuple[int, int, int, int]


@lru_cache(maxsize=None)
def get_font(font_name: str) -> ImageFont.FreeTypeFont:
    font_path = Path(__file__).parent / f'{font_name}.ttf'
    return ImageFont.truetype(str(font_path), 30)


@lru_cache(maxsize=None)
def get_symbol_size(symbol: str):
    font = get_font('SuttonSignWritingLine')
    line_id = symbol_line(key2id(symbol))
    left, top, right, bottom = font.getbbox(line_id)
    return right - left, bottom - top


def signwriting_box(sign: Sign) -> Tuple[int, int]:
    """Recompute a sign's bottom-right box corner ``(max_x, max_y)`` from its
    symbols' rendered sizes - the tight box used when ``trust_box`` is off."""
    max_x, max_y = 0, 0
    for symbol in sign["symbols"]:
        symbol_x, symbol_y = symbol["position"]
        symbol_width, symbol_height = get_symbol_size(symbol["symbol"])
        max_x = max(max_x, symbol_x + symbol_width)
        max_y = max(max_y, symbol_y + symbol_height)
    return max_x, max_y


def _clear_caches_after_fork():
    # ImageFont objects cached by lru_cache can become corrupted after fork(),
    # causing garbage data (e.g., wrong image dimensions). Clear caches in child
    # processes so fonts are reloaded fresh.
    get_font.cache_clear()
    get_symbol_size.cache_clear()


os.register_at_fork(after_in_child=_clear_caches_after_fork)


# pylint: disable=too-many-locals, too-many-arguments
def visualize_sign(fsw: str, antialiasing=True, trust_box=True, embedded_color=False,
                   line_color: RGBA = (0, 0, 0, 255),
                   fill_color: RGBA = (255, 255, 255, 255)) -> Image.Image:
    if is_swu(fsw):
        fsw = swu2fsw(fsw)

    sign = fsw_to_sign(fsw)
    if len(sign['symbols']) == 0:
        return Image.new('RGBA', (1, 1), (0, 0, 0, 0))

    positions = [s["position"] for s in sign['symbols']]
    min_x = min(positions, key=lambda p: p[0])[0]
    min_y = min(positions, key=lambda p: p[1])[1]

    max_x, max_y, = sign["box"]["position"]

    if not trust_box:
        max_x, max_y = signwriting_box(sign)

    img = Image.new('RGBA', (max_x - min_x, max_y - min_y), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img, 'RGBA')
    if not antialiasing:
        draw.fontmode = '1'

    fill_font = get_font('SuttonSignWritingFill')
    line_font = get_font('SuttonSignWritingLine')

    for symbol in sign['symbols']:
        x, y = symbol["position"]
        x, y = x - min_x, y - min_y
        symbol_id = key2id(symbol["symbol"])
        draw.text((x, y), symbol_fill(symbol_id), fill=fill_color,
                  font=fill_font, embedded_color=embedded_color)
        draw.text((x, y), symbol_line(symbol_id), fill=line_color,
                  font=line_font, embedded_color=embedded_color)

    return img


def _box_symbol(fsw: str) -> str:
    if is_swu(fsw):
        fsw = swu2fsw(fsw)
    return fsw_to_sign(fsw)["box"]["symbol"]


def stack_signs(images: List[Image.Image], box_symbols: List[str]) -> Image.Image:
    GAP = 20
    width = max(img.width for img in images)
    height = sum(img.height for img in images) + GAP * (len(images) - 1)

    layout_image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    y = 0
    for img, box in zip(images, box_symbols):
        if box == "L":
            x = 0
        elif box == "R":
            x = width - img.width
        else:  # M / B: centered lane
            x = (width - img.width) // 2
        layout_image.paste(img, (x, y))
        y += img.height + GAP

    return layout_image


def signwriting_to_image(fsw: Union[str, List[str]], **kwargs) -> Image.Image:
    fsw_list = [fsw] if isinstance(fsw, str) else fsw
    images = [visualize_sign(f, **kwargs) for f in fsw_list]
    if len(images) == 1:
        return images[0]
    return stack_signs(images, [_box_symbol(f) for f in fsw_list])
