# This should be reimplemented in python https://github.com/sign-language-processing/signwriting/issues/1
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.formats.fsw_to_swu import key2id, symbol_line, symbol_fill


@lru_cache(maxsize=None)
def get_font(font_name: str):
    return ImageFont.truetype(f'{font_name}.ttf', 30)


def signwriting_to_image(fsw: str) -> Image:
    sign = fsw_to_sign(fsw)
    if len(sign['symbols']) == 0:
        return Image.new('RGBA', (1, 1), (0, 0, 0, 0))

    positions = [s["position"] for s in sign['symbols']]
    min_x = min(positions, key=lambda p: p[0])[0]
    min_y = min(positions, key=lambda p: p[1])[1]
    max_x, max_y, = sign["box"]["position"]
    size = (max_x - min_x, max_y - min_y)
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    line_font = get_font('SuttonSignWritingLine')
    fill_font = get_font('SuttonSignWritingFill')

    for symbol in sign['symbols']:
        x, y = symbol["position"]
        x, y = x - min_x, y - min_y
        symbol_id = key2id(symbol["symbol"])
        draw.text((x, y), symbol_line(symbol_id), font=line_font, fill=(0, 0, 0))
        draw.text((x, y), symbol_fill(symbol_id), font=fill_font, fill=(255, 255, 255))

    return img
