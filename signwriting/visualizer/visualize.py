# pylint: disable=unnecessary-lambda-assignment

from functools import lru_cache
from pathlib import Path
from typing import Tuple, List, Literal

from PIL import Image, ImageDraw, ImageFont

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.formats.fsw_to_swu import key2id, symbol_line, symbol_fill

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


# pylint: disable=too-many-locals, too-many-arguments
def signwriting_to_image(fsw: str, antialiasing=True, trust_box=True, embedded_color=False,
                         line_color: RGBA = (0, 0, 0, 255),
                         fill_color: RGBA = (255, 255, 255, 255)) -> Image:
    sign = fsw_to_sign(fsw)
    if len(sign['symbols']) == 0:
        return Image.new('RGBA', (1, 1), (0, 0, 0, 0))

    positions = [s["position"] for s in sign['symbols']]
    min_x = min(positions, key=lambda p: p[0])[0]
    min_y = min(positions, key=lambda p: p[1])[1]

    max_x, max_y, = sign["box"]["position"]

    if not trust_box:
        max_x, max_y = 0, 0
        for symbol in sign['symbols']:
            symbol_x, symbol_y = symbol["position"]
            symbol_width, symbol_height = get_symbol_size(symbol["symbol"])
            max_x = max(max_x, symbol_x + symbol_width)
            max_y = max(max_y, symbol_y + symbol_height)

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


# pylint: disable=too-many-locals, too-many-arguments
def signwritings_to_image(fsw_list: List[str], antialiasing: bool = True, trust_box: bool = True,
                        embedded_color: bool = False, line_color: Tuple[int, int, int, int] = (0, 0, 0, 255),
                        fill_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
                        direction: Literal["horizontal", "vertical"] = "horizontal") -> Image:
    images = [
        signwriting_to_image(fsw_string, antialiasing, trust_box, embedded_color, line_color, fill_color)
        for fsw_string in fsw_list
    ]

    if direction == "horizontal":
        max_height = max(img.height for img in images)
        total_width = sum(img.width for img in images)
        size = (total_width, max_height)
        paste_position = lambda offset: (offset, 0)
        offset_increment = lambda img: img.width
    else:
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images)
        size = (max_width, total_height)
        paste_position = lambda offset: (0, offset)
        offset_increment = lambda img: img.height

    final_image = Image.new("RGBA", size, (255, 255, 255, 0))
    offset = 0
    for img in images:
        final_image.paste(img, paste_position(offset))
        offset += offset_increment(img)

    return final_image
