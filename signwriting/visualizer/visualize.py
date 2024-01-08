from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.formats.fsw_to_swu import key2id, symbol_line, symbol_fill


@lru_cache(maxsize=None)
def get_font(font_name: str):
    font_path = Path(__file__).parent / f'{font_name}.ttf'
    return ImageFont.truetype(str(font_path), 30)


# pylint: disable=too-many-locals
def signwriting_to_image(fsw: str, antialiasing=True) -> Image:
    sign = fsw_to_sign(fsw)
    if len(sign['symbols']) == 0:
        return Image.new('RGBA', (1, 1), (0, 0, 0, 0))

    positions = [s["position"] for s in sign['symbols']]
    min_x = min(positions, key=lambda p: p[0])[0]
    min_y = min(positions, key=lambda p: p[1])[1]
    max_x, max_y, = sign["box"]["position"]
    img = Image.new('RGBA', (max_x - min_x, max_y - min_y), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    if not antialiasing:
        draw.fontmode = '1'

    fill_font = get_font('SuttonSignWritingFill')
    line_font = get_font('SuttonSignWritingLine')

    for symbol in sign['symbols']:
        x, y = symbol["position"]
        x, y = x - min_x, y - min_y
        symbol_id = key2id(symbol["symbol"])
        draw.text((x, y), symbol_fill(symbol_id), font=fill_font, fill=(255, 255, 255))
        draw.text((x, y), symbol_line(symbol_id), font=line_font, fill=(0, 0, 0))

    return img
