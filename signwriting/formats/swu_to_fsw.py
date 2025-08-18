import re
from typing import List

from signwriting.formats.swu import re_swu


def swu2fsw(swu_text: str) -> str:
    if not swu_text:
        return ''

    # Initial replacements
    fsw = swu_text.replace("𝠀", "A").replace("𝠁", "B").replace("𝠂", "L").replace("𝠃", "M").replace("𝠄", "R")

    # SWU symbols to FSW keys
    syms = re.findall(re_swu['symbol'], fsw)
    if syms:
        for sym in syms:
            fsw = fsw.replace(sym, swu2key(sym))

    # SWU coordinates to FSW coordinates
    coords = re.findall(re_swu['coord'], fsw)
    if coords:
        for coord in coords:
            fsw = fsw.replace(coord, 'x'.join(map(str, swu2coord(coord))))

    return fsw


def swu2key(swu_sym: str) -> str:
    symcode = ord(swu_sym) - 0x40001
    base = symcode // 96
    fill = (symcode - (base * 96)) // 16
    rotation = symcode - (base * 96) - (fill * 16)
    return f'S{hex(base + 0x100)[2:]}{hex(fill)[2:]}{hex(rotation)[2:]}'


def swu2num(swu_num: str) -> int:
    return ord(swu_num) - 0x1D80C + 250


def swu2coord(swu_coord: str) -> List[int]:
    return [swu2num(swu_coord[0]), swu2num(swu_coord[1])]
